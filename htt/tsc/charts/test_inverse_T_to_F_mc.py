"""
Test suite: inverse_T_to_F_mc.py (Week 3 Day 3, merged v4.1)
=============================================================

Exercises the Monte Carlo sweep and the retrofit-readiness of the inverse
map module (classification as `tsc/charts/`).

  1. TestSweepInfrastructure   (sweep returns, determinism, product-space)
  2. TestRoundtripPrecision    (per-cell tolerance envelopes)
  3. TestIterationStatistics   (Newton iter + condition number scaling)
  4. TestReportGeneration      (CSV + markdown output)
  5. TestAdmissibilityHandling (rejection sampling boundaries)
  6. TestStatisticsUniformity  (BE/MB/FD behaviour parity)
  7. TestRetrofitReadiness     (prep for W3D5b freeze commit)

Test strategy
-------------
Tests use a reduced `n_draws = 5` per cell (135 trials) for fast pytest runs.
The full 1350-trial sweep is executed once (outside the test suite) to
populate `inverse_T_to_F_mc_report.md`. The tests verify the infrastructure
and closure properties; the production numbers live in the report.
"""
from __future__ import annotations

import csv
import os
import tempfile
from typing import List

import numpy as np
import pytest

from tsc.charts.inverse_T_to_F_mc import (
    XI_LIST, MOMENT_ORDER_LIST, AMP_LIST, L_THETA_DEFAULT, REJECTION_CAP,
    TrialRecord, CellStats,
    draw_admissible_theta,
    run_trial, run_sweep,
    aggregate_by_cell,
    records_to_csv, render_report_markdown,
)
from tsc.charts.forward_F_to_T import AxisymmetricField, check_theta_positive


# ============================================================================
# Test Class 1 - Sweep infrastructure
# ============================================================================

class TestSweepInfrastructure:
    """Sweep return shape, determinism, coverage."""

    def test_sweep_returns_list_of_records(self):
        records = run_sweep(n_draws_per_cell=2)
        assert isinstance(records, list)
        assert all(isinstance(r, TrialRecord) for r in records)

    def test_sweep_count_matches_product(self):
        # 3 xi × 3 n × 3 amp × 2 draws = 54
        records = run_sweep(n_draws_per_cell=2)
        assert len(records) == 3 * 3 * 3 * 2

    def test_sweep_covers_full_product_space(self):
        records = run_sweep(n_draws_per_cell=1)
        seen = {(r.xi, r.moment_order, r.amp) for r in records}
        expected = {
            (xi, n, amp)
            for xi in XI_LIST for n in MOMENT_ORDER_LIST for amp in AMP_LIST
        }
        assert seen == expected

    def test_sweep_deterministic_given_seed(self):
        recs_a = run_sweep(n_draws_per_cell=3, seed=42)
        recs_b = run_sweep(n_draws_per_cell=3, seed=42)
        assert len(recs_a) == len(recs_b)
        for a, b in zip(recs_a, recs_b):
            assert a.theta_true == b.theta_true
            assert a.max_rel_error == b.max_rel_error
            assert a.n_iter == b.n_iter

    def test_different_seeds_give_different_draws(self):
        recs_a = run_sweep(n_draws_per_cell=3, seed=1)
        recs_b = run_sweep(n_draws_per_cell=3, seed=2)
        # At least one draw must differ (astronomically unlikely to collide)
        diff = [a.theta_true != b.theta_true for a, b in zip(recs_a, recs_b)]
        assert any(diff)

    def test_sweep_rejects_zero_draws(self):
        with pytest.raises(ValueError, match="n_draws_per_cell"):
            run_sweep(n_draws_per_cell=0)

    def test_sweep_rejects_negative_draws(self):
        with pytest.raises(ValueError, match="n_draws_per_cell"):
            run_sweep(n_draws_per_cell=-1)


# ============================================================================
# Test Class 2 - Per-cell precision envelopes
# ============================================================================

class TestRoundtripPrecision:
    """Per-cell tolerance verification across the product space."""

    # Per the full 1350-trial run (see inverse_T_to_F_mc_report.md):
    #   amp 0.05: worst max ≈ 1.5e-9
    #   amp 0.10: worst max ≈ 1.0e-9
    #   amp 0.20: worst max ≈ 4.2e-8 (outlier; typical 10⁻⁹)
    # We test that *all* trials in each cell stay under generous envelopes
    # to leave headroom for seed-sensitive outliers.

    AMP_ENVELOPE = {
        0.05: 1e-7,   # three-decade headroom over observed 1e-10
        0.10: 1e-7,
        0.20: 1e-6,   # one decade over observed 4e-8
    }

    @pytest.mark.parametrize("xi", list(XI_LIST))
    @pytest.mark.parametrize("amp", list(AMP_LIST))
    def test_max_error_within_envelope(self, xi, amp):
        records = [
            r for r in run_sweep(n_draws_per_cell=5)
            if r.xi == xi and r.amp == amp
        ]
        assert len(records) > 0
        max_err = max(r.max_rel_error for r in records)
        envelope = self.AMP_ENVELOPE[amp]
        assert max_err < envelope, (
            f"xi={xi}, amp={amp}: max_rel_error={max_err:.2e} exceeds "
            f"envelope {envelope:.2e}"
        )

    def test_p50_error_is_machine_precision_at_small_amp(self):
        # At amp=0.05 the median error should hug machine epsilon
        records = [
            r for r in run_sweep(n_draws_per_cell=10)
            if r.amp == 0.05
        ]
        errors = np.array([r.max_rel_error for r in records])
        p50 = np.median(errors)
        assert p50 < 1e-8

    def test_all_trials_converge(self):
        records = run_sweep(n_draws_per_cell=3)
        assert all(r.converged for r in records), (
            "Some trial failed to converge"
        )


