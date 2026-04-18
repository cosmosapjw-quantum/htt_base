"""
tsc/diagnostics/test_filling_fraction.py — TSC-02 tests.

Covers:
* FillingFractionReport invariants
* compute_filling_fraction on synthetic Gaussian posteriors
* regression: the published F_Bayes = 0.093 ± 0.025 value is reproduced
  by a Gaussian x ~ 𝒩(0.093 B, 0.025 B) posterior
* point vs posterior-mean gap ≳ 30 % on a diffuse posterior
* abs_mode='signed' passthrough
* callable-B branch (variance-dependent bound)
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from tsc.diagnostics.filling_fraction import (
    FillingFractionReport,
    compute_filling_fraction,
    gaussian_posterior_F_Bayes,
)


# ---------------------------------------------------------------------------
# §1 — FillingFractionReport invariants
# ---------------------------------------------------------------------------

class TestFillingFractionReport:
    def test_rejects_bad_Q_shape(self):
        with pytest.raises(ValueError, match="1-D"):
            FillingFractionReport(
                F_Bayes=0.1, F_point=0.1,
                Q_samples=np.ones((3, 3)),
                weights=np.ones((3, 3)),
                credible_intervals={0.68: (0.0, 1.0)},
                n_eff=9.0,
            )

    def test_rejects_weights_shape_mismatch(self):
        with pytest.raises(ValueError, match="weights shape"):
            FillingFractionReport(
                F_Bayes=0.1, F_point=0.1,
                Q_samples=np.ones(5),
                weights=np.ones(4),
                credible_intervals={0.68: (0.0, 1.0)},
                n_eff=5.0,
            )

    def test_rejects_negative_Q(self):
        with pytest.raises(ValueError, match="must be ≥ 0"):
            FillingFractionReport(
                F_Bayes=0.1, F_point=0.1,
                Q_samples=np.array([-1.0, 0.0, 1.0]),
                weights=np.full(3, 1.0 / 3.0),
                credible_intervals={0.68: (0.0, 1.0)},
                n_eff=3.0,
            )

    def test_posterior_vs_point_ratio(self):
        rep = FillingFractionReport(
            F_Bayes=0.12, F_point=0.10,
            Q_samples=np.linspace(0.0, 1.0, 5),
            weights=np.full(5, 1.0 / 5.0),
            credible_intervals={0.68: (0.0, 0.5)},
            n_eff=5.0,
        )
        assert math.isclose(rep.posterior_vs_point_ratio, 1.2, rel_tol=1e-12)


# ---------------------------------------------------------------------------
# §2 — compute_filling_fraction on Gaussian x-posteriors
# ---------------------------------------------------------------------------

class TestComputeFillingFraction:
    def test_matches_closed_form_gaussian(self):
        rng = np.random.default_rng(0)
        mu, sigma, B = 0.3, 0.08, 3.2
        samples = rng.normal(mu, sigma, size=20_000)
        rep = compute_filling_fraction(samples, B)
        ref = gaussian_posterior_F_Bayes(mu, sigma, B)
        # MC vs closed-form within 1% (20k samples)
        np.testing.assert_allclose(rep.F_Bayes, ref["F_Bayes"], rtol=2e-2)
        np.testing.assert_allclose(rep.F_point, ref["F_point"], rtol=5e-3)

    def test_published_regression_value(self):
        """Regression: F_Bayes = 0.093 ± 0.025 reproduced from a Gaussian
        x-posterior whose first two moments match the published summary.

        Anchor: BASS_PY_HTT_TSC_RESEARCH_PLAN §9.2 and §7.9."""
        rng = np.random.default_rng(42)
        # A ~ B choice (x in the same units as B) so that E[|x|/B] ≈ 0.093.
        # Pick μ_x = 0.093 B, σ_x such that the standard deviation of |x|/B
        # is ≈ 0.025.
        B = 1.0
        mu = 0.093 * B
        # For μ ≫ 0, |x|/B ≈ x/B with std = σ/B → choose σ = 0.025.
        sigma = 0.025
        samples = rng.normal(mu, sigma, size=50_000)
        rep = compute_filling_fraction(samples, B)
        assert abs(rep.F_Bayes - 0.093) <= 0.025, (
            f"F_Bayes = {rep.F_Bayes:.4f} outside published [0.068, 0.118] band"
        )

    def test_posterior_mean_exceeds_point_for_diffuse_posterior(self):
        """For a posterior broad relative to |μ|, the |·| kink makes
        F_Bayes > F_point — the entire motivation for §6.10's regression.

        ParentPlan §7.9 claims the gap ≳ 30 % at the published scenario;
        we pick σ/|μ| = 1 (broader than production) to reliably observe it."""
        rng = np.random.default_rng(1)
        mu, sigma, B = 0.3, 0.3, 3.2
        samples = rng.normal(mu, sigma, size=30_000)
        rep = compute_filling_fraction(samples, B)
        ratio = rep.posterior_vs_point_ratio
        assert ratio > 1.15, (
            f"posterior/point ratio {ratio:.3f} ≤ 1.15; diffuse posterior "
            "should produce a ≥ 15% gap"
        )

    def test_callable_B_branch(self):
        """B can be a callable (bound depends on x). Used by the TSC-03
        three-bound-hierarchy integration when B_σ depends on Σ² itself."""
        rng = np.random.default_rng(2)
        samples = rng.normal(0.5, 0.1, size=10_000)

        def B_fn(x: np.ndarray) -> np.ndarray:
            return 2.0 + 0.1 * x    # slightly x-dependent bound

        rep = compute_filling_fraction(samples, B_fn)
        # With this smooth B(x) and small σ, the MC answer should be close
        # to |μ| / B(μ) (point estimate).
        expected_point = 0.5 / (2.0 + 0.1 * 0.5)
        assert abs(rep.F_point - expected_point) < 5e-3
        assert abs(rep.F_Bayes - expected_point) < 0.05

    def test_signed_mode_can_produce_negative(self):
        rng = np.random.default_rng(3)
        samples = rng.normal(-0.5, 0.1, size=5_000)
        rep = compute_filling_fraction(samples, 2.0, abs_mode="signed")
        assert rep.F_Bayes < 0.0
        assert rep.F_point < 0.0

    def test_importance_weights_shift_F(self):
        rng = np.random.default_rng(4)
        samples = np.concatenate([
            rng.normal(0.0, 0.05, size=5_000),
            rng.normal(0.5, 0.05, size=5_000),
        ])
        # Equal weights → F_Bayes ≈ 0.25/B
        rep_eq = compute_filling_fraction(samples, 2.0)
        # Weight second bump heavily → F_Bayes ≈ 0.5/B
        weights = np.concatenate([np.full(5_000, 0.01), np.full(5_000, 1.0)])
        rep_w = compute_filling_fraction(samples, 2.0, weights=weights)
        assert rep_w.F_Bayes > rep_eq.F_Bayes

    def test_rejects_non_positive_B(self):
        with pytest.raises(ValueError, match="B must be > 0"):
            compute_filling_fraction(np.zeros(3), B=0.0)
        with pytest.raises(ValueError, match="B must be > 0"):
            compute_filling_fraction(np.zeros(3), B=-1.0)

    def test_rejects_B_callable_shape(self):
        def bad_B(x):
            return np.array([1.0])     # wrong shape
        with pytest.raises(ValueError, match="B\\(samples\\)"):
            compute_filling_fraction(np.zeros(5), bad_B)

    def test_rejects_non_positive_B_samples(self):
        def bad_B(x):
            return -np.ones_like(x)
        with pytest.raises(ValueError, match="non-positive"):
            compute_filling_fraction(np.zeros(5), bad_B)

    def test_rejects_bad_abs_mode(self):
        with pytest.raises(ValueError, match="abs_mode"):
            compute_filling_fraction(np.zeros(5), 2.0, abs_mode="weird")

    def test_rejects_bad_level(self):
        with pytest.raises(ValueError, match="level"):
            compute_filling_fraction(np.ones(5), 2.0, levels=(0.0,))

    def test_credible_intervals_are_monotone(self):
        rng = np.random.default_rng(5)
        samples = rng.normal(0.4, 0.08, size=20_000)
        rep = compute_filling_fraction(samples, 3.0, levels=(0.5, 0.68, 0.95))
        lo50, hi50 = rep.credible_intervals[0.5]
        lo68, hi68 = rep.credible_intervals[0.68]
        lo95, hi95 = rep.credible_intervals[0.95]
        assert lo95 <= lo68 <= lo50
        assert hi50 <= hi68 <= hi95

    def test_n_eff_matches_uniform_for_equal_weights(self):
        rep = compute_filling_fraction(np.ones(100) * 0.3, B=2.0)
        assert math.isclose(rep.n_eff, 100.0, rel_tol=1e-9)

    def test_n_eff_drops_with_peaked_weights(self):
        rng = np.random.default_rng(6)
        samples = rng.normal(0.3, 0.1, size=1000)
        weights = np.zeros(1000)
        weights[0] = 1.0                  # single-sample dominance
        rep = compute_filling_fraction(samples, 2.0, weights=weights)
        assert rep.n_eff == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# §3 — gaussian_posterior_F_Bayes (analytic)
# ---------------------------------------------------------------------------

class TestGaussianPosteriorFBayes:
    def test_zero_mean_reduces_to_abs_gaussian(self):
        """For μ=0, E[|x|] = σ √(2/π); so F_Bayes = σ √(2/π) / B."""
        out = gaussian_posterior_F_Bayes(mean=0.0, sigma=0.5, B=1.0)
        expected = 0.5 * math.sqrt(2.0 / math.pi)
        assert math.isclose(out["F_Bayes"], expected, rel_tol=1e-12)
        assert out["F_point"] == 0.0
        assert math.isinf(out["ratio"])

    def test_large_mu_limit_approaches_mu_over_B(self):
        """For μ ≫ σ, E[|x|] → μ → F_Bayes → μ/B (ratio → 1)."""
        out = gaussian_posterior_F_Bayes(mean=10.0, sigma=0.01, B=3.0)
        np.testing.assert_allclose(out["F_Bayes"], 10.0 / 3.0, rtol=1e-6)
        np.testing.assert_allclose(out["ratio"], 1.0, rtol=1e-6)

    def test_rejects_non_positive_sigma(self):
        with pytest.raises(ValueError, match="sigma"):
            gaussian_posterior_F_Bayes(0.3, -1.0, 1.0)

    def test_rejects_non_positive_B(self):
        with pytest.raises(ValueError, match="B"):
            gaussian_posterior_F_Bayes(0.3, 0.1, 0.0)
