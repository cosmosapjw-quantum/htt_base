from pathlib import Path
import sys
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from signed_sector_box import bounds,run


def test_zero_width_inputs_exact():
    a=bounds([70,70],[9,9],[16,16],[0,0],[-.001,-.001],[.03,.03])
    expected=((9-16)/(6*70**2)-.001)/(1.5*.03**2)
    assert np.allclose(a['Q'],[expected,expected],atol=1e-13)
    assert a['Q'][0]<0

def test_signed_crossing_zero_and_no_zero_fill():
    a=run()['manufactured_example']
    assert a['x_C'][0]<0<a['x_C'][1]
    assert a['Q'][0]<0<a['Q'][1]
    assert a['U_sigma'][0]>0
    assert run()['physical_exceedance_unknown_mass']==1


def test_extrema_match_grid_corners():
    h=[68.,72.];sigma=[1.,16.];omega=[0.,25.];tilt=[-.001,.002];curv=[-.002,.003];B=[.03,.05]
    result=bounds(h,sigma,omega,tilt,curv,B)
    vals=[];xs=[]
    from itertools import product
    for H,S,W,T,K,b in product(h,sigma,omega,tilt,curv,B):
        x=(S-W)/(6*H*H)+T+K;xs.append(x);vals.append(x/(1.5*b*b))
    assert np.allclose(result['x_C'],[min(xs),max(xs)])
    assert np.allclose(result['Q'],[min(vals),max(vals)])


def test_nonpositive_mes_or_h_rejected():
    cases=[([0,70],[0,1],[0,1],[0,0],[0,0],[.01,.02]),
           ([70,80],[0,1],[0,1],[0,0],[0,0],[0,.02]),
           ([70,80],[-1,1],[0,1],[0,0],[0,0],[.01,.02]),
           ([70,80],[0,1],[0,1],[0,0],[0,0],[.2,.1])]
    for c in cases:
        with pytest.raises(ValueError):bounds(*c)


def test_negative_numerator_monotonic_not_wrong_H_corner():
    a=bounds([1.,3.],[0.,0.],[2.,4.],[0.,0.],[0.,0.],[1.,1.])
    assert np.isclose(a['x_C'][0],-4/6)
    assert np.isclose(a['x_C'][1],-2/(6*9))
