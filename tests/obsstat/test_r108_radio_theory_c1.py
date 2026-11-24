"""Fast synthetic tests for scripts/r108/radio_theory_c1.py (no CAMB needed; < 30 s)."""
from __future__ import annotations

import math

import numpy as np
import pytest
from scipy import special

from scripts.r108 import radio_theory_c1 as T

H0C = 67.66 / T.C_KM_S  # 1/Mpc


def toy_background(zmax=1.2):
    """Static toy background: chi = z / (H0/c), H/c = H0/c, D = 1 (enough for the k^-2 identity)."""
    z = np.linspace(0.0, zmax, 2001)
    return T.Background(z, z / H0C, np.full_like(z, H0C), growth=np.ones_like(z), omega_m=0.3, h0c=H0C)


def gaussian_nz(bg, mu, sig):
    return lambda z: np.exp(-0.5 * ((bg.chi_of_z(z) - mu) / sig) ** 2) / bg.hubble_over_c(z)


@pytest.mark.parametrize("ell", [1, 2])
def test_kspace_matches_exact_realspace_identity_for_k_minus_2(ell):
    bg = toy_background()
    kern = T.Kernel(bg, gaussian_nz(bg, 2000.0, 400.0), lambda z: T.bias("unit", z), z_hi=1.2)
    kg = T.kgrid_log(1e-6, 0.5, 401)
    tpl = lambda k, z: np.full(np.shape(np.atleast_1d(z)), 1.0 / k)
    w = T.windows_for(kern, kg, tpl, ell, per_period=16)["density"]
    num = T.cl_from_windows(kg, w)
    chi = np.linspace(kern.chi_lo, kern.chi_hi, 200001)
    ref = T.realspace_powerlaw_m2(chi, kern.n_chi(chi), ell)
    assert abs(num / ref - 1) < 1e-4


def test_realspace_identity_thin_shell_limit():
    # Gaussian shell of width sig at r: C_l = A/((2l+1) r) [1 - (2l+1) sig/(sqrt(pi) r) + O((sig/r)^2)]
    # (first-order term from the cusp of chi_<^l/chi_>^(l+1) at chi = chi': E[max] - E[min] = 2 sig/sqrt(pi))
    r, sig = 3000.0, 2.0
    chi = np.linspace(r - 12 * sig, r + 12 * sig, 200001)
    n = np.exp(-0.5 * ((chi - r) / sig) ** 2)
    n /= np.trapezoid(n, chi)
    for ell in (1, 3):
        c = T.realspace_powerlaw_m2(chi, n, ell)
        expected = (1 - (2 * ell + 1) * sig / (math.sqrt(math.pi) * r)) / ((2 * ell + 1) * r)
        assert abs(c / expected - 1) < 1e-5


@pytest.mark.parametrize("ell", [1, 2, 3])
def test_second_derivative_of_spherical_bessel(ell):
    x = np.concatenate([np.logspace(-5, -3.01, 20), np.linspace(1e-3, 40, 400)])
    h = 1e-4
    xs = np.maximum(x, 2 * h)
    num = (special.spherical_jn(ell, xs + h) - 2 * special.spherical_jn(ell, xs) + special.spherical_jn(ell, xs - h)) / h ** 2
    got = T.sph_jn_dd(ell, xs)
    assert np.max(np.abs(got - num)) < 2e-5


def test_kernel_normalised_and_brackets():
    bg = toy_background(zmax=1.2)
    kern = T.Kernel(bg, lambda z: T.nz_shape("TN16", z), lambda z: T.bias("NT15", z), z_hi=1.2)
    chi = np.linspace(kern.chi_lo, kern.chi_hi, 100001)
    assert abs(np.trapezoid(kern.n_chi(chi), chi) - 1) < 1e-6
    zr = T.dz10_root()
    assert 3.7 < zr < 3.8
    assert T.nz_shape("DZ10", np.array([zr + 0.01]))[0] == 0.0
    assert T.nz_shape("DZ10", np.array([0.0]))[0] == pytest.approx(1.29)
    b = T.bias("NT15cap", np.array([1.5, 3.0]))
    assert b[0] == b[1] == pytest.approx(0.33 * 2.25 + 0.85 * 1.5 + 1.6)


