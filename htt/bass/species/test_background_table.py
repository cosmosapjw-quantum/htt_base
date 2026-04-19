"""Tests for bass/species/background_table.py (LB-1) — FLRW table builder."""
from __future__ import annotations

import numpy as np
import pytest

from bass.species.background_table import (
    FLRWBackgroundTable,
    build_flrw_background_table,
)
from bass.species.constants import default_constants


def test_a_endpoint_is_exactly_one():
    """a[-1] = 1.0 exactly (required for T-22)."""
    t = build_flrw_background_table()
    assert t.a[-1] == 1.0


def test_eta_is_monotone_increasing():
    t = build_flrw_background_table(n_eta=1000)
    assert np.all(np.diff(t.eta) > 0)


def test_z_equals_inverse_a_minus_one():
    t = build_flrw_background_table(n_eta=500)
    np.testing.assert_allclose(t.z, 1.0 / t.a - 1.0, rtol=1e-15)


def test_calH_equals_a_times_H_mpc():
    t = build_flrw_background_table(n_eta=500)
    np.testing.assert_allclose(t.calH_mpc, t.a * t.H_mpc, rtol=1e-15)


def test_Theta_equals_three_H_mpc():
    t = build_flrw_background_table(n_eta=500)
    np.testing.assert_allclose(t.Theta, 3.0 * t.H_mpc, rtol=1e-15)


def test_H_at_a_eq_1_matches_H0():
    t = build_flrw_background_table()
    assert t.H_mpc[-1] == pytest.approx(t.H0_mpc, rel=1e-15)


def test_eta_today_consistent_with_CAMB_range():
    """Sanity: η_0 is ≈ 14100-14200 Mpc (Planck 2018 CAMB reference)."""
    t = build_flrw_background_table()
    assert 14000.0 < t.eta_today < 14300.0


def test_a_spline_recovers_grid_points():
    t = build_flrw_background_table(n_eta=500)
    for idx in (0, 50, 250, 400, 499):
        assert t.interp_a(t.eta[idx]) == pytest.approx(t.a[idx], rel=1e-12)


def test_check_range_raises_beyond_bounds():
    t = build_flrw_background_table()
    with pytest.raises(ValueError):
        t.interp_a(t.eta_today + 1.0e3)
    with pytest.raises(ValueError):
        t.interp_a(t.eta_min - 1.0e3)


def test_build_validates_a_start_range():
    with pytest.raises(ValueError):
        build_flrw_background_table(a_start=0.0)
    with pytest.raises(ValueError):
        build_flrw_background_table(a_start=1.5)


def test_build_validates_n_eta():
    with pytest.raises(ValueError):
        build_flrw_background_table(n_eta=50)


def test_eta_at_a_inverts_a_of_eta():
    """eta_at_a is the inverse of a spline along the grid.

    Tolerance 1e-4 because eta_at_a uses linear interpolation on the
    (a, η) pair while interp_a uses cubic spline — the two inversions
    together accumulate a ≲1e-5 round-trip error. The function is
    intended for locating η at a target a, not for bit-exact inversion.
    """
    t = build_flrw_background_table(n_eta=2000)
    for a_t in (1e-6, 1e-3, 0.1, 0.5, 0.9, 0.999):
        eta = t.eta_at_a(a_t)
        a_back = t.interp_a(eta)
        assert a_back == pytest.approx(a_t, rel=1e-4)


def test_custom_constants_propagate():
    """Passing custom SpeciesConstants is respected."""
    c = default_constants()
    t = build_flrw_background_table(constants=c, n_eta=500)
    assert t.constants is c
    assert t.H0_mpc == pytest.approx(c.H0_mpc, rel=1e-15)
