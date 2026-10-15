"""No simulated astrophysical detection: check the registered math and synthetic inference."""
import numpy as np
import pytest
from obsstat.cf4_apparent_kinematic_distribution import (
    xyz_from_equatorial,stf2_orthonormal,radial_velocity_gradient,
    luminosity_distance_flat_lcdm,model_matrix,weighted_lsq,posterior_shear_proxy,
    Cf4KinematicInputError
)


def test_five_STF2_basis_orthonormal_and_tracefree():
    T=stf2_orthonormal()
    assert T.shape==(5,3,3)
    np.testing.assert_allclose(np.trace(T,axis1=1,axis2=2),0,atol=1e-15)
    np.testing.assert_allclose(np.einsum('aij,bij->ab',T,T),np.eye(5),atol=1e-15)


def test_antisymmetric_radial_velocity_is_exactly_absent():
    rng=np.random.default_rng(37)
    n=rng.normal(size=(77,3))
    n=n/np.linalg.norm(n,axis=1,keepdims=True)
    omega=rng.normal(size=(3,3))
    omega=omega-omega.T
    rad=radial_velocity_gradient(n,omega)
    np.testing.assert_allclose(rad,np.zeros(77),atol=1e-15)


def test_anisotropic_H_angular_terms_have_no_fullsky_trace():
    rng=np.random.default_rng(12)
    n=rng.normal(size=(120000,3))
    n=n/np.linalg.norm(n,axis=1,keepdims=True)
    T=stf2_orthonormal()
    p=np.einsum('ai,tij,aj->at',n,T,n,optimize=True).mean(axis=0)
    assert np.max(abs(p)) < 0.004


def test_LCDM_luminosity_distance_small_redshift_limit():
    z=np.asarray([1e-4,0.001,.01,.1])
    d,I,loggrad=luminosity_distance_flat_lcdm(z, H0=74.6, omega_m=.3153)
    assert np.all(np.diff(d)>0) and np.all(I>0)
    assert abs(d[0]/(299792.458*z[0]/74.6)-1)<2e-4
    np.testing.assert_allclose(loggrad[0]*z[0],1,atol=2e-4)


def test_source_conditioned_shear_and_bulk_injection_recovered():
    rng=np.random.default_rng(20261015)
    n=rng.normal(size=(1800,3));n/=np.linalg.norm(n,axis=1,keepdims=True)
    z=rng.uniform(.015,.08,size=len(n))
    cat=np.array(['FP','SN','TF'])[rng.integers(0,3,size=len(n))]
    out=model_matrix(z,n,cat,include_method_slope=True)
    k=np.zeros(out['design'].shape[1])
    k[out['slices']['shear']]=np.array([.013,-.007,.009,.002,-.01])
    k[out['slices']['bulk']]=np.array([150,-100,70])
    k[out['slices']['angular_dipole']]=np.array([.003,-.002,.001])
    residual=out['design']@k
    fit=weighted_lsq(out['design'],residual,np.full(len(z),.3))
    np.testing.assert_allclose(fit['beta'],k,atol=1e-8)
    assert fit['condition_scaled']<1e8 and fit['qr_orthonormality_residual']<1e-8
    samp=posterior_shear_proxy(fit['beta'],fit['cov'],out['slices']['shear'],
                                 draws=3000,seed=3)
    assert samp['mean_sigma_over_theta']>0


def test_invalid_raw_geometry_rejected():
    with pytest.raises(Cf4KinematicInputError):
        xyz_from_equatorial([1],[109])
    with pytest.raises(Cf4KinematicInputError):
        luminosity_distance_flat_lcdm(np.array([-1]))
    with pytest.raises(Cf4KinematicInputError):
        weighted_lsq(np.ones((20,3)),np.ones(20),np.zeros(20))


def test_posterior_stf_normalization_matches_frobenius_kinematics():
    """A=σ/H only in this algebraic fixture, not an observed identity."""
    from obsstat.cf4_apparent_kinematic_distribution import posterior_shear_proxy
    mean=np.array([.023,-.011,.004,.009,.006])
    C=np.diag([1e-10]*5)
    law=posterior_shear_proxy(mean,C,slice(None),draws=1001,seed=4)
    a=np.asarray(law['quantiles_025_16_50_84_975_STF_coefficient_norm'])
    s=np.asarray(law['quantiles_025_16_50_84_975_sigma_over_H'])
    theta=np.asarray(law['quantiles_025_16_50_84_975_sigma_over_theta'])
    sigma2=np.asarray(law['quantiles_025_16_50_84_975_apparent_Sigma2_std'])
    np.testing.assert_allclose(s,a/np.sqrt(2),rtol=1e-14)
    np.testing.assert_allclose(theta,s/3,rtol=1e-14)
    np.testing.assert_allclose(sigma2,a*a/6,rtol=1e-14)
    assert law['median_sigma_over_H']==pytest.approx(law['median_STF_coefficient_frobenius_norm']/np.sqrt(2))
    assert 'NOT PHYSICAL' in law['sampling_scope']


def test_posterior_stf_rejects_invalid_mean_cov_and_draw_count():
    from obsstat.cf4_apparent_kinematic_distribution import posterior_shear_proxy
    mean=np.zeros(5);cov=np.eye(5)
    for badmean in (np.array([np.nan,0.,0.,0.,0.]),):
        with pytest.raises(Cf4KinematicInputError):
            posterior_shear_proxy(badmean,cov,slice(None),draws=5)
    nonsym=cov.copy();nonsym[0,1]=.1
    with pytest.raises(Cf4KinematicInputError):
        posterior_shear_proxy(mean,nonsym,slice(None),draws=5)
    with pytest.raises(Cf4KinematicInputError):
        posterior_shear_proxy(mean,cov,slice(None),draws=True)
    with pytest.raises(Cf4KinematicInputError):
        posterior_shear_proxy(mean,cov,slice(None),draws=0)
