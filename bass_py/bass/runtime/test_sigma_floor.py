"""
Test suite: sigma_floor.sigma_min_gate (Week 3 Day 2, merged v4.1)
==================================================================

Sobolev-validity floor on Σ². Pass iff min(Σ²) ≥ floor (default 1e-6).

Target: ~12 tests across 4 classes:
  1. TestScalarInput    (single-value semantics)
  2. TestArrayInput     (multi-value, argmin localization)
  3. TestInputValidation (negative values, empty array, bad floor)
  4. TestDiagnostics    (dict shape, tuple compatibility)
"""
from __future__ import annotations

import numpy as np
import pytest

from bass.runtime.sigma_floor import sigma_min_gate, SIGMA_FLOOR_DEFAULT


# ============================================================================
# Test Class 1 - Scalar input
# ============================================================================

class TestScalarInput:
    """Single-value Σ² semantics."""

    def test_scalar_well_above_floor_passes(self):
        passed, diag = sigma_min_gate(1e-4)
        assert passed is True
        assert diag["margin_factor"] == pytest.approx(100.0, rel=1e-14)

    def test_scalar_well_below_floor_fails(self):
        passed, diag = sigma_min_gate(1e-9)
        assert passed is False
        assert diag["margin_factor"] < 1.0

    def test_scalar_exactly_at_floor_passes(self):
        # The gate is inclusive: >= floor
        passed, diag = sigma_min_gate(SIGMA_FLOOR_DEFAULT)
        assert passed is True
        assert diag["margin_factor"] == pytest.approx(1.0, rel=1e-14)

    def test_scalar_just_below_floor_fails(self):
        passed, _ = sigma_min_gate(SIGMA_FLOOR_DEFAULT * 0.99)
        assert passed is False


# ============================================================================
# Test Class 2 - Array input
# ============================================================================

class TestArrayInput:
    """Array semantics: min governs pass, argmin reported."""

    def test_array_all_above_floor_passes(self):
        arr = np.array([1e-4, 1e-5, 1e-3, 1e-5])
        passed, diag = sigma_min_gate(arr)
        assert passed is True
        assert diag["sigma_min"] == pytest.approx(1e-5, rel=1e-14)
        assert diag["n_samples"] == 4

    def test_array_one_below_floor_fails(self):
        arr = np.array([1e-4, 1e-5, 1e-8, 1e-3])
        passed, diag = sigma_min_gate(arr)
        assert passed is False
        assert diag["argmin_index"] == 2
        assert diag["sigma_min"] == pytest.approx(1e-8, rel=1e-14)

    def test_argmin_identifies_first_minimum_for_ties(self):
        # numpy argmin returns the first occurrence for ties
        arr = np.array([5e-5, 1e-9, 1e-5, 1e-9])
        _, diag = sigma_min_gate(arr)
        assert diag["argmin_index"] == 1

    def test_2d_array_flattened_index(self):
        arr = np.array([[1e-5, 1e-4], [1e-9, 1e-3]])
        passed, diag = sigma_min_gate(arr)
        assert passed is False
        assert diag["argmin_index"] == 2  # row-major flat index of [1][0]
        assert diag["n_samples"] == 4

    def test_single_element_array_equivalent_to_scalar(self):
        scalar_p, scalar_d = sigma_min_gate(1e-5)
        array_p, array_d = sigma_min_gate(np.array([1e-5]))
        assert scalar_p == array_p
        assert scalar_d["sigma_min"] == array_d["sigma_min"]
        assert array_d["n_samples"] == 1


# ============================================================================
# Test Class 3 - Input validation
# ============================================================================

class TestInputValidation:
    """Malformed inputs raise ValueError."""

    def test_rejects_zero_floor(self):
        with pytest.raises(ValueError, match="floor"):
            sigma_min_gate(1e-5, floor=0.0)

    def test_rejects_negative_floor(self):
        with pytest.raises(ValueError, match="floor"):
            sigma_min_gate(1e-5, floor=-1e-6)

    def test_rejects_negative_sigma_squared(self):
        with pytest.raises(ValueError, match="non-negative"):
            sigma_min_gate(-1e-5)

    def test_rejects_negative_in_array(self):
        with pytest.raises(ValueError, match="non-negative"):
            sigma_min_gate(np.array([1e-5, -1e-7, 1e-4]))

    def test_rejects_empty_array(self):
        with pytest.raises(ValueError, match="empty"):
            sigma_min_gate(np.array([]))


# ============================================================================
# Test Class 4 - Diagnostics and tuple shape
# ============================================================================

class TestDiagnostics:
    """Diagnostic dict keys + canonical_decision compatibility."""

    REQUIRED_KEYS = {
        "sigma_min", "floor", "margin_factor", "argmin_index", "n_samples",
    }

    def test_diagnostic_keys_complete(self):
        _, diag = sigma_min_gate(1e-5)
        assert set(diag.keys()) == self.REQUIRED_KEYS

    def test_returns_tuple_shape_for_canonical_decision(self):
        result = sigma_min_gate(1e-5)
        assert isinstance(result, tuple) and len(result) == 2
        assert isinstance(result[0], bool) and isinstance(result[1], dict)

    def test_custom_floor_reflected_in_diagnostic(self):
        custom = 1e-4
        _, diag = sigma_min_gate(5e-5, floor=custom)
        assert diag["floor"] == pytest.approx(custom, rel=1e-14)
        assert diag["margin_factor"] == pytest.approx(0.5, rel=1e-14)
