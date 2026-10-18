"""Mathematical correctness of proper common calibration / selection laws."""
import numpy as np
import pytest
from scipy.stats import multivariate_normal
from obsstat.cf4_shared_selected_law import (
    Cf4SelectedLawError, shared_calibration_gaussian_logpdf,
    gaussian_preselection_loglik,gaussian_slot_conditioned_loglik,
    profiled_common_offset_chisq,uncalibrated_distance_model,
    fit_intercept_and_dipole,combined_distance_uncertainty)


def test_shared_calibration_woodbury_equals_exact_dense():
    rng=np.random.default_rng(71)
    y=rng.normal(size=6)
    m=rng.normal(size=6)
    d=np.linspace(.1,.3,6)
    for sigma_eta in (0.,.02,.2,3.):
        got=shared_calibration_gaussian_logpdf(y,m,d,sigma_eta)
        dense=np.diag(d*d)+sigma_eta*sigma_eta*np.ones((6,6))
        expected=multivariate_normal.logpdf(y,mean=m,cov=dense)
        assert got == pytest.approx(expected,rel=1e-11,abs=1e-11)


def test_selected_joint_density_has_correct_global_normalization():
    y=np.array([0.,.2])
    m=np.array([-.05,.1])
    err=np.array([.2,.35])
    lower=np.array([-.4,-.2])
    upper=np.array([.6,.6])
    full=shared_calibration_gaussian_logpdf(y,m,err,.2)
    pre=gaussian_preselection_loglik(y,m,err,.2,lower,upper,nquad=120)
    slot=gaussian_slot_conditioned_loglik(y,m,err,.2,lower,upper,nquad=120)
    assert np.isfinite(pre) and np.isfinite(slot)
    assert not np.isclose(pre,slot)
    no_selection=gaussian_preselection_loglik(y,m,err,.2,
        np.full(2,-np.inf),np.full(2,np.inf),nquad=120)
    assert no_selection==pytest.approx(full,abs=1e-11)


def test_selection_agreement_when_shared_variance_zero():
    yy=np.array([.4,-.2,.3])
    mm=np.array([.2,-.1,0.])
    e=np.array([.3,.25,.2])
    lo=np.full(3,-1.)
    hi=np.full(3,1.)
    p=gaussian_preselection_loglik(yy,mm,e,0.,lo,hi)
    s=gaussian_slot_conditioned_loglik(yy,mm,e,0.,lo,hi)
    assert p==pytest.approx(s,rel=1e-11)


def test_outside_support_is_impossible():
    y=np.array([.1,3.])
    with pytest.raises(Cf4SelectedLawError,match='outside'):
        gaussian_preselection_loglik(y,np.zeros(2),np.ones(2),.05,
                                     np.full(2,-1.),np.full(2,1.))


def test_gauge_profile_is_invariant_under_H_reference_change():
    v=np.linspace(3000,10000,15)
    rng=np.random.default_rng(40)
    y=uncalibrated_distance_model(v,70.)+rng.normal(scale=.1,size=len(v))
    err=np.linspace(.09,.22,len(v))
    c1=profiled_common_offset_chisq(y,uncalibrated_distance_model(v,67.),err)
    c2=profiled_common_offset_chisq(y,uncalibrated_distance_model(v,77.),err)
    assert c1==pytest.approx(c2,abs=1e-10)
    delta=5*np.log10(77/67)
    # (eta, H) -> (eta+delta, H*77/67) is an exact scale/zero-point gauge.
    np.testing.assert_allclose(uncalibrated_distance_model(v,77.)+delta,
                               uncalibrated_distance_model(v,67.),atol=1e-12)


def test_shared_offset_does_not_improve_angular_shape_information_with_free_intercept():
    rng=np.random.default_rng(21)
    n=rng.normal(size=(50,3));n/=np.linalg.norm(n,axis=1,keepdims=True)
    y=0.4+np.array([.08,-.04,.02])@n.T+rng.normal(size=50,scale=.2)
    d=.2*np.ones(50)
    r=fit_intercept_and_dipole(y,n,d)
    r2=fit_intercept_and_dipole(y+20.,n,d)
    np.testing.assert_allclose(r['dipole'],r2['dipole'],atol=1e-12)
    assert r['rank']==4 and np.linalg.eigvalsh(r['dipole_covariance']).min()>0


def test_velocity_width_quadrature_dimension_and_reject_invalid():
    e=np.array([.12,.18])
    v=np.array([3000.,9000.])
    base=combined_distance_uncertainty(e,v,0.)
    np.testing.assert_array_equal(base,e)
    big=combined_distance_uncertainty(e,v,300.)
    assert np.all(big>e)
    with pytest.raises(Cf4SelectedLawError):
        combined_distance_uncertainty(e,np.array([-1.,9000.]),300.)


def test_general_lowrank_method_calibration_matches_dense_for_psd_prior():
    from obsstat.cf4_shared_selected_law import lowrank_calibration_gaussian_logpdf
    rng=np.random.default_rng(105)
    n,k=13,4
    y=rng.normal(size=n)
    m=rng.normal(size=n)
    sig=rng.uniform(.1,.4,n)
    Z=rng.normal(size=(n,k))
    K=rng.normal(size=(k,k))
    K=K@K.T
    # Rank deficient correlated shared prior is still allowed.
    e,u=np.linalg.eigh(K)
    e[0]=0.
    K=(u*e)@u.T
    got=lowrank_calibration_gaussian_logpdf(y,m,sig,Z,K)
    exact=multivariate_normal.logpdf(y,mean=m,
        cov=np.diag(sig**2)+Z@K@Z.T)
    assert got==pytest.approx(exact,rel=1e-11,abs=1e-11)


def test_general_lowrank_common_calibration_reduces_to_one_offset_law():
    from obsstat.cf4_shared_selected_law import lowrank_calibration_gaussian_logpdf
    rng=np.random.default_rng(606)
    y=rng.normal(size=18);m=rng.normal(size=18)
    sig=rng.uniform(.08,.4,18)
    for t in (0.,.03,.5,4.):
        compact=lowrank_calibration_gaussian_logpdf(y,m,sig,
              np.ones((18,1)),np.array([[t*t]]))
        original=shared_calibration_gaussian_logpdf(y,m,sig,t)
        assert compact==pytest.approx(original,rel=1e-11,abs=1e-11)


def test_general_lowrank_rejects_indefinite_unphysical_nuisance_prior():
    from obsstat.cf4_shared_selected_law import lowrank_calibration_gaussian_logpdf
    with pytest.raises(Cf4SelectedLawError):
        lowrank_calibration_gaussian_logpdf(
            np.ones(4),np.zeros(4),np.ones(4),np.ones((4,2)),
            np.diag([1.,-1.]))
