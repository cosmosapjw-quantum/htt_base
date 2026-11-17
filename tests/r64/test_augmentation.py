import sys
from pathlib import Path
import numpy as np
from scipy import linalg

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/r64'))
from run_r64_augmented import profile_nuisance
from htt.htt.infer import r58_mixed_tensor_likelihood as mt


def test_nuisance_projection_equals_full_joint_gls_and_keeps_covariance():
    rng=np.random.default_rng(6408)
    x=rng.normal(size=(40,8));n=rng.normal(size=(40,5));y=rng.normal(size=40)
    a=rng.normal(size=(40,40));c=a@a.T+np.eye(40)
    full=mt.fit_linear(y,c,np.column_stack([x,n]))
    fit,_,_,meta=profile_nuisance(y,c,x,n,mt.fit_linear,np.ones(8))
    np.testing.assert_allclose(fit['estimate'],full['estimate'][:8],rtol=2e-11,atol=2e-12)
    np.testing.assert_allclose(fit['covariance'],full['covariance'][:8,:8],rtol=2e-11,atol=2e-12)
    np.testing.assert_allclose(fit['residual_chi2'],full['residual_chi2'],rtol=2e-12)
    assert meta['nuisance_rank']==5 and fit['dof']==full['dof']==27
    np.testing.assert_allclose(meta['complement'].T@meta['whitened_nuisance'],0.,atol=3e-15)


def test_free_nuisance_that_mimics_signal_preserves_identification_failure():
    rng=np.random.default_rng(6409)
    x=np.eye(24)[:,:6];n=x[:,:1]
    fit,_,_,meta=profile_nuisance(rng.normal(size=24),np.eye(24),x,n,mt.fit_linear,np.ones(6))
    # This exact orthogonal chart preserves the true algebraic-zero column.
    # Rank disagreement in a roundoff-ambiguous chart is still fail-closed.
    assert meta['nuisance_rank']==1
    assert fit['rank']==5
    assert not mt.linear_interval(fit,np.eye(6)[0])['identified']
