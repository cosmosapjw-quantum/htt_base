"""Exact finite design q-information nuisance ablation, not cosmological q."""
import numpy as np
import pytest
from obsstat.cf4_q_nuisance_ablation import (
  compare_nuisance_stages,NuisanceAblationError)


def test_nested_nuisance_can_only_remove_information():
    rng=np.random.default_rng(920)
    n=150
    z=rng.normal(size=(n,1))
    q=np.column_stack([z[:,0],rng.normal(size=n),rng.normal(size=n)])
    h=np.column_stack([z,rng.normal(size=(n,1))])
    cubic=np.column_stack([z**2,rng.normal(size=(n,1))])
    stages={'unrestricted':np.empty((n,0)),
            'H':h,'H_plus_cubic':np.column_stack((h,cubic))}
    x=compare_nuisance_stages(q,np.ones(n),stages)
    eig=x['stages']
    assert min(eig['unrestricted']['relative_information_eigenvalues'])==pytest.approx(1)
    assert eig['H']['weakest_relative_information'] < .1
    assert eig['H_plus_cubic']['weakest_relative_information']<=eig['H']['weakest_relative_information']+1e-11
    assert eig['H_plus_cubic']['mean_relative_information']<=eig['H']['mean_relative_information']+1e-11


def test_invariant_under_parameter_basis_and_global_weight_scaling():
    rng=np.random.default_rng(811)
    q=rng.normal(size=(130,3))
    v=rng.normal(size=(130,7))
    A=rng.normal(size=(3,3))
    w=np.linspace(.2,2,130)
    x=compare_nuisance_stages(q,w,{'A':v})['stages']['A']
    y=compare_nuisance_stages(q@A,20*w,{'A':v})['stages']['A']
    np.testing.assert_allclose(x['relative_information_eigenvalues'],
                               y['relative_information_eigenvalues'],rtol=2e-9,atol=1e-10)


def test_rejects_invalid_and_complex_weights():
    rng=np.random.default_rng(44)
    q=rng.normal(size=(44,3))
    w=np.ones(44)
    w[0]=-1
    with pytest.raises(NuisanceAblationError):
        compare_nuisance_stages(q,w,{'none':None})
    with pytest.raises(NuisanceAblationError):
        compare_nuisance_stages(q.astype(complex),np.ones(44),{'none':None})


def test_exact_radial_alias_and_small_shell_fourth_power():
    from obsstat.cf4_q_nuisance_ablation import exact_radial_alias_bound
    rng=np.random.default_rng(344)
    n=rng.normal(size=(70,3));n/=np.linalg.norm(n,axis=1,keepdims=True)
    w=np.exp(rng.normal(scale=.2,size=70))
    z0=.04
    samples=rng.normal(size=70)
    x=[]
    for eps in (.0005,.001):
        r=exact_radial_alias_bound(z0+eps*samples,n,w,pivot_z=z0)
        assert r['exact_identity_max_abs_residual']<1e-14
        assert r['actual_best_H_and_cubic_weighted_squared_ratio']<=r['constructive_upper_squared_ratio']+1e-14
        x.append(r['constructive_upper_squared_ratio'])
    # Small-shell 2x width --> fourth-moment energy roughly 16x.
    assert x[1]/x[0] == pytest.approx(16,rel=.03)
