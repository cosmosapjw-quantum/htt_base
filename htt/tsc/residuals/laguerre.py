"""Skeleton Laguerre residual helpers for TSC active-service reports."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

import numpy as np


@dataclass(frozen=True)
class ResidualSignal:
    """Typed residual payload keeping collision/state semantics explicit."""

    values: np.ndarray
    kind: Literal["collision", "state"]
    label: str = ""


def laguerre_coefficients(
    source_or_residual: Iterable[float] | np.ndarray,
    basis: object | None = None,
    weight: object | None = None,
) -> np.ndarray:
    """Return a 1-D coefficient vector for the skeleton phase.

    The pre-implementation packet preserves semantic separation and vector
    shape only; it does not yet compute the final chart-specific transform.
    """

    del basis, weight
    arr = np.asarray(source_or_residual, dtype=float)
    return arr.reshape(-1)


def collision_laguerre_coefficients(values: Iterable[float] | np.ndarray) -> ResidualSignal:
    return ResidualSignal(values=laguerre_coefficients(values), kind="collision")


def state_laguerre_coefficients(values: Iterable[float] | np.ndarray) -> ResidualSignal:
    return ResidualSignal(values=laguerre_coefficients(values), kind="state")


def n_ge_2_norm(coeffs: Iterable[float] | np.ndarray) -> float:
    arr = np.asarray(coeffs, dtype=float).reshape(-1)
    if arr.size <= 2:
        return 0.0
    return float(np.linalg.norm(arr[2:]))


def tangency_status(norm: float, threshold: float) -> Literal["tangent", "warn", "non_tangent"]:
    if norm <= threshold:
        return "tangent"
    if norm <= 2.0 * threshold:
        return "warn"
    return "non_tangent"


__all__ = [
    "ResidualSignal",
    "collision_laguerre_coefficients",
    "laguerre_coefficients",
    "n_ge_2_norm",
    "state_laguerre_coefficients",
    "tangency_status",
]
