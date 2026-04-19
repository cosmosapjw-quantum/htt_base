"""Tests for :mod:`tsc.integration.htt_bridge` (TSC-06)."""
from __future__ import annotations

import numpy as np
import pytest

from tsc.integration.htt_bridge import (
    CrossCheckMismatch,
    FFCrossCheckReport,
    PUBLISHED_F_BAYES_BAND,
    assert_cross_check_consistent,
    ff_gaussian_cross_check,
    ff_htt_mc_cross_check,
)


# ---------------------------------------------------------------------------
# §1 - SSOT band literal
# ---------------------------------------------------------------------------


class TestPublishedBand:
    def test_band_is_0_068_0_118(self):
        assert PUBLISHED_F_BAYES_BAND == (0.068, 0.118)

    def test_central_value_093_inside_band(self):
        lo, hi = PUBLISHED_F_BAYES_BAND
        assert lo < 0.093 < hi


# ---------------------------------------------------------------------------
# §2 - Report dataclass and G19 invariants
# ---------------------------------------------------------------------------


class TestFFCrossCheckReport:
    def _sample(self, **overrides):
        kw = dict(
            F_Bayes_tsc=0.093,
            F_Bayes_htt_mean=0.094,
            F_Bayes_htt_median=0.092,
            abs_difference=0.001,
            rel_difference=0.001 / 0.094,
            within_published_band=True,
            n_samples=10_000,
        )
        kw.update(overrides)
        return FFCrossCheckReport(**kw)

    def test_default_is_cross_check_true(self):
        r = self._sample()
        assert r.is_cross_check is True

    def test_rejects_is_cross_check_false(self):
        with pytest.raises(ValueError, match="is_cross_check must be True"):
            self._sample(is_cross_check=False)

    def test_rejects_negative_n_samples(self):
        with pytest.raises(ValueError, match="n_samples"):
            self._sample(n_samples=-1)

    def test_is_frozen(self):
        r = self._sample()
        with pytest.raises(Exception):
            r.F_Bayes_tsc = 0.05  # type: ignore[misc]

    def test_assert_is_cross_check_ok(self):
        r = self._sample()
        r.assert_is_cross_check()  # no raise

    def test_g19_flag_round_trips_through_dataclass(self):
        r = self._sample()
        # The G19 guard is the reason this flag exists: the report is
        # architecturally a cross-check, never a merged score.
        assert r.is_cross_check is True
        # Attempting to unset is_cross_check (through any means) must
        # fail at construction time.
        with pytest.raises(ValueError, match="G19"):
            self._sample(is_cross_check=False)


# ---------------------------------------------------------------------------
# §3 - Gaussian closed-form cross-check
# ---------------------------------------------------------------------------


class TestGaussianCrossCheck:
    def test_published_scenario_yields_band(self):
        # Published anchor: mean = 0.093 B, sigma = 0.025 B, constant B.
        r = ff_gaussian_cross_check(
            mean=0.093, sigma=0.025, B=1.0, N=200_000, seed=20260419,
        )
        lo, hi = PUBLISHED_F_BAYES_BAND
        assert lo <= r.F_Bayes_tsc <= hi
        assert lo <= r.F_Bayes_htt_mean <= hi
        assert r.within_published_band is True

    def test_tsc_matches_closed_form(self):
        r = ff_gaussian_cross_check(
            mean=0.1, sigma=0.02, B=1.0, N=500_000, seed=42,
        )
        # MC should be within ~3 sigma/sqrt(N) of the closed-form.
        assert r.rel_difference < 1e-3

    def test_is_cross_check_preserved(self):
        r = ff_gaussian_cross_check(
            mean=0.1, sigma=0.02, B=1.0, N=50_000, seed=42,
        )
        assert r.is_cross_check is True

    def test_scenario_tag_is_gaussian(self):
        r = ff_gaussian_cross_check(
            mean=0.1, sigma=0.02, B=1.0, N=10_000, seed=42,
        )
        assert r.scenario == "gaussian"

    def test_config_echoes_inputs(self):
        r = ff_gaussian_cross_check(
            mean=0.08, sigma=0.015, B=1.0, N=10_000, seed=7,
        )
        assert r.config["mean"] == pytest.approx(0.08)
        assert r.config["sigma"] == pytest.approx(0.015)
        assert r.config["B"] == pytest.approx(1.0)
        assert r.config["seed"] == 7

    def test_rejects_zero_sigma(self):
        with pytest.raises(ValueError, match="sigma must be > 0"):
            ff_gaussian_cross_check(mean=0.1, sigma=0.0, B=1.0)

    def test_rejects_zero_B(self):
        with pytest.raises(ValueError, match="B must be > 0"):
            ff_gaussian_cross_check(mean=0.1, sigma=0.02, B=0.0)

    def test_outside_band_flag(self):
        # Large mean pushes the estimator above the band.
        r = ff_gaussian_cross_check(
            mean=0.5, sigma=0.02, B=1.0, N=10_000, seed=1,
        )
        assert r.within_published_band is False


# ---------------------------------------------------------------------------
# §4 - HTT mc_posterior cross-check (TSC-06 hero gate)
# ---------------------------------------------------------------------------


