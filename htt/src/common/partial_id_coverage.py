"""PR-200: calibrated partial-identification confidence sets (H14).

The honest CF4 simultaneous coverage 0.913 (below the nominal 0.95) is a
FAILURE of the naive union-of-one-sided intervals, not a calibrated set. The
Imbens-Manski construction widens the interval by the factor solving
Phi(C + Delta/sigma) - Phi(-C) = 1 - alpha, restoring coverage of the true
point at the least-favorable identified-set boundary. Misspecified / empty
samples are routed to a pseudotrue (never-empty) branch.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.optimize import brentq
from scipy.stats import beta, norm


def im_constant(delta_over_sigma: float, alpha: float) -> float:
    """Solve Phi(C + Delta/sigma) - Phi(-C) = 1 - alpha for C (Imbens-Manski)."""
    target = 1.0 - alpha

    def f(c: float) -> float:
        return norm.cdf(c + delta_over_sigma) - norm.cdf(-c) - target

    # C is between the one-sided z_{1-alpha} and the two-sided z_{1-alpha/2}
    lo = norm.ppf(1.0 - alpha) - 1e-6
    hi = norm.ppf(1.0 - alpha / 2.0) + 1e-6
    return float(brentq(f, lo, hi))


def im_interval(lo_hat: float, hi_hat: float, sigma: float, alpha: float) -> tuple[float, float]:
    delta = max(hi_hat - lo_hat, 0.0)
    c = im_constant(delta / sigma, alpha)
    return lo_hat - c * sigma, hi_hat + c * sigma


def naive_interval(lo_hat: float, hi_hat: float, sigma: float, alpha: float) -> tuple[float, float]:
    """Union of two one-sided (1-alpha) intervals."""
    z = norm.ppf(1.0 - alpha)
    return lo_hat - z * sigma, hi_hat + z * sigma


def point_gaussian_interval(
    lo_hat: float, hi_hat: float, sigma: float, alpha: float
) -> tuple[float, float]:
    """The MISTAKE (H14 failure mode): a point-estimate two-sided Gaussian CI
    centered on the identified-set midpoint, ignoring the set width. This
    undercovers the least-favorable boundary when the set is wide (the CF4
    0.913 pathology)."""
    mid = 0.5 * (lo_hat + hi_hat)
    z = norm.ppf(1.0 - alpha / 2.0)
    return mid - z * sigma, mid + z * sigma


def cp_lower(covered: int, n: int, confidence: float = 0.99) -> float:
    if covered == 0:
        return 0.0
    return float(beta.ppf(1.0 - confidence, covered, n - covered + 1))


def coverage_mc(
    *, half_width: float, sigma: float, alpha: float, reps: int, seed: int,
    method: str = "im",
) -> dict:
    """Coverage of the TRUE point at the least-favorable boundary.

    Identified set [theta_lo, theta_hi] = [-w, w]; the true point is the
    least-favorable boundary theta0 = w (worst case for one-sided coverage).
    """
    rng = np.random.default_rng(seed)
    w = half_width
    theta0 = w  # least-favorable boundary
    covered = 0
    crossing_samples = 0
    invalid_intervals = 0
    for _ in range(reps):
        lo_hat = -w + rng.normal(scale=sigma)
        hi_hat = w + rng.normal(scale=sigma)
        if lo_hat > hi_hat:  # sample crossing -> pseudotrue midpoint (never empty)
            crossing_samples += 1
            mid = 0.5 * (lo_hat + hi_hat)
            lo_hat = hi_hat = mid
        if method == "im":
            a, b = im_interval(lo_hat, hi_hat, sigma, alpha)
        elif method == "point_gaussian":
            a, b = point_gaussian_interval(lo_hat, hi_hat, sigma, alpha)
        else:
            a, b = naive_interval(lo_hat, hi_hat, sigma, alpha)
        interval_valid = math.isfinite(a) and math.isfinite(b) and a <= b
        if not interval_valid:
            invalid_intervals += 1
        elif a <= theta0 <= b:
            covered += 1
    est = covered / reps
    return {
        "method": method,
        "half_width": half_width,
        "reps": reps,
        "coverage": est,
        "cp_lower_99": cp_lower(covered, reps, 0.99),
        "covered": covered,
        "crossing_samples": crossing_samples,
        "invalid_intervals": invalid_intervals,
    }


def classify_regime(half_width: float, sigma: float) -> str:
    """point (w~0) / weak (w~sigma) / nonidentified (w >> sigma)."""
    r = half_width / sigma
    if r < 0.25:
        return "point"
    if r < 4.0:
        return "weak"
    return "nonidentified"
