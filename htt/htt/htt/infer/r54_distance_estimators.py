"""R54 catalogue-level estimators of apparent-Hubble multipoles from distance-indicator data.

Purpose: replace the linear-in-distance estimator of R36 (which regresses c z on the noisy
catalogue distance) by an estimator that is linear in the noisy quantity, and expose both as
explicit operators so that the exact LCDM body O C_uu O^T (r54_lcdm_body) can be attached.

R54-EQ-34  log-distance ratio and model (fractional multipoles)
           eta_i = ln[y(z_i)/d_i],  y(z) = c (1+z) chi_hat(z) = H0 d_L(z)  (flat LCDM, H0-free),
           d_i = 10^((mu_i - 25)/5) Mpc
           eta_i = h + delta.n_i + n_i.kappa.n_i + g(z_i) u_i - s_i eps_i,   s_i = (ln10/5) e_mu,i
           h = ln H0, delta = fractional dipole of the apparent Hubble rate, kappa = STF quadrupole
           weights w_i = W(z_i)/tau_i^2,  tau_i^2 = s_i^2 + (sigma_* g_i)^2
           The distance modulus enters the response linearly: no errors-in-variables bias.
R54-EQ-35  R36 linear estimator (reproduced here for continuity and for its same-estimator null)
           c z_i = d_i (H + D.n_i + n_i.q.n_i),  weights W(z_i)/sigma_i^2,
           sigma_i = hypot(sigma_*, h_sigma (ln10/5) d_i e_mu,i).  The regressor d_i is noisy; for
           homogeneous errors and weights ~ 1/d^2 the fitted H is biased by exp(+s^2/2).
R54-EQ-36  magnitude equivalent of a fractional rate offset: Delta mu = -(5/ln10) Delta eta
           (a distance modulus that is too large lowers the apparent rate).

Conventions: n = unit vector observer -> source (ICRS); basis order [1, n_x, n_y, n_z, STF5]
with r54_tensor_five_view.STF5_BASIS; operators have shape (parameters, N) and act on the response.
"""
from __future__ import annotations

import math
from typing import Sequence

import numpy as np
from scipy.linalg import qr, solve_triangular

from . import r54_lcdm_body as lb
from . import r54_tensor_five_view as fv

LN10_OVER_5 = math.log(10.0) / 5.0
C_KM_S = 299792.458


def multipole_basis(nhat: np.ndarray) -> np.ndarray:
    """(N, 9) design [1, n, STF5(n)] with STF5_a(n) = n.E_a.n for the orthonormal STF basis E_a."""
    n = np.asarray(nhat, float)
    if n.ndim != 2 or n.shape[1] != 3 or np.abs(np.einsum("ij,ij->i", n, n) - 1.0).max() > 1e-9:
        raise ValueError("nhat must be (N, 3) unit vectors")
    stf = np.einsum("ni,aij,nj->na", n, fv.STF5_BASIS, n, optimize=True)
    return np.column_stack((np.ones(n.shape[0]), n, stf))


def wls_operator(design: np.ndarray, weights: np.ndarray, cond_limit: float = 1.0e10) -> np.ndarray:
    """(X^T W X)^-1 X^T W by an economic QR of sqrt(W) X; raises on a rank-deficient design."""
    x, w = np.asarray(design, float), np.asarray(weights, float)
    if x.ndim != 2 or w.shape != (x.shape[0],) or (w < 0).any() or not np.isfinite(w).all():
        raise ValueError("design must be (N, p) and weights (N,), non-negative and finite")
    keep = w > 0
    s = np.sqrt(w[keep])
    q, r = qr(s[:, None] * x[keep], mode="economic", check_finite=False)
    diag = np.abs(np.diag(r))
    if diag.min() <= 0 or np.linalg.cond(r) > cond_limit:
        raise ValueError("weighted design is rank deficient; the requested parameters are not identified")
    out = np.zeros((x.shape[1], x.shape[0]))
    out[:, keep] = solve_triangular(r, q.T, check_finite=False) * s[None, :]
    return out


