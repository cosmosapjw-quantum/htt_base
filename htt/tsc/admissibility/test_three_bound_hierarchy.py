"""Tests for :mod:`tsc.admissibility.three_bound_hierarchy` (TSC-03)."""
from __future__ import annotations

from fractions import Fraction

import numpy as np
import pytest

from htt.core.ssot import C
from tsc.admissibility.three_bound_hierarchy import (
    A2_max,
    BIANCHI_TYPES,
    B_accel,
    B_omega,
    B_sigma,
    COEFFS,
    HierarchyViolationError,
    Sigma2_max,
    ThreeBoundReport,
    W2_max,
    compare_against_htt_bounds,
    compute_three_bound_hierarchy,
    evaluate_all_bianchi_types,
)


# ---------------------------------------------------------------------------
# §1 - SSOT sanity
# ---------------------------------------------------------------------------


class TestBianchiTypesRoster:
    def test_nine_types(self):
        assert len(BIANCHI_TYPES) == 9

    def test_no_duplicates(self):
        assert len(set(BIANCHI_TYPES)) == 9

    def test_types_are_strings(self):
        for t in BIANCHI_TYPES:
            assert isinstance(t, str) and t, f"bad type label: {t!r}"

    def test_roster_matches_htt_core_bounds(self):
        from tsc_legacy.htt_core_bounds import _TYPE_INFO
        assert set(BIANCHI_TYPES) == set(_TYPE_INFO.keys())


class TestCoefficientsAreExact:
    def test_sigma_coeffs(self):
        assert COEFFS["sigma"] == (
            Fraction(5, 3), Fraction(3, 1), Fraction(3, 7),
        )

    def test_omega_coeffs(self):
        assert COEFFS["omega"] == (
            Fraction(3, 4), Fraction(2, 1), Fraction(2, 7),
        )

    def test_accel_coeffs(self):
        assert COEFFS["accel"] == (
            Fraction(3, 4), Fraction(1, 1), Fraction(3, 14),
        )

    def test_all_values_are_fractions(self):
        for name, triple in COEFFS.items():
            for f in triple:
                assert isinstance(f, Fraction), (
                    f"COEFFS[{name!r}] contains non-Fraction entry {f!r}"
                )

    def test_no_floating_point_sigma_denominator(self):
        # Guard against somebody introducing Fraction(3, 14).limit_denominator()
        # style drift. Denominators must be the published small integers.
        allowed_denoms = {1, 3, 4, 7, 14}
        for triple in COEFFS.values():
            for f in triple:
                assert f.denominator in allowed_denoms


# ---------------------------------------------------------------------------
# §2 - Scalar bound evaluators
# ---------------------------------------------------------------------------


class TestScalarEvaluators:
    def test_B_sigma_known_value_at_S3(self):
        # S3 scenario: eps1 = eps1_kin, eps2 = Planck Commander, eps3 = Planck
        b = B_sigma(C.eps1_kin, C.eps2, C.eps3)
        expected = (5.0 / 3) * C.eps1_kin + 3.0 * C.eps2 + (3.0 / 7) * C.eps3
        assert b == pytest.approx(expected, rel=1e-14)

    def test_B_omega_known_value(self):
        b = B_omega(C.eps1_kin, C.eps2, C.eps3)
        expected = (3.0 / 4) * C.eps1_kin + 2.0 * C.eps2 + (2.0 / 7) * C.eps3
        assert b == pytest.approx(expected, rel=1e-14)

    def test_B_accel_known_value(self):
        b = B_accel(C.eps1_kin, C.eps2, C.eps3)
        expected = (3.0 / 4) * C.eps1_kin + 1.0 * C.eps2 + (3.0 / 14) * C.eps3
        assert b == pytest.approx(expected, rel=1e-14)

    def test_B_sigma_at_zero_is_zero(self):
        assert B_sigma(0.0, 0.0, 0.0) == 0.0

    def test_B_omega_at_zero_is_zero(self):
        assert B_omega(0.0, 0.0, 0.0) == 0.0

    def test_B_accel_at_zero_is_zero(self):
        assert B_accel(0.0, 0.0, 0.0) == 0.0

    def test_linearity_in_eps1(self):
        # Evaluating at (2a, 0, 0) = 2 * evaluating at (a, 0, 0)
        a = 1e-3
        assert B_sigma(2 * a, 0.0, 0.0) == pytest.approx(
            2 * B_sigma(a, 0.0, 0.0), rel=1e-14,
        )

    def test_negative_eps_rejected(self):
        with pytest.raises(ValueError, match="must be >= 0"):
            B_sigma(-1e-6, 0.0, 0.0)

    def test_nonfinite_eps_rejected(self):
        with pytest.raises(ValueError, match="must be finite"):
            B_omega(np.nan, 0.0, 0.0)


