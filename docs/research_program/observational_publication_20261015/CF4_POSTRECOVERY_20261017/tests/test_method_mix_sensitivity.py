import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from method_mix_sensitivity import method_mixture_bound

def test_vertex_extrema_are_exact_by_random_points():
    cnt=np.array([10,30,1],float);f=np.array([[0.,0],[1.,0],[0,1.]])
    a=method_mixture_bound(cnt,f,2.5)
    r=np.random.default_rng(0)
    w=r.uniform(1/2.5,2.5,size=(1000,3))
    x=((w*cnt)@f)/(w@cnt)[:,None]
    assert np.all(x>=np.asarray(a['lower'])-1e-12)
    assert np.all(x<=np.asarray(a['upper'])+1e-12)

def test_equal_weight_limit_fixed():
    a=method_mixture_bound([2,4],[[1,0,0],[-1,0,0]],1.)
    assert np.allclose(a['lower'],a['upper'])
    assert np.isclose(a['lower'][0],-1/3)

def test_unphysical_weight_refusal():
    with pytest.raises(ValueError):method_mixture_bound([1,2],[[0,0],[1,0]],.9)
    with pytest.raises(ValueError):method_mixture_bound([1,0],[[0],[1]],2.)
