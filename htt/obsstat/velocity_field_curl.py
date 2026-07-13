"""CF4++ WF velocity-field vorticity + constrained-realization distribution (REV-R198).

K6 tests whether the CF4 peculiar-velocity field carries VORTICITY (curl), i.e.
non-potential flow, which the Wiener-filter (WF) reconstruction suppresses by its
potential-flow prior. The rev-r127 no-go was established abstractly; this module
quantifies it on the REAL CF4++ 3-D WF field (v_mean) and builds a
constrained-realization (CR) vorticity distribution from a CORRELATED residual field
scaled to the per-cell WF std (v_std) -- an upgrade over the toy
per-cell-independent draws (which give spurious curl, since curl = a derivative).

    curl v = nabla x v ,   div v = nabla . v   (central differences, (km/s)/Mpc)
    v_CR   = v_mean + residual ,
    residual = smoothed white noise (correlation length R) scaled per cell to
               v_std -> a stationary GRF with the WF std amplitude.

The residual correlation length R is NOT determined by (v_mean, v_std) alone (the
true Hoffman-Ribak CR needs the full WF residual covariance / operator), so the
CR vorticity distribution is reported as a function of R (a sensitivity). The
mean-field curl/div ratio IS a real measurement of the potential-flow suppression.

Diagnostic-only kinematic descriptor; no Bianchi family, geometry, or
observer-frame claim.
"""
from __future__ import annotations

import numpy as np


def curl(v, cell):
    """nabla x v for v (3,n,n,n), central differences; returns (3,n,n,n)."""
    wx = np.gradient(v[2], cell, axis=1) - np.gradient(v[1], cell, axis=2)
    wy = np.gradient(v[0], cell, axis=2) - np.gradient(v[2], cell, axis=0)
    wz = np.gradient(v[1], cell, axis=0) - np.gradient(v[0], cell, axis=1)
    return np.array([wx, wy, wz])


def divergence(v, cell):
    """nabla . v for v (3,n,n,n)."""
    return (np.gradient(v[0], cell, axis=0) + np.gradient(v[1], cell, axis=1)
            + np.gradient(v[2], cell, axis=2))


def rms_over(field_sq, mask):
    return float(np.sqrt(np.mean(field_sq[mask])))


def correlated_residual(v_std, cell, R_smooth_mpc, rng):
    """A stationary GRF residual (correlation length R_smooth) scaled per cell to
    the WF std v_std (3,n,n,n)."""
    from scipy.ndimage import gaussian_filter
    sig_pix = R_smooth_mpc / cell
    res = np.empty_like(v_std)
    for c in range(3):
        wn = gaussian_filter(rng.standard_normal(v_std.shape[1:]), sig_pix,
                             mode="nearest")
        s = wn.std()
        res[c] = (wn / s if s > 0 else wn) * v_std[c]
    return res


def cr_vorticity_ensemble(v_mean, v_std, cell, mask, R_smooth_mpc, n_cr, seed):
    """CR ensemble RMS|curl| over the mask for a given residual correlation
    length. Returns (mean, std) of the ensemble RMS|curl| (km/s per Mpc)."""
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_cr):
        v_cr = v_mean + correlated_residual(v_std, cell, R_smooth_mpc, rng)
        w2 = np.sum(curl(v_cr, cell) ** 2, axis=0)
        vals.append(rms_over(w2, mask))
    vals = np.array(vals)
    return float(vals.mean()), float(vals.std(ddof=1) if len(vals) > 1 else 0.0)
