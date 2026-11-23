"""Conditional Gaussian tomography and finite shared-field selected mark responses."""
from dataclasses import dataclass

import numpy as np
from scipy.linalg import cho_factor, cho_solve, qr, solve_triangular
from scipy.special import erfcx, log_ndtr, logsumexp

_LOG_2PI = np.log(2 * np.pi)


@dataclass(frozen=True)
class PredictiveContrasts:
    """Rows act on the concatenation of the training and predicted coordinates."""
    train: np.ndarray
    predicted: np.ndarray


def predictive_contrasts(train_design, test_design):
    """Precompute universal-kriging error contrasts for a fixed full-rank design.

    One flat common coefficient per column, also allowing zero coefficients.
    These dense operators are intended for compressed summaries, not raw galaxies.
    """
    x = np.asarray(train_design, dtype=float)
    h = np.asarray(test_design, dtype=float)
    if x.ndim != 2 or h.ndim != 2 or h.shape[1] != x.shape[1]:
        raise ValueError("training and test designs need the same number of columns")
    n, p = x.shape
    m = len(h)
    if not n or not m or p > n or not np.isfinite(x).all() or not np.isfinite(h).all():
        raise ValueError("nonempty finite designs with identifiable training coefficients required")
    if p:
        scales = np.linalg.norm(x, axis=0)
        if np.any(scales == 0):
            raise ValueError("training design is rank deficient")
        xs = x / scales
        if np.linalg.matrix_rank(xs) != p:
            raise ValueError("training design is rank deficient")
        q, r = qr(xs, mode="full")
        common = solve_triangular(r[:p].T, (h / scales).T, lower=True).T @ q[:, :p].T
        z = q[:, p:].T
    else:
        z, common = np.eye(n), np.zeros((m, n))
    return PredictiveContrasts(np.column_stack((z, np.zeros((n-p, m)))),
                               np.column_stack((-common, np.eye(m))))


def _symmetric(value, n, name):
    a = np.asarray(value, dtype=float)
    if a.shape != (n, n) or not np.isfinite(a).all():
        raise ValueError(f"{name} must be a finite square matrix matching the data")
    scale = np.max(np.abs(a))
    if np.max(np.abs(a - a.T)) > 1e-11 * scale:
        raise ValueError(f"{name} must be symmetric")
    return (a + a.T) / 2


def predictive_covariance_response(y, covariance, covariance_tangent, contrasts):
    """Conditional prediction and first derivative along C(alpha), at fixed y, X.

    The flat nuisance measure is eliminated by training-only error contrasts.
    Both the predictive mean and variance move with the supplied covariance.
    """
    y = np.asarray(y, dtype=float)
    t, w = contrasts.train, contrasts.predicted
    if y.ndim != 1 or not np.isfinite(y).all() or t.shape[1] != len(y) or w.shape[1] != len(y):
        raise ValueError("ordered finite training and test coordinates required")
    c = _symmetric(covariance, len(y), "covariance")
    dc = _symmetric(covariance_tangent, len(y), "covariance tangent")
    # Validate the declared full covariance, including directions removed by the fit.
    cho_factor(c, lower=True, check_finite=False)
    nt = len(y) - len(w)
    if len(t):
        train_cov = t @ c @ t.T
        chol_t = cho_factor(train_cov, lower=True, check_finite=False)
        reg = cho_solve(chol_t, t @ c @ w.T, check_finite=False).T
        innovation = w - reg @ t
        train_score = cho_solve(chol_t, t @ y, check_finite=False)
        dmean = innovation @ dc @ t.T @ train_score
    else:
        innovation = w
        dmean = np.zeros(len(w))
    # Only training marks enter the predicted mean, even for a very large test residual.
    mean = -innovation[:, :nt] @ y[:nt]
    residual = y[nt:] - mean
    s = innovation @ c @ innovation.T
    ds = innovation @ dc @ innovation.T
    s = (s + s.T) / 2
    ds = (ds + ds.T) / 2
    chol_s = cho_factor(s, lower=True, check_finite=False)
    v = cho_solve(chol_s, residual, check_finite=False)
    chi2 = float(residual @ v)
    mean_term = float(-2 * dmean @ v)
    variance_term = float(-v @ ds @ v)
    dchi2 = mean_term + variance_term
    dlogdet = float(np.trace(cho_solve(chol_s, ds, check_finite=False)))
    logdet = 2 * np.log(chol_s[0].diagonal()).sum()
    return dict(mean=mean, covariance=s, mean_tangent=dmean, covariance_tangent=ds,
                chi2=chi2, log_density=float(-0.5 * (chi2 + logdet + len(w) * _LOG_2PI)),
                chi2_tangent=dchi2, chi2_mean_term=mean_term,
                chi2_covariance_term=variance_term, logdet_tangent=dlogdet,
                log_density_tangent=-0.5 * (dchi2 + dlogdet))


