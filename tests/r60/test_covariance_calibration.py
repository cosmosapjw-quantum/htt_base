"""Scientific identities for the new conditional sensitivity calculation."""
import numpy as np
import pytest
from scipy import linalg, optimize, stats

from htt.htt.infer.r58_mixed_tensor_likelihood import fit_linear
from htt.htt.infer.r60_covariance_calibration import (
    calibration_distance, calibration_breakdown, calibrated_support,
    block_wald, fixed_mean_amplitude, residual_contrast_amplitude,
)


def test_calibration_distance_and_breakdown_spherical_oracle():
    h, c, b = np.array([3.,4.]), 4*np.eye(2), np.eye(2)
    ans = calibration_distance(h,c,b,1.)
    assert ans['distance2'] == pytest.approx(4.)
    assert np.allclose(ans['witness'], [.6,.8])
    root = calibration_breakdown(h,c,b)
    assert root['radius'] == pytest.approx(5 - 2*np.sqrt(stats.chi2.ppf(.95,2)), abs=1e-11)
    assert calibration_breakdown(h,100*c,b)['radius'] == 0


def test_calibration_distance_independent_slsqp_and_coordinate_change():
    rng = np.random.default_rng(92)
    a, g = rng.normal(size=(5,5)), rng.normal(size=(5,5))
    c, b = a@a.T+np.eye(5), g@g.T+np.eye(5)
    h = rng.normal(size=5)*3
    radius = .6
    ci, bi = np.linalg.inv(c), np.linalg.inv(b)
    oracle = optimize.minimize(lambda x:(h-x)@ci@(h-x), np.zeros(5),
        jac=lambda x:-2*ci@(h-x), method='SLSQP',
        constraints={'type':'ineq','fun':lambda x:radius**2-x@bi@x,
                     'jac':lambda x:-2*bi@x},options={'ftol':1e-11,'maxiter':1000})
    answer = calibration_distance(h,c,b,radius)
    assert oracle.success
    assert answer['distance2'] == pytest.approx(oracle.fun,abs=1e-8)
    t = np.diag([.1,.5,2,3,7])
    changed = calibration_distance(t@h,t@c@t.T,t@b@t.T,radius)
    assert changed['distance2'] == pytest.approx(answer['distance2'],rel=1e-11)
    assert answer['budget_used'] <= radius*(1+1e-10)


def test_support_minkowski_sum_has_statistical_and_calibration_terms():
    out=calibrated_support([0,0],np.eye(2),4*np.eye(2),[1,0],.2)
    assert out['upper'] == pytest.approx(np.sqrt(stats.chi2.ppf(.95,2))+.4)
    assert out['lower'] == -out['upper']


def test_block_wald_matches_profiled_likelihood_ratio():
    rng=np.random.default_rng(61)
    y=rng.normal(size=12);x=rng.normal(size=(12,5))
    b=rng.normal(size=(12,12));c=b@b.T+np.eye(12)
    full=fit_linear(y,c,x); reduced=fit_linear(y,c,x[:,:2])
    w=block_wald(full,[2,3,4])
    assert w['wald'] == pytest.approx(reduced['residual_chi2']-full['residual_chi2'],abs=1e-11)


def test_wald_is_not_monotone_under_psd_covariance_growth():
    y=np.array([0.,1.]);x=np.array([[1.],[0.]])
    for a in [0.,.1,1.,10.]:
        f=fit_linear(y,np.eye(2)+a*np.ones((2,2)),x)
        assert f['wald'] == pytest.approx(a*a/((1+a)*(1+2*a)),abs=1e-14)
    assert fit_linear(y,np.eye(2)+np.ones((2,2)),x)['wald'] > 0


def test_residual_likelihood_is_invariant_to_mean_and_contrast_rotation():
    rng=np.random.default_rng(152)
    y=rng.normal(size=9);x=rng.normal(size=(9,3))
    b=rng.normal(size=(9,9)); n=b@b.T+np.eye(9)
    b=rng.normal(size=(9,9)); s=b@b.T
    a=residual_contrast_amplitude(y,n,s,x)
    shift=residual_contrast_amplitude(y+x@np.array([1.,-3.,.2]),n,s,x)
    assert a['amplitude'] == pytest.approx(shift['amplitude'],abs=1e-7)
    z=linalg.null_space(x.T)
    q,_=np.linalg.qr(rng.normal(size=(6,6)));z=z@q
    independent=fixed_mean_amplitude(z.T@y,z.T@n@z,z.T@s@z)
    assert a['loglike_gain'] == pytest.approx(independent['loglike_gain'],abs=1e-9)
    assert a['annihilation_error'] < 1e-12


def test_invalid_calibration_shape_or_budget_rejected():
    with pytest.raises(ValueError):calibration_distance([1],[[1]],[[1]],-1)
    with pytest.raises(ValueError):calibration_distance([1],[[-1]],[[1]],0)
    with pytest.raises(ValueError):calibration_breakdown([1],[[1]],[[1]],level=1)


def test_calibration_body_boundary_one_ulp_is_feasible():
    h=np.array([.0123,-.0045,.0082,.0023,-.0099])
    b=7.5*np.eye(5);c=np.diag([1,2,3,4,5])*1e-5
    radius=np.nextafter(np.sqrt(h@np.linalg.solve(b,h)),0.)
    answer=calibration_distance(h,c,b,radius)
    assert answer['budget_used'] <= radius*(1+2e-15)
    assert answer['distance2'] < 1e-24
def test_low_rank_linear_nuisance_budget_has_independent_geometric_oracle():
    from htt.htt.infer.r60_covariance_calibration import linear_budget_distance
    H = np.array([[1.,0.],[0.,1.],[0.,0.]])
    out = linear_budget_distance([3.,4.,2.],np.eye(3),H,1.)
    assert out['distance2'] == pytest.approx(20.,abs=1e-10)
    assert np.allclose(out['nuisance_witness'],[.6,.8],atol=1e-10)
    assert out['image_rank'] == 2
    assert linear_budget_distance([3.,4.,2.],np.eye(3),H,6.)['distance2'] == pytest.approx(4.)


def test_tiny_nuisance_mode_is_not_silently_discarded_at_finite_budget():
    from htt.htt.infer.r60_covariance_calibration import linear_budget_distance
    # v=(0,3) exactly fits h, so a rank-truncated distance of nine is wrong.
    # This highly ill-scaled response needs a resolved numerical chart.
    with pytest.raises(ValueError,match='unresolved nonzero nuisance mode'):
        linear_budget_distance([0.,3.],np.eye(2),np.diag([1e13,1.]),3.)


def test_resolved_ill_scaled_nuisance_keeps_budget_and_optimum():
    from htt.htt.infer.r60_covariance_calibration import linear_budget_distance
    out=linear_budget_distance([0.,3.],np.eye(2),np.diag([1e8,1.]),2.)
    assert out['distance2'] == pytest.approx(1.,abs=1e-10)
    assert np.allclose(out['nuisance_witness'],[0.,2.],atol=1e-10)
    assert out['budget_used'] == pytest.approx(2.,abs=1e-10)
