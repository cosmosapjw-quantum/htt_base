"""
tsc/charts/test_theta4_bridge_verify.py — TSC-04 tests.

Covers:
* Exact closed-form Θ⁴ → a_2 coefficient table
* Numerical Gauss-Legendre extraction of each coefficient
* End-to-end verifier returns a pass on the closed-form cross-check
* Direct a_2(A, Q) evaluation matches the expansion at small (A, Q)
* htt audit is *not* strictly required (passes when htt unavailable)
"""
from __future__ import annotations

import json

import numpy as np
import pytest

from tsc.charts.theta4_bridge_verify import (
    BridgeCoefficientReport,
    THETA4_A2_COEFFS_EXACT,
    gaunt_P_ell_int,
    theta4_a2_expansion_numerical,
    theta4_a2_numerical,
    theta4_bridge_coeffs_artifact,
    verify_theta4_a2_coefficients,
)


# ---------------------------------------------------------------------------
# §1 — closed-form table
# ---------------------------------------------------------------------------

class TestClosedFormCoefficients:
    def test_exact_table_present(self):
        assert set(THETA4_A2_COEFFS_EXACT.keys()) == {
            (0, 1), (2, 0), (0, 2), (2, 1),
        }

    def test_exact_values(self):
        assert THETA4_A2_COEFFS_EXACT[(0, 1)] == pytest.approx(4.0)
        assert THETA4_A2_COEFFS_EXACT[(2, 0)] == pytest.approx(4.0)
        assert THETA4_A2_COEFFS_EXACT[(0, 2)] == pytest.approx(12.0 / 7.0)
        assert THETA4_A2_COEFFS_EXACT[(2, 1)] == pytest.approx(44.0 / 7.0)


# ---------------------------------------------------------------------------
# §2 — individual Gaunt integrals
# ---------------------------------------------------------------------------

class TestGauntIntegrals:
    def test_P1_power_0_P2_power_1_integral(self):
        # ⟨P_2 · P_2⟩ = 2/5
        val = gaunt_P_ell_int(0, 1)
        assert val == pytest.approx(2.0 / 5.0, rel=1e-12)

    def test_P1_power_2_P2_power_0_integral(self):
        # ⟨P_1² P_2⟩ = ⟨μ² · P_2⟩ = 4/15 (computed by hand)
        val = gaunt_P_ell_int(2, 0)
        assert val == pytest.approx(4.0 / 15.0, rel=1e-12)

    def test_P2_cubed_integral(self):
        # ⟨P_2³⟩ = 4/35
        val = gaunt_P_ell_int(0, 2)
        assert val == pytest.approx(4.0 / 35.0, rel=1e-12)

    def test_odd_parity_integrals_vanish(self):
        # ⟨P_1 · P_2⟩ = 0 (odd × even on symmetric interval)
        assert abs(gaunt_P_ell_int(1, 0)) < 1e-14
        # ⟨P_1 · P_2²⟩ = 0 (odd × even)
        assert abs(gaunt_P_ell_int(1, 1)) < 1e-14

    def test_rejects_negative_exponents(self):
        with pytest.raises(ValueError, match="exponents"):
            gaunt_P_ell_int(-1, 0)


# ---------------------------------------------------------------------------
# §3 — numerical expansion extraction
# ---------------------------------------------------------------------------

class TestExpansionNumerical:
    def test_four_audited_coefficients_recovered(self):
        coeffs = theta4_a2_expansion_numerical()
        for monomial, exact in THETA4_A2_COEFFS_EXACT.items():
            assert coeffs[monomial] == pytest.approx(exact, rel=1e-10), (
                f"{monomial} mismatch: {coeffs[monomial]} vs {exact}"
            )

    def test_higher_order_monomials_also_present(self):
        coeffs = theta4_a2_expansion_numerical()
        # A⁴ coefficient: (5/2) · C(4,0,4,0) · ⟨P_1⁴ · P_2⟩.
        # The multinomial coefficient is 1; ⟨μ⁴ · (3μ²-1)/2⟩
        # = (1/2)∫(3μ⁶ − μ⁴)dμ = (1/2)(6/7 − 2/5) = 8/35.
        expected = (5.0 / 2.0) * 1 * (8.0 / 35.0)
        assert coeffs[(4, 0)] == pytest.approx(expected, rel=1e-10)

    def test_parity_cancellations(self):
        coeffs = theta4_a2_expansion_numerical()
        # Any monomial with odd exponent on A (odd parity in μ) gives zero.
        for monomial, val in coeffs.items():
            j, k = monomial
            if j % 2 == 1:
                assert abs(val) < 1e-10, f"{monomial} should vanish; got {val}"


