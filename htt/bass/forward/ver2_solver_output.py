"""VER2 observer-neutral solver-output builders for the BASS S3 lane."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from common.contracts import ArtifactManifest, SolverCoreOutput

from bass.background.bianchi_types import StructureConstants, get_type
from bass.hierarchy.integrator import IntegrationResult
from bass.los.ver2_source_propagator import (
    ObserverFrameMetadata,
    PropagatorMode,
    SourcePropagator,
    SourcePropagatorConfig,
    build_source_propagator,
)
from bass.runtime.ver2_execution import (
    FeatureStatus,
    RuntimeControlBlock,
    SolverFeatureFlags,
    SolverTier,
)
from bass.species.base import SpeciesLabel
from bass.species.registry import SpeciesBackgroundRegistry

__all__ = [
    "BassReleaseMetadata",
    "build_solver_core_output",
    "build_solver_core_output_from_native_result",
    "build_solver_core_output_from_lowell_result",
    "solver_core_output_to_payload",
    "solver_core_output_from_payload",
]


@dataclass(frozen=True)
class BassReleaseMetadata:
    """Release and reproducibility metadata for one solver run."""

    release_stage: str
    run_label: str
    config_hash: str
    code_version: str
    schema_version: str
    git_commit: str | None
    random_seed: int | None = None

    def __post_init__(self) -> None:
        if not self.release_stage:
            raise ValueError("release_stage must be non-empty")
        if not self.run_label:
            raise ValueError("run_label must be non-empty")
        if not self.config_hash:
            raise ValueError("config_hash must be non-empty")
        if not self.code_version:
            raise ValueError("code_version must be non-empty")
        if not self.schema_version:
            raise ValueError("schema_version must be non-empty")
        if self.random_seed is not None and self.random_seed < 0:
            raise ValueError("random_seed must be non-negative when provided")


def build_solver_core_output(
    *,
    manifest: ArtifactManifest,
    bianchi_type: str,
    tilt_enabled: bool,
    harmonic_basis: str,
    eb_sign_convention: str,
    thomson_mode: str,
    runtime_controls: RuntimeControlBlock,
    feature_flags: SolverFeatureFlags,
    propagator: SourcePropagatorConfig,
    release: BassReleaseMetadata,
    alm_T: object | None = None,
    alm_E: object | None = None,
    alm_B: object | None = None,
    map_T: object | None = None,
    map_Q: object | None = None,
    map_U: object | None = None,
    deterministic_template: dict[str, Any] | None = None,
    anisotropic_covariance: object | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> SolverCoreOutput:
    """Build the canonical observer-neutral `SolverCoreOutput` shell."""
    if manifest.owner != "BASS":
        raise ValueError("SolverCoreOutput manifests must be owned by BASS")
    metadata = {
        "bianchi_type": bianchi_type,
        "harmonic_basis": harmonic_basis,
        "eb_sign_convention": eb_sign_convention,
        "multipole_cutoff": runtime_controls.multipole_cutoff,
        "tilt_enabled": tilt_enabled,
        "thomson_mode": thomson_mode,
        "solver_tier": runtime_controls.tier.value,
        "integrator_family": runtime_controls.integrator_family.value,
        "coupling_mode": runtime_controls.coupling_mode.value,
        "propagator_mode": propagator.mode.value,
        "feature_flags": {key: value.value for key, value in asdict(feature_flags).items()},
        "release_stage": release.release_stage,
        "run_label": release.run_label,
        "observer_neutral": True,
        "forbidden_products": ("posterior", "likelihood", "p_value"),
    }
    if extra_metadata is not None:
        overlap = {
            key for key in extra_metadata
            if key in {"observer_neutral", "forbidden_products"}
        }
        if overlap:
            raise ValueError(f"extra_metadata may not override reserved keys: {sorted(overlap)}")
        metadata.update(extra_metadata)
    return SolverCoreOutput(
        alm_T=alm_T,
        alm_E=alm_E,
        alm_B=alm_B,
        map_T=map_T,
        map_Q=map_Q,
        map_U=map_U,
        deterministic_template=deterministic_template,
        anisotropic_covariance=anisotropic_covariance,
        metadata=metadata,
        manifest=manifest,
    )


def _interp_series(eta_grid: np.ndarray, values: np.ndarray, eta: float) -> float:
    return float(np.interp(float(eta), eta_grid, values))


def _build_visibility_fn_from_a_lookup(species: SpeciesBackgroundRegistry, a_lookup):
    baryon = species[SpeciesLabel.BARYON]
    interp = baryon._recomb  # noqa: SLF001 - stable internal ownership for the current tier-B bridge

    def visibility_fn(eta: float) -> float:
        a_val = float(a_lookup(float(eta)))
        z_val = (1.0 / max(a_val, 1.0e-30)) - 1.0
        if z_val < interp.table.z_min or z_val > interp.table.z_max:
            return 0.0
        return float(interp.query_visibility(z_val))

    return visibility_fn


def _build_lowell_source_builder(result: IntegrationResult):
    eta_grid = np.asarray(result.eta, dtype=np.float64)
    theta_0 = np.asarray(result.pi_ell_m(0, 0), dtype=np.float64)
    pi_2 = {
        "m0": np.asarray(result.pi_ell_m(2, 0), dtype=np.float64),
        "m_plus2": np.asarray(result.pi_ell_m(2, 2), dtype=np.float64),
        "m_minus2": np.asarray(result.pi_ell_m(2, -2), dtype=np.float64),
    }

    def source_builder(eta: float, k: float) -> dict[str, float]:
        del k  # Tier-B low-ell bridge currently uses k-independent source amplitudes.
        return {
            "theta_0": _interp_series(eta_grid, theta_0, eta),
            "pi_m0": _interp_series(eta_grid, pi_2["m0"], eta),
            "pi_m_plus2": _interp_series(eta_grid, pi_2["m_plus2"], eta),
            "pi_m_minus2": _interp_series(eta_grid, pi_2["m_minus2"], eta),
        }

    return source_builder


def _build_template_from_result(
    result: IntegrationResult,
    propagator: SourcePropagator,
    *,
    kind: str,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "quadrupole_m0": float(result.pi_ell_m(2, 0)[-1]),
        "quadrupole_m_plus2": float(result.pi_ell_m(2, 2)[-1]),
        "quadrupole_m_minus2": float(result.pi_ell_m(2, -2)[-1]),
        "e2_m0": float(result.e_ell_m(2, 0)[-1]),
        "e2_m_plus2": float(result.e_ell_m(2, 2)[-1]),
        "e2_m_minus2": float(result.e_ell_m(2, -2)[-1]),
        "tca_active_fraction": float(np.mean(result.tca_active_mask.astype(np.float64))),
        "critical_events": {str(key): float(value) for key, value in result.critical_events.items()},
        "propagator_mode": propagator.config.mode.value,
        "offdiag_strategy": str(propagator.covariance_bundle.get("off_diagonal_strategy", "")),
    }


def build_solver_core_output_from_native_result(
    *,
    manifest: ArtifactManifest,
    bianchi_type: str,
    result: IntegrationResult,
    species: SpeciesBackgroundRegistry,
    runtime_controls: RuntimeControlBlock,
    feature_flags: SolverFeatureFlags,
    release: BassReleaseMetadata,
    k_grid_mpc: np.ndarray,
    structure: StructureConstants | None = None,
    propagator: SourcePropagatorConfig | None = None,
    thomson_mode: str = "electron_frame_projected",
    limber_eta_sp_sign: str = "integrator",
    off_diagonal_strategy: str = "m_decoupled_blocks",
) -> SolverCoreOutput:
    """Build an observer-neutral VER2 output from the native Tier-B core."""
    if runtime_controls.tier is not SolverTier.TIER_B_PSTF:
        raise ValueError(
            "build_solver_core_output_from_native_result requires Tier B runtime controls"
        )
    if runtime_controls.multipole_cutoff > result.L_max:
        raise ValueError(
            f"runtime cutoff L={runtime_controls.multipole_cutoff} exceeds result.L_max={result.L_max}"
        )
    if propagator is None and feature_flags.source_propagator.value == "disabled":
        raise ValueError(
            "build_solver_core_output_from_native_result requires a live source_propagator feature flag "
            "or an explicit propagator config"
        )
    structure_constants = get_type(bianchi_type) if structure is None else structure
    propagator_config = (
        SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            polarization_rotation=feature_flags.source_propagator,
            temperature_transport=feature_flags.source_propagator,
            flrw_validation_only=False,
            kernel_family="anisotropic_green_function",
            observer_frame=ObserverFrameMetadata(
                harmonic_basis="m_explicit",
                eb_sign_convention="cmb",
            ),
        )
        if propagator is None
        else propagator
    )

    a_lookup = lambda eta: _interp_series(
        np.asarray(result.eta, dtype=np.float64),
        np.asarray(result.a, dtype=np.float64),
        eta,
    )
    live_propagator = build_source_propagator(
        propagator_config,
        structure=structure_constants,
        eta_grid_mpc=np.asarray(result.eta, dtype=np.float64),
        k_grid_mpc=np.asarray(k_grid_mpc, dtype=np.float64),
        ell_max=int(runtime_controls.multipole_cutoff),
        visibility_fn=_build_visibility_fn_from_a_lookup(species, a_lookup),
        source_builder=_build_lowell_source_builder(result),
        limber_eta_sp_sign=limber_eta_sp_sign,
        off_diagonal_strategy=off_diagonal_strategy,
    )
    final_T = np.asarray(result.photon_T_tower[-1], dtype=np.float64)
    final_E = np.asarray(result.photon_E_tower[-1], dtype=np.float64)
    alm_representation = {
        "representation": "ver2_native_pstf_final_slice",
        "ell_max": int(result.L_max),
        "eta_final_mpc": float(result.eta[-1]),
    }
    return build_solver_core_output(
        manifest=manifest,
        bianchi_type=bianchi_type,
        tilt_enabled=bool(abs(result.config.tilt_rapidity) > 0.0),
        harmonic_basis=live_propagator.config.observer_frame.harmonic_basis,
        eb_sign_convention=live_propagator.config.observer_frame.eb_sign_convention,
        thomson_mode=thomson_mode,
        runtime_controls=runtime_controls,
        feature_flags=feature_flags,
        propagator=live_propagator.config,
        release=release,
        alm_T={**alm_representation, "values": final_T},
        alm_E={**alm_representation, "values": final_E},
        alm_B={**alm_representation, "values": np.zeros_like(final_E)},
        deterministic_template=_build_template_from_result(
            result,
            live_propagator,
            kind="tier_b_native_template",
        ),
        anisotropic_covariance=live_propagator.covariance_bundle,
        extra_metadata={
            "propagator_ready": True,
            "validation_reference": False,
            "k_grid_size": int(np.asarray(k_grid_mpc).size),
            "eta_grid_size": int(np.asarray(result.eta).size),
            "off_diagonal_strategy": off_diagonal_strategy,
            "limber_eta_sp_sign": limber_eta_sp_sign,
            "source_builder_scope": "theta0_plus_pi_quadrupole_ver2_native",
            "tier_b_core_owner": str(result.solver_info.get("tier_b_core_owner", "ver2_s1s2_native")),
            "solver_method": str(result.solver_info.get("solver_method", result.config.solver_method)),
            "solver_family_realization": str(result.solver_info.get("solver_family_realization", "runtime_family_direct")),
            "seed_k_comoving": float(result.solver_info.get("seed_k_comoving", 0.0)),
            "seed_injection_mode": str(result.solver_info.get("seed_injection_mode", "unknown")),
            "startup_manifold_applied": bool(result.solver_info.get("startup_manifold_applied", False)),
        },
    )


def build_solver_core_output_from_lowell_result(
    *,
    manifest: ArtifactManifest,
    bianchi_type: str,
    result: IntegrationResult,
    species: SpeciesBackgroundRegistry,
    runtime_controls: RuntimeControlBlock,
    feature_flags: SolverFeatureFlags,
    release: BassReleaseMetadata,
    k_grid_mpc: np.ndarray,
    structure: StructureConstants | None = None,
    propagator: SourcePropagatorConfig | None = None,
    thomson_mode: str = "electron_frame_projected",
    limber_eta_sp_sign: str = "integrator",
    off_diagonal_strategy: str = "m_decoupled_blocks",
) -> SolverCoreOutput:
    """Build an executable Tier-B neutral output from the current Lowell result.

    The bridge is intentionally bounded and research-grade: it packages the
    live Tier-B hierarchy output through the VER2 S3/O contracts without
    introducing posterior or observational ownership into BASS.
    """
    if runtime_controls.tier not in {SolverTier.TIER_B_PSTF, SolverTier.TIER_A_ANGULAR}:
        raise ValueError(
            "build_solver_core_output_from_lowell_result requires Tier A or Tier B runtime controls"
        )
    if runtime_controls.multipole_cutoff > result.L_max:
        raise ValueError(
            f"runtime cutoff L={runtime_controls.multipole_cutoff} exceeds result.L_max={result.L_max}"
        )
    if propagator is None and feature_flags.source_propagator.value == "disabled":
        raise ValueError(
            "build_solver_core_output_from_lowell_result requires a live source_propagator feature flag "
            "or an explicit propagator config"
        )
    structure_constants = get_type(bianchi_type) if structure is None else structure
    propagator_config = (
        SourcePropagatorConfig(
            mode=(
                PropagatorMode.ANISOTROPIC_FORWARD
                if runtime_controls.tier is SolverTier.TIER_B_PSTF
                else PropagatorMode.FLRW_VALIDATION
            ),
            polarization_rotation=(
                feature_flags.source_propagator
                if runtime_controls.tier is SolverTier.TIER_B_PSTF
                else FeatureStatus.DISABLED
            ),
            temperature_transport=(
                feature_flags.source_propagator
                if runtime_controls.tier is SolverTier.TIER_B_PSTF
                else FeatureStatus.EXACT
            ),
            flrw_validation_only=(runtime_controls.tier is SolverTier.TIER_A_ANGULAR),
            kernel_family=(
                "anisotropic_green_function"
                if runtime_controls.tier is SolverTier.TIER_B_PSTF
                else "flrw_scalar_validation"
            ),
            observer_frame=ObserverFrameMetadata(
                harmonic_basis=(
                    "m_explicit"
                    if runtime_controls.tier is SolverTier.TIER_B_PSTF
                    else "flrw_scalar_validation"
                ),
                eb_sign_convention="cmb",
            ),
        )
        if propagator is None
        else propagator
    )
    live_propagator = build_source_propagator(
        propagator_config,
        structure=structure_constants,
        eta_grid_mpc=np.asarray(result.eta, dtype=np.float64),
        k_grid_mpc=np.asarray(k_grid_mpc, dtype=np.float64),
        ell_max=int(runtime_controls.multipole_cutoff),
        visibility_fn=_build_visibility_fn_from_a_lookup(
            species,
            lambda eta: float(species.bg_table.interp_a(float(eta))),
        ),
        source_builder=_build_lowell_source_builder(result),
        limber_eta_sp_sign=limber_eta_sp_sign,
        off_diagonal_strategy=off_diagonal_strategy,
    )
    final_T = np.asarray(result.photon_T_tower[-1], dtype=np.float64)
    final_E = np.asarray(result.photon_E_tower[-1], dtype=np.float64)
    alm_representation = {
        "representation": (
            "lowell_pstf_final_slice"
            if runtime_controls.tier is SolverTier.TIER_B_PSTF
            else "tier_a_validation_reference_slice"
        ),
        "ell_max": int(result.L_max),
        "eta_final_mpc": float(result.eta[-1]),
    }
    return build_solver_core_output(
        manifest=manifest,
        bianchi_type=bianchi_type,
        tilt_enabled=bool(abs(result.config.tilt_rapidity) > 0.0),
        harmonic_basis=live_propagator.config.observer_frame.harmonic_basis,
        eb_sign_convention=live_propagator.config.observer_frame.eb_sign_convention,
        thomson_mode=thomson_mode,
        runtime_controls=runtime_controls,
        feature_flags=feature_flags,
        propagator=live_propagator.config,
        release=release,
        alm_T={**alm_representation, "values": final_T},
        alm_E={**alm_representation, "values": final_E},
        alm_B={**alm_representation, "values": np.zeros_like(final_E)},
        deterministic_template=_build_template_from_result(
            result,
            live_propagator,
            kind="tier_b_lowell_template",
        ),
        anisotropic_covariance=live_propagator.covariance_bundle,
        extra_metadata={
            "propagator_ready": True,
            "validation_reference": runtime_controls.tier is SolverTier.TIER_A_ANGULAR,
            "k_grid_size": int(np.asarray(k_grid_mpc).size),
            "eta_grid_size": int(np.asarray(result.eta).size),
            "off_diagonal_strategy": off_diagonal_strategy,
            "limber_eta_sp_sign": limber_eta_sp_sign,
            "source_builder_scope": "theta0_plus_pi_quadrupole_lowell_bridge",
        },
    )


def solver_core_output_to_payload(output: SolverCoreOutput) -> dict[str, Any]:
    """Return a JSON-ready payload for a neutral solver output."""
    return {
        "alm_T": output.alm_T,
        "alm_E": output.alm_E,
        "alm_B": output.alm_B,
        "map_T": output.map_T,
        "map_Q": output.map_Q,
        "map_U": output.map_U,
        "deterministic_template": output.deterministic_template,
        "anisotropic_covariance": output.anisotropic_covariance,
        "metadata": dict(output.metadata),
        "manifest": asdict(output.manifest),
    }


def solver_core_output_from_payload(payload: dict[str, Any]) -> SolverCoreOutput:
    """Reconstruct a `SolverCoreOutput` from a serialized payload."""
    manifest = ArtifactManifest(**payload["manifest"])
    return SolverCoreOutput(
        alm_T=payload.get("alm_T"),
        alm_E=payload.get("alm_E"),
        alm_B=payload.get("alm_B"),
        map_T=payload.get("map_T"),
        map_Q=payload.get("map_Q"),
        map_U=payload.get("map_U"),
        deterministic_template=payload.get("deterministic_template"),
        anisotropic_covariance=payload.get("anisotropic_covariance"),
        metadata=payload["metadata"],
        manifest=manifest,
    )
