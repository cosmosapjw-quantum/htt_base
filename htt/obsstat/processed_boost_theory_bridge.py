"""Declared band-limited thermodynamic CMB boost response under a fixed map fit.

Owns ONLY observable response algebra. No inferred velocity, posterior, p-value,
physical E2E fidelity, native Bianchi transfer or independent Planck detection.
Directions point outward; metric (-,+,+,+); beta=v/c dimensionless.
"""
from __future__ import annotations

import numpy as np
from scipy.special import sph_harm_y


class ProcessedBoostBridgeError(ValueError):
    """Invalid sky or unsupported exact finite-matrix contract."""


def real_harmonics_with_gradients(directions: object, *, lmax: int):
    """Return orthonormal-real Y, d_theta Y, (1/sin(theta))d_phi Y.

    Layout: ell0 m0; then for each m>0 sqrt(2)*Re(Y_lm),
    sqrt(2)*Im(Y_lm), matching obsstat.r7_cmb_product_response.
    Coordinate singular poles are intentionally rejected, never silently
    regularised. HEALPix pixel centres avoid these poles.
    """
    n = np.asarray(directions, dtype=float)
    if (n.ndim != 2 or n.shape[1] != 3 or not np.isfinite(n).all()
        or not np.allclose(np.linalg.norm(n, axis=1), 1, rtol=0, atol=5e-13)):
        raise ProcessedBoostBridgeError("finite unit sky directions required")
    if not isinstance(lmax, int) or not (0 <= lmax <= 16):
        raise ProcessedBoostBridgeError("registered finite source lmax in [0,16]")
    rho = np.hypot(n[:, 0], n[:, 1])
    if np.min(rho) < 1e-8:
        raise ProcessedBoostBridgeError("a polar chart is needed for pole directions")
    th = np.arccos(np.clip(n[:, 2], -1, 1))
    ph = np.arctan2(n[:, 1], n[:, 0])
    vals, dtheta, dphi_sin = [], [], []
    for ell in range(lmax + 1):
        modes = [(0, 1., "real")]
        for m in range(1, ell + 1):
            modes.extend(((m, np.sqrt(2.), "real"),
                          (m, np.sqrt(2.), "imag")))
        computed = {}
        for m, scale, kind in modes:
            if m not in computed:
                computed[m] = sph_harm_y(ell, m, th, ph, diff_n=1)
            y, derivatives = computed[m]
            component = np.real if kind == "real" else np.imag
            vals.append(scale * component(y))
            dtheta.append(scale * component(derivatives[:, 0]))
            dphi_sin.append(scale * component(derivatives[:, 1]) / rho)
    return (np.column_stack(vals), np.column_stack(dtheta),
            np.column_stack(dphi_sin))


def first_order_sky_generator(directions: object, harmonic_packet, coefficients: object):
    """Return pixel response d(Ttilde)/d(beta_x,y,z) in source temperature units.

    Full thermodynamic first order: n*T - e_theta*partial_theta(T)
    - e_phi*(partial_phi(T)/sin(theta)). No monopole is silently inferred.
    """
    n = np.asarray(directions, dtype=float)
    y, dt, dp = harmonic_packet
    a = np.asarray(coefficients, dtype=float)
    if (a.shape != (y.shape[1],) or y.shape != dt.shape or y.shape != dp.shape
        or n.shape != (y.shape[0], 3) or
        not np.isfinite(a).all()):
        raise ProcessedBoostBridgeError("basis/coefficient identity mismatch")
    sky = y @ a
    ttheta = dt @ a
    tphi = dp @ a
    phi = np.arctan2(n[:, 1], n[:, 0])
    cp, sp, ct, st = np.cos(phi), np.sin(phi), n[:, 2], np.hypot(n[:, 0], n[:, 1])
    eth = np.stack([ct * cp, ct * sp, -st], axis=1)
    eph = np.stack([-sp, cp, np.zeros_like(sp)], axis=1)
    return n * sky[:, None] - eth * ttheta[:, None] - eph * tphi[:, None]


def processed_boost_jacobian(pixel_generator: object, selected: object, operator: object):
    """Return the 32x3 processed Jacobian from an exact frozen 0..5 fit operator."""
    g = np.asarray(pixel_generator, dtype=float)
    mask = np.asarray(selected, dtype=bool)
    p = np.asarray(operator, dtype=float)
    if (g.ndim != 2 or g.shape[1] != 3 or mask.shape != (len(g),)
        or p.shape != (36, int(mask.sum()))
        or not np.isfinite(g[mask]).all() or not np.isfinite(p).all()):
        raise ProcessedBoostBridgeError("frozen selected/OLS operator mismatch")
    return p[4:36] @ g[mask]


def fisher_with_high_mode_stress(jacobian, sampling_covariance, high_mode_response,
                                 high_mode_sigma_microk: float):
    """F=J^T (C+sigma_high^2 K K^T)^(-1) J (conditional Gaussian stress).

    C is ALREADY the sampling covariance of the delivered null; sigma_high is
    an *additional* hypothetical omitted component, not automatically additive
    physical sky variance. Returns exact finite-dimensional conditional math.
    """
    j = np.asarray(jacobian, dtype=float)
    c = np.asarray(sampling_covariance, dtype=float)
    k = np.asarray(high_mode_response, dtype=float)
    v = float(high_mode_sigma_microk)
    if (j.shape != (32, 3) or c.shape != (32, 32) or k.ndim != 2
        or k.shape[0] != 32 or not np.isfinite(j).all()
        or not np.isfinite(c).all() or not np.isfinite(k).all()
        or not np.isfinite(v) or v < 0):
        raise ProcessedBoostBridgeError("invalid conditional Fisher inputs")
    if np.max(np.abs(c-c.T)) > 1e-9:
        raise ProcessedBoostBridgeError("sampling covariance is not symmetric")
    covariance = (c+c.T)/2 + v*v*(k@k.T)
    evals = np.linalg.eigvalsh(covariance)
    if evals[0] <= 0 or evals[-1]/evals[0] > 1e12:
        raise ProcessedBoostBridgeError("singular or numerically unsupported covariance")
    info = j.T @ np.linalg.solve(covariance, j)
    return (info + info.T)/2