class TestCeilings:
    def test_Sigma2_max_equals_three_halves_Bsigma_squared(self):
        e1, e2, e3 = 1e-3, 3e-6, 6e-6
        expected = 1.5 * B_sigma(e1, e2, e3) ** 2
        assert Sigma2_max(e1, e2, e3) == pytest.approx(expected, rel=1e-14)

    def test_W2_max_equals_three_halves_Bomega_squared(self):
        e1, e2, e3 = 1e-3, 3e-6, 6e-6
        expected = 1.5 * B_omega(e1, e2, e3) ** 2
        assert W2_max(e1, e2, e3) == pytest.approx(expected, rel=1e-14)

    def test_A2_max_equals_three_halves_Baccel_squared(self):
        e1, e2, e3 = 1e-3, 3e-6, 6e-6
        expected = 1.5 * B_accel(e1, e2, e3) ** 2
        assert A2_max(e1, e2, e3) == pytest.approx(expected, rel=1e-14)

    def test_ceilings_non_negative(self):
        e1, e2, e3 = 0.0, 0.0, 0.0
        assert Sigma2_max(e1, e2, e3) == 0.0
        assert W2_max(e1, e2, e3) == 0.0
        assert A2_max(e1, e2, e3) == 0.0


# ---------------------------------------------------------------------------
# §3 - Hierarchy property
# ---------------------------------------------------------------------------


class TestHierarchyProperty:
    @pytest.mark.parametrize("eps1,eps2,eps3", [
        (1.0e-3, 3.5e-6, 6.0e-6),      # S1-like
        (1.476e-3, 3.5e-6, 6.0e-6),    # S3 / CatWISE
        (3.3e-3, 3.5e-6, 6.0e-6),      # radio-dominated
        (0.0, 1.0e-5, 0.0),            # eps2-only
        (0.0, 0.0, 1.0e-5),            # eps3-only
    ])
    def test_hierarchy_holds_positive_eps(self, eps1, eps2, eps3):
        rep = compute_three_bound_hierarchy(eps1, eps2, eps3)
        assert rep.hierarchy_strict is True
        assert rep.B_sigma_val > rep.B_omega_val > rep.B_accel_val

    def test_eps1_only_degenerate_equality(self):
        # With eps2 = eps3 = 0, B_omega = B_accel = (3/4) eps1, so the
        # strict hierarchy inequality fails even though the bounds are
        # physically well-defined. Strict mode must surface this.
        with pytest.raises(HierarchyViolationError):
            compute_three_bound_hierarchy(1e-3, 0.0, 0.0, strict=True)
        rep = compute_three_bound_hierarchy(1e-3, 0.0, 0.0, strict=False)
        assert rep.hierarchy_strict is False
        assert rep.B_omega_val == pytest.approx(rep.B_accel_val, rel=1e-14)

    def test_zero_eps_triggers_violation_in_strict(self):
        # All bounds equal zero → strict hierarchy fails.
        with pytest.raises(HierarchyViolationError):
            compute_three_bound_hierarchy(0.0, 0.0, 0.0)

    def test_zero_eps_soft_returns_report(self):
        rep = compute_three_bound_hierarchy(0.0, 0.0, 0.0, strict=False)
        assert rep.hierarchy_strict is False
        assert np.isnan(rep.ratio_omega_over_sigma)
        assert np.isnan(rep.ratio_accel_over_omega)

    def test_ratios_less_than_one(self):
        rep = compute_three_bound_hierarchy(1e-3, 3e-6, 6e-6)
        assert 0.0 < rep.ratio_omega_over_sigma < 1.0
        assert 0.0 < rep.ratio_accel_over_omega < 1.0

    def test_violation_message_includes_inputs(self):
        try:
            compute_three_bound_hierarchy(0.0, 0.0, 0.0)
        except HierarchyViolationError as exc:
            msg = str(exc)
            assert "B_sigma" in msg
            assert "B_accel" in msg
            assert "hierarchy violated" in msg.lower()


class TestTypeLabelHandling:
    def test_default_label_is_generic(self):
        rep = compute_three_bound_hierarchy(1e-3, 3e-6, 6e-6)
        assert rep.type_name == "generic"

    def test_accepts_known_type(self):
        rep = compute_three_bound_hierarchy(
            1e-3, 3e-6, 6e-6, type_name="VIIh",
        )
        assert rep.type_name == "VIIh"

    def test_rejects_unknown_type(self):
        with pytest.raises(ValueError, match="not in BIANCHI_TYPES"):
            compute_three_bound_hierarchy(
                1e-3, 3e-6, 6e-6, type_name="BogusVII",
            )


