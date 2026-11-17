"""Conditional covariance and calibration sensitivity of tensor carriers.

Uses the existing R58 fixed-Gaussian experiment; it does not infer a new
Bianchi transfer or calibrate a composite-null statistic by an invented law.
"""
from __future__ import annotations

import numpy as np
from scipy import linalg, optimize, stats

from common.covariance_amplitude import maximize_covariance_amplitude
from .r58_mixed_tensor_likelihood import fit_linear


def _spd(value, n, name):
    value = np.asarray(value, float)
    if value.shape != (n, n) or not np.isfinite(value).all():
        raise ValueError(f"{name} has invalid shape or nonfinite entries")
    scale = max(float(np.max(np.abs(value))), np.finfo(float).tiny)
    if np.max(np.abs(value - value.T)) > 1e-10 * scale:
        raise ValueError(f"{name} must be symmetric")
    value = 0.5 * (value + value.T)
    try:
        linalg.cholesky(value, lower=True)
    except linalg.LinAlgError as exc:
        raise ValueError(f"{name} must be positive definite") from exc
    return value


def calibration_distance(center, covariance, body_shape, radius):
    """Squared Mahalanobis distance to {b: b.T B^-1 b <= radius**2}.

    Returns a feasible calibration witness. For an 8-D marginal apparent
    dipole+STF estimate, compare distance with chi2_8(level): this is
    confidence-set inversion, not a chi-square law for the optimized distance.
    """
    h = np.asarray(center, float)
    if h.ndim != 1 or h.size == 0 or not np.isfinite(h).all():
        raise ValueError("center must be a nonempty finite vector")
    if not np.isfinite(radius) or radius < 0:
        raise ValueError("radius must be finite and nonnegative")
    c = _spd(covariance, h.size, "covariance")
    b = _spd(body_shape, h.size, "body_shape")
    lb = linalg.cholesky(b, lower=True)
    v = linalg.solve_triangular(lb, h, lower=True)
    vnorm = float(np.linalg.norm(v))
    if vnorm <= radius * (1.0 + 16.0 * np.finfo(float).eps):
        # The outer breakdown solve visits the exact body-boundary endpoint.
        # Two equivalent norm computations can straddle it by one ulp. Keep
        # the witness feasible instead of bracketing a nonexistent multiplier.
        fraction = min(1.0, radius / vnorm) if vnorm else 1.0
        witness = h * fraction
        residual = h - witness
        return dict(distance2=float(residual @ linalg.solve(c, residual, assume_a="pos")),
                    witness=witness, multiplier=0.0,
                    budget_used=vnorm * fraction, kkt_residual=0.0)
    if radius == 0:
        return dict(distance2=float(h @ linalg.solve(c, h, assume_a="pos")),
                    witness=np.zeros_like(h), multiplier=None,
                    budget_used=0.0, kkt_residual=0.0)
    a = lb.T @ linalg.solve(c, lb, assume_a="pos")
    eigen, u = linalg.eigh(0.5 * (a + a.T))
    eigen_scale = float(eigen.max())
    eigen = eigen / eigen_scale
    nu = u.T @ v
    def coords(t):
        return (eigen / (eigen + t)) * nu
    def norm_excess(t):
        return float(np.linalg.norm(coords(t)) - radius)
    upper = max(1.0, float(np.linalg.norm(nu)) / radius)
    t = optimize.brentq(norm_excess, 0.0, upper,
                       xtol=np.nextafter(0.0, 1.0), rtol=1e-13, maxiter=256)
    x = coords(t)
    if abs(float(np.linalg.norm(x)) - radius) > 1e-9 * radius:
        raise ValueError("calibration multiplier did not resolve the active budget boundary")
    witness = lb @ (u @ x)
    residual = h - witness
    distance2 = float(residual @ linalg.solve(c, residual, assume_a="pos"))
    kkt = float(np.linalg.norm(eigen * (x - nu) + t * x))
    return dict(distance2=distance2, witness=witness, multiplier=t * eigen_scale,
                budget_used=float(np.linalg.norm(x)), kkt_residual=kkt)


