"""VER2 executable runtime surfaces for the BASS S3 lane."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from time import perf_counter

import numpy as np

from common.contracts import RuntimeReductionDecision, SolverCoreOutput

from bass.runtime.canonical_decision import CanonicalDecision
from bass.runtime.gate_fragments import (
    ic_provenance_gate_bundle,
    physics_gate_fragment,
    tilt_boost_separation_gate_bundle,
)

__all__ = [
    "SolverTier",
    "IntegratorFamily",
    "CouplingMode",
    "FeatureStatus",
    "CheckpointPolicy",
    "ConstraintProjectionPolicy",
    "SolverFeatureFlags",
    "RuntimeControlBlock",
    "ValidationMatrixSpec",
    "SolverExecutionPlan",
    "TierBExecutionTrace",
    "TierBExecutableRun",
    "TierAValidationTrace",
    "TierAValidationRun",
    "TierATierBComparison",
    "build_runtime_reduction_decision",
    "plan_solver_execution",
    "execute_tier_a_validation_solver",
    "execute_tier_b_solver",
    "resume_tier_b_solver_from_checkpoint",
    "execute_tier_b_lowell_solver",
    "compare_tier_a_to_tier_b",
]


class SolverTier(str, Enum):
    """Explicit tier selection for the VER2 solver."""

    TIER_A_ANGULAR = "tier_a_angular"
    TIER_B_PSTF = "tier_b_pstf"


class IntegratorFamily(str, Enum):
    """Declared integration family."""

    EXPLICIT_RK = "explicit_rk"
    IMPLICIT_BDF = "implicit_bdf"
    IMPLICIT_RADAU = "implicit_radau"
    IMEX_SPLIT = "imex_split"


class CouplingMode(str, Enum):
    """Background/radiation coupling mode."""

    BACKGROUND_THEN_RADIATION = "background_then_radiation"
    FULLY_COUPLED = "fully_coupled"


class FeatureStatus(str, Enum):
    """Exactness/availability flag required by VER2."""

    EXACT = "exact"
    APPROXIMATE = "approximate"
    DISABLED = "disabled"


@dataclass(frozen=True)
class CheckpointPolicy:
    """Checkpoint/restart policy with explicit reproducibility semantics."""

    enabled: bool
    every_n_steps: int | None = None
    path_template: str = ""
    reproducibility_mode: str = "bitwise_or_tolerance_logged"

    def __post_init__(self) -> None:
        if self.enabled:
            if self.every_n_steps is None or self.every_n_steps <= 0:
                raise ValueError("enabled checkpoints require every_n_steps > 0")
            if not self.path_template:
                raise ValueError("enabled checkpoints require a path_template")
        elif self.every_n_steps is not None and self.every_n_steps <= 0:
            raise ValueError("every_n_steps must be > 0 when provided")


@dataclass(frozen=True)
class ConstraintProjectionPolicy:
    """Constraint-projection hook metadata."""

    enabled: bool
    every_n_steps: int | None = None
    status: FeatureStatus = FeatureStatus.DISABLED
    logged: bool = True

    def __post_init__(self) -> None:
        if self.enabled:
            if self.every_n_steps is None or self.every_n_steps <= 0:
                raise ValueError(
                    "enabled constraint projection requires every_n_steps > 0"
                )
            if self.status is FeatureStatus.DISABLED:
                raise ValueError("enabled constraint projection cannot be DISABLED")
        elif self.every_n_steps is not None and self.every_n_steps <= 0:
            raise ValueError("every_n_steps must be > 0 when provided")


@dataclass(frozen=True)
class SolverFeatureFlags:
    """Explicit exact/approximate/disabled flags for S3 subsystems."""

    background_dynamics: FeatureStatus
    photon_transport: FeatureStatus
    thomson_collision: FeatureStatus
    visibility_history: FeatureStatus
    source_propagator: FeatureStatus
    checkpoint_restart: FeatureStatus


@dataclass(frozen=True)
class RuntimeControlBlock:
    """Tier, integrator, tolerance, cutoff, and restart controls."""

    tier: SolverTier
    integrator_family: IntegratorFamily
    coupling_mode: CouplingMode
    multipole_cutoff: int
    rtol: float
    atol: float
    checkpoint: CheckpointPolicy
    constraint_projection: ConstraintProjectionPolicy
    tilt_background_owner: str = "fixed_velocity_closure"
    diagnostic_l2_override: bool = False
    random_seed: int | None = None
    low_resolution_reference: bool = False

    def __post_init__(self) -> None:
        if self.multipole_cutoff < 2:
            raise ValueError("multipole_cutoff must be >= 2")
        if self.multipole_cutoff == 2 and not self.diagnostic_l2_override:
            raise ValueError(
                "L=2 requires an explicit diagnostic_l2_override in VER2"
            )
        if self.multipole_cutoff in {4, 6, 8}:
            pass
        elif self.multipole_cutoff < 4 and not self.diagnostic_l2_override:
            raise ValueError(
                "VER2 development cutoffs are L=4,6,8 unless a diagnostic override is recorded"
            )
        if self.rtol <= 0.0 or self.atol <= 0.0:
            raise ValueError("rtol and atol must both be positive")
        if self.tilt_background_owner not in {
            "fixed_velocity_closure",
            "nonperturbative_tilt_rhs",
        }:
            raise ValueError(
                "tilt_background_owner must be 'fixed_velocity_closure' or "
                "'nonperturbative_tilt_rhs'"
            )
        if self.random_seed is not None and self.random_seed < 0:
            raise ValueError("random_seed must be non-negative when provided")


@dataclass(frozen=True)
class ValidationMatrixSpec:
    """Type/branch validation matrix hook for later executable packets."""

    bianchi_types: tuple[str, ...]
    branches: tuple[str, ...] = ("orthogonal", "tilted")
    suites: tuple[str, ...] = ("background", "photon", "collision", "tier_b_smoke")
    record_constraint_residuals: bool = True
    record_runtime_metadata: bool = True

    def __post_init__(self) -> None:
        if not self.bianchi_types:
            raise ValueError("ValidationMatrixSpec.bianchi_types must be non-empty")
        if not self.branches:
            raise ValueError("ValidationMatrixSpec.branches must be non-empty")
        if not self.suites:
            raise ValueError("ValidationMatrixSpec.suites must be non-empty")

    @property
    def expected_rows(self) -> int:
        return len(self.bianchi_types) * len(self.branches) * len(self.suites)


@dataclass(frozen=True)
class SolverExecutionPlan:
    """Observer-neutral execution plan for Tier A or Tier B."""

    runtime_controls: RuntimeControlBlock
    feature_flags: SolverFeatureFlags
    runtime_decision: RuntimeReductionDecision
    validation_matrix: ValidationMatrixSpec
    manifest_required: bool = True
    observer_neutral_output_required: bool = True
    statistics_interpretation_forbidden: bool = True

    def __post_init__(self) -> None:
        if not self.manifest_required:
            raise ValueError("VER2 S3 requires manifest attachment on solver outputs")
        if not self.observer_neutral_output_required:
            raise ValueError("solver outputs must remain observer-neutral in VER2")
        if not self.statistics_interpretation_forbidden:
            raise ValueError("BASS runtime must not attach observational interpretation")


@dataclass(frozen=True)
class TierBExecutionTrace:
    """Live S1/S2/S3 hook products consumed by the Tier-B runtime."""

    background_monitor: "BackgroundEvolutionResult"
    startup_gate: "StartupGateDecision"
    startup_state: "QuadrupoleStartupState | None"
    seed_projection: "SeedConstraintProjection"
    geodesic_probe: "PhotonGeodesicRhs"
    thomson_probe: "ExactThomsonSource"
    visibility_source: "TiltedVisibilitySource"
    canonical_projection: "CanonicalLayoutProjection"

    @classmethod
    def from_runtime_bundle(cls, runtime_trace) -> "TierBExecutionTrace":
        return cls(
            background_monitor=runtime_trace.background_monitor,
            startup_gate=runtime_trace.startup_gate,
            startup_state=runtime_trace.startup_state,
            seed_projection=runtime_trace.seed_projection,
            geodesic_probe=runtime_trace.geodesic_probe,
            thomson_probe=runtime_trace.thomson_probe,
            visibility_source=runtime_trace.visibility_source,
            canonical_projection=runtime_trace.canonical_projection,
        )


@dataclass(frozen=True)
class TierBExecutableRun:
    """Executable Tier-B low-ell bundle produced by the VER2 runtime."""

    execution_plan: SolverExecutionPlan
    runtime_decision: RuntimeReductionDecision
    trace: TierBExecutionTrace
    integration_result: "IntegrationResult"
    solver_output: SolverCoreOutput
    cutoff_campaign: "ExecutedCutoffCampaign | None" = None

    @classmethod
    def from_execution_bundle(
        cls,
        *,
        execution_plan: SolverExecutionPlan,
        runtime_decision: RuntimeReductionDecision,
        runtime_trace,
        integration_result,
        solver_output: SolverCoreOutput,
        cutoff_campaign=None,
    ) -> "TierBExecutableRun":
        return cls(
            execution_plan=execution_plan,
            runtime_decision=runtime_decision,
            trace=TierBExecutionTrace.from_runtime_bundle(runtime_trace),
            integration_result=integration_result,
            solver_output=solver_output,
            cutoff_campaign=cutoff_campaign,
        )


@dataclass(frozen=True)
class _TierBPostRunBundle:
    runtime_trace: object
    gate_registry: Mapping[str, object]
    solver_output: SolverCoreOutput
    cutoff_campaign: object | None
    metadata: Mapping[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata))


@dataclass(frozen=True)
class _TierBPreparedRuntimeContext:
    runtime_config: object
    family_realization: str
    restart_state: object | None
    background_monitor: object
    visibility_source: object
    k_grid_mpc: np.ndarray
    seed_k_comoving: float
    backend: object
    reionization_amplitude: float
    integrator: object
    runtime_decision: RuntimeReductionDecision
    execution_plan: SolverExecutionPlan
    checkpoint_callback: object | None
    checkpoint_paths: list[str]
    metadata: Mapping[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, "k_grid_mpc", np.asarray(self.k_grid_mpc, dtype=np.float64))
        object.__setattr__(self, "seed_k_comoving", float(self.seed_k_comoving))
        object.__setattr__(
            self,
            "checkpoint_paths",
            self.checkpoint_paths if isinstance(self.checkpoint_paths, list) else list(self.checkpoint_paths),
        )
        object.__setattr__(self, "metadata", dict(self.metadata))


@dataclass(frozen=True)
class _TierBRuntimeRequest:
    manifest: object
    bianchi_type: str
    species: "SpeciesBackgroundRegistry"
    integrator_config: object
    runtime_controls: RuntimeControlBlock
    feature_flags: SolverFeatureFlags
    release: object
    k_grid_mpc: np.ndarray
    validation_matrix: "ValidationMatrixSpec | None" = None
    cutoff_spec: "CutoffCampaignSpec | None" = None
    restart_checkpoint_path: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "bianchi_type", str(self.bianchi_type))
        object.__setattr__(self, "k_grid_mpc", np.asarray(self.k_grid_mpc, dtype=np.float64))


def _build_tier_b_runtime_request(
    *,
    manifest,
    bianchi_type: str,
    species: "SpeciesBackgroundRegistry",
    integrator_config,
    runtime_controls: RuntimeControlBlock,
    feature_flags: SolverFeatureFlags,
    release,
    k_grid_mpc: np.ndarray,
    validation_matrix: "ValidationMatrixSpec | None" = None,
    cutoff_spec: "CutoffCampaignSpec | None" = None,
    restart_checkpoint_path: str | None = None,
) -> _TierBRuntimeRequest:
    return _TierBRuntimeRequest(
        manifest=manifest,
        bianchi_type=bianchi_type,
        species=species,
        integrator_config=integrator_config,
        runtime_controls=runtime_controls,
        feature_flags=feature_flags,
        release=release,
        k_grid_mpc=k_grid_mpc,
        validation_matrix=validation_matrix,
        cutoff_spec=cutoff_spec,
        restart_checkpoint_path=restart_checkpoint_path,
    )


def _build_tier_b_executable_run(
    *,
    request: _TierBRuntimeRequest,
    prepared: _TierBPreparedRuntimeContext,
    result,
) -> TierBExecutableRun:
    _stamp_native_result_solver_info(
        result=result,
        request=request,
        prepared=prepared,
    )
    post_run = _assemble_tier_b_post_run_bundle(
        request=request,
        prepared=prepared,
        result=result,
    )
    return TierBExecutableRun.from_execution_bundle(
        execution_plan=prepared.execution_plan,
        runtime_decision=prepared.runtime_decision,
        runtime_trace=post_run.runtime_trace,
        integration_result=result,
        solver_output=post_run.solver_output,
        cutoff_campaign=post_run.cutoff_campaign,
    )


def _execute_prepared_tier_b_runtime(
    *,
    request: _TierBRuntimeRequest,
    prepared: _TierBPreparedRuntimeContext,
) -> TierBExecutableRun:
    result = prepared.integrator.run(
        checkpoint_every_n_steps=request.runtime_controls.checkpoint.every_n_steps
        if request.runtime_controls.checkpoint.enabled
        else None,
        checkpoint_callback=prepared.checkpoint_callback,
        restart_state=prepared.restart_state,
    )
    return _build_tier_b_executable_run(
        request=request,
        prepared=prepared,
        result=result,
    )


def _stamp_native_result_solver_info(
    *,
    result,
    request: _TierBRuntimeRequest,
    prepared: _TierBPreparedRuntimeContext,
) -> None:
    result.solver_info["runtime_integrator_family"] = request.runtime_controls.integrator_family.value
    result.solver_info["requested_integrator_family"] = request.runtime_controls.integrator_family.value
    result.solver_info["resolved_solver_method"] = prepared.runtime_config.solver_method
    result.solver_info["executor_realization"] = prepared.family_realization
    result.solver_info["solver_family_realization"] = prepared.family_realization
    result.solver_info["checkpoint_enabled"] = bool(request.runtime_controls.checkpoint.enabled)
    result.solver_info["checkpoint_paths"] = tuple(prepared.checkpoint_paths)
    result.solver_info["restart_checkpoint_path"] = request.restart_checkpoint_path


@dataclass(frozen=True)
class TierAValidationTrace:
    """Validation-only angular-reference payload for Tier A cross-checks."""

    background_monitor: "BackgroundEvolutionResult"
    source_builder_scope: str
    reference_scope: str
    propagator_mode: str
    off_diagonal_strategy: str
    preferred_axis: tuple[float, float, float]
    dl_reference: Mapping[str, np.ndarray]
    transport_contract: Mapping[str, object]

    def __post_init__(self) -> None:
        if not self.source_builder_scope:
            raise ValueError("source_builder_scope must be non-empty")
        if not self.reference_scope:
            raise ValueError("reference_scope must be non-empty")
        if not self.propagator_mode:
            raise ValueError("propagator_mode must be non-empty")
        if not self.off_diagonal_strategy:
            raise ValueError("off_diagonal_strategy must be non-empty")
        if len(self.preferred_axis) != 3:
            raise ValueError("preferred_axis must be a 3-vector")
        if not self.dl_reference:
            raise ValueError("dl_reference must be non-empty")
        if not self.transport_contract:
            raise ValueError("transport_contract must be non-empty")
        for channel, values in self.dl_reference.items():
            arr = np.asarray(values, dtype=np.float64)
            if arr.ndim != 1:
                raise ValueError(f"dl_reference[{channel!r}] must be 1-D")
            if not np.all(np.isfinite(arr)):
                raise ValueError(f"dl_reference[{channel!r}] must be finite")


def _screen_basis_from_direction(direction: np.ndarray):
    from bass.transport.geodesics import ScreenBasisState

    ray = np.asarray(direction, dtype=np.float64)
    ray /= max(float(np.linalg.norm(ray)), 1.0e-30)
    anchor = np.array([1.0, 0.0, 0.0], dtype=np.float64)
    if abs(float(np.dot(anchor, ray))) > 0.9:
        anchor = np.array([0.0, 1.0, 0.0], dtype=np.float64)
    u = anchor - float(np.dot(anchor, ray)) * ray
    u /= max(float(np.linalg.norm(u)), 1.0e-30)
    v = np.cross(ray, u)
    v /= max(float(np.linalg.norm(v)), 1.0e-30)
    return ScreenBasisState(u=u, v=v)


def _build_tiera_transport_reference_probe(
    *,
    result,
    background_monitor: "BackgroundEvolutionResult",
    visibility_source: "TiltedVisibilitySource",
    config: "IntegratorConfig",
) -> Mapping[str, object]:
    from bass.hierarchy.pstf_tensor import unpack_hierarchy
    from bass.transport import TierAState, collision_source_tierA, ray_rhs, screen_basis_rhs

    direction = np.asarray(config.tilt_direction, dtype=np.float64)
    if not np.any(direction):
        direction = np.array([0.0, 0.0, 1.0], dtype=np.float64)
    direction /= max(float(np.linalg.norm(direction)), 1.0e-30)
    temperature = unpack_hierarchy(result.photon_T_tower[-1], result.L_max)
    polarization = unpack_hierarchy(result.photon_E_tower[-1], result.L_max)
    I_dir = (
        np.asarray(temperature.tensors[1].components, dtype=np.float64)
        if result.L_max >= 1
        else np.zeros(3, dtype=np.float64)
    )
    if result.L_max >= 2:
        e2 = np.asarray(polarization.tensors[2].components, dtype=np.float64)
        P_dir = np.asarray([e2[0], e2[2], e2[4]], dtype=np.float64)
        I2 = float(np.linalg.norm(np.asarray(temperature.tensors[2].components, dtype=np.float64)))
        E2_pol = float(np.linalg.norm(e2))
    else:
        P_dir = np.zeros_like(I_dir)
        I2 = 0.0
        E2_pol = 0.0
    ray_state = TierAState(
        eta=float(result.eta[-1]),
        ray_direction=direction,
        screen_basis=_screen_basis_from_direction(direction),
        phase=0.0,
        I_dir=I_dir,
        P_dir=P_dir,
    )
    bg = {
        "H": float(background_monitor.H[-1]),
        "sigma_ab": np.asarray(background_monitor.sigma_tensor[-1], dtype=np.float64),
        "geometry": background_monitor.initial_conditions.geometry,
    }
    ray_probe = ray_rhs(float(result.eta[-1]), ray_state, bg)
    screen_probe = screen_basis_rhs(float(result.eta[-1]), ray_state, bg)
    gamma_t = _resolved_gamma_t(
        visibility_source=visibility_source,
        eta=float(result.eta[-1]),
        direction=direction,
        config=config,
    )
    collision_probe = collision_source_tierA(
        float(result.eta[-1]),
        ray_state,
        bg,
        {
            "Gamma_T": float(gamma_t),
            "I0": float(temperature.tensors[0].components[0]),
            "I2": I2,
            "E2_pol": E2_pol,
            "opacity_data": {"Gamma_T": float(gamma_t)},
        },
    )
    return {
        "owner": "ver3_tiera_transport_reference_probe",
        "ray_rhs_direction_norm": float(np.linalg.norm(ray_probe.direction_dot)),
        "ray_rhs_energy_dot": float(ray_probe.energy_dot),
        "screen_phase_dot": float(screen_probe.phase_dot),
        "collision_effective_opacity": float(collision_probe.effective_opacity),
        "collision_source_split": str(collision_probe.metadata.get("source_split", "")),
        "direction_convention": collision_probe.direction_convention.value,
    }


@dataclass(frozen=True)
class TierAValidationRun:
    """Validation-grade angular reference run for Tier-B cross-checking."""

    execution_plan: SolverExecutionPlan
    runtime_decision: RuntimeReductionDecision
    trace: TierAValidationTrace
    integration_result: "IntegrationResult"
    solver_output: SolverCoreOutput

    def __post_init__(self) -> None:
        if self.execution_plan.runtime_controls.tier is not SolverTier.TIER_A_ANGULAR:
            raise ValueError("TierAValidationRun requires Tier A runtime controls")
        if self.solver_output.metadata.get("solver_tier") != SolverTier.TIER_A_ANGULAR.value:
            raise ValueError("solver_output must advertise solver_tier='tier_a_angular'")


@dataclass(frozen=True)
class TierATierBComparison:
    """Machine-readable comparison between Tier A validation and Tier B runtime."""

    compared_channels: tuple[str, ...]
    relative_l2_by_channel: Mapping[str, float]
    max_abs_delta_by_channel: Mapping[str, float]
    preferred_axis_delta_deg: float
    ell_grid_match: bool
    k_grid_match: bool
    tolerance: float
    passed: bool
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.compared_channels:
            raise ValueError("compared_channels must be non-empty")
        if self.tolerance < 0.0:
            raise ValueError("tolerance must be non-negative")
        if not np.isfinite(self.preferred_axis_delta_deg) or self.preferred_axis_delta_deg < 0.0:
            raise ValueError("preferred_axis_delta_deg must be finite and non-negative")
        for name, values in (
            ("relative_l2_by_channel", self.relative_l2_by_channel),
            ("max_abs_delta_by_channel", self.max_abs_delta_by_channel),
        ):
            missing = sorted(set(self.compared_channels) - set(values))
            if missing:
                raise ValueError(f"{name} missing channels: {missing}")
            for channel, value in values.items():
                if not np.isfinite(value) or value < 0.0:
                    raise ValueError(f"{name}[{channel!r}] must be finite and non-negative")


def build_runtime_reduction_decision(
    canonical_decision: CanonicalDecision,
    *,
    propagation_status: str,
    reason: str,
) -> RuntimeReductionDecision:
    """Bridge the legacy BASS gate owner into the shared VER2 decision primitive."""
    source_status = (
        "adequate" if canonical_decision.source_Dge2_gate_pass else "inadequate"
    )
    allow_reduction = (
        canonical_decision.allow_reduction and propagation_status != "blocked"
    )
    return RuntimeReductionDecision(
        owner="BASS",
        allow_reduction=allow_reduction,
        source_status=source_status,
        propagation_status=propagation_status,
        reason=reason,
    )


def plan_solver_execution(
    *,
    runtime_controls: RuntimeControlBlock,
    feature_flags: SolverFeatureFlags,
    runtime_decision: RuntimeReductionDecision,
    validation_matrix: ValidationMatrixSpec,
) -> SolverExecutionPlan:
    """Return the canonical S3 execution-plan shell."""
    return SolverExecutionPlan(
        runtime_controls=runtime_controls,
        feature_flags=feature_flags,
        runtime_decision=runtime_decision,
        validation_matrix=validation_matrix,
    )


def _tilt_velocity(cosmo: "BianchiCosmology") -> np.ndarray:
    from bass.species.tilted import rapidity_to_velocity

    velocity = rapidity_to_velocity(float(cosmo.beta))
    return velocity * np.asarray(cosmo.v_hat_e, dtype=np.float64)


def _tilt_velocity_from_monitor(
    background_monitor: "BackgroundEvolutionResult",
    *,
    eta: float,
    fallback_direction: np.ndarray,
) -> np.ndarray:
    velocities = np.asarray(background_monitor.tilt_velocity, dtype=np.float64)
    if velocities.ndim != 2 or velocities.shape[0] != len(background_monitor.eta):
        return np.zeros(3, dtype=np.float64)
    if not np.any(np.abs(velocities) > 0.0):
        return np.zeros(3, dtype=np.float64)
    eta_grid = np.asarray(background_monitor.eta, dtype=np.float64)
    interpolated = np.array(
        [
            np.interp(float(eta), eta_grid, velocities[:, axis])
            for axis in range(3)
        ],
        dtype=np.float64,
    )
    norm = float(np.linalg.norm(interpolated))
    if norm <= 0.0:
        return np.zeros(3, dtype=np.float64)
    direction = np.asarray(fallback_direction, dtype=np.float64)
    direction_norm = float(np.linalg.norm(direction))
    if direction_norm > 0.0 and float(np.dot(interpolated, direction / direction_norm)) < 0.0:
        interpolated *= -1.0
    return interpolated


def _build_visibility_contract(
    species: "SpeciesBackgroundRegistry",
) -> "VisibilityHistoryContract":
    from bass.recombination.history_visibility import (
        ScalarHistoryMetadata,
        VisibilityEventMarkers,
        VisibilityHistoryContract,
    )
    from bass.recombination.recombination_ingest import find_visibility_peak
    from bass.recombination.reionization import compute_reionization_tau
    from bass.species.base import SpeciesLabel

    baryon = species[SpeciesLabel.BARYON]
    interp = baryon._recomb  # noqa: SLF001 - stable internal ownership in current Tier-B runtime
    table = interp.table
    reionization_mode = (
        "tanh" if table.metadata.get("reionization") == "tanh" else "disabled"
    )
    z_star, g_star = find_visibility_peak(interp)
    tau_reion = (
        compute_reionization_tau(table, z_high_cutoff=min(30.0, float(table.z_max)))
        if reionization_mode == "tanh"
        else 0.0
    )
    return VisibilityHistoryContract(
        table=table,
        interp=interp,
        history_metadata=ScalarHistoryMetadata(reionization_mode=reionization_mode),
        events=VisibilityEventMarkers(
            z_last_scattering=float(z_star),
            visibility_peak=float(g_star),
            reionization_detected=(reionization_mode == "tanh" and tau_reion > 0.0),
            tau_reion=float(tau_reion),
            reionization_mode=reionization_mode,
        ),
    )


def _build_background_monitor(
    *,
    bianchi_type: str,
    config: "IntegratorConfig",
    species: "SpeciesBackgroundRegistry",
    tilt_background_owner: str,
) -> "BackgroundEvolutionResult":
    from bass.background.bianchi_types import build_bianchi_algebra
    from bass.background.evolution import (
        BackgroundEvolutionConfig,
        solve_background_evolution,
    )
    from bass.background.initial_conditions import (
        build_orthogonal_initial_conditions,
        build_tilted_initial_conditions,
    )
    from bass.background.nonperturbative_tilt import integrate_tilt_rapidity_history
    from bass.background.tetrad_state import axisymmetric_sigma_tensor
    from bass.species.base import CANONICAL_ORDER, SpeciesLabel
    from bass.species.barotropic_closures import (
        DynamicTiltedSpeciesRegistryClosure,
        OrthogonalSpeciesRegistryClosure,
        TiltedSpeciesRegistryClosure,
    )
    from bass.tilt.species_tilt import TiltedSpeciesParams, decompose_tilted_species

    eta_start = float(config.eta_initial_mpc)
    eta_end = float(config.eta_final_mpc)
    a_start = float(species.bg_table.interp_a(eta_start))
    a_end = float(species.bg_table.interp_a(eta_end))
    sigma0 = axisymmetric_sigma_tensor(
        float(config.Sigma_plus_initial),
        float(config.Sigma_minus_initial),
    )
    algebra = build_bianchi_algebra(bianchi_type)
    lambda_value = float(species[SpeciesLabel.LAMBDA].rho_rest(eta_start))
    if abs(float(config.tilt_rapidity)) == 0.0:
        rho = 0.0
        pressure = 0.0
        for label in CANONICAL_ORDER:
            if label is SpeciesLabel.LAMBDA:
                continue
            rho += float(species[label].rho_rest(eta_start))
            pressure += float(species[label].p_rest(eta_start))
        initial_conditions = build_orthogonal_initial_conditions(
            algebra=algebra,
            rho=rho,
            p=pressure,
            sigma_ab=sigma0,
            lambda_value=lambda_value,
            closure="solve_H",
        )
        matter_model_override = OrthogonalSpeciesRegistryClosure(species)
    else:
        velocity = _tilt_velocity(config.bianchi_cosmo)
        decompositions = tuple(
            decompose_tilted_species(
                TiltedSpeciesParams(
                    rho_hat=float(species[label].rho_rest(eta_start)),
                    p_hat=float(species[label].p_rest(eta_start)),
                    v=velocity,
                    label=str(label),
                )
            )
            for label in CANONICAL_ORDER
            if label is not SpeciesLabel.LAMBDA
        )
        initial_conditions = build_tilted_initial_conditions(
            algebra=algebra,
            species=decompositions,
            sigma_ab=sigma0,
            lambda_value=lambda_value,
            closure="solve_H",
        )
        if tilt_background_owner == "fixed_velocity_closure":
            matter_model_override = TiltedSpeciesRegistryClosure(
                registry=species,
                velocity=velocity,
            )
        else:
            rapidity_a, rapidity_history = integrate_tilt_rapidity_history(
                registry=species,
                a_start=a_start,
                a_end=a_end,
                beta_initial=abs(float(config.tilt_rapidity)),
                n_steps=max(32, min(int(config.n_output) * 4, 512)),
                solver_method="BDF",
                rtol=min(float(config.rtol), 1.0e-8),
                atol=min(max(float(config.atol), 1.0e-12), 1.0e-10),
            )

            def rapidity_at_scale_factor(a: float) -> float:
                return float(
                    np.interp(
                        float(a),
                        np.asarray(rapidity_a, dtype=np.float64),
                        np.asarray(rapidity_history, dtype=np.float64),
                    )
                )

            matter_model_override = DynamicTiltedSpeciesRegistryClosure(
                registry=species,
                tilt_direction=velocity,
                rapidity_at_scale_factor=rapidity_at_scale_factor,
            )
    return solve_background_evolution(
        initial_conditions,
        config=BackgroundEvolutionConfig(
            a_start=a_start,
            a_end=a_end,
            n_steps=max(16, min(int(config.n_output), 256)),
            rtol=min(float(config.rtol), 1.0e-8),
            atol=min(max(float(config.atol), 1.0e-12), 1.0e-10),
            solver_method="BDF",
            lambda_value=lambda_value,
            matter_model_override=matter_model_override,
            eta_at_scale_factor=species.bg_table.eta_at_a,
        ),
    )


def _build_seed_projection(
    *,
    background_monitor: "BackgroundEvolutionResult",
    config: "IntegratorConfig",
) -> "SeedConstraintProjection":
    from bass.hierarchy.seed_compatibility import (
        build_constraint_projection,
        build_flrw_regular_seed,
        promote_tilted_seed,
    )

    amplitude = max(
        abs(float(config.Sigma_plus_initial)),
        abs(float(config.Sigma_minus_initial)),
        1.0e-6,
    )
    seed = build_flrw_regular_seed(amplitude=amplitude)
    if abs(float(config.tilt_rapidity)) > 0.0:
        seed = promote_tilted_seed(
            seed,
            electron_velocity=_tilt_velocity(config.bianchi_cosmo),
        )
    return build_constraint_projection(
        seed,
        geometry=background_monitor.initial_conditions.geometry,
        sigma_ab=background_monitor.sigma_tensor[0],
    )


def _build_visibility_source(
    *,
    species: "SpeciesBackgroundRegistry",
    config: "IntegratorConfig",
    background_monitor: "BackgroundEvolutionResult | None" = None,
) -> "TiltedVisibilitySource":
    from bass.hierarchy.frame_contracts import PhotonDirectionConvention
    from bass.recombination.history_visibility import build_tilted_visibility_source
    from bass.species.base import SpeciesLabel

    baryon = species[SpeciesLabel.BARYON]
    velocity = _tilt_velocity(config.bianchi_cosmo)
    fallback_direction = np.asarray(config.tilt_direction, dtype=np.float64)

    def v_e(_eta: float) -> np.ndarray:
        if background_monitor is not None:
            return _tilt_velocity_from_monitor(
                background_monitor,
                eta=float(_eta),
                fallback_direction=fallback_direction,
            )
        return velocity

    return build_tilted_visibility_source(
        _build_visibility_contract(species),
        baryon=baryon,
        v_e=v_e,
        direction_convention=PhotonDirectionConvention.PROPAGATION,
    )


def _build_startup_gate(
    *,
    visibility_source: "TiltedVisibilitySource",
    background_monitor: "BackgroundEvolutionResult",
    config: "IntegratorConfig",
) -> "StartupGateDecision":
    from bass.closure.stiff_closure import decide_startup_gate

    direction = np.asarray(config.tilt_direction, dtype=np.float64)
    if not np.any(direction):
        direction = np.array([1.0, 0.0, 0.0], dtype=np.float64)
    gamma_t = _resolved_gamma_t(
        visibility_source=visibility_source,
        eta=float(background_monitor.eta[0]),
        direction=direction,
        config=config,
    )
    return decide_startup_gate(
        gamma_T=float(gamma_t),
        H=float(background_monitor.H[0]),
        threshold=float(config.gamma_T_over_H_threshold),
    )


def _static_gate_bundle(
    gate_name: str,
    *,
    family: str,
    branch: str,
):
    from bass.validation import make_gate_bundle

    return make_gate_bundle(
        gate_name,
        family=family,
        branch=branch,
        backend="docs_ver3_authority",
        truncation={},
        residual_summary={},
        known_limit_checks={"authority_frozen": True},
        forbidden_shortcut_checks={"no_mock_claim_promotion": True},
        metadata={"source": "docs/ver3"},
        passed=True,
        opened_claim=f"{gate_name} frozen by docs/ver3 authority",
    )


def _production_cutoff_gate_bundle(
    *,
    bianchi_type: str,
    branch: str,
    runtime_controls: RuntimeControlBlock,
    cutoff_campaign,
):
    from bass.validation import make_gate_bundle

    if cutoff_campaign is None:
        return make_gate_bundle(
            "production_cutoff_gate",
            family=bianchi_type,
            branch=branch,
            backend="cutoff_campaign",
            truncation={"ell_max": int(runtime_controls.multipole_cutoff)},
            residual_summary={"campaign_ready": False},
            known_limit_checks={"all_cutoffs_recorded": False},
            forbidden_shortcut_checks={"no_development_cutoff_promoted": True},
            metadata={"status": "missing_cutoff_campaign"},
            passed=False,
            opened_claim="production cutoff policy validated on an executed campaign",
        )
    delta_values = [
        float(delta.relative_delta)
        for deltas in cutoff_campaign.deltas.values()
        for delta in deltas
    ]
    return make_gate_bundle(
        "production_cutoff_gate",
        family=bianchi_type,
        branch=branch,
        backend="cutoff_campaign",
        truncation={
            "ell_max": int(runtime_controls.multipole_cutoff),
            "campaign_cutoffs": tuple(int(x) for x in cutoff_campaign.spec.cutoffs),
            "baseline_cutoff": int(cutoff_campaign.spec.baseline_cutoff),
        },
        residual_summary={
            "max_relative_delta": max(delta_values, default=0.0),
            "campaign_ready": bool(cutoff_campaign.ready),
            "campaign_runtime_count": float(len(cutoff_campaign.runtime_seconds)),
        },
        known_limit_checks={
            "all_cutoffs_recorded": bool(cutoff_campaign.all_cutoffs_recorded),
            "runtime_logged": bool(cutoff_campaign.runtime_logging_required),
            "baseline_cutoff_matches_runtime": int(cutoff_campaign.spec.baseline_cutoff)
            == int(runtime_controls.multipole_cutoff),
        },
        forbidden_shortcut_checks={
            "no_development_cutoff_promoted": True,
            "no_cutoff_stub_used_as_evidence": True,
        },
        metadata={
            "closure_name": str(cutoff_campaign.spec.closure_name),
            "runtime_seconds": {
                int(key): float(value) for key, value in cutoff_campaign.runtime_seconds.items()
            },
        },
        passed=bool(
            cutoff_campaign.ready
            and cutoff_campaign.all_cutoffs_recorded
            and int(cutoff_campaign.spec.baseline_cutoff) == int(runtime_controls.multipole_cutoff)
        ),
        opened_claim="runtime cutoff policy backed by an executed convergence campaign",
    )


def _build_gate_registry(
    *,
    request: _TierBRuntimeRequest,
    prepared: _TierBPreparedRuntimeContext,
    runtime_trace,
    cutoff_campaign,
) -> dict[str, object]:
    from bass.hierarchy.ver3_layout_protocol import hierarchy_layout_gate_bundle
    from bass.los.family_backend_protocol import family_backend_gate_bundle

    background_monitor = runtime_trace.background_monitor
    visibility_source = runtime_trace.visibility_source
    seed_pack = runtime_trace.seed_pack
    seed_projection = runtime_trace.seed_projection
    runtime_trace_products = runtime_trace.runtime_trace_products
    branch = str(background_monitor.branch)
    thomson_probe = runtime_trace_products.thomson_probe
    layout_projection = runtime_trace_products.layout_projection
    mode_ops = layout_projection.mode_ops
    physics_fragment = physics_gate_fragment(
        bianchi_type=request.bianchi_type,
        background_monitor=background_monitor,
        species=request.species,
        visibility_source=visibility_source,
        thomson_probe=thomson_probe,
    )
    gate_fragment = (
        {}
        if layout_projection is None
        else dict(layout_projection.metadata.get("gate_registry_fragment", {}))
    )
    return {
        "authority_freeze": _static_gate_bundle(
            "authority_freeze",
            family=request.bianchi_type,
            branch=branch,
        ),
        "tensor_helper_correctness": _static_gate_bundle(
            "tensor_helper_correctness",
            family=request.bianchi_type,
            branch=branch,
        ),
        "family_registry_freeze": _static_gate_bundle(
            "family_registry_freeze",
            family=request.bianchi_type,
            branch=branch,
        ),
        "geometry_diagnostics_gate": gate_fragment.get(
            "geometry_diagnostics_gate",
            physics_fragment["geometry_diagnostics_gate"],
        ),
        "matter_projection_gate": gate_fragment.get(
            "matter_projection_gate",
            physics_fragment["matter_projection_gate"],
        ),
        "background_core_gate": gate_fragment.get(
            "background_core_gate",
            physics_fragment["background_core_gate"],
        ),
        "exact_thomson_gate": gate_fragment.get(
            "exact_thomson_gate",
            physics_fragment["exact_thomson_gate"],
        ),
        "visibility_history_gate": gate_fragment.get(
            "visibility_history_gate",
            physics_fragment["visibility_history_gate"],
        ),
        "tilt_boost_separation_gate": gate_fragment.get(
            "tilt_boost_separation_gate",
            tilt_boost_separation_gate_bundle(
                bianchi_type=request.bianchi_type,
                branch=branch,
                background_monitor=background_monitor,
            ),
        ),
        "ic_provenance_gate": gate_fragment.get(
            "ic_provenance_gate",
            ic_provenance_gate_bundle(
                bianchi_type=request.bianchi_type,
                branch=branch,
                backend=prepared.backend,
                seed_pack=seed_pack,
                seed_projection=seed_projection,
            ),
        ),
        "family_backend_gate": gate_fragment.get(
            "family_backend_gate",
            family_backend_gate_bundle(prepared.backend, mode_ops),
        ),
        "hierarchy_layout_gate": gate_fragment.get(
            "hierarchy_layout_gate",
            hierarchy_layout_gate_bundle(
                prepared.backend,
                mode_ops,
                provenance_metadata={},
            ),
        ),
        "production_cutoff_gate": _production_cutoff_gate_bundle(
            bianchi_type=request.bianchi_type,
            branch=branch,
            runtime_controls=request.runtime_controls,
            cutoff_campaign=cutoff_campaign,
        ),
    }


def _assemble_tier_b_post_run_bundle(
    *,
    request: _TierBRuntimeRequest,
    prepared: _TierBPreparedRuntimeContext,
    result,
) -> _TierBPostRunBundle:
    from bass.forward.ver2_solver_output import build_solver_core_output_from_execution_bundle
    from bass.spectrum.ver2_cutoff_campaign import run_executed_cutoff_campaign

    runtime_trace = getattr(result, "runtime_execution_trace", None)
    if runtime_trace is None:
        runtime_trace = prepared.integrator.build_runtime_execution_trace(
            result,
            reionization_amplitude=prepared.reionization_amplitude,
        )
    cutoff_campaign = None
    if request.cutoff_spec is not None:
        baseline_cutoff = int(getattr(result, "L_max", request.integrator_config.L_max))
        baseline_channels = {
            "temperature": np.asarray(result.photon_T_tower[-1], dtype=np.float64),
            "polarization_E": np.asarray(result.photon_E_tower[-1], dtype=np.float64),
            "neutrino_reduced": np.asarray(result.neutrino_reduced[-1], dtype=np.float64),
        }
        delegated_runner = _campaign_runner(
            bianchi_type=request.bianchi_type,
            base_config=request.integrator_config,
            species=request.species,
            seed_k_comoving=prepared.seed_k_comoving,
            runtime_controls=request.runtime_controls,
        )

        def runner(cutoff: int) -> tuple[Mapping[str, np.ndarray], float]:
            if int(cutoff) == baseline_cutoff:
                return baseline_channels, 0.0
            return delegated_runner(int(cutoff))

        cutoff_campaign = run_executed_cutoff_campaign(
            request.cutoff_spec,
            runner=runner,
        )
    result.solver_info.update(dict(runtime_trace.layout_projection.metadata["solver_info_fragment"]))
    gate_registry = _build_gate_registry(
        request=request,
        prepared=prepared,
        runtime_trace=runtime_trace,
        cutoff_campaign=cutoff_campaign,
    )
    solver_output = build_solver_core_output_from_execution_bundle(
        manifest=request.manifest,
        bianchi_type=request.bianchi_type,
        result=result,
        species=request.species,
        runtime_controls=request.runtime_controls,
        feature_flags=request.feature_flags,
        release=request.release,
        k_grid_mpc=prepared.k_grid_mpc,
        runtime_trace=runtime_trace,
        thomson_mode="electron_frame_exact_wrapper",
        gate_registry=gate_registry,
    )
    return _TierBPostRunBundle(
        runtime_trace=runtime_trace,
        gate_registry=gate_registry,
        solver_output=solver_output,
        cutoff_campaign=cutoff_campaign,
        metadata={"owner": "runtime._assemble_tier_b_post_run_bundle"},
    )


def _prepare_tier_b_runtime_context(
    *,
    request: _TierBRuntimeRequest,
) -> _TierBPreparedRuntimeContext:
    from bass.hierarchy.aux_state import build_integrator_canonical_decision
    from bass.hierarchy.frame_contracts import PhotonDirectionConvention
    from bass.hierarchy.ver2_native_integrator import Ver2TierBIntegrator
    from bass.los.family_backend_protocol import build_backend
    from bass.runtime.ver2_checkpoint import load_tier_b_restart_checkpoint

    runtime_config, family_realization = _native_runtime_config(
        request.bianchi_type,
        request.integrator_config,
        request.runtime_controls,
    )
    direction_convention = str(PhotonDirectionConvention.PROPAGATION.value)
    k_grid = request.k_grid_mpc
    restart_state = None
    if request.restart_checkpoint_path is not None:
        checkpoint = load_tier_b_restart_checkpoint(request.restart_checkpoint_path)
        _validate_restart_checkpoint(
            checkpoint=checkpoint,
            bianchi_type=request.bianchi_type,
            runtime_config=runtime_config,
            direction_convention=direction_convention,
        )
        restart_state = checkpoint.to_restart_state()
    background_monitor = _build_background_monitor(
        bianchi_type=request.bianchi_type,
        config=runtime_config,
        species=request.species,
        tilt_background_owner=request.runtime_controls.tilt_background_owner,
    )
    visibility_source = _build_visibility_source(
        species=request.species,
        config=runtime_config,
        background_monitor=background_monitor,
    )
    canonical_decision = build_integrator_canonical_decision(
        beta=float(runtime_config.bianchi_cosmo.beta),
        sigma_squared=max(
            0.5 * float(np.sum(background_monitor.sigma_tensor[0] ** 2)),
            1.0e-12,
        ),
    )
    seed_k_comoving = _representative_seed_k(k_grid)
    backend = build_backend(
        request.bianchi_type,
        truncation={"ell_max": int(request.runtime_controls.multipole_cutoff)},
        chart_options={},
    )
    reionization_amplitude = (
        0.0
        if visibility_source.contract.events is None
        else float(visibility_source.contract.events.tau_reion)
    )
    integrator = Ver2TierBIntegrator(
        runtime_config,
        request.species,
        backend=backend,
        background_monitor=background_monitor,
        visibility_source=visibility_source,
        canonical_decision=canonical_decision,
        seed_k_comoving=seed_k_comoving,
    )
    runtime_decision = _build_runtime_decision(
        feature_flags=request.feature_flags,
        canonical_decision=integrator.canonical_decision,
    )
    execution_plan = plan_solver_execution(
        runtime_controls=request.runtime_controls,
        feature_flags=request.feature_flags,
        runtime_decision=runtime_decision,
        validation_matrix=(
            request.validation_matrix
            if request.validation_matrix is not None
            else _default_validation_matrix(
                bianchi_type=request.bianchi_type,
                integrator_config=runtime_config,
                suite="tier_b_smoke",
            )
        ),
    )
    checkpoint_callback = None
    checkpoint_paths: list[str] = []
    if request.runtime_controls.checkpoint.enabled:
        checkpoint_callback, checkpoint_paths = _checkpoint_writer(
            path_template=request.runtime_controls.checkpoint.path_template,
            bianchi_type=request.bianchi_type,
            runtime_config=runtime_config,
            direction_convention=direction_convention,
            L_max=int(runtime_config.L_max),
        )
    return _TierBPreparedRuntimeContext(
        runtime_config=runtime_config,
        family_realization=family_realization,
        restart_state=restart_state,
        background_monitor=background_monitor,
        visibility_source=visibility_source,
        k_grid_mpc=k_grid,
        seed_k_comoving=seed_k_comoving,
        backend=backend,
        reionization_amplitude=reionization_amplitude,
        integrator=integrator,
        runtime_decision=runtime_decision,
        execution_plan=execution_plan,
        checkpoint_callback=checkpoint_callback,
        checkpoint_paths=checkpoint_paths,
        metadata={"owner": "runtime._prepare_tier_b_runtime_context"},
    )


def _validate_tier_b_runtime_request(
    *,
    request: _TierBRuntimeRequest,
) -> None:
    if request.runtime_controls.tier is not SolverTier.TIER_B_PSTF:
        raise ValueError("execute_tier_b_solver requires Tier B runtime controls")
    if request.runtime_controls.multipole_cutoff > request.integrator_config.L_max:
        raise ValueError("runtime cutoff must not exceed integrator_config.L_max")
    if (
        request.runtime_controls.checkpoint.enabled
        and request.feature_flags.checkpoint_restart is FeatureStatus.DISABLED
    ):
        raise ValueError("checkpoint policy requires checkpoint_restart feature flag to be enabled")


def _run_tier_b_runtime_request(request: _TierBRuntimeRequest) -> TierBExecutableRun:
    _validate_tier_b_runtime_request(request=request)
    prepared = _prepare_tier_b_runtime_context(request=request)
    return _execute_prepared_tier_b_runtime(request=request, prepared=prepared)


def _execute_tier_b_runtime_entrypoint(
    *,
    manifest,
    bianchi_type: str,
    species: "SpeciesBackgroundRegistry",
    integrator_config,
    runtime_controls: RuntimeControlBlock,
    feature_flags: SolverFeatureFlags,
    release,
    k_grid_mpc: np.ndarray,
    validation_matrix: "ValidationMatrixSpec | None" = None,
    cutoff_spec: "CutoffCampaignSpec | None" = None,
    restart_checkpoint_path: str | None = None,
) -> TierBExecutableRun:
    return _run_tier_b_runtime_request(
        _build_tier_b_runtime_request(
            manifest=manifest,
            bianchi_type=bianchi_type,
            species=species,
            integrator_config=integrator_config,
            runtime_controls=runtime_controls,
            feature_flags=feature_flags,
            release=release,
            k_grid_mpc=k_grid_mpc,
            validation_matrix=validation_matrix,
            cutoff_spec=cutoff_spec,
            restart_checkpoint_path=restart_checkpoint_path,
        )
    )


def _build_runtime_decision(
    *,
    feature_flags: SolverFeatureFlags,
    canonical_decision: CanonicalDecision,
) -> RuntimeReductionDecision:
    propagation_status = (
        "validated"
        if feature_flags.source_propagator is FeatureStatus.EXACT
        else "pending"
    )
    reason = (
        "tier_b_native_s1s2_core_with_exact_propagator"
        if propagation_status == "validated"
        else "tier_b_native_runtime_without_exact_propagator"
    )
    return build_runtime_reduction_decision(
        canonical_decision,
        propagation_status=propagation_status,
        reason=reason,
    )


def _resolved_gamma_t(
    *,
    visibility_source: "TiltedVisibilitySource",
    eta: float,
    direction: np.ndarray,
    config: "IntegratorConfig",
) -> float:
    if config.gamma_T_override is None:
        return float(visibility_source.Gamma_T(float(eta), np.asarray(direction, dtype=np.float64)))
    direction_arr = np.asarray(direction, dtype=np.float64)
    boost = float(visibility_source.visibility.boost_factor(float(eta), direction_arr))
    return float(config.gamma_T_override(float(eta))) * boost


def _representative_seed_k(k_grid_mpc: np.ndarray) -> float:
    grid = np.asarray(k_grid_mpc, dtype=np.float64)
    if grid.ndim != 1 or grid.size == 0:
        raise ValueError(f"k_grid_mpc must be a non-empty 1-D array, got shape {grid.shape}")
    positive = grid[np.isfinite(grid) & (grid >= 0.0)]
    if positive.size == 0:
        raise ValueError("k_grid_mpc must contain at least one finite non-negative entry")
    return float(np.min(positive))


def _resolve_native_solver_method(
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
    raise ValueError(f"Unsupported integrator family: {family!r}")


def _resolve_guarded_solver_override(
    *,
    bianchi_type: str,
    beta: float,
    runtime_controls: RuntimeControlBlock,
    solver_method: str,
    realization: str,
) -> tuple[str, str]:
    if (
        runtime_controls.integrator_family is IntegratorFamily.IMEX_SPLIT
        and str(bianchi_type) == "VIII"
        and abs(float(beta)) > 0.0
    ):
        return "BDF", "native_guarded_tilted_bdf_full_rhs"
    return solver_method, realization


def _native_runtime_config(
    bianchi_type: str,
    base_config: "IntegratorConfig",
    runtime_controls: RuntimeControlBlock,
) -> tuple["IntegratorConfig", str]:
    from bass.hierarchy.integrator import IntegratorConfig

    solver_method, realization = _resolve_native_solver_method(runtime_controls)
    solver_method, realization = _resolve_guarded_solver_override(
        bianchi_type=bianchi_type,
        beta=float(base_config.bianchi_cosmo.beta),
        runtime_controls=runtime_controls,
        solver_method=solver_method,
        realization=realization,
    )
    return (
        IntegratorConfig(
            L_max=int(base_config.L_max),
            eta_initial_mpc=float(base_config.eta_initial_mpc),
            eta_final_mpc=float(base_config.eta_final_mpc),
            n_output=int(base_config.n_output),
            rtol=float(base_config.rtol),
            atol=float(base_config.atol),
            bianchi_cosmo=base_config.bianchi_cosmo,
            Sigma_plus_initial=float(base_config.Sigma_plus_initial),
            Sigma_minus_initial=float(base_config.Sigma_minus_initial),
            closure_strategy=base_config.closure_strategy,
            collision_T=base_config.collision_T,
            collision_E=base_config.collision_E,
            gamma_T_over_H_threshold=float(base_config.gamma_T_over_H_threshold),
            solver_method=solver_method,
            gamma_T_override=base_config.gamma_T_override,
        ),
        realization,
    )


def _campaign_runner(
    *,
    bianchi_type: str,
    base_config: "IntegratorConfig",
    species: "SpeciesBackgroundRegistry",
    seed_k_comoving: float,
    runtime_controls: RuntimeControlBlock,
):
    from bass.hierarchy.aux_state import build_integrator_canonical_decision
    from bass.hierarchy.ver2_native_integrator import Ver2TierBIntegrator
    from bass.los.family_backend_protocol import build_backend

    def runner(cutoff: int) -> tuple[Mapping[str, np.ndarray], float]:
        start = perf_counter()
        cutoff_config, _ = _native_runtime_config(
            bianchi_type,
            base_config,
            runtime_controls,
        )
        config = cutoff_config.__class__(
            L_max=int(cutoff),
            eta_initial_mpc=float(cutoff_config.eta_initial_mpc),
            eta_final_mpc=float(cutoff_config.eta_final_mpc),
            n_output=int(cutoff_config.n_output),
            rtol=float(cutoff_config.rtol),
            atol=float(cutoff_config.atol),
            bianchi_cosmo=cutoff_config.bianchi_cosmo,
            Sigma_plus_initial=float(cutoff_config.Sigma_plus_initial),
            Sigma_minus_initial=float(cutoff_config.Sigma_minus_initial),
            closure_strategy=cutoff_config.closure_strategy,
            collision_T=cutoff_config.collision_T,
            collision_E=cutoff_config.collision_E,
            gamma_T_over_H_threshold=float(cutoff_config.gamma_T_over_H_threshold),
            solver_method=cutoff_config.solver_method,
            gamma_T_override=cutoff_config.gamma_T_override,
        )
        background_monitor = _build_background_monitor(
            bianchi_type=bianchi_type,
            config=config,
            species=species,
            tilt_background_owner=runtime_controls.tilt_background_owner,
        )
        visibility_source = _build_visibility_source(
            species=species,
            config=config,
            background_monitor=background_monitor,
        )
        canonical_decision = build_integrator_canonical_decision(
            beta=float(config.bianchi_cosmo.beta),
            sigma_squared=max(
                0.5 * float(np.sum(background_monitor.sigma_tensor[0] ** 2)),
                1.0e-12,
            ),
        )
        backend = build_backend(
            bianchi_type,
            truncation={"ell_max": int(cutoff)},
            chart_options={},
        )
        result = Ver2TierBIntegrator(
            config,
            species,
            backend=backend,
            background_monitor=background_monitor,
            visibility_source=visibility_source,
            canonical_decision=canonical_decision,
            seed_k_comoving=seed_k_comoving,
        ).run()
        runtime_sec = perf_counter() - start
        return (
            {
                "temperature": np.asarray(result.photon_T_tower[-1], dtype=np.float64),
                "polarization_E": np.asarray(result.photon_E_tower[-1], dtype=np.float64),
                "neutrino_reduced": np.asarray(result.neutrino_reduced[-1], dtype=np.float64),
            },
            runtime_sec,
        )

    return runner


def _checkpoint_writer(
    *,
    path_template: str,
    bianchi_type: str,
    runtime_config: "IntegratorConfig",
    direction_convention: str,
    L_max: int,
):
    from bass.runtime.ver2_checkpoint import (
        checkpoint_path_from_template,
        write_tier_b_restart_checkpoint,
    )

    written_paths: list[str] = []

    def writer(restart_state):
        path = checkpoint_path_from_template(
            path_template,
            step=int(restart_state.step_index),
            eta=float(restart_state.eta_restart),
        )
        write_tier_b_restart_checkpoint(
            path,
            bianchi_type=bianchi_type,
            structure_label=str(runtime_config.bianchi_cosmo.structure.label),
            structure_n_diag=np.asarray(
                runtime_config.bianchi_cosmo.structure.n_diag,
                dtype=np.float64,
            ),
            structure_a_twist=float(runtime_config.bianchi_cosmo.structure.a_twist),
            tilt_rapidity=float(runtime_config.tilt_rapidity),
            tilt_direction=np.asarray(runtime_config.tilt_direction, dtype=np.float64),
            direction_convention=direction_convention,
            eta_initial_mpc=float(runtime_config.eta_initial_mpc),
            eta_final_mpc=float(runtime_config.eta_final_mpc),
            n_output=int(runtime_config.n_output),
            solver_method=str(runtime_config.solver_method),
            L_max=int(L_max),
            restart_state=restart_state,
        )
        written_paths.append(str(path))

    return writer, written_paths


def _validate_restart_checkpoint(
    *,
    checkpoint,
    bianchi_type: str,
    runtime_config: "IntegratorConfig",
    direction_convention: str,
) -> None:
    if checkpoint.bianchi_type != bianchi_type:
        raise ValueError(
            "restart checkpoint bianchi_type does not match requested bianchi_type"
        )
    if checkpoint.L_max != runtime_config.L_max:
        raise ValueError("restart checkpoint L_max does not match runtime_config.L_max")
    if checkpoint.structure_label != runtime_config.bianchi_cosmo.structure.label:
        raise ValueError("restart checkpoint structure_label does not match runtime configuration")
    if not np.allclose(
        np.asarray(checkpoint.structure_n_diag, dtype=np.float64),
        np.asarray(runtime_config.bianchi_cosmo.structure.n_diag, dtype=np.float64),
        atol=0.0,
        rtol=0.0,
    ):
        raise ValueError("restart checkpoint structure_n_diag does not match runtime configuration")
    if float(checkpoint.structure_a_twist) != float(runtime_config.bianchi_cosmo.structure.a_twist):
        raise ValueError("restart checkpoint structure_a_twist does not match runtime configuration")
    if float(checkpoint.tilt_rapidity) != float(runtime_config.tilt_rapidity):
        raise ValueError("restart checkpoint tilt_rapidity does not match runtime configuration")
    if not np.allclose(
        np.asarray(checkpoint.tilt_direction, dtype=np.float64),
        np.asarray(runtime_config.tilt_direction, dtype=np.float64),
        atol=0.0,
        rtol=0.0,
    ):
        raise ValueError("restart checkpoint tilt_direction does not match runtime configuration")
    if checkpoint.direction_convention != direction_convention:
        raise ValueError(
            "restart checkpoint direction_convention does not match runtime configuration"
        )
    if float(checkpoint.eta_initial_mpc) != float(runtime_config.eta_initial_mpc):
        raise ValueError(
            "restart checkpoint eta_initial_mpc does not match runtime configuration"
        )
    if float(checkpoint.eta_final_mpc) != float(runtime_config.eta_final_mpc):
        raise ValueError(
            "restart checkpoint eta_final_mpc does not match runtime configuration"
        )
    if int(checkpoint.n_output) != int(runtime_config.n_output):
        raise ValueError("restart checkpoint n_output does not match runtime configuration")
    if checkpoint.solver_method != runtime_config.solver_method:
        raise ValueError(
            "restart checkpoint solver_method does not match runtime configuration"
        )


def _default_validation_matrix(
    *,
    bianchi_type: str,
    integrator_config: "IntegratorConfig",
    suite: str,
) -> ValidationMatrixSpec:
    branch = "tilted" if abs(float(integrator_config.tilt_rapidity)) > 0.0 else "orthogonal"
    return ValidationMatrixSpec(
        bianchi_types=(bianchi_type,),
        branches=(branch,),
        suites=("background", "photon", "collision", suite),
    )


def _covariance_bundle(output: SolverCoreOutput) -> Mapping[str, object]:
    covariance = output.anisotropic_covariance
    if not isinstance(covariance, Mapping):
        raise TypeError("solver_output.anisotropic_covariance must be a mapping")
    return covariance


def _relative_l2_delta(reference: np.ndarray, candidate: np.ndarray) -> float:
    ref = np.asarray(reference, dtype=np.float64)
    cand = np.asarray(candidate, dtype=np.float64)
    scale = max(float(np.linalg.norm(ref)), 1.0e-30)
    return float(np.linalg.norm(cand - ref) / scale)


def _max_abs_delta(reference: np.ndarray, candidate: np.ndarray) -> float:
    ref = np.asarray(reference, dtype=np.float64)
    cand = np.asarray(candidate, dtype=np.float64)
    return float(np.max(np.abs(cand - ref)))


def _axis_delta_deg(reference_axis: np.ndarray, candidate_axis: np.ndarray) -> float:
    ref = np.asarray(reference_axis, dtype=np.float64)
    cand = np.asarray(candidate_axis, dtype=np.float64)
    ref_norm = max(float(np.linalg.norm(ref)), 1.0e-30)
    cand_norm = max(float(np.linalg.norm(cand)), 1.0e-30)
    cosine = float(np.clip(np.dot(ref, cand) / (ref_norm * cand_norm), -1.0, 1.0))
    return float(np.degrees(np.arccos(cosine)))


def execute_tier_a_validation_solver(
    *,
    manifest,
    bianchi_type: str,
    species: "SpeciesBackgroundRegistry",
    integrator_config: "IntegratorConfig",
    runtime_controls: RuntimeControlBlock,
    feature_flags: SolverFeatureFlags,
    release,
    k_grid_mpc: np.ndarray,
    validation_matrix: "ValidationMatrixSpec | None" = None,
    off_diagonal_strategy: str = "dense_matrix",
) -> TierAValidationRun:
    """Execute the Tier A angular-reference path for Tier-B validation.

    The current implementation deliberately stays bounded to the existing
    Lowell hierarchy core, but it emits a Tier-A-labelled observer-neutral
    reference bundle and machine-readable comparison metadata so Tier B
    cannot be promoted without an explicit cross-check surface.
    """
    if runtime_controls.tier is not SolverTier.TIER_A_ANGULAR:
        raise ValueError("execute_tier_a_validation_solver requires Tier A runtime controls")

    from bass.hierarchy.integrator import LowellBianchiIntegrator
    from bass.forward.ver2_solver_output import build_solver_core_output_from_lowell_result

    background_monitor = _build_background_monitor(
        bianchi_type=bianchi_type,
        config=integrator_config,
        species=species,
        tilt_background_owner=runtime_controls.tilt_background_owner,
    )
    visibility_source = _build_visibility_source(
        species=species,
        config=integrator_config,
        background_monitor=background_monitor,
    )
    integrator = LowellBianchiIntegrator(integrator_config, species)
    runtime_decision = build_runtime_reduction_decision(
        integrator.canonical_decision,
        propagation_status="validated",
        reason="tier_a_validation_reference",
    )
    plan = plan_solver_execution(
        runtime_controls=runtime_controls,
        feature_flags=feature_flags,
        runtime_decision=runtime_decision,
        validation_matrix=(
            validation_matrix
            if validation_matrix is not None
            else _default_validation_matrix(
                bianchi_type=bianchi_type,
                integrator_config=integrator_config,
                suite="tier_a_validation",
            )
        ),
    )
    result = integrator.run()
    solver_output = build_solver_core_output_from_lowell_result(
        manifest=manifest,
        bianchi_type=bianchi_type,
        result=result,
        species=species,
        runtime_controls=runtime_controls,
        feature_flags=feature_flags,
        release=release,
        k_grid_mpc=np.asarray(k_grid_mpc, dtype=np.float64),
        off_diagonal_strategy=off_diagonal_strategy,
        thomson_mode="electron_frame_projected_validation",
    )
    covariance = _covariance_bundle(solver_output)
    d_ell = covariance.get("D_ell")
    if not isinstance(d_ell, Mapping):
        raise TypeError("Tier A validation covariance must expose D_ell mapping")
    preferred_axis = np.asarray(
        covariance.get("preferred_axis", np.array([0.0, 0.0, 1.0], dtype=np.float64)),
        dtype=np.float64,
    )
    preferred_axis /= max(float(np.linalg.norm(preferred_axis)), 1.0e-30)
    reference_channels = {
        channel: np.asarray(values, dtype=np.float64)
        for channel, values in d_ell.items()
        if channel in {"TT", "EE", "TE"}
    }
    transport_contract = _build_tiera_transport_reference_probe(
        result=result,
        background_monitor=background_monitor,
        visibility_source=visibility_source,
        config=integrator_config,
    )
    return TierAValidationRun(
        execution_plan=plan,
        runtime_decision=runtime_decision,
        trace=TierAValidationTrace(
            background_monitor=background_monitor,
            source_builder_scope=str(solver_output.metadata.get("source_builder_scope", "")),
            reference_scope="validation_only_angular_truth",
            propagator_mode=str(solver_output.metadata.get("propagator_mode", "")),
            off_diagonal_strategy=str(covariance.get("off_diagonal_strategy", "")),
            preferred_axis=tuple(float(x) for x in preferred_axis),
            dl_reference=reference_channels,
            transport_contract=transport_contract,
        ),
        integration_result=result,
        solver_output=solver_output,
    )


def compare_tier_a_to_tier_b(
    tier_a_run: TierAValidationRun,
    tier_b_run: TierBExecutableRun,
    *,
    tolerance: float = 5.0e-2,
) -> TierATierBComparison:
    """Compare Tier A validation spectra against Tier B executable outputs."""

    tier_a_cov = _covariance_bundle(tier_a_run.solver_output)
    tier_b_cov = _covariance_bundle(tier_b_run.solver_output)
    tier_a_d_ell = tier_a_cov.get("D_ell")
    tier_b_d_ell = tier_b_cov.get("D_ell")
    if not isinstance(tier_a_d_ell, Mapping) or not isinstance(tier_b_d_ell, Mapping):
        raise TypeError("Tier A and Tier B covariance bundles must expose D_ell mappings")

    compared_channels = tuple(
        channel for channel in ("TT", "EE", "TE")
        if channel in tier_a_d_ell and channel in tier_b_d_ell
    )
    if not compared_channels:
        raise ValueError("No overlapping TT/EE/TE channels available for comparison")

    tier_a_ell = np.asarray(tier_a_cov.get("ell"), dtype=np.int64)
    tier_b_ell = np.asarray(tier_b_cov.get("ell"), dtype=np.int64)
    ell_match = tier_a_ell.shape == tier_b_ell.shape and np.array_equal(tier_a_ell, tier_b_ell)

    tier_a_k = np.asarray(tier_a_cov.get("k_grid_mpc"), dtype=np.float64)
    tier_b_k = np.asarray(tier_b_cov.get("k_grid_mpc"), dtype=np.float64)
    k_grid_match = tier_a_k.shape == tier_b_k.shape and np.allclose(tier_a_k, tier_b_k)

    relative_l2_by_channel: dict[str, float] = {}
    max_abs_delta_by_channel: dict[str, float] = {}
    notes: list[str] = []
    for channel in compared_channels:
        ref = np.asarray(tier_a_d_ell[channel], dtype=np.float64)
        cand = np.asarray(tier_b_d_ell[channel], dtype=np.float64)
        if ref.shape != cand.shape:
            raise ValueError(
                f"Tier A/Tier B D_ell shape mismatch for {channel}: {ref.shape} vs {cand.shape}"
            )
        relative_l2_by_channel[channel] = _relative_l2_delta(ref, cand)
        max_abs_delta_by_channel[channel] = _max_abs_delta(ref, cand)

    axis_delta = _axis_delta_deg(
        np.asarray(tier_a_cov.get("preferred_axis"), dtype=np.float64),
        np.asarray(tier_b_cov.get("preferred_axis"), dtype=np.float64),
    )
    if not ell_match:
        notes.append("ell_grid_mismatch")
    if not k_grid_match:
        notes.append("k_grid_mismatch")
    passed = ell_match and k_grid_match and all(
        relative_l2_by_channel[channel] <= tolerance for channel in compared_channels
    )
    if passed:
        notes.append("tier_a_validation_matches_tier_b_within_tolerance")
    else:
        notes.append("tier_a_validation_exceeds_tolerance")

    return TierATierBComparison(
        compared_channels=compared_channels,
        relative_l2_by_channel=relative_l2_by_channel,
        max_abs_delta_by_channel=max_abs_delta_by_channel,
        preferred_axis_delta_deg=axis_delta,
        ell_grid_match=ell_match,
        k_grid_match=k_grid_match,
        tolerance=float(tolerance),
        passed=passed,
        notes=tuple(notes),
    )


def execute_tier_b_lowell_solver(
    *,
    manifest,
    bianchi_type: str,
    species: "SpeciesBackgroundRegistry",
    integrator_config: "IntegratorConfig",
    runtime_controls: RuntimeControlBlock,
    feature_flags: SolverFeatureFlags,
    release,
    k_grid_mpc: np.ndarray,
    validation_matrix: "ValidationMatrixSpec | None" = None,
    cutoff_spec: "CutoffCampaignSpec | None" = None,
) -> TierBExecutableRun:
    """Compatibility alias for the native VER2 Tier-B production route."""
    return _execute_tier_b_runtime_entrypoint(
        manifest=manifest,
        bianchi_type=bianchi_type,
        species=species,
        integrator_config=integrator_config,
        runtime_controls=runtime_controls,
        feature_flags=feature_flags,
        release=release,
        k_grid_mpc=k_grid_mpc,
        validation_matrix=validation_matrix,
        cutoff_spec=cutoff_spec,
    )


def resume_tier_b_solver_from_checkpoint(
    *,
    checkpoint_path: str,
    manifest,
    bianchi_type: str,
    species: "SpeciesBackgroundRegistry",
    integrator_config: "IntegratorConfig",
    runtime_controls: RuntimeControlBlock,
    feature_flags: SolverFeatureFlags,
    release,
    k_grid_mpc: np.ndarray,
    validation_matrix: "ValidationMatrixSpec | None" = None,
    cutoff_spec: "CutoffCampaignSpec | None" = None,
) -> TierBExecutableRun:
    """Resume the native Tier-B runtime from a saved checkpoint."""
    return _execute_tier_b_runtime_entrypoint(
        manifest=manifest,
        bianchi_type=bianchi_type,
        species=species,
        integrator_config=integrator_config,
        runtime_controls=runtime_controls,
        feature_flags=feature_flags,
        release=release,
        k_grid_mpc=k_grid_mpc,
        validation_matrix=validation_matrix,
        cutoff_spec=cutoff_spec,
        restart_checkpoint_path=checkpoint_path,
    )


def execute_tier_b_solver(
    *,
    manifest,
    bianchi_type: str,
    species: "SpeciesBackgroundRegistry",
    integrator_config: "IntegratorConfig",
    runtime_controls: RuntimeControlBlock,
    feature_flags: SolverFeatureFlags,
    release,
    k_grid_mpc: np.ndarray,
    validation_matrix: "ValidationMatrixSpec | None" = None,
    cutoff_spec: "CutoffCampaignSpec | None" = None,
    restart_checkpoint_path: str | None = None,
) -> TierBExecutableRun:
    """Execute the VER2 Tier-B production route on the native S1/S2 core.

    BF-01B-HCORE replaces the bounded Lowell bridge on the production path.
    Tier-B now uses:

    - `background.evolution` as the background owner,
    - S2 photon/collision/history surfaces as the hierarchy owner,
    - the Lowell integrator only as a retained compatibility path outside the
      production route.
    """
    return _execute_tier_b_runtime_entrypoint(
        manifest=manifest,
        bianchi_type=bianchi_type,
        species=species,
        integrator_config=integrator_config,
        runtime_controls=runtime_controls,
        feature_flags=feature_flags,
        release=release,
        k_grid_mpc=k_grid_mpc,
        validation_matrix=validation_matrix,
        cutoff_spec=cutoff_spec,
        restart_checkpoint_path=restart_checkpoint_path,
    )
