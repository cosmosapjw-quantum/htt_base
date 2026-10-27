"""Physical-domain and estimator falsifiers for the conditional response."""
import numpy as np
import pytest

from consume import directions
from optical_joint import (B2, B3, KAPPA, boost_chart, boost_dipole,
                           invert_boost, joint_budget, joint_test, lift_matrix,
                           m_matrix, raw_estimator, raw_to_target,
                           residual_covariance, source_design, stf3,
                           NumericalProfileFailure)


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


def test_reviewed_interior_witness_and_underflow_rejections():
    s = np.diag([.001,-.001,0.])
    out = joint_test(np.zeros(7), s, np.array([.001,0,0]),
                     1e-8, e_d=.002, d_max=.01)
    assert out['compatible'] and not out['physical_set_empty']
    assert out['residual_norm'] == 0
    np.testing.assert_allclose(out['profiled_d'], np.zeros(3), atol=1e-14)
    assert out['profile_certificate']['status'] == 'NORM_BOUNDS_CERTIFIED'
    assert out['certified_upper_bound'] <= 1e-8
    tiny_o = np.r_[1e-200,np.zeros(6)]
    zero = joint_test(tiny_o,np.zeros((3,3)),np.zeros(3),0)
    assert zero['branch'] == 'S_ZERO_DIRECT_MEMBERSHIP'
    assert zero['residual_norm'] == 1e-200 and not zero['compatible']
    nonzero = joint_test(tiny_o,np.diag([1e-200,-1e-200,0]),np.zeros(3),0)
    assert nonzero['branch'] == 'INVERTIBLE_S'
    assert nonzero['residual_norm'] == 1e-200 and not nonzero['compatible']


def test_profile_boundary_norm_bounds_scale_and_rotation_invariance():
    s = np.diag([.02,-.03,.01])
    k = KAPPA*lift_matrix(s)
    d_obs = np.array([.001,0.,0.])
    o = k@np.array([.003,0,0])
    boundary = joint_test(o,s,d_obs,1e-6,e_d=.001,d_max=.001)
    assert boundary['profile_certificate']['status'] == 'NORM_BOUNDS_CERTIFIED'
    np.testing.assert_allclose(boundary['profiled_d'], [.001,0,0],atol=2e-8)
    assert boundary['certified_lower_bound'] > 1e-6
    for factor in (1e-30, 1e-150):
        scaled = joint_test(o*factor,s*factor,d_obs,1e-6*factor,e_d=.001,d_max=.001)
        np.testing.assert_allclose(scaled['score'],boundary['score'],rtol=2e-8)
        assert scaled['compatible'] == boundary['compatible']
    theta=.37
    r=np.array([[np.cos(theta),-np.sin(theta),0],
                [np.sin(theta),np.cos(theta),0],[0,0,1]])
    ot=np.tensordot(o,B3,axes=(0,0))
    ort=np.einsum('ia,jb,kc,abc->ijk',r,r,r,ot)
    orc=np.einsum('aijk,ijk->a',B3,ort)
    rotated=joint_test(orc,r@s@r.T,r@d_obs,1e-6,e_d=.001,d_max=.001)
    np.testing.assert_allclose(rotated['score'],boundary['score'],rtol=2e-8)
    assert rotated['compatible']==boundary['compatible']


def test_unrepresentable_response_is_typed_numerical_range():
    s=np.diag([1e-200,-1e-200,0])
    with pytest.raises(NumericalProfileFailure,match='NUMERIC_RANGE'):
        joint_test(np.zeros(7),s,np.array([1e-200,0,0]),0)


def test_rf1_narrow_ball_feasible_and_rf2_physical_boundary_rejects():
    s=np.diag([.001,-.001,0.])
    k=KAPPA*lift_matrix(s)
    rf1=joint_test(k@np.array([.0100005,0,0]),s,np.array([.01,0,0]),
                   5.606717652542515e-10,e_d=1e-6,d_max=.1)
    assert rf1['compatible']
    assert rf1['certified_upper_bound'] < rf1['budget']
    assert np.linalg.norm(np.array(rf1['profiled_d'])-[.01,0,0]) <= 1e-6
    assert np.linalg.norm(rf1['profiled_d']) <= .1
    rf2=joint_test(k@np.array([.0001000000009,0,0]),s,np.zeros(3),
                   1.0092091825422658e-15,e_d=.1,d_max=.0001)
    assert not rf2['compatible']
    assert rf2['certified_lower_bound'] > rf2['budget']
    assert np.linalg.norm(rf2['profiled_d']) <= .0001
    with pytest.raises(NumericalProfileFailure,match='NUMERIC_RANGE'):
        joint_test(np.r_[1e200,np.zeros(6)],np.zeros((3,3)),np.zeros(3),0)


@pytest.mark.parametrize('d_obs,e_d,d_max,target',[
    (.01,1e-6,.1,.010002),
    (0.,.1,.0001,.0001000000009),
    (-.003,.001,.1,-.0015),
])
def test_analytic_one_axis_interval_oracle_and_output_units(d_obs,e_d,d_max,target):
    s=np.diag([.001,-.001,0.])
    response=KAPPA*lift_matrix(s)[:,0]
    interval=(max(d_obs-e_d,-d_max),min(d_obs+e_d,d_max))
    assert interval[0]<=interval[1]
    exact_min=np.linalg.norm(response)*abs(target-np.clip(target,*interval))
    assert exact_min>0
    for factor in (.7,1.3):
        for unit in (1.,1e-30):
            out=joint_test(unit*response*target,unit*s,
                           np.array([d_obs,0,0]),unit*factor*exact_min,
                           e_d=e_d,d_max=d_max)
            assert out['compatible']==(factor>1)
            assert out['certified_lower_bound'] <= unit*exact_min*(1+1e-10)
            assert out['certified_upper_bound'] >= unit*exact_min*(1-1e-10)
            witness=np.array(out['profiled_d'])
            assert np.linalg.norm(witness-[d_obs,0,0]) <= e_d
            assert np.linalg.norm(witness) <= d_max


def test_rf1_rf2_rotation_invariant_decisions():
    s=np.diag([.001,-.001,0.])
    theta=.53
    r=np.array([[np.cos(theta),-np.sin(theta),0],
                [np.sin(theta),np.cos(theta),0],[0,0,1]])
    for target,d_obs,e_d,d_max,budget,expected in [
        (.0100005,.01,1e-6,.1,5.606717652542515e-10,True),
        (.0001000000009,0.,.1,.0001,1.0092091825422658e-15,False),
    ]:
        o=KAPPA*lift_matrix(s)@np.array([target,0,0])
        tensor=np.tensordot(o,B3,axes=(0,0))
        rotated=np.einsum('ia,jb,kc,abc->ijk',r,r,r,tensor)
        orc=np.einsum('aijk,ijk->a',B3,rotated)
        try:
            out=joint_test(orc,r@s@r.T,r@np.array([d_obs,0,0]),
                           budget,e_d=e_d,d_max=d_max)
        except NumericalProfileFailure as exc:
            assert not expected and exc.code=='NUMERICAL_FAILURE'
        else:
            assert out['compatible']==expected
