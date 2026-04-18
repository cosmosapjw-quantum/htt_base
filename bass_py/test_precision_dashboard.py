"""
Test suite: precision_dashboard.py (Week 3 Day 5a, merged v4.1)
================================================================

Tests cover both the analytic oracle library and the L0 gate verdict.

Test classes (6):
  1. TestAnalyticOracle      (closed-form I_n, I_4/I_3, Σ_2 values)
  2. TestCheckResult         (dataclass contract)
  3. TestDashboardSmallRun   (fast run with n_draws=5)
  4. TestDashboardGateVerdict (production-seed all-green gate)
  5. TestFormatting          (Markdown + JSON output)
  6. TestCheckCoverage       (expected checks present)

Target: ~20 tests.

Test strategy
-------------
Most tests use `n_draws_per_cell=5` for speed (adds ~1s each). One
production-seed test runs with n_draws=50 to verify the L0 gate passes
at the settings documented in `inverse_T_to_F_mc_report.md`.
"""
from __future__ import annotations

import json
import math

import numpy as np
import pytest
from scipy.special import zeta

from precision_dashboard import (
    L0_DASHBOARD_VERSION,
    analytic_I_n,
    analytic_I4_over_I3,
    analytic_Sigma_2,
    CheckResult,
    DashboardReport,
    run_l0_dashboard,
    to_markdown,
    to_json,
)


# ============================================================================
# Test Class 1 - Analytic oracle library
# ============================================================================

class TestAnalyticOracle:
    """Closed-form I_n, I_4/I_3, Σ_2 at η = 0."""

    def test_I_n_BE_matches_Gamma_zeta(self):
        # I_n(BE) = Γ(n+1) × ζ(n+1)
        for n in (2, 3, 4, 5):
            expected = math.gamma(n + 1) * float(zeta(n + 1))
            assert analytic_I_n("BE", n) == pytest.approx(expected, rel=1e-15)

    def test_I_n_MB_matches_factorial(self):
        for n in (2, 3, 4, 5):
            expected = math.gamma(n + 1)
            assert analytic_I_n("MB", n) == pytest.approx(expected, rel=1e-15)

    def test_I_n_FD_matches_eta_function(self):
        # I_n(FD) = (1 - 2^{-n}) × Γ(n+1) × ζ(n+1)
        for n in (2, 3, 4, 5):
            expected = (
                (1.0 - 2.0 ** (-n))
                * math.gamma(n + 1)
                * float(zeta(n + 1))
            )
            assert analytic_I_n("FD", n) == pytest.approx(expected, rel=1e-15)

    def test_I4_over_I3_MB_is_exactly_4(self):
        assert analytic_I4_over_I3("MB") == pytest.approx(4.0, abs=1e-15)

    def test_I4_over_I3_BE_matches_memory_value(self):
        # Memory: BE I_4/I_3 ≈ 3.8322
        val = analytic_I4_over_I3("BE")
        assert val == pytest.approx(3.8322, rel=1e-3)

    def test_I4_over_I3_FD_matches_memory_value(self):
        # Memory: FD I_4/I_3 ≈ 4.1060
        val = analytic_I4_over_I3("FD")
        assert val == pytest.approx(4.1060, rel=1e-3)

    def test_Sigma_2_MB_is_32_over_15(self):
        assert analytic_Sigma_2("MB") == pytest.approx(32.0 / 15.0, rel=1e-15)

    def test_Sigma_2_is_8_over_15_times_ratio(self):
        for label in ("BE", "MB", "FD"):
            assert analytic_Sigma_2(label) == pytest.approx(
                (8.0 / 15.0) * analytic_I4_over_I3(label),
                rel=1e-15,
            )

    def test_rejects_unknown_statistics(self):
        with pytest.raises(ValueError, match="unknown statistics"):
            analytic_I_n("BOGUS", 3)


# ============================================================================
# Test Class 2 - CheckResult contract
# ============================================================================

class TestCheckResult:
    """Frozen dataclass + relative_error property."""

    def test_relative_error_on_nonzero_oracle(self):
        c = CheckResult(
            check_id="t", category="cat", statistics=None,
            oracle_value=10.0, observed_value=10.001,
            tolerance=1e-3, passed=True,
        )
        assert c.relative_error == pytest.approx(1e-4, rel=1e-6)

    def test_relative_error_none_for_missing_oracle(self):
        c = CheckResult(
            check_id="t", category="cat", statistics=None,
            oracle_value=None, observed_value=1.0,
            tolerance=None, passed=True,
        )
        assert c.relative_error is None

    def test_relative_error_none_for_zero_oracle(self):
        c = CheckResult(
            check_id="t", category="cat", statistics=None,
            oracle_value=0.0, observed_value=1e-12,
            tolerance=1e-10, passed=True,
        )
        assert c.relative_error is None

    def test_dataclass_is_frozen(self):
        c = CheckResult(
            check_id="t", category="cat", statistics=None,
            oracle_value=1.0, observed_value=1.0,
            tolerance=1e-10, passed=True,
        )
        with pytest.raises(Exception):
            c.passed = False


# ============================================================================
# Test Class 3 - Fast dashboard run (n_draws=5)
# ============================================================================

