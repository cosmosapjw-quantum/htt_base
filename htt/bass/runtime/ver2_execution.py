"""VER2 executable runtime surfaces for the BASS S3 lane."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from time import perf_counter

import numpy as np

from common.contracts import RuntimeReductionDecision, SolverCoreOutput

from bass.runtime.canonical_decision import CanonicalDecision

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
    thomson_probe: "ProjectedThomsonSource"
    visibility_source: "TiltedVisibilitySource"


@dataclass(frozen=True)
class TierBExecutableRun:
    """Executable Tier-B low-ell bundle produced by the VER2 runtime."""

    execution_plan: SolverExecutionPlan
    runtime_decision: RuntimeReductionDecision
    trace: TierBExecutionTrace
    integration_result: "IntegrationResult"
    solver_output: SolverCoreOutput
    cutoff_campaign: "ExecutedCutoffCampaign | None" = None


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
        for channel, values in self.dl_reference.items():
            arr = np.asarray(values, dtype=np.float64)
            if arr.ndim != 1:
                raise ValueError(f"dl_reference[{channel!r}] must be 1-D")
            if not np.all(np.isfinite(arr)):
                raise ValueError(f"dl_reference[{channel!r}] must be finite")


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
    from bass.background.tetrad_state import axisymmetric_sigma_tensor
    from bass.species.base import CANONICAL_ORDER, SpeciesLabel
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
    return solve_background_evolution(
        initial_conditions,
        config=BackgroundEvolutionConfig(
            a_start=a_start,
            a_end=a_end,
            n_steps=max(16, min(int(config.n_output), 256)),
            rtol=min(float(config.rtol), 1.0e-8),
            atol=min(max(float(config.atol), 1.0e-12), 1.0e-10),
            lambda_value=lambda_value,
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
) -> "TiltedVisibilitySource":
    from bass.hierarchy.frame_contracts import PhotonDirectionConvention
    from bass.recombination.history_visibility import build_tilted_visibility_source
    from bass.species.base import SpeciesLabel

    baryon = species[SpeciesLabel.BARYON]
    velocity = _tilt_velocity(config.bianchi_cosmo)

    def v_e(_eta: float) -> np.ndarray:
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


def _build_geodesic_probe(
    *,
    background_monitor: "BackgroundEvolutionResult",
) -> "PhotonGeodesicRhs":
    from bass.transport.geodesics import (
        PhotonGeodesicState,
        ScreenBasisState,
        photon_geodesic_rhs,
    )

    direction = np.array([1.0, 0.0, 0.0], dtype=np.float64)
    screen_basis = ScreenBasisState(
        u=np.array([0.0, 1.0, 0.0], dtype=np.float64),
        v=np.array([0.0, 0.0, 1.0], dtype=np.float64),
    )
    state = PhotonGeodesicState(
        energy=1.0,
        direction=direction,
        screen_basis=screen_basis,
    )
    return photon_geodesic_rhs(
        state=state,
        H=float(background_monitor.H[-1]),
        sigma_ab=background_monitor.sigma_tensor[-1],
        geometry=background_monitor.initial_conditions.geometry,
    )


def _build_thomson_probe(
    *,
    result: "IntegrationResult",
    species: "SpeciesBackgroundRegistry",
    config: "IntegratorConfig",
    gamma_t: float,
) -> "ProjectedThomsonSource":
    from bass.collision.electron_frame import (
        ElectronFrameThomsonContext,
        project_thomson_source,
    )
    from bass.collision.polarization import PolarizationHierarchyState
    from bass.hierarchy.pstf_tensor import unpack_hierarchy
    from bass.species.base import SpeciesLabel
    from bass.species.tilted import TiltedSpeciesBackground

    temperature_state = unpack_hierarchy(result.photon_T_tower[-1], result.L_max)
    polarization_state = PolarizationHierarchyState(
        E=unpack_hierarchy(result.photon_E_tower[-1], result.L_max)
    )
    tilted_electron = None
    if abs(float(config.tilt_rapidity)) > 0.0:
        tilted_electron = TiltedSpeciesBackground.from_rapidity(
            base=species[SpeciesLabel.BARYON],
            rapidity=float(config.tilt_rapidity),
            v_hat_e=tuple(float(x) for x in config.tilt_direction),
        )
    return project_thomson_source(
        ElectronFrameThomsonContext(),
        temperature_state=temperature_state,
        polarization_state=polarization_state,
        v_b_real_sph=np.zeros(3, dtype=np.float64),
        Gamma_T=float(gamma_t),
        direction=np.asarray(config.tilt_direction, dtype=np.float64),
        tilted_electron=tilted_electron,
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
        # The native BF-02 seed/startup path is still a single stiff ODE
        # solve; until an actual split executor exists, use the stable
        # implicit backend explicitly rather than inheriting legacy LSODA.
        return "BDF", "imex_split_declared_bdf_executor"
    raise ValueError(f"Unsupported integrator family: {family!r}")


def _native_runtime_config(
    base_config: "IntegratorConfig",
    runtime_controls: RuntimeControlBlock,
) -> tuple["IntegratorConfig", str]:
    from bass.hierarchy.integrator import IntegratorConfig

    solver_method, realization = _resolve_native_solver_method(runtime_controls)
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

    def runner(cutoff: int) -> tuple[Mapping[str, np.ndarray], float]:
        start = perf_counter()
        cutoff_config, _ = _native_runtime_config(base_config, runtime_controls)
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
        )
        visibility_source = _build_visibility_source(
            species=species,
            config=config,
        )
        canonical_decision = build_integrator_canonical_decision(
            beta=float(config.bianchi_cosmo.beta),
            sigma_squared=max(
                0.5 * float(np.sum(background_monitor.sigma_tensor[0] ** 2)),
                1.0e-12,
            ),
        )
        result = Ver2TierBIntegrator(
            config,
            species,
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
    return execute_tier_b_solver(
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
) -> TierBExecutableRun:
    """Execute the VER2 Tier-B production route on the native S1/S2 core.

    BF-01B-HCORE replaces the bounded Lowell bridge on the production path.
    Tier-B now uses:

    - `background.evolution` as the background owner,
    - S2 photon/collision/history surfaces as the hierarchy owner,
    - the Lowell integrator only as a retained compatibility path outside the
      production route.
    """
    if runtime_controls.tier is not SolverTier.TIER_B_PSTF:
        raise ValueError("execute_tier_b_solver requires Tier B runtime controls")
    if runtime_controls.multipole_cutoff > integrator_config.L_max:
        raise ValueError("runtime cutoff must not exceed integrator_config.L_max")

    from bass.hierarchy.aux_state import build_integrator_canonical_decision
    from bass.hierarchy.ver2_native_integrator import Ver2TierBIntegrator
    from bass.spectrum.ver2_cutoff_campaign import run_executed_cutoff_campaign

    runtime_config, family_realization = _native_runtime_config(
        integrator_config,
        runtime_controls,
    )
    background_monitor = _build_background_monitor(
        bianchi_type=bianchi_type,
        config=runtime_config,
        species=species,
    )
    visibility_source = _build_visibility_source(
        species=species,
        config=runtime_config,
    )
    canonical_decision = build_integrator_canonical_decision(
        beta=float(runtime_config.bianchi_cosmo.beta),
        sigma_squared=max(
            0.5 * float(np.sum(background_monitor.sigma_tensor[0] ** 2)),
            1.0e-12,
        ),
    )
    seed_k_comoving = _representative_seed_k(np.asarray(k_grid_mpc, dtype=np.float64))
    integrator = Ver2TierBIntegrator(
        runtime_config,
        species,
        background_monitor=background_monitor,
        visibility_source=visibility_source,
        canonical_decision=canonical_decision,
        seed_k_comoving=seed_k_comoving,
    )
    runtime_decision = _build_runtime_decision(
        feature_flags=feature_flags,
        canonical_decision=integrator.canonical_decision,
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
                integrator_config=runtime_config,
                suite="tier_b_smoke",
            )
        ),
    )
    result = integrator.run()
    result.solver_info["runtime_integrator_family"] = runtime_controls.integrator_family.value
    result.solver_info["solver_family_realization"] = family_realization

    geodesic_probe = _build_geodesic_probe(background_monitor=background_monitor)
    gamma_t_probe = _resolved_gamma_t(
        visibility_source=visibility_source,
        eta=float(result.eta[-1]),
        direction=np.asarray(runtime_config.tilt_direction, dtype=np.float64),
        config=runtime_config,
    )
    thomson_probe = _build_thomson_probe(
        result=result,
        species=species,
        config=runtime_config,
        gamma_t=gamma_t_probe,
    )

    from bass.forward.ver2_solver_output import build_solver_core_output_from_native_result

    solver_output = build_solver_core_output_from_native_result(
        manifest=manifest,
        bianchi_type=bianchi_type,
        result=result,
        species=species,
        runtime_controls=runtime_controls,
        feature_flags=feature_flags,
        release=release,
        k_grid_mpc=np.asarray(k_grid_mpc, dtype=np.float64),
    )
    cutoff_campaign = None
    if cutoff_spec is not None:
        cutoff_campaign = run_executed_cutoff_campaign(
            cutoff_spec,
            runner=_campaign_runner(
                bianchi_type=bianchi_type,
                base_config=integrator_config,
                species=species,
                seed_k_comoving=seed_k_comoving,
                runtime_controls=runtime_controls,
            ),
        )
    return TierBExecutableRun(
        execution_plan=plan,
        runtime_decision=runtime_decision,
        trace=TierBExecutionTrace(
            background_monitor=background_monitor,
            startup_gate=integrator.startup_gate,
            startup_state=integrator.startup_state,
            seed_projection=integrator.seed_projection,
            geodesic_probe=geodesic_probe,
            thomson_probe=thomson_probe,
            visibility_source=visibility_source,
        ),
        integration_result=result,
        solver_output=solver_output,
        cutoff_campaign=cutoff_campaign,
    )
