from fractions import Fraction as F
import itertools
import numpy as np
import pytest
from obsstat.r8_orbit_bounds import invariant_lower,refine_pair,chart_rotation,cell_radius

def axial():
    o=np.zeros((3,3,3));o[0,0,0]=2
    for indices in ((0,1,1),(0,2,2)):
        for p in set(itertools.permutations(indices)):o[p]=-1
    return o

def test_exact_scaling_multiplicities_zeros_and_repeated_spectra():
    q=np.diag([-1,0,1]);z=np.zeros((3,3,3));zero=np.zeros((3,3))
    for x,y,exact_squared in [((q,z),(2*q,z),2*10**10),((zero,axial()),(zero,2*axial()),10*10**10)]:
        b=invariant_lower(x,y,128)
        assert b.lo*b.lo <= exact_squared <= b.hi*b.hi
        assert float(b.hi-b.lo)<1e-8
    assert invariant_lower((zero,z),(zero,z),128).hi==0
    with pytest.raises(ValueError):invariant_lower((q*np.nan,z),(q,z),128)

def test_chart_rotations_are_exact_proper_and_radius_cover():
    for a in range(4):
        r=chart_rotation(a,[F(1,3),F(-2,3),F(1)])
        assert np.array_equal(r.T@r,np.eye(3,dtype=int))
        assert r[0,0]*(r[1,1]*r[2,2]-r[1,2]*r[2,1])-r[0,1]*(r[1,0]*r[2,2]-r[1,2]*r[2,0])+r[0,2]*(r[1,0]*r[2,1]-r[1,1]*r[2,0])==1
    assert cell_radius([(F(-1,20),F(1,20))]*3)<=F(7,40)

def test_pair_refinement_monotone_symmetric_bound_and_wrong_prior():
    q=np.diag([-1.,0,1])*1e-5;o=axial()*1e-5
    r=np.array([[.6,-.8,0],[.8,.6,0],[0,0,1]])
    op=np.einsum('ia,jb,kc,abc->ijk',r,r,r,o)
    x=(q,o);y=(q,op)
    a=refine_pair(x,y,None,0);b=refine_pair(x,y,a,8)
    assert a.lo<=b.lo<=b.hi<=a.hi
    assert refine_pair(y,x,b,0)==b
    with pytest.raises(ValueError):refine_pair((q,2*o),y,b,0)

def test_every_pair_large_pool_has_invariant_bound_and_exact_pair_contains():
    from obsstat.r8_orbit_bounds import initialize_pool
    q=np.diag([-1.,0,1.])*1e-5; o=axial()*1e-5
    rows=[(q*(i+1)/50,o*(i+1)/50) for i in range(50)]
    pool=initialize_pool(rows,tuple(map(str,range(50))))
    assert pool.bounds.shape==(50,50,2)
    assert np.count_nonzero(pool.bounds[:,:,0])==50*49
    for i,j in ((0,1),(0,49),(20,35)):
        exact=invariant_lower(rows[i],rows[j],128)
        assert F(pool.bounds[i,j,0])<=exact.lo<=exact.hi<=F(pool.bounds[i,j,1])
    with pytest.raises(ValueError):initialize_pool(rows,['duplicate']*50)

def test_finite_large_nonstf_is_not_admitted_by_overflowed_tolerance():
    with pytest.raises(ValueError):invariant_lower((np.eye(3)*1e200,np.zeros((3,3,3))),
                                                (np.zeros((3,3)),np.zeros((3,3,3))),128)

def test_stf_guard_scales_each_irrep_independently():
    with pytest.raises(ValueError):invariant_lower((np.eye(3)*1e-200,axial()*1e200),
                                                (np.zeros((3,3)),np.zeros((3,3,3))),128)
