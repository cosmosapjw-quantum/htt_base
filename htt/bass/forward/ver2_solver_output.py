"""VER2 observer-neutral solver-output builders for the BASS S3 lane."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import pi
from typing import Any, Callable, Mapping

import numpy as np

from common.contracts import ArtifactManifest, SolverCoreOutput

from bass.background.bianchi_types import StructureConstants, get_type
from bass.collision.polarization import PolarizationHierarchyState
from bass.hierarchy.boost_kernel import is_axis_aligned
from bass.hierarchy.pstf_radiation import (
    RadiationPSTFState,
    TruncationMetadata,
    reconstruct_on_sphere,
)
from bass.hierarchy.pstf_tensor import unpack_hierarchy, zero_hierarchy
from bass.hierarchy.integrator import IntegrationResult
from bass.los.ver2_source_propagator import (
    ObserverFrameMetadata,
    PropagatorMode,
    SourcePropagator,
    SourcePropagatorConfig,
    build_source_propagator,
    select_propagator_kernel_family,
)
from bass.runtime.ver2_execution import (
    FeatureStatus,
    IntegratorFamily,
    RuntimeControlBlock,
    SolverFeatureFlags,
    SolverTier,
)
from bass.recombination.recombination_ingest import find_visibility_peak
from bass.recombination.reionization import compute_reionization_tau
from bass.species.base import SpeciesLabel
from bass.species.massive_neutrino import MassiveNeutrinoBackground
from bass.species.registry import SpeciesBackgroundRegistry
from bass.validation import summarize_gate_status

__all__ = [
    "BassReleaseMetadata",
    "build_solver_core_output",
    "build_solver_core_output_from_native_result",
    "build_solver_core_output_from_lowell_result",
    "solver_core_output_to_payload",
    "solver_core_output_from_payload",
]


def _branch_name(*, tilt_enabled: bool) -> str:
    return "tilted" if bool(tilt_enabled) else "orthogonal"


def _base_interop_metadata(
    *,
    bianchi_type: str,
    tilt_enabled: bool,
) -> dict[str, Any]:
    branch = _branch_name(tilt_enabled=tilt_enabled)
    try:
        structure = get_type(bianchi_type)
    except Exception:  # pragma: no cover - defensive only
        structure = None
    return {
        "solver_domain_scope": "all_11_bianchi_types",
        "branch_contract": "explicit_orthogonal_vs_tilted",
        "bianchi_branch": branch,
        "bianchi_class_label": None if structure is None else ("A" if structure.is_class_a else "B"),
        "no_flrw_limit": None if structure is None else bool(structure.no_flrw_limit),
        "global_tilt_contract": (
            "model_matter_frame_state"
            if tilt_enabled
            else "orthogonal_branch_zero_global_tilt"
        ),
        "local_boost_contract": "observer_side_only_not_applied_in_bass_output",
        "local_boost_applied": False,
        "tilt_boost_separation": "explicit_nonmerged",
        "frame_split_contract": "transport_normal_tetrad_collision_electron_frame",
        "algebra_backend_contract": "tetrad_commutator_substitution",
        "constraint_backend_contract": "identity_derived_jacobi_ricci_gauss_codazzi_bianchi",
        "theory_family": f"{bianchi_type}_{branch}",
        "geometry_params": {
            "type_label": bianchi_type,
            "class_label": None if structure is None else ("A" if structure.is_class_a else "B"),
            "h_parameter": None
            if structure is None or abs(float(structure.h_parameter)) == 0.0
            else float(structure.h_parameter),
            "no_flrw_limit": None if structure is None else bool(structure.no_flrw_limit),
        },
        "kinematic_params": {
            "branch": branch,
            "global_tilt_enabled": bool(tilt_enabled),
            "local_boost_applied": False,
            "local_boost_contract": "observer_side_only_not_applied_in_bass_output",
        },
        "tilt_params": {
            "branch": branch,
            "enabled": bool(tilt_enabled),
            "rapidity": None,
            "direction": None,
            "contract": (
                "global_tilt_matter_frame"
                if tilt_enabled
                else "orthogonal_branch_zero_global_tilt"
            ),
        },
    }


def _structure_metadata(
    *,
    structure: StructureConstants,
    tilt_enabled: bool,
    tilt_rapidity: float,
    tilt_direction: tuple[float, float, float],
) -> dict[str, Any]:
    branch = _branch_name(tilt_enabled=tilt_enabled)
    return {
        "bianchi_class_label": "A" if structure.is_class_a else "B",
        "bianchi_h_parameter": None if abs(float(structure.h_parameter)) == 0.0 else float(structure.h_parameter),
        "no_flrw_limit": bool(structure.no_flrw_limit),
        "geometry_params": {
            "type_label": str(structure.label),
            "class_label": "A" if structure.is_class_a else "B",
            "n1": float(structure.n1),
            "n2": float(structure.n2),
            "n3": float(structure.n3),
            "a_twist": float(structure.a_twist),
            "h_parameter": None if abs(float(structure.h_parameter)) == 0.0 else float(structure.h_parameter),
            "no_flrw_limit": bool(structure.no_flrw_limit),
        },
        "kinematic_params": {
            "branch": branch,
            "global_tilt_enabled": bool(tilt_enabled),
            "global_tilt_rapidity": float(tilt_rapidity),
            "global_tilt_direction": tuple(float(x) for x in tilt_direction),
            "local_boost_applied": False,
            "local_boost_contract": "observer_side_only_not_applied_in_bass_output",
        },
        "tilt_params": {
            "branch": branch,
            "enabled": bool(tilt_enabled),
            "rapidity": float(tilt_rapidity),
            "direction": tuple(float(x) for x in tilt_direction),
            "contract": (
                "global_tilt_matter_frame"
                if tilt_enabled
                else "orthogonal_branch_zero_global_tilt"
            ),
        },
    }


def _default_solver_resolution(
    runtime_controls: RuntimeControlBlock,
) -> tuple[str, str]:
    family = runtime_controls.integrator_family
    if family is IntegratorFamily.IMPLICIT_BDF:
        return "BDF", "runtime_family_direct"
    if family is IntegratorFamily.IMPLICIT_RADAU:
        return "Radau", "runtime_family_direct"
    if family is IntegratorFamily.EXPLICIT_RK:
        return "RK45", "runtime_family_direct"
    if family is IntegratorFamily.IMEX_SPLIT:
        return "IMEX_MIDPOINT_BDF", "native_imex_midpoint_bdf_split"
    raise ValueError(f"unsupported integrator_family {family!r}")


def _propagator_readiness(
    propagator: SourcePropagatorConfig,
    feature_flags: SolverFeatureFlags,
) -> str:
    if feature_flags.source_propagator is FeatureStatus.DISABLED:
        return "contract_only_unavailable"
    if propagator.temperature_transport is FeatureStatus.DISABLED:
        return "contract_only_unavailable"
    if propagator.kernel_family == "bianchi_i_matrix_exact":
        return "exact"
    if propagator.kernel_family == "flrw_scalar_validation":
        return "contract_only_unavailable"
    return "approximate_family_kernel"


def _native_propagator_readiness(
    *,
    propagator: SourcePropagatorConfig,
    feature_flags: SolverFeatureFlags,
    gate_registry: Mapping[str, object] | None,
    mode_ops: object | None,
) -> str:
    fallback = _propagator_readiness(propagator, feature_flags)
    if mode_ops is None:
        return fallback
    mode_ops_metadata = dict(getattr(mode_ops, "metadata", {}))
    gate_status = {} if gate_registry is None else summarize_gate_status(gate_registry)
    required_gates = (
        "tilt_boost_separation_gate",
        "ic_provenance_gate",
        "family_backend_gate",
        "hierarchy_layout_gate",
    )
    if gate_status and any(gate_status.get(gate) != "open" for gate in required_gates):
        return "contract_only_unavailable"
    if (
        mode_ops_metadata.get("lookup_resolution_status") != "frozen_v5_formula_set"
        or not bool(mode_ops_metadata.get("verification_crosscheck_pass", False))
    ):
        return "contract_only_unavailable"
    exact_kernel = str(getattr(mode_ops, "operator_kernel_family", "")) == "bianchi_i_matrix_exact"
    exact_layout = bool(
        getattr(mode_ops, "layout_metadata", {}).get("exact_family_operator_available", False)
    )
    if fallback == "exact" and exact_kernel and exact_layout:
        return "exact"
    if feature_flags.source_propagator is FeatureStatus.DISABLED:
        return "contract_only_unavailable"
    return "approximate_family_kernel"


def _base_covariance_readiness(anisotropic_covariance: object | None) -> str:
    return "proxy" if anisotropic_covariance is not None else "missing"


def _neutrino_runtime_metadata(
    species: SpeciesBackgroundRegistry,
) -> dict[str, object]:
    neutrino = species[SpeciesLabel.NEUTRINO]
    if isinstance(neutrino, MassiveNeutrinoBackground) and neutrino.mass_eV > 0.0:
        return {
            "neutrino_background_readiness": "massive_fd_background_and_hierarchy",
            "massive_neutrino_support": True,
            "massive_neutrino_block_reason": None,
            "massive_neutrino_mass_eV": float(neutrino.mass_eV),
        }
    readiness = str(getattr(neutrino, "background_readiness", "massless_only"))
    supported = bool(getattr(neutrino, "massive_neutrino_supported", False))
    return {
        "neutrino_background_readiness": readiness,
        "massive_neutrino_support": supported,
        "massive_neutrino_block_reason": (
            None if supported else "massive_neutrino_background_not_implemented"
        ),
        "massive_neutrino_mass_eV": 0.0,
    }


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
    gate_registry: Mapping[str, object] | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> SolverCoreOutput:
    """Build the canonical observer-neutral `SolverCoreOutput` shell."""
    if manifest.owner != "BASS":
        raise ValueError("SolverCoreOutput manifests must be owned by BASS")
    resolved_solver_method, executor_realization = _default_solver_resolution(
        runtime_controls
    )
    propagator_readiness = _propagator_readiness(propagator, feature_flags)
    metadata = {
        "bianchi_type": bianchi_type,
        "harmonic_basis": harmonic_basis,
        "eb_sign_convention": eb_sign_convention,
        "multipole_cutoff": runtime_controls.multipole_cutoff,
        "tilt_enabled": tilt_enabled,
        "thomson_mode": thomson_mode,
        "solver_tier": runtime_controls.tier.value,
        "integrator_family": runtime_controls.integrator_family.value,
        "requested_integrator_family": runtime_controls.integrator_family.value,
        "resolved_solver_method": resolved_solver_method,
        "executor_realization": executor_realization,
        "coupling_mode": runtime_controls.coupling_mode.value,
        "propagator_mode": propagator.mode.value,
        "propagator_readiness": propagator_readiness,
        "propagator_exactness": propagator_readiness,
        "covariance_readiness": _base_covariance_readiness(anisotropic_covariance),
        "feature_flags": {key: value.value for key, value in asdict(feature_flags).items()},
        "release_stage": release.release_stage,
        "run_label": release.run_label,
        "observer_neutral": True,
        "forbidden_products": ("posterior", "likelihood", "p_value"),
        "tilt_background_owner": runtime_controls.tilt_background_owner,
        "tilt_background_owner_status": (
            "production_dynamic_nonperturbative_rapidity"
            if runtime_controls.tilt_background_owner == "nonperturbative_tilt_rhs"
            else "production_policy_fixed_velocity_closure"
        ),
        "nonperturbative_tilt_rhs_status": (
            "runtime_wired_dynamic_rapidity_owner"
            if runtime_controls.tilt_background_owner == "nonperturbative_tilt_rhs"
            else "research_contract_only"
        ),
        "off_axis_support": False,
        "axis_aligned_tilt_support": True,
        "off_axis_fallback_applied": False,
        "off_axis_block_reason": "off_axis_not_closed",
        "reionization_history_readiness": "homogeneous_tanh_only",
        "reionization_anisotropy_support": False,
        "reionization_block_reason": "anisotropic_reionization_not_implemented",
        "neutrino_background_readiness": "massless_only",
        "massive_neutrino_support": False,
        "massive_neutrino_block_reason": "massive_neutrino_background_not_implemented",
        **_base_interop_metadata(
            bianchi_type=bianchi_type,
            tilt_enabled=tilt_enabled,
        ),
    }
    if gate_registry is not None:
        metadata["gate_registry"] = dict(gate_registry)
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


def _interp_redshift_series(a_grid: np.ndarray, values: np.ndarray, z: float) -> float | None:
    target_a = 1.0 / (1.0 + float(z))
    a = np.asarray(a_grid, dtype=np.float64)
    series = np.asarray(values, dtype=np.float64)
    a_min = float(np.min(a))
    a_max = float(np.max(a))
    tol = max(abs(a_max) * 2.0e-8, 1.0e-12)
    if target_a < a_min - tol or target_a > a_max + tol:
        return None
    target_clipped = min(max(target_a, a_min), a_max)
    return float(np.interp(target_clipped, a, series))


def _build_visibility_source_metadata(
    result: IntegrationResult,
    *,
    species: SpeciesBackgroundRegistry,
    visibility_fn: Callable[[float], float],
    gpi_m0: np.ndarray,
) -> dict[str, Any]:
    baryon = species[SpeciesLabel.BARYON]
    interp = baryon._recomb  # noqa: SLF001 - stable internal ownership for the current tier-B bridge
    table = interp.table
    reionization_mode = "tanh" if table.metadata.get("reionization") == "tanh" else "disabled"
    tau_reion = (
        float(compute_reionization_tau(table, z_high_cutoff=min(30.0, float(table.z_max))))
        if reionization_mode == "tanh"
        else 0.0
    )
    visibility_peak_z, _ = find_visibility_peak(interp)
    visibility_peak_gpi_m0 = _interp_redshift_series(
        np.asarray(result.a, dtype=np.float64),
        np.asarray(gpi_m0, dtype=np.float64),
        float(visibility_peak_z),
    )
    low_z_probe = 8.0
    low_z_gpi_m0 = _interp_redshift_series(
        np.asarray(result.a, dtype=np.float64),
        np.asarray(gpi_m0, dtype=np.float64),
        low_z_probe,
    )
    low_z_eta = _interp_redshift_series(
        np.asarray(result.a, dtype=np.float64),
        np.asarray(result.eta, dtype=np.float64),
        low_z_probe,
    )
    low_z_visibility = (
        float(visibility_fn(float(low_z_eta)))
        if low_z_eta is not None
        else None
    )
    low_z_probe_available = low_z_gpi_m0 is not None
    if low_z_probe_available:
        low_z_probe_status = "available"
    else:
        low_z_probe_status = "not_covered_by_runtime_domain"
    if reionization_mode != "tanh":
        reionization_source_claim_status = "reionization_disabled"
    elif low_z_probe_available:
        reionization_source_claim_status = "bounded_live_low_z_delta"
    else:
        reionization_source_claim_status = "unavailable_due_to_runtime_domain"
    return {
        "source_builder_combined_polter": True,
        "source_builder_visibility_weighted_polter": True,
        "visibility_reionization_mode": reionization_mode,
        "visibility_reionization_detected": bool(reionization_mode == "tanh" and tau_reion > 0.0),
        "visibility_tau_reion": tau_reion,
        "visibility_peak_z": float(visibility_peak_z),
        "source_builder_visibility_peak_gpi_m0": visibility_peak_gpi_m0,
        "source_builder_low_z_probe_z": low_z_probe,
        "source_builder_low_z_probe_available": low_z_probe_available,
        "source_builder_low_z_probe_status": low_z_probe_status,
        "source_builder_low_z_visibility": low_z_visibility,
        "source_builder_low_z_gpi_m0": low_z_gpi_m0,
        "reionization_source_claim_status": reionization_source_claim_status,
    }


def _build_lowell_source_builder(
    result: IntegrationResult,
    *,
    species: SpeciesBackgroundRegistry,
    visibility_fn: Callable[[float], float],
):
    eta_grid = np.asarray(result.eta, dtype=np.float64)
    theta_0 = np.asarray(result.pi_ell_m(0, 0), dtype=np.float64)
    theta_2 = {
        "m0": np.asarray(result.pi_ell_m(2, 0), dtype=np.float64),
        "m_plus2": np.asarray(result.pi_ell_m(2, 2), dtype=np.float64),
        "m_minus2": np.asarray(result.pi_ell_m(2, -2), dtype=np.float64),
    }
    e_2 = {
        "m0": np.asarray(result.e_ell_m(2, 0), dtype=np.float64),
        "m_plus2": np.asarray(result.e_ell_m(2, 2), dtype=np.float64),
        "m_minus2": np.asarray(result.e_ell_m(2, -2), dtype=np.float64),
    }
    polter = {
        name: np.asarray(theta_2[name] - np.sqrt(6.0) * e_2[name], dtype=np.float64)
        for name in theta_2
    }
    visibility = np.asarray([float(visibility_fn(float(eta))) for eta in eta_grid], dtype=np.float64)
    gpi = {
        name: visibility * polter[name]
        for name in polter
    }

    def source_builder(eta: float, k: float) -> dict[str, float]:
        del k  # Tier-B low-ell bridge currently uses k-independent source amplitudes.
        return {
            "theta_0": _interp_series(eta_grid, theta_0, eta),
            "theta_2_m0": _interp_series(eta_grid, theta_2["m0"], eta),
            "theta_2_m_plus2": _interp_series(eta_grid, theta_2["m_plus2"], eta),
            "theta_2_m_minus2": _interp_series(eta_grid, theta_2["m_minus2"], eta),
            "E_2_m0": _interp_series(eta_grid, e_2["m0"], eta),
            "E_2_m_plus2": _interp_series(eta_grid, e_2["m_plus2"], eta),
            "E_2_m_minus2": _interp_series(eta_grid, e_2["m_minus2"], eta),
            "pi_m0": _interp_series(eta_grid, polter["m0"], eta),
            "pi_m_plus2": _interp_series(eta_grid, polter["m_plus2"], eta),
            "pi_m_minus2": _interp_series(eta_grid, polter["m_minus2"], eta),
            "gpi_m0": _interp_series(eta_grid, gpi["m0"], eta),
            "gpi_m_plus2": _interp_series(eta_grid, gpi["m_plus2"], eta),
            "gpi_m_minus2": _interp_series(eta_grid, gpi["m_minus2"], eta),
        }

    return source_builder, _build_visibility_source_metadata(
        result,
        species=species,
        visibility_fn=visibility_fn,
        gpi_m0=gpi["m0"],
    )


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


def _tensor_product_sphere_rule(L: int) -> tuple[np.ndarray, np.ndarray]:
    """Deterministic tensor-product sphere rule exact for polynomial content up to `L`."""
    mu, mu_weights = np.polynomial.legendre.leggauss(2 * L + 3)
    n_phi = 4 * L + 5
    phi = np.linspace(0.0, 2.0 * pi, n_phi, endpoint=False, dtype=np.float64)
    directions: list[list[float]] = []
    weights: list[float] = []
    for mu_i, w_i in zip(mu, mu_weights):
        sin_theta = float(np.sqrt(max(0.0, 1.0 - float(mu_i) * float(mu_i))))
        for phi_j in phi:
            directions.append(
                [
                    sin_theta * float(np.cos(phi_j)),
                    sin_theta * float(np.sin(phi_j)),
                    float(mu_i),
                ]
            )
            weights.append(float(w_i) * (2.0 * pi / float(n_phi)))
    return np.asarray(directions, dtype=np.float64), np.asarray(weights, dtype=np.float64)


def _final_slice_radiation_state(
    result: IntegrationResult,
    *,
    b_coefficients: np.ndarray | None = None,
) -> RadiationPSTFState:
    L = int(result.L_max)
    return RadiationPSTFState(
        I=unpack_hierarchy(np.asarray(result.photon_T_tower[-1], dtype=np.float64), L),
        E=PolarizationHierarchyState(
            E=unpack_hierarchy(np.asarray(result.photon_E_tower[-1], dtype=np.float64), L)
        ),
        B=(
            zero_hierarchy(L)
            if b_coefficients is None
            else unpack_hierarchy(np.asarray(b_coefficients, dtype=np.float64), L)
        ),
        truncation=TruncationMetadata(
            L=L,
            allow_L2_override=(L == 2),
            closure_name="ver2_runtime_final_slice_reconstruction",
        ),
    )


def _build_reconstructed_channel_payload(
    coefficient_values: np.ndarray,
    sphere_samples: np.ndarray,
    directions: np.ndarray,
    weights: np.ndarray,
    *,
    representation: str,
    coefficient_representation: str,
    eta_final_mpc: float,
    ell_max: int,
    component_status: str,
    available: bool,
) -> dict[str, Any]:
    return {
        "representation": representation,
        "coefficient_representation": coefficient_representation,
        "ell_max": int(ell_max),
        "eta_final_mpc": float(eta_final_mpc),
        "component_status": component_status,
        "available": bool(available),
        "quadrature_rule": "gauss_legendre_x_uniform_phi_tensor_product",
        "quadrature_exactness_contract": f"polynomial_exact_up_to_L={int(ell_max)}",
        "values": np.asarray(coefficient_values, dtype=np.float64),
        "sphere_directions": np.asarray(directions, dtype=np.float64),
        "sphere_weights": np.asarray(weights, dtype=np.float64),
        "sphere_samples": np.asarray(sphere_samples, dtype=np.float64),
    }


def _build_reconstructed_payloads(
    result: IntegrationResult,
    *,
    coefficient_representation: str,
    angular_representation: str,
    b_mode_coefficients: np.ndarray | None = None,
    b_mode_payload_available: bool = False,
    b_mode_component_status: str = "zero_filled_layout_contract_only",
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    state = _final_slice_radiation_state(result, b_coefficients=b_mode_coefficients)
    directions, weights = _tensor_product_sphere_rule(int(result.L_max))
    samples = reconstruct_on_sphere(state, directions)
    eta_final = float(result.eta[-1])
    ell_max = int(result.L_max)
    return (
        _build_reconstructed_channel_payload(
            np.asarray(result.photon_T_tower[-1], dtype=np.float64),
            np.asarray(samples["I"], dtype=np.float64),
            directions,
            weights,
            representation=angular_representation,
            coefficient_representation=coefficient_representation,
            eta_final_mpc=eta_final,
            ell_max=ell_max,
            component_status="runtime_evolved",
            available=True,
        ),
        _build_reconstructed_channel_payload(
            np.asarray(result.photon_E_tower[-1], dtype=np.float64),
            np.asarray(samples["E"], dtype=np.float64),
            directions,
            weights,
            representation=angular_representation,
            coefficient_representation=coefficient_representation,
            eta_final_mpc=eta_final,
            ell_max=ell_max,
            component_status="runtime_evolved",
            available=True,
        ),
        _build_reconstructed_channel_payload(
            (
                np.zeros_like(np.asarray(result.photon_E_tower[-1], dtype=np.float64))
                if b_mode_coefficients is None
                else np.asarray(b_mode_coefficients, dtype=np.float64)
            ),
            np.asarray(samples["B"], dtype=np.float64),
            directions,
            weights,
            representation=angular_representation,
            coefficient_representation=coefficient_representation,
            eta_final_mpc=eta_final,
            ell_max=ell_max,
            component_status=str(b_mode_component_status),
            available=bool(b_mode_payload_available),
        ),
    )


def _default_tier_b_propagator_config(
    *,
    structure: StructureConstants,
    requested_status: FeatureStatus,
) -> SourcePropagatorConfig:
    if structure.label == "I":
        return SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            polarization_rotation=FeatureStatus.DISABLED,
            temperature_transport=FeatureStatus.EXACT,
            flrw_validation_only=False,
            kernel_family="bianchi_i_matrix_exact",
            observer_frame=ObserverFrameMetadata(
                harmonic_basis="m_explicit",
                eb_sign_convention="cmb",
            ),
        )
    return SourcePropagatorConfig(
        mode=PropagatorMode.ANISOTROPIC_FORWARD,
        polarization_rotation=requested_status,
        temperature_transport=requested_status,
        flrw_validation_only=False,
        kernel_family=select_propagator_kernel_family(structure),
        observer_frame=ObserverFrameMetadata(
            harmonic_basis="m_explicit",
            eb_sign_convention="cmb",
        ),
    )


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
    gate_registry: Mapping[str, object] | None = None,
    mode_ops: object | None = None,
    seed_pack: object | None = None,
    canonical_projection: object | None = None,
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
    if (
        propagator is None
        and feature_flags.source_propagator is FeatureStatus.EXACT
        and structure_constants.label != "I"
    ):
        raise ValueError(
            "Tier-B exact source propagation requires an explicit propagator config; "
            "the default native bridge remains an approximate FLRW-kernel carry path."
        )
    propagator_config = (
        _default_tier_b_propagator_config(
            structure=structure_constants,
            requested_status=feature_flags.source_propagator,
        )
        if propagator is None
        else propagator
    )

    a_lookup = lambda eta: _interp_series(
        np.asarray(result.eta, dtype=np.float64),
        np.asarray(result.a, dtype=np.float64),
        eta,
    )
    visibility_fn = _build_visibility_fn_from_a_lookup(species, a_lookup)
    source_builder, source_builder_metadata = _build_lowell_source_builder(
        result,
        species=species,
        visibility_fn=visibility_fn,
    )
    live_propagator = build_source_propagator(
        propagator_config,
        structure=structure_constants,
        eta_grid_mpc=np.asarray(result.eta, dtype=np.float64),
        k_grid_mpc=np.asarray(k_grid_mpc, dtype=np.float64),
        ell_max=int(runtime_controls.multipole_cutoff),
        visibility_fn=visibility_fn,
        source_builder=source_builder,
        limber_eta_sp_sign=limber_eta_sp_sign,
        off_diagonal_strategy=off_diagonal_strategy,
    )
    b_mode_payload_status = "zero_filled_layout_contract_only"
    b_mode_payload_available = False
    b_mode_runtime_available = False
    b_mode_coefficients = None
    if canonical_projection is not None:
        b_mode_coefficients = np.asarray(
            getattr(canonical_projection, "hierarchy_state").photon_polarization_block.get("B"),
            dtype=np.float64,
        )
        b_mode_sector_status = str(getattr(canonical_projection, "sector_status", {}).get("ph_B", ""))
        if (
            b_mode_sector_status == "layout_operator_auxiliary_b_mode_history"
            and np.any(np.abs(b_mode_coefficients) > 0.0)
        ):
            b_mode_payload_status = b_mode_sector_status
            b_mode_payload_available = True
            b_mode_runtime_available = True
    alm_T, alm_E, alm_B = _build_reconstructed_payloads(
        result,
        coefficient_representation="ver2_native_pstf_final_slice",
        angular_representation="ver2_native_pstf_sphere_reconstruction",
        b_mode_coefficients=b_mode_coefficients,
        b_mode_payload_available=b_mode_payload_available,
        b_mode_component_status=b_mode_payload_status,
    )
    tilt_direction = tuple(float(x) for x in result.config.tilt_direction)
    off_axis_supported = bool(
        abs(float(result.config.tilt_rapidity)) > 0.0
        and not is_axis_aligned(tilt_direction)
    )
    output = build_solver_core_output(
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
        alm_T=alm_T,
        alm_E=alm_E,
        alm_B=alm_B,
        deterministic_template=_build_template_from_result(
            result,
            live_propagator,
            kind="tier_b_native_template",
        ),
        anisotropic_covariance=live_propagator.covariance_bundle,
        gate_registry=gate_registry,
        extra_metadata={
            **_structure_metadata(
                structure=structure_constants,
                tilt_enabled=bool(abs(result.config.tilt_rapidity) > 0.0),
                tilt_rapidity=float(result.config.tilt_rapidity),
                tilt_direction=tilt_direction,
            ),
            "propagator_ready": True,
            "validation_reference": False,
            "k_grid_size": int(np.asarray(k_grid_mpc).size),
            "eta_grid_size": int(np.asarray(result.eta).size),
            "off_diagonal_strategy": off_diagonal_strategy,
            "limber_eta_sp_sign": limber_eta_sp_sign,
            "source_builder_scope": "theta0_plus_combined_polter_visibility_ver2_native",
            "source_propagator_status": live_propagator.config.temperature_transport.value,
            "source_propagator_requested_status": feature_flags.source_propagator.value,
            "source_propagator_rotation_status": live_propagator.config.polarization_rotation.value,
            "source_propagator_realization": live_propagator.config.kernel_family,
            "requested_integrator_family": str(
                result.solver_info.get(
                    "requested_integrator_family",
                    runtime_controls.integrator_family.value,
                )
            ),
            "tier_b_core_owner": str(result.solver_info.get("tier_b_core_owner", "ver2_s1s2_native")),
            "solver_method": str(
                result.solver_info.get("solver_method", result.config.solver_method)
            ),
            "resolved_solver_method": str(
                result.solver_info.get(
                    "resolved_solver_method",
                    result.solver_info.get("solver_method", result.config.solver_method),
                )
            ),
            "executor_realization": str(
                result.solver_info.get(
                    "executor_realization",
                    result.solver_info.get(
                        "solver_family_realization",
                        "runtime_family_direct",
                    ),
                )
            ),
            "solver_family_realization": str(
                result.solver_info.get("solver_family_realization", "runtime_family_direct")
            ),
            "neutrino_hierarchy_mode": str(result.solver_info.get("neutrino_hierarchy_mode", "reduced_summary_only")),
            "layout_operator_consumed": bool(result.solver_info.get("layout_operator_consumed", False)),
            "layout_initial_mode_ops_owner": str(
                result.solver_info.get("layout_initial_mode_ops_owner", "unconsumed")
            ),
            "layout_collision_operator_source": str(
                result.solver_info.get(
                    "layout_collision_operator_source",
                    "gamma_t_scalar_fallback",
                )
            ),
            "layout_source_template_consumed": bool(
                result.solver_info.get("layout_source_template_consumed", False)
            ),
            "layout_source_template_channel": str(
                result.solver_info.get(
                    "layout_source_template_channel",
                    "disabled",
                )
            ),
            "layout_source_block_norm": float(
                result.solver_info.get("layout_source_block_norm", 0.0)
            ),
            "layout_source_block_owner": str(
                result.solver_info.get("layout_source_block_owner", "unconsumed")
            ),
            "layout_source_history_sample_count": int(
                result.solver_info.get("layout_source_history_sample_count", 0)
            ),
            "layout_source_mode_labels": list(
                result.solver_info.get("layout_source_mode_labels", [])
            ),
            "layout_local_matter_blocks_consumed": bool(
                result.solver_info.get("layout_local_matter_blocks_consumed", False)
            ),
            "layout_local_matter_owner": str(
                result.solver_info.get("layout_local_matter_owner", "unconsumed")
            ),
            "layout_local_matter_sample_count": int(
                result.solver_info.get("layout_local_matter_sample_count", 0)
            ),
            "layout_local_matter_reference_owner": str(
                result.solver_info.get("layout_local_matter_reference_owner", "unavailable")
            ),
            "layout_local_matter_reference_sample_count": int(
                result.solver_info.get("layout_local_matter_reference_sample_count", 0)
            ),
            "layout_local_matter_reference_delta_norm": float(
                result.solver_info.get("layout_local_matter_reference_delta_norm", 0.0)
            ),
            "layout_b_mode_proxy_consumed": bool(
                result.solver_info.get("layout_b_mode_proxy_consumed", False)
            ),
            "layout_b_mode_proxy_norm": float(
                result.solver_info.get("layout_b_mode_proxy_norm", 0.0)
            ),
            "layout_b_mode_proxy_source": str(
                result.solver_info.get("layout_b_mode_proxy_source", "disabled")
            ),
            "layout_b_mode_history_sample_count": int(
                result.solver_info.get("layout_b_mode_history_sample_count", 0)
            ),
            "layout_auxiliary_coupling_passes": int(
                result.solver_info.get("layout_auxiliary_coupling_passes", 0)
            ),
            "layout_auxiliary_bundle_owner": str(
                result.solver_info.get("layout_auxiliary_bundle_owner", "unconsumed")
            ),
            "layout_projection_owner": str(
                result.solver_info.get("layout_projection_owner", "unconsumed")
            ),
            "seed_k_comoving": float(result.solver_info.get("seed_k_comoving", 0.0)),
            "seed_injection_mode": str(result.solver_info.get("seed_injection_mode", "unknown")),
            "seed_factory_owner": str(result.solver_info.get("seed_factory_owner", "legacy_runtime_seed")),
            "seed_factory_mode": result.solver_info.get("seed_factory_mode"),
            "seed_chart": result.solver_info.get("seed_chart"),
            "seed_family": result.solver_info.get("seed_family"),
            "seed_branch": result.solver_info.get("seed_branch"),
            "seed_pack_metadata": dict(result.solver_info.get("seed_pack_metadata", {})),
            "seed_pack_normalization": dict(result.solver_info.get("seed_pack_normalization", {})),
            "startup_manifold_applied": bool(result.solver_info.get("startup_manifold_applied", False)),
            "checkpoint_enabled": bool(result.solver_info.get("checkpoint_enabled", False)),
            "checkpoint_write_count": int(result.solver_info.get("checkpoint_write_count", 0)),
            "restart_used": bool(result.solver_info.get("restart_used", False)),
            "restart_checkpoint_path": result.solver_info.get("restart_checkpoint_path"),
            "off_axis_support": off_axis_supported,
            "axis_aligned_tilt_support": True,
            "off_axis_fallback_applied": False,
            "off_axis_block_reason": None if off_axis_supported else "off_axis_not_closed",
            "canonical_sector_order_contract": ("ph_I", "ph_E", "ph_B", "nu_I", "baryon", "cdm", "src"),
            "runtime_resolved_sector_order": (
                ("ph_I", "ph_E", "nu_I")
                if canonical_projection is None
                else tuple(
                    getattr(canonical_projection, "metadata", {}).get(
                        "resolved_sector_order",
                        ("ph_I", "ph_E", "nu_I"),
                    )
                )
            ),
            "b_mode_runtime_available": bool(b_mode_runtime_available),
            "b_mode_payload_available": bool(b_mode_payload_available),
            "b_mode_payload_status": str(b_mode_payload_status),
            "layout_contract_consumed": bool(
                result.solver_info.get("layout_contract_consumed", mode_ops is not None)
            ),
            "layout_mode_labels": list(result.solver_info.get("layout_mode_labels", []))
            if "layout_mode_labels" in result.solver_info
            else (
                []
                if mode_ops is None
                else list(getattr(mode_ops, "layout_metadata", {}).get("mode_labels", []))
            ),
            "layout_sector_order": list(result.solver_info.get("layout_sector_order", []))
            if "layout_sector_order" in result.solver_info
            else (
                []
                if mode_ops is None
                else list(getattr(mode_ops, "layout_metadata", {}).get("sector_order", []))
            ),
            "layout_operator_kernel_family": result.solver_info.get("layout_operator_kernel_family")
            if "layout_operator_kernel_family" in result.solver_info
            else (
                None
                if mode_ops is None
                else str(getattr(mode_ops, "operator_kernel_family", ""))
            ),
            "seed_provenance_mode": result.solver_info.get("seed_provenance_mode")
            if "seed_provenance_mode" in result.solver_info
            else (
                None
                if mode_ops is None
                else str(getattr(mode_ops, "seed_provenance_mode", ""))
            ),
            "backend_lookup_resolution_status": None
            if mode_ops is None
            else str(getattr(mode_ops, "metadata", {}).get("lookup_resolution_status", "")),
            "backend_verification_crosscheck_pass": bool(
                False
                if mode_ops is None
                else getattr(mode_ops, "metadata", {}).get("verification_crosscheck_pass", False)
            ),
            "backend_verification_reference": None
            if mode_ops is None
            else getattr(mode_ops, "metadata", {}).get("verification_reference"),
            "backend_operator_payload_status": None
            if mode_ops is None
            else getattr(mode_ops, "metadata", {}).get("operator_payload_status"),
            "backend_contract_release_status": None
            if mode_ops is None
            else getattr(mode_ops, "metadata", {}).get("contract_release_status"),
            "ic_provenance_status": None
            if seed_pack is None
            else str(getattr(seed_pack, "seed_mode", "")),
            "canonical_projection_available": bool(canonical_projection is not None),
            "canonical_projection_mode": None
            if canonical_projection is None
            else str(getattr(canonical_projection, "metadata", {}).get("projection_mode")),
            "canonical_projection_state_size": None
            if canonical_projection is None
            else int(np.asarray(getattr(canonical_projection, "state_vector")).size),
            "canonical_projection_covered_mode_labels": []
            if canonical_projection is None
            else list(getattr(canonical_projection, "covered_mode_labels", ())),
            "canonical_projection_zero_filled_mode_labels": []
            if canonical_projection is None
            else list(getattr(canonical_projection, "zero_filled_mode_labels", ())),
            "canonical_projection_sector_status": {}
            if canonical_projection is None
            else dict(getattr(canonical_projection, "sector_status", {})),
            "canonical_projection_b_history_available": False
            if canonical_projection is None
            else bool(getattr(canonical_projection, "metadata", {}).get("b_history_available", False)),
            "canonical_projection_b_history_sample_count": 0
            if canonical_projection is None
            else int(getattr(canonical_projection, "metadata", {}).get("b_history_sample_count", 0)),
            "canonical_projection_source_mode_labels": []
            if canonical_projection is None
            else list(getattr(canonical_projection, "metadata", {}).get("source_mode_labels", ())),
            "canonical_projection_source_history_mode_labels": []
            if canonical_projection is None
            else list(
                getattr(canonical_projection, "metadata", {}).get("source_history_mode_labels", ())
            ),
            "canonical_projection_matter_labels": {}
            if canonical_projection is None
            else dict(getattr(canonical_projection, "metadata", {}).get("matter_block_labels", {})),
            **_neutrino_runtime_metadata(species),
            **source_builder_metadata,
        },
    )
    readiness = _native_propagator_readiness(
        propagator=live_propagator.config,
        feature_flags=feature_flags,
        gate_registry=gate_registry,
        mode_ops=mode_ops,
    )
    output.metadata["propagator_readiness"] = readiness
    output.metadata["propagator_exactness"] = readiness
    output.metadata["propagator_ready"] = readiness != "contract_only_unavailable"
    from bass.forward.ver3_output_archive import resolve_output_gate_registry

    output.metadata["gate_registry"] = resolve_output_gate_registry(
        output,
        gate_registry=gate_registry,
    )
    return output


def build_solver_core_output_from_execution_bundle(
    *,
    manifest: ArtifactManifest,
    bianchi_type: str,
    result: IntegrationResult,
    species: SpeciesBackgroundRegistry,
    runtime_controls: RuntimeControlBlock,
    feature_flags: SolverFeatureFlags,
    release: BassReleaseMetadata,
    k_grid_mpc: np.ndarray,
    runtime_trace,
    gate_registry: Mapping[str, object] | None = None,
    structure: StructureConstants | None = None,
    propagator: SourcePropagatorConfig | None = None,
    thomson_mode: str = "electron_frame_projected",
    limber_eta_sp_sign: str = "integrator",
    off_diagonal_strategy: str = "m_decoupled_blocks",
) -> SolverCoreOutput:
    """Build a VER2 observer-neutral output from an integrator-owned execution bundle."""

    return build_solver_core_output_from_native_result(
        manifest=manifest,
        bianchi_type=bianchi_type,
        result=result,
        species=species,
        runtime_controls=runtime_controls,
        feature_flags=feature_flags,
        release=release,
        k_grid_mpc=np.asarray(k_grid_mpc, dtype=np.float64),
        structure=structure,
        propagator=propagator,
        thomson_mode=thomson_mode,
        limber_eta_sp_sign=limber_eta_sp_sign,
        off_diagonal_strategy=off_diagonal_strategy,
        gate_registry=gate_registry,
        mode_ops=runtime_trace.mode_ops,
        seed_pack=runtime_trace.seed_pack,
        canonical_projection=runtime_trace.canonical_projection,
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
    gate_registry: Mapping[str, object] | None = None,
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
    if (
        runtime_controls.tier is SolverTier.TIER_B_PSTF
        and propagator is None
        and feature_flags.source_propagator is FeatureStatus.EXACT
        and structure_constants.label != "I"
    ):
        raise ValueError(
            "Tier-B exact source propagation requires an explicit propagator config; "
            "the retained Lowell bridge is only an approximate FLRW-kernel carry path."
        )
    propagator_config = (
        (
            _default_tier_b_propagator_config(
                structure=structure_constants,
                requested_status=feature_flags.source_propagator,
            )
            if runtime_controls.tier is SolverTier.TIER_B_PSTF
            else SourcePropagatorConfig(
                mode=PropagatorMode.FLRW_VALIDATION,
                polarization_rotation=FeatureStatus.DISABLED,
                temperature_transport=FeatureStatus.EXACT,
                flrw_validation_only=True,
                kernel_family="flrw_scalar_validation",
                observer_frame=ObserverFrameMetadata(
                    harmonic_basis="flrw_scalar_validation",
                    eb_sign_convention="cmb",
                ),
            )
        )
        if propagator is None
        else propagator
    )
    visibility_fn = _build_visibility_fn_from_a_lookup(
        species,
        lambda eta: float(species.bg_table.interp_a(float(eta))),
    )
    source_builder, source_builder_metadata = _build_lowell_source_builder(
        result,
        species=species,
        visibility_fn=visibility_fn,
    )
    live_propagator = build_source_propagator(
        propagator_config,
        structure=structure_constants,
        eta_grid_mpc=np.asarray(result.eta, dtype=np.float64),
        k_grid_mpc=np.asarray(k_grid_mpc, dtype=np.float64),
        ell_max=int(runtime_controls.multipole_cutoff),
        visibility_fn=visibility_fn,
        source_builder=source_builder,
        limber_eta_sp_sign=limber_eta_sp_sign,
        off_diagonal_strategy=off_diagonal_strategy,
    )
    coefficient_representation = (
        "lowell_pstf_final_slice"
        if runtime_controls.tier is SolverTier.TIER_B_PSTF
        else "tier_a_validation_reference_slice"
    )
    angular_representation = (
        "lowell_pstf_sphere_reconstruction"
        if runtime_controls.tier is SolverTier.TIER_B_PSTF
        else "tier_a_validation_reference_sphere_reconstruction"
    )
    alm_T, alm_E, alm_B = _build_reconstructed_payloads(
        result,
        coefficient_representation=coefficient_representation,
        angular_representation=angular_representation,
    )
    output = build_solver_core_output(
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
        alm_T=alm_T,
        alm_E=alm_E,
        alm_B=alm_B,
        deterministic_template=_build_template_from_result(
            result,
            live_propagator,
            kind="tier_b_lowell_template",
        ),
        anisotropic_covariance=live_propagator.covariance_bundle,
        gate_registry=gate_registry,
        extra_metadata={
            **_structure_metadata(
                structure=structure_constants,
                tilt_enabled=bool(abs(result.config.tilt_rapidity) > 0.0),
                tilt_rapidity=float(result.config.tilt_rapidity),
                tilt_direction=tuple(float(x) for x in result.config.tilt_direction),
            ),
            "propagator_ready": True,
            "validation_reference": runtime_controls.tier is SolverTier.TIER_A_ANGULAR,
            "k_grid_size": int(np.asarray(k_grid_mpc).size),
            "eta_grid_size": int(np.asarray(result.eta).size),
            "off_diagonal_strategy": off_diagonal_strategy,
            "limber_eta_sp_sign": limber_eta_sp_sign,
            "source_builder_scope": "theta0_plus_combined_polter_visibility_lowell_bridge",
            "source_propagator_status": live_propagator.config.temperature_transport.value,
            "source_propagator_requested_status": feature_flags.source_propagator.value,
            "source_propagator_rotation_status": live_propagator.config.polarization_rotation.value,
            "source_propagator_realization": live_propagator.config.kernel_family,
            "solver_method": str(
                result.solver_info.get("solver_method", result.config.solver_method)
            ),
            "resolved_solver_method": str(
                result.solver_info.get(
                    "resolved_solver_method",
                    result.solver_info.get("solver_method", result.config.solver_method),
                )
            ),
            "executor_realization": str(
                result.solver_info.get(
                    "executor_realization",
                    result.solver_info.get(
                        "solver_family_realization",
                        "runtime_family_direct",
                    ),
                )
            ),
            **_neutrino_runtime_metadata(species),
            **source_builder_metadata,
        },
    )
    from bass.forward.ver3_output_archive import resolve_output_gate_registry

    output.metadata["gate_registry"] = resolve_output_gate_registry(
        output,
        gate_registry=gate_registry,
    )
    return output


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
