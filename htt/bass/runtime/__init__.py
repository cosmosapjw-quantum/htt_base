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
    FeatureStatus,
    IntegratorFamily,
    RuntimeControlBlock,
    SolverExecutionPlan,
    SolverFeatureFlags,
    SolverTier,
    ValidationMatrixSpec,
    build_runtime_reduction_decision,
    plan_solver_execution,
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
    "build_runtime_reduction_decision",
    "plan_solver_execution",
]
