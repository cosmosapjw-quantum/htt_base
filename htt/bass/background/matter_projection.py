"""ver3 PR-04 matter projection surfaces for the BASS background lane.

This module freezes the normal-frame matter projection contract:

- rest-frame species thermodynamics live in ``SpeciesRestFrameState``
- homogeneous global tilt is an explicit input ``v^A``
- output is the normal-frame source pack ``(rho, p, q_A, pi_AB)``

Local observer boost is intentionally absent from this layer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import numpy as np

from bass.background.constraints import MatterNormalFrameState
from common.conventions import gamma_trace, lower_vector, pstf_gamma

__all__ = [
    "SpeciesRestFrameState",
    "SpeciesProjectedState",
    "project_species_to_normal_frame",
    "total_matter_projection",
]


def _gamma_metric(gamma_ab: np.ndarray | None) -> np.ndarray:
    gamma = np.eye(3, dtype=np.float64) if gamma_ab is None else np.asarray(gamma_ab, dtype=np.float64)
    if gamma.shape != (3, 3):
        raise ValueError(f"gamma_AB must have shape (3,3), got {gamma.shape}")
    if not np.allclose(gamma, gamma.T, atol=1.0e-12):
        raise ValueError("gamma_AB must be symmetric")
    return gamma


def _lorentz_gamma_from_vsq(v_sq: float) -> float:
    if v_sq < 0.0:
        raise ValueError(f"v^2 must be non-negative, got {v_sq!r}")
    if v_sq >= 1.0:
        raise ValueError(f"v^2 must stay below 1, got {v_sq!r}")
    return 1.0 / np.sqrt(1.0 - v_sq)


@dataclass(frozen=True)
class SpeciesRestFrameState:
    """Rest-frame thermodynamics for one homogeneous species."""

    rho_hat: float
    p_hat: float
    label: str = ""
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class SpeciesProjectedState:
    """Normal-frame projection of one rest-frame species."""

    label: str
    rho: float
    p: float
    q: np.ndarray
    pi: np.ndarray
    tilt_contravariant: np.ndarray
    tilt_covariant: np.ndarray
    gamma_lorentz: float
    rest_frame: SpeciesRestFrameState

    def __post_init__(self) -> None:
        q = np.asarray(self.q, dtype=np.float64)
        pi = np.asarray(self.pi, dtype=np.float64)
        tilt_contravariant = np.asarray(self.tilt_contravariant, dtype=np.float64)
        tilt_covariant = np.asarray(self.tilt_covariant, dtype=np.float64)
        if q.shape != (3,):
            raise ValueError(f"SpeciesProjectedState.q must have shape (3,), got {q.shape}")
        if pi.shape != (3, 3):
            raise ValueError(f"SpeciesProjectedState.pi must have shape (3,3), got {pi.shape}")
        if tilt_contravariant.shape != (3,):
            raise ValueError(
                "SpeciesProjectedState.tilt_contravariant must have shape (3,), "
                f"got {tilt_contravariant.shape}"
            )
        if tilt_covariant.shape != (3,):
            raise ValueError(
                f"SpeciesProjectedState.tilt_covariant must have shape (3,), got {tilt_covariant.shape}"
            )
        object.__setattr__(self, "q", q)
        object.__setattr__(self, "pi", pstf_gamma(pi))
        object.__setattr__(self, "tilt_contravariant", tilt_contravariant)
        object.__setattr__(self, "tilt_covariant", tilt_covariant)


def project_species_to_normal_frame(
    species_rest: SpeciesRestFrameState,
    tilt: np.ndarray,
    gamma_ab: np.ndarray | None = None,
) -> SpeciesProjectedState:
    """Project one homogeneous rest-frame species onto the normal frame."""

    gamma = _gamma_metric(gamma_ab)
    tilt_up = np.asarray(tilt, dtype=np.float64)
    if tilt_up.shape != (3,):
        raise ValueError(f"tilt must have shape (3,), got {tilt_up.shape}")
    tilt_down = lower_vector(tilt_up, gamma)
    v_sq = float(np.dot(tilt_up, tilt_down))
    gamma_lorentz = _lorentz_gamma_from_vsq(v_sq)
    gamma_sq = gamma_lorentz * gamma_lorentz
    rho_plus_p = float(species_rest.rho_hat) + float(species_rest.p_hat)
    rho = gamma_sq * rho_plus_p - float(species_rest.p_hat)
    p = float(species_rest.p_hat) + (gamma_sq * rho_plus_p * v_sq) / 3.0
    q = gamma_sq * rho_plus_p * tilt_down
    pi = gamma_sq * rho_plus_p * pstf_gamma(np.outer(tilt_down, tilt_down), gamma)
    return SpeciesProjectedState(
        label=species_rest.label,
        rho=rho,
        p=p,
        q=q,
        pi=pi,
        tilt_contravariant=tilt_up,
        tilt_covariant=tilt_down,
        gamma_lorentz=gamma_lorentz,
        rest_frame=species_rest,
    )


def total_matter_projection(
    projected_species: Iterable[SpeciesProjectedState],
    gamma_ab: np.ndarray | None = None,
) -> MatterNormalFrameState:
    """Aggregate normal-frame species pieces into the total source pack."""

    gamma = _gamma_metric(gamma_ab)
    rho = 0.0
    p = 0.0
    q = np.zeros(3, dtype=np.float64)
    pi = np.zeros((3, 3), dtype=np.float64)
    for piece in tuple(projected_species):
        rho += float(piece.rho)
        p += float(piece.p)
        q += np.asarray(piece.q, dtype=np.float64)
        pi += np.asarray(piece.pi, dtype=np.float64)
    pi = pstf_gamma(pi, gamma)
    _ = gamma_trace(pi, gamma)
    return MatterNormalFrameState(rho=rho, p=p, q=q, pi=pi)