def _inverse_mills(t):
    mills = np.empty_like(t)
    neg = t < 0
    mills[neg] = np.sqrt(2/np.pi) / erfcx(-t[neg] / np.sqrt(2))
    mills[~neg] = np.exp(-0.5 * (t[~neg]**2 + _LOG_2PI) - log_ndtr(t[~neg]))
    return mills


def selected_probit_field_response(mark, field_means, sigma, intercept, slope, probabilities,
                                   *, included=None, mean_tangent=None):
    """Gaussian marks under one common field, conditional on the observed inclusion pattern.

    Positive rows use their marks in the density. Negative rows contribute their
    integrated noninclusion probability to both sums; their marks may be NaN.
    The default conditions on all objects being included. Tangent varies means only.
    """
    y = np.asarray(mark, dtype=float)
    means = np.asarray(field_means, dtype=float)
    p = np.asarray(probabilities, dtype=float)
    if y.ndim != 1 or y.size == 0 or means.ndim != 2 or means.shape[1] != len(y):
        raise ValueError("nonempty mark vector and field-by-object means required")
    kept = np.ones(len(y), dtype=bool) if included is None else np.asarray(included)
    if kept.dtype != bool or kept.shape != y.shape:
        raise ValueError("one boolean inclusion indicator per target required")
    if p.shape != (len(means),) or np.any(p <= 0) or not np.isclose(p.sum(), 1, rtol=0, atol=1e-12):
        raise ValueError("strictly positive normalized shared-field probabilities required")
    sig, a, b = [np.broadcast_to(np.asarray(q, dtype=float), y.shape)
                 for q in (sigma, intercept, slope)]
    if np.any(sig <= 0) or not all(np.isfinite(x).all() for x in (y[kept], means, a, b, sig, p)):
        raise ValueError("finite selected marks, means, coefficients and strictly positive widths required")
    den_scale = np.hypot(1, b * sig)
    t = (a + b * means) / den_scale
    negative = ~kept
    base = np.log(p) + log_ndtr(-t[:, negative]).sum(axis=1)
    residual = (y[kept] - means[:, kept]) / sig[kept]
    log_num = (base - 0.5 * np.sum(residual**2, axis=1)
               - np.log(sig[kept]).sum() - 0.5 * kept.sum() * _LOG_2PI
               + log_ndtr(a[kept] + b[kept] * y[kept]).sum())
    log_den = base + log_ndtr(t[:, kept]).sum(axis=1)
    ln, ld = logsumexp(log_num), logsumexp(log_den)
    post, incl = np.exp(log_num - ln), np.exp(log_den - ld)
    result = dict(log_density=float(ln - ld), log_inclusion_pattern=float(ld),
                  observed_field_weights=post, included_field_weights=incl)
    all_kept = bool(kept.all())
    if all_kept:
        result["log_joint_inclusion"] = float(ld)
    if mean_tangent is not None:
        dm = np.asarray(mean_tangent, dtype=float)
        if dm.shape != means.shape or not np.isfinite(dm).all():
            raise ValueError("finite field-by-object mean tangent required")
        dt = (b / den_scale) * dm
        missed_score = -(_inverse_mills(-t[:, negative]) * dt[:, negative]).sum(axis=1)
        num_score = float(post @ (missed_score + (residual * (dm[:, kept]/sig[kept])).sum(axis=1)))
        denom = missed_score + (_inverse_mills(t[:, kept]) * dt[:, kept]).sum(axis=1)
        den_score = float(incl @ denom)
        result.update(log_density_tangent=num_score - den_score, log_inclusion_pattern_tangent=den_score)
        if all_kept:
            result["log_joint_inclusion_tangent"] = den_score
    return result
