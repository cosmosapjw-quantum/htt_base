import numpy as np
import pytest
from htt.infer.cf4_latent_modulus import (TRUTH,SCALE,C,generate_catalogue,LatentModulusLikelihood,
    directions,fit_catalogue,refined_fit,covariance_from_hessian,local_response_svd)

def catalogue(selected=True):
    return generate_catalogue(np.random.default_rng(101),selected=selected)

def test_directions_group_slots_and_selection():
    cat=catalogue()
    assert len(cat.slot_id)==24 and len(np.unique(cat.slot_id))==24
    np.testing.assert_allclose(np.linalg.norm(directions(),axis=1),1)
    np.testing.assert_allclose(np.sum(directions(),axis=0),0,atol=1e-14)
    assert np.all(cat.proposals>=1)
    assert np.all(np.bincount(cat.shell)==12)
    assert np.all(np.bincount(cat.method)==12)

def test_joint_latent_relation_and_normalized_quadrature():
    like=LatentModulusLikelihood(catalogue())
    assert np.sum(np.exp(like.log_weights))==pytest.approx(1.)
    v=70*like.r+like.nx*(TRUTH[0]+like.r*TRUTH[1])+like.u
    dl=(1+v/C)**2*like.r
    mu=25+5*np.log10(dl)
    expected=25+(5/np.log(10))*like.ell+10*np.log10(1+v/C)
    np.testing.assert_allclose(mu,expected,atol=1e-13)

def test_analytic_score_matches_finite_difference():
    like=LatentModulusLikelihood(catalogue())
    point=TRUTH/SCALE
    value,grad=like.objective(point)
    numerical=[]
    for j in range(3):
        e=np.eye(3)[j]*1e-5
        numerical.append((like.objective(point+e)[0]-like.objective(point-e)[0])/2e-5)
    np.testing.assert_allclose(grad,numerical,rtol=1e-5,atol=1e-7)

def test_selection_normalizer_parameter_dependent_and_control_unity():
    like=LatentModulusLikelihood(catalogue())
    _,alpha=like.row_terms(TRUTH)
    shifted=TRUTH.copy();shifted[2]+=.1
    _,other=like.row_terms(shifted)
    assert np.max(np.abs(alpha-other))>.01
    assert np.all(alpha<=0)
    complete=LatentModulusLikelihood(catalogue(False))
    np.testing.assert_array_equal(complete.row_terms(TRUTH)[1],0)
    omitted=LatentModulusLikelihood(like.catalogue,omit_selection_normalizer=True)
    actual=like.objective(TRUTH/SCALE)[0];negative=omitted.objective(TRUTH/SCALE)[0]
    assert actual-negative==pytest.approx(float(np.sum(alpha)))

def test_shared_anchor_once_and_frozen_domains():
    cat=catalogue(False);like=LatentModulusLikelihood(cat)
    li,la=like.row_terms(TRUTH)
    anchor=-.5*((cat.anchor-TRUTH[2])/.03)**2-np.log(.03*np.sqrt(2*np.pi))
    assert -like.objective(TRUTH/SCALE)[0]==pytest.approx(np.sum(li-la)+anchor)
    with pytest.raises(ValueError):like.row_terms([4000,0,0])
    with pytest.raises(ValueError):LatentModulusLikelihood(cat,(128,96))
    with pytest.raises(ValueError):covariance_from_hessian(np.diag([1.,0.,2.]))

def test_refinement_recovery_and_method_deletion():
    cat=catalogue();result=refined_fit(cat)
    assert result['status']=='QUADRATURE_ACCEPTED'
    assert result['checks'][-1]['max_per_row_log_density_change']<=1e-5
    assert result['fits'][-1]['standard_errors'] is not None
    retained=cat.subset(cat.method!=1)
    assert len(retained.slot_id)==12 and retained.anchor==cat.anchor
    assert fit_catalogue(retained)['status']=='FIT_NUMERICALLY_STABLE'

def test_zero_width_shell_null_exposed():
    cat=catalogue().subset(catalogue().shell==0)
    out=local_response_svd(cat,TRUTH,anchor=True,zero_shell_width=True)
    assert out['rank']==2
    # B+40 A survives; B and A separately cannot be inferred in this control.
    np.testing.assert_allclose(np.abs(out['null_directions_scaled'][0][2]),0.,atol=1e-12)