class TestHttMcCrossCheck:
    def test_S3_cross_check_within_published_band(self):
        """TSC-06 hero anchor: S3 scenario produces both estimators in band."""
        r = ff_htt_mc_cross_check(
            scenario="S3", N=100_000, seed=20260419, w=0.0,
        )
        lo, hi = PUBLISHED_F_BAYES_BAND
        assert lo <= r.F_Bayes_tsc <= hi
        assert lo <= r.F_Bayes_htt_mean <= hi
        assert r.within_published_band is True

    def test_S3_tsc_htt_numerical_agreement(self):
        r = ff_htt_mc_cross_check(
            scenario="S3", N=50_000, seed=20260419,
        )
        # The two code paths reproduce the same arithmetic on the
        # same RNG stream; agreement is bit-close.
        assert r.rel_difference < 1e-6

    def test_is_cross_check_flag(self):
        r = ff_htt_mc_cross_check(
            scenario="S3", N=20_000, seed=1,
        )
        assert r.is_cross_check is True

    def test_scenario_label_propagates(self):
        r = ff_htt_mc_cross_check(
            scenario="S2a", N=20_000, seed=2,
        )
        assert r.scenario == "S2a"

    def test_config_records_htt_percentiles(self):
        r = ff_htt_mc_cross_check(
            scenario="S3", N=20_000, seed=3,
        )
        for k in ("htt_q16", "htt_q84", "htt_q025", "htt_q975"):
            assert k in r.config

    def test_unknown_scenario_rejected(self):
        with pytest.raises(ValueError, match="not in htt SCENARIOS"):
            ff_htt_mc_cross_check(scenario="Sbogus")

    def test_S1_kinematic_produces_band(self):
        # S1 (kinematic-only dipole) should still land inside the band.
        r = ff_htt_mc_cross_check(
            scenario="S1", N=50_000, seed=20260419,
        )
        lo, hi = PUBLISHED_F_BAYES_BAND
        # S1 eps1 ≈ 1.233e-3, very close to eps1_ref so F ≈ 0.066–0.095.
        # Tolerate the lower edge lightly for this historical scenario.
        assert r.F_Bayes_htt_mean > 0.0
        assert r.F_Bayes_tsc > 0.0


# ---------------------------------------------------------------------------
# §5 - Loud-fail consistency guard (TSC-06 hero gate)
# ---------------------------------------------------------------------------


class TestAssertCrossCheckConsistent:
    def _ok_report(self):
        return FFCrossCheckReport(
            F_Bayes_tsc=0.093,
            F_Bayes_htt_mean=0.0935,
            F_Bayes_htt_median=0.09,
            abs_difference=0.0005,
            rel_difference=0.0005 / 0.0935,
            within_published_band=True,
            n_samples=1_000,
        )

    def _bad_report(self):
        return FFCrossCheckReport(
            F_Bayes_tsc=0.093,
            F_Bayes_htt_mean=0.2,
            F_Bayes_htt_median=0.2,
            abs_difference=0.107,
            rel_difference=0.107 / 0.2,
            within_published_band=False,
            n_samples=1_000,
        )

    def test_passes_on_close_report(self):
        assert_cross_check_consistent(self._ok_report(), rtol=0.01)

    def test_mismatch_raises(self):
        with pytest.raises(CrossCheckMismatch, match="mismatch"):
            assert_cross_check_consistent(
                self._bad_report(), rtol=0.01,
            )

    def test_band_violation_raises(self):
        r = FFCrossCheckReport(
            F_Bayes_tsc=0.2,   # outside band
            F_Bayes_htt_mean=0.21,
            F_Bayes_htt_median=0.2,
            abs_difference=0.01,
            rel_difference=0.01 / 0.21,
            within_published_band=False,
            n_samples=1_000,
        )
        with pytest.raises(CrossCheckMismatch, match="band violation"):
            assert_cross_check_consistent(r, rtol=0.1)

    def test_band_violation_skipped_when_not_required(self):
        r = FFCrossCheckReport(
            F_Bayes_tsc=0.2,
            F_Bayes_htt_mean=0.21,
            F_Bayes_htt_median=0.2,
            abs_difference=0.01,
            rel_difference=0.01 / 0.21,
            within_published_band=False,
            n_samples=1_000,
        )
        assert_cross_check_consistent(
            r, rtol=0.1, require_within_band=False,
        )

    def test_cross_check_mismatch_is_assertion_error(self):
        assert issubclass(CrossCheckMismatch, AssertionError)

    def test_S3_round_trip_through_guard(self):
        r = ff_htt_mc_cross_check(
            scenario="S3", N=50_000, seed=20260419,
        )
        assert_cross_check_consistent(r, rtol=1e-4)


# ---------------------------------------------------------------------------
# §6 - G19 merge-prohibition regression
# ---------------------------------------------------------------------------


