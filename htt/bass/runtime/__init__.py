"""BASS runtime surfaces.

This package contains the legacy runtime decision gates and the VER2 S3
execution/control skeletons.
"""

from bass.runtime.canonical_decision import (
    CanonicalBlockError,
    CanonicalDecision,
    make_canonical_decision,
    require_allow_reduction,
)
from bass.runtime.validation_labels import ValidationLabel, derive_labels
from bass.runtime.ver2_execution import (
    CheckpointPolicy,
    ConstraintProjectionPolicy,
    CouplingMode,
    TierBExecutionTrace,
    TierBExecutableRun,
    TierAValidationTrace,
    TierAValidationRun,
    TierATierBComparison,
    FeatureStatus,
    IntegratorFamily,
    RuntimeControlBlock,
    SolverExecutionPlan,
    SolverFeatureFlags,
    SolverTier,
    ValidationMatrixSpec,
    build_runtime_reduction_decision,
    compare_tier_a_to_tier_b,
    execute_tier_a_validation_solver,
    execute_tier_b_solver,
    execute_tier_b_lowell_solver,
    resume_tier_b_solver_from_checkpoint,
    plan_solver_execution,
)
from bass.runtime.ver2_checkpoint import (
    TierBCheckpointRecord,
    checkpoint_path_from_template,
    load_tier_b_restart_checkpoint,
)

__all__ = [
    "CanonicalBlockError",
    "CanonicalDecision",
    "make_canonical_decision",
    "require_allow_reduction",
    "ValidationLabel",
    "derive_labels",
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
    "compare_tier_a_to_tier_b",
    "execute_tier_a_validation_solver",
    "execute_tier_b_solver",
    "plan_solver_execution",
    "execute_tier_b_lowell_solver",
    "resume_tier_b_solver_from_checkpoint",
    "TierBCheckpointRecord",
    "checkpoint_path_from_template",
    "load_tier_b_restart_checkpoint",
]
