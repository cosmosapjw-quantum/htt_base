"""
tsc/diagnostics/filling_fraction.py  (TSC-02, Week 4)
======================================================

Filling-fraction posterior-mean diagnostic.

Role
----
Independent (from htt) re-computation of the Bayesian filling fraction

    F_Bayes = E[Q | D],    Q = |x| / B,

where ``x`` is the departure parameter (tsc.entropy_invariants) and
``B`` is the applicable tangency/MES bound (tsc.tangency or
tsc.admissibility). The published value for the Bianchi defect
framework is F_Bayes = 0.093 ± 0.025 (BASS_PY_HTT_TSC_RESEARCH_PLAN §9.2).

Why a posterior mean, not a point estimate
------------------------------------------
For any nonlinear ``Q(x)`` and posterior ``p(x|D)``, ``E[Q] ≠ Q(E[x])``.
The absolute-value kink of |x| is non-differentiable at x=0, and the
bound B(x) typically contracts toward 0 at small x. Both effects push
``F_Bayes`` above the naive point estimate ``F_point = |E[x]|/B(E[x])``
by ~30 % at the published S3 scenario (parent plan §7.9). TSC-02 is
the tsc-side independent computation used to cross-check htt's
``FillingFraction.mc_posterior``.

Gating
------
Pure numerical layer — no CanonicalDecision is consulted. TSC-06 is the
cross-check integration with htt.

Public API
----------
* :class:`FillingFractionReport` — dataclass with F_Bayes, F_point,
  credible intervals, N_eff, Q-samples.
* :func:`compute_filling_fraction(samples, B_callable, *, weights)` —
  core computation.
* :func:`gaussian_posterior_F_Bayes(mean, sigma, B, *, n)` —
  closed-form convenience for the Gaussian test case.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

import numpy as np

__all__ = [
    "FillingFractionReport",
    "compute_filling_fraction",
    "gaussian_posterior_F_Bayes",
]


# ---------------------------------------------------------------------------
# Report dataclass
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FillingFractionReport:
    """Posterior-mean filling fraction plus diagnostics.

    Attributes
    ----------
    F_Bayes
        Posterior-mean ``E[Q | D]``; the fiducial value (§9.2).
    F_point
        Naive point estimate ``|E[x]| / B(E[x])`` — exposed so callers can
        exhibit the posterior-vs-point gap.
    Q_samples
        Per-sample Q values; callers can recover arbitrary quantiles.
    weights
        Normalised importance weights over ``Q_samples``.
    credible_intervals
        ``{level: (low, high)}`` pairs — default keys 0.68 and 0.95.
    n_eff
        Kish effective sample size.
    config
        Provenance echo (estimator options, absolute-value mode, …).
    """

    F_Bayes: float
    F_point: float
    Q_samples: np.ndarray
    weights: np.ndarray
    credible_intervals: Mapping[float, tuple[float, float]]
    n_eff: float
    abs_mode: str = "abs"
    config: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.Q_samples.ndim != 1:
            raise ValueError(
                f"Q_samples must be 1-D; got ndim={self.Q_samples.ndim}"
            )
        if self.weights.shape != self.Q_samples.shape:
            raise ValueError(
                f"weights shape {self.weights.shape} incompatible with "
                f"Q_samples shape {self.Q_samples.shape}"
            )
        if self.abs_mode == "abs" and not np.all(self.Q_samples >= 0.0):
            raise ValueError(
                "Q_samples must be ≥ 0 under abs_mode='abs'"
            )
        if self.abs_mode == "abs" and self.F_Bayes < 0.0:
            raise ValueError(
                f"F_Bayes must be ≥ 0 under abs_mode='abs'; got {self.F_Bayes}"
            )

    @property
    def posterior_vs_point_ratio(self) -> float:
        """F_Bayes / F_point — values > 1 mean the point estimate *under*-reports."""
        if self.F_point <= 0.0:
            return float("inf")
        return float(self.F_Bayes / self.F_point)


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

def _weighted_quantile(
    values: np.ndarray, weights: np.ndarray, q: float,
) -> float:
    order = np.argsort(values)
    cum = np.cumsum(weights[order])
    idx = int(np.searchsorted(cum, q))
    idx = min(idx, values.size - 1)
    return float(values[order][idx])


def compute_filling_fraction(
    samples: np.ndarray,
    B: float | Callable[[np.ndarray], np.ndarray],
    *,
    weights: np.ndarray | None = None,
    levels: tuple[float, ...] = (0.68, 0.95),
    abs_mode: str = "abs",
) -> FillingFractionReport:
    """Posterior-mean filling fraction from departure-parameter samples.

    Parameters
    ----------
    samples
        1-D array of posterior draws of the departure parameter ``x``.
    B
        Either a positive float (bound evaluated at a fiducial ``x``) or a
        callable returning per-sample bounds (same shape as ``samples``).
        Non-positive bounds raise ``ValueError`` — the F = |x|/B statistic
        is undefined against a vanishing tangency bound.
    weights
        Optional importance weights. Defaults to equal weights.
    levels
        Credible-interval levels to compute. Default ``(0.68, 0.95)``.
    abs_mode
        ``'abs'`` (default) uses ``Q = |x|/B`` exactly as §9.2; ``'signed'``
        reports ``Q = x / B`` (can be negative — diagnostic only).

    Returns
    -------
    FillingFractionReport
    """
    samples = np.asarray(samples, dtype=float)
    if samples.ndim != 1:
        raise ValueError(f"samples must be 1-D; got ndim={samples.ndim}")
    n = samples.size
    if n == 0:
        raise ValueError("samples is empty")

    if weights is None:
        w = np.full(n, 1.0 / n, dtype=float)
    else:
        w = np.asarray(weights, dtype=float)
        if w.shape != (n,):
            raise ValueError(
                f"weights shape {w.shape} incompatible with n={n}"
            )
        if np.any(w < 0.0):
            raise ValueError("weights must be ≥ 0")
        s = float(w.sum())
        if s <= 0.0:
            raise ValueError("weights sum to zero")
        w = w / s

    if callable(B):
        B_vals = np.asarray(B(samples), dtype=float)
        if B_vals.shape != (n,):
            raise ValueError(
                f"B(samples) must have shape {(n,)}; got {B_vals.shape}"
            )
    else:
        B_val = float(B)
        if B_val <= 0.0:
            raise ValueError(f"B must be > 0; got {B_val}")
        B_vals = np.full(n, B_val, dtype=float)
    if np.any(B_vals <= 0.0):
        raise ValueError(
            "B(samples) produced non-positive value(s); F = |x|/B undefined"
        )

    if abs_mode == "abs":
        Q = np.abs(samples) / B_vals
    elif abs_mode == "signed":
        Q = samples / B_vals
    else:
        raise ValueError(
            f"abs_mode must be 'abs' or 'signed'; got {abs_mode!r}"
        )

    F_Bayes = float((w * Q).sum())
    x_mean = float((w * samples).sum())
    if callable(B):
        B_at_mean = float(B(np.asarray([x_mean]))[0])
    else:
        B_at_mean = float(B)
    if B_at_mean <= 0.0:
        raise ValueError(
            f"B(E[x]) non-positive ({B_at_mean}); F_point undefined"
        )
    F_point = abs(x_mean) / B_at_mean if abs_mode == "abs" else x_mean / B_at_mean

    ci: dict[float, tuple[float, float]] = {}
    for lv in levels:
        if not (0.0 < lv < 1.0):
            raise ValueError(f"level must be in (0, 1); got {lv}")
        lo = _weighted_quantile(Q, w, (1.0 - lv) / 2.0)
        hi = _weighted_quantile(Q, w, (1.0 + lv) / 2.0)
        ci[float(lv)] = (lo, hi)

    n_eff = float((w.sum()) ** 2 / (w * w).sum())

    return FillingFractionReport(
        F_Bayes=F_Bayes,
        F_point=float(F_point),
        Q_samples=Q,
        weights=w,
        credible_intervals=ci,
        n_eff=n_eff,
        abs_mode=abs_mode,
        config={
            "n_samples": n,
            "abs_mode": abs_mode,
            "B_callable": bool(callable(B)),
            "B_at_mean": B_at_mean,
            "levels": tuple(float(lv) for lv in levels),
        },
    )


# ---------------------------------------------------------------------------
# Gaussian closed-form convenience
# ---------------------------------------------------------------------------

def gaussian_posterior_F_Bayes(
    mean: float,
    sigma: float,
    B: float,
) -> dict[str, float]:
    """Analytic ``E[|x|/B]`` for ``x ~ 𝒩(mean, sigma²)`` with constant B.

    Returns a dict with keys ``F_Bayes`` (closed-form), ``F_point`` (naive),
    and ``ratio``. Handy for regressions that synthesise a Gaussian posterior
    and want to assert agreement with :func:`compute_filling_fraction`
    without round-tripping through a Monte-Carlo draw.
    """
    from math import erf, exp, pi, sqrt

    if sigma <= 0.0:
        raise ValueError(f"sigma must be > 0; got {sigma}")
    if B <= 0.0:
        raise ValueError(f"B must be > 0; got {B}")
    # E[|x|] for 𝒩(μ,σ):  σ √(2/π) exp(-μ²/2σ²) + μ erf(μ/(σ√2))
    z = mean / (sigma * sqrt(2.0))
    e_abs = sigma * sqrt(2.0 / pi) * exp(-z * z) + mean * erf(z)
    F_Bayes = e_abs / B
    F_point = abs(mean) / B
    ratio = F_Bayes / F_point if F_point > 0.0 else float("inf")
    return {"F_Bayes": float(F_Bayes), "F_point": float(F_point),
            "ratio": float(ratio)}
