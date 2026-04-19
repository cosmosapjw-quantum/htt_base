"""
Test suite: baryon_only_policy.beta_policy_gate (Week 3 Day 2, merged v4.1)
===========================================================================

VT-07 frame-attribution-corrected safe-route gate. Condition:
    |β| ≤ safety_margin × ε_1 / (1 + η_{u̇})

Target: ~15 tests across 4 classes:
  1. TestBoundary       (pass/fail at threshold, VER06 production check)
  2. TestScaling        (safety_margin, η_{u̇}, ε_1 effects)
  3. TestInputValidation (malformed inputs)
  4. TestDiagnostics    (returned dict shape + values)
"""
from __future__ import annotations

import pytest

from bass.tilt.baryon_only_policy import (
    beta_policy_gate,
    BETA_SAFETY_MARGIN_DEFAULT,
)


# ============================================================================
# Test Class 1 - Boundary behaviour
# ============================================================================

class TestBoundary:
    """Pass/fail at and near the threshold."""

    def test_passes_when_well_below_threshold(self):
        # threshold = 0.5 * 0.02 / (1 + 0.16) = 8.62e-3, |β| = 1.36e-3
        passed, diag = beta_policy_gate(
            beta=1.36e-3, epsilon_1=0.02, eta_u_dot=0.16,
        )
        assert passed is True
        assert diag["fractional_slack"] > 0

    def test_fails_when_above_threshold(self):
        # threshold = 0.5 * 1e-3 / 1.16 = 4.31e-4, |β| = 1.36e-3 fails
        passed, diag = beta_policy_gate(
            beta=1.36e-3, epsilon_1=1e-3, eta_u_dot=0.16,
        )
        assert passed is False
        assert diag["fractional_slack"] < 0

    def test_passes_exactly_at_threshold(self):
        # Construct β = safety_margin × ε_1 / (1 + η), expect pass (inclusive)
        eps_1, eta = 0.02, 0.16
        smgn = BETA_SAFETY_MARGIN_DEFAULT
        beta_at_threshold = smgn * eps_1 / (1.0 + eta)
        passed, diag = beta_policy_gate(
            beta=beta_at_threshold, epsilon_1=eps_1, eta_u_dot=eta,
        )
        assert passed is True
        assert abs(diag["fractional_slack"]) < 1e-12

    def test_sign_of_beta_is_immaterial(self):
        # The gate compares |β|; sign should not affect pass/fail
        passed_pos, _ = beta_policy_gate(1e-3, 0.02, 0.16)
        passed_neg, _ = beta_policy_gate(-1e-3, 0.02, 0.16)
        assert passed_pos == passed_neg

    def test_VER06_production_values_pass_at_reasonable_eps(self):
        # Production β = 1.36e-3. For the gate to pass at default safety
        # margin 0.5, ε_1 / (1 + η_{u̇}) must exceed 2.72e-3.
        # Plausible production values: ε_1 = 0.02, η_{u̇} = 0.16 → 1.72e-2
        # (well above). Document the production pass case.
        passed, _ = beta_policy_gate(1.36e-3, 0.02, 0.16)
        assert passed, "VER06 production β must clear VT-07 gate"


# ============================================================================
# Test Class 2 - Scaling
# ============================================================================

class TestScaling:
    """Threshold scales correctly with safety_margin, ε_1, η_{u̇}."""

    def test_safety_margin_halves_threshold(self):
        _, diag_full = beta_policy_gate(
            1e-3, 0.02, 0.16, safety_margin=1.0,
        )
        _, diag_half = beta_policy_gate(
            1e-3, 0.02, 0.16, safety_margin=0.5,
        )
        assert diag_half["threshold"] == pytest.approx(
            0.5 * diag_full["threshold"], rel=1e-14,
        )

    def test_larger_eta_u_dot_tightens_threshold(self):
        _, diag_small_eta = beta_policy_gate(1e-3, 0.02, 0.0)
        _, diag_large_eta = beta_policy_gate(1e-3, 0.02, 1.0)
        # Larger η_{u̇} → smaller threshold
        assert diag_large_eta["threshold"] < diag_small_eta["threshold"]
        # Specifically: ratio should be 1 / 2 since 1/(1+0) vs 1/(1+1)
        assert diag_large_eta["threshold"] == pytest.approx(
            0.5 * diag_small_eta["threshold"], rel=1e-14,
        )

    def test_larger_epsilon_relaxes_threshold(self):
        _, diag_a = beta_policy_gate(1e-3, 0.01, 0.0)
        _, diag_b = beta_policy_gate(1e-3, 0.02, 0.0)
        assert diag_b["threshold"] == pytest.approx(
            2 * diag_a["threshold"], rel=1e-14,
        )

    def test_eta_u_dot_zero_yields_safety_margin_times_eps_1(self):
        _, diag = beta_policy_gate(
            1e-3, 0.02, 0.0, safety_margin=1.0,
        )
        assert diag["threshold"] == pytest.approx(0.02, rel=1e-14)


# ============================================================================
# Test Class 3 - Input validation
# ============================================================================

class TestInputValidation:
    """Malformed inputs raise ValueError with informative messages."""

    def test_rejects_zero_epsilon_1(self):
        with pytest.raises(ValueError, match="epsilon_1"):
            beta_policy_gate(1e-3, 0.0, 0.16)

    def test_rejects_negative_epsilon_1(self):
        with pytest.raises(ValueError, match="epsilon_1"):
            beta_policy_gate(1e-3, -0.01, 0.16)

    def test_rejects_negative_eta_u_dot(self):
        with pytest.raises(ValueError, match="eta_u_dot"):
            beta_policy_gate(1e-3, 0.02, -0.1)

    def test_rejects_zero_safety_margin(self):
        with pytest.raises(ValueError, match="safety_margin"):
            beta_policy_gate(1e-3, 0.02, 0.16, safety_margin=0.0)

    def test_rejects_safety_margin_above_1(self):
        with pytest.raises(ValueError, match="safety_margin"):
            beta_policy_gate(1e-3, 0.02, 0.16, safety_margin=1.5)


# ============================================================================
# Test Class 4 - Diagnostics shape
# ============================================================================

class TestDiagnostics:
    """Returned diagnostic dict carries all documented keys."""

    REQUIRED_KEYS = {
        "beta", "epsilon_1", "eta_u_dot", "safety_margin",
        "threshold", "fractional_slack",
    }

    def test_diagnostic_keys_complete(self):
        _, diag = beta_policy_gate(1e-3, 0.02, 0.16)
        assert set(diag.keys()) == self.REQUIRED_KEYS

    def test_diagnostic_values_are_floats(self):
        _, diag = beta_policy_gate(1e-3, 0.02, 0.16)
        for key in self.REQUIRED_KEYS:
            assert isinstance(diag[key], float), (
                f"{key} should be float, got {type(diag[key])}"
            )

    def test_returns_tuple_shape_for_canonical_decision(self):
        # Compatibility with make_canonical_decision's expected input
        result = beta_policy_gate(1e-3, 0.02, 0.16)
        assert isinstance(result, tuple) and len(result) == 2
        assert isinstance(result[0], bool) and isinstance(result[1], dict)
