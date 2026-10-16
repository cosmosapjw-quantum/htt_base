import sys,importlib.util
from pathlib import Path
import numpy as np
import pytest
path=Path(__file__).resolve().parents[1]/'src/selection_identifiability.py'
s=importlib.util.spec_from_file_location('selection_identifiability',path)
m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)

def test_two_population_selection_models_identical_observed_sample():
    q=np.array([.7,.2,.1]);p1=np.array([.3,.2,.5]);p2=np.array([.05,.8,.15])
    a=m.selection_equivalent_parents(q,p1)
    b=m.selection_equivalent_parents(q,p2)
    assert np.allclose(q,p1*a/(p1@a),atol=1e-13)
    assert np.allclose(q,p2*b/(p2@b),atol=1e-13)
    assert not np.allclose(a,b)
    assert a.max()<=1+1e-13 and b.max()<=1+1e-13

def test_degenerate_selection_rejected():
    with pytest.raises(ValueError):m.selection_equivalent_parents([1,0],[.5,.5])
    with pytest.raises(ValueError):m.selection_equivalent_parents([2,1],[.5,.5])

def test_common_calibration_covariance_not_identified():
    sig=np.array([.2,.5,.3,.1]);cov0=m.indistinguishable_calibration_covariance(sig,0.)
    cov9=m.indistinguishable_calibration_covariance(sig,.9)
    assert np.allclose(np.diag(cov0),np.diag(cov9))
    assert not np.allclose(cov0,cov9)
    assert np.linalg.eigvalsh(cov9).min()>0

def test_duplicate_aggregation_error():
    d=m.double_count_factor(.09,2)
    assert d['true_information_rank']==1
    assert np.isclose(d['incorrect_iid_variance'],.045)
    assert np.isclose(d['true_variance'],.09)

def test_profiled_design_projection_rank():
    z=np.array([[1,0],[1,0],[0,1],[0,1],[1,1]],float)
    x=np.array([[1,0],[0,1],[1,1],[2,1],[1,-1]],float)
    c=m.fit_profile_nullspace(z,x)
    assert c['rank_calibration_design']==2
    assert c['rank_angular_after_calibration']==2
    assert c['rank_joint']==4
