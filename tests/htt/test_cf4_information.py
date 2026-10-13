import numpy as np
import pytest
from types import SimpleNamespace
from htt.infer.cf4_information import (A_MAG,C,SCALES,T_CART_TO_FROB,NoiseScenario,angular_design,latent_jacobian,
    local_values,profiled_rows,information,contrast_uncertainty,stf_crosswalk)

def fixture(n=30):
    rng=np.random.default_rng(19);d=rng.normal(size=(n,3));d/=np.linalg.norm(d,axis=1)[:,None]
    return SimpleNamespace(direction=d,modulus=rng.uniform(30,37,n),modulus_error=np.full(n,.4),vh_km_s=rng.uniform(1000,15000,n),
        method_presence=rng.uniform(size=(n,7))>.65)

def test_jacobian_finite_difference():
    n=np.array([.3,.4,np.sqrt(.75)]);theta=np.arange(13,dtype=float);theta[4]=70
    lr,z=np.log(80),.04;r=np.exp(lr);f=angular_design(n[None,:])[0]@theta[4:]
    actual=latent_jacobian(r,z,f)
    numerical=np.column_stack(((local_values(lr+1e-5,z,n,theta)-local_values(lr-1e-5,z,n,theta))/2e-5,
        (local_values(lr,z+1e-6,n,theta)-local_values(lr,z-1e-6,n,theta))/2e-6))
    np.testing.assert_allclose(actual,numerical,rtol=1e-8,atol=1e-5)

def test_tiny_dense_schur_reference():
    cat=fixture(5);sc=NoiseScenario('test',40,200);x,_,r,z=profiled_rows(cat,sc)
    expected=np.zeros((13,13));ang=angular_design(cat.direction)
    for i in range(5):
        sig=np.array([cat.modulus_error[i],40,200]);e=latent_jacobian(r[i],z[i],70)/sig[:,None]
        j=np.zeros((3,13));j[2]=-np.r_[1,cat.direction[i],r[i]*ang[i]]/200
        expected+=j.T@(np.eye(3)-e@np.linalg.solve(e.T@e,e.T))@j
    np.testing.assert_allclose(x.T@x,expected,rtol=2e-10,atol=2e-10)

def test_free_calibration_scale_null_and_no_finite_h_uncertainty():
    x,n,_,_=profiled_rows(fixture(),NoiseScenario('free',50,250,True))
    info=information(x,n)
    assert info['rank']==12
    # At the declared isotropic fiducial, full scale tangent has only delta H.
    delta=np.zeros(13);delta[4]=70.
    np.testing.assert_allclose(x@delta+n[:,0]*A_MAG,0.,atol=1e-12)
    assert not contrast_uncertainty(info,np.eye(13)[4])['estimable']
    assert contrast_uncertainty(info,np.eye(13)[4])['standard_error'] is None
    assert contrast_uncertainty(info,np.eye(13)[1])['estimable']
    np.testing.assert_allclose(info['fixed_coefficient_scales'],SCALES)

def test_method_deletion_and_fixed_scaling():
    cat=fixture();sc=NoiseScenario('method',50,250,True,True)
    x,n,_,_=profiled_rows(cat,sc);mask=~cat.method_presence[:,0]
    full=information(x,n);cut=information(x,n,mask)
    assert cut['rows']==int(mask.sum())
    np.testing.assert_array_equal(full['fixed_coefficient_scales'],cut['fixed_coefficient_scales'])
    direct=information(x[mask],n[mask]);np.testing.assert_allclose(cut['singular_values'],direct['singular_values'])
    assert cut['nuisance_rank']<=full['nuisance_rank']

def test_basis_covariance_and_invalid_inputs():
    q=np.array([1,2,3,4,5.]);v=np.diag([1,2,3,4,5.]);qf,vf=stf_crosswalk(q,v)
    np.testing.assert_allclose(np.linalg.solve(T_CART_TO_FROB,qf),q)
    inv=np.linalg.inv(T_CART_TO_FROB);np.testing.assert_allclose(inv@vf@inv.T,v,atol=1e-14)
    for value in [0,-1,np.inf,np.nan]:
        with pytest.raises(ValueError):NoiseScenario('bad',value,100)
    with pytest.raises(ValueError):latent_jacobian(1,-1,70)
    with pytest.raises(ValueError):information(np.full((4,13),np.nan),np.empty((4,0)))

def test_tiny_sample_has_complete_nullspace():
    x,n,_,_=profiled_rows(fixture(3),NoiseScenario('tiny',50,200))
    out=information(x,n)
    assert out['null_basis_scaled'].shape==(13,10)
    assert not contrast_uncertainty(out,np.eye(13)[4])['estimable']

def test_complete_nuisance_confounding_is_rank_zero():
    x=np.random.default_rng(23).normal(size=(30,13))
    out=information(x,x)
    assert out['rank']==0
    assert not contrast_uncertainty(out,np.eye(13)[0])['estimable']
    assert out['null_basis_scaled'].shape==(13,13)

def test_independent_method_offsets_exhaust_three_group_information():
    cat=fixture(3);cat.method_presence=np.zeros((3,7),bool)
    cat.method_presence[:,:3]=np.eye(3,dtype=bool)
    x,n,_,_=profiled_rows(cat,NoiseScenario('three_offsets',50,200,False,True))
    out=information(x,n)
    assert out['nuisance_rank']==3
    assert out['rank']==0
    assert not contrast_uncertainty(out,np.eye(13)[4])['estimable']

def test_contrast_estimability_is_homogeneous_and_zero_is_estimable():
    x,n,_,_=profiled_rows(fixture(),NoiseScenario('free_scale',50,250,True))
    out=information(x,n)
    for factor in [1.,1e-12,1e12,-1e-12]:
        assert not contrast_uncertainty(out,factor*np.eye(13)[4])['estimable']
        actual=contrast_uncertainty(out,factor*np.eye(13)[1])
        baseline=contrast_uncertainty(out,np.eye(13)[1])
        assert actual['estimable']
        np.testing.assert_allclose(actual['standard_error'],abs(factor)*baseline['standard_error'])
    assert contrast_uncertainty(out,np.zeros(13))['standard_error']==0.