# ---------------------------------------------------------------------------
# §4 — direct a_2(A, Q) evaluation vs expansion
# ---------------------------------------------------------------------------

class TestDirectEvaluation:
    def test_matches_expansion_for_small_A_Q(self):
        A, Q = 5e-3, 5e-3
        direct = theta4_a2_numerical(A, Q)
        expected = (
            4.0 * Q
            + 4.0 * A ** 2
            + (12.0 / 7.0) * Q ** 2
            + (44.0 / 7.0) * A ** 2 * Q
        )
        # Higher-order corrections are O((A,Q)^3) ≈ 1e-7 — generous rtol.
        assert direct == pytest.approx(expected, rel=5e-3, abs=1e-7)

    def test_scales_as_4Q_for_Q_alone(self):
        """With A = 0, the leading a_2 is ``4Q``."""
        Q = 1e-4
        val = theta4_a2_numerical(0.0, Q)
        assert val == pytest.approx(4.0 * Q, rel=1e-4)

    def test_scales_as_4A2_for_A_alone(self):
        """With Q = 0, the leading a_2 is ``4 A²``."""
        A = 1e-3
        val = theta4_a2_numerical(A, 0.0)
        assert val == pytest.approx(4.0 * A ** 2, rel=1e-4)


# ---------------------------------------------------------------------------
# §5 — end-to-end verifier
# ---------------------------------------------------------------------------

class TestVerifier:
    def test_reports_generated_for_all_four_coefficients(self):
        reports = verify_theta4_a2_coefficients(audit_htt=False)
        for monomial in THETA4_A2_COEFFS_EXACT:
            assert monomial in reports
            rep = reports[monomial]
            assert isinstance(rep, BridgeCoefficientReport)
            assert rep.passed, (
                f"{monomial} failed: rel_err = {rep.rel_err_vs_exact}"
            )

    def test_htt_audit_graceful_when_unimportable(self):
        """If ``htt`` cannot be imported, the report's ``htt_extracted``
        slot is ``None`` and the pass flag still reflects only the
        closed-form cross-check."""
        reports = verify_theta4_a2_coefficients(audit_htt=True)
        for rep in reports.values():
            # Either htt is importable (and the htt value landed in tol) or
            # not (and the slot is None); either way, the pass flag is set
            # by the closed-form check.
            if rep.htt_extracted is None:
                assert rep.passed
            else:
                assert isinstance(rep.htt_extracted, float)

    def test_htt_native_table_matches_exact_when_available(self):
        reports = verify_theta4_a2_coefficients(audit_htt=True)
        if any(rep.htt_extracted is None for rep in reports.values()):
            pytest.skip("htt import unavailable in this environment")
        for monomial, rep in reports.items():
            assert rep.htt_extracted == pytest.approx(
                THETA4_A2_COEFFS_EXACT[monomial], rel=1e-12
            )

    def test_tolerance_is_respected(self):
        """Setting a silly-tight tolerance should flip passed to False."""
        reports = verify_theta4_a2_coefficients(audit_htt=False, tol=1e-18)
        # Numerical extraction at float64 precision cannot match exact
        # rationals to 1e-18.
        any_failed = any(not r.passed for r in reports.values())
        assert any_failed

    def test_report_rejects_bad_rel_err(self):
        with pytest.raises(ValueError, match="rel_err"):
            BridgeCoefficientReport(
                monomial=(0, 1),
                exact=4.0,
                numerical=4.0,
                htt_extracted=None,
                rel_err_vs_exact=-0.1,
                passed=True,
            )

    def test_artifact_is_json_ready(self):
        artifact = theta4_bridge_coeffs_artifact(
            audit_htt=False,
            metadata={"git_commit": "test"},
        )
        assert artifact["artifact_name"] == "theta4_bridge_coeffs_v1.json"
        assert artifact["production_allowed"] is False
        assert artifact["all_passed"] is True
        assert len(artifact["reports"]) == 4
        assert artifact["config_hash"] != ""
        json.dumps(artifact)
