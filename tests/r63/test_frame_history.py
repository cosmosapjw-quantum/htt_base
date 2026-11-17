"""Local R63 construction checks; actual-source integration belongs to parent."""
import numpy as np
import pytest
from scipy import linalg, stats

from htt.htt.infer import r63_frame_history as fh


def test_distance_quadrature_against_three_closed_form_backgrounds():
    z = np.geomspace(1e-7, 5, 51)
    cases = [(0., 0., z), (0., 1., z/(1+z)),
             (1., 0., 2*z/(np.sqrt(1+z)*(np.sqrt(1+z)+1)))]
    for m, r, exact_chi in cases:
        f = fh.background_factors(z, m, r)
        np.testing.assert_allclose(f["chi_hat"], exact_chi, rtol=3e-14)
    np.testing.assert_array_equal(fh.background_factors(z, 0, 0)["h"], np.zeros(z.size))
    np.testing.assert_allclose(fh.background_factors(z, 0, 1)["h"], z, rtol=3e-14)


def test_quadrature_refinement_and_small_z_cancellation():
    z = np.geomspace(1e-11, 3, 61)
    coarse = fh.background_factors(z, .3153, .0001, quadrature_order=32)
    fine = fh.background_factors(z, .3153, .0001, quadrature_order=96)
    for key in ("chi_hat", "E", "A", "g_per_km_s", "h"):
        np.testing.assert_allclose(coarse[key], fine[key], rtol=3e-13)
    expected = (3*.3153+4*.0001)/4
    np.testing.assert_allclose(fine["h"][:5]/z[:5], expected, rtol=2e-9)
    np.testing.assert_allclose(fine["h"], 1-fh.C_KM_S*z*fine["g_per_km_s"], atol=4e-16, rtol=5e-15)


def test_endpoint_signs_against_independent_finite_lorentz_derivative():
    # Exact prescribed EdS kinematic endpoint test; not a coupled GR solution.
    zbar, s, o, r, d, cal = .06, .4, -.17, .31, -.11, .07
    chi = lambda z: 2*z/(np.sqrt(1+z)*(np.sqrt(1+z)+1))
    dlbar = (1+zbar)*chi(zbar)
    def exact_eta(eps):
        ds = (1+eps*s)/np.sqrt(1-(eps*s)**2)
        do = (1+eps*o)/np.sqrt(1-(eps*o)**2)
        zhel = (1+zbar)*ds/do-1
        zr = (1+zhel)*np.exp(eps*r)-1
        d_corr = dlbar*ds**2/do*np.exp(eps*d)
        return np.log((1+zr)*chi(zr)/d_corr)+eps*cal
    eps = 1e-7
    derivative = (exact_eta(eps)-exact_eta(-eps))/(2*eps)
    factor = fh.background_factors(np.array([zbar]), 1, 0)["g_per_km_s"]
    x = lambda a: np.array([a*fh.C_KM_S, 0., 0.])
    model = fh.processed_eta(factor, [[1, 0, 0]], x(s), x(o), x(r), x(d), [cal, 0, 0])[0]
    assert derivative == pytest.approx(model, abs=2e-8)


def test_exact_first_order_common_boost_calibration_fibre_and_chart_action():
    rng = np.random.default_rng(9203)
    n = rng.normal(size=(31, 3)); n /= np.linalg.norm(n, axis=1)[:, None]
    g = fh.background_factors(np.linspace(.01, .12, 31), .3153, 0)["g_per_km_s"]
    vs, vo, vr, vd = rng.normal(size=(4, 3))*200
    cal, shift, dr, dd = rng.normal(size=3)*.001, rng.normal(size=3)*100, rng.normal(size=3)*80, rng.normal(size=3)*20
    old = fh.processed_eta(g, n, vs, vo, vr, vd, cal)
    fibre = fh.processed_eta(g, n, vs+shift, vo+shift, vr, vd, cal+shift/fh.C_KM_S)
    np.testing.assert_allclose(fibre, old, atol=2e-17, rtol=2e-14)
    changed = fh.processed_eta(g, n, vs, vo, vr+dr, vd+dd, cal)
    np.testing.assert_allclose(changed-old, g*(n@dr)+n@(2*dr-dd)/fh.C_KM_S, atol=2e-17, rtol=2e-14)


def test_compensated_tied_response_and_momentum_all_epochs():
    z = np.array([.01, .03, .08])
    n = np.eye(3)
    m, r, c = .3153, .0001, fh.C_KM_S
    ratio = 3*m/(4*r)
    assert ratio == pytest.approx(2364.75)
    U, vr, vd, cal = np.array([300., -150., 90.]), np.array([100., 250., -80.]), np.zeros(3), np.array([.01, -.02, .03])
    W = U/(1+ratio)
    vo = vr-ratio*W
    vs = (1+z[:, None])*W
    f = fh.background_factors(z, m, r)
    eta = fh.processed_eta(f["g_per_km_s"], n, vs, vo, vr, vd, cal)
    angular = cal+(2*vr-vo-vd)/c
    expected = f["g_per_km_s"]*(1+z/(1+ratio))*(n@U)+n@angular
    np.testing.assert_allclose(eta, expected, atol=2e-17, rtol=2e-14)
    a = 1/(1+np.array([0., .1, 1., 8.]))
    q_m = m*a[:, None]**-4*(W/c)
    q_r = (4*r/3)*a[:, None]**-4*(-ratio*W/c)
    np.testing.assert_allclose(q_m+q_r, np.zeros_like(q_m), atol=np.max(abs(q_m))*3e-16)