def gaussian_window_weights(z: np.ndarray, centers: Sequence[float], width: float) -> np.ndarray:
    """(W, N) Gaussian redshift windows exp[-(z - z_w)^2 / (2 width^2)] (R36 convention, not normalised)."""
    z = np.asarray(z, float)
    if width <= 0:
        raise ValueError("window width must be positive")
    return np.exp(-0.5 * ((z[None, :] - np.asarray(centers, float)[:, None]) / width) ** 2)


def distance_mpc(mu: np.ndarray) -> np.ndarray:
    return 10.0 ** ((np.asarray(mu, float) - 25.0) / 5.0)


def r36_linear_window_operator(mu: np.ndarray, e_mu: np.ndarray, z: np.ndarray, nhat: np.ndarray, centers: Sequence[float],
                               width: float = 0.012, sigma_star: float = 250.0, h_sigma: float = 70.0) -> np.ndarray:
    """R36/H03 operator A (9W x N) acting on c z in km/s (R54-EQ-35); output rows [H, D(3), q(5)] per window."""
    d = distance_mpc(mu)
    sigma = np.hypot(sigma_star, h_sigma * LN10_OVER_5 * d * np.asarray(e_mu, float))
    design = d[:, None] * multipole_basis(nhat)
    win = gaussian_window_weights(z, centers, width)
    return np.concatenate([wls_operator(design, w / sigma**2) for w in win], axis=0)


def log_distance_ratio(mu: np.ndarray, z: np.ndarray, omega_m: float) -> dict:
    """eta = ln[y(z)/d] with its velocity response g(z) and the fiducial factors (R54-EQ-33/34)."""
    fac = lb.flat_lcdm_distance_factors(z, omega_m)
    return {"eta": np.log(fac["y_km_s"] / distance_mpc(mu)), "g_per_km_s": fac["g_per_km_s"],
            "y_km_s": fac["y_km_s"], "chi_hat": fac["chi_hat"]}


def log_noise_variance(e_mu: np.ndarray, g_per_km_s: np.ndarray, sigma_star: float = 250.0) -> np.ndarray:
    """tau^2 = [(ln10/5) e_mu]^2 + (sigma_* g)^2: distance-modulus error plus uncorrelated velocity noise."""
    return (LN10_OVER_5 * np.asarray(e_mu, float)) ** 2 + (sigma_star * np.asarray(g_per_km_s, float)) ** 2


def log_window_operator(tau2: np.ndarray, z: np.ndarray, nhat: np.ndarray, centers: Sequence[float], width: float = 0.012,
                        nuisance: np.ndarray | None = None, select: np.ndarray | None = None) -> np.ndarray:
    """Log-distance operator (9W x N) acting on eta; rows [h, delta(3), kappa(5)] per window (R54-EQ-34).

    ``nuisance`` (N, m): extra design columns fitted and marginalised in every window (their rows are dropped).
    ``select`` (N,) bool: objects outside the selection get zero weight.
    """
    base = multipole_basis(nhat)
    design = base if nuisance is None else np.column_stack((base, np.asarray(nuisance, float)))
    win = gaussian_window_weights(z, centers, width) / np.asarray(tau2, float)[None, :]
    if select is not None:
        win = win * np.asarray(select, bool)[None, :]
    return np.concatenate([wls_operator(design, w)[:9] for w in win], axis=0)


def white_covariance(op: np.ndarray, variance: np.ndarray) -> np.ndarray:
    """O diag(variance) O^T for independent per-object noise."""
    scaled = np.asarray(op, float) * np.sqrt(np.asarray(variance, float))[None, :]
    cov = scaled @ scaled.T
    return 0.5 * (cov + cov.T)


def magnitude_equivalent(delta_eta: float) -> float:
    """|Delta mu| in mag for a fractional rate offset (R54-EQ-36)."""
    return abs(float(delta_eta)) / LN10_OVER_5
