"""Conditional Gaussian carrier reductions; no cosmological response is assumed.

G=X^T C^-1 X and b=X^T C^-1 y are a fixed-design normal-equation
carrier. Profile a declared nuisance subspace before comparing compressions.
This is Gaussian linear algebra, not a new sufficiency theorem.
"""
from __future__ import annotations

import numpy as np
from scipy.linalg import cho_factor, cho_solve


def _spd_solve(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Equilibrated SPD solve, without jitter or silently removed modes."""
    a = np.asarray(a, float)
    if a.ndim != 2 or a.shape[0] != a.shape[1] or not np.isfinite(a).all():
        raise ValueError("finite square information required")
    if not np.allclose(a, a.T, rtol=1e-12, atol=1e-13):
        raise ValueError("information must be symmetric")
    d = np.sqrt(np.diag(a))
    if not np.isfinite(d).all() or np.any(d <= 0):
        raise ValueError("information diagonal must be positive")
    scale = d[:, None] if np.ndim(b) == 2 else d
    return cho_solve(cho_factor(a / d[:, None] / d[None, :], lower=True), b / scale) / scale


def profile_normal_carrier(G, b, signal, nuisance):
    """Return (F,t) with log L(theta)-log L(0)=theta.t-theta.F.theta/2.

    Nuisance coefficients have an unrestricted common flat measure. This gives
    profile likelihood ratios (and a conditional Gaussian posterior with flat
    signal prior), not evidences between different nuisance models.
    """
    G, b, J, N = [np.asarray(x, float) for x in (G, b, signal, nuisance)]
    n = len(b)
    if G.shape != (n, n) or J.ndim != 2 or N.ndim != 2 or J.shape[0] != n or N.shape[0] != n:
        raise ValueError("incompatible normal carrier dimensions")
    if not all(np.isfinite(x).all() for x in (G, b, J, N)):
        raise ValueError("finite carrier required")
    # Validate the complete working law, not just a successful Schur complement.
    _spd_solve(G, b)
    F, t = J.T @ G @ J, J.T @ b
    if N.shape[1]:
        H, cross = N.T @ G @ N, J.T @ G @ N
        F = F - cross @ _spd_solve(H, cross.T)
        t = t - cross @ _spd_solve(H, N.T @ b)
    F = (F + F.T) / 2
    mean = _spd_solve(F, t)
    return F, t, mean, _spd_solve(F, np.eye(len(t)))


def linear_compression_information(F, compression):
    """Information retained by x=B theta_hat for theta_hat~N(theta,F^-1)."""
    F, B = np.asarray(F, float), np.asarray(compression, float)
    if B.ndim != 2 or B.shape[1] != F.shape[0] or not np.isfinite(B).all():
        raise ValueError("finite compression matrix with compatible width required")
    C = _spd_solve(F, np.eye(F.shape[0]))
    return B.T @ _spd_solve(B @ C @ B.T, B)


def log_likelihood_ratio(F, t, theta, reference):
    theta, reference = np.asarray(theta, float), np.asarray(reference, float)
    return float((theta-reference) @ t - (theta @ F @ theta-reference @ F @ reference)/2)
