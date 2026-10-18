"""Finite-null-safe train/calibration separation and physics-response regression."""
import numpy as np
import pytest
from obsstat.paired_highmode_control import (
  fit_control, transform_rows, rank_upper_tail, fit_family,
  run_fixed_family, PairedHighModeError)


def test_conditional_response_recovers_known_linear_relation():
    rng=np.random.default_rng(30)
    h=rng.normal(size=(200,4))
    transfer=np.array([[1,0,0,0],[0,2,0,0],[0,0,0.5,0],[0,0,0,1.]])
    y=h@transfer+0.05*rng.normal(size=(200,4))
    fit=fit_control(y,h,ridge_multiplier=.25,cov_shrink=.2)
    assert fit.operator.shape==(4,4)
    residual=transform_rows(y,h,fit)
    assert np.mean(np.sum(residual**2,axis=1)) < .2*np.mean(np.sum((y-y.mean(axis=0))**2,axis=1))
    assert np.min(np.linalg.eigvalsh(fit.covariance))>0


def test_null_covariance_stress_and_invariance():
    rng=np.random.default_rng(44)
    y=rng.normal(size=(80,4))
    h=rng.normal(size=(80,4))
    for factor in (1e-3,1,30):
        r=fit_control(y*factor,h*factor,ridge_multiplier=1,cov_shrink=.2)
        new=transform_rows(y*factor,h*factor,r)
        assert np.isfinite(new).all()
        np.testing.assert_allclose(r.scaled_scores(new),
            fit_control(y,h,ridge_multiplier=1,cov_shrink=.2).scaled_scores(
                transform_rows(y,h,fit_control(y,h,ridge_multiplier=1,cov_shrink=.2))),
            rtol=1e-10,atol=1e-10)


def test_plus_one_rank_and_ties():
    assert rank_upper_tail(3,np.array([2,2,4,3])) == {'exceedances':2,'B':4,'p_rank':.6}
    assert rank_upper_tail(5,np.array([2,3,4]))['p_rank']==.25


def test_family_frozen_on_train_and_handles_same_sky_columns():
    rng=np.random.default_rng(321)
    arr=rng.normal(size=(301,2,2,4))
    # 1 observed row plus 60 independent training and 240 calibration.
    observed=arr[0];train=arr[1:61];cal=arr[61:]
    result=run_fixed_family(observed,train,cal,ridge_multipliers=(.25,1,4),cov_shrink=.2)
    assert len(result['per_feature'])==8
    assert result['global_rank']['B']==240
    assert result['null_maxima'].shape==(240,)
    assert result['observed_scores'].shape==(8,)
    assert result['training_models']['0:0.25'].operator.shape==(4,4)
    with pytest.raises(PairedHighModeError):
        run_fixed_family(observed,train,cal,ridge_multipliers=(0.,1),cov_shrink=.2)


def test_fixed_trained_transform_is_exchangeability_safe_simulation():
    rng=np.random.default_rng(1029)
    probs=[]
    for _ in range(500):
        rows=rng.normal(size=(61,2,2,3))
        train=rng.normal(size=(24,2,2,3))
        result=run_fixed_family(rows[0],train,rows[1:],ridge_multipliers=(1.,),cov_shrink=.2)
        probs.append(result['global_rank']['p_rank'])
    # Loose Monte Carlo calibration bound, method is finite-rank valid under iid.
    assert .025 < np.mean(np.asarray(probs)<=.05) < .095


def test_rotating_full_harmonic_basis_preserves_frozen_scores():
    rng=np.random.default_rng(6791)
    arr=rng.normal(size=(101,2,2,4))
    training=rng.normal(size=(45,2,2,4))
    base=run_fixed_family(arr[0],training,arr[1:],
                          ridge_multipliers=(.25,1,4),cov_shrink=.2)
    u,_=np.linalg.qr(rng.normal(size=(4,4)))
    changed=run_fixed_family(arr[0]@u,training@u,arr[1:]@u,
                          ridge_multipliers=(.25,1,4),cov_shrink=.2)
    np.testing.assert_allclose(base['observed_scores'],changed['observed_scores'],
                               rtol=1e-10,atol=1e-10)
    np.testing.assert_allclose(base['null_maxima'],changed['null_maxima'],
                               rtol=1e-10,atol=1e-10)
    assert base['global_rank']==changed['global_rank']


def test_no_silent_complex_harmonic_to_real_cast():
    with pytest.raises(PairedHighModeError):
        fit_control(np.ones((12,3),complex),np.ones((12,3)),ridge_multiplier=1,cov_shrink=.2)
    with pytest.raises(PairedHighModeError):
        rank_upper_tail(2.,np.array([1.,2.+0.j]))
