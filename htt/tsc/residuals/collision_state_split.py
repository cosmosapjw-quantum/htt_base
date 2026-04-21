"""Typed collision/state residual helpers for TSC bridge logic."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from common.contracts import TscResidualReport


ResidualKind = Literal["D_coll", "D_state", "Delta_obs"]


@dataclass(frozen=True)
class TypedResidual:
    """Named residual value preserving the SDD type split."""

    kind: ResidualKind
    value: float | None


def collision_side_residual(report: TscResidualReport) -> TypedResidual:
    """Return the collision/source-side residual diagnostic ``D_coll``."""
    values = [
        abs(float(report.laguerre_n_ge_2_norm)),
        abs(float(report.trace_residual_q_tr)) if report.trace_residual_q_tr is not None else 0.0,
    ]
    return TypedResidual(kind="D_coll", value=max(values))


def state_side_residual(report: TscResidualReport) -> TypedResidual:
    """Return the state-side reduced-manifold residual ``D_state``."""
    value = report.twofield_residual
    if value is None:
        value = report.onefield_residual
    return TypedResidual(kind="D_state", value=None if value is None else abs(float(value)))


def observable_residual(value: float | None) -> TypedResidual:
    """Wrap an observable-side discrepancy or bound as ``Delta_obs``."""
    return TypedResidual(kind="Delta_obs", value=None if value is None else abs(float(value)))


__all__ = [
    "ResidualKind",
    "TypedResidual",
    "collision_side_residual",
    "observable_residual",
    "state_side_residual",
]
