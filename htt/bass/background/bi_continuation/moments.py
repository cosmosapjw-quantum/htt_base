"""Multispecies tilted-perfect-fluid moments for a Bianchi-I normal frame."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence
import numpy as np


def _stf(t: np.ndarray) -> np.ndarray:
    s = 0.5 * (np.asarray(t, dtype=float) + np.asarray(t, dtype=float).T)
    return s - np.eye(3) * np.trace(s) / 3.0


@dataclass(frozen=True)
class SpeciesPrimitive:
    rho_hat: float
    w: float
    velocity: np.ndarray
    name: str = 'species'

    def __post_init__(self):
        v = np.asarray(self.velocity, dtype=float).reshape(3)
        object.__setattr__(self, 'velocity', v)
        if self.rho_hat < 0:
            raise ValueError('rho_hat must be nonnegative')
        if not (-1.0 < self.w <= 1.0):
            raise ValueError('this continuation branch requires -1 < w <= 1')
        if float(v @ v) >= 1.0:
            raise ValueError('species speed must satisfy v^2<1 (c=1)')


@dataclass(frozen=True)
class NormalProjection:
    mu: float
    pressure: float
    flux: np.ndarray
    anisotropic_stress: np.ndarray
    gamma: float


@dataclass(frozen=True)
class TiltMoments:
    J: np.ndarray
    K: np.ndarray
    Omega_tilt: float
    Pi: np.ndarray
    total_projection: NormalProjection
    normalization: float


def project_species(species: SpeciesPrimitive) -> NormalProjection:
    v = species.velocity
    v2 = float(v @ v)
    gamma = 1.0 / np.sqrt(1.0 - v2)
    p0 = species.w * species.rho_hat
    h0 = species.rho_hat + p0
    mu = gamma*gamma*h0 - p0
    p = p0 + gamma*gamma*h0*v2/3.0
    q = gamma*gamma*h0*v
    pi = gamma*gamma*h0*_stf(np.outer(v, v))
    return NormalProjection(mu, p, q, pi, gamma)


def total_projection(species: Sequence[SpeciesPrimitive]) -> NormalProjection:
    projections = [project_species(s) for s in species]
    return NormalProjection(
        mu=float(sum(p.mu for p in projections)),
        pressure=float(sum(p.pressure for p in projections)),
        flux=sum((p.flux for p in projections), np.zeros(3)),
        anisotropic_stress=sum((p.anisotropic_stress for p in projections), np.zeros((3,3))),
        gamma=float('nan'),
    )


def tilt_moments(species: Sequence[SpeciesPrimitive], H: float, kappa: float = 1.0) -> TiltMoments:
    if H <= 0:
        raise ValueError('H must be positive for Hubble-normalized moments')
    factor = kappa / (3.0 * H * H)
    J = np.zeros(3)
    K = np.zeros((3,3))
    for s in species:
        p = project_species(s)
        J += factor * p.flux
        h0 = (1.0 + s.w) * s.rho_hat
        K += factor * (p.gamma**2) * h0 * np.outer(s.velocity, s.velocity)
    omega = float(np.trace(K))
    return TiltMoments(J=J, K=K, Omega_tilt=omega, Pi=_stf(K),
                       total_projection=total_projection(species), normalization=factor)


def codazzi_residual_bianchi_i(moments: TiltMoments) -> np.ndarray:
    """For the registered flat Bianchi-I normal-frame branch, Codazzi is J_a=0."""
    return moments.J.copy()


def realizability_margin(K: np.ndarray) -> float:
    k = 0.5 * (np.asarray(K, dtype=float) + np.asarray(K, dtype=float).T)
    return float(np.min(np.linalg.eigvalsh(k)))


def abstract_antipodal_pair_decomposition(K: np.ndarray, tol: float = 1e-12) -> list[dict]:
    """Spectral realization of a PSD second moment by antipodal stream pairs.

    Each pair contributes ``weight * e e^T`` and exactly zero first moment.
    This is an abstract moment realization, not a unique physical species
    decomposition.
    """
    k = 0.5 * (np.asarray(K, dtype=float) + np.asarray(K, dtype=float).T)
    values, vectors = np.linalg.eigh(k)
    if float(np.min(values)) < -tol * max(1.0, float(np.max(np.abs(values)))):
        raise ValueError('K is not positive semidefinite')
    out = []
    for value, direction in zip(values, vectors.T):
        if value > tol:
            out.append({'weight': float(value), 'directions': [direction.copy(), -direction.copy()]})
    return out
