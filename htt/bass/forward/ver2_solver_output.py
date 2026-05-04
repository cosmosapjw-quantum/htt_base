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
from bass.los.b_mode_projector import (
    B_MODE_OUTPUT_SUPPORT_WIGNER_D_PATH_B,
    project_B_mode_transfer,
)
from bass.los.family_backend_protocol import family_backend_status
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


def _resolved_tilt_background_owner(
    *,
    tilt_enabled: bool,
    requested_owner: str,
) -> tuple[str, str, str]:
    if not bool(tilt_enabled):
        return (
            "orthogonal_zero_tilt",
            "not_applicable_orthogonal_zero_tilt",
            "not_applicable_orthogonal_zero_tilt",
        )
    if requested_owner == "nonperturbative_tilt_rhs":
        return (
            "nonperturbative_tilt_rhs",
            "production_dynamic_nonperturbative_rapidity",
            "runtime_wired_dynamic_rapidity_owner",
        )
    return (
        "fixed_velocity_closure",
        "legacy_fixed_velocity_closure",
        "research_contract_only",
    )


def _mode_label_history_payload_summary(
    result: IntegrationResult,
) -> dict[str, Any]:
    metadata = result.solver_info.get("live_mode_label_harmonic_history_metadata", {})
    sector_maps = {
        "ph_I": getattr(result, "photon_T_history_by_mode_label", None),
        "ph_E": getattr(result, "photon_E_history_by_mode_label", None),
        "ph_B": getattr(result, "photon_B_history_by_mode_label", None),
        "nu_I": getattr(result, "neutrino_history_by_mode_label", None),
    }
    mode_labels: list[str] = []
    sector_norms: dict[str, dict[str, float]] = {}
    for sector, mapping in sector_maps.items():
        if not isinstance(mapping, Mapping):
            continue
        sector_norms[sector] = {}
        for mu, values in mapping.items():
            mu_key = str(mu)
            if mu_key not in mode_labels:
                mode_labels.append(mu_key)
            sector_norms[sector][mu_key] = float(np.linalg.norm(np.asarray(values, dtype=np.float64)))
    nonzero_mode_labels = [
        mu
        for mu in mode_labels
        if any(sector_norms.get(sector, {}).get(mu, 0.0) > 0.0 for sector in sector_norms)
    ]
    return {
        "live_mode_label_harmonic_history_owner": str(metadata.get("owner", "unavailable")),
        "live_mode_label_harmonic_history_integration_scheme": metadata.get("integration_scheme"),
        "live_mode_label_harmonic_history_sample_count": int(metadata.get("history_sample_count", 0)),
        "live_mode_label_harmonic_history_mode_labels": mode_labels,
        "live_mode_label_harmonic_history_residual_mode_labels": list(
            metadata.get("residual_mode_labels", [])
        ),
        "live_mode_label_harmonic_history_sector_norms": sector_norms,
        "live_mode_label_harmonic_history_nonzero_mode_labels": nonzero_mode_labels,
    }


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


def _independent_gate_passed(
    gate_registry: Mapping[str, object] | None,
    gate_name: str,
) -> bool:
    """Return one gate's own pass bit without fitting-ladder propagation."""

    if gate_registry is None:
        return False
    gate = gate_registry.get(gate_name)
    if gate is None:
        return False
    if hasattr(gate, "passed"):
        return bool(getattr(gate, "passed"))
    if isinstance(gate, Mapping):
        return bool(gate.get("passed", False))
    return bool(gate)


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
    required_gates = (
        "tilt_boost_separation_gate",
        "ic_provenance_gate",
        "family_backend_gate",
        "hierarchy_layout_gate",
    )
    if gate_registry is not None and any(
        not _independent_gate_passed(gate_registry, gate)
        for gate in required_gates
    ):
        return "contract_only_unavailable"
    if (
        mode_ops_metadata.get("lookup_resolution_status") != "frozen_v5_formula_set"
        or not bool(mode_ops_metadata.get("verification_crosscheck_pass", False))
    ):
        return "contract_only_unavailable"
    if not bool(mode_ops_metadata.get("reduced_local_evaluator_available", False)):
        return "contract_only_unavailable"
    if not bool(mode_ops_metadata.get("reduced_harmonic_evaluator_available", False)):
        return "contract_only_unavailable"
    if not bool(mode_ops_metadata.get("reduced_source_evaluator_available", False)):
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


def _ic_provenance_status_from_runtime(
    *,
    seed_pack: object | None,
    gate_registry: Mapping[str, object] | None,
    result: IntegrationResult,
) -> str | None:
    if seed_pack is not None:
        seed_metadata = getattr(seed_pack, "metadata", {})
        if isinstance(seed_metadata, Mapping) and seed_metadata.get(
            "ic_provenance_status"
        ):
            return str(seed_metadata["ic_provenance_status"])
    if gate_registry is not None:
        gate = gate_registry.get("ic_provenance_gate")
        gate_metadata = dict(getattr(gate, "metadata", {}))
        if gate_metadata.get("ic_provenance_status"):
            return str(gate_metadata["ic_provenance_status"])
        seed_payload = gate_metadata.get("seed_pack")
        if isinstance(seed_payload, Mapping):
            nested_metadata = seed_payload.get("metadata")
            if isinstance(nested_metadata, Mapping) and nested_metadata.get(
                "ic_provenance_status"
            ):
                return str(nested_metadata["ic_provenance_status"])
    solver_seed_metadata = result.solver_info.get("seed_pack_metadata", {})
    if isinstance(solver_seed_metadata, Mapping) and solver_seed_metadata.get(
        "ic_provenance_status"
    ):
        return str(solver_seed_metadata["ic_provenance_status"])
    return None


def _attach_output_gate_metadata(
    output: SolverCoreOutput,
    *,
    gate_registry: Mapping[str, object] | None,
) -> None:
    from bass.forward.ver3_output_archive import resolve_output_gate_registry

    resolved = resolve_output_gate_registry(output, gate_registry=gate_registry)
    output.metadata["gate_registry"] = resolved

    output_split = resolved.get("output_split_gate")
    output_split_metadata = dict(getattr(output_split, "metadata", {}))
    if output_split_metadata:
        output.metadata["stochastic_channel_status"] = output_split_metadata.get(
            "stochastic_channel_status",
            output.metadata.get("stochastic_channel_status", "unknown"),
        )
        output.metadata["stochastic_block_reason"] = output_split_metadata.get(
            "stochastic_block_reason",
            output.metadata.get("stochastic_block_reason"),
        )

    production_cutoff = resolved.get("production_cutoff_gate")
    production_cutoff_metadata = dict(getattr(production_cutoff, "metadata", {}))
    if production_cutoff_metadata:
        output.metadata["production_cutoff_status"] = production_cutoff_metadata.get(
            "production_cutoff_status",
            output.metadata.get("production_cutoff_status", "unknown"),
        )


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
    (
        resolved_tilt_owner,
        tilt_owner_status,
        nonperturbative_tilt_status,
    ) = _resolved_tilt_background_owner(
        tilt_enabled=tilt_enabled,
        requested_owner=runtime_controls.tilt_background_owner,
    )
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
        "family_backend_status": family_backend_status(bianchi_type),
        "propagator_readiness": propagator_readiness,
        "propagator_exactness": propagator_readiness,
        "covariance_readiness": _base_covariance_readiness(anisotropic_covariance),
        "feature_flags": {key: value.value for key, value in asdict(feature_flags).items()},
        "release_stage": release.release_stage,
        "run_label": release.run_label,
        "observer_neutral": True,
        "forbidden_products": ("posterior", "likelihood", "p_value"),
        "tilt_background_owner_requested": runtime_controls.tilt_background_owner,
        "tilt_background_owner": resolved_tilt_owner,
        "tilt_background_owner_status": tilt_owner_status,
        "nonperturbative_tilt_rhs_status": nonperturbative_tilt_status,
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
        # Map-domain output (audit P-08): no production producer yet for
        # T(n̂)/Q(n̂)/U(n̂); fields are typed pass-throughs and must remain
        # ``None`` unless a real-space producer is attached upstream.
        "map_output_support": (
            "producer_attached"
            if any(m is not None for m in (map_T, map_Q, map_U))
            else "not_implemented"
        ),
        "map_output_block_reason": "real_space_map_producer_not_attached",
        # B-mode polarization output (audit P-05): the FLRW Bessel
        # projector zeros B by construction, so the ``alm_B`` archive
        # column is identically zero unless a Bianchi tensor projector is
        # plugged in. Mark the column status explicitly so downstream
        # gates cannot mistake the zero array for a B-mode prediction.
        "b_mode_output_support": "flrw_zero_only",
        "b_mode_block_reason": "flrw_bessel_projector_zeros_b_by_construction",
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


