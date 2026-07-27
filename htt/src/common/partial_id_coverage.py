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

from common.statistical_foundations import im_critical_value


def im_constant(delta_over_sigma: float, alpha: float) -> float:
    """Solve Phi(C + Delta/sigma) - Phi(-C) = 1 - alpha for C (Imbens-Manski)."""
    return im_critical_value(delta_over_sigma, 1.0, alpha)


def im_interval(lo_hat: float, hi_hat: float, sigma: float, alpha: float) -> tuple[float, float]:
    if not np.isfinite(sigma) or sigma <= 0.0:
        raise ValueError("sigma must be finite and positive")
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
    for _ in range(reps):
        lo_hat = -w + rng.normal(scale=sigma)
        hi_hat = w + rng.normal(scale=sigma)
        if lo_hat > hi_hat:  # sample crossing -> pseudotrue midpoint (never empty)
            mid = 0.5 * (lo_hat + hi_hat)
            lo_hat = hi_hat = mid
        if method == "im":
            a, b = im_interval(lo_hat, hi_hat, sigma, alpha)
        elif method == "point_gaussian":
            a, b = point_gaussian_interval(lo_hat, hi_hat, sigma, alpha)
        else:
            a, b = naive_interval(lo_hat, hi_hat, sigma, alpha)
        if a <= theta0 <= b:
            covered += 1
    est = covered / reps
    return {
        "method": method,
        "half_width": half_width,
        "reps": reps,
        "coverage": est,
        "cp_lower_99": cp_lower(covered, reps, 0.99),
        "covered": covered,
    }


def classify_regime(half_width: float, sigma: float) -> str:
    """point (w~0) / weak (w~sigma) / nonidentified (w >> sigma)."""
    r = half_width / sigma
    if r < 0.25:
        return "point"
    if r < 4.0:
        return "weak"
    return "nonidentified"
