from fractions import Fraction as F
import numpy as np
import pytest
from htt.infer.r8_support import factor_support,contains_residual,reduced_quadratic,log_density

def test_rational_support_and_normalized_density():
    law=factor_support([[F(3,5)],[F(4,5)]],[[4]],{'source':'V06','semantics':'EXACT_STRUCTURAL'})
    r=[F(6,5),F(8,5)]
    assert contains_residual(law,r)=='ACCEPT' and reduced_quadratic(law,r)==1
    assert contains_residual(law,[F(2,5),F(11,5)])=='REJECT'
    assert abs(log_density(law,r)-(-.5*(np.log(8*np.pi)+1)))<1e-12

def test_rounded_support_stays_unresolved_and_rank_zero():
    law=factor_support([[.6],[.8]],[[4]],{'source':'rounded','semantics':'ROUNDED_UNCERTAIN'})
    assert contains_residual(law,[1.2,1.6])=='UNRESOLVED'
    assert contains_residual(law,[0,0])=='UNRESOLVED'
    zero=factor_support(np.empty((2,0)),np.empty((0,0)),{'source':'zero','semantics':'EXACT_STRUCTURAL'})
    assert contains_residual(zero,[0,0])=='ACCEPT' and reduced_quadratic(zero,[0,0])==0
    assert contains_residual(zero,[0,1])=='REJECT'

def test_duplicate_coordinates_add_no_information_and_bad_factors_refuse():
    p={'source':'fixture','semantics':'EXACT_STRUCTURAL'}
    a=factor_support([[1]],[[4]],p);b=factor_support([[1],[1]],[[4]],p)
    assert reduced_quadratic(a,[2])==reduced_quadratic(b,[2,2])==1
    for B,V in [([[1,1]],[[1,0],[0,1]]),([[1]],[[0]]),([[1,0],[0,1]],[[1,1],[0,1]]),([[np.nan]],[[1]])]:
        with pytest.raises(ValueError):factor_support(B,V,p)