def calibration_breakdown(center, covariance, body_shape, *, level=0.95):
    """Smallest deterministic budget for the confidence ellipsoid to meet 0.

    This is the existing gauge-minimum construction applied to measured
    tensor coefficients. The ellipsoid dimension is the target dimension;
    nuisance mean coordinates have already been profiled (marginal covariance).
    """
    h = np.asarray(center, float)
    if h.ndim != 1 or h.size == 0 or not np.isfinite(h).all():
        raise ValueError("center must be a finite vector")
    if not np.isfinite(level) or not 0 < level < 1:
        raise ValueError("level must lie in (0,1)")
    c = _spd(covariance, h.size, "covariance")
    b = _spd(body_shape, h.size, "body_shape")
    threshold = float(stats.chi2.ppf(level, h.size))
    zero = calibration_distance(h, c, b, 0.0)
    if zero["distance2"] <= threshold:
        return dict(radius=0.0, threshold=threshold, dof=h.size,
                    level=level, witness=zero["witness"], distance2=zero["distance2"],
                    interpretation="zero belongs to the confidence ellipsoid with no calibration shift")
    upper = float(np.sqrt(h @ linalg.solve(b, h, assume_a="pos")))
    root = optimize.brentq(lambda r: calibration_distance(h, c, b, r)["distance2"] - threshold,
                           0.0, upper, xtol=1e-13, rtol=1e-12)
    out = calibration_distance(h, c, b, root)
    return dict(radius=float(root), threshold=threshold, dof=h.size, level=level,
                witness=out["witness"], distance2=out["distance2"],
                interpretation="minimum full-sky RMS calibration for confidence-set intersection")


def calibrated_support(center, covariance, body_shape, contrast, radius, *, level=0.95):
    """Exact support of E(level) Minkowski-summed with a calibration ellipsoid."""
    h, u = np.asarray(center, float), np.asarray(contrast, float)
    if h.ndim != 1 or h.shape != u.shape or not np.isfinite(h).all() or not np.isfinite(u).all():
        raise ValueError("center and contrast must be finite matching vectors")
    if not np.isfinite(radius) or radius < 0 or not np.isfinite(level) or not 0 < level < 1:
        raise ValueError("invalid radius or confidence level")
    c, b = _spd(covariance, h.size, "covariance"), _spd(body_shape, h.size, "body_shape")
    statistical = float(np.sqrt(stats.chi2.ppf(level, h.size) * (u @ c @ u)))
    systematic = float(radius * np.sqrt(u @ b @ u))
    point = float(u @ h)
    return dict(lower=point-statistical-systematic, upper=point+statistical+systematic,
                center=point, statistical_radius=statistical, calibration_radius=systematic,
                semantics="support interval of one simultaneous confidence set; not occupancy")


def linear_budget_distance(center, covariance, nuisance_map, radius):
    """Distance to {H v: ||v||<=radius}, including rank-deficient image bodies.

    This is confidence-set geometry for a deterministic nuisance budget, not
    a calibrated composite-null p-value. Coordinates of v must have one stated
    common unit; here the consumer uses km/s for a velocity-slope vector.
    An unresolved nonzero singular mode is rejected rather than silently
    discarded: even a small response can matter at a finite nuisance budget.
    """
    h, H = np.asarray(center, float), np.asarray(nuisance_map, float)
    if (h.ndim != 1 or H.ndim != 2 or H.shape[0] != h.size or H.shape[1] == 0
            or not np.isfinite(h).all() or not np.isfinite(H).all()
            or not np.isfinite(radius) or radius < 0):
        raise ValueError("invalid center, nuisance map or radius")
    c = _spd(covariance, h.size, "covariance")
    lc = linalg.cholesky(c, lower=True)
    yw = linalg.solve_triangular(lc, h, lower=True)
    Hw = linalg.solve_triangular(lc, H, lower=True)
    u, s, vt = linalg.svd(Hw, full_matrices=False)
    keep = s > 1e-12 * s[0] if s.size and s[0] else np.zeros(s.size, bool)
    if radius > 0 and np.any((s > 0) & ~keep):
        raise ValueError("numerically unresolved nonzero nuisance mode; rescale or supply a resolved response before confidence inversion")
    if not np.any(keep) or radius == 0:
        v = np.zeros(H.shape[1])
    else:
        s, u, vt = s[keep], u[:, keep], vt[keep]
        nu = (u.T @ yw) / s
        norm = float(np.linalg.norm(nu))
        if norm <= radius * (1.0 + 16.0 * np.finfo(float).eps):
            v = vt.T @ (nu * min(1.0, radius / norm) if norm else nu)
        else:
            d = (s / s.max()) ** 2
            def coords(t): return d / (d+t) * nu
            t = optimize.brentq(lambda t: float(np.linalg.norm(coords(t))-radius),
                                0.0, max(1.0, norm/radius),
                                xtol=np.nextafter(0.0, 1.0), rtol=1e-13, maxiter=256)
            v = vt.T @ coords(t)
            if abs(float(np.linalg.norm(v)) - radius) > 1e-9 * radius:
                raise ValueError("nuisance multiplier did not resolve the active budget boundary")
    residual = yw - Hw @ v
    return dict(distance2=float(residual @ residual), nuisance_witness=v,
                image_witness=H @ v, budget_used=float(np.linalg.norm(v)),
                image_rank=int(np.count_nonzero(keep)))


