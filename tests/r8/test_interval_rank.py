from fractions import Fraction as F
import math
import numpy as np
import pytest
from htt.infer.r8_interval_rank import rank_from_score_bounds, rank_envelope

def test_wide_bounds_determine_rank():
    out=rank_from_score_bounds([(0,3)]*4+[(7,10)],4,F(1,20))
    assert out.p_lower==out.p_upper==F(1,5) and out.decision=='NON_REJECT'

def test_inclusive_ties():
    out=rank_from_score_bounds([(0,1)]+[(0,0)]*30,0,F(1,20))
    assert out.p_upper==1
    assert rank_from_score_bounds([(0,0)]*31,0,F(1,20)).p_lower==1

@pytest.mark.parametrize('m,k,limit',[(301,18,14),(1000,32,49)])
def test_exact_thresholds(m,k,limit):
    bounds=[(3,3)]+[(4,4)]*limit+[(0,0)]*(m-limit-1)
    out=rank_from_score_bounds(bounds,0,F(1,20))
    assert out.k==k and out.decision=='REJECT'
    bounds[limit+1]=(3,3)
    assert rank_from_score_bounds(bounds,0,F(1,20)).decision=='NON_REJECT'

def test_pair_kth_symmetry_permutation_and_nan():
    x=np.array([0.,1.,2.,3.,10.]);d=np.abs(x[:,None]-x)
    out=rank_envelope(np.stack([d,d],axis=-1),4,2,F(1,20))
    assert out.score_bounds==((2.,2.),(1.,1.),(1.,1.),(2.,2.),(8.,8.))
    p=[4,2,0,3,1]
    assert rank_envelope(np.stack([d[np.ix_(p,p)]]*2,-1),0,2,F(1,20)).p_upper==out.p_upper
    bad=np.stack([d,d],-1);bad[0,1,0]=np.nan
    with pytest.raises(ValueError):rank_envelope(bad,0,2,F(1,20))
    with pytest.raises(ValueError):rank_envelope(np.stack([d,d],-1),4,1,F(1,20))
    with pytest.raises(ValueError):rank_from_score_bounds([(0,1)]*3,0,.05)
