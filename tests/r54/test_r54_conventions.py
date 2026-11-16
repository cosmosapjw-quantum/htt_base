"""R54 sign, frame and cache conventions of the run scripts (gates MG-21..MG-28, independent diff review R54-IR-01..05).

Each test protects one convention that a regenerated result would otherwise carry silently:
frame closure sign (R54-EQ-38), hemisphere-step magnitude sign (R54-EQ-36), the ICRS -> Galactic rotation,
the direction of the axis-locking tail, the E response sign (R54-EQ-04), the pair-sum cache key,
the reionization-only E functional (R54-EQ-01..04) and the magnitude map of the log estimator (R54-EQ-36).
"""
from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.integrate import solve_ivp

from htt.htt.infer import r54_distance_estimators as de
from htt.htt.infer import r54_type1_thomson as th

ROOT = Path(__file__).resolve().parents[2]
NPZ = ROOT / "docs/research_program/observational_publication_20261015/R50_OBSERVED_CONVERGENCE_20261115/R51/observed_carrier.npz"


def _module(rel: str, name: str):
    path = ROOT / rel
    for extra in (ROOT / "htt", ROOT / "htt/src", ROOT, path.parent):
        if str(extra) not in sys.path:
            sys.path.insert(0, str(extra))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def cf4():
    return _module("scripts/r54/run_r54_cf4_exact.py", "r54_conv_cf4")


@pytest.fixture(scope="module")
def lz():
    return _module("scripts/r54/run_r54_lowz_frames.py", "r54_conv_lowz")


@pytest.fixture(scope="module")
def cmb():
    return _module("scripts/r54/run_r54_cmb_type1.py", "r54_conv_cmb")


def test_mg21_eq38_tilt_closure_vanishes_for_one_frame_offset(cf4):
    """One matter-radiation frame offset: V_CF4 = -c beta_RM and c beta_excess = +c beta_RM, so the closure chi2 is zero."""
    c_beta = np.array([250.0, -120.0, 60.0])
    v = -c_beta
    cv, sb = np.diag([40.0, 50.0, 60.0]) ** 2, np.array([80.0, 90.0, 100.0])
    assert cf4.tilt_closure(v, cv, c_beta, sb) < 1e-20
    assert cf4.tilt_closure(c_beta, cv, c_beta, sb) > 20.0          # the same-sign pair is not a single frame offset


def test_mg22_eq36_north_modulus_offset_gives_negative_step_and_positive_delta_mu(cf4):
    """A +0.05 mag distance-modulus offset in the north lowers eta there: s < 0 and Delta mu(N - S) = +0.05."""
    rng = np.random.default_rng(20261116)
    nvec = rng.normal(size=(4000, 3))
    nvec /= np.linalg.norm(nvec, axis=1)[:, None]
    z = rng.uniform(0.01, 0.05, nvec.shape[0])
    y = de.log_distance_ratio(np.full(z.size, 30.0), z, 0.3153)["eta"]     # ln[y/d] at d(mu = 30); shift to eta = ln 70
    mu = 30.0 + 5.0 / math.log(10.0) * (y - math.log(70.0)) + 0.05 * (nvec[:, 2] >= 0.0)
    eta = de.log_distance_ratio(mu, z, 0.3153)["eta"]
    design = np.column_stack([np.ones(z.size), np.where(nvec[:, 2] >= 0.0, 1.0, -1.0)])
    step = float(de.wls_operator(design, np.ones(z.size))[1] @ eta)
    assert step < 0.0
    out = cf4.hemisphere_steps(np.full(4, step), np.eye(4) * 1e-8, np.zeros((4, 4)))
    for row in out["white"]["per_method"].values():
        assert math.isclose(row["delta_mu_north_minus_south_mag"], 0.05, rel_tol=1e-9)
    assert math.isclose(out["white"]["common_delta_mu_north_minus_south_mag"], 0.05, rel_tol=1e-9)


def test_mg23_icrs_to_galactic_rotation(lz):
    r = lz.R_I2G
    assert np.allclose(r @ r.T, np.eye(3), atol=1e-12) and math.isclose(np.linalg.det(r), 1.0, abs_tol=1e-12)
    l, b = lz.icrs_to_lb(np.array([0.0, 0.0, 1.0]))                         # north celestial pole
    assert abs(l - 122.932) < 0.01 and abs(b - 27.128) < 0.01
    gc = r.T @ np.array([1.0, 0.0, 0.0])                                    # Galactic centre in ICRS
    ra, dec = math.degrees(math.atan2(gc[1], gc[0])) % 360.0, math.degrees(math.asin(gc[2]))
    assert abs(ra - 266.405) < 0.01 and abs(dec + 28.936) < 0.01


