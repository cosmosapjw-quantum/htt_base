import sys,math
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from h02_calibration_fisher import *
DATA=Path(__file__).resolve().parents[1]/'inputs/selected_source_observables.npz'

def test_source_hash():
    n,m,s,z=read_source(DATA)
    assert n.shape==(35970,3) and np.sum(m=='FP')==26916

def test_fixed_source_gauge():
    n,m,s,z=read_source(DATA);x=shape8(n)
    assert nuisance_span_residual(x,m)==0
    assert demeaning_invariant(s,m,1/s**2,-0.147)<1e-12

def test_calibration_limit():
    g={'M':np.diag([2000.,500.])};A=info_marginal(g,0);B=info_marginal(g,0.1)
    assert np.allclose(np.diag(B),[2000/21.,500/6.],atol=1e-12)
    assert np.allclose(info_marginal(g,float('inf')),0)
    assert np.array_equal(A,np.diag([2000,500]))

def test_gram_positive():
    n,m,s,z=read_source(DATA);g,means,counts=method_grams(shape8(n),m,s)
    assert counts=={'FP':26916,'TF':7614,'SN':700,'OTHER':740}
    assert all(np.linalg.eigvalsh(v).min()>0 for v in g.values())
    e0=np.linalg.eigvalsh(info_marginal(g,0))
    e1=np.linalg.eigvalsh(info_marginal(g,.02))
    assert np.all(e1<=e0) and np.all(e1>0)

def test_rank_and_anchor():
    n,m,s,z=read_source(DATA);g,_,_=method_grams(shape8(n),m,s)
    assert conditional_standard_errors(info_marginal(g,float('inf')))==[None]*8
    assert np.linalg.eigvalsh(info_marginal(g,float('inf'),anchored=['FP'])).min()>0

def test_fixed_method_prior_no_physical_claim():
    r=diagnostics(DATA)
    assert r['global_method_angular_design_exact_null_max']==0
    assert r['grid'][0]['rank_numerical']==8
    assert r['grid'][-1]['rank_numerical']==0
    assert 'H02_PENDING' in r['admission']

def test_bad_inputs():
    with pytest.raises(ValueError):info_marginal({'A':np.eye(2)},-0.1)
    with pytest.raises(ValueError):shape8(np.ones((8,4)))
