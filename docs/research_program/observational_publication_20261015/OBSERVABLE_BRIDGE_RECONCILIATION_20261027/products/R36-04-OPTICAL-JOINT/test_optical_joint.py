"""Physical-domain and estimator falsifiers for the conditional response."""
import numpy as np
import pytest

from consume import directions
from optical_joint import (B2, B3, KAPPA, boost_chart, boost_dipole,
                           invert_boost, joint_budget, joint_test, lift_matrix,
                           m_matrix, raw_estimator, raw_to_target,
                           residual_covariance, source_design, stf3)


def test_full_stf_lift_sign_scale_rotation_and_zero():
    s = np.diag([.02, -.03, .01])
    d = np.array([.03, -.02, .01])
    l = lift_matrix(s)
    assert l.shape == (7, 3)
    np.testing.assert_allclose(l.T @ l, m_matrix(s), rtol=2e-14, atol=1e-18)
    np.testing.assert_allclose(lift_matrix(-s), -l, rtol=2e-14, atol=1e-18)
    np.testing.assert_array_equal(lift_matrix(np.zeros((3,3))), np.zeros((7,3)))
    theta = .41
    r = np.array([[np.cos(theta),-np.sin(theta),0],
                  [np.sin(theta), np.cos(theta),0],[0,0,1]])
    tensor = np.tensordot(l @ d, B3, axes=(0,0))
    rotated_tensor = np.einsum('ia,jb,kc,abc->ijk', r, r, r, tensor)
    rotated_s = r @ s @ r.T
    actual = np.tensordot(lift_matrix(rotated_s) @ (r @ d), B3, axes=(0,0))
    np.testing.assert_allclose(actual, rotated_tensor, rtol=3e-14, atol=1e-18)


def test_joint_counterexample_profile_and_zero_branch():
    s = np.diag([.02, -.03, .01])
    l = lift_matrix(s)
    proj = l @ np.linalg.solve(l.T @ l, l.T)
    perpendicular = (np.eye(7)-proj)[:,0]
    perpendicular /= np.linalg.norm(perpendicular)
    parallel = l[:,0]/np.linalg.norm(l[:,0])
    o = .8*(perpendicular + parallel)
    out = joint_test(o, s, np.zeros(3), 1)
    assert not out['compatible']
    np.testing.assert_allclose([np.sqrt(out['perpendicular_squared']),
                                np.sqrt(out['parallel_squared']), out['score']],
                               [.8,.8,np.sqrt(1.28)], rtol=2e-14)
    profile = joint_test(o, s, np.zeros(3), 1, e_d=.8/(KAPPA*np.linalg.norm(l[:,0])))
    assert profile['score'] <= out['score']
    assert joint_test(np.zeros(7), np.zeros((3,3)), np.zeros(3), 0)['compatible']
    assert not joint_test(np.ones(7), np.zeros((3,3)), np.zeros(3), 0)['compatible']
    assert not joint_test(np.ones(7)*1e-20, np.zeros((3,3)), np.zeros(3), 0)['compatible']
    assert joint_test(np.zeros(7), s, np.array([1e-20,0,0]), 0, e_d=1e-20, d_max=0)['compatible']
    with pytest.raises(ValueError):
        joint_test(np.zeros(7), s, np.zeros(3), -1)


def test_tiny_nonzero_s_keeps_inverse_domain():
    unit = np.diag([1., -1., 0.])
    s = unit * 1e-120
    d = np.array([.1,.2,-.3])
    o = KAPPA * lift_matrix(s) @ d
    out = joint_test(o, s, d, 1e-118)
    assert out['branch'] == 'INVERTIBLE_S'
    np.testing.assert_allclose(out['inverse_d'], d, rtol=2e-14, atol=1e-14)


def test_bound_ownership_and_zero_budget():
    b = joint_budget(.1, .02, .03, .04, .001, .05)
    np.testing.assert_allclose(b['total'], sum(value for key,value in b.items() if key != 'total'))
    np.testing.assert_allclose(b['uncertain_S'], KAPPA*np.sqrt(3/5)*.001*.05)
    with pytest.raises(ValueError):
        joint_budget(1,0,0,0,0,1)


