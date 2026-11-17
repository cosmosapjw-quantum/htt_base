"""Finite construction checks; not survey coverage or a physical H inference."""
import numpy as np
import pytest
from scipy.stats import chi2

from htt.htt.infer import r54_distance_estimators as de
from htt.htt.infer import r58_mixed_tensor_likelihood as mt
from htt.htt.infer import r64_directional_hubble as dh


def _directions(rng, count):
    n = rng.normal(size=(count, 3))
    return n / np.linalg.norm(n, axis=1)[:, None]


def _simple_fit(degree=2, coefficient_sd=.0001):
    p = 3+9*(degree+1)
    theta = np.zeros(p)
    theta[3] = np.log(67.36)
    theta[12:21] = np.linspace(-.001, .001, 9)
    cov = np.diag(np.r_[np.full(3, 30.**2), np.full(p-3, coefficient_sd**2)])
    fit = mt.fit_linear(theta, cov, np.eye(p), parameter_scale=np.r_[np.full(3, 300.), np.full(p-3, .01)])
    return theta, cov, fit


def test_legendre_jet_exact_and_shapes():
    z = np.array([.01, .025, .055, .08, .1])
    t = (z-.055)/.045
    p, first, second = dh.radial_jet(z, 3)
    np.testing.assert_allclose(p, np.stack([np.ones_like(t), t, (3*t*t-1)/2, (5*t**3-3*t)/2], axis=-1), atol=2e-15)
    np.testing.assert_allclose(first*.045, np.stack([t*0, t*0+1, 3*t, (15*t*t-3)/2], axis=-1), atol=2e-15)
    np.testing.assert_allclose(second*.045**2, np.stack([t*0, t*0, t*0+3, 15*t], axis=-1), atol=2e-14)
    assert dh.radial_jet(.04, 0)[0].shape == (1,)


def test_source_design_preserves_velocity_units_and_tensor_basis():
    rng = np.random.default_rng(64)
    z, n = np.linspace(.011, .099, 50), _directions(rng, 50)
    bg = dh.background_factors(z, .3153)
    g = ((1+z)/(bg['E']*bg['chi_hat'])-1)/dh.C_KM_S
    x = dh.source_design(z, n, g, 2)
    theta = rng.normal(size=30)
    b, p = de.multipole_basis(n), dh.radial_jet(z, 2)[0]
    expected = g*np.sum(n*theta[:3], axis=1) + sum(p[:, j]*(b@theta[3+9*j:12+9*j]) for j in range(3))
    np.testing.assert_allclose(x@theta, expected, atol=5e-15)
    for i in [0, 20, 49]:
        row = dh.field_rows(z[i], n[i], 2)[0]
        assert np.all(row[:3] == 0)
        np.testing.assert_allclose(row@theta, expected[i]-g[i]*(n[i]@theta[:3]), atol=5e-15)


def test_background_exact_de_sitter_and_eds_limits():
    z = np.array([0., .0001, .01, .08, 1.])
    ds, eds = dh.background_factors(z, 0.), dh.background_factors(z, 1.)
    np.testing.assert_allclose(ds['chi_hat'], z, atol=1e-15)
    np.testing.assert_allclose(eds['chi_hat'], 2*(1-1/np.sqrt(1+z)), atol=5e-16)
    np.testing.assert_allclose(eds['q_ref'], .5, atol=5e-16)
    np.testing.assert_allclose(ds['B_prime'], 1., atol=0)


