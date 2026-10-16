import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import pytest
from h03_method_gauge import calibration_rank
from h03_tomography import METHODS

def data(seed=48,n=280):
 r=np.random.default_rng(seed);d=r.uniform(30,280,size=n);ang=r.normal(size=(n,3));ang/=np.linalg.norm(ang,axis=1)[:,None]
 m=np.array(METHODS)[np.arange(n)%4];w=r.uniform(.5,2.5,size=n)
 return d,ang,w,m

def test_mean_zero_point_global_rescaling_gauge():
 r=calibration_rank(*data())
 assert r['mean_design_rank']==12 and r['remaining_theta_rank']==8
 assert r['explicit_monopole_equals_sum_methods_relative_residual']<1e-14
 assert r['mean_design_nullity']==1 and r['remaining_theta_nullity']==1

def test_forbid_missing_method_family():
 d,n,w,m=data();m[:]='TF'
 with pytest.raises(ValueError):calibration_rank(d,n,w,m)