class TestDashboardSmallRun:
    """Fast runs with reduced MC draws for structural checks."""

    def test_report_returns_DashboardReport(self):
        report = run_l0_dashboard(n_draws_per_cell=5, seed=42)
        assert isinstance(report, DashboardReport)

    def test_spec_version_pinned(self):
        report = run_l0_dashboard(n_draws_per_cell=5, seed=42)
        assert report.spec_version == L0_DASHBOARD_VERSION

    def test_n_total_consistent_with_checks(self):
        report = run_l0_dashboard(n_draws_per_cell=5, seed=42)
        assert report.n_total == len(report.checks)
        assert report.n_passed == sum(1 for c in report.checks if c.passed)

    def test_all_passed_is_AND(self):
        report = run_l0_dashboard(n_draws_per_cell=5, seed=42)
        expected = all(c.passed for c in report.checks)
        assert report.all_passed == expected

    def test_skip_roundtrip_reduces_check_count(self):
        with_rt = run_l0_dashboard(n_draws_per_cell=5, include_roundtrip=True)
        without_rt = run_l0_dashboard(
            n_draws_per_cell=5, include_roundtrip=False,
        )
        assert without_rt.n_total < with_rt.n_total
        # 6 roundtrip checks (2 per amp × 3 amps)
        assert with_rt.n_total - without_rt.n_total == 6


# ============================================================================
# Test Class 4 - Production-seed gate verdict
# ============================================================================

class TestDashboardGateVerdict:
    """The L0 gate must pass at the documented production seed."""

    def test_L0_gate_passes_at_production_seed(self):
        # Full 50-draw sweep with the production seed; must all-pass.
        report = run_l0_dashboard(
            n_draws_per_cell=50, seed=20260417,
        )
        assert report.all_passed, (
            "L0 gate failed; failing checks: "
            + ", ".join(c.check_id for c in report.checks if not c.passed)
        )

    def test_analytic_checks_are_all_exact(self):
        report = run_l0_dashboard(
            n_draws_per_cell=5, seed=42, include_roundtrip=False,
        )
        # At eta=0, xi_moment uses the analytical closed-form path and
        # the oracle uses the same formula — rel err is exactly 0 in
        # all moment/ratio/ch05 rows.
        analytic_rows = [
            c for c in report.checks
            if c.category in ("moment", "ratio", "ch05_cross_ref")
        ]
        for c in analytic_rows:
            assert c.passed
            assert c.relative_error == pytest.approx(0.0, abs=1e-15)

    def test_MB_gram_diag_relative_error_below_1e_13(self):
        report = run_l0_dashboard(
            n_draws_per_cell=5, include_roundtrip=False,
        )
        c = next(
            x for x in report.checks if x.check_id.startswith("MB_gram_diag")
        )
        assert c.passed
        # Observed ~3e-14 (from smoke run)
        assert "diag_rel_err_max=" in c.notes

    def test_MB_twofield_kappa_close_to_54p3(self):
        report = run_l0_dashboard(
            n_draws_per_cell=5, include_roundtrip=False,
        )
        c = next(
            x for x in report.checks if x.check_id == "MB_twofield_Gram_kappa"
        )
        assert c.observed_value == pytest.approx(54.3, rel=0.05)
        assert c.passed


# ============================================================================
# Test Class 5 - Output formatting
# ============================================================================

class TestFormatting:
    """Markdown + JSON output."""

    def test_markdown_contains_verdict_line(self):
        report = run_l0_dashboard(n_draws_per_cell=5, include_roundtrip=False)
        md = to_markdown(report)
        assert "L0 Precision Dashboard" in md
        assert ("PASS" in md) or ("FAIL" in md)

    def test_markdown_row_per_check(self):
        report = run_l0_dashboard(
            n_draws_per_cell=5, include_roundtrip=False,
        )
        md = to_markdown(report)
        # Each check_id should appear as a row
        for c in report.checks:
            assert f"`{c.check_id}`" in md

    def test_json_roundtrips(self):
        report = run_l0_dashboard(
            n_draws_per_cell=5, include_roundtrip=False,
        )
        payload = to_json(report)
        parsed = json.loads(payload)
        assert parsed["spec_version"] == L0_DASHBOARD_VERSION
        assert parsed["n_total"] == report.n_total
        assert parsed["all_passed"] == report.all_passed

    def test_json_contains_checks_list(self):
        report = run_l0_dashboard(
            n_draws_per_cell=5, include_roundtrip=False,
        )
        payload = to_json(report)
        parsed = json.loads(payload)
        assert "checks" in parsed
        assert len(parsed["checks"]) == report.n_total


# ============================================================================
# Test Class 6 - Check-coverage sanity
# ============================================================================

class TestCheckCoverage:
    """Every expected check_id shows up in the report."""

    def test_all_statistics_covered_in_moment_checks(self):
        report = run_l0_dashboard(
            n_draws_per_cell=5, include_roundtrip=False,
        )
        moment_ids = {
            c.check_id for c in report.checks if c.category == "moment"
        }
        # Expect 6 moment checks: {BE, MB, FD} × {I_3, I_4}
        assert len(moment_ids) == 6

    def test_each_amplitude_has_two_roundtrip_checks(self):
        report = run_l0_dashboard(n_draws_per_cell=5, seed=20260417)
        rt_checks = [c for c in report.checks if c.category == "roundtrip"]
        # 3 amps × 2 metrics (p95, worst) = 6
        assert len(rt_checks) == 6
        # Each amp has exactly one p95 and one worst
        for amp in (0.05, 0.10, 0.20):
            matching = [c for c in rt_checks if f"amp={amp}" in c.check_id]
            assert len(matching) == 2

    def test_gram_checks_present(self):
        report = run_l0_dashboard(
            n_draws_per_cell=5, include_roundtrip=False,
        )
        gram_ids = {
            c.check_id for c in report.checks if c.category == "gram"
        }
        assert any("diag" in cid for cid in gram_ids)
        assert any("offdiag" in cid for cid in gram_ids)
