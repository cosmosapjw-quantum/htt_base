"""VER2 tetrad geometry operators for the BASS background lane.

`SK-01S1` is a skeleton packet. This module therefore implements the
authoritative algebraic geometry operators from the VER2 solver docs, while
stopping short of a production integrator rewrite. The goal is to freeze the
equation-to-code mapping now so later packets can bind real evolution logic to
the same operators without re-deriving conventions.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from bass.background.bianchi_types import BianchiAlgebra

__all__ = [
    "TetradGeometry",
    "pstf_rank2",
    "spatial_connection",
    "spatial_ricci",
    "div_vector",
    "covariant_derivative_rank2_homogeneous",
    "div_pstf2",
    "curl_pstf2",
    "build_geometry",
]


def _epsilon_3d() -> np.ndarray:
    eps = np.zeros((3, 3, 3), dtype=np.float64)
    eps[0, 1, 2] = eps[1, 2, 0] = eps[2, 0, 1] = +1.0
    eps[0, 2, 1] = eps[2, 1, 0] = eps[1, 0, 2] = -1.0
    return eps


def pstf_rank2(tensor: np.ndarray) -> np.ndarray:
    """Return the symmetric trace-free part of a spatial rank-2 tensor."""
    arr = np.asarray(tensor, dtype=np.float64)
    sym = 0.5 * (arr + arr.T)
    return sym - np.trace(sym) * np.eye(3, dtype=np.float64) / 3.0


def spatial_connection(C: np.ndarray) -> np.ndarray:
    """Koszul connection in an orthonormal anholonomic spatial frame."""
    tensor = np.asarray(C, dtype=np.float64)
    Gamma = np.zeros((3, 3, 3), dtype=np.float64)
    for gamma in range(3):
        for beta in range(3):
            for alpha in range(3):
                Gamma[gamma, beta, alpha] = 0.5 * (
                    tensor[alpha, beta, gamma]
                    - tensor[beta, gamma, alpha]
                    + tensor[gamma, alpha, beta]
                )
    return Gamma


def spatial_ricci(C: np.ndarray) -> tuple[np.ndarray, float, np.ndarray]:
    """Return `(^3R_ab, ^3R, ^3S_ab)` from the commutator tensor."""
    tensor = np.asarray(C, dtype=np.float64)
    Gamma = spatial_connection(tensor)
    riemann = np.zeros((3, 3, 3, 3), dtype=np.float64)
    for delta in range(3):
        for gamma in range(3):
            for alpha in range(3):
                for beta in range(3):
                    term = 0.0
                    for eps_i in range(3):
                        term += Gamma[eps_i, gamma, beta] * Gamma[delta, eps_i, alpha]
                        term -= Gamma[eps_i, gamma, alpha] * Gamma[delta, eps_i, beta]
                        term -= tensor[eps_i, alpha, beta] * Gamma[delta, gamma, eps_i]
                    riemann[delta, gamma, alpha, beta] = term
    ricci = np.zeros((3, 3), dtype=np.float64)
    for gamma in range(3):
        for beta in range(3):
            ricci[gamma, beta] = float(np.sum(riemann[:, gamma, :, beta].diagonal()))
    ricci_scalar = float(np.trace(ricci))
    return ricci, ricci_scalar, pstf_rank2(ricci)


def div_vector(vector: np.ndarray, Gamma: np.ndarray) -> float:
    """Algebraic divergence of a homogeneous spatial vector."""
    v = np.asarray(vector, dtype=np.float64)
    connection = np.asarray(Gamma, dtype=np.float64)
    out = 0.0
    for alpha in range(3):
        for gamma in range(3):
            out -= connection[gamma, alpha, alpha] * v[gamma]
    return float(out)


def covariant_derivative_rank2_homogeneous(tensor: np.ndarray, Gamma: np.ndarray) -> np.ndarray:
    """Return `D_gamma X_{alpha beta}` for a homogeneous rank-2 spatial tensor.

    The VER2 SDD fixes the anholonomic-frame convention as

    `D_gamma X_{alpha beta} = -Gamma^mu_{gamma alpha} X_{mu beta}
                              -Gamma^mu_{gamma beta} X_{alpha mu}`.
    """

    X = np.asarray(tensor, dtype=np.float64)
    connection = np.asarray(Gamma, dtype=np.float64)
    D = np.zeros((3, 3, 3), dtype=np.float64)
    for gamma in range(3):
        for alpha in range(3):
            for beta in range(3):
                for mu in range(3):
                    D[gamma, alpha, beta] -= connection[mu, gamma, alpha] * X[mu, beta]
                    D[gamma, alpha, beta] -= connection[mu, gamma, beta] * X[alpha, mu]
    return D


def div_pstf2(tensor: np.ndarray, Gamma: np.ndarray) -> np.ndarray:
    """Algebraic divergence of a homogeneous PSTF rank-2 tensor."""
    D = covariant_derivative_rank2_homogeneous(tensor, Gamma)
    out = np.zeros(3, dtype=np.float64)
    for alpha in range(3):
        for beta in range(3):
            out[alpha] += D[beta, alpha, beta]
    return out


def curl_pstf2(tensor: np.ndarray, Gamma: np.ndarray) -> np.ndarray:
    """Algebraic curl of a homogeneous PSTF rank-2 tensor."""
    D = covariant_derivative_rank2_homogeneous(tensor, Gamma)
    eps = _epsilon_3d()
    out = np.zeros((3, 3), dtype=np.float64)
    for alpha in range(3):
        for beta in range(3):
            val = 0.0
            for gamma in range(3):
                for delta in range(3):
                    val += eps[gamma, delta, alpha] * D[gamma, beta, delta]
            out[alpha, beta] = val
    return pstf_rank2(out)


@dataclass(frozen=True)
class TetradGeometry:
    """Bundle of geometry operators derived from one `BianchiAlgebra`."""

    algebra: BianchiAlgebra
    Gamma: np.ndarray
    ricci_tensor: np.ndarray
    ricci_scalar: float
    ricci_pstf: np.ndarray

    def __post_init__(self) -> None:
        Gamma = np.asarray(self.Gamma, dtype=np.float64)
        ricci_tensor = np.asarray(self.ricci_tensor, dtype=np.float64)
        ricci_pstf = np.asarray(self.ricci_pstf, dtype=np.float64)
        if Gamma.shape != (3, 3, 3):
            raise ValueError(f"TetradGeometry.Gamma must have shape (3,3,3), got {Gamma.shape}")
        if ricci_tensor.shape != (3, 3):
            raise ValueError(
                f"TetradGeometry.ricci_tensor must have shape (3,3), got {ricci_tensor.shape}"
            )
        if ricci_pstf.shape != (3, 3):
            raise ValueError(
                f"TetradGeometry.ricci_pstf must have shape (3,3), got {ricci_pstf.shape}"
            )
        object.__setattr__(self, "Gamma", Gamma)
        object.__setattr__(self, "ricci_tensor", ricci_tensor)
        object.__setattr__(self, "ricci_pstf", ricci_pstf)

    @property
    def torsion_residual_norm(self) -> float:
        residual = np.zeros_like(self.algebra.C)
        for gamma in range(3):
            for alpha in range(3):
                for beta in range(3):
                    residual[gamma, beta, alpha] = (
                        self.Gamma[gamma, beta, alpha]
                        - self.Gamma[gamma, alpha, beta]
                        - self.algebra.C[gamma, alpha, beta]
                    )
        return float(np.max(np.abs(residual)))


def build_geometry(algebra: BianchiAlgebra) -> TetradGeometry:
    """Construct canonical geometry operators from a VER2 algebra object."""
    Gamma = spatial_connection(algebra.C)
    ricci_tensor, ricci_scalar, ricci_pstf = spatial_ricci(algebra.C)
    return TetradGeometry(
        algebra=algebra,
        Gamma=Gamma,
        ricci_tensor=ricci_tensor,
        ricci_scalar=ricci_scalar,
        ricci_pstf=ricci_pstf,
    )
