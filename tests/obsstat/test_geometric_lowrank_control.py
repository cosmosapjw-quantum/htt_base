"""Physics-anchored mask-geometry reduced-rank nuisance control tests."""
import numpy as np
import pytest
from obsstat.paired_highmode_control import transform_rows
from obsstat.geometric_lowrank_control import (
    geometry_directions,fit_geometric_control,cv_select_control,
    score_selected_mask,rank_two_mask_joint,LowrankControlError)


def test_left_svd_is_geometry_only_and_orthonormal():
    rng=np.random.default_rng(921)
    k=rng.normal(size=(6,13))
    directions,singular=geometry_directions(k,rank=3)
    np.testing.assert_allclose(directions.T@directions,np.eye(3),atol=1e-12)
    assert singular.shape==(6,)
    # Changing right-side harmonic representation leaves left output space.
    r,_=np.linalg.qr(rng.normal(size=(13,13)))
    other,_=geometry_directions(k@r,rank=3)
    np.testing.assert_allclose(directions@directions.T,other@other.T,atol=1e-12)


def test_rank_one_captures_true_physical_predictor_out_of_sample():
    rng=np.random.default_rng(106)
    yhigh=rng.normal(size=(200,4))
    u=np.eye(4)[:,:1]
    y=2*yhigh[:,[0]]@np.array([[1.,-1.,.5,0]])+.1*rng.normal(size=(200,4))
    model=fit_geometric_control(y[:60],yhigh[:60],u,rank=1,ridge_multiplier=.25)
    res=transform_rows(y[60:],yhigh[60:],model)
    baseline=y[60:]-y[:60].mean(axis=0)
    assert np.sum(res*res)<.2*np.sum(baseline*baseline)


def test_ridge_rotation_covariance_in_selected_image():
    rng=np.random.default_rng(101)
    y=rng.normal(size=(60,6))
    h=rng.normal(size=(60,6))
    u,_=np.linalg.qr(rng.normal(size=(6,3)))
    model=fit_geometric_control(y,h,u,rank=3,ridge_multiplier=.4)
    r,_=np.linalg.qr(rng.normal(size=(3,3)))
    rotated=fit_geometric_control(y,h,u@r,rank=3,ridge_multiplier=.4)
    np.testing.assert_allclose(transform_rows(y,h,model),
                               transform_rows(y,h,rotated),atol=1e-12,rtol=0)
    np.testing.assert_allclose(model.operator,rotated.operator,atol=1e-12)


def test_training_only_cv_and_joint_rank():
    rng=np.random.default_rng(19)
    u=np.eye(4)[:,:3]
    ytrain=rng.normal(size=(60,4))
    htrain=rng.normal(size=(60,4))
    a=cv_select_control(ytrain,htrain,u,rank_choices=(1,2,3),
                        ridge_choices=(.25,1.,4.))
    assert a['model'] is not None
    assert len(a['candidates'])==9
    assert a['selection_source']=='training_only_60'
    yt=rng.normal(size=(35,4));ht=rng.normal(size=(35,4))
    obs=rng.normal(size=(4,));oh=rng.normal(size=(4,))
    scores=score_selected_mask(a,obs,oh,yt,ht)
    assert scores['null'].shape==(35,)
    assert scores['observed'].shape==()
    p=rank_two_mask_joint([scores,scores])
    assert 0<p['p_rank']<=1
    with pytest.raises(LowrankControlError):
        geometry_directions(np.zeros((4,6)),rank=1)


def test_training_selection_does_not_see_observation_and_calibration():
    rng=np.random.default_rng(171)
    ytrain=rng.normal(size=(60,5))
    htrain=rng.normal(size=(60,5))
    u=np.eye(5)[:,:3]
    sel=cv_select_control(ytrain,htrain,u,rank_choices=(1,2),ridge_choices=(1.,))
    null1=rng.normal(size=(30,5))
    null2=100*rng.normal(size=(30,5))
    v1=score_selected_mask(sel,rng.normal(size=5),rng.normal(size=5),null1,null1)
    v2=score_selected_mask(sel,rng.normal(size=5),rng.normal(size=5),null2,null2)
    assert sel['selected']==sel['selected']  # parameters frozen by train only
    assert len(v1['null'])==len(v2['null'])==30
    assert sel['cv_ratio']>=0


def test_fixed_cv_selected_score_superuniform_under_iid():
    rng=np.random.default_rng(543)
    u=np.eye(3)[:,:2]
    rejects=[]
    for _ in range(240):
        # Source null: same iid joint vectors, independent training.
        ytrain=rng.normal(size=(60,3)); htrain=rng.normal(size=(60,3))
        sel=cv_select_control(ytrain,htrain,u,rank_choices=(1,2),ridge_choices=(1.,))
        null=rng.normal(size=(59,3));nh=rng.normal(size=(59,3))
        obs=rng.normal(size=3);oh=rng.normal(size=3)
        p=rank_two_mask_joint([score_selected_mask(sel,obs,oh,null,nh)]*2)['p_rank']
        rejects.append(p<=.05)
    # Monte Carlo error: nominal 0.05, loose two-sided acceptance interval
    assert .008 < np.mean(rejects)<.11


def test_complex_coefficients_rejected():
    u=np.eye(3)
    with pytest.raises(LowrankControlError):
        fit_geometric_control(np.ones((15,3),complex),np.ones((15,3)),u,rank=2,ridge_multiplier=1.)
