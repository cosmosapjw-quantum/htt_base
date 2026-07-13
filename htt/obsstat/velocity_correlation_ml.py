"""Maximum-likelihood noise-aware velocity-field f sigma_8 (REV-R198).

The precision upgrade of the rev-r196 pair-correlation DIAGNOSTIC (Johnson+2014,
MNRAS 444, 3926; CF4 arXiv:2604.08314). The simplified pair estimator fits the
Gorski Psi_par/Psi_perp by least squares, ignoring the noise covariance and the
cross-correlations between pairs, so its f sigma_8 is treatment-dependent. The
maximum-likelihood field estimator instead uses the FULL Gaussian likelihood of
the velocity data vector u with covariance

    C(A) = A * G + N ,   A = (f sigma_8 / f sigma_8_fid)^2 ,

where G is the fiducial linear velocity covariance (the same closed-form
Psi_par/Psi_perp tensor, `mv_bulkflow.pair_velocity_covariance`, which scales as
(f sigma_8)^2) and N = diag(noise variance) is the measurement + nonlinear-
dispersion noise. Maximising ln L over the single amplitude A gives f sigma_8 and
its Fisher error -- noise-aware (N enters C) and correlation-aware (the G
off-diagonals enter C), unlike the pair least-squares.

Fast profile: whiten by N^{-1/2} and eigendecompose Gt = N^{-1/2} G N^{-1/2} =
U diag(lam) U^T ONCE; then for every A,

    -2 ln L(A) = sum_i c_i/(A lam_i + 1) + sum_i ln(A lam_i + 1) + ln|N|,
    c = (U^T N^{-1/2} u)^2 ,

so the amplitude scan + curvature are O(N) after the one O(N^3) eigendecomp.

Diagnostic-tier growth-rate (f sigma_8) constraint; no Bianchi family, geometry,
or observer-frame claim.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class MLFsigma8:
    f_sigma8: float
    f_sigma8_fisher_error: float
    amplitude: float                  # A = (fs8/fs8_fid)^2
    amplitude_error: float
    fs8_fid: float
    n_data: int


def _eig_whiten(G, noise_var):
    inv_sqrt = 1.0 / np.sqrt(noise_var)
    Gt = (inv_sqrt[:, None] * np.asarray(G, float)) * inv_sqrt[None, :]
    Gt = 0.5 * (Gt + Gt.T)
    lam, U = np.linalg.eigh(Gt)
    return lam, U, inv_sqrt


def _profile(lam, U, inv_sqrt, u, ln_det_N):
    c = ((inv_sqrt * np.asarray(u, float)) @ U) ** 2

    def m2lnL(A):
        d = A * lam + 1.0
        if np.any(d <= 0.0):
            return np.inf
        return float(np.sum(c / d) + np.sum(np.log(d)) + ln_det_N)
    return m2lnL


def ml_from_eig(lam, U, inv_sqrt, ln_det_N, u, fs8_fid, *, a_max=9.0):
    """ML A from a PREcomputed whitened eigenbasis (reuse across injections).

    Returns (MLFsigma8, railed) where railed=True if A_hat hit a_max (the data
    are noise-dominated and the amplitude is not reliably bounded)."""
    from scipy.optimize import minimize_scalar
    m2lnL = _profile(lam, U, inv_sqrt, u, ln_det_N)
    lam_min = float(lam.min())
    a_hi = a_max if lam_min >= 0 else min(a_max, -0.999 / lam_min)
    grid = np.linspace(1e-4, a_hi, 200)
    vals = np.array([m2lnL(A) for A in grid])
    a0 = float(grid[np.argmin(vals)])
    step = grid[1] - grid[0]
    res = minimize_scalar(m2lnL, bounds=(max(1e-5, a0 - step), min(a_hi, a0 + step)),
                          method="bounded")
    A_hat = float(res.x)
    railed = bool(A_hat > 0.98 * a_hi)
    dA = max(1e-4, 0.01 * A_hat)
    f0, fp, fm = m2lnL(A_hat), m2lnL(A_hat + dA), m2lnL(A_hat - dA)
    curv = (fp - 2.0 * f0 + fm) / dA ** 2          # d^2(-2lnL)/dA^2 = 2 Fisher
    A_err = float(np.sqrt(2.0 / curv)) if curv > 0 else float("nan")
    fs8 = fs8_fid * np.sqrt(A_hat) if A_hat > 0 else 0.0
    fs8_err = (fs8_fid / (2.0 * np.sqrt(A_hat)) * A_err
               if (A_hat > 0 and np.isfinite(A_err)) else float("nan"))
    return MLFsigma8(float(fs8), float(fs8_err), A_hat, A_err,
                     float(fs8_fid), int(len(u))), railed


def whiten_eig(G, noise_var):
    """Whitened eigenbasis (lam, U, inv_sqrt, ln_det_N) of C(A) = A G + N."""
    noise_var = np.asarray(noise_var, float)
    lam, U, inv_sqrt = _eig_whiten(G, noise_var)
    return lam, U, inv_sqrt, float(np.sum(np.log(noise_var)))


def ml_fsigma8_field(G, noise_var, u, fs8_fid, *, a_max=9.0):
    """Field-level ML f sigma_8 from C(A) = A G + diag(noise_var). Convenience
    wrapper (eigendecomposes G every call); returns MLFsigma8 (drops the rail
    flag -- use ml_from_eig when you need it or a reused eigenbasis)."""
    lam, U, inv_sqrt, ln_det_N = whiten_eig(G, noise_var)
    fit, _ = ml_from_eig(lam, U, inv_sqrt, ln_det_N, u, fs8_fid, a_max=a_max)
    return fit


def profile_curve(G, noise_var, u, fs8_fid, fs8_grid):
    """-2 Delta ln L vs f sigma_8 on fs8_grid (for a likelihood diagnostic)."""
    noise_var = np.asarray(noise_var, float)
    lam, U, inv_sqrt = _eig_whiten(G, noise_var)
    ln_det_N = float(np.sum(np.log(noise_var)))
    m2lnL = _profile(lam, U, inv_sqrt, u, ln_det_N)
    A_grid = (np.asarray(fs8_grid, float) / fs8_fid) ** 2
    vals = np.array([m2lnL(A) for A in A_grid])
    return vals - vals.min()
