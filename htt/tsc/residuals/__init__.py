"""Residual and defect-report helpers for the VER2 TSC service."""

from .blockwise import ambient_vs_projected_defect_report, classify_residual_origin
from .laguerre import (
    ResidualSignal,
    collision_laguerre_coefficients,
    n_ge_2_norm,
    state_laguerre_coefficients,
    tangency_status,
)

__all__ = [
    "ResidualSignal",
    "ambient_vs_projected_defect_report",
    "classify_residual_origin",
    "collision_laguerre_coefficients",
    "n_ge_2_norm",
    "state_laguerre_coefficients",
    "tangency_status",
]
