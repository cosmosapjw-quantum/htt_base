"""R106 NVSS null-mock review helpers: C_1 option, l=1 dipole, closed-form C_1 dependence, amplitude nuisance."""
import math

import healpy as hp
import numpy as np
from numpy.testing import assert_allclose

from scripts.r106 import radio_null_mocks as rn


def test_diff_spectrum_c1_scale_only_touches_l1_and_is_identity_at_one():
    for kind in ("red", "mid", "flat"):
        base = rn.spectrum(0.0123, kind)
        assert np.array_equal(rn.diff_spectrum(0.0123, kind, 1.0), base)
        zero = rn.diff_spectrum(0.0123, kind, 0.0)
        assert zero[1] == 0.0 and np.array_equal(zero[2:], base[2:]) and zero[0] == 0.0
        assert_allclose(rn.diff_spectrum(0.0123, kind, 0.3)[1], 0.3 * base[1], rtol=0, atol=0)
    for bad in (-0.1, np.nan):
        try:
            rn.diff_spectrum(1.0, "red", bad)
        except ValueError:
            continue
        raise AssertionError("invalid c1_scale accepted")


def test_l1_dipole_matches_healpy_map_of_field_construction():
    nside, lmax, c1 = 8, 4, 0.37
    ell, emm = hp.Alm.getlm(lmax)
    rng = np.random.default_rng(106)
    z = rng.standard_normal((2, len(ell)))
    cl = np.zeros(lmax + 1)
    cl[1] = c1
    amp = np.sqrt(cl[ell])
    alm = np.where(emm == 0, amp * z[0], amp * (z[0] + 1j * z[1]) / np.sqrt(2.0)).astype(complex)  # as rn.field
    m = hp.alm2map(alm, nside, lmax=lmax)
    v = np.array(hp.pix2vec(nside, np.arange(hp.nside2npix(nside))))
    coef, *_ = np.linalg.lstsq(np.column_stack([np.ones(v.shape[1]), v[0], v[1], v[2]]), m, rcond=None)
    assert_allclose(rn.l1_dipole_xy(z, c1, lmax), coef[1:3], rtol=1e-10, atol=1e-12)
    # per-component variance 3 C_1 / 4 pi
    zz = rng.standard_normal((4000, 2, len(ell)))
    d = np.array([rn.l1_dipole_xy(x, c1, lmax) for x in zz])
    assert_allclose(d.var(axis=0), 3 * c1 / (4 * np.pi), rtol=0.08)


def test_offdiag_fraction_contrast_on_r65_joint_counts():
    j = [[1172716, 20345, 808, 113], [0, 106785, 11795, 434], [0, 0, 59520, 6782], [0, 0, 0, 56576]]
    out = rn.offdiag_fraction_contrast(j)
    f_peak = (11795 + 434 + 6782) / (106785 + 11795 + 434 + 59520 + 6782 + 56576)
    f_int = (20345 + 808 + 113 + 11795 + 434 + 6782) / (20345 + 106785 + 808 + 11795 + 59520 + 113 + 434 + 6782 + 56576)
    assert_allclose([out["f_off_peak"], out["f_off_integrated"], out["df"]], [f_peak, f_int, f_int - f_peak], rtol=1e-14)
    cube = np.zeros((4, 4, 3))
    cube[..., 0] = np.array(j)
    assert_allclose(rn.offdiag_fraction_contrast(cube)["df"], out["df"], rtol=1e-14)


def test_gaussian_closed_form_crossing_solves_wald_equation():
    cov0 = np.array([[2.0e-6, 3.0e-7], [3.0e-7, 1.5e-6]])
    d, df = np.array([-1.4e-3, 5.6e-3]), 0.0745
    for alpha in (0.05, 0.01):
        c1 = rn.c1_crossing_gaussian(d, cov0, df, alpha, 1.0)
        assert c1 > 0
        assert_allclose(rn.wald(d, rn.closed_form_cov(cov0, df, c1)), -2 * math.log(alpha), rtol=1e-9)
    assert rn.c1_crossing_gaussian(1e-6 * d, cov0, df, 0.05, 1.0) == 0.0
    assert rn.c1_crossing_gaussian(d, cov0, df, 0.05, 1e-9) is None
    assert_allclose(rn.closed_form_cov(cov0, df, 0.01) - cov0, df ** 2 * 3 * 0.01 / (4 * np.pi) * np.eye(2), rtol=1e-14)


def test_semi_analytic_tself_and_crossing_against_chi2_law():
    rng = np.random.default_rng(2026)
    n, s0, df, tobs = 6000, 1.0e-3, 0.075, 20.0
    d0 = s0 * rng.standard_normal((n, 2))
    u = rng.standard_normal((n, 2)) * math.sqrt(3 / (4 * math.pi))
    prec = np.broadcast_to(np.eye(2) / s0 ** 2, (n, 2, 2))
    coeffs = rn.tself_coefficients(d0, prec, u, df)
    c1 = 2.3e-3
    x = d0 + df * math.sqrt(c1) * u
    assert_allclose(rn.tself_curve(coeffs, [c1])[0], np.einsum("ni,nij,nj->n", x, prec, x), rtol=1e-12)
    # delta ~ N(0, (s0^2 + df^2 3 C_1/4pi) I): p(t >= tobs) = exp(-tobs s0^2 / (2 (s0^2 + df^2 3 C_1/4pi)))
    for alpha in (0.05, 0.01):
        want = s0 ** 2 * (tobs / (-2 * math.log(alpha)) - 1) / (df ** 2 * 3 / (4 * math.pi))
        got, _ = rn.c1_crossing_mc(coeffs, tobs, alpha, 1.0)
        assert abs(got / want - 1) < 0.2, (alpha, got, want)


def test_amplitude_ratio_draws_are_deterministic_positive_and_match_quantiles():
    sigma = 0.25
    r = np.array([rn.draw_amplitude_ratio([1, 500, 3, i], sigma) for i in range(4000)])
    assert np.all(r > 0) and rn.draw_amplitude_ratio([1, 500, 3, 7], sigma) == r[7]
    q = rn.amplitude_ratio_quantiles(sigma)
    assert_allclose(np.quantile(r, [0.16, 0.5, 0.84]), q, atol=0.02)
    assert_allclose(q[1], 1.0, atol=1e-3)
    assert rn.p_display(0, 1000) == "0.001 (0/1000)"