def test_dipole_conventions():
    # per-component RMS sqrt(3 C1/4pi) and TN16 Eq. 3.9 C1 = (4pi/9) D^2 agree for a random dipole
    c1 = 1e-5
    d_rms_component = math.sqrt(3 * c1 / (4 * math.pi))
    assert (4 * math.pi / 9) * (3 * d_rms_component ** 2) == pytest.approx(c1)


def test_lensing_efficiency_starts_at_observer():
    # g(chi) = int_chi n(chi_s)(chi_s - chi)/chi_s: g(0) = 1 and g decreases to 0 at the far edge, also for a window with z_lo > 0
    bg = toy_background()
    kern = T.Kernel(bg, gaussian_nz(bg, 2000.0, 200.0), lambda z: T.bias("unit", z), z_lo=0.2, z_hi=1.2)
    assert kern.g_lens(np.array([0.0]))[0] == pytest.approx(1.0, rel=1e-4)
    chi = np.linspace(0, kern.chi_hi, 50)
    g = kern.g_lens(chi)
    assert np.all(np.diff(g) <= 1e-9) and g[-1] < 1e-6


def _v3_rows(amp_by_window, exponent=-1.4, sign=-1.0, ells=range(2, 11)):
    return [dict(nz=w, ell=ell, density=dict(rel=sign * a * ell ** exponent)) for w, a in amp_by_window.items() for ell in ells]


def test_v3_low_l_systematic_recovers_power_law_and_is_one_sided_upward():
    rows = _v3_rows({"wA": 0.07, "wB": 0.22})
    s = T.v3_low_l_systematic(rows)
    assert s["worst_window"] == "wB"
    assert s["per_window"]["wB"]["power_law_exponent"] == pytest.approx(-1.4, rel=1e-12)
    assert s["s_abs_rel_l1"] == pytest.approx(0.22, rel=1e-12)
    assert s["integrator_below_camb_at_every_tested_l"]
    assert s["factor_up"] == pytest.approx(1.0 / (1.0 - 0.22)) and s["factor_up"] > 1.22
    assert s["factor_down"] == 1.0
    env = dict(primary_min=1.0, extended_min=0.5, primary_max=2.0, extended_max=3.0, differential_pair_max=dict(C1=4.0),
               differential_triangle_bound_4max=12.0)
    app = T.apply_v3_systematic(env, s)
    assert app["extended_max"] == pytest.approx(3.0 * s["factor_up"]) and app["extended_min"] == 0.5
    assert app["differential_pair_max"] == pytest.approx(4.0 * s["factor_up"])


def test_v3_low_l_systematic_signs_and_cap():
    pos = T.v3_low_l_systematic(_v3_rows({"w": 0.1}, sign=1.0))
    assert pos["factor_up"] == 1.0 and pos["factor_down"] == pytest.approx(1 / 1.1)
    mixed = _v3_rows({"w": 0.1}) + _v3_rows({"v": 0.05}, sign=1.0)
    m = T.v3_low_l_systematic(mixed)
    assert m["factor_up"] == pytest.approx(1 / 0.9) and m["factor_down"] == pytest.approx(1 / 1.1)
    with pytest.raises(ValueError):
        T.v3_low_l_systematic(_v3_rows({"w": 0.6}))


def test_v3_gap_label():
    from scripts.r108 import radio_v3_diag as V

    assert V.gap_label(6e-5, 1.4e-3, -0.077).startswith("unexplained (not integrator")
    assert V.gap_label(2e-3, 1.4e-3, -0.077).startswith("not resolved: integrator")
    assert "CAMB accuracy" in V.gap_label(6e-5, 0.01, -0.077)
