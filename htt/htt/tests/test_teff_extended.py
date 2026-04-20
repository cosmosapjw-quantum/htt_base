"""HTT teff_extended regression guards."""
from __future__ import annotations

import pytest

from htt.core.teff_extended import _a2_coefficient_table


def test_a2_coefficient_table_matches_theta4_bridge_identity():
    coeffs = _a2_coefficient_table()
    assert coeffs[(0, 1)] == pytest.approx(4.0)
    assert coeffs[(2, 0)] == pytest.approx(4.0)
    assert coeffs[(0, 2)] == pytest.approx(12.0 / 7.0)
    assert coeffs[(2, 1)] == pytest.approx(44.0 / 7.0)


def test_a2_coefficient_table_returns_fresh_copy():
    coeffs = _a2_coefficient_table()
    coeffs[(0, 1)] = -1.0
    assert _a2_coefficient_table()[(0, 1)] == pytest.approx(4.0)
