from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

import numpy as np


class PoleDefinition(str, Enum):
    """Registered low-ell pole definitions.

    ``ANISOTROPY_TENSOR`` is the core, dependency-free definition implemented in
    this bundle.  Other definitions are plugin targets and must never be silently
    substituted for it.
    """

    ANISOTROPY_TENSOR = "anisotropy_tensor"
    MAX_ANGULAR_MOMENTUM = "max_angular_momentum"
    MIN_ANGULAR_MOMENTUM = "min_angular_momentum"
    MULTIPOLE_VECTOR_NORMAL = "multipole_vector_normal"


class SourceModel(str, Enum):
    ISOTROPIC = "isotropic"
    LOCAL_BOOST = "local_boost"
    LOCAL_STRUCTURE = "local_structure"
    GLOBAL_COHERENT = "global_coherent"
    MIXTURE = "mixture"


@dataclass(frozen=True)
class ShellGrid:
    redshifts: tuple[float, ...]
    weights: tuple[float, ...]

    @classmethod
    def from_redshifts(
        cls, redshifts: Iterable[float], weights: Iterable[float] | None = None
    ) -> "ShellGrid":
        z = tuple(float(x) for x in redshifts)
        if not z:
            raise ValueError("redshift grid must be non-empty")
        if any(x < 0 for x in z):
            raise ValueError("redshifts must be non-negative")
        if any(b <= a for a, b in zip(z[:-1], z[1:])):
            raise ValueError("redshifts must be strictly increasing")
        if weights is None:
            w = np.ones(len(z), dtype=float)
        else:
            w = np.asarray(tuple(float(x) for x in weights), dtype=float)
            if len(w) != len(z):
                raise ValueError("weights and redshifts must have equal length")
            if np.any(w < 0):
                raise ValueError("weights must be non-negative")
        if not np.any(w > 0):
            raise ValueError("at least one shell weight must be positive")
        w = w / np.sum(w)
        return cls(z, tuple(float(x) for x in w))

    @property
    def size(self) -> int:
        return len(self.redshifts)


@dataclass(frozen=True)
class PoleTrajectory:
    ell: int
    redshifts: tuple[float, ...]
    poles: tuple[tuple[float, float, float], ...]
    eigenvalues: tuple[tuple[float, float, float], ...]

    def pole_array(self) -> np.ndarray:
        return np.asarray(self.poles, dtype=float)