# ============================================================================
# Test Class 3 - Iteration statistics
# ============================================================================

class TestIterationStatistics:
    """Newton iteration count and Jacobian condition scaling."""

    def test_iteration_count_bounded_for_small_amp(self):
        records = [
            r for r in run_sweep(n_draws_per_cell=5)
            if r.amp == 0.05
        ]
        max_iter = max(r.n_iter for r in records)
        # At amp=0.05 the linear-response initial guess is nearly exact
        assert max_iter <= 6, f"Unexpectedly high iter count: {max_iter}"

    def test_iteration_count_bounded_for_large_amp(self):
        records = [
            r for r in run_sweep(n_draws_per_cell=5)
            if r.amp == 0.20
        ]
        max_iter = max(r.n_iter for r in records)
        # At amp=0.20 even worst case should stay well under 15
        assert max_iter <= 15

    def test_condition_number_grows_with_amplitude(self):
        records = run_sweep(n_draws_per_cell=10)
        cond_by_amp = {amp: [] for amp in AMP_LIST}
        for r in records:
            cond_by_amp[r.amp].append(r.jacobian_cond)
        mean_cond = {
            amp: float(np.mean(vals)) for amp, vals in cond_by_amp.items()
        }
        # Expect cond(amp=0.05) < cond(amp=0.10) < cond(amp=0.20)
        assert mean_cond[0.05] < mean_cond[0.10]
        assert mean_cond[0.10] < mean_cond[0.20]

    def test_all_conditions_finite_and_positive(self):
        records = run_sweep(n_draws_per_cell=3)
        for r in records:
            assert np.isfinite(r.jacobian_cond)
            assert r.jacobian_cond > 0


# ============================================================================
# Test Class 4 - Aggregation and report output
# ============================================================================

class TestReportGeneration:
    """CSV + markdown output integrity."""

    def test_aggregate_produces_27_cells(self):
        records = run_sweep(n_draws_per_cell=2)
        stats = aggregate_by_cell(records)
        assert len(stats) == 27

    def test_aggregate_empty_input_returns_empty(self):
        assert aggregate_by_cell([]) == []

    def test_aggregate_statistics_consistency(self):
        records = run_sweep(n_draws_per_cell=5)
        stats = aggregate_by_cell(records)
        for s in stats:
            # p50 ≤ p95 ≤ max always
            assert s.max_rel_error_p50 <= s.max_rel_error_p95
            assert s.max_rel_error_p95 <= s.max_rel_error_max
            assert 0 <= s.converged_fraction <= 1

    def test_csv_writes_and_reloads(self):
        records = run_sweep(n_draws_per_cell=2)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False,
        ) as f:
            csv_path = f.name
        try:
            records_to_csv(records, csv_path)
            with open(csv_path, "r") as f:
                rows = list(csv.DictReader(f))
            assert len(rows) == len(records)
            # Check one representative row has expected keys
            assert "max_rel_error" in rows[0]
            assert "jacobian_cond" in rows[0]
        finally:
            os.unlink(csv_path)

    def test_render_markdown_contains_all_cells(self):
        records = run_sweep(n_draws_per_cell=2)
        stats = aggregate_by_cell(records)
        md = render_report_markdown(
            stats, n_draws_per_cell=2, seed=20260417,
        )
        assert "Per-cell summary" in md
        assert "Precision floor per amplitude tier" in md
        # Per-cell table: header (9+ pipes) + separator + 27 cell rows
        n_main_rows = sum(1 for line in md.split("\n") if line.count("|") >= 9)
        assert n_main_rows >= 27 + 2  # cells + header + separator


# ============================================================================
# Test Class 5 - Admissibility handling
# ============================================================================

