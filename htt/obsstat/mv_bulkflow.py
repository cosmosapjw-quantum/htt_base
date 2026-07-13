"""Minimum-variance (MV) ideal-window bulk-flow estimator (REV-R196).

Watkins-Feldman-Hudson 2009 (MNRAS 392, 743) / Feldman-Watkins-Hudson 2010
(MNRAS 407, 2328). Given line-of-sight peculiar velocities S_n at positions r_n
with unit vectors n_hat_n and errors sigma_n, the MV estimator forms the bulk
flow moments

    p_i = sum_n w_{i,n} S_n

whose weights minimise the variance <(p_i - U_i)^2> against the bulk flow U_i of
an IDEAL survey of a Gaussian window of scale R (exact velocities, uniform
sampling), subject to the unbiasedness constraint sum_n w_{i,n} n_hat_{n,j} =
delta_ij (a spatially constant flow B is recovered exactly). The weights tie the
estimator's effective window to the SPECIFIED large-scale W_R, so its
cosmic-variance covariance is the FAITHFUL one (unlike the rev-r195
noise-weighted GLS window, whose small-scale aliasing made its cosmic variance a
lower bound and forced the significance to be withheld).

Covariance (all in (km/s)^2), split into the two physically distinct pieces:

    R = R_v + R_eps,                                   (object/cell covariance)
    R^(v)_{mn} = (H0 f)^2/(2 pi)^3 int dk P(k) oint dOmega_k
                   (n_m.khat)(n_n.khat) exp(i k khat.(x_m - x_n)),
    R^(eps)_{mn} = delta_mn sigma_n^2 ,
    Q_{i,n} = <S_n U_i>
            = (H0 f)^2/(2 pi)^3 int dk P(k) e^{-k^2 R^2/2} oint dOmega_k
                   khat_i (n_n.khat) exp(-i k khat.x_n) ,
    w_i = R^{-1}(Q_i + G lambda_i),  lambda_i = (G^T R^{-1} G)^{-1}(e_i - G^T R^{-1} Q_i),
    Cov_cosmic = W R_v W^T ,   Cov_noise = W R_eps W^T .

The k^2 in d^3k cancels the 1/k^2 of the velocity kernel, leaving a 1-D radial
integral of a mode function on a HEALPix khat grid -- the pairwise generalisation
of the validated `cf4_bulkflow_lcdm_variance._mode_function_M`, using the shared
`velocity_power` P(k). Feasible on ~hundreds of binned cells (not the raw N^2).

Diagnostic-only kinematic descriptor; a bulk-flow-vs-LambdaCDM statement only, no
Bianchi family, geometry, or observer-frame claim.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class MVBulkFlow:
    vector: np.ndarray            # p_i (km/s), supergalactic Cartesian
    cov_cosmic: np.ndarray        # (3,3) LambdaCDM sample variance at scale R
    cov_noise: np.ndarray         # (3,3) measurement noise
    amplitude: float              # |p| (km/s)
    R_window: float               # Gaussian window scale (Mpc/h)
    n_cells: int

    @property
    def cov_total(self) -> np.ndarray:
        return self.cov_cosmic + self.cov_noise

    def amplitude_error(self, which: str = "total") -> float:
        cov = {"total": self.cov_total, "cosmic": self.cov_cosmic,
               "noise": self.cov_noise}[which]
        u = self.vector / max(self.amplitude, 1e-30)
        return float(np.sqrt(u @ cov @ u))


def _trapz(y, x):
    return np.trapz(y, x) if hasattr(np, "trapz") else np.trapezoid(y, x)


def pair_velocity_covariance(pos_hmpc, n_hat, pk, hf2, *, na=1000, kmin=1.0e-4,
                             kmax=10.0, nk=8000, sigma_v_sq=None):
    """R^(v) (Nc,Nc): linear pairwise radial-velocity covariance (km/s)^2 via the
    closed-form Gorski correlation functions (well-converged, no solid-angle
    grid):

        R^(v)_{mn} = Psi_perp(A) (n_m.n_n) + [Psi_par(A)-Psi_perp(A)]
                        (n_m.Ahat)(n_n.Ahat),   A = |x_m-x_n|, Ahat = (x_m-x_n)/A.

    Diagonal R^(v)_{mm} = sigma_v_1d^2 (validation anchor)."""
    from htt.obsstat.velocity_power import velocity_correlation_functions
    pos = np.asarray(pos_hmpc, float)
    nh = np.asarray(n_hat, float)
    nc = pos.shape[0]
    dx = pos[:, None, :] - pos[None, :, :]               # (Nc,Nc,3)
    A = np.linalg.norm(dx, axis=2)                        # (Nc,Nc)
    amax = float(A.max())
    a_grid = np.linspace(0.0, amax * 1.0001, na)
    psi_par_g, psi_perp_g = velocity_correlation_functions(
        pk, hf2, a_grid, kmin=kmin, kmax=kmax, nk=nk)
    psi_par = np.interp(A, a_grid, psi_par_g)
    psi_perp = np.interp(A, a_grid, psi_perp_g)
    cosang = nh @ nh.T                                    # (Nc,Nc)
    with np.errstate(invalid="ignore", divide="ignore"):
        ahat = dx / A[:, :, None]                         # (Nc,Nc,3); diag = nan
    pm = np.einsum("mi,mni->mn", nh, ahat)                # n_m . Ahat
    pn = np.einsum("ni,mni->mn", nh, ahat)                # n_n . Ahat
    R = psi_perp * cosang + (psi_par - psi_perp) * pm * pn
    sv2 = float(psi_par_g[0]) if sigma_v_sq is None else float(sigma_v_sq)
    np.fill_diagonal(R, sv2)                              # A->0 isotropic limit
    return 0.5 * (R + R.T)


def ideal_window_target(r_hmpc, n_hat, pk, hf2, R_window, *, kmin=1.0e-4,
                        kmax=10.0, nk=4000):
    """Q (3,Nc) = <S_n U_i> and cov_uu (3,3) = <U_i U_j> for a Gaussian window
    W_R = exp(-r^2/2R^2) of scale R_window (Mpc/h), closed form. Units (km/s)^2.

    Since x_n = r_n n_hat_n, Q_{i,n} = n_hat_{n,i} g(r_n),
        g(r) = hf2/(2 pi^2) int dk P(k) e^{-k^2 R^2/2} [j0(kr) - 2 j1(kr)/(kr)] dk,
        cov_uu = delta_ij hf2/(6 pi^2) int dk P(k) e^{-k^2 R^2}."""
    from scipy.special import spherical_jn
    r = np.asarray(r_hmpc, float)
    nh = np.asarray(n_hat, float)
    k = np.geomspace(kmin, kmax, nk)
    pkv = pk(k)
    win = np.exp(-0.5 * (k * R_window) ** 2)
    pref = hf2 / (2.0 * np.pi ** 2)
    g = np.empty_like(r)
    for i, ri in enumerate(r):
        x = k * ri
        j1_over_x = spherical_jn(1, x) / x
        g[i] = pref * _trapz(pkv * win * (spherical_jn(0, x) - 2.0 * j1_over_x), k)
    Q = (nh * g[:, None]).T                              # (3,Nc)
    cov_scalar = (hf2 / (6.0 * np.pi ** 2)) * _trapz(pkv * win ** 2, k)
    cov_uu = cov_scalar * np.eye(3)
    return Q, cov_uu


def mv_weights(R_total, Q, n_hat):
    """MV weights W (3,Nc): w_i = R^{-1}(Q_i + G lambda_i), G^T w_i = e_i."""
    G = np.asarray(n_hat, float)                         # (Nc,3)
    Rinv_Q = np.linalg.solve(R_total, np.asarray(Q, float).T)   # (Nc,3)
    Rinv_G = np.linalg.solve(R_total, G)                 # (Nc,3)
    GtRinvQ = G.T @ Rinv_Q                               # (3,3)
    GtRinvG = G.T @ Rinv_G                               # (3,3)
    lam = np.linalg.solve(GtRinvG, np.eye(3) - GtRinvQ)  # (3,3), col i = lambda_i
    W_cols = Rinv_Q + Rinv_G @ lam                       # (Nc,3), col i = w_i
    return W_cols.T                                      # (3,Nc)


def mv_bulk_flow(S, sigma2, R_v, Q, n_hat, R_window) -> MVBulkFlow:
    """MV bulk flow estimate + split cosmic/noise covariance."""
    S = np.asarray(S, float)
    sigma2 = np.asarray(sigma2, float)
    R_total = R_v + np.diag(sigma2)
    W = mv_weights(R_total, Q, n_hat)                    # (3,Nc)
    p = W @ S                                            # (3,)
    cov_cosmic = W @ R_v @ W.T
    cov_noise = (W * sigma2) @ W.T
    return MVBulkFlow(p, cov_cosmic, cov_noise, float(np.linalg.norm(p)),
                      float(R_window), int(S.shape[0]))
