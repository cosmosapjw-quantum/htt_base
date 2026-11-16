"""R54-L02 PR4 bypass: analytic low-ell T covariance, a low-resolution E/B estimator and covariance tests.

No NPIPE simulation is used (PR4_BYPASS_CONTRACT.json). Functions:

  t_response_matrix      response of a masked, coupling-debiased low-ell T estimator to unit real harmonic modes
  analytic_covariance    C_th = R diag(C_ell b_ell^2) R^T  (+ a noise covariance)
  wishart_lrt            LRT of a model covariance against a sample covariance: n [tr M - ln det M - p], M = C^-1 S
  eb_operator            coupling inversion of a masked E/B estimator for 2 <= ell <= lmax at any NSIDE
  extract_eb             E/B 90-vector (ell = 2..6, real orthonormal packing) of masked Q/U maps
  posterior_zero_tail    tail of the zero vector among posterior samples (Mahalanobis about the sample mean)

The real packing of a_lm is the one of scripts/r49/run_r49_cmb_and_multiprobe_lanes.py: (ell, 0) -> Re a,
(ell, m > 0, r) -> sqrt2 Re a, (ell, m > 0, i) -> -sqrt2 Im a (orthonormal real basis).
"""
from __future__ import annotations

import math
from typing import Callable, Sequence

import healpy as hp
import numpy as np
from scipy import stats

SQ2 = math.sqrt(2.0)


def mode_tuples(lmax: int, lmin: int) -> list[tuple[int, int, str]]:
    out = []
    for ell in range(lmin, lmax + 1):
        out.append((ell, 0, "r"))
        for m in range(1, ell + 1):
            out += [(ell, m, "r"), (ell, m, "i")]
    return out


def pack(alm: np.ndarray, lmax_alm: int, modes: Sequence[tuple[int, int, str]]) -> np.ndarray:
    out = np.empty(len(modes))
    for k, (ell, m, tag) in enumerate(modes):
        c = alm[hp.Alm.getidx(lmax_alm, ell, m)]
        out[k] = float(np.real(c)) if m == 0 else (SQ2 * float(np.real(c)) if tag == "r" else -SQ2 * float(np.imag(c)))
    return out


def unit_alm(lmax_alm: int, ell: int, m: int, tag: str) -> np.ndarray:
    """Complex healpy a_lm of the unit real mode (ell, m, tag) of the orthonormal real basis."""
    a = np.zeros(hp.Alm.getsize(lmax_alm), dtype=np.complex128)
    if m == 0:
        a[hp.Alm.getidx(lmax_alm, ell, 0)] = 1.0
    else:
        a[hp.Alm.getidx(lmax_alm, ell, m)] = (1.0 / SQ2) if tag == "r" else (-1j / SQ2)
    return a


def t_response_matrix(mask: np.ndarray, nside: int, ell_cut: int, k_inv: np.ndarray, out_modes: Sequence[tuple[int, int, str]],
                      lmax_est: int = 6) -> tuple[np.ndarray, np.ndarray]:
    """R[:, j] = K^-1 pack(map2alm(mask * Y_j)) for the unit real modes j with 2 <= ell <= ell_cut (masked T estimator).

    ``mask`` is a RING map at ``nside``; ``k_inv`` maps the packed ell <= lmax_est coefficients (``out_modes``) of the
    masked map to the debiased estimate. Returns R and the ell of every column."""
    mask = np.asarray(mask, float)
    if mask.size != hp.nside2npix(nside):
        raise ValueError("mask does not match nside")
    modes = mode_tuples(ell_cut, 2)
    r = np.zeros((k_inv.shape[0], len(modes)))
    for j, (ell, m, tag) in enumerate(modes):
        t = hp.alm2map(unit_alm(ell_cut, ell, m, tag), nside, lmax=ell_cut)
        alm = hp.map2alm(t * mask, lmax=lmax_est, iter=0)
        r[:, j] = k_inv @ pack(alm, lmax_est, out_modes)
    return r, np.array([e for e, _, _ in modes])


def analytic_covariance(r: np.ndarray, ells: np.ndarray, cl: Callable[[np.ndarray], np.ndarray], noise: np.ndarray | None = None) -> np.ndarray:
    """C = R diag(C_ell(ell_j)) R^T (+ noise); ``cl`` returns the beam- and window-convolved power at the column ells."""
    w = np.asarray(cl(np.asarray(ells)), float)
    if w.shape != (r.shape[1],) or np.any(w < 0):
        raise ValueError("power must be non-negative with one value per column")
    c = (r * w[None, :]) @ r.T
    if noise is not None:
        c = c + np.asarray(noise, float)
    return 0.5 * (c + c.T)