def test_history_projection_equals_h_kernel_and_is_pivot_invariant():
    rng = np.random.default_rng(331)
    z = np.linspace(.01, .12, 24)
    n = rng.normal(size=(24, 3)); n /= np.linalg.norm(n, axis=1)[:, None]
    f = fh.background_factors(z, .3153, .0001)
    x = f["g_per_km_s"][:, None]*n
    w = z[:, None]*x
    cov = np.eye(24)+.03*np.ones((24, 24))
    nuisance = np.column_stack((n, x))
    old = fh.residualized_response(cov, nuisance, w)
    pivot = fh.residualized_response(cov, nuisance, w-.055*x)
    alternative = fh.residualized_response(cov, nuisance, -f["h"][:, None]*n/fh.C_KM_S)
    np.testing.assert_allclose(old["information"], pivot["information"], rtol=1e-11, atol=1e-27)
    np.testing.assert_allclose(old["information"], alternative["information"], rtol=2e-11, atol=1e-27)


def test_full_covariance_profile_matches_independent_schur_complement():
    rng = np.random.default_rng(28)
    B = rng.normal(size=(14, 14)); cov = B@B.T+np.eye(14)
    nuisance, target = rng.normal(size=(14, 4)), rng.normal(size=(14, 3))
    ciN, ciT = np.linalg.solve(cov, nuisance), np.linalg.solve(cov, target)
    direct = target.T@ciT-(target.T@ciN)@np.linalg.solve(nuisance.T@ciN, nuisance.T@ciT)
    projected = fh.residualized_response(cov, nuisance, target)
    np.testing.assert_allclose(projected["information"], direct, rtol=3e-13, atol=1e-14)
    scaled = fh.residualized_response(cov, nuisance*np.array([1e-12, 1e7, 3., .02]), target)
    np.testing.assert_allclose(scaled["information"], direct, rtol=3e-13, atol=1e-14)
    assert projected["nuisance_rank"] == scaled["nuisance_rank"] == 4


def test_saturated_nuisance_is_exact_zero_and_partial_alias_has_zero_rank():
    rng = np.random.default_rng(123)
    cov = np.eye(6)+.2*np.ones((6, 6))
    target = rng.normal(size=(6, 3))
    full = fh.residualized_response(cov, np.eye(6), target)
    assert full["full_nuisance_span"] and full["target_rank"] == 0
    np.testing.assert_array_equal(full["residual"], np.zeros_like(target))
    np.testing.assert_array_equal(full["information"], np.zeros((3, 3)))
    nuisance = rng.normal(size=(6, 3))
    alias = fh.residualized_response(cov, nuisance, nuisance@rng.normal(size=(3, 3)))
    assert alias["nuisance_rank"] == 3 and alias["target_rank"] == 0
    assert not alias["full_nuisance_span"]


def test_noise_units_and_target_rotation_covariance():
    rng = np.random.default_rng(572)
    B = rng.normal(size=(10, 10)); cov = B@B.T+np.eye(10)
    N, T = rng.normal(size=(10, 2)), rng.normal(size=(10, 3))
    R, _ = np.linalg.qr(rng.normal(size=(3, 3)))
    base = fh.residualized_response(cov, N, T)
    scaled = fh.residualized_response(1e-18*cov, 1e-9*N, 1e-9*T)
    rotated = fh.residualized_response(cov, N, T@R.T)
    np.testing.assert_allclose(base["information"], scaled["information"], atol=1e-14, rtol=1e-13)
    np.testing.assert_allclose(rotated["information"], R@base["information"]@R.T, atol=1e-14, rtol=1e-13)


def test_velocity_body_distinguishes_U_from_W_and_enforces_early_interval():
    m, r = .3153, .0001
    U = np.array([300., 0., 0.])
    body = fh.compensated_body(U, [370., 0., 0.], m, r, 1, .01)
    assert body["admissible_speed_body"]
    assert body["W_km_s"][0] == pytest.approx(300/2365.75)
    assert body["radiation_beta"] < .002
    low = fh.compensated_velocity_bound(m, r, 1, .01)
    early = fh.compensated_velocity_bound(m, r, 1e5, .01)
    assert early < low
    huge_W_as_U = U*2365.75
    assert not fh.compensated_body(huge_W_as_U, [370., 0., 0.], m, r, 1, .01)["admissible_speed_body"]


def test_oracle_bound_exceeds_actual_three_dimensional_wald_power():
    alpha = .1
    distances = np.linspace(0., 6., 25)
    wald_power = stats.ncx2.sf(stats.chi2.isf(alpha, 3), 3, distances**2)
    upper = fh.oracle_power(distances, alpha)
    assert upper[0] == pytest.approx(alpha)
    assert np.all(np.diff(upper) > 0)
    assert np.all(wald_power <= upper+2e-14)


@pytest.mark.parametrize("call", [
    lambda: fh.background_factors([0.], .3, 0),
    lambda: fh.background_factors([.1], .9, .2),
    lambda: fh.background_factors([.1], .3, 0, quadrature_order=True),
    lambda: fh.compensated_velocity_bound(.3, 0, .1, .01),
    lambda: fh.compensated_velocity_bound(.3, .0001, -1, .01),
    lambda: fh.compensated_velocity_bound(.3, .0001, .1, np.nan),
    lambda: fh.oracle_power(-1),
    lambda: fh.oracle_power(1, 0),
    lambda: fh.residualized_response(np.diag([1., -1.]), np.empty((2, 0)), np.ones((2, 1))),
])
def test_invalid_physical_or_statistical_contract_is_rejected(call):
    with pytest.raises(ValueError):
        call()