def test_raw_response_full_cross_covariance_and_finite_difference():
    n = directions(80)
    s = np.diag([.02,-.03,.01])
    d = np.array([.01,-.005,.003])
    weights = 1 + .2*n[:,0]
    u = np.linspace(-1,1,len(n))
    c = 1e-8*(np.eye(len(n))+.3*np.outer(u,u))
    result = raw_to_target(n,s,d,weights,c)
    assert result['estimator'].shape == (10,len(n))
    assert result['jacobian_d_S'].shape == (10,8)
    eps=1e-6
    s_plus = s+eps*B2[0]
    s_minus = s-eps*B2[0]
    central = (raw_to_target(n,s_plus,d,weights)['summary']-
               raw_to_target(n,s_minus,d,weights)['summary'])/(2*eps)
    np.testing.assert_allclose(central, result['jacobian_d_S'][:,3], rtol=3e-7, atol=2e-9)
    k = result['estimator']
    np.testing.assert_allclose(result['summary_covariance'], k@c@k.T, rtol=2e-14, atol=1e-22)
    cross = result['summary_covariance'][:3,3:]
    assert np.linalg.norm(cross) > 0
    a = np.column_stack((-KAPPA*lift_matrix(s),np.eye(7)))
    np.testing.assert_allclose(residual_covariance(result['summary_covariance'],s),
                               a@result['summary_covariance']@a.T, rtol=2e-14, atol=1e-22)
    with pytest.raises(ValueError):
        raw_to_target(n,s,d,weights,np.diag(np.ones(len(n)-1)))
    with pytest.raises(ValueError):
        raw_estimator(n[:8])


def test_corrected_chart_vertex_and_spurious_slope_octupole():
    gamma = 1.004
    h = .07  # synthetic rate per arbitrary distance unit
    ell = np.array([0.,.01,.02])
    z = h*ell
    d_l = ell*(1+z)**2  # chosen matter-frame corrected distance = ell
    ch = boost_chart(z,d_l,gamma)
    np.testing.assert_allclose(ch['d_l_star_tilde'],gamma*ell,atol=1e-16)
    assert np.isclose(ch['vertex_z_tilde'],1/gamma-1)
    corrected_slope = np.diff(ch['z_tilde'])/np.diff(ch['d_l_star_tilde'])
    np.testing.assert_allclose(corrected_slope,h/gamma**2,rtol=1e-12)
    # At the vertex the raw luminosity distance has slope d_L/dell=1/Gamma.
    raw_slope = (ch['z_tilde'][1]-ch['z_tilde'][0])/(ch['d_l_tilde'][1]-ch['d_l_tilde'][0])
    assert np.isclose(raw_slope,h/(1+z[1])**2,rtol=1e-3)
    # Eq. (70): wrong slope has a rank-3 term; true boosted Hubble slope does not.
    n = directions(128)
    s = np.diag([.02,-.03,.01])
    beta = np.array([.003,-.001,.002])
    true_hubble = 1+n@boost_dipole(s,beta)+np.einsum('ni,ij,nj->n',n,s,n)
    wrong_hubble = true_hubble*(1+2*n@beta)
    fit = np.linalg.pinv(source_design(n))
    assert np.linalg.norm((fit@true_hubble)[9:]) < 1e-12
    assert np.linalg.norm((fit@wrong_hubble)[9:]) > 1e-6
    # The logarithmic magnitude of a true dipole+quadrupole has a distinct octupole.
    true_magnitude = -KAPPA*np.log(true_hubble)
    assert np.linalg.norm((fit@true_magnitude)[9:]) > 1e-7


def test_boost_inverse_domain_and_acceleration_distinction():
    s = np.diag([.02,-.03,.01])
    beta = np.array([.003,-.001,.002])
    d_boost = boost_dipole(s,beta)
    np.testing.assert_allclose(invert_boost(s,d_boost),beta,rtol=1e-14,atol=1e-16)
    assert not np.allclose(d_boost,-beta)  # different from d=-A/(cH)
    with pytest.raises(ValueError):
        invert_boost(np.diag([-1.,.5,.5]),d_boost)
