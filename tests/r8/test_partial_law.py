from fractions import Fraction as F
import numpy as np
import pytest
from htt.infer.r8_partial_law import marginal_acceptance,moment_acceptance,gaussian_marginal,require_joint_gaussian

def test_fixed_allocations_and_missing_scope():
    allocation={'a':F(1,80),'b':F(1,80)}
    block=gaussian_marginal(2.4,lambda x:x['theta'],1.,'declared V05 marginal')
    assert marginal_acceptance({'a':block},{'theta':0},allocation)=='ACCEPT'
    assert marginal_acceptance({'a':block},{'theta':-2},allocation)=='REJECT'
    with pytest.raises(ValueError):marginal_acceptance({'c':block},{'theta':0},allocation)

def test_gaussian_marginals_do_not_admit_joint_gaussian():
    with pytest.raises(ValueError):require_joint_gaussian({'marginals':'GAUSSIAN','covariance':np.eye(2)})
    # Y=(Z,SZ) has covariance I but its squared coordinates are identical.
    z=np.arange(-4,5,dtype=float);y=np.stack([z,(-1.)**np.arange(len(z))*z],1)
    assert np.array_equal(y[:,0]**2,y[:,1]**2)

def test_moment_zero_variance_and_bias_contract():
    assert moment_acceptance([0,1],[0,0],[0,1],F(1,20))=='ACCEPT'
    assert moment_acceptance([1,0],[0,0],[0,1],F(1,20))=='REJECT'
    assert moment_acceptance([0,0],[0,0],[0,0],F(1,20))=='ACCEPT'
    for v in ([-1],[float('nan')]):
        with pytest.raises(ValueError):moment_acceptance([0],[0],v,F(1,20))

def test_scalar_normal_quantile_does_not_reject_rounding_boundary():
    from htt.infer.r8_partial_law import gaussian_marginal,normal_critical_square
    from fractions import Fraction as F
    law=gaussian_marginal(1.150349380376008,float,1.,'REVIEW_BOUNDARY')
    assert law.accept(0.,F(1,4))!='REJECT'
    lo,hi=normal_critical_square(F(1,4))
    assert lo<hi and hi-lo<F(1,10**12)

def test_integer_chi_square_quantile_enclosures_against_high_precision_cdf():
    import mpmath as mp
    from fractions import Fraction as F
    from htt.infer.r8_partial_law import chi_critical_bounds,QuantileUnresolved
    with mp.workdps(80):
        for rank in (0,1,2,3,5,12,32):
            lo,hi=chi_critical_bounds(F(1,20),rank)
            if not rank:assert lo==hi==0;continue
            cdf=lambda z:mp.gammainc(mp.mpf(rank)/2,0,mp.mpf(z.numerator)/z.denominator/2,regularized=True)
            assert cdf(lo)<=mp.mpf(19)/20<=cdf(hi)
            assert hi-lo<F(1,10**10)
    with pytest.raises(QuantileUnresolved):chi_critical_bounds(F(1,20),257)
