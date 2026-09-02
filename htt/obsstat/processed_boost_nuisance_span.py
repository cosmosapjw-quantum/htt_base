"""Directional nuisance-span contracts for PMG-WU-011 Task-7C.

This module extends the synthetic processed local-observer scalar response from
Task-7B.  It does not fit an observer velocity, choose a high-multipole prior,
or alter the strict-positive finite-sky production path.
"""

from __future__ import annotations

from enum import Enum
import math
from types import MappingProxyType
from typing import Mapping

import numpy as np


DIRECTION_IDS = ("X", "Y", "Z", "D111", "D1M11", "D11M1")
CORE_SOURCE_CUTOFFS = (9, 12, 16)


class Task7CTerminal(str, Enum):
    """Typed terminals for source-band convergence and nuisance geometry."""

    PASS_TASK7C_MODEL_FREE_IDENTIFIED_SUBSPACE = (
        "PASS_TASK7C_MODEL_FREE_IDENTIFIED_SUBSPACE"
    )
    PASS_TASK7C_MODEL_FREE_NO_IDENTIFIED_SUBSPACE = (
        "PASS_TASK7C_MODEL_FREE_NO_IDENTIFIED_SUBSPACE"
    )
    PASS_TASK7C_SOURCE_BAND_NOT_CONVERGED = (
        "PASS_TASK7C_SOURCE_BAND_NOT_CONVERGED"
    )
    BLOCKED_BY_DIRECTIONAL_METRIC_FAILURE = (
        "BLOCKED_BY_DIRECTIONAL_METRIC_FAILURE"
    )
    BLOCKED_BY_CUTOFF_CONSTRUCTION = "BLOCKED_BY_CUTOFF_CONSTRUCTION"
    BLOCKED_BY_ARTIFACT_INTEGRITY = "BLOCKED_BY_ARTIFACT_INTEGRITY"


def _sealed_direction(values: tuple[float, float, float]) -> np.ndarray:
    vector = np.asarray(values, dtype="<f8")
    if vector.shape != (3,) or not np.all(np.isfinite(vector)):
        raise ValueError("Task-7C direction must be a finite three-vector")
    norm = float(np.linalg.norm(vector))
    if not math.isfinite(norm) or norm <= 0.0:
        raise ValueError("Task-7C direction must have positive norm")
    unit = np.ascontiguousarray(vector / norm, dtype="<f8")
    unit.flags.writeable = False
    return unit


_DIRECTION_REGISTRY: Mapping[str, np.ndarray] = MappingProxyType(
    {
        "X": _sealed_direction((1.0, 0.0, 0.0)),
        "Y": _sealed_direction((0.0, 1.0, 0.0)),
        "Z": _sealed_direction((0.0, 0.0, 1.0)),
        "D111": _sealed_direction((1.0, 1.0, 1.0)),
        "D1M11": _sealed_direction((1.0, -1.0, 1.0)),
        "D11M1": _sealed_direction((1.0, 1.0, -1.0)),
    }
)


def direction_registry() -> Mapping[str, np.ndarray]:
    """Return the immutable, sign-nonredundant unit-direction registry."""

    return _DIRECTION_REGISTRY


__all__ = [
    "CORE_SOURCE_CUTOFFS",
    "DIRECTION_IDS",
    "Task7CTerminal",
    "direction_registry",
]
