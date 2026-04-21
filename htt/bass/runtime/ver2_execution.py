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
    "build_runtime_reduction_decision",
    "plan_solver_execution",
    "execute_tier_b_lowell_solver",
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
        if feature_flags.source_propagator is not FeatureStatus.DISABLED
        else "pending"
    )
    reason = (
        "tier_b_lowell_live_bridge"
        if propagation_status == "validated"
        else "tier_b_lowell_runtime_without_live_propagator"
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


def _campaign_runner(
    *,
    base_config: "IntegratorConfig",
    species: "SpeciesBackgroundRegistry",
):
    from bass.hierarchy.integrator import IntegratorConfig, LowellBianchiIntegrator

    def runner(cutoff: int) -> tuple[Mapping[str, np.ndarray], float]:
        start = perf_counter()
        config = IntegratorConfig(
            L_max=int(cutoff),
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
            solver_method=base_config.solver_method,
            gamma_T_override=base_config.gamma_T_override,
        )
        result = LowellBianchiIntegrator(config, species).run()
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
    """Execute the bounded VER2 Tier-B low-ell runtime/orchestrator path.

    The selected implementation keeps the shipped Lowell Tier-B hierarchy as
    the numerical core while making the S1/S2/S3 contracts live owners of the
    execution trace, output assembly, and cutoff campaign. This is deliberately
    narrower than a universal solver rewrite and is the lowest-risk executable
    bridge within the IM-03S3A write scope.
    """
    if runtime_controls.tier is not SolverTier.TIER_B_PSTF:
        raise ValueError("execute_tier_b_lowell_solver requires Tier B runtime controls")
    if runtime_controls.multipole_cutoff > integrator_config.L_max:
        raise ValueError("runtime cutoff must not exceed integrator_config.L_max")

    from bass.hierarchy.integrator import LowellBianchiIntegrator
    from bass.spectrum.ver2_cutoff_campaign import run_executed_cutoff_campaign

    background_monitor = _build_background_monitor(
        bianchi_type=bianchi_type,
        config=integrator_config,
        species=species,
    )
    visibility_source = _build_visibility_source(
        species=species,
        config=integrator_config,
    )
    startup_gate = _build_startup_gate(
        visibility_source=visibility_source,
        background_monitor=background_monitor,
        config=integrator_config,
    )
    seed_projection = _build_seed_projection(
        background_monitor=background_monitor,
        config=integrator_config,
    )

    integrator = LowellBianchiIntegrator(integrator_config, species)
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
            else ValidationMatrixSpec(
                bianchi_types=(bianchi_type,),
                branches=(
                    ("tilted",) if abs(float(integrator_config.tilt_rapidity)) > 0.0 else ("orthogonal",)
                ),
            )
        ),
    )
    result = integrator.run()

    geodesic_probe = _build_geodesic_probe(background_monitor=background_monitor)
    gamma_t_probe = _resolved_gamma_t(
        visibility_source=visibility_source,
        eta=float(result.eta[-1]),
        direction=np.asarray(integrator_config.tilt_direction, dtype=np.float64),
        config=integrator_config,
    )
    thomson_probe = _build_thomson_probe(
        result=result,
        species=species,
        config=integrator_config,
        gamma_t=gamma_t_probe,
    )

    from bass.forward.ver2_solver_output import build_solver_core_output_from_lowell_result

    solver_output = build_solver_core_output_from_lowell_result(
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
                base_config=integrator_config,
                species=species,
            ),
        )
    return TierBExecutableRun(
        execution_plan=plan,
        runtime_decision=runtime_decision,
        trace=TierBExecutionTrace(
            background_monitor=background_monitor,
            startup_gate=startup_gate,
            seed_projection=seed_projection,
            geodesic_probe=geodesic_probe,
            thomson_probe=thomson_probe,
            visibility_source=visibility_source,
        ),
        integration_result=result,
        solver_output=solver_output,
        cutoff_campaign=cutoff_campaign,
    )
