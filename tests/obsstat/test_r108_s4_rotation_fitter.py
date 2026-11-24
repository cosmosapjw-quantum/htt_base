"""R108 lane s4: synthetic tests of the BJS template evaluator, roll decomposition and SO(3) rotation fitter.

The fitter of ``scripts/r108/s4_bjs_comparator.py`` must recover a known rotation and amplitude of an exactly
rotated ``bjs_temperature_sky`` map, prefer the correct handedness, and its fast spline evaluator must agree with
``bjs_temperature_sky``.  Also checks the admissible-state builder (constraints, H = 1, McEwen 2006 eq. A2).
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from bass.transport.hybrid_los_transfer import healpix_directions
from scripts.r108.s4_bjs_comparator import (
    GLOBAL_CHECK_TOL,
    TemplateSky,
    angle_deg,
    axis_rotation,
    build_bjs_state,
    euler_determined,
    euler_from_matrix,
    euler_zyz,
    fit_rotation,
    global_check,
    map_paths,
    rot_z,
    rotation_angle_deg,
    roll_basis,
    score_axis,
    stable_compensating_tilt_velocity,
)

pytest.importorskip("healpy")


@pytest.fixture(scope="module")
def tmpl():
    return TemplateSky(0.5, 0.8, "mcewen2006", n_theta=4097, n_quadrature=1024)


def test_euler_roundtrip_and_axis_rotation():
    R = euler_zyz(1.1, 2.0, -0.7)
    a, b, g = euler_from_matrix(R)
    assert np.allclose(euler_zyz(a, b, g), R, atol=1e-14)
    d = np.array([0.3, -0.5, 0.81])
    d /= np.linalg.norm(d)
    assert np.allclose(axis_rotation(d) @ np.array([0.0, 0.0, 1.0]), d, atol=1e-15)


def test_spline_evaluator_matches_bjs_temperature_sky(tmpl):
    m = healpix_directions(8) @ euler_zyz(0.4, 1.3, 2.2)
    for kappa in (1, -1):
        v = tmpl.validate(m, kappa)
        assert v["relative"] < 1e-8


def test_roll_decomposition_is_exact(tmpl):
    m = healpix_directions(8)
    s0, s90 = roll_basis(tmpl, m, 1)
    for gam in (0.3, -1.7, 2.9):
        rolled = tmpl.exact(m @ rot_z(gam), 1)  # S(Rz(-gamma) m) for row vectors m
        assert np.max(np.abs(rolled - (math.cos(gam) * s0 + math.sin(gam) * s90))) < 1e-8 * np.max(np.abs(rolled))


@pytest.mark.parametrize("kappa", [1, -1])
def test_fitter_recovers_known_rotation_and_amplitude(tmpl, kappa):
    dirs = healpix_directions(16)
    R_true = euler_zyz(1.1, 2.0, -0.7)
    amp_true = 3.3e-5
    y = amp_true * tmpl.exact(dirs @ R_true, kappa) + 1.7e-6  # constant offset must not matter
    r = fit_rotation(tmpl, kappa, dirs, y, grid_nside=8, n_starts=4)
    R_fit = np.asarray(r["rotation_matrix"])
    assert r["corr"] > 1.0 - 1e-9
    assert abs(r["amp"] / amp_true - 1.0) < 1e-5
    assert rotation_angle_deg(R_fit.T @ R_true) < 0.01
    # review S4-3: an independent finer grid + random restarts finds no better basin than the fit
    gc = r["global_check"]
    assert gc["corr_check_max_minus_corr_best"] <= GLOBAL_CHECK_TOL
    assert gc["passes"] and gc["n_checks_in_fit_basin"] >= 1
    assert gc["check_nside"] == 16 and gc["n_random_restarts"] == 8
    assert "global_check_refined_ge_grid" not in r
    wrong = fit_rotation(tmpl, -kappa, dirs, y, grid_nside=8, n_starts=4, exact_final=False, check=False)
    assert wrong["corr_spline"] < r["corr"] - 1e-3


def test_global_check_flags_a_fit_stuck_in_a_wrong_basin(tmpl):
    """The check must not be true by construction: handed a sub-optimal 'best' it reports a positive excess."""
    dirs = healpix_directions(16)
    R_true = euler_zyz(1.1, 2.0, -0.7)
    y = 3.3e-5 * tmpl.exact(dirs @ R_true, 1)
    d_true = R_true @ np.array([0.0, 0.0, 1.0])
    d_wrong = np.array([0.0, 0.0, 1.0]) if angle_deg(d_true, [0, 0, 1]) > 30.0 else np.array([1.0, 0.0, 0.0])
    corr_wrong = score_axis(tmpl, 1, d_wrong, dirs, y - y.mean())[0]
    gc = global_check(tmpl, 1, dirs, y, corr_wrong, d_wrong, check_nside=16, n_refine=4, n_random=4)
    assert gc["corr_check_max_minus_corr_best"] > 1e-3
    assert not gc["passes"]
    assert gc["angle_check_max_to_fit_axis_deg"] > 5.0
    assert gc["corr_check_max"] > 1.0 - 1e-9


def test_euler_determined_combination_near_gimbal_lock():
    for a, g in ((0.52, -1.02), (2.9, 0.4)):
        R = euler_zyz(a, math.pi - 2e-5, g)
        e = euler_determined(R)
        assert e["alpha_gamma_individually_ill_conditioned"] and e["combination"] == "alpha - gamma"
        assert abs(math.remainder(e["value_rad"] - (a - g), 2.0 * math.pi)) < 1e-8
        R0 = euler_zyz(a, 1e-5, g)
        e0 = euler_determined(R0)
        assert e0["combination"] == "alpha + gamma"
        assert abs(math.remainder(e0["value_rad"] - (a + g), 2.0 * math.pi)) < 1e-8
    generic = euler_determined(euler_zyz(1.1, 2.0, -0.7))
    assert not generic["alpha_gamma_individually_ill_conditioned"] and generic["combination"] is None


def test_map_tags_separate_richardson_runs():
    """Review S4-5a: a --richardson run must not write its main map under the production tag."""
    args = (0.3, 0.62, 1e-8, 64, 0.02, 1400, 1e-12, 1e-16)
    prod = map_paths(*args, richardson=False)
    rich = map_paths(*args, richardson=True)
    assert prod["main"] != rich["main"]
    files = {p for d in (prod, rich) for p in d.values() if p is not None}
    assert len(files) == 4
    assert prod["main"].name == "S4_map_O0.3_x0.62_s1e-08_ns64_st0.02_M1400_rt1e-12_at1e-16.npz"


def test_state_builder_constraints_and_vorticity_relation():
    st, info = build_bjs_state(0.3, 0.62, 1e-8)
    assert info["constraints_admissible"]
    assert abs(info["H_minus_1"]) < 1e-14
    assert abs(info["dust_speed"] / info["speed_closed_form"] - 1.0) < 1e-12
    # McEwen et al. 2006 eq. A2 holds for the repository vorticity when (sigma/H)_BJS = sigma_13/H = sigma_perp/sqrt(2)
    assert abs(info["dust_vorticity_over_H"] / (info["A2_omega_over_sigma"] * 1e-8 / math.sqrt(2.0)) - 1.0) < 1e-9


def test_stable_tilt_root_solves_the_quadratic():
    q = np.array([2.9e-8, 6.3e-9, 0.0])
    v = stable_compensating_tilt_velocity(q, eps_hat=0.9, p_hat=0.0)
    assert np.allclose(0.9 * v / (1.0 - v @ v), q, rtol=1e-14, atol=0.0)
