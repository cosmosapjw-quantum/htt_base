"""Global numerical maximization of a one-parameter covariance likelihood.

For fixed mean, N positive definite, and S positive semidefinite, whitening
reduces C(a)=N+a*S to independent variances 1+a*lam. No monotonic-score
assumption is made. The reported objective gap is a floating-point branch
bound, not a formal interval-arithmetic certificate or a confidence interval.
"""
from __future__ import annotations

import heapq
import math

import numpy as np
from scipy.optimize import minimize_scalar


def maximize_covariance_amplitude(p2, lam, *, a_cap=1.0e5,
                                  loglike_tol=1.0e-8, max_intervals=200000):
    """Return the best amplitude on [0,a_cap] with a numerical global gap.

    p2 contains squared rotated whitened residuals; lam are the eigenvalues
    of N^(-1/2) S N^(-1/2). The mean must be fixed independently of a, or be
    removed by an a-independent contrast matrix (a restricted likelihood).
    This bound must not be applied to an ordinary profiled-mean likelihood.

    Each summand f_i(a)=.5*[p2_i*a*lam_i/(1+a*lam_i)-log1p(a*lam_i)]
    increases up to a_i=max(0,(p2_i-1)/lam_i), then decreases. Therefore
    sum_i max_{a in I} f_i(a) bounds the total likelihood on every interval I.
    A second, midpoint Taylor bound preserves score cancellation and avoids
    slow linear convergence of the separable bound near a many-mode maximum.
    The score of the SUM need not be monotone and can have multiple roots.
    """
    p2, lam = np.asarray(p2, float), np.asarray(lam, float)
    if (p2.ndim != 1 or p2.shape != lam.shape or p2.size == 0
            or not np.isfinite(p2).all() or not np.isfinite(lam).all()
            or np.any(p2 < 0) or np.any(lam < 0)):
        raise ValueError("p2 and lam must be nonempty finite nonnegative vectors of equal length")
    if not np.isfinite(a_cap) or a_cap <= 0:
        raise ValueError("a_cap must be positive and finite")
    if not np.isfinite(loglike_tol) or loglike_tol <= 0:
        raise ValueError("loglike_tol must be positive and finite")
    if isinstance(max_intervals, bool) or int(max_intervals) != max_intervals or max_intervals < 1:
        raise ValueError("max_intervals must be a positive integer")
    active = lam > 0
    p2, lam = p2[active], lam[active]
    if not lam.size:
        return dict(amplitude=0.0, fisher_variance=math.inf, loglike_gain=0.0,
                    objective_gap=0.0, evaluations=0, intervals=0,
                    search_upper=0.0, at_cap=False, identified=False,
                    status="FLAT_COVARIANCE_RESPONSE")
    with np.errstate(over="ignore"):
        peaks = np.maximum(0.0, (p2 - 1.0) / lam)
    upper = min(float(a_cap), float(np.max(peaks)))
    peaks = np.minimum(peaks, float(a_cap))
    log_lam = np.log(lam)
    evaluations = 0

    def terms(a):
        av = np.asarray(a, float)
        with np.errstate(divide="ignore"):
            logden = np.logaddexp(0.0, np.log(av) + log_lam)
        return 0.5 * (p2 * (-np.expm1(-logden)) - logden)

    def objective(a):
        nonlocal evaluations
        evaluations += 1
        return math.fsum(terms(float(a)).tolist())

    def upper_bound(lo, hi):
        vals = terms(np.clip(peaks, lo, hi))
        value = math.fsum(vals.tolist())
        # Summation guard; this remains a numerical, not directed-rounding,
        # bound. Requested tolerances smaller than roundoff fail explicitly.
        pad = 64.0 * np.finfo(float).eps * (1.0 + math.fsum(np.abs(vals).tolist()))
        separable = float(np.nextafter(value + pad, math.inf))
        mid, radius = lo + 0.5 * (hi - lo), 0.5 * (hi - lo)
        vals_mid = terms(mid)
        fmid = math.fsum(vals_mid.tolist())
        # On I, |sum f_i''| <= .5 sum r_i(lo)^2*(1+2*p2_i*u_i(lo)),
        # where u=1/(1+a*lam), r=lam*u. This follows by differentiating
        # each summand twice; it does not assume a monotone total score.
        # Extreme ill-scaled inputs may overflow this optional bound. The
        # finite separable bound remains available in that case.
        with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
            logden_mid = np.logaddexp(0.0, np.log(mid) + log_lam)
            logden_lo = np.logaddexp(0.0, np.log(lo) + log_lam)
            u_mid, u_lo = np.exp(-logden_mid), np.exp(-logden_lo)
            r_mid, r_lo = np.exp(log_lam - logden_mid), np.exp(log_lam - logden_lo)
            score_terms = 0.5 * r_mid * (p2 * u_mid - 1.0)
            curvature_terms = 0.5 * r_lo**2 * (1.0 + 2.0 * p2 * u_lo)
        if (np.isfinite(score_terms).all() and np.isfinite(curvature_terms).all()):
            score = math.fsum(score_terms.tolist())
            curvature = math.fsum(curvature_terms.tolist())
            with np.errstate(over="ignore", invalid="ignore"):
                delta = abs(score) * radius + 0.5 * curvature * radius * radius
                guard_scale = (1.0 + math.fsum(np.abs(vals_mid).tolist())
                               + radius * math.fsum(np.abs(score_terms).tolist())
                               + delta)
            if math.isfinite(delta) and math.isfinite(guard_scale):
                taylor = float(np.nextafter(fmid + delta +
                               128.0 * np.finfo(float).eps * guard_scale, math.inf))
                return min(separable, taylor)
        return separable

    best_a, best = 0.0, 0.0
    if upper > 0:
        for a in (upper, float(np.median(peaks)), math.expm1(0.5 * math.log1p(upper))):
            a = min(max(float(a), 0.0), upper)
            value = objective(a)
            if value > best:
                best_a, best = a, value
        # This bounded local solver only provides a candidate lower bound;
        # the branch bound, not assumed unimodality, determines termination.
        opt = minimize_scalar(lambda t: -objective(math.expm1(t)),
                              bounds=(0.0, math.log1p(upper)), method="bounded",
                              options={"xatol": 1e-12})
        if opt.success and -float(opt.fun) > best:
            best_a, best = math.expm1(float(opt.x)), -float(opt.fun)
    heap = [(-upper_bound(0.0, upper), 0.0, upper)]
    splits = 0
    while -heap[0][0] - best > loglike_tol:
        if splits >= max_intervals:
            raise RuntimeError("covariance-amplitude global objective gap unresolved at max_intervals")
        _, lo, hi = heapq.heappop(heap)
        mid = math.expm1(0.5 * (math.log1p(lo) + math.log1p(hi)))
        if not lo < mid < hi:
            mid = lo + 0.5 * (hi - lo)
        if not lo < mid < hi:
            raise RuntimeError("floating-point interval resolution cannot meet loglike_tol")
        value = objective(mid)
        if value > best:
            best_a, best = mid, value
        for left, right in ((lo, mid), (mid, hi)):
            ub = upper_bound(left, right)
            heapq.heappush(heap, (-ub, left, right))
        splits += 1
    gap = max(0.0, -heap[0][0] - best)
    # Refine inside the winning bracket without changing the proven gap.
    # A higher candidate likelihood can only tighten that gap.
    nearby = [(lo, hi) for _, lo, hi in heap if lo <= best_a <= hi]
    if nearby and upper > 0:
        lo, hi = min(nearby, key=lambda pair: pair[1] - pair[0])
        if hi > lo:
            opt = minimize_scalar(lambda a: -objective(a), bounds=(lo, hi),
                                  method="bounded", options={"xatol": 1e-13})
            if opt.success and -float(opt.fun) > best:
                best_a, best = float(opt.x), -float(opt.fun)
                gap = max(0.0, -heap[0][0] - best)
    # Stable expression for lam/(1+a*lam).
    fisher = 0.5 * float(np.sum((1.0 / (best_a + 1.0 / lam)) ** 2))
    return dict(amplitude=float(best_a), fisher_variance=float(1.0 / fisher) if fisher > 0 else math.inf,
                loglike_gain=float(best), objective_gap=float(gap),
                evaluations=evaluations, intervals=splits + 1,
                search_upper=float(upper), at_cap=bool(best_a == float(a_cap)),
                identified=True, status="NUMERICAL_GLOBAL_OBJECTIVE_GAP",
                loglike_tolerance=float(loglike_tol))