def wishart_lrt(c_model: np.ndarray, s_sample: np.ndarray, n_dof: int) -> dict:
    """LRT for S ~ Wishart_p(n, C)/n against the model C: n [tr M - ln det M - p], M = C^-1 S, asymptotically chi2(p(p+1)/2)."""
    c_model, s_sample = np.asarray(c_model, float), np.asarray(s_sample, float)
    p = c_model.shape[0]
    m = np.linalg.solve(c_model, s_sample)
    sign, logdet = np.linalg.slogdet(m)
    if sign <= 0:
        raise ValueError("C^-1 S is not positive definite")
    stat = float(n_dof * (np.trace(m) - logdet - p))
    dof = p * (p + 1) // 2
    return {"law": f"wishart_lrt_asymptotic_chi2(dof={dof})", "statistic": stat, "dof": dof, "p_value": float(stats.chi2.sf(stat, dof)),
            "max_abs_diag_ratio_minus_1": float(np.max(np.abs(np.diag(s_sample) / np.diag(c_model) - 1.0))),
            "diag_ratio_sample_over_model": (np.diag(s_sample) / np.diag(c_model)).tolist()}


def eb_operator(mask_pol: np.ndarray, nside: int, lmax: int = 6) -> np.ndarray:
    """Inverse of the E/B coupling of a masked polarization map for 2 <= ell <= lmax (packed E then B)."""
    mask_pol = np.asarray(mask_pol, float)
    if mask_pol.size != hp.nside2npix(nside):
        raise ValueError("mask does not match nside")
    modes = mode_tuples(lmax, 2)
    n = len(modes)
    k = np.zeros((2 * n, 2 * n))
    zero_t = np.zeros(hp.nside2npix(nside))
    for pb in range(2):
        for j, (ell, m, tag) in enumerate(modes):
            a0 = np.zeros(hp.Alm.getsize(lmax), dtype=np.complex128)
            ae, ab = a0.copy(), a0.copy()
            (ae if pb == 0 else ab)[:] = unit_alm(lmax, ell, m, tag)
            _, q, u = hp.alm2map([a0, ae, ab], nside, lmax=lmax, pol=True)
            back = hp.map2alm([zero_t, q * mask_pol, u * mask_pol], lmax=lmax, pol=True, iter=0)
            k[:n, pb * n + j] = pack(back[1], lmax, modes)
            k[n:, pb * n + j] = pack(back[2], lmax, modes)
    cond = np.linalg.cond(k)
    if not np.isfinite(cond) or cond > 1e8:
        raise ValueError(f"E/B coupling is not invertible (condition {cond:.3g})")
    return np.linalg.inv(k)


def extract_eb(q: np.ndarray, u: np.ndarray, mask_pol: np.ndarray, k_inv: np.ndarray, lmax: int = 6) -> np.ndarray:
    """Debiased E/B coefficients (E rows then B rows, ell = 2..lmax) of RING Q/U maps under the mask used for k_inv."""
    mask_pol = np.asarray(mask_pol, float)
    alm = hp.map2alm([np.zeros_like(q), np.asarray(q) * mask_pol, np.asarray(u) * mask_pol], lmax=lmax, pol=True, iter=0)
    modes = mode_tuples(lmax, 2)
    return k_inv @ np.concatenate([pack(alm[1], lmax, modes), pack(alm[2], lmax, modes)])


def quadratic_form(x: np.ndarray, cov: np.ndarray) -> float:
    x = np.asarray(x, float)
    return float(x @ np.linalg.solve(np.asarray(cov, float), x))


def posterior_zero_tail(samples: np.ndarray) -> dict:
    """Fraction of posterior samples whose Mahalanobis distance from the sample mean is at least that of the zero vector.

    Invariant under any invertible linear change of coordinates (independent of the real-a_lm convention)."""
    s = np.asarray(samples, float)
    if s.ndim != 2 or s.shape[0] < 30:
        raise ValueError("need at least 30 posterior samples")
    mu, cov = s.mean(axis=0), np.cov(s.T, ddof=1)
    d0 = quadratic_form(mu, cov)
    ds = np.einsum("ij,ij->i", (s - mu) @ np.linalg.inv(cov), s - mu)
    k = int(np.sum(ds >= d0))
    return {"law": f"posterior sample ensemble (N={s.shape[0]}), Mahalanobis about the sample mean", "statistic": d0,
            "n_samples": int(s.shape[0]), "n_exceed": k, "p_value": (k + 1.0) / (s.shape[0] + 1.0)}
