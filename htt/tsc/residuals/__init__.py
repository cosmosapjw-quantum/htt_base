"""Residual and defect-report helpers for the VER2 TSC service."""

from .blockwise import ambient_vs_projected_defect_report, classify_residual_origin
from .collision_state_split import (
    ResidualKind,
    TypedResidual,
    collision_side_residual,
    observable_residual,
    state_side_residual,
)
from .laguerre import (
    ResidualSignal,
    collision_laguerre_coefficients,
    n_ge_2_norm,
    state_laguerre_coefficients,
    tangency_status,
)
from .observable_bridge import (
    ResidualBridgeStatus,
    TscResidualBridgeReport,
    build_residual_bridge_from_reports,
    build_residual_bridge_report,
)

__all__ = [
    "ResidualBridgeStatus",
    "ResidualKind",
    "ResidualSignal",
    "TscResidualBridgeReport",
    "TypedResidual",
    "ambient_vs_projected_defect_report",
    "classify_residual_origin",
    "collision_side_residual",
    "collision_laguerre_coefficients",
    "build_residual_bridge_from_reports",
    "build_residual_bridge_report",
    "n_ge_2_norm",
    "observable_residual",
    "state_side_residual",
    "state_laguerre_coefficients",
    "tangency_status",
]
