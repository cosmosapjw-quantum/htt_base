"""VER2 executable runtime skeletons for the BASS S3 lane."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from common.contracts import RuntimeReductionDecision

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
    "build_runtime_reduction_decision",
    "plan_solver_execution",
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
