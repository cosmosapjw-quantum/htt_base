from pathlib import Path
import sys
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from h02_calibration_fisher import *
from l03_paired_scan import *
BASE=Path(__file__).resolve().parents[1]

def test_schur_vs_dense_marginal_with_intercept():
    rng=np.random.default_rng(27)
    x=rng.normal(size=(35,8))
    s=rng.uniform(.15,.8,size=35)
    m=np.asarray(['M']*35)
    G,_,_=method_grams(x,m,s,labels=('M',))
    tau=.13
    # Directly integrate angular nuisance in *data space*, then profile intercept.
    C=np.diag(s*s)+tau*tau*x@x.T
    Z=np.ones((len(x),1))
    Ci=np.linalg.inv(C)
    precision=Ci-Ci@Z@np.linalg.inv(Z.T@Ci@Z)@Z.T@Ci
    direct=x.T@precision@x
    fast=info_marginal(G,tau)
    assert np.allclose(direct,fast,rtol=1e-10,atol=1e-9)

def test_multiple_grammar_shapes():
    g={'A':np.diag(np.arange(1,9,dtype=float)),
       'B':np.diag(np.arange(10,18,dtype=float))}
    tau=.3
    x=info_marginal(g,tau)
    expect=sum(v/(1+tau**2*v) for v in [np.arange(1,9),np.arange(10,18)])
    assert np.allclose(np.diag(x),expect)
    assert np.max(np.abs(x-np.diag(np.diag(x))))<1e-14

def test_source_rank_monotonic():
    p=BASE/'inputs/selected_source_observables.npz'
    n,m,s,z=read_source(p)
    grams,_,_=method_grams(shape8(n),m,s)
    eig=np.linalg.eigvalsh(info_marginal(grams,2))
    assert np.allclose(eig,np.ones(8),rtol=1e-4,atol=1e-4)
    assert np.linalg.eigvalsh(info_marginal(grams,0)).min()>1e4

def test_one_sky_per_condition_and_calibration_permutation():
    obs,bank=read_bank(BASE/'inputs/processing_coefficients.npz')
    a=process_scan(obs,bank)
    rng=np.random.default_rng(22)
    order=rng.permutation(200)
    perm=bank.copy();perm[:,100:]=bank[:,100:][:,order]
    b=process_scan(obs,perm)
    assert a['descriptive_rank_p']==b['descriptive_rank_p']
    assert np.allclose(a['method_energy_correlation_lower_tri'],b['method_energy_correlation_lower_tri'])

def test_invalid_source_mutation_rejected(tmp_path):
    p=BASE/'inputs/selected_source_observables.npz'
    bad=tmp_path/'bad.npz'; b=p.read_bytes();bad.write_bytes(b[:-1]+bytes([b[-1]^1]))
    with pytest.raises(ValueError,match='SHA'):
        read_source(bad)
    p2=BASE/'inputs/processing_coefficients.npz'; bad2=tmp_path/'bad2.npz';b=p2.read_bytes();bad2.write_bytes(b[:-1]+bytes([b[-1]^1]))
    with pytest.raises(ValueError,match='hash'):read_bank(bad2)