def _build_result_a_lookup(result: IntegrationResult):
    eta_grid = np.asarray(result.eta, dtype=np.float64)
    a_grid = np.asarray(result.a, dtype=np.float64)
    if eta_grid.ndim != 1 or a_grid.ndim != 1 or eta_grid.shape != a_grid.shape:
        raise ValueError(
            "result.eta and result.a must be 1-D arrays with identical shape "
            f"for visibility source construction, got {eta_grid.shape} and {a_grid.shape}"
        )
    if eta_grid.size < 2:
        raise ValueError("visibility source construction requires at least two eta samples")
    if not np.all(np.isfinite(eta_grid)) or not np.all(np.isfinite(a_grid)):
        raise ValueError("result.eta/result.a contain non-finite values")
    if not np.all(np.diff(eta_grid) > 0.0):
        raise ValueError("result.eta must be strictly increasing for visibility interpolation")
    if np.any(a_grid <= 0.0):
        raise ValueError("result.a must be strictly positive for recombination visibility lookup")

    def a_lookup(eta: float) -> float:
        return _interp_series(eta_grid, a_grid, float(eta))

    return a_lookup


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


def _build_kappa_fn_from_a_lookup(species: SpeciesBackgroundRegistry, a_lookup):
    baryon = species[SpeciesLabel.BARYON]
    interp = baryon._recomb  # noqa: SLF001 - stable internal ownership for the current tier-B bridge
    table = interp.table

    def kappa_fn(eta: float) -> float:
        a_val = float(a_lookup(float(eta)))
        z_val = (1.0 / max(a_val, 1.0e-30)) - 1.0
        if z_val < table.z_min:
            return 0.0
        z_query = table.z_max if z_val > table.z_max else z_val
        return float(interp.query_kappa(z_query))

    return kappa_fn


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
    scale_factor_owner: str = "integration_result",
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
    baryon_history = getattr(result, "baryon_local_history", None)
    if baryon_history is None:
        v_b_m0 = np.zeros_like(eta_grid)
        doppler_status = "zero_unavailable_missing_baryon_local_history"
    else:
        baryon_arr = np.asarray(baryon_history, dtype=np.float64)
        if baryon_arr.ndim != 2 or baryon_arr.shape[0] != eta_grid.size or baryon_arr.shape[1] < 2:
            raise ValueError(
                "result.baryon_local_history must have shape (n_eta, >=2) "
                "when used for LoS Doppler sourcing"
            )
        v_b_m0 = np.asarray(baryon_arr[:, 1], dtype=np.float64)
        if np.any(~np.isfinite(v_b_m0)):
            raise ValueError("result.baryon_local_history[:, 1] contains non-finite Doppler velocities")
        doppler_status = "baryon_local_history_slot1"
    gvb_m0 = visibility * v_b_m0

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
            "v_b_m0": _interp_series(eta_grid, v_b_m0, eta),
            "gpi_m0": _interp_series(eta_grid, gpi["m0"], eta),
            "gpi_m_plus2": _interp_series(eta_grid, gpi["m_plus2"], eta),
            "gpi_m_minus2": _interp_series(eta_grid, gpi["m_minus2"], eta),
            "g_v_b_m0": _interp_series(eta_grid, gvb_m0, eta),
        }

    metadata = _build_visibility_source_metadata(
        result,
        species=species,
        visibility_fn=visibility_fn,
        gpi_m0=gpi["m0"],
    )
    a_grid = np.asarray(result.a, dtype=np.float64)
    z_grid = (1.0 / np.maximum(a_grid, 1.0e-30)) - 1.0
    metadata.update(
        {
            "source_builder_scale_factor_owner": str(scale_factor_owner),
            "source_builder_runtime_z_min": float(np.min(z_grid)),
            "source_builder_runtime_z_max": float(np.max(z_grid)),
            "source_builder_visibility_max": float(np.max(visibility)),
            "source_builder_visibility_nonzero_sample_count": int(np.count_nonzero(visibility > 0.0)),
            "source_builder_doppler_status": doppler_status,
            "source_builder_doppler_max_abs_v_b_m0": float(np.max(np.abs(v_b_m0))),
            "source_builder_doppler_nonzero_sample_count": int(np.count_nonzero(np.abs(v_b_m0) > 0.0)),
        }
    )
    return source_builder, metadata


def _build_tier_b_exact_type_i_source_builder(
    result: IntegrationResult,
    *,
    species: SpeciesBackgroundRegistry,
    kappa_fn: Callable[[float], float],
    visibility_fn: Callable[[float], float],
    source_builder_scope: str = "tier_b_einstein_extracted_type_i_exact",
    matrix_scope: str = "type_i",
):
    """Build explicit exact matrix-LoS ingredients from Tier-B histories.

    This path is used for exact matrix propagators. It fails closed through
    ``extract_flrw_sources_from_tier_b`` when the Tier-B result lacks
    neutrino or matter histories, rather than letting the LoS layer
    interpret missing Ψ/ISW/Doppler ingredients as zeros.
    """

    from bass.spectrum.tier_b_source_extraction import extract_flrw_sources_from_tier_b

    eta_grid = np.asarray(result.eta, dtype=np.float64)
    theta_2 = {
        "m_plus2": np.asarray(result.pi_ell_m(2, 2), dtype=np.float64),
        "m_minus2": np.asarray(result.pi_ell_m(2, -2), dtype=np.float64),
    }
    e_2 = {
        "m_plus2": np.asarray(result.e_ell_m(2, 2), dtype=np.float64),
        "m_minus2": np.asarray(result.e_ell_m(2, -2), dtype=np.float64),
    }
    pi_spin2 = {
        name: np.asarray(theta_2[name] - np.sqrt(6.0) * e_2[name], dtype=np.float64)
        for name in theta_2
    }
    visibility = np.asarray([float(visibility_fn(float(eta))) for eta in eta_grid], dtype=np.float64)
    if np.any(~np.isfinite(visibility)) or np.any(visibility < 0.0):
        raise ValueError("Type-I exact source builder requires finite non-negative visibility")
    source_cache: dict[float, object] = {}

    def sources_for_k(k: float):
        key = float(k)
        if key not in source_cache:
            source_cache[key] = extract_flrw_sources_from_tier_b(
                result,
                species,
                key,
                anisotropic_stress=True,
            )
        return source_cache[key]

    def source_builder(eta: float, k: float) -> dict[str, float]:
        eta_f = float(eta)
        sources = sources_for_k(float(k))
        theta_0 = float(sources.theta_0(eta_f))
        psi = float(sources.psi(eta_f))
        isw = float(sources.phi_dot_plus_psi_dot(eta_f))
        v_b = float(sources.v_b(eta_f))
        pi_m0 = float(sources.pi(eta_f))
        kappa = float(kappa_fn(eta_f))
        if not np.all(np.isfinite([theta_0, psi, isw, v_b, pi_m0, kappa])):
            raise ValueError("Type-I exact LoS source ingredient became non-finite")
        return {
            "kappa": kappa,
            "optical_depth": kappa,
            "theta_0_m0": theta_0,
            "psi_m0": psi,
            "phi_dot_plus_psi_dot_m0": isw,
            "v_b_m0": v_b,
            "pi_m0": pi_m0,
            "theta_0_m_plus2": 0.0,
            "psi_m_plus2": 0.0,
            "phi_dot_plus_psi_dot_m_plus2": 0.0,
            "v_b_m_plus2": 0.0,
            "pi_m_plus2": _interp_series(eta_grid, pi_spin2["m_plus2"], eta_f),
            "theta_0_m_minus2": 0.0,
            "psi_m_minus2": 0.0,
            "phi_dot_plus_psi_dot_m_minus2": 0.0,
            "v_b_m_minus2": 0.0,
            "pi_m_minus2": _interp_series(eta_grid, pi_spin2["m_minus2"], eta_f),
        }

    metadata = _build_visibility_source_metadata(
        result,
        species=species,
        visibility_fn=visibility_fn,
        gpi_m0=visibility * np.asarray(
            [float(sources_for_k(1.0e-2).pi(float(eta))) for eta in eta_grid],
            dtype=np.float64,
        ),
    )
    metadata.update(
        {
            "source_builder_scope": str(source_builder_scope),
            "source_builder_einstein_source_owner": (
                "bass.spectrum.tier_b_source_extraction.extract_flrw_sources_from_tier_b"
            ),
            "source_builder_exact_type_i_decomposed": matrix_scope == "type_i",
            "source_builder_exact_matrix_decomposed": True,
            "source_builder_matrix_scope": str(matrix_scope),
            "source_builder_explicit_zero_spin2_scalar_terms": True,
            "source_builder_anisotropic_stress_owner": (
                "tier_b_source_extraction.photon_neutrino_intensity_quadrupoles"
            ),
            "source_builder_neutrino_metric_feedback_owner": str(
                result.solver_info.get("neutrino_metric_feedback_owner", "unavailable")
            ),
            "source_builder_neutrino_metric_feedback_status": str(
                result.solver_info.get("neutrino_metric_feedback_status", "unavailable")
            ),
            "source_builder_neutrino_metric_feedback_evidence_passed": bool(
                result.solver_info.get("neutrino_metric_feedback_evidence_passed", False)
            ),
            "source_builder_kappa_owner": "recombination_table_via_result_a_lookup",
            "source_builder_visibility_max": float(np.max(visibility)),
            "source_builder_visibility_nonzero_sample_count": int(np.count_nonzero(visibility > 0.0)),
        }
    )
    return source_builder, metadata