def test_eta_repo_normalization_and_angular_calibration():
    theta, _, _ = _simple_fit()
    theta[12:] = 0.
    n = np.array([1., 0., 0.])
    first = dh.point_image(theta, .06, n, 2, .3153)
    bg = dh.background_factors(.06, .3153)
    assert first['H_D'] == pytest.approx(bg['H_ref'], rel=2e-15)
    assert first['q_D'] == pytest.approx(bg['q_ref'], abs=1e-15)
    altered = theta.copy()
    altered[3:12] += np.linspace(-.03, .04, 9)
    a = float(de.multipole_basis(n[None])[0]@(altered[3:12]-theta[3:12]))
    second = dh.point_image(altered, .06, n, 2, .3153)
    assert second['H_D']/first['H_D'] == pytest.approx(np.exp(a), rel=2e-15)
    assert second['q_D'] == first['q_D']
    assert dh.point_image(theta, .06, n, 2, .3153, H0=70.)['H_D'] == first['H_D']


def test_calibration_quotient_after_a_nontrivial_operator():
    rng = np.random.default_rng(6401)
    z, n = np.linspace(.011, .099, 120), _directions(rng, 120)
    bg = dh.background_factors(z, .3153)
    g = ((1+z)/(bg['E']*bg['chi_hat'])-1)/dh.C_KM_S
    src = dh.source_design(z, n, g, 1)
    op = rng.normal(size=(36, len(z))) / np.sqrt(len(z))
    x = op@src
    theta = np.r_[np.array([120., -50., 80.]), np.log(67.36), np.zeros(8), np.linspace(-.001, .001, 9)]
    cal = rng.normal(scale=.01, size=9)
    shift = op@de.multipole_basis(n)@cal
    kwargs = dict(parameter_scale=np.r_[np.full(3, 300.), np.full(18, .01)])
    fit = mt.fit_linear(x@theta, np.eye(36)*1e-8, x, **kwargs)
    shifted = mt.fit_linear(x@theta+shift, np.eye(36)*1e-8, x, **kwargs)
    assert fit['rank'] == 21
    at = np.array([0., 1., 0.])
    for row in dh.field_rows(.06, at, 1)[1:]:
        assert row@(shifted['estimate']-fit['estimate']) == pytest.approx(0., abs=2e-10)
    before = dh.radial_hubble_interval(fit, .08, .04, at, 1, .3153)
    after = dh.radial_hubble_interval(shifted, .08, .04, at, 1, .3153)
    assert before['status'] == after['status'] == 'OK'
    np.testing.assert_allclose([before['lower'], before['upper']], [after['lower'], after['upper']], rtol=1e-10)


def test_joint_support_enclosures_contain_finite_ellipsoid_witnesses():
    theta, cov, fit = _simple_fit()
    z, zr, n = .08, .04, np.array([0., 0., 1.])
    ratio = dh.radial_hubble_interval(fit, z, zr, n, 2, .3153)
    q = dh.q_interval(fit, z, n, 2, .3153)
    assert ratio['status'] == q['status'] == 'OK'
    rng = np.random.default_rng(6402)
    for _ in range(80):
        u = rng.normal(size=len(theta)); u /= np.linalg.norm(u)
        th = theta+np.sqrt(chi2.ppf(.95, len(theta)))*np.sqrt(np.diag(cov))*u
        a, b = dh.point_image(th, z, n, 2, .3153), dh.point_image(th, zr, n, 2, .3153)
        assert a['status'] == b['status'] == 'OK'
        assert ratio['lower'] <= a['H_D']/b['H_D'] <= ratio['upper']
        assert q['lower'] <= a['q_D'] <= q['upper']


def test_domain_failure_is_not_a_finite_interval():
    theta, _, fit = _simple_fit(coefficient_sd=.4)
    n = np.array([1., 0., 0.])
    assert dh.radial_hubble_interval(fit, .08, .04, n, 2, .3153)['status'] == 'DOMAIN_NOT_CERTIFIED'
    assert dh.q_interval(fit, .08, n, 2, .3153)['lower'] is None
    theta[12] = 10.
    point = dh.point_image(theta, .08, n, 2, .3153)
    assert point['status'] == 'NONPOSITIVE_DERIVATIVE'
    assert point['H_D'] is None and point['q_D'] is None