def test_mg24_axis_locking_tail_is_small_for_a_pole_aligned_signal(cf4, lz):
    """The sky-fraction statistic is a lower tail: a signal locked to the pole gives a small tail."""
    dq = np.sort(np.concatenate([lz.block_rows("dipole"), lz.block_rows("quadrupole")]))
    theta = np.zeros(36)
    theta[dq] = lz.axis_template(lz.AXES_ICRS["equatorial_pole"]) @ np.array([0.05, 0.05])
    out = cf4.locking_null(theta, np.eye(36) * 1e-4, np.random.default_rng([20261116, 99]), 200)
    assert out["tails"]["sky_fraction_at_most_observed"] < 0.02


def test_mg25_eq04_ideal_e_response_has_the_sign_of_the_t_response(cmb):
    with np.load(NPZ, allow_pickle=False) as z:
        labels, j_ideal = [str(x) for x in z["mode_labels"]], z["response_J_ideal_135x5_uK"]
    t2, e2 = cmb.rows(labels, "T", (2,)), cmb.rows(labels, "E", (2,))
    j_e = cmb.ideal_e_response(j_ideal, t2, e2)
    assert np.array_equal(j_e[e2], j_ideal[t2]) and np.abs(j_ideal[t2]).max() > 0
    others = [i for i in range(135) if i not in e2]
    assert not np.any(j_e[others])


def test_mg26_pair_sum_cache_key_changes_under_row_permutation_and_positions(cf4):
    rng = np.random.default_rng(1)
    stack = rng.normal(size=(6, 50))
    assert str(cf4.operator_fingerprint(stack)) != str(cf4.operator_fingerprint(stack[[3, 4, 5, 0, 1, 2]]))
    n = rng.normal(size=(50, 3))
    r, grid = rng.uniform(10, 300, 50), np.linspace(0.0, 700.0, 11)
    assert cf4.model_key(n, r, grid) != cf4.model_key(n, r * 1.001, grid)
    assert cf4.model_key(n, r, grid) != cf4.model_key(n, r, np.linspace(0.0, 701.0, 11))


def test_mg27_reionization_only_e_equals_the_propagated_quadrupole(cmb):
    """E from reionization scattering alone of the z > 50 quadrupole: [P(tau_50)]_10 Theta(z = 50), checked by direct
    integration of R54-EQ-01/02 with the shear switched off at z = 50: E(0) - [P(tau_50)]_11 E(z = 50)."""
    tab = np.loadtxt(ROOT / "tests/fixtures/r54/planck18_tau_history.csv", delimiter=",", skiprows=1)
    bg = th.planck18_background()
    hist = th.OpticalDepthHistory(tab[:, 0], tab[:, 1], bg.e2)
    n_hi, n_re = -math.log1p(1.0e4), -math.log1p(50.0)

    def pf(n: float) -> float:
        return float(th.perfect_fluid_shear(bg, n)[0])

    def kappa(n: float) -> float:
        h = 1e-6
        a, b = min(n + h, 0.0), n - h
        return (hist.tau(b) - hist.tau(a)) / (a - b)

    def rhs(n, y):
        k, s = kappa(n), (pf(n) if n < n_re else 0.0)
        return [-s - k * (0.9 * y[0] + math.sqrt(6.0) / 10.0 * y[1]), -k * (math.sqrt(6.0) / 10.0 * y[0] + 0.4 * y[1])]

    first = solve_ivp(rhs, [n_hi, n_re], [0.0, 0.0], method="Radau", rtol=1e-9, atol=1e-14)
    th50, e50 = first.y[:, -1]
    second = solve_ivp(rhs, [n_re, 0.0], [th50, e50], method="Radau", rtol=1e-9, atol=1e-14)
    p = th.thomson_propagator(hist.tau(n_re))
    expected = second.y[1, -1] - p[1, 1] * e50
    assert math.isclose(cmb.reionization_only_e(pf, hist, n_hi, n_re), expected, rel_tol=1e-4)


def test_mg28_eq36_log_estimator_magnitude_map(lz):
    """For the log estimator (h_fit = 1) the magnitude of a dipole A is (5/ln10) |A| (R54-EQ-36)."""
    theta = np.zeros(36)
    a = np.array([0.02, -0.01, 0.015])
    for w in range(4):
        theta[9 * w + 1:9 * w + 4] = a
    an = np.zeros((36, 3))
    for w, d in enumerate((100.0, 160.0, 240.0, 320.0)):
        an[9 * w + 1:9 * w + 4] = -np.eye(3) / (300.0 * d)
    out = lz.analyse_window_multipoles(theta, np.eye(36) * 1e-6, an, 1.0, "synthetic", estimator="log")
    amp = float(np.linalg.norm(out["dipole"]["A_only"]["km_s_Mpc_icrs"]))
    assert math.isclose(out["dipole"]["A_only"]["equivalent_mag"], amp * 5.0 / math.log(10.0), rel_tol=1e-12)
    with pytest.raises(ValueError):
        lz.analyse_window_multipoles(theta, np.eye(36) * 1e-6, an, 70.0, "synthetic", estimator="log")