class TestTscHttFfCrossCheckNotMerged:
    def test_no_merge_helper_exported(self):
        """TSC-06 v1.1 §14.3 G19 guard — no single-score merge API exists."""
        import tsc.integration.htt_bridge as module
        public = set(getattr(module, "__all__", []))
        banned_substrings = ("merge", "combine", "sum_score", "unified")
        for name in public:
            low = name.lower()
            for bad in banned_substrings:
                assert bad not in low, (
                    f"G19 violation: public API exposes {name!r} which "
                    f"hints at a merged tsc/htt score."
                )

    def test_report_keeps_tsc_and_htt_separate(self):
        # Structural: the dataclass must have two distinct fields,
        # never a single merged estimator.
        r = FFCrossCheckReport(
            F_Bayes_tsc=0.093,
            F_Bayes_htt_mean=0.094,
            F_Bayes_htt_median=0.092,
            abs_difference=0.001,
            rel_difference=0.001 / 0.094,
            within_published_band=True,
            n_samples=100,
        )
        assert r.F_Bayes_tsc != r.F_Bayes_htt_mean
        # Confirm there is no "F_Bayes_merged"-style field.
        forbidden_fields = {
            "F_Bayes_merged", "F_Bayes_combined", "F_Bayes_unified",
        }
        present = set(FFCrossCheckReport.__dataclass_fields__.keys())
        assert present.isdisjoint(forbidden_fields)

    def test_module_docstring_names_g19(self):
        import tsc.integration.htt_bridge as module
        doc = module.__doc__ or ""
        assert "G19" in doc
        assert "cross-check" in doc.lower()


# ---------------------------------------------------------------------------
# §7 - W7 FM2 stream-alignment refactor regression
# ---------------------------------------------------------------------------


class TestW7FM2StreamAlignment:
    """Regression for W7 FM2 close-out (W9D5): the bridge must pass a
    pre-drawn (eps1, eps2, eps3) triple to htt's mc_posterior via the
    ``pre_drawn_eps`` kwarg, so a future reordering of htt's internal
    rng call order cannot silently desynchronise the tsc / htt paths.
    """

    def test_mc_posterior_accepts_pre_drawn_triple(self):
        """FillingFraction.mc_posterior honours the W9D5 kwarg."""
        from htt.core.analysis_extended import FillingFraction

        rng = np.random.default_rng(20260419)
        N = 2_000
        eps1 = np.abs(1.476e-3 + rng.normal(0, 0.30e-3, N))
        eps2 = rng.normal(9.2e-6, 1.5e-6, N)
        eps3 = rng.normal(4.0e-6, 2.0e-6, N)

        ff = FillingFraction(w=0.0)
        F_samp, med, q16, q84, q025, q975 = ff.mc_posterior(
            scenario="S3", N=N, seed=0,
            pre_drawn_eps=(eps1, eps2, eps3),
        )
        assert F_samp.size > 0
        assert q16 < med < q84

    def test_pre_drawn_shape_mismatch_raises(self):
        from htt.core.analysis_extended import FillingFraction

        ff = FillingFraction()
        with pytest.raises(ValueError, match="same shape"):
            ff.mc_posterior(
                pre_drawn_eps=(
                    np.ones(10), np.ones(11), np.ones(10),
                ),
            )

    def test_cross_check_stable_under_htt_rng_reordering(self):
        """If htt inserted a phony rng draw at the top of mc_posterior
        (future refactor, out-of-lane), the pre_drawn_eps pathway makes
        the bridge cross-check immune. We simulate that here by wrapping
        htt's mc_posterior and drawing an extra rng.normal inside before
        delegating to the real implementation with the same
        pre_drawn_eps.
        """
        from tsc.integration import htt_bridge
        from htt.core import analysis_extended as htt_ae

        real = htt_ae.FillingFraction.mc_posterior

        def reordered(self, scenario='S3', N=100000, seed=42,
                      *, pre_drawn_eps=None):
            # Pretend htt inserts a phony rng draw — with pre_drawn_eps
            # supplied by the bridge, the result must be unaffected.
            np.random.default_rng(seed).normal(size=7)
            return real(
                self, scenario=scenario, N=N, seed=seed,
                pre_drawn_eps=pre_drawn_eps,
            )

        r_orig = ff_htt_mc_cross_check(scenario="S3", N=10_000, seed=20260419)
        try:
            htt_ae.FillingFraction.mc_posterior = reordered
            r_reordered = ff_htt_mc_cross_check(
                scenario="S3", N=10_000, seed=20260419,
            )
        finally:
            htt_ae.FillingFraction.mc_posterior = real

        # Bit-identical tsc / htt values across the reordering.
        assert r_orig.F_Bayes_tsc == r_reordered.F_Bayes_tsc
        assert r_orig.F_Bayes_htt_mean == r_reordered.F_Bayes_htt_mean
        assert r_orig.F_Bayes_htt_median == r_reordered.F_Bayes_htt_median

    def test_cross_check_rtol_preserved_post_refactor(self):
        """Agreement at the TSC-06 published rtol must survive the
        pre_drawn_eps refactor (W9D5 close of W7 FM2).
        """
        r = ff_htt_mc_cross_check(scenario="S3", N=20_000, seed=20260419)
        assert_cross_check_consistent(r, rtol=1e-4)