def test_scalar_radial_null_and_equal_redshift_identity_are_retained():
    # O z=0 is the exact mechanism of the inherited radial-nuisance operator.
    rng = np.random.default_rng(6403)
    z, n = np.linspace(.011, .099, 90), _directions(rng, 90)
    g = 1/(dh.C_KM_S*z)
    op = np.eye(len(z))-np.outer(z, z)/(z@z)
    x = op@dh.source_design(z, n, g, 1)
    fit = mt.fit_linear(np.zeros(len(z)), np.eye(len(z)), x,
                        parameter_scale=np.r_[np.full(3, 300.), np.full(18, .01)])
    assert fit['rank'] == 20
    target = dh.radial_difference_row(.08, .04, np.array([1., 0., 0.]), 1)
    assert not mt.linear_interval(fit, target)['identified']
    different = dh.radial_hubble_interval(fit, .08, .04, np.array([1., 0., 0.]), 1, .3153)
    same = dh.radial_hubble_interval(fit, .04, .04, np.array([1., 0., 0.]), 1, .3153)
    assert different['status'] == 'INGREDIENT_UNIDENTIFIED'
    assert same['status'] == 'DOMAIN_NOT_CERTIFIED'
    assert same['formal_equal_redshift_identity'] and same['identity_on_positive_domain'] == 1.
    assert same['lower'] is None


def test_milne_counterexample_through_exact_local_eta_jet():
    # Match the exact Milne eta jet at one point, using a polynomial only as
    # a local jet carrier. No claim that the whole Milne curve is quadratic.
    z, h0, n = .08, 70., np.array([1., 0., 0.])
    s = 1+z
    exactjet = [np.log(2*h0*s/(s+1)), 1/s-1/(s+1), -1/s**2+1/(s+1)**2]
    rows = dh.field_rows(z, n, 2)
    cols = [3, 12, 21]
    theta = np.zeros(30)
    theta[cols] = np.linalg.solve(np.stack(rows)[:, cols], exactjet)
    point = dh.point_image(theta, z, n, 2, 0., H0=h0)
    assert point['H_D'] == pytest.approx(2*h0*s*s/(s*s+1), rel=2e-15)
    assert point['q_D'] == pytest.approx((1-s*s)/(1+s*s), abs=1e-14)
    assert abs(point['H_D']-h0*s) > .1


def test_four_shell_values_do_not_identify_derivatives():
    z = np.array([.025, .04, .06, .08])
    p = np.polynomial.Polynomial.fit(z, 1/z, 3).convert()
    np.testing.assert_allclose(p(z), 1/z, atol=4e-13)
    derivative_null = -1/z**2-p.deriv()(z)
    expected = np.array([np.prod(zi-np.delete(z, i))/(zi*np.prod(z)) for i, zi in enumerate(z)])
    np.testing.assert_allclose(derivative_null, expected, rtol=2e-13, atol=2e-10)
    assert np.all(np.abs(derivative_null) > 1.)


@pytest.mark.parametrize('call', [
    lambda: dh.radial_jet([], 1), lambda: dh.radial_jet(.04, True),
    lambda: dh.radial_jet(-.04, 1), lambda: dh.radial_jet(np.nan, 1),
    lambda: dh.field_rows(.04, [1., 0., np.nan], 1),
    lambda: dh.field_rows(.04, [2., 0., 0.], 1),
    lambda: dh.source_design([.04], [[1., 0., 0.]], [np.inf], 1),
    lambda: dh.source_design([.04], [[1., 0., 0.]], [[.001]], 1),
    lambda: dh.background_factors(.04, -1.), lambda: dh.background_factors(2., .3153),
    lambda: dh.background_factors(.04, .3153, H0=0.),
    lambda: dh.point_image(np.zeros(20), .04, [1., 0., 0.], 1, .3153),
])
def test_invalid_input_is_rejected(call):
    with pytest.raises(ValueError):
        call()
