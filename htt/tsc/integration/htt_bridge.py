"""
tsc/integration/htt_bridge.py  (TSC-06, Week 7)
================================================

Filling-fraction cross-check between the tsc-side diagnostic
(``tsc.diagnostics.filling_fraction.compute_filling_fraction``) and
the htt-side Monte-Carlo posterior
(``htt.core.analysis_extended.FillingFraction.mc_posterior``).

G19 architectural stance
------------------------
This module implements a **cross-check**, not a merge. Under the G19
rule (parent plan v3 §10.2bis and INDEPENDENT_TRACKS_PLAN v1.1
§14.3) the tsc and htt filling-fraction scores are **two independent
views of the same physics** — they must agree within the published
band, but the pipeline must never form a single summed / averaged
score by combining them. The :class:`FFCrossCheckReport` below
enforces this at the type level by carrying a frozen
``is_cross_check=True`` tag that downstream consumers are expected
to assert on ingest; any code path that strips or negates the tag is
architecturally invalid.

Two independent paths are computed
----------------------------------
``ff_htt_mc_cross_check`` draws the same RNG stream twice:

* Path HTT — ``htt.core.analysis_extended.FillingFraction.mc_posterior``
  builds ``x_V = (1+w) Omega_m sinh^2(eps1 / (1 + eta))``, the
  corrected ``Sigma2_max`` ceiling, and their per-sample ratio ``F``.
  ``F_Bayes_htt_mean`` is the sample mean of ``F``.

* Path TSC — this module redraws the same stream using
  ``numpy.random.default_rng(seed)`` with identical variance /
  location parameters, rebuilds ``x_V`` and the corrected ceiling from
  literal coefficients, and invokes
  ``tsc.diagnostics.filling_fraction.compute_filling_fraction`` on
  the resulting pair. ``F_Bayes_tsc`` is the resulting estimator.

The two paths apply the same physics with different code. A
coefficient drift on either side therefore fires
``assert_cross_check_consistent``.

Published regression target
---------------------------
BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN v3 §9.2 anchor

    F_Bayes = 0.093 ± 0.025    (68 % band → [0.068, 0.118]).

Public API
----------
* :class:`FFCrossCheckReport` --- frozen dataclass; carries the
  ``is_cross_check=True`` G19 flag plus tsc/htt F_Bayes means and
  agreement diagnostics.
* :data:`PUBLISHED_F_BAYES_BAND` --- ``(0.068, 0.118)`` SSOT.
* :func:`ff_gaussian_cross_check(mean, sigma, B)` --- closed-form
  Gaussian cross-check (tsc closed-form vs tsc MC); htt-free.
* :func:`ff_htt_mc_cross_check(scenario, N, seed, w)` --- runs htt's
  mc_posterior and the tsc re-derivation on the same RNG stream.
* :func:`assert_cross_check_consistent(report, rtol)` --- loud-fail
  guard used by the TSC-06 gate tests.

This module must never combine the two scores into a merged point
estimate. See the docstring of :class:`FFCrossCheckReport` for the
architectural rationale.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

import numpy as np

from tsc.diagnostics.filling_fraction import (
    compute_filling_fraction,
    gaussian_posterior_F_Bayes,
)

__all__ = [
    "PUBLISHED_F_BAYES_BAND",
    "FFCrossCheckReport",
    "ff_gaussian_cross_check",
    "ff_htt_mc_cross_check",
    "assert_cross_check_consistent",
    "CrossCheckMismatch",
]


#: (low, high) 68 % band from BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN v3
#: §9.2; the SSOT both sides must fall within.
PUBLISHED_F_BAYES_BAND: tuple[float, float] = (0.068, 0.118)


# ---------------------------------------------------------------------------
# Exception type
# ---------------------------------------------------------------------------


class CrossCheckMismatch(AssertionError):
    """Raised when tsc / htt disagreement exceeds tolerance.

    Subclass of :class:`AssertionError` so it also surfaces through
    pytest's assertion machinery.
    """


# ---------------------------------------------------------------------------
# Report dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FFCrossCheckReport:
    """Bundle of tsc + htt filling-fraction estimates.

    The ``is_cross_check`` field is **frozen True** to enforce the
    G19 architectural stance: any consumer that ingests this report
    must confirm the flag is set, and no pipeline stage may form a
    merged score from the two sides. See the module docstring.
    """

    F_Bayes_tsc: float
    F_Bayes_htt_mean: float
    F_Bayes_htt_median: float
    abs_difference: float
    rel_difference: float
    within_published_band: bool
    is_cross_check: bool = True
    scenario: str = "gaussian"
    n_samples: int = 0
    config: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.is_cross_check is not True:
            raise ValueError(
                "FFCrossCheckReport.is_cross_check must be True "
                "(G19 architectural stance — merging tsc and htt "
                "filling-fraction scores into a single point estimate "
                "is forbidden)."
            )
        if self.n_samples < 0:
            raise ValueError(
                f"n_samples must be >= 0; got {self.n_samples}"
            )

    def assert_is_cross_check(self) -> None:
        """Re-assert the G19 flag for defensive consumers."""
        if self.is_cross_check is not True:
            raise CrossCheckMismatch(
                "G19 violation: is_cross_check was flipped to False."
            )


# ---------------------------------------------------------------------------
# Closed-form Gaussian cross-check
# ---------------------------------------------------------------------------


def ff_gaussian_cross_check(
    mean: float,
    sigma: float,
    B: float,
    *,
    N: int = 100_000,
    seed: int = 20260419,
    rtol: float = 1e-3,
) -> FFCrossCheckReport:
    """Gaussian closed-form / MC cross-check with a constant bound B.

    This route does not touch htt; it cross-checks the tsc MC estimator
    against the tsc closed-form estimator for ``x ~ N(mean, sigma^2)``
    with a bound ``B`` held constant. It is the smoke-test route used
    by the TSC-06 gate when a full htt install is unavailable.

    Populates the report with ``F_Bayes_htt_mean`` set to the
    closed-form value (treating the closed-form derivation as the
    second, independently-derived view).
    """
    if sigma <= 0.0:
        raise ValueError(f"sigma must be > 0; got {sigma}")
    if B <= 0.0:
        raise ValueError(f"B must be > 0; got {B}")

    rng = np.random.default_rng(seed)
    samples = rng.normal(mean, sigma, N)
    tsc_report = compute_filling_fraction(samples, B)
    closed = gaussian_posterior_F_Bayes(mean=mean, sigma=sigma, B=B)

    tsc_val = float(tsc_report.F_Bayes)
    htt_val = float(closed["F_Bayes"])
    abs_diff = abs(tsc_val - htt_val)
    scale = max(abs(tsc_val), abs(htt_val), 1.0e-30)
    rel_diff = abs_diff / scale

    lo, hi = PUBLISHED_F_BAYES_BAND
    within = (lo <= tsc_val <= hi) and (lo <= htt_val <= hi)

    return FFCrossCheckReport(
        F_Bayes_tsc=tsc_val,
        F_Bayes_htt_mean=htt_val,
        F_Bayes_htt_median=float(np.median(tsc_report.Q_samples)),
        abs_difference=float(abs_diff),
        rel_difference=float(rel_diff),
        within_published_band=bool(within),
        scenario="gaussian",
        n_samples=int(N),
        config={
            "mean": float(mean),
            "sigma": float(sigma),
            "B": float(B),
            "seed": int(seed),
            "rtol_gate": float(rtol),
            "route": "gaussian_closed_form_vs_mc",
        },
    )


# ---------------------------------------------------------------------------
# HTT mc_posterior cross-check
# ---------------------------------------------------------------------------


def _tsc_filling_fraction_from_stream(
    eps1_samp: np.ndarray,
    eps2_samp: np.ndarray,
    eps3_samp: np.ndarray,
    *,
    w: float,
    Omega_m: float,
    eta: float,
    eps1_ref: float,
) -> float:
    """Rebuild x_V / x_max on the tsc side from a shared RNG stream.

    Literal coefficients are re-stated locally so a silent drift in
    htt's copy of the arithmetic fires the TSC-06 regression.
    """
    x_V = (1.0 + w) * Omega_m * np.sinh(eps1_samp / (1.0 + eta)) ** 2
    Bs_corr = (1.0 + 2.69 * eps1_ref) * (
        (5.0 / 3.0) * eps1_ref
        + 3.0 * eps2_samp
        + (3.0 / 7.0) * eps3_samp
    )
    x_max = 1.5 * Bs_corr ** 2
    # Per-sample ratio via callable-B branch of compute_filling_fraction.
    report = compute_filling_fraction(
        x_V, lambda _s: x_max, abs_mode="signed",
    )
    return float(report.F_Bayes)


def ff_htt_mc_cross_check(
    scenario: str = "S3",
    *,
    N: int = 100_000,
    seed: int = 20260419,
    w: float = 0.0,
) -> FFCrossCheckReport:
    """Run htt's mc_posterior and a tsc-side re-derivation on shared draws.

    Both paths draw from ``numpy.random.default_rng(seed)`` with the
    same (mean, sigma) parameters and re-compute ``F_Bayes`` from the
    MES identity independently. The gate is (i) numerical agreement at
    the rtol supplied to ``assert_cross_check_consistent`` and (ii)
    placement of both point estimates inside
    :data:`PUBLISHED_F_BAYES_BAND`.

    Raises :class:`ImportError` if the htt editable install is not
    available in the active interpreter.
    """
    from htt.core.analysis_extended import FillingFraction, SCENARIOS
    from htt.core.ssot import C as HttC

    if scenario not in SCENARIOS:
        raise ValueError(
            f"scenario {scenario!r} not in htt SCENARIOS {list(SCENARIOS)}"
        )

    # Draw the shared (eps1, eps2, eps3) triple ONCE on the bridge side.
    # Both paths consume the same stream via pre_drawn_eps / explicit
    # arguments — no hidden coupling to htt's internal rng call order.
    # (W9D5 close of W7 FM2.)
    rng = np.random.default_rng(seed)
    sc = SCENARIOS[scenario]
    e1_samp = sc["eps1"] + rng.normal(0, 0.30e-3, N)
    e1_samp = np.clip(e1_samp, 0, None)
    e2_samp = rng.normal(HttC.eps2, 1.5e-6, N)
    e3_samp = rng.normal(HttC.eps3, 2.0e-6, N)
    shared_triple = (e1_samp, e2_samp, e3_samp)

    # Path HTT — htt recomputes F_Bayes from the shared draws.
    ff = FillingFraction(w=w)
    F_samp, med, q16, q84, q025, q975 = ff.mc_posterior(
        scenario=scenario, N=N, seed=seed,
        pre_drawn_eps=shared_triple,
    )
    htt_val = float(np.mean(F_samp))

    # Path TSC — re-derive from the same shared triple.
    tsc_val = _tsc_filling_fraction_from_stream(
        e1_samp, e2_samp, e3_samp,
        w=w,
        Omega_m=float(HttC.Omega_m),
        eta=float(HttC.eta_udot),
        eps1_ref=float(HttC.eps1_kin),
    )

    abs_diff = abs(tsc_val - htt_val)
    scale = max(abs(tsc_val), abs(htt_val), 1.0e-30)
    rel_diff = abs_diff / scale

    lo, hi = PUBLISHED_F_BAYES_BAND
    within = (lo <= tsc_val <= hi) and (lo <= htt_val <= hi)

    return FFCrossCheckReport(
        F_Bayes_tsc=tsc_val,
        F_Bayes_htt_mean=htt_val,
        F_Bayes_htt_median=float(med),
        abs_difference=float(abs_diff),
        rel_difference=float(rel_diff),
        within_published_band=bool(within),
        scenario=str(scenario),
        n_samples=int(N),
        config={
            "seed": int(seed),
            "w": float(w),
            "htt_q16": float(q16),
            "htt_q84": float(q84),
            "htt_q025": float(q025),
            "htt_q975": float(q975),
            "route": "htt_mc_posterior_vs_tsc_compute_filling_fraction",
        },
    )


# ---------------------------------------------------------------------------
# Loud-fail guard
# ---------------------------------------------------------------------------


def assert_cross_check_consistent(
    report: FFCrossCheckReport,
    *,
    rtol: float = 5.0e-2,
    require_within_band: bool = True,
) -> None:
    """Assert that the two views agree and that the G19 flag is set.

    Parameters
    ----------
    report
        The :class:`FFCrossCheckReport` to audit.
    rtol
        Relative-difference threshold. Default 5 %.
    require_within_band
        When ``True`` (default), also assert that both tsc and htt
        point estimates fall within :data:`PUBLISHED_F_BAYES_BAND`.

    Raises
    ------
    CrossCheckMismatch
        On any of: rel_diff > rtol, G19 flag not set, or band
        violation (when requested).
    """
    report.assert_is_cross_check()
    if report.rel_difference > rtol:
        raise CrossCheckMismatch(
            f"TSC / HTT F_Bayes mismatch: tsc={report.F_Bayes_tsc:.4f}, "
            f"htt_mean={report.F_Bayes_htt_mean:.4f}, "
            f"rel_diff={report.rel_difference:.3e} > rtol={rtol:.3e}."
        )
    if require_within_band and not report.within_published_band:
        lo, hi = PUBLISHED_F_BAYES_BAND
        raise CrossCheckMismatch(
            "F_Bayes band violation: tsc="
            f"{report.F_Bayes_tsc:.4f}, htt_mean="
            f"{report.F_Bayes_htt_mean:.4f}; "
            f"published band = [{lo}, {hi}]."
        )
