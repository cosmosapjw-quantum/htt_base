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

from bass.background.bianchi_types import BianchiAlgebra, FamilySpec
from common.conventions import gamma_trace, pstf_gamma

__all__ = [
    "TetradGeometry",
    "pstf_rank2",
    "connection_from_commutators",
    "spatial_connection",
    "spatial_ricci_from_connection",
    "spatial_ricci_from_compact_formula",
    "dual_route_curvature_residual",
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
    return pstf_gamma(np.asarray(tensor, dtype=np.float64))


def connection_from_commutators(C: np.ndarray) -> np.ndarray:
    """Levi-Civita connection from orthonormal-frame commutators.

    The ver3 geometry contract uses the anholonomic Koszul form

    ``2 Γ_{kji} = -c_{ijk} + c_{jki} + c_{kij}``

    for ``[e_i, e_j] = c^k{}_{ij} e_k`` with the orthonormal metric.
    The returned array is stored as ``Gamma[k, slot, deriv]`` so
    ``∇_{e_deriv} e_slot = Gamma[k, slot, deriv] e_k``.
    """

    tensor = np.asarray(C, dtype=np.float64)
    Gamma = np.zeros((3, 3, 3), dtype=np.float64)
    for k in range(3):
        for j in range(3):
            for i in range(3):
                Gamma[k, j, i] = 0.5 * (
                    -tensor[i, j, k]
                    + tensor[j, k, i]
                    + tensor[k, i, j]
                )
    return Gamma


def spatial_connection(C: np.ndarray) -> np.ndarray:
    """Compatibility alias for the ver3 connection contract."""

    return connection_from_commutators(C)


def spatial_ricci_from_connection(
    commutator_tensor: np.ndarray,
    Gamma: np.ndarray | None = None,
) -> tuple[np.ndarray, float, np.ndarray]:
    """Return ``(^3R_ab, ^3R, ^3S_ab)`` from the connection/commutator route."""

    tensor = np.asarray(commutator_tensor, dtype=np.float64)
    Gamma_eff = connection_from_commutators(tensor) if Gamma is None else np.asarray(Gamma, dtype=np.float64)
    riemann = np.zeros((3, 3, 3, 3), dtype=np.float64)
    for delta in range(3):
        for gamma in range(3):
            for alpha in range(3):
                for beta in range(3):
                    term = 0.0
                    for eps_i in range(3):
                        term += Gamma_eff[eps_i, gamma, beta] * Gamma_eff[delta, eps_i, alpha]
                        term -= Gamma_eff[eps_i, gamma, alpha] * Gamma_eff[delta, eps_i, beta]
                        term -= tensor[eps_i, alpha, beta] * Gamma_eff[delta, gamma, eps_i]
                    riemann[delta, gamma, alpha, beta] = term
    ricci = np.zeros((3, 3), dtype=np.float64)
    for gamma in range(3):
        for beta in range(3):
            ricci[gamma, beta] = float(np.sum(riemann[:, gamma, :, beta].diagonal()))
    ricci_scalar = gamma_trace(ricci)
    return ricci, ricci_scalar, pstf_rank2(ricci)


def spatial_ricci_from_compact_formula(
    algebra: BianchiAlgebra,
) -> tuple[np.ndarray, float, np.ndarray]:
    """Family-aware compact Ricci route from canonical ``(a, n)`` data."""

    n1, n2, n3 = np.diag(algebra.n)
    a_sq = float(np.dot(algebra.a, algebra.a))
    R11 = 0.5 * (n1 * n1 - (n2 - n3) ** 2)
    R22 = 0.5 * (n2 * n2 - (n3 - n1) ** 2)
    R33 = 0.5 * (n3 * n3 - (n1 - n2) ** 2)
    ricci = np.diag([R11, R22, R33]).astype(np.float64) - 2.0 * a_sq * np.eye(3, dtype=np.float64)
    ricci_scalar = gamma_trace(ricci)
    return ricci, ricci_scalar, pstf_rank2(ricci)


def dual_route_curvature_residual(
    ricci_route_a: np.ndarray,
    ricci_route_b: np.ndarray | None,
) -> tuple[str, float]:
    """Return the machine-readable dual-route curvature residual contract."""

    if ricci_route_b is None:
        return "UNAVAILABLE", float("nan")
    residual = float(np.max(np.abs(np.asarray(ricci_route_a) - np.asarray(ricci_route_b))))
    return "AVAILABLE", residual


def spatial_ricci(C: np.ndarray) -> tuple[np.ndarray, float, np.ndarray]:
    """Compatibility alias for the connection-route Ricci helper."""

    return spatial_ricci_from_connection(C)


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

    With the storage convention ``Gamma[mu, slot, deriv]``, this becomes

    `D_gamma X_{alpha beta} = -Gamma^mu_{alpha gamma} X_{mu beta}
                              -Gamma^mu_{beta gamma} X_{alpha mu}`.
    """

    X = np.asarray(tensor, dtype=np.float64)
    connection = np.asarray(Gamma, dtype=np.float64)
    D = np.zeros((3, 3, 3), dtype=np.float64)
    for gamma in range(3):
        for alpha in range(3):
            for beta in range(3):
                for mu in range(3):
                    D[gamma, alpha, beta] -= connection[mu, alpha, gamma] * X[mu, beta]
                    D[gamma, alpha, beta] -= connection[mu, beta, gamma] * X[alpha, mu]
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
    compact_ricci_tensor: np.ndarray | None = None
    compact_ricci_scalar: float | None = None
    compact_ricci_pstf: np.ndarray | None = None
    dual_route_status: str = "UNAVAILABLE"
    dual_route_curvature_residual_norm: float = float("nan")
    compact_formula_status: str = "UNAVAILABLE"

    def __post_init__(self) -> None:
        Gamma = np.asarray(self.Gamma, dtype=np.float64)
        ricci_tensor = np.asarray(self.ricci_tensor, dtype=np.float64)
        ricci_pstf = np.asarray(self.ricci_pstf, dtype=np.float64)
        compact_ricci_tensor = (
            None if self.compact_ricci_tensor is None else np.asarray(self.compact_ricci_tensor, dtype=np.float64)
        )
        compact_ricci_pstf = (
            None if self.compact_ricci_pstf is None else np.asarray(self.compact_ricci_pstf, dtype=np.float64)
        )
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
        if compact_ricci_tensor is not None and compact_ricci_tensor.shape != (3, 3):
            raise ValueError(
                f"TetradGeometry.compact_ricci_tensor must have shape (3,3), got {compact_ricci_tensor.shape}"
            )
        if compact_ricci_pstf is not None and compact_ricci_pstf.shape != (3, 3):
            raise ValueError(
                f"TetradGeometry.compact_ricci_pstf must have shape (3,3), got {compact_ricci_pstf.shape}"
            )
        object.__setattr__(self, "Gamma", Gamma)
        object.__setattr__(self, "ricci_tensor", ricci_tensor)
        object.__setattr__(self, "ricci_pstf", ricci_pstf)
        object.__setattr__(self, "compact_ricci_tensor", compact_ricci_tensor)
        object.__setattr__(self, "compact_ricci_pstf", compact_ricci_pstf)

    @property
    def torsion_residual_norm(self) -> float:
        residual = np.swapaxes(self.Gamma, 1, 2) - self.Gamma - self.algebra.C
        return float(np.max(np.abs(residual)))

    @property
    def S_AB(self) -> np.ndarray:
        return self.ricci_pstf


def _as_algebra(spec_or_algebra: FamilySpec | BianchiAlgebra) -> BianchiAlgebra:
    if isinstance(spec_or_algebra, FamilySpec):
        return spec_or_algebra.algebra
    return spec_or_algebra


def build_geometry(spec_or_algebra: FamilySpec | BianchiAlgebra) -> TetradGeometry:
    """Construct canonical geometry operators from a ver3 family/algebra object."""

    algebra = _as_algebra(spec_or_algebra)
    Gamma = connection_from_commutators(algebra.C)
    ricci_tensor, ricci_scalar, ricci_pstf = spatial_ricci_from_connection(algebra.C, Gamma=Gamma)
    compact_ricci_tensor, compact_ricci_scalar, compact_ricci_pstf = spatial_ricci_from_compact_formula(algebra)
    dual_status, dual_residual = dual_route_curvature_residual(ricci_tensor, compact_ricci_tensor)
    return TetradGeometry(
        algebra=algebra,
        Gamma=Gamma,
        ricci_tensor=ricci_tensor,
        ricci_scalar=ricci_scalar,
        ricci_pstf=ricci_pstf,
        compact_ricci_tensor=compact_ricci_tensor,
        compact_ricci_scalar=compact_ricci_scalar,
        compact_ricci_pstf=compact_ricci_pstf,
        dual_route_status=dual_status,
        dual_route_curvature_residual_norm=dual_residual,
        compact_formula_status="AVAILABLE",
    )
