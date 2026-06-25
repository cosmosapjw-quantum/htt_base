"""Constraint-tested Bianchi-I multifluid continuation branch.

Assumptions: expanding geodesic normal congruence, Fermi-propagated orthonormal
triad, Bianchi I, homogeneous non-interacting perfect-fluid species with
p_hat=w rho_hat, and signature (-,+,+,+).  Internal units use c=1 while kappa
and Lambda remain explicit.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
import numpy as np

from .moments import SpeciesPrimitive, total_projection


def _stf(t: np.ndarray) -> np.ndarray:
    s = 0.5 * (np.asarray(t, dtype=float) + np.asarray(t, dtype=float).T)
    return s - np.eye(3) * np.trace(s) / 3.0


@dataclass(frozen=True)
class BIState:
    a: float
    H: float
    sigma: np.ndarray
    species: tuple[SpeciesPrimitive, ...]

    def __post_init__(self):
        s = _stf(np.asarray(self.sigma, dtype=float).reshape(3,3))
        object.__setattr__(self, 'sigma', s)
        object.__setattr__(self, 'species', tuple(self.species))
        if self.a <= 0 or self.H <= 0:
            raise ValueError('this branch requires a>0 and H>0')


@dataclass(frozen=True)
class BIRHS:
    adot: float
    Hdot: float
    sigmadot: np.ndarray
    rho_dot: tuple[float, ...]
    velocity_dot: tuple[np.ndarray, ...]


def rhs(state: BIState, kappa: float = 1.0, Lambda: float = 0.0,
        include_anisotropic_stress: bool = True) -> BIRHS:
    H, sigma = state.H, state.sigma
    rho_dot = []
    velocity_dot = []
    for sp in state.species:
        v = sp.velocity
        v2 = float(v @ v)
        svv = float(v @ sigma @ v)
        den = 1.0 - sp.w * v2
        rhofrac = -(1.0 + sp.w) * (H*(3.0-v2) - svv) / den
        rho_dot.append(sp.rho_hat * rhofrac)
        scalar = (H*(1.0-3.0*sp.w)*(1.0-v2) - (1.0-sp.w)*svv) / den
        velocity_dot.append(-sigma @ v - scalar * v)

    projection = total_projection(state.species)
    sigma2 = 0.5 * float(np.einsum('ij,ij', sigma, sigma))
    Hdot = -H*H - (2.0/3.0)*sigma2 - (kappa/6.0)*(projection.mu + 3.0*projection.pressure) + Lambda/3.0
    pi = projection.anisotropic_stress if include_anisotropic_stress else np.zeros((3,3))
    sigmadot = _stf(-3.0*H*sigma + kappa*pi)
    return BIRHS(state.a*H, Hdot, sigmadot, tuple(rho_dot), tuple(velocity_dot))


def _pack(state: BIState) -> np.ndarray:
    pieces = [[state.a, state.H], state.sigma.reshape(-1)]
    for sp in state.species:
        pieces.extend([[sp.rho_hat], sp.velocity])
    return np.concatenate([np.asarray(x, dtype=float).reshape(-1) for x in pieces])


def _unpack(y: np.ndarray, template: BIState) -> BIState:
    y = np.asarray(y, dtype=float)
    a, H = y[:2]
    sigma = y[2:11].reshape(3,3)
    pos = 11
    species = []
    for old in template.species:
        rho = float(y[pos]); v = y[pos+1:pos+4]
        pos += 4
        species.append(SpeciesPrimitive(rho, old.w, v, old.name))
    return BIState(float(a), float(H), sigma, tuple(species))


def _pack_rhs(value: BIRHS) -> np.ndarray:
    pieces = [[value.adot, value.Hdot], value.sigmadot.reshape(-1)]
    for rd, vd in zip(value.rho_dot, value.velocity_dot):
        pieces.extend([[rd], vd])
    return np.concatenate([np.asarray(x, dtype=float).reshape(-1) for x in pieces])


def rk4_step(state: BIState, dt: float, kappa: float = 1.0, Lambda: float = 0.0,
             include_anisotropic_stress: bool = True) -> BIState:
    y = _pack(state)
    def f(z):
        return _pack_rhs(rhs(_unpack(z, state), kappa, Lambda, include_anisotropic_stress))
    k1 = f(y)
    k2 = f(y + 0.5*dt*k1)
    k3 = f(y + 0.5*dt*k2)
    k4 = f(y + dt*k3)
    return _unpack(y + dt*(k1 + 2*k2 + 2*k3 + k4)/6.0, state)


def integrate(state: BIState, times: np.ndarray, kappa: float = 1.0, Lambda: float = 0.0,
              include_anisotropic_stress: bool = True) -> list[BIState]:
    t = np.asarray(times, dtype=float)
    if t.ndim != 1 or len(t) < 1 or np.any(np.diff(t) <= 0):
        raise ValueError('times must be a strictly increasing 1D array')
    out = [state]
    current = state
    for dt in np.diff(t):
        current = rk4_step(current, float(dt), kappa, Lambda, include_anisotropic_stress)
        out.append(current)
    return out


def constraint_residuals(state: BIState, kappa: float = 1.0, Lambda: float = 0.0) -> dict:
    p = total_projection(state.species)
    sigma2 = 0.5 * float(np.einsum('ij,ij', state.sigma, state.sigma))
    gauss = 3.0*state.H*state.H - kappa*p.mu - sigma2 - Lambda
    return {'gauss': float(gauss), 'codazzi': np.asarray(p.flux, dtype=float)}


def dust_flrw_exact(t: np.ndarray, H0: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    t = np.asarray(t, dtype=float)
    d = 1.0 + 1.5*H0*t
    return d**(2.0/3.0), H0/d
