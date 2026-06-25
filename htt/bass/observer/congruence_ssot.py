"""Single-source-of-truth first-jet kinematics for signature (-,+,+,+).

A velocity or rapidity at one event does *not* determine expansion, shear, or
vorticity.  Those quantities require a congruence first jet.  This module is
therefore deliberately fail-closed on incomplete input.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import numpy as np

METRIC_SIGNATURE = '(-,+,+,+)'


@dataclass
class CongruenceFirstJet:
    g_cov: np.ndarray             # g_ab
    dg_cov: np.ndarray            # partial_c g_ab, shape (4,4,4)
    u_contra: np.ndarray          # u^a
    du_contra: np.ndarray         # partial_b u^a, shape (4,4)
    label: str = 'unspecified'

    def __post_init__(self) -> None:
        self.g_cov = np.asarray(self.g_cov, dtype=float)
        self.dg_cov = np.asarray(self.dg_cov, dtype=float)
        self.u_contra = np.asarray(self.u_contra, dtype=float)
        self.du_contra = np.asarray(self.du_contra, dtype=float)
        if self.g_cov.shape != (4,4) or self.dg_cov.shape != (4,4,4):
            raise ValueError('metric first jet must have shapes (4,4) and (4,4,4)')
        if self.u_contra.shape != (4,) or self.du_contra.shape != (4,4):
            raise ValueError('congruence first jet must have shapes (4,) and (4,4)')
        if not np.allclose(self.g_cov, self.g_cov.T, atol=1e-12, rtol=0):
            raise ValueError('metric must be symmetric')


@dataclass(frozen=True)
class KinematicDecomposition:
    theta: float
    acceleration_cov: np.ndarray
    shear_cov: np.ndarray
    vorticity_cov: np.ndarray
    projector_cov: np.ndarray
    covariant_derivative_u: np.ndarray
    reconstruction_error: float
    normalization_error: float
    derivative_normalization_error: float


def _christoffel(g: np.ndarray, dg: np.ndarray) -> np.ndarray:
    gi = np.linalg.inv(g)
    gamma = np.zeros((4,4,4), dtype=float)
    for a in range(4):
        for b in range(4):
            for c in range(4):
                gamma[a,b,c] = 0.5 * sum(
                    gi[a,d] * (dg[b,d,c] + dg[c,d,b] - dg[d,b,c])
                    for d in range(4)
                )
    return gamma


def decompose_first_jet(jet: CongruenceFirstJet, atol: float = 2e-9) -> KinematicDecomposition:
    g = jet.g_cov
    eig = np.linalg.eigvalsh(g)
    if np.count_nonzero(eig < 0) != 1 or np.count_nonzero(eig > 0) != 3:
        raise ValueError(f'metric does not have signature {METRIC_SIGNATURE}: eigenvalues={eig}')
    gi = np.linalg.inv(g)
    u = jet.u_contra
    uc = g @ u
    norm_err = abs(float(u @ uc) + 1.0)
    if norm_err > atol:
        raise ValueError(f'u is not unit timelike: error={norm_err}')

    # d_b u_a = (d_b g_ac)u^c + g_ac d_b u^c
    du_cov = np.zeros((4,4), dtype=float)  # [a,b]
    for a in range(4):
        for b in range(4):
            du_cov[a,b] = np.dot(jet.dg_cov[b,a,:], u) + np.dot(g[a,:], jet.du_contra[b,:])
    gamma = _christoffel(g, jet.dg_cov)
    nabla = np.zeros((4,4), dtype=float)  # nabla_b u_a as [a,b]
    for a in range(4):
        for b in range(4):
            nabla[a,b] = du_cov[a,b] - np.dot(gamma[:,a,b], uc)

    # Derivative of g_ab u^a u^b for each coordinate derivative.
    dnorm = np.empty(4, dtype=float)
    for b in range(4):
        dnorm[b] = np.einsum('ac,a,c', jet.dg_cov[b], u, u) + 2*np.einsum('ac,a,c', g, jet.du_contra[b], u)
    dnorm_err = float(np.max(np.abs(dnorm)))
    if dnorm_err > 20 * atol:
        raise ValueError(f'first jet violates differentiated normalization: error={dnorm_err}')

    h_cov = g + np.outer(uc, uc)
    h_contra = gi + np.outer(u, u)
    p_mixed = np.eye(4) + np.outer(uc, u)  # h_a^c
    bproj = p_mixed @ nabla @ p_mixed.T
    theta = float(np.einsum('ab,ab', h_contra, bproj))
    sym = 0.5 * (bproj + bproj.T)
    anti = 0.5 * (bproj - bproj.T)
    shear = sym - (theta / 3.0) * h_cov
    accel = nabla @ u
    reconstruction = -np.outer(accel, uc) + (theta/3.0)*h_cov + shear + anti
    rec_err = float(np.max(np.abs(nabla - reconstruction)))
    if rec_err > 50 * atol:
        raise RuntimeError(f'kinematic reconstruction failed: error={rec_err}')
    return KinematicDecomposition(
        theta=theta,
        acceleration_cov=accel,
        shear_cov=shear,
        vorticity_cov=anti,
        projector_cov=h_cov,
        covariant_derivative_u=nabla,
        reconstruction_error=rec_err,
        normalization_error=norm_err,
        derivative_normalization_error=dnorm_err,
    )


def lorentz_boost_matrix(velocity: np.ndarray) -> np.ndarray:
    """Active Lorentz boost mapping (1,0,0,0) to gamma(1,v)."""
    v = np.asarray(velocity, dtype=float).reshape(3)
    v2 = float(v @ v)
    if v2 >= 1.0:
        raise ValueError('speed must satisfy |v|<1 (c=1 internally)')
    if v2 == 0.0:
        return np.eye(4)
    gamma = 1.0 / np.sqrt(1.0 - v2)
    out = np.eye(4)
    out[0,0] = gamma
    out[0,1:] = gamma * v
    out[1:,0] = gamma * v
    out[1:,1:] += (gamma - 1.0) * np.outer(v, v) / v2
    return out


def rapidity_vector_to_velocity(rapidity_vector: np.ndarray) -> np.ndarray:
    r = np.asarray(rapidity_vector, dtype=float).reshape(3)
    eta = float(np.linalg.norm(r))
    if eta == 0.0:
        return np.zeros(3)
    return np.tanh(eta) * r / eta


def compose_rapidity_vectors(first: np.ndarray, second: np.ndarray) -> dict:
    """Exact non-collinear composition; order is second after first."""
    l1 = lorentz_boost_matrix(rapidity_vector_to_velocity(first))
    l2 = lorentz_boost_matrix(rapidity_vector_to_velocity(second))
    total = l2 @ l1
    u = total @ np.array([1.0, 0.0, 0.0, 0.0])
    v = u[1:] / u[0]
    eta = np.arctanh(np.linalg.norm(v)) if np.linalg.norm(v) else 0.0
    r = np.zeros(3) if eta == 0 else eta * v / np.linalg.norm(v)
    minkowski = np.diag([-1.0,1.0,1.0,1.0])
    lorentz_error = float(np.max(np.abs(total.T @ minkowski @ total - minkowski)))
    return {'lorentz_matrix': total, 'velocity': v, 'rapidity_vector': r,
            'lorentz_error': lorentz_error}
