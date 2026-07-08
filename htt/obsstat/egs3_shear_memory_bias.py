"""EGS3 Axis F: shear-memory kernel bias of the registered closure (P13 companion).

P13 registers the shear transport law in the Weyl-explicit form

    sigma'_<ab> + c_H H sigma_ab + E_ab = lambda_Pi Pi_ab + N_ab,

and the exact LINEARIZED 1+3 law has c_H = 2 and lambda_Pi = kappa/2. The naive
scalar closure sigma' = -3 H sigma + kappa_hat Pi (the form the external review
flagged) differs in (i) the friction coefficient (3H vs 2H), (ii) the coupling
(kappa_hat vs kappa/2), and (iii) the MISSING electric-Weyl term E_ab. This module
QUANTIFIES the kappa-inference bias those differences produce, under a declared toy
Weyl closure E = e0 H sigma:

  exact law:       sigma' = -(2 + e0) H sigma + (kappa/2) Pi
  registered fit:  kappa_hat = argmin sum_z [ sigma' + 3 H sigma - kappa Pi ]^2

Structure of the answer (closed form, no noise): sigma' + 3 H sigma =
(1 - e0) H sigma + (kappa/2) Pi, so

  kappa_hat = kappa/2 + (1 - e0) H <Pi, sigma> / <Pi, Pi>,

which is UNBIASED (kappa_hat = kappa/2) exactly when e0 = 1 (the toy friction
matches 3H) and increasingly biased as |e0 - 1| grows. The qualitative P13
conclusion (dsigma'/dPi != 0, shear remembers anisotropic stress) SURVIVES for all
e0; the QUANTITATIVE kernel does not survive an unregistered closure -- which is
exactly why P13 marks the coefficients convention-dependent and the quantitative
use closure-conditional (ledger status DERIVED_CONDITIONAL).

Same driving history for both laws: Pi(z) = Pi0 exp(-z/z0) on z in [0, 3], H
constant, sigma(0) = 0 (integrating-factor closed form, mirrors
`egs3_volterra_memory.volterra_shear`).

Claim discipline. Toy-closure diagnostic only; the exact physical E_ab transfer
awaits the native low-ell solver; no data, detection, family/geometry, or
native-solver claim.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

__all__ = [
    "exact_linearized_shear",
    "registered_law_shear",
    "fit_registered_kappa",
    "ShearMemoryBias",
    "kappa_bias_curve",
]


def _exp_pi(pi0: float, z0: float, z: np.ndarray) -> np.ndarray:
    return float(pi0) * np.exp(-np.asarray(z, dtype=float) / float(z0))


def exact_linearized_shear(z_grid, *, pi0: float = 1e-3, z0: float = 1.0,
                           H: float = 1.0, e0: float = 1.0, kappa: float = 1.0,
                           sigma0: float = 0.0) -> np.ndarray:
    """Closed-form solution of sigma' = -(2 + e0) H sigma + (kappa/2) Pi with
    Pi = Pi0 exp(-z/z0) and sigma(0) = sigma0 (integrating factor, constant H)."""
    z = np.asarray(z_grid, dtype=float)
    a = (2.0 + float(e0)) * float(H)
    s = float(kappa) / 2.0 * float(pi0)
    lam = 1.0 / float(z0)
    if abs(a - lam) < 1e-12:
        particular = s * z * np.exp(-lam * z)
    else:
        particular = s * (np.exp(-lam * z) - np.exp(-a * z)) / (a - lam)
    return float(sigma0) * np.exp(-a * z) + particular


def registered_law_shear(z_grid, *, pi0: float = 1e-3, z0: float = 1.0,
                         H: float = 1.0, kappa_hat: float = 0.5,
                         sigma0: float = 0.0) -> np.ndarray:
    """Closed-form solution of the registered scalar closure
    sigma' = -3 H sigma + kappa_hat Pi under the same driving history."""
    z = np.asarray(z_grid, dtype=float)
    a = 3.0 * float(H)
    s = float(kappa_hat) * float(pi0)
    lam = 1.0 / float(z0)
    if abs(a - lam) < 1e-12:
        particular = s * z * np.exp(-lam * z)
    else:
        particular = s * (np.exp(-lam * z) - np.exp(-a * z)) / (a - lam)
    return float(sigma0) * np.exp(-a * z) + particular


def fit_registered_kappa(sigma: np.ndarray, sigma_prime: np.ndarray,
                         pi_vals: np.ndarray, *, H: float = 1.0) -> float:
    """Least-squares kappa_hat of the registered law on a given trajectory:
    kappa_hat = <Pi, sigma' + 3 H sigma> / <Pi, Pi>."""
    sigma = np.asarray(sigma, dtype=float)
    sigma_prime = np.asarray(sigma_prime, dtype=float)
    pi_vals = np.asarray(pi_vals, dtype=float)
    target = sigma_prime + 3.0 * float(H) * sigma
    denom = float(pi_vals @ pi_vals)
    if denom <= 0.0:
        raise ValueError("Pi history is identically zero: kappa is unidentified")
    return float(pi_vals @ target) / denom


@dataclass(frozen=True)
class ShearMemoryBias:
    e0_grid: tuple
    kappa_bias_ratio: tuple
    zero_crossing_e0: float
    pi0: float
    z0: float
    H: float
    kappa: float
    n_nodes: int


def kappa_bias_curve(e0_grid=(0.0, 0.5, 1.0, 1.5, 2.0), *, pi0: float = 1e-3,
                     z0: float = 1.0, H: float = 1.0, kappa: float = 1.0,
                     z_max: float = 3.0, n_nodes: int = 241) -> ShearMemoryBias:
    """Bias ratio kappa_hat / (kappa/2) - 1 of the registered-law fit on exact-law
    trajectories, as a function of the toy Weyl-closure coefficient e0.

    Deterministic (no noise); sigma' is evaluated ANALYTICALLY from the exact law
    (sigma' = -(2 + e0) H sigma + (kappa/2) Pi), so the bias isolates the kernel
    mismatch, not differentiation error."""
    z = np.linspace(0.0, float(z_max), int(n_nodes))
    pi_vals = _exp_pi(pi0, z0, z)
    biases = []
    for e0 in e0_grid:
        sigma = exact_linearized_shear(z, pi0=pi0, z0=z0, H=H, e0=e0, kappa=kappa)
        sigma_prime = -(2.0 + float(e0)) * float(H) * sigma + (kappa / 2.0) * pi_vals
        k_hat = fit_registered_kappa(sigma, sigma_prime, pi_vals, H=H)
        biases.append(k_hat / (kappa / 2.0) - 1.0)
    # locate the (analytic) zero crossing e0 = 1 from the sampled curve
    e0_arr = np.asarray(e0_grid, dtype=float)
    b_arr = np.asarray(biases, dtype=float)
    idx = int(np.argmin(np.abs(b_arr)))
    zero_e0 = float(e0_arr[idx])
    return ShearMemoryBias(
        e0_grid=tuple(float(e) for e in e0_grid),
        kappa_bias_ratio=tuple(float(b) for b in biases),
        zero_crossing_e0=zero_e0,
        pi0=float(pi0), z0=float(z0), H=float(H), kappa=float(kappa),
        n_nodes=int(n_nodes),
    )
