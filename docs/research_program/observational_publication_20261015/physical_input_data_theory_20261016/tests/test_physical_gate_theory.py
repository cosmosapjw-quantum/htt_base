import math
import numpy as np
import pytest
from research.physical_gate_theory import (
    partial_interval,exceedance_bounds,selected_normal_loglike,
    truncated_gaussian_mean_positive,witness_L03_same_sky,history_design,
    sky_directions,radial_tangential_joint,jacobi_majorant,physical_bianchi_registry)

def test_s04_missing_preservation_and_sign():
    lo,hi=partial_interval(-0.2,None,0.3)
    assert lo==-math.inf and hi==pytest.approx(0.1)
    assert exceedance_bounds([.2,.5,.3],[-1.,None,2.],0)==(.3,.8,.5)
    with pytest.raises(ValueError):exceedance_bounds([.2,.7],[-1.,None],0)

def test_h02_truncation_normalized():
    from scipy.integrate import quad
    mu=0.4; sigma=1.2
    assert abs(quad(lambda x: math.exp(selected_normal_loglike(x,mu,sigma,low=0)),1e-10,15)[0]-1)<2e-8

def test_h02_omitting_selection_bias():
    mu=0.;sigma=1.
    assert abs(truncated_gaussian_mean_positive(mu,sigma)-math.sqrt(2/math.pi))<1e-13
    assert selected_normal_loglike(1,mu,sigma,low=0)!=selected_normal_loglike(1,mu,sigma)

def test_h02_gaussian_tail_stability():
    val=selected_normal_loglike(9.3,mu=0.0,sigma=1.0,low=9.0,high=10.0)
    assert math.isfinite(val)

def test_l03_same_sky_not_independent():
    C,c=witness_L03_same_sky(Nsky=4096)
    assert C.shape==(4,4) and 0.88<c<0.96
    assert np.allclose(np.diag(C),1)

def test_v03_history_rank_defect():
    F,s=history_design()
    assert np.linalg.matrix_rank(F)==2
    assert np.allclose(F@np.array([1.,-1.,0.]),0)
    assert np.min(s)>0

def test_b02_admitted_subset():
    r=physical_bianchi_registry()
    assert len(r['canonical_11'])==11
    assert len(r['aniCLASS_near_FLRW'])==5
    assert r['full_all_m_complete'] is False

def test_k03_sky_radial_and_tangent_rank():
    n=sky_directions()
    A,J,R=radial_tangential_joint(n)
    assert np.linalg.matrix_rank(R,tol=1e-10)==6
    assert np.linalg.matrix_rank(A,tol=1e-10)==9
    # Nonradial data resolve three curl modes only if reference-frame spin is calibrated.
    assert np.linalg.matrix_rank(J,tol=1e-10)==9
    assert J.shape[1]==12

def test_k04_jacobi_positive_distance_bound():
    K=0.01; s=2.
    delta=jacobi_majorant(K,s)/s
    assert delta<1
    sqrtK=math.sqrt(K)
    Dmag=math.sin(s*sqrtK)/sqrtK
    assert abs(Dmag-s)<=jacobi_majorant(K,s)+1e-13

def test_h02_invalid_truncation_fail_closed():
    for kw in ({'low':1,'high':0},{'low':0,'high':1}):
        with pytest.raises(ValueError):selected_normal_loglike(-1,mu=0,sigma=1,**kw)
