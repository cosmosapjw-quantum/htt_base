"""Independent exact fixtures and boundary tests for normalized selection."""

from fractions import Fraction

import numpy as np
import pytest

from selection_bounds import (box_mass_bounds, normalized_bounds,
                              retained_result, unsupported_mass_bounds)


P = [0.2, 0.3, 0.5]
A = [0.5] * 3
B = [2.0] * 3


def test_exact_rational_witnesses_and_original_residuals():
    result = normalized_bounds(P, [0, 1, 0], [0, 1, 1], A, B,
                               joint_ids=["j1", "j2", "j3"])
    assert result["lower"]["value"] == pytest.approx(float(Fraction(3, 31)), abs=1e-10)
    assert result["upper"]["value"] == pytest.approx(float(Fraction(16, 17)), abs=1e-10)
    for endpoint in ("lower", "upper"):
        assert result[endpoint]["max_original_residual"] <= 1e-10


def test_common_ratio_cancels_and_box_mass_formula():
    common = normalized_bounds(P, [0, 1, 0], [0, 1, 1], [1.7] * 3, [1.7] * 3)
    assert common["lower"]["value"] == pytest.approx(0.3, abs=1e-10)
    assert common["upper"]["value"] == pytest.approx(0.8, abs=1e-10)
    assert box_mass_bounds(0.3, 0.8, 1) == pytest.approx((0.3, 0.8))
    assert box_mass_bounds(0.3, 0.8, 2) == pytest.approx((3 / 31, 16 / 17))
    assert box_mass_bounds(0, 1, 1e308) == (0, 1)


def test_unsupported_target_mass_and_unknown_physical_event():
    lo, hi = box_mass_bounds(0.3, 0.8, 2)
    assert unsupported_mass_bounds(lo, hi, 0.1) == pytest.approx((27 / 310, 161 / 170))
    assert unsupported_mass_bounds(0, 1, 1) == (0, 1)
    unknown = normalized_bounds(P, [0] * 3, [1] * 3, A, B)
    assert (unknown["lower"]["value"], unknown["upper"]["value"]) == pytest.approx((0, 1))


def test_polytope_constraints_and_equality_boundary():
    # Equality r1=r2=r3 forces the common-ratio cancellation on a boundary.
    result = normalized_bounds(P, [0, 1, 0], [0, 1, 1], A, B,
                               E=[[1, -1, 0], [0, 1, -1]], f=[0, 0],
                               B=[[1, 0, 0]], d=[0.5])
    assert result["lower"]["value"] == pytest.approx(0.3, abs=1e-10)
    assert result["upper"]["value"] == pytest.approx(0.8, abs=1e-10)
    for endpoint in ("lower", "upper"):
        assert result[endpoint]["weight_witness"] == pytest.approx([0.5] * 3, abs=1e-10)
        assert result[endpoint]["max_original_residual"] <= 1e-10


def test_infeasible_polytope_rejected():
    with pytest.raises(ValueError, match="weight polytope LP failed"):
        normalized_bounds(P, [0, 1, 0], [0, 1, 1], A, B,
                          B=[[1, 0, 0]], d=[0.4])


def test_positive_support_and_unique_joint_ids_required():
    with pytest.raises(ValueError, match="strictly positive"):
        normalized_bounds([0.0, 1.0], [0, 0], [1, 1], [0.5, 0.5], [2, 2])
    with pytest.raises(ValueError, match="ordered and unique"):
        normalized_bounds(P, [0, 1, 0], [0, 1, 1], A, B, joint_ids=["same"] * 3)
    with pytest.raises(ValueError, match="binary"):
        normalized_bounds(P, [0.5, 0, 0], [0.5, 1, 1], A, B)
    with pytest.raises(ValueError, match="underflow"):
        normalized_bounds([1e-320, 1.0], [1, 0], [1, 0], [1e-320, 0.5], [1e308, 2])


def test_tiny_reference_mass_does_not_hide_large_normalized_upper():
    result = normalized_bounds([1e-10, 1 - 1e-10], [1, 0], [1, 0],
                               [0.5, 0.5], [1e10, 2])
    assert result["upper"]["value"] == pytest.approx(0.6666666666888889, abs=1e-12)
    assert result["upper"]["weight_witness"] == pytest.approx([1e10, 0.5], rel=1e-12)
    assert result["upper"]["max_original_residual"] <= 1e-10


def test_overflowing_common_weight_normalizer_fails_closed():
    weight = np.finfo(float).max
    with pytest.raises(ArithmeticError, match="nonfinite or nonpositive weight normalizer"):
        normalized_bounds([0.5, 0.5 + 1e-11], [1, 0], [1, 0],
                          [weight, weight], [weight, weight])


def test_tiny_mass_coupled_lp_fails_closed_if_dual_cannot_certify():
    # A redundant inequality deliberately routes through the coupled LP.
    # This ill-scaled instance must not emit a false finite endpoint.
    try:
        result = normalized_bounds([1e-10, 1 - 1e-10], [1, 0], [1, 0],
                                   [0.5, 0.5], [1e10, 2], B=[[1, 0]], d=[1e10])
    except (ArithmeticError, ValueError):
        return
    assert result["upper"]["value"] == pytest.approx(0.6666666666888889, abs=1e-10)


def test_unnormalized_weights_and_normalized_rn_are_distinct():
    result = normalized_bounds([0.3, 0.7], [1, 0], [1, 0], [0.5, 2], [0.5, 2])
    endpoint = result["lower"]
    assert endpoint["normalizer"] == pytest.approx(1.55)
    assert endpoint["value"] == pytest.approx(0.15 / 1.55)
    assert endpoint["normalized_rn_witness"] == pytest.approx([0.5 / 1.55, 2 / 1.55])


def test_ratio_scale_invariance_with_scaled_constraints():
    kwargs = dict(B=[[1, 0, 0]], d=[1.6], E=[[1, -1, 0]], f=[0])
    first = normalized_bounds(P, [0, 1, 0], [0, 1, 1], A, B, **kwargs)
    scale = 3.7
    second = normalized_bounds(P, [0, 1, 0], [0, 1, 1],
                               [scale * x for x in A], [scale * x for x in B],
                               B=[[1, 0, 0]], d=[scale * 1.6],
                               E=kwargs["E"], f=[0])
    for endpoint in ("lower", "upper"):
        assert first[endpoint]["value"] == pytest.approx(second[endpoint]["value"], abs=1e-10)


def test_retained_s02_values_have_separate_physical_row():
    result = retained_result()
    assert result["retained_event_masses"]["assumed_hard_ball"] == [0.14697265625, 0.95654296875]
    assert result["retained_event_masses"]["exact_working"] == 0.60302734375
    assert result["physical"]["Q_domain"] == "UNRESOLVED"
    assert result["physical"]["outer_bound"] == [0, 1]
    assert len(result["gamma_sweep"]) == 5
    for key in ("assumed_hard_ball", "exact_working"):
        lows = [row[key][0] for row in result["gamma_sweep"]]
        highs = [row[key][1] for row in result["gamma_sweep"]]
        assert lows == sorted(lows, reverse=True)
        assert highs == sorted(highs)
