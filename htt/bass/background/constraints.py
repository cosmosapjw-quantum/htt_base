"""VER2 background-constraint skeletons for the BASS S1 lane."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from bass.background.bianchi_types import BianchiAlgebra
from bass.background.geometry import TetradGeometry, div_pstf2, pstf_rank2

__all__ = [
    "MatterNormalFrameState",
    "BackgroundConstraintResiduals",
    "gauss_constraint_residual",
    "codazzi_constraint_residual",
    "evaluate_background_constraints",
]


@dataclass(frozen=True)
class MatterNormalFrameState:
    """Normal-frame matter summary used by the VER2 background skeletons."""

    rho: float
    p: float
    q: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float64))
    pi: np.ndarray = field(default_factory=lambda: np.zeros((3, 3), dtype=np.float64))

    def __post_init__(self) -> None:
        q = np.asarray(self.q, dtype=np.float64)
        pi = pstf_rank2(self.pi)
        if q.shape != (3,):
            raise ValueError(f"MatterNormalFrameState.q must have shape (3,), got {q.shape}")
        if pi.shape != (3, 3):
            raise ValueError(f"MatterNormalFrameState.pi must have shape (3,3), got {pi.shape}")
        object.__setattr__(self, "q", q)
        object.__setattr__(self, "pi", pi)


@dataclass(frozen=True)
class BackgroundConstraintResiduals:
    """Machine-readable residual block for Gauss/Codazzi/Jacobi checks."""

    gauss: float
    codazzi: np.ndarray
    jacobi: np.ndarray
    twice_contracted_bianchi: np.ndarray

    def __post_init__(self) -> None:
        codazzi = np.asarray(self.codazzi, dtype=np.float64)
        jacobi = np.asarray(self.jacobi, dtype=np.float64)
        bianchi = np.asarray(self.twice_contracted_bianchi, dtype=np.float64)
        if codazzi.shape != (3,):
            raise ValueError(f"codazzi residual must have shape (3,), got {codazzi.shape}")
        if jacobi.shape != (3,):
            raise ValueError(f"jacobi residual must have shape (3,), got {jacobi.shape}")
        if bianchi.shape != (4,):
            raise ValueError(
                f"twice_contracted_bianchi residual must have shape (4,), got {bianchi.shape}"
            )
        object.__setattr__(self, "codazzi", codazzi)
        object.__setattr__(self, "jacobi", jacobi)
        object.__setattr__(self, "twice_contracted_bianchi", bianchi)


def gauss_constraint_residual(
    H: float,
    rho: float,
    lambda_value: float,
    sigma_ab: np.ndarray,
    ricci_scalar: float,
    *,
    kappa: float = 1.0,
) -> float:
    """Return `3H^2 - κρ - Λ - σ^2 + 1/2 ^3R`."""
    sigma = np.asarray(sigma_ab, dtype=np.float64)
    sigma_sq = 0.5 * float(np.sum(sigma * sigma))
    return 3.0 * float(H) ** 2 - kappa * float(rho) - float(lambda_value) - sigma_sq + 0.5 * float(
        ricci_scalar
    )


def codazzi_constraint_residual(
    sigma_ab: np.ndarray,
    matter: MatterNormalFrameState,
    geometry: TetradGeometry,
    *,
    kappa: float = 1.0,
) -> np.ndarray:
    """Return `(div σ)_α - κ q_α`."""
    sigma = pstf_rank2(sigma_ab)
    return div_pstf2(sigma, geometry.Gamma) - kappa * matter.q


def evaluate_background_constraints(
    *,
    algebra: BianchiAlgebra,
    geometry: TetradGeometry,
    H: float,
    sigma_ab: np.ndarray,
    matter: MatterNormalFrameState,
    lambda_value: float,
    kappa: float = 1.0,
    conservation_residual: np.ndarray | None = None,
) -> BackgroundConstraintResiduals:
    """Evaluate the skeleton constraint block for one background state.

    `twice_contracted_bianchi` is carried as a four-vector hook:
    `(energy_residual, momentum_x, momentum_y, momentum_z)`. In `SK-01S1`
    it is a plumbing surface only; later packets will feed real matter
    conservation residuals into it.
    """

    sigma = pstf_rank2(sigma_ab)
    if conservation_residual is None:
        bianchi = np.zeros(4, dtype=np.float64)
    else:
        bianchi = np.asarray(conservation_residual, dtype=np.float64)
    return BackgroundConstraintResiduals(
        gauss=gauss_constraint_residual(
            H,
            matter.rho,
            lambda_value,
            sigma,
            geometry.ricci_scalar,
            kappa=kappa,
        ),
        codazzi=codazzi_constraint_residual(sigma, matter, geometry, kappa=kappa),
        jacobi=algebra.jacobi_violation,
        twice_contracted_bianchi=bianchi,
    )