def _requires_explicit_decomposed_los_sources(config: SourcePropagatorConfig) -> bool:
    return (
        config.mode is PropagatorMode.ANISOTROPIC_FORWARD
        and config.kernel_family != "flrw_scalar_validation"
        and (
            config.temperature_transport is FeatureStatus.EXACT
            or config.polarization_rotation is FeatureStatus.EXACT
        )
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


def _flat_history_to_l_m5(history: object, *, L: int) -> np.ndarray:
    """Convert flat ell/m history to the projector's (eta, ell, m=-2..2) view."""

    arr = np.asarray(history, dtype=np.float64)
    target = (int(L) + 1) ** 2
    if arr.ndim != 2 or arr.shape[1] != target:
        raise ValueError(
            f"flat hierarchy history must have shape (n_eta, {target}), got {arr.shape}"
        )
    out = np.zeros((arr.shape[0], int(L) + 1, 5), dtype=np.float64)
    for ell in range(int(L) + 1):
        for m in range(max(-2, -ell), min(2, ell) + 1):
            out[:, ell, m + 2] = arr[:, ell * ell + ell + m]
    return out


def _default_sigma_2m_history(result: IntegrationResult) -> np.ndarray:
    """Build the minimal shear-quadrupole history used by the B projector."""

    eta = np.asarray(result.eta, dtype=np.float64)
    sigma = np.zeros((eta.size, 5), dtype=np.float64)
    sigma[:, 2] = np.asarray(result.Sigma_plus, dtype=np.float64)
    if np.asarray(result.Sigma_minus, dtype=np.float64).shape == eta.shape:
        sigma[:, 4] = np.asarray(result.Sigma_minus, dtype=np.float64)
    return sigma


def _b_mode_source_projection_evidence(propagator: SourcePropagator) -> dict[str, Any]:
    transfer = np.asarray(
        propagator.transfer_bundle.get("transfer_B", np.array([], dtype=np.float64)),
        dtype=np.float64,
    )
    if transfer.size == 0:
        return {
            "b_mode_source_projection_status": "missing_transfer_b",
            "b_mode_source_transfer_b_norm": None,
            "b_mode_source_projection_known_zero": False,
            "b_mode_source_projection_exactness": propagator.evidence.get("exactness"),
        }
    norm = float(np.linalg.norm(transfer))
    finite = bool(np.isfinite(norm) and np.all(np.isfinite(transfer)))
    output_ready = bool(propagator.evidence.get("output_claim_allowed", False))
    known_zero = bool(finite and output_ready and norm == 0.0)
    status = (
        "known_zero_output_ready_transfer"
        if known_zero
        else "nonzero_or_not_output_ready_transfer"
        if finite
        else "nonfinite_transfer_b"
    )
    return {
        "b_mode_source_projection_status": status,
        "b_mode_source_transfer_b_norm": norm,
        "b_mode_source_projection_known_zero": known_zero,
        "b_mode_source_projection_exactness": propagator.evidence.get("exactness"),
    }


def _b_mode_projector_evidence(
    result: IntegrationResult,
    *,
    visibility_fn: Callable[[float], float],
    k_grid_mpc: np.ndarray,
    b_mode_runtime_available: bool,
    canonical_projection: object | None,
) -> dict[str, Any]:
    if not b_mode_runtime_available:
        return {
            "b_mode_projector_status": "not_run_no_runtime_b_mode",
            "b_mode_projector_support": None,
            "b_mode_projector_norm": 0.0,
        }
    if canonical_projection is None:
        return {
            "b_mode_projector_status": "not_run_no_canonical_projection",
            "b_mode_projector_support": None,
            "b_mode_projector_norm": 0.0,
        }
    block = getattr(canonical_projection, "hierarchy_state").photon_polarization_block
    b_history = block.get("B_history")
    if b_history is None:
        return {
            "b_mode_projector_status": "not_run_no_b_history",
            "b_mode_projector_support": None,
            "b_mode_projector_norm": 0.0,
        }
    b_hist = np.asarray(b_history, dtype=np.float64)
    eta = np.asarray(result.eta, dtype=np.float64)
    if b_hist.ndim != 2 or b_hist.shape[0] != eta.size:
        return {
            "b_mode_projector_status": "not_run_b_history_eta_mismatch",
            "b_mode_projector_support": None,
            "b_mode_projector_norm": 0.0,
            "b_mode_projector_b_history_shape": tuple(int(x) for x in b_hist.shape),
            "b_mode_projector_eta_size": int(eta.size),
        }
    L = int(result.L_max)
    k_norm = float(np.linalg.norm(np.asarray(k_grid_mpc, dtype=np.float64).ravel()[:1]))
    try:
        transfer = project_B_mode_transfer(
            photon_B_tower_history=_flat_history_to_l_m5(b_hist, L=L),
            photon_E_tower_history=_flat_history_to_l_m5(result.photon_E_tower, L=L),
            sigma_2M_history=_default_sigma_2m_history(result),
            eta_grid=eta,
            visibility_history=np.asarray(
                [float(visibility_fn(float(value))) for value in eta],
                dtype=np.float64,
            ),
            k_norm=k_norm,
            ell_max=L,
        )
    except Exception as exc:
        return {
            "b_mode_projector_status": "failed",
            "b_mode_projector_support": None,
            "b_mode_projector_norm": 0.0,
            "b_mode_projector_k_norm_mpc": k_norm,
            "b_mode_projector_error": str(exc),
        }
    norm = float(np.linalg.norm(transfer))
    if not np.isfinite(norm):
        return {
            "b_mode_projector_status": "failed_nonfinite",
            "b_mode_projector_support": None,
            "b_mode_projector_norm": norm,
        }
    return {
        "b_mode_projector_status": "computed_wigner_d_path_b",
        "b_mode_projector_support": B_MODE_OUTPUT_SUPPORT_WIGNER_D_PATH_B,
        "b_mode_projector_norm": norm,
        "b_mode_projector_transfer_shape": tuple(int(x) for x in transfer.shape),
        "b_mode_projector_nonzero": bool(norm > 0.0),
        "b_mode_projector_source_owner": "photon_B_tower_history.ell2",
        "b_mode_projector_source_combination": "Pi_B_channel=(2/5)*B_2",
        "b_mode_projector_input_validation": "finite_strict_eta_positive_k_quadrupole_required",
        "b_mode_projector_k_norm_mpc": k_norm,
    }


def _exact_thomson_authority_path(
    *,
    thomson_mode: str,
    gate_registry: Mapping[str, object] | None,
) -> bool:
    if gate_registry is None:
        return False
    exact_gate = gate_registry.get("exact_thomson_gate")
    return bool(getattr(exact_gate, "passed", exact_gate))


def _exact_thomson_gate_metadata(gate_registry: Mapping[str, object] | None) -> dict[str, object]:
    if gate_registry is None:
        return {}
    exact_gate = gate_registry.get("exact_thomson_gate")
    if exact_gate is None:
        return {}
    metadata = getattr(exact_gate, "metadata", None)
    if isinstance(metadata, Mapping):
        return dict(metadata)
    if isinstance(exact_gate, Mapping) and isinstance(exact_gate.get("metadata"), Mapping):
        return dict(exact_gate["metadata"])
    return {}


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
    b_mode_component_status: str = "zero_filled_not_evolved",
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

    a_lookup = _build_result_a_lookup(result)
    visibility_fn = _build_visibility_fn_from_a_lookup(species, a_lookup)
    if _requires_explicit_decomposed_los_sources(propagator_config):
        matrix_scope = "type_i" if structure_constants.label == "I" else "family_matrix"
        source_scope = (
            "tier_b_einstein_extracted_type_i_exact"
            if structure_constants.label == "I"
            else "tier_b_einstein_extracted_family_matrix_exact"
        )
        source_builder, source_builder_metadata = _build_tier_b_exact_type_i_source_builder(
            result,
            species=species,
            kappa_fn=_build_kappa_fn_from_a_lookup(species, a_lookup),
            visibility_fn=visibility_fn,
            source_builder_scope=source_scope,
            matrix_scope=matrix_scope,
        )
    else:
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
    b_mode_payload_status = str(
        result.solver_info.get("layout_b_mode_payload_status", "zero_filled_not_evolved")
    )
    b_mode_payload_available = False
    b_mode_runtime_available = False
    b_mode_coefficients = None
    runtime_b_tower = getattr(result, "photon_B_tower", None)
    if canonical_projection is not None:
        b_mode_coefficients = (
            np.asarray(runtime_b_tower[-1], dtype=np.float64)
            if runtime_b_tower is not None
            else np.asarray(
                getattr(canonical_projection, "hierarchy_state").photon_polarization_block.get("B"),
                dtype=np.float64,
            )
        )
        b_mode_sector_status = str(getattr(canonical_projection, "sector_status", {}).get("ph_B", ""))
        if (
            b_mode_sector_status in {
                "layout_operator_auxiliary_b_mode_history",
                "hierarchy_rhs_direct_b_mode_history",
                "main_state_coevolved_b_mode_history",
            }
            and np.any(np.abs(b_mode_coefficients) > 0.0)
        ):
            b_mode_payload_status = b_mode_sector_status
            b_mode_payload_available = True
            b_mode_runtime_available = True
        elif b_mode_sector_status:
            b_mode_payload_status = b_mode_sector_status
    elif runtime_b_tower is not None:
        b_mode_coefficients = np.asarray(runtime_b_tower[-1], dtype=np.float64)
        if np.any(np.abs(b_mode_coefficients) > 0.0):
            b_history_metadata = result.solver_info.get("live_b_mode_history_metadata", {})
            b_mode_payload_status = (
                "main_state_coevolved_b_mode_history"
                if str(getattr(b_history_metadata, "get", lambda *_: "")("owner", ""))
                == "ver2_native_integrator.main_state_photon_B"
                else "hierarchy_rhs_direct_b_mode_history"
            )
            b_mode_payload_available = True
            b_mode_runtime_available = True
    b_source_projection_evidence = _b_mode_source_projection_evidence(live_propagator)
    b_source_known_zero = bool(
        b_source_projection_evidence["b_mode_source_projection_known_zero"]
    )
    b_mode_output_support = (
        "evolved_b_mode_history"
        if b_mode_runtime_available
        else "known_zero_source_projection_not_evolved"
        if b_mode_payload_status == "zero_filled_not_evolved" and b_source_known_zero
        else "zero_filled_without_b_mode_evidence"
        if b_mode_payload_status == "zero_filled_not_evolved"
        else "layout_contract_only"
    )
    b_mode_block_reason = (
        None
        if b_mode_runtime_available
        else "b_mode_zero_supported_by_exact_source_projection"
        if b_mode_payload_status == "zero_filled_not_evolved" and b_source_known_zero
        else "b_mode_zero_filled_without_output_ready_source_projection"
        if b_mode_payload_status == "zero_filled_not_evolved"
        else "b_mode_layout_contract_without_runtime_evidence"
    )
    b_projector_evidence = _b_mode_projector_evidence(
        result,
        visibility_fn=visibility_fn,
        k_grid_mpc=np.asarray(k_grid_mpc, dtype=np.float64),
        b_mode_runtime_available=bool(b_mode_runtime_available),
        canonical_projection=canonical_projection,
    )
    if (
        b_projector_evidence["b_mode_projector_support"]
        == B_MODE_OUTPUT_SUPPORT_WIGNER_D_PATH_B
        and bool(b_projector_evidence.get("b_mode_projector_nonzero", False))
    ):
        b_mode_output_support = B_MODE_OUTPUT_SUPPORT_WIGNER_D_PATH_B
        b_mode_block_reason = None
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
    exact_thomson_gate_metadata = _exact_thomson_gate_metadata(gate_registry)
    exact_thomson_gate_passed = _exact_thomson_authority_path(
        thomson_mode=thomson_mode,
        gate_registry=gate_registry,
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
            "source_propagator_exactness": live_propagator.evidence.get("exactness"),
            "source_propagator_source_completeness_policy": live_propagator.transfer_bundle.get(
                "source_completeness_policy"
            ),
            "source_propagator_fail_closed_sources": (
                live_propagator.transfer_bundle.get("source_completeness_policy")
                == "explicit_required_fail_closed"
            ),
            "source_propagator_temperature_doppler_derivative": live_propagator.transfer_bundle.get(
                "temperature_source_doppler_derivative"
            ),
            "source_propagator_publication_output_claim_allowed": bool(
                live_propagator.evidence.get("output_claim_allowed", False)
            ),
            "source_propagator_statistics_claim_allowed": bool(
                live_propagator.evidence.get("statistics_claim_allowed", False)
            ),
            "source_propagator_block_reason": live_propagator.evidence.get("block_reason"),
            "source_propagator_helical_transport_status": live_propagator.transfer_bundle.get(
                "helical_transport_status"
            ),
            "source_propagator_helical_pitch": live_propagator.transfer_bundle.get(
                "helical_pitch"
            ),
            "source_propagator_helical_phase_max": live_propagator.transfer_bundle.get(
                "helical_phase_max"
            ),
            "source_propagator_polarization_basis_transport": live_propagator.transfer_bundle.get(
                "polarization_basis_transport"
            ),
            "source_propagator_helicity_mode_mixing_norm": live_propagator.transfer_bundle.get(
                "helicity_mode_mixing_norm"
            ),
            "source_propagator_nil_transport_status": live_propagator.transfer_bundle.get(
                "nil_transport_status"
            ),
            "source_propagator_nil_structure_scale": live_propagator.transfer_bundle.get(
                "nil_structure_scale"
            ),
            "source_propagator_nil_shear_max": live_propagator.transfer_bundle.get(
                "nil_shear_max"
            ),
            "source_propagator_nil_phase_max": live_propagator.transfer_bundle.get(
                "nil_phase_max"
            ),
            "source_propagator_nil_mode_mixing_norm": live_propagator.transfer_bundle.get(
                "nil_mode_mixing_norm"
            ),
            "source_propagator_typeiii_transport_status": live_propagator.transfer_bundle.get(
                "typeiii_transport_status"
            ),
            "source_propagator_typeiii_branch_flag": live_propagator.transfer_bundle.get(
                "typeiii_branch_flag"
            ),
            "source_propagator_typeiii_h_parameter": live_propagator.transfer_bundle.get(
                "typeiii_h_parameter"
            ),
            "source_propagator_typeiii_hyperbolic_scale": live_propagator.transfer_bundle.get(
                "typeiii_hyperbolic_scale"
            ),
            "source_propagator_typeiii_twist_scale": live_propagator.transfer_bundle.get(
                "typeiii_twist_scale"
            ),
            "source_propagator_typeiii_open_attenuation_min": live_propagator.transfer_bundle.get(
                "typeiii_open_attenuation_min"
            ),
            "source_propagator_typeiii_mode_mixing_norm": live_propagator.transfer_bundle.get(
                "typeiii_mode_mixing_norm"
            ),
            "source_propagator_typeiv_transport_status": live_propagator.transfer_bundle.get(
                "typeiv_transport_status"
            ),
            "source_propagator_typeiv_coordinate_order": live_propagator.transfer_bundle.get(
                "typeiv_coordinate_order"
            ),
            "source_propagator_typeiv_structure_scale": live_propagator.transfer_bundle.get(
                "typeiv_structure_scale"
            ),
            "source_propagator_typeiv_n3_scale": live_propagator.transfer_bundle.get(
                "typeiv_n3_scale"
            ),
            "source_propagator_typeiv_twist_scale": live_propagator.transfer_bundle.get(
                "typeiv_twist_scale"
            ),
            "source_propagator_typeiv_privileged_weight": live_propagator.transfer_bundle.get(
                "typeiv_privileged_weight"
            ),
            "source_propagator_typeiv_edge_attenuation_min": live_propagator.transfer_bundle.get(
                "typeiv_edge_attenuation_min"
            ),
            "source_propagator_typeiv_mode_mixing_norm": live_propagator.transfer_bundle.get(
                "typeiv_mode_mixing_norm"
            ),
            "source_propagator_typev_transport_status": live_propagator.transfer_bundle.get(
                "typev_transport_status"
            ),
            "source_propagator_typev_chart_metadata": live_propagator.transfer_bundle.get(
                "typev_chart_metadata"
            ),
            "source_propagator_typev_curvature_scale": live_propagator.transfer_bundle.get(
                "typev_curvature_scale"
            ),
            "source_propagator_typev_open_envelope_min": live_propagator.transfer_bundle.get(
                "typev_open_envelope_min"
            ),
            "source_propagator_typev_open_envelope_max": live_propagator.transfer_bundle.get(
                "typev_open_envelope_max"
            ),
            "source_propagator_typev_open_anchor_deviation_max": live_propagator.transfer_bundle.get(
                "typev_open_anchor_deviation_max"
            ),
            "source_propagator_typev_mode_mixing_norm": live_propagator.transfer_bundle.get(
                "typev_mode_mixing_norm"
            ),
            "source_propagator_vi0_transport_status": live_propagator.transfer_bundle.get(
                "vi0_transport_status"
            ),
            "source_propagator_vi0_structure_scale": live_propagator.transfer_bundle.get(
                "vi0_structure_scale"
            ),
            "source_propagator_vi0_directional_imbalance": live_propagator.transfer_bundle.get(
                "vi0_directional_imbalance"
            ),
            "source_propagator_vi0_shear_max": live_propagator.transfer_bundle.get(
                "vi0_shear_max"
            ),
            "source_propagator_vi0_mode_mixing_norm": live_propagator.transfer_bundle.get(
                "vi0_mode_mixing_norm"
            ),
            "source_propagator_vih_transport_status": live_propagator.transfer_bundle.get(
                "vih_transport_status"
            ),
            "source_propagator_vih_branch_flag": live_propagator.transfer_bundle.get(
                "vih_branch_flag"
            ),
            "source_propagator_vih_h_parameter": live_propagator.transfer_bundle.get(
                "vih_h_parameter"
            ),
            "source_propagator_vih_structure_scale": live_propagator.transfer_bundle.get(
                "vih_structure_scale"
            ),
            "source_propagator_vih_twist_scale": live_propagator.transfer_bundle.get(
                "vih_twist_scale"
            ),
            "source_propagator_vih_h_twist_scale": live_propagator.transfer_bundle.get(
                "vih_h_twist_scale"
            ),
            "source_propagator_vih_directional_imbalance": live_propagator.transfer_bundle.get(
                "vih_directional_imbalance"
            ),
            "source_propagator_vih_open_attenuation_min": live_propagator.transfer_bundle.get(
                "vih_open_attenuation_min"
            ),
            "source_propagator_vih_mode_mixing_norm": live_propagator.transfer_bundle.get(
                "vih_mode_mixing_norm"
            ),
            "source_propagator_viih_transport_status": live_propagator.transfer_bundle.get(
                "viih_transport_status"
            ),
            "source_propagator_viih_helical_pitch": live_propagator.transfer_bundle.get(
                "viih_helical_pitch"
            ),
            "source_propagator_viih_twist_scale": live_propagator.transfer_bundle.get(
                "viih_twist_scale"
            ),
            "source_propagator_viih_h_parameter": live_propagator.transfer_bundle.get(
                "viih_h_parameter"
            ),
            "source_propagator_viih_open_attenuation_min": live_propagator.transfer_bundle.get(
                "viih_open_attenuation_min"
            ),
            "source_propagator_viih_mode_mixing_norm": live_propagator.transfer_bundle.get(
                "viih_mode_mixing_norm"
            ),
            "source_propagator_typeviii_transport_status": live_propagator.transfer_bundle.get(
                "typeviii_transport_status"
            ),
            "source_propagator_typeviii_branch_flag": live_propagator.transfer_bundle.get(
                "typeviii_branch_flag"
            ),
            "source_propagator_typeviii_structure_scale": live_propagator.transfer_bundle.get(
                "typeviii_structure_scale"
            ),
            "source_propagator_typeviii_negative_axis_weight": live_propagator.transfer_bundle.get(
                "typeviii_negative_axis_weight"
            ),
            "source_propagator_typeviii_positive_axis_split": live_propagator.transfer_bundle.get(
                "typeviii_positive_axis_split"
            ),
            "source_propagator_typeviii_disc_radius_x_eq_tanh_xi": live_propagator.transfer_bundle.get(
                "typeviii_disc_radius_x_eq_tanh_xi"
            ),
            "source_propagator_typeviii_noncompact_attenuation_min": live_propagator.transfer_bundle.get(
                "typeviii_noncompact_attenuation_min"
            ),
            "source_propagator_typeviii_mode_mixing_norm": live_propagator.transfer_bundle.get(
                "typeviii_mode_mixing_norm"
            ),
            "source_propagator_typeviii_series_tags": live_propagator.transfer_bundle.get(
                "typeviii_series_tags"
            ),
            "source_propagator_typeviii_continuous_series_tag": live_propagator.transfer_bundle.get(
                "typeviii_continuous_series_tag"
            ),
            "source_propagator_typeix_transport_status": live_propagator.transfer_bundle.get(
                "typeix_transport_status"
            ),
            "source_propagator_typeix_branch_flag": live_propagator.transfer_bundle.get(
                "typeix_branch_flag"
            ),
            "source_propagator_typeix_curvature_scale": live_propagator.transfer_bundle.get(
                "typeix_curvature_scale"
            ),
            "source_propagator_typeix_positive_axis_anisotropy_split": live_propagator.transfer_bundle.get(
                "typeix_positive_axis_anisotropy_split"
            ),
            "source_propagator_typeix_discrete_j": live_propagator.transfer_bundle.get(
                "typeix_discrete_j"
            ),
            "source_propagator_typeix_spectral_eigenvalue_jj1": live_propagator.transfer_bundle.get(
                "typeix_spectral_eigenvalue_jj1"
            ),
            "source_propagator_typeix_invariant_volume": live_propagator.transfer_bundle.get(
                "typeix_invariant_volume"
            ),
            "source_propagator_typeix_wigner_d_j2_unit_amplitude": live_propagator.transfer_bundle.get(
                "typeix_wigner_d_j2_unit_amplitude"
            ),
            "source_propagator_typeix_compact_phase_max": live_propagator.transfer_bundle.get(
                "typeix_compact_phase_max"
            ),
            "source_propagator_typeix_spectral_envelope_min": live_propagator.transfer_bundle.get(
                "typeix_spectral_envelope_min"
            ),
            "source_propagator_typeix_spectral_envelope_max": live_propagator.transfer_bundle.get(
                "typeix_spectral_envelope_max"
            ),
            "source_propagator_typeix_mode_mixing_norm": live_propagator.transfer_bundle.get(
                "typeix_mode_mixing_norm"
            ),
            "source_propagator_typeix_discrete_representation_labels": live_propagator.transfer_bundle.get(
                "typeix_discrete_representation_labels"
            ),
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
            "collision_owner": str(
                result.solver_info.get("collision_owner", "unavailable")
            ),
            "collision_temperature_rhs_owner": str(
                result.solver_info.get("collision_temperature_rhs_owner", "unavailable")
            ),
            "collision_polarization_rhs_owner": str(
                result.solver_info.get("collision_polarization_rhs_owner", "unavailable")
            ),
            "collision_full_stokes_temperature_rhs_active": bool(
                result.solver_info.get("collision_full_stokes_temperature_rhs_active", False)
            ),
            "imex_full_rhs_fallback_steps": int(
                result.solver_info.get("imex_full_rhs_fallback_steps", 0)
            ),
            "imex_full_rhs_fallback_used": bool(
                result.solver_info.get("imex_full_rhs_fallback_used", False)
            ),
            "imex_min_accepted_step_mpc": result.solver_info.get(
                "imex_min_accepted_step_mpc"
            ),
            "imex_max_accepted_step_mpc": result.solver_info.get(
                "imex_max_accepted_step_mpc"
            ),
            "neutrino_hierarchy_mode": str(result.solver_info.get("neutrino_hierarchy_mode", "reduced_summary_only")),
            "neutrino_metric_feedback_owner": str(
                result.solver_info.get("neutrino_metric_feedback_owner", "unavailable")
            ),
            "neutrino_metric_feedback_status": str(
                result.solver_info.get("neutrino_metric_feedback_status", "unavailable")
            ),
            "neutrino_metric_feedback_evidence_passed": bool(
                result.solver_info.get("neutrino_metric_feedback_evidence_passed", False)
            ),
            "neutrino_metric_feedback_R_nu_min": float(
                result.solver_info.get("neutrino_metric_feedback_R_nu_min", 0.0)
            ),
            "neutrino_metric_feedback_R_nu_max": float(
                result.solver_info.get("neutrino_metric_feedback_R_nu_max", 0.0)
            ),
            "neutrino_metric_feedback_quadrupole_max_abs": float(
                result.solver_info.get("neutrino_metric_feedback_quadrupole_max_abs", 0.0)
            ),
            "neutrino_metric_feedback_rhs_max_abs": float(
                result.solver_info.get("neutrino_metric_feedback_rhs_max_abs", 0.0)
            ),
            "neutrino_metric_feedback_sample_count": int(
                result.solver_info.get("neutrino_metric_feedback_sample_count", 0)
            ),
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
            "layout_source_history_owner": str(
                result.solver_info.get("layout_source_history_owner", "unconsumed")
            ),
            "layout_source_history_sample_count": int(
                result.solver_info.get("layout_source_history_sample_count", 0)
            ),
            "residual_harmonic_orthogonal_bridge": str(
                result.solver_info.get("residual_harmonic_orthogonal_bridge", "disabled")
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
            "layout_local_matter_extension_owner": str(
                result.solver_info.get("layout_local_matter_extension_owner", "unconsumed")
            ),
            "layout_local_matter_mode_labels": list(
                result.solver_info.get("layout_local_matter_mode_labels", [])
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
            "layout_b_mode_payload_available": bool(
                result.solver_info.get("layout_b_mode_payload_available", False)
            ),
            "layout_b_mode_payload_status": str(
                result.solver_info.get("layout_b_mode_payload_status", "zero_filled_not_evolved")
            ),
            "layout_b_mode_proxy_norm": float(
                result.solver_info.get("layout_b_mode_proxy_norm", 0.0)
            ),
            "layout_b_mode_proxy_source": str(
                result.solver_info.get("layout_b_mode_proxy_source", "disabled")
            ),
            "layout_b_mode_integration_scheme": str(
                result.solver_info.get("layout_b_mode_integration_scheme", "")
            ),
            "layout_b_mode_history_sample_count": int(
                result.solver_info.get("layout_b_mode_history_sample_count", 0)
            ),
            "layout_b_mode_mode_labels": list(
                result.solver_info.get("layout_b_mode_mode_labels", [])
            ),
            "layout_b_mode_history_mode_labels": list(
                result.solver_info.get("layout_b_mode_history_mode_labels", [])
            ),
            "layout_auxiliary_coupling_passes": int(
                result.solver_info.get("layout_auxiliary_coupling_passes", 0)
            ),
            "layout_auxiliary_integration_scheme": str(
                result.solver_info.get("layout_auxiliary_integration_scheme", "")
            ),
            "layout_auxiliary_reduced_block_size": int(
                result.solver_info.get("layout_auxiliary_reduced_block_size", 0)
            ),
            "layout_auxiliary_bundle_owner": str(
                result.solver_info.get("layout_auxiliary_bundle_owner", "unconsumed")
            ),
            "layout_state_history_sample_count": int(
                result.solver_info.get("layout_state_history_sample_count", 0)
            ),
            "layout_state_history_size": int(
                result.solver_info.get("layout_state_history_size", 0)
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
            "scalar_metric_history_metadata": dict(
                result.solver_info.get("scalar_metric_history_metadata", {})
            ),
            "scalar_metric_history_owner": str(
                dict(result.solver_info.get("scalar_metric_history_metadata", {})).get(
                    "owner",
                    "unavailable",
                )
            ),
            "scalar_metric_photon_neutrino_monopole_coupled": bool(
                dict(result.solver_info.get("scalar_metric_history_metadata", {})).get(
                    "photon_neutrino_monopole_coupled",
                    False,
                )
            ),
            "scalar_metric_photon_neutrino_quadrupole_coupled": bool(
                dict(result.solver_info.get("scalar_metric_history_metadata", {})).get(
                    "photon_neutrino_quadrupole_coupled",
                    False,
                )
            ),
            "scalar_metric_photon_neutrino_scalar_streaming_coupled": bool(
                dict(result.solver_info.get("scalar_metric_history_metadata", {})).get(
                    "photon_neutrino_scalar_streaming_coupled",
                    False,
                )
            ),
            "scalar_metric_matter_continuity_coupled": bool(
                dict(result.solver_info.get("scalar_metric_history_metadata", {})).get(
                    "matter_continuity_coupled",
                    False,
                )
            ),
            "scalar_metric_baryon_euler_pressure_coupled": bool(
                dict(result.solver_info.get("scalar_metric_history_metadata", {})).get(
                    "baryon_euler_pressure_coupled",
                    False,
                )
            ),
            "startup_manifold_applied": bool(result.solver_info.get("startup_manifold_applied", False)),
            "checkpoint_enabled": bool(result.solver_info.get("checkpoint_enabled", False)),
            "checkpoint_write_count": int(result.solver_info.get("checkpoint_write_count", 0)),
            "restart_used": bool(result.solver_info.get("restart_used", False)),
            "restart_checkpoint_path": result.solver_info.get("restart_checkpoint_path"),
            "off_axis_support": off_axis_supported,
            "axis_aligned_tilt_support": True,
            "off_axis_fallback_applied": False,
            "off_axis_block_reason": None if off_axis_supported else "off_axis_not_closed",
            "b_mode_output_support": b_mode_output_support,
            "b_mode_block_reason": b_mode_block_reason,
            **b_source_projection_evidence,
            **b_projector_evidence,
            "exact_thomson_authority_path": exact_thomson_gate_passed,
            "exact_thomson_gate_passed": exact_thomson_gate_passed,
            "exact_thomson_operator_scope": exact_thomson_gate_metadata.get("operator_scope"),
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
            "backend_reduced_local_evaluator_available": bool(
                False
                if mode_ops is None
                else getattr(mode_ops, "metadata", {}).get("reduced_local_evaluator_available", False)
            ),
            "backend_reduced_harmonic_evaluator_available": bool(
                False
                if mode_ops is None
                else getattr(mode_ops, "metadata", {}).get("reduced_harmonic_evaluator_available", False)
            ),
            "backend_reduced_source_evaluator_available": bool(
                False
                if mode_ops is None
                else getattr(mode_ops, "metadata", {}).get("reduced_source_evaluator_available", False)
            ),
            "backend_contract_release_status": None
            if mode_ops is None
            else getattr(mode_ops, "metadata", {}).get("contract_release_status"),
            "ic_provenance_status": None
            if seed_pack is None
            else _ic_provenance_status_from_runtime(
                seed_pack=seed_pack,
                gate_registry=gate_registry,
                result=result,
            ),
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
            "canonical_projection_b_mode_labels": []
            if canonical_projection is None
            else list(getattr(canonical_projection, "metadata", {}).get("b_mode_labels", ())),
            "canonical_projection_b_history_mode_labels": []
            if canonical_projection is None
            else list(getattr(canonical_projection, "metadata", {}).get("b_history_mode_labels", ())),
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
            "canonical_projection_matter_mode_labels": []
            if canonical_projection is None
            else list(getattr(canonical_projection, "metadata", {}).get("matter_mode_labels", ())),
            "canonical_projection_matter_history_mode_labels": []
            if canonical_projection is None
            else list(
                getattr(canonical_projection, "metadata", {}).get("matter_history_mode_labels", ())
            ),
            **_mode_label_history_payload_summary(result),
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
    _attach_output_gate_metadata(output, gate_registry=gate_registry)
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
    a_lookup = _build_result_a_lookup(result)
    visibility_fn = _build_visibility_fn_from_a_lookup(species, a_lookup)
    if _requires_explicit_decomposed_los_sources(propagator_config):
        matrix_scope = "type_i" if structure_constants.label == "I" else "family_matrix"
        source_scope = (
            "tier_b_einstein_extracted_type_i_exact"
            if structure_constants.label == "I"
            else "tier_b_einstein_extracted_family_matrix_exact"
        )
        source_builder, source_builder_metadata = _build_tier_b_exact_type_i_source_builder(
            result,
            species=species,
            kappa_fn=_build_kappa_fn_from_a_lookup(species, a_lookup),
            visibility_fn=visibility_fn,
            source_builder_scope=source_scope,
            matrix_scope=matrix_scope,
        )
    else:
        source_builder, source_builder_metadata = _build_lowell_source_builder(
            result,
            species=species,
            visibility_fn=visibility_fn,
            scale_factor_owner="integration_result",
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
    b_source_projection_evidence = _b_mode_source_projection_evidence(live_propagator)
    b_source_known_zero = bool(
        b_source_projection_evidence["b_mode_source_projection_known_zero"]
    )
    b_mode_output_support = (
        "known_zero_source_projection_not_evolved"
        if b_source_known_zero
        else "zero_filled_without_b_mode_evidence"
    )
    b_mode_block_reason = (
        "b_mode_zero_supported_by_exact_source_projection"
        if b_source_known_zero
        else "b_mode_zero_filled_without_output_ready_source_projection"
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
            "b_mode_output_support": b_mode_output_support,
            "b_mode_block_reason": b_mode_block_reason,
            "b_mode_payload_status": "zero_filled_not_evolved",
            "b_mode_runtime_available": False,
            **b_source_projection_evidence,
            "k_grid_size": int(np.asarray(k_grid_mpc).size),
            "eta_grid_size": int(np.asarray(result.eta).size),
            "off_diagonal_strategy": off_diagonal_strategy,
            "limber_eta_sp_sign": limber_eta_sp_sign,
            "source_builder_scope": "theta0_plus_combined_polter_visibility_lowell_bridge",
            "source_propagator_status": live_propagator.config.temperature_transport.value,
            "source_propagator_requested_status": feature_flags.source_propagator.value,
            "source_propagator_rotation_status": live_propagator.config.polarization_rotation.value,
            "source_propagator_realization": live_propagator.config.kernel_family,
            "source_propagator_exactness": live_propagator.evidence.get("exactness"),
            "source_propagator_source_completeness_policy": live_propagator.transfer_bundle.get(
                "source_completeness_policy"
            ),
            "source_propagator_fail_closed_sources": (
                live_propagator.transfer_bundle.get("source_completeness_policy")
                == "explicit_required_fail_closed"
            ),
            "source_propagator_temperature_doppler_derivative": live_propagator.transfer_bundle.get(
                "temperature_source_doppler_derivative"
            ),
            "source_propagator_publication_output_claim_allowed": bool(
                live_propagator.evidence.get("output_claim_allowed", False)
            ),
            "source_propagator_statistics_claim_allowed": bool(
                live_propagator.evidence.get("statistics_claim_allowed", False)
            ),
            "source_propagator_block_reason": live_propagator.evidence.get("block_reason"),
            "source_propagator_helical_transport_status": live_propagator.transfer_bundle.get(
                "helical_transport_status"
            ),
            "source_propagator_helical_pitch": live_propagator.transfer_bundle.get(
                "helical_pitch"
            ),
            "source_propagator_helical_phase_max": live_propagator.transfer_bundle.get(
                "helical_phase_max"
            ),
            "source_propagator_polarization_basis_transport": live_propagator.transfer_bundle.get(
                "polarization_basis_transport"
            ),
            "source_propagator_helicity_mode_mixing_norm": live_propagator.transfer_bundle.get(
                "helicity_mode_mixing_norm"
            ),
            "source_propagator_nil_transport_status": live_propagator.transfer_bundle.get(
                "nil_transport_status"
            ),
            "source_propagator_nil_structure_scale": live_propagator.transfer_bundle.get(
                "nil_structure_scale"
            ),
            "source_propagator_nil_shear_max": live_propagator.transfer_bundle.get(
                "nil_shear_max"
            ),
            "source_propagator_nil_phase_max": live_propagator.transfer_bundle.get(
                "nil_phase_max"
            ),
            "source_propagator_nil_mode_mixing_norm": live_propagator.transfer_bundle.get(
                "nil_mode_mixing_norm"
            ),
            "source_propagator_typeiii_transport_status": live_propagator.transfer_bundle.get(
                "typeiii_transport_status"
            ),
            "source_propagator_typeiii_branch_flag": live_propagator.transfer_bundle.get(
                "typeiii_branch_flag"
            ),
            "source_propagator_typeiii_h_parameter": live_propagator.transfer_bundle.get(
                "typeiii_h_parameter"
            ),
            "source_propagator_typeiii_hyperbolic_scale": live_propagator.transfer_bundle.get(
                "typeiii_hyperbolic_scale"
            ),
            "source_propagator_typeiii_twist_scale": live_propagator.transfer_bundle.get(
                "typeiii_twist_scale"
            ),
            "source_propagator_typeiii_open_attenuation_min": live_propagator.transfer_bundle.get(
                "typeiii_open_attenuation_min"
            ),
            "source_propagator_typeiii_mode_mixing_norm": live_propagator.transfer_bundle.get(
                "typeiii_mode_mixing_norm"
            ),
            "source_propagator_typeiv_transport_status": live_propagator.transfer_bundle.get(
                "typeiv_transport_status"
            ),
            "source_propagator_typeiv_coordinate_order": live_propagator.transfer_bundle.get(
                "typeiv_coordinate_order"
            ),
            "source_propagator_typeiv_structure_scale": live_propagator.transfer_bundle.get(
                "typeiv_structure_scale"
            ),
            "source_propagator_typeiv_n3_scale": live_propagator.transfer_bundle.get(
                "typeiv_n3_scale"
            ),
            "source_propagator_typeiv_twist_scale": live_propagator.transfer_bundle.get(
                "typeiv_twist_scale"
            ),
            "source_propagator_typeiv_privileged_weight": live_propagator.transfer_bundle.get(
                "typeiv_privileged_weight"
            ),
            "source_propagator_typeiv_edge_attenuation_min": live_propagator.transfer_bundle.get(
                "typeiv_edge_attenuation_min"
            ),
            "source_propagator_typeiv_mode_mixing_norm": live_propagator.transfer_bundle.get(
                "typeiv_mode_mixing_norm"
            ),
            "source_propagator_typev_transport_status": live_propagator.transfer_bundle.get(
                "typev_transport_status"
            ),
            "source_propagator_typev_chart_metadata": live_propagator.transfer_bundle.get(
                "typev_chart_metadata"
            ),
            "source_propagator_typev_curvature_scale": live_propagator.transfer_bundle.get(
                "typev_curvature_scale"
            ),
            "source_propagator_typev_open_envelope_min": live_propagator.transfer_bundle.get(
                "typev_open_envelope_min"
            ),
            "source_propagator_typev_open_envelope_max": live_propagator.transfer_bundle.get(
                "typev_open_envelope_max"
            ),
            "source_propagator_typev_open_anchor_deviation_max": live_propagator.transfer_bundle.get(
                "typev_open_anchor_deviation_max"
            ),
            "source_propagator_typev_mode_mixing_norm": live_propagator.transfer_bundle.get(
                "typev_mode_mixing_norm"
            ),
            "source_propagator_vi0_transport_status": live_propagator.transfer_bundle.get(
                "vi0_transport_status"
            ),
            "source_propagator_vi0_structure_scale": live_propagator.transfer_bundle.get(
                "vi0_structure_scale"
            ),
            "source_propagator_vi0_directional_imbalance": live_propagator.transfer_bundle.get(
                "vi0_directional_imbalance"
            ),
            "source_propagator_vi0_shear_max": live_propagator.transfer_bundle.get(
                "vi0_shear_max"
            ),
            "source_propagator_vi0_mode_mixing_norm": live_propagator.transfer_bundle.get(
                "vi0_mode_mixing_norm"
            ),
            "source_propagator_vih_transport_status": live_propagator.transfer_bundle.get(
                "vih_transport_status"
            ),
            "source_propagator_vih_branch_flag": live_propagator.transfer_bundle.get(
                "vih_branch_flag"
            ),
            "source_propagator_vih_h_parameter": live_propagator.transfer_bundle.get(
                "vih_h_parameter"
            ),
            "source_propagator_vih_structure_scale": live_propagator.transfer_bundle.get(
                "vih_structure_scale"
            ),
            "source_propagator_vih_twist_scale": live_propagator.transfer_bundle.get(
                "vih_twist_scale"
            ),
            "source_propagator_vih_h_twist_scale": live_propagator.transfer_bundle.get(
                "vih_h_twist_scale"
            ),
            "source_propagator_vih_directional_imbalance": live_propagator.transfer_bundle.get(
                "vih_directional_imbalance"
            ),
            "source_propagator_vih_open_attenuation_min": live_propagator.transfer_bundle.get(
                "vih_open_attenuation_min"
            ),
            "source_propagator_vih_mode_mixing_norm": live_propagator.transfer_bundle.get(
                "vih_mode_mixing_norm"
            ),
            "source_propagator_viih_transport_status": live_propagator.transfer_bundle.get(
                "viih_transport_status"
            ),
            "source_propagator_viih_helical_pitch": live_propagator.transfer_bundle.get(
                "viih_helical_pitch"
            ),
            "source_propagator_viih_twist_scale": live_propagator.transfer_bundle.get(
                "viih_twist_scale"
            ),
            "source_propagator_viih_h_parameter": live_propagator.transfer_bundle.get(
                "viih_h_parameter"
            ),
            "source_propagator_viih_open_attenuation_min": live_propagator.transfer_bundle.get(
                "viih_open_attenuation_min"
            ),
            "source_propagator_viih_mode_mixing_norm": live_propagator.transfer_bundle.get(
                "viih_mode_mixing_norm"
            ),
            "source_propagator_typeviii_transport_status": live_propagator.transfer_bundle.get(
                "typeviii_transport_status"
            ),
            "source_propagator_typeviii_branch_flag": live_propagator.transfer_bundle.get(
                "typeviii_branch_flag"
            ),
            "source_propagator_typeviii_structure_scale": live_propagator.transfer_bundle.get(
                "typeviii_structure_scale"
            ),
            "source_propagator_typeviii_negative_axis_weight": live_propagator.transfer_bundle.get(
                "typeviii_negative_axis_weight"
            ),
            "source_propagator_typeviii_positive_axis_split": live_propagator.transfer_bundle.get(
                "typeviii_positive_axis_split"
            ),
            "source_propagator_typeviii_disc_radius_x_eq_tanh_xi": live_propagator.transfer_bundle.get(
                "typeviii_disc_radius_x_eq_tanh_xi"
            ),
            "source_propagator_typeviii_noncompact_attenuation_min": live_propagator.transfer_bundle.get(
                "typeviii_noncompact_attenuation_min"
            ),
            "source_propagator_typeviii_mode_mixing_norm": live_propagator.transfer_bundle.get(
                "typeviii_mode_mixing_norm"
            ),
            "source_propagator_typeviii_series_tags": live_propagator.transfer_bundle.get(
                "typeviii_series_tags"
            ),
            "source_propagator_typeviii_continuous_series_tag": live_propagator.transfer_bundle.get(
                "typeviii_continuous_series_tag"
            ),
            "source_propagator_typeix_transport_status": live_propagator.transfer_bundle.get(
                "typeix_transport_status"
            ),
            "source_propagator_typeix_branch_flag": live_propagator.transfer_bundle.get(
                "typeix_branch_flag"
            ),
            "source_propagator_typeix_curvature_scale": live_propagator.transfer_bundle.get(
                "typeix_curvature_scale"
            ),
            "source_propagator_typeix_positive_axis_anisotropy_split": live_propagator.transfer_bundle.get(
                "typeix_positive_axis_anisotropy_split"
            ),
            "source_propagator_typeix_discrete_j": live_propagator.transfer_bundle.get(
                "typeix_discrete_j"
            ),
            "source_propagator_typeix_spectral_eigenvalue_jj1": live_propagator.transfer_bundle.get(
                "typeix_spectral_eigenvalue_jj1"
            ),
            "source_propagator_typeix_invariant_volume": live_propagator.transfer_bundle.get(
                "typeix_invariant_volume"
            ),
            "source_propagator_typeix_wigner_d_j2_unit_amplitude": live_propagator.transfer_bundle.get(
                "typeix_wigner_d_j2_unit_amplitude"
            ),
            "source_propagator_typeix_compact_phase_max": live_propagator.transfer_bundle.get(
                "typeix_compact_phase_max"
            ),
            "source_propagator_typeix_spectral_envelope_min": live_propagator.transfer_bundle.get(
                "typeix_spectral_envelope_min"
            ),
            "source_propagator_typeix_spectral_envelope_max": live_propagator.transfer_bundle.get(
                "typeix_spectral_envelope_max"
            ),
            "source_propagator_typeix_mode_mixing_norm": live_propagator.transfer_bundle.get(
                "typeix_mode_mixing_norm"
            ),
            "source_propagator_typeix_discrete_representation_labels": live_propagator.transfer_bundle.get(
                "typeix_discrete_representation_labels"
            ),
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
    _attach_output_gate_metadata(output, gate_registry=gate_registry)
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