# ---------------------------------------------------------------------------
# §4 - Report dataclass invariants
# ---------------------------------------------------------------------------


class TestThreeBoundReport:
    def test_report_is_frozen(self):
        rep = compute_three_bound_hierarchy(1e-3, 3e-6, 6e-6)
        with pytest.raises(Exception):
            rep.eps1 = 0.5  # type: ignore[misc]

    def test_as_dict_has_expected_keys(self):
        rep = compute_three_bound_hierarchy(1e-3, 3e-6, 6e-6)
        d = rep.as_dict()
        for k in (
            "type_name", "eps1", "eps2", "eps3",
            "B_sigma", "B_omega", "B_accel",
            "Sigma2_max", "W2_max", "A2_max",
            "ratio_omega_over_sigma", "ratio_accel_over_omega",
            "hierarchy_strict", "config",
        ):
            assert k in d, f"missing key {k}"

    def test_config_records_coefficient_source(self):
        rep = compute_three_bound_hierarchy(1e-3, 3e-6, 6e-6)
        assert "coefficient_source" in rep.config
        assert "tsc.admissibility.three_bound_hierarchy" in rep.config[
            "coefficient_source"
        ]


# ---------------------------------------------------------------------------
# §5 - Nine-type evaluation
# ---------------------------------------------------------------------------


class TestEvaluateAllBianchiTypes:
    def test_returns_nine_reports(self):
        reports = evaluate_all_bianchi_types(1e-3, 3e-6, 6e-6)
        assert set(reports.keys()) == set(BIANCHI_TYPES)

    def test_hierarchy_holds_for_all_types(self):
        reports = evaluate_all_bianchi_types(
            C.eps1_kin, C.eps2, C.eps3,
        )
        for t, rep in reports.items():
            assert rep.hierarchy_strict is True, f"violation at type {t}"

    def test_type_labels_round_trip(self):
        reports = evaluate_all_bianchi_types(1e-3, 3e-6, 6e-6)
        for t, rep in reports.items():
            assert rep.type_name == t

    def test_bounds_are_type_independent(self):
        # Because bounds depend only on (eps1, eps2, eps3), not on type.
        reports = evaluate_all_bianchi_types(1e-3, 3e-6, 6e-6)
        values = {rep.B_sigma_val for rep in reports.values()}
        assert len(values) == 1

    def test_violation_surfaces_in_strict_mode(self):
        with pytest.raises(HierarchyViolationError):
            evaluate_all_bianchi_types(0.0, 0.0, 0.0, strict=True)


# ---------------------------------------------------------------------------
# §6 - Cross-check against the explicit legacy HTT bounds
# ---------------------------------------------------------------------------


class TestCompareAgainstHttBounds:
    def test_three_bound_hierarchy_matches_htt_bounds(self):
        """TSC-03 hero anchor: tsc and htt bounds agree to rtol 1e-10."""
        result = compare_against_htt_bounds(
            C.eps1_kin, C.eps2, C.eps3, rtol=1e-10,
        )
        assert result["all_agree"] is True
        for key in ("B_sigma", "B_omega", "B_accel"):
            assert result["rel_error"][key] < 1e-10
            assert result["agree"][key] is True

    @pytest.mark.parametrize("eps1,eps2,eps3", [
        (1.233e-3, 3.56e-6, 6.07e-6),   # S1 kinematic
        (1.476e-3, 3.56e-6, 6.07e-6),   # S3
        (3.296e-3, 3.56e-6, 6.07e-6),   # radio
        (0.0, 1.0e-5, 1.0e-5),          # no dipole
        (1.0e-2, 1.0e-4, 1.0e-4),       # large amplitudes (inside unit)
    ])
    def test_tsc_htt_agreement_on_sweep(self, eps1, eps2, eps3):
        result = compare_against_htt_bounds(eps1, eps2, eps3, rtol=1e-10)
        assert result["all_agree"] is True

    def test_result_has_provenance_keys(self):
        result = compare_against_htt_bounds(1e-3, 3e-6, 6e-6)
        for k in (
            "tsc_B_sigma", "htt_B_sigma",
            "tsc_B_omega", "htt_B_omega",
            "tsc_B_accel", "htt_B_accel",
            "abs_error", "rel_error", "agree", "rtol", "all_agree",
        ):
            assert k in result

    def test_returns_floats_not_numpy_scalars(self):
        result = compare_against_htt_bounds(1e-3, 3e-6, 6e-6)
        for k in ("tsc_B_sigma", "htt_B_sigma"):
            assert isinstance(result[k], float), (
                f"{k} must be Python float; got {type(result[k])}"
            )
        assert isinstance(result["all_agree"], bool)