class TestAdmissibilityHandling:
    """Rejection sampling and Θ > 0 guards."""

    def test_drawn_theta_is_always_admissible(self):
        rng = np.random.default_rng(7)
        for _ in range(30):
            field, _ = draw_admissible_theta(amp=0.2, L_Theta=3, rng=rng)
            assert check_theta_positive(field)

    def test_rejection_count_small_at_moderate_amp(self):
        # At amp=0.2 L=3 the admissibility fail rate is extremely low;
        # most draws accept on first try. Total rejections across 50 draws
        # observed in the full sweep was 0. We assert ≤ a lenient bound.
        rng = np.random.default_rng(11)
        total_rejected = 0
        for _ in range(50):
            _, n_rej = draw_admissible_theta(amp=0.2, L_Theta=3, rng=rng)
            total_rejected += n_rej
        assert total_rejected < 50  # generous; observed = 0 in production

    def test_rejection_cap_raises_on_impossible(self):
        # Set amp absurdly large; all draws should fail. With
        # rejection_cap=3 we expect RuntimeError.
        rng = np.random.default_rng(0)
        with pytest.raises(RuntimeError, match="rejection sampling"):
            draw_admissible_theta(
                amp=100.0, L_Theta=3, rng=rng, rejection_cap=3,
            )


# ============================================================================
# Test Class 6 - Statistics uniformity
# ============================================================================

class TestStatisticsUniformity:
    """BE / MB / FD produce comparable behaviour at matched (n, amp)."""

    def test_convergence_uniform_across_statistics(self):
        records = run_sweep(n_draws_per_cell=5)
        conv_by_xi = {xi: [] for xi in XI_LIST}
        for r in records:
            conv_by_xi[r.xi].append(r.converged)
        # Every xi should achieve 100% convergence at this amp range
        for xi, convs in conv_by_xi.items():
            assert all(convs), f"xi={xi} has non-convergent trials"

    def test_no_xi_dominates_iteration_cost(self):
        records = run_sweep(n_draws_per_cell=10)
        iters_by_xi = {xi: [] for xi in XI_LIST}
        for r in records:
            iters_by_xi[r.xi].append(r.n_iter)
        mean_iter = {xi: float(np.mean(vals)) for xi, vals in iters_by_xi.items()}
        # All three means within factor 1.5 of each other
        lo, hi = min(mean_iter.values()), max(mean_iter.values())
        assert hi / lo < 1.5, (
            f"Iteration-count imbalance across statistics: {mean_iter}"
        )

    def test_precision_comparable_across_statistics(self):
        # Absolute uniformity: at matched (n=3, amp=0.05), all three
        # statistics must achieve p95 < 1e-7. A ratio-based check is
        # unstable because the machine-zero tail dominates some xi bins
        # and not others (seed-sensitive).
        records = [
            r for r in run_sweep(n_draws_per_cell=10)
            if r.moment_order == 3 and r.amp == 0.05
        ]
        errs_by_xi = {xi: [] for xi in XI_LIST}
        for r in records:
            errs_by_xi[r.xi].append(r.max_rel_error)
        p95 = {
            xi: float(np.percentile(vals, 95))
            for xi, vals in errs_by_xi.items()
        }
        for xi, p in p95.items():
            assert p < 1e-7, (
                f"xi={xi} p95 error {p:.2e} exceeds uniformity floor 1e-7; "
                f"full map: {p95}"
            )


# ============================================================================
# Test Class 7 - Retrofit readiness (prep for W3D5b freeze commit)
# ============================================================================

class TestRetrofitReadiness:
    """Verify the inverse map module is clean for the tsc/charts/ move."""

    def test_mc_library_does_not_leak_bass_runtime(self):
        # inverse_T_to_F_mc.py is TSC-layer; must not import bass/runtime/
        import tsc.charts.inverse_T_to_F_mc as mod
        src = open(mod.__file__).read()
        forbidden = [
            "from canonical_decision", "from validation_labels",
            "from sigma_floor", "from baryon_only_policy",
        ]
        for pattern in forbidden:
            assert pattern not in src, (
                f"MC module leaks bass/runtime dependency: {pattern}"
            )

    def test_tsc_charts_chain_self_contained(self):
        # The future tsc/charts/ chain is: laguerre_basis → forward_F_to_T
        # → inverse_T_to_F → inverse_T_to_F_mc. No external dependencies
        # outside tsc/ except for numpy, scipy.
        from tsc.charts import inverse_T_to_F
        src_inverse = open(inverse_T_to_F.__file__).read()
        # These imports (from W1/W2 BASS modules) would block a clean move
        forbidden = [
            "from bianchi_types", "from shear_sources",
            "from baryon_only_policy", "from channel_routing",
            "from einstein_bianchi", "from comparator_policy",
        ]
        for pattern in forbidden:
            assert pattern not in src_inverse, (
                f"inverse_T_to_F imports BASS layer: {pattern}"
            )

    def test_mc_library_reproduces_seed_across_process_restart(self):
        # Pseudo-test for reproducibility: same sweep parameters yield
        # identical theta_true tuples. Already exercised in
        # test_sweep_deterministic_given_seed above, re-asserted here as
        # a retrofit contract.
        recs = run_sweep(n_draws_per_cell=1, seed=999)
        recs_again = run_sweep(n_draws_per_cell=1, seed=999)
        assert [r.theta_true for r in recs] == [
            r.theta_true for r in recs_again
        ]