def fixed_mean_amplitude(y, noise, signal, *, a_cap=1.0e5, loglike_tol=1e-7):
    """Amplitude likelihood for a fixed zero mean or fixed mean-free contrasts."""
    y = np.asarray(y, float)
    if y.ndim != 1 or y.size == 0 or not np.isfinite(y).all():
        raise ValueError("y must be a nonempty finite vector")
    n = _spd(noise, y.size, "noise")
    s = np.asarray(signal, float)
    if s.shape != n.shape or not np.isfinite(s).all():
        raise ValueError("signal has invalid shape or entries")
    scale = max(float(np.max(np.abs(s))), np.finfo(float).tiny)
    if np.max(np.abs(s - s.T)) > 1e-10 * scale:
        raise ValueError("signal must be symmetric positive semidefinite")
    s = 0.5 * (s + s.T)
    ln = linalg.cholesky(n, lower=True)
    sw = linalg.solve_triangular(ln, s, lower=True)
    sw = linalg.solve_triangular(ln, sw.T, lower=True).T
    lam, v = linalg.eigh(0.5 * (sw + sw.T))
    tol = 1e-11 * max(float(np.max(np.abs(lam))), np.finfo(float).tiny)
    if lam.min() < -tol:
        raise ValueError("signal is not positive semidefinite")
    lam = np.maximum(lam, 0.0)
    yw = linalg.solve_triangular(ln, y, lower=True)
    p2 = (v.T @ yw) ** 2
    result = maximize_covariance_amplitude(p2, lam, a_cap=a_cap, loglike_tol=loglike_tol)
    def gain(a):
        den = 1.0 + a * lam
        return float(0.5 * np.sum(p2 * (a * lam / den) - np.log1p(a * lam)))
    result.update(n_contrasts=y.size, loglike_gain_at_one=gain(1.0),
                  twice_gain_over_one=2.0 * (result["loglike_gain"]-gain(1.0)),
                  variance_is_confidence_interval=False,
                  interpretation="conditional covariance fit; fitted-amplitude chi-square tails are not calibrated")
    return result


def residual_contrast_amplitude(y, noise, signal, design, *, loglike_tol=1e-7):
    """Fit amplitude in an amplitude-independent orthonormal mean annihilator.

    This is a restricted/contrast likelihood. It is not the normalized
    profile-mean likelihood and is not compared across differing data operators.
    """
    y, x = np.asarray(y, float), np.asarray(design, float)
    if x.ndim != 2 or y.shape != (x.shape[0],) or not np.isfinite(x).all():
        raise ValueError("invalid design or y")
    norms = np.linalg.norm(x, axis=0)
    if np.any(norms == 0):
        raise ValueError("contrast design must have nonzero independent columns")
    q, r = linalg.qr(x / norms, mode="full")
    p = x.shape[1]
    if x.shape[0] <= p or np.min(np.abs(np.diag(r[:p, :]))) <= 1e-12:
        raise ValueError("need full column rank with residual degrees of freedom")
    z = q[:, p:]
    result = fixed_mean_amplitude(z.T @ y, z.T @ np.asarray(noise) @ z,
                                  z.T @ np.asarray(signal) @ z, loglike_tol=loglike_tol)
    result.update(kind="fixed orthonormal residual-contrast likelihood (REML)",
                  annihilation_error=float(np.max(np.abs(z.T @ (x / norms)))),
                  n_mean_parameters=p)
    return result


def block_wald(fit, indices):
    """Fixed-covariance Wald test, with every other mean parameter profiled."""
    indices = np.asarray(indices, int)
    if indices.ndim != 1 or indices.size == 0 or len(np.unique(indices)) != indices.size:
        raise ValueError("indices must be nonempty and unique")
    if np.any(indices < 0) or np.any(indices >= len(fit["estimate"])) or fit["rank"] != fit["n_parameters"]:
        raise ValueError("need valid indices and an identified mean model")
    h = fit["estimate"][indices]
    c = fit["covariance"][np.ix_(indices, indices)]
    w = float(h @ linalg.solve(c, h, assume_a="pos"))
    return dict(wald=w, dof=len(indices), p=float(stats.chi2.sf(w, len(indices))))
