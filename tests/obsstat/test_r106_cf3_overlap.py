"""R106 CF3-overlap review helpers: tail records, cz-binned zero points, epsilon strata, heterogeneity, ReadMe counts."""
import numpy as np
import pytest
from numpy.testing import assert_allclose

from scripts.r106 import cf3_overlap as c3


def test_tail_record_add_one_and_resolution():
    rec = c3.tail_record(np.arange(10.), 2.)
    assert rec["replicates"] == 10 and rec["k_control_le_observed"] == 3 and rec["k_control_ge_observed"] == 8
    assert_allclose([rec["fraction_control_le_observed"], rec["p_le_plus_one"], rec["p_ge_plus_one"],
                     rec["resolution_1_over_R_plus_1"]], [.3, 4 / 11, 9 / 11, 1 / 11])
    lo = c3.tail_record(np.ones(4), 0.)
    assert lo["fraction_control_le_observed"] == 0. and lo["p_le_plus_one"] == pytest.approx(.2)


@pytest.mark.parametrize("ctl,obs", [(np.zeros(0), 1.), (np.ones(3), None), (np.ones(3), float("nan"))])
def test_tail_record_null_when_undefined(ctl, obs):
    rec = c3.tail_record(ctl, obs)
    assert rec["fraction_control_le_observed"] is None and rec["p_le_plus_one"] is None and rec["p_ge_plus_one"] is None


def test_czbin_zero_points_per_bin_and_fallback():
    cz = np.array([500., 900., 1500., 2500., 2600., 2700., 4100.])
    y = np.array([1., 3., 2., 10., 10., 10., 7.])
    sig = np.ones(7)
    c, fb = c3.czbin_zero_points(cz, y, sig, np.arange(7), width=2000., min_rows=3)
    glob = y.mean()
    assert fb == 1
    assert_allclose(c, [2., 2., 2., 10., 10., 10., glob])
    # only training rows define the zero point; held-out rows of the same bin inherit it
    c2, _ = c3.czbin_zero_points(cz, y, sig, np.array([0, 1, 2]), width=2000., min_rows=3)
    assert_allclose(c2, 2.)


def test_czbin_zero_points_inverse_variance():
    cz = np.full(3, 100.)
    c, fb = c3.czbin_zero_points(cz, np.array([0., 0., 3.]), np.array([1., 1., .5]), np.arange(3), min_rows=1)
    assert fb == 0 and c[0] == pytest.approx(3. * 4. / 6.)


def test_eps_quintile_strata_refines_without_mixing_bins():
    rng = np.random.default_rng(106)
    cz = np.r_[rng.uniform(0, 2000, 50), rng.uniform(2000, 4000, 50), [5000.] * 5]
    eps = rng.uniform(.05, .2, len(cz))
    base = np.repeat([0, 1, 2], [50, 50, 5])
    st = c3.eps_quintile_strata(base, cz, eps)
    assert np.array_equal(st // 5, base)
    assert set(np.unique(st[:50] % 5)) == {0, 1, 2, 3, 4} and np.all(st[100:] % 5 == 0)
    for q in range(5):
        assert np.sum(st[:50] % 5 == q) == 10


def test_heterogeneity_constant_and_inflated():
    h = c3.heterogeneity([1., 1., 1.], [.1, .2, .1])
    assert h["chi2_about_combined"] == pytest.approx(0.) and h["combined_err_inflated"] == pytest.approx(h["combined_err"])
    h = c3.heterogeneity([0., 1.], [.1, .1])
    assert h["combined"] == pytest.approx(.5) and h["chi2_about_combined"] == pytest.approx(50.) and h["dof"] == 1
    assert h["combined_err_inflated"] == pytest.approx(h["combined_err"] * np.sqrt(50.))
    assert h["p_value_homogeneous"] < 1e-10


def test_stratified_masks_counts_preserved():
    strata = np.repeat([3, 7, 9], [10, 5, 4])
    M = c3.stratified_masks(strata, {3: 4, 7: 5, 9: 0}, 20, np.random.default_rng(1))
    assert M.shape == (19, 20)
    assert np.all(M[strata == 3].sum(0) == 4) and np.all(M[strata == 7] == 1) and np.all(M[strata == 9] == 0)


def test_zero_point_record_observed_vs_controls():
    rec = c3.zero_point_record(2., 4., np.array([1., 1., 3.]), np.array([2., 2., 2.]), .1, np.array([.1, .2, .3]),
                               ["0-2000"], np.array([2.]), np.array([4.]), np.array([[1., 1., 3.]]),
                               np.array([[2., 2., 2.]]), np.array([3.]))
    assert rec["observed"] == .5 and rec["control"]["mean"] == pytest.approx(5 / 6)
    assert rec["control"]["k_control_le_observed"] == 2
    assert rec["per_cz_bin_2000kms"]["0-2000"]["observed"] == .5


def test_cf3_readme_counts_parse():
    text = ("    edition contained 8188 entries is now expanded to 17669 entries. The\n"
            "    3.6{mu}m obtained with the Spitzer Space Telescope and 8885 distances\n"
            "    based on the Fundamental Plane methodology from the Six Degree Field\n"
            "table2.dat     197      11508    Summary group properties\n"
            "table3.dat     406      17669    Individual galaxy properties\n"
            "  87- 90  F4.2  mag   e_DM-P   [0.5]?=0 One standard deviation uncertainty in\n")
    assert c3.cf3_readme_counts(text) == dict(table2_nests=11508, table3_galaxies=17669, sixdfgs_fp_distances=8885,
                                              e_DM_P_stated_mag=.5)
    with pytest.raises(ValueError):
        c3.cf3_readme_counts("no tables here")


def test_sky_match_position_only_route_ignores_cz():
    nr = c3.unit_gal([0., 0.], [0., 10.])
    nq = c3.unit_gal([0., 0.], [1. / 3600., 10. + 5. / 3600.])
    m = c3.sky_match(nq, np.array([1000., 1000.]), nr, np.array([9000., 1000.]), arcsec=2., dv=np.inf)
    assert m["best"].tolist() == [0, -1] and m["dv_kms"][0] == pytest.approx(8000.)
    gated = c3.sky_match(nq, np.array([1000., 1000.]), nr, np.array([9000., 1000.]), arcsec=2., dv=500.)
    assert gated["best"].tolist() == [-1, -1]
