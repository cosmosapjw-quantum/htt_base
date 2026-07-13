"""Peculiar velocity correlation function Psi_par(r) / Psi_perp(r) (REV-R196).

The physical, well-posed, RECONSTRUCTION-INDEPENDENT statistic (Gorski 1988; CF4
precedent arXiv:2604.08314): computed directly from pairs of observed line-of-
sight peculiar velocities, with NO 3-D field reconstruction. For a pair (m,n) at
positions x_m, x_n (unit LOS n_m, n_n), separation A = |x_m - x_n|, shat =
(x_m - x_n)/A, the linear velocity covariance is

    <u_m u_n> = Psi_par(A) f + Psi_perp(A) g,
    f = (n_m.shat)(n_n.shat),   g = (n_m.n_n) - f,

so binning pairs in A and least-squares-solving the 2x2 normal equations per bin
gives the estimators Psi_hat_par(r), Psi_hat_perp(r). The linear-theory
prediction Psi_par/Psi_perp scales as (f sigma_8)^2, so fitting the amplitude
yields f sigma_8 (a growth-rate constraint) -- reconstruction-free. The theory
curves come from `velocity_power.velocity_correlation_functions`.

Diagnostic-only kinematic descriptor; a growth-rate (f sigma_8) constraint, no
Bianchi family, geometry, or observer-frame claim.
"""
from __future__ import annotations

import numpy as np


def pair_correlation(pos_hmpc, n_hat, u, r_edges, *, w_gal=None,
                     chunk=4_000_000, min_pairs=50):
    """Psi_hat_par(r), Psi_hat_perp(r) from LOS-velocity pairs, binned in
    separation r_edges (Mpc/h). Returns (r_mid, psi_par, psi_perp, counts).

    w_gal: optional per-galaxy weight (e.g. inverse measurement error) applied
    as w_pair = w_gal[m] w_gal[n]; the noisy distant galaxies otherwise dominate
    the pair products. The sample bulk flow should be subtracted from u before
    the call (the coherent monopole biases the correlation high at large r)."""
    from scipy.spatial import cKDTree
    pos = np.asarray(pos_hmpc, float)
    nh = np.asarray(n_hat, float)
    u = np.asarray(u, float)
    wg = np.ones(len(u)) if w_gal is None else np.asarray(w_gal, float)
    rmax = float(r_edges[-1])
    rmin = float(r_edges[0])
    pairs = cKDTree(pos).query_pairs(rmax, output_type="ndarray")
    nbin = len(r_edges) - 1
    Sff = np.zeros(nbin); Sgg = np.zeros(nbin); Sfg = np.zeros(nbin)
    Sfu = np.zeros(nbin); Sgu = np.zeros(nbin); cnt = np.zeros(nbin)
    for s in range(0, len(pairs), chunk):
        pc = pairs[s:s + chunk]
        i, j = pc[:, 0], pc[:, 1]
        sv = pos[i] - pos[j]
        A = np.linalg.norm(sv, axis=1)
        sel = (A >= rmin) & (A < rmax)
        i, j, sv, A = i[sel], j[sel], sv[sel], A[sel]
        shat = sv / A[:, None]
        ni, nj = nh[i], nh[j]
        cos1 = np.einsum("pk,pk->p", ni, shat)
        cos2 = np.einsum("pk,pk->p", nj, shat)
        f = cos1 * cos2
        g = np.einsum("pk,pk->p", ni, nj) - f
        uu = u[i] * u[j]
        wp = wg[i] * wg[j]
        b = np.digitize(A, r_edges) - 1
        np.add.at(Sff, b, wp * f * f); np.add.at(Sgg, b, wp * g * g)
        np.add.at(Sfg, b, wp * f * g)
        np.add.at(Sfu, b, wp * f * uu); np.add.at(Sgu, b, wp * g * uu)
        np.add.at(cnt, b, 1.0)
    psi_par = np.full(nbin, np.nan); psi_perp = np.full(nbin, np.nan)
    for b in range(nbin):
        M = np.array([[Sff[b], Sfg[b]], [Sfg[b], Sgg[b]]])
        if cnt[b] >= min_pairs and np.linalg.det(M) > 0:
            psi_par[b], psi_perp[b] = np.linalg.solve(M, [Sfu[b], Sgu[b]])
    r_mid = 0.5 * (np.asarray(r_edges[:-1]) + np.asarray(r_edges[1:]))
    return r_mid, psi_par, psi_perp, cnt


def fit_amplitude(psi_data, psi_theory_fid):
    """Least-squares amplitude A of psi_data ~ A * psi_theory_fid (stacked
    Psi_par + Psi_perp bins). psi_data ~ (f sigma_8)^2 -> A = (fs8/fs8_fid)^2."""
    d = np.asarray(psi_data, float)
    t = np.asarray(psi_theory_fid, float)
    m = np.isfinite(d) & np.isfinite(t)
    if m.sum() < 2 or np.sum(t[m] ** 2) <= 0:
        return float("nan")
    return float(np.sum(d[m] * t[m]) / np.sum(t[m] ** 2))


def cosmic_mach_number(u, bulk_vec, n_hat):
    """M = |B| / sigma_1D, the sigma_8-/bias-/window-insensitive ratio of the
    bulk flow to the 1-D velocity dispersion about it."""
    u = np.asarray(u, float)
    resid = u - np.asarray(n_hat, float) @ np.asarray(bulk_vec, float)
    sigma_1d = float(np.sqrt(np.mean(resid ** 2)))
    return float(np.linalg.norm(bulk_vec) / sigma_1d), sigma_1d
