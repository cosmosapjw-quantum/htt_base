import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

PATH=Path(__file__).with_name('compute.py')
sys.path.insert(0,str(PATH.parents[5]))
spec=importlib.util.spec_from_file_location('r25_conditional_gram',PATH)
c=importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def test_canonical_bridge_and_decode_all60():
    from htt.obsstat.planck_lowell_irrep_projection import (
        real_harmonic_l2_to_stf,real_harmonic_l3_to_stf,
        stf2_to_real_harmonic,stf3_to_real_harmonic)
    rows,X=c.load()
    raw=c.raw_from_canonical(X)
    assert np.max(abs(c.canonical(raw)-X))<1e-20
    for row,r in zip(rows,raw):
        assert np.max(abs(r-row['harmonic12_K_CMB']))<1e-20
        q,o=c.tensors_from_raw(r)
        qr=real_harmonic_l2_to_stf(r[:5]); or_=real_harmonic_l3_to_stf(r[5:])
        assert np.max(abs(q-qr))<1e-18
        assert np.max(abs(o-or_))<1e-18
        assert np.max(abs(stf2_to_real_harmonic(q)-r[:5]))<1e-18
        assert np.max(abs(stf3_to_real_harmonic(o)-r[5:]))<1e-18
        assert np.max(abs(q))>0 and np.max(abs(o))>0
    assert c.controls(X)['bridge_max_absolute_K']<1e-18


def test_shared_gram_rotations_shape_parity():
    _,X=c.load(); rng=np.random.default_rng(3)
    g2=X[:,:5]@X[:,:5].T; g3=X[:,5:]@X[:,5:].T
    observed=c.statistics(X)
    for law in ('H_orient','H_Gram'):
        Y=c.draw(rng,law,96,X)
        assert np.max(abs(np.einsum('bvi,bwi->bvw',Y[:,:,:5],Y[:,:,:5])-g2))/np.max(abs(g2))<1e-11
        assert np.max(abs(np.einsum('bvi,bwi->bvw',Y[:,:,5:],Y[:,:,5:])-g3))/np.max(abs(g3))<1e-11
        S=c.statistics(Y)
        assert np.min(S)>=-1e-11 and np.max(S)<=1+1e-11
        if law=='H_orient':
            assert np.max(abs(S[:,:,:2]-observed[None,:,:2]))<1e-11
        else:
            assert np.max(np.std(S[:,:,:2],axis=0))>.01
    # Reflect a Cartesian axis: even statistics cannot distinguish mirror parity.
    m=np.diag([-1.,1.,1.]); q,o=c.tensors_from_raw(c.raw_from_canonical(X[0]))
    q2=np.einsum('ia,jb,ab->ij',m,m,q)
    o2=np.einsum('ia,jb,kc,abc->ijk',m,m,m,o)
    assert np.isclose(np.linalg.norm(q2),np.linalg.norm(q))
    assert np.isclose(np.linalg.norm(o2),np.linalg.norm(o))
    y2=q2.ravel()@c.DUAL2
    y3=o2.ravel()@c.DUAL3
    np.testing.assert_allclose(c.statistics(np.r_[y2,y3]),c.statistics(X[0]),rtol=1e-10,atol=1e-12)
    assert np.all(np.isfinite(c.statistics(X)))


def test_independent_view_actions_break_crossview_gram():
    _,X=c.load(); rng=np.random.default_rng(9)
    separate=np.array([c.draw(rng,'H_Gram',1,X)[0,v] for v in range(60)])
    assert abs(np.dot(separate[0,:5],separate[1,:5])-np.dot(X[0,:5],X[1,:5]))>1e-15


def test_zero_isotropic_repeated_eigenvalue_and_statistic_oracle():
    _,X=c.load()
    with pytest.raises(ValueError,match='zero tensor norm'):
        c.statistics(np.zeros((1,12)))
    # Pure m=0 has a repeated eigenvalue. No eigensolver or axis tie-break is used.
    z=np.zeros(12); z[0]=2e-6; z[5]=3e-6
    assert np.all(np.isfinite(c.statistics(z)))
    q,o=c.tensors_from_raw(c.raw_from_canonical(X[0]))
    A=q/np.linalg.norm(q); B=o/np.linalg.norm(o)
    C=np.zeros((3,3))
    for i in range(3):
        for j in range(3):
            C[i,j]=sum(B[i,k,l]*B[j,k,l] for k in range(3) for l in range(3))-(i==j)/3
    t=6*np.trace(A@A@A)**2
    oracle=np.array([t,1.5*np.sum(C*C),1.5*np.sum(A*C)**2,
        sum(sum(B[i,j,k]*A[j,k] for j in range(3) for k in range(3))**2 for i in range(3))])
    np.testing.assert_allclose(c.statistics(X[0]),oracle,rtol=1e-10,atol=1e-12)


def test_rank_ties_strict_and_moment_theorem():
    p=np.ones((5,2)); v=np.ones((4,2))
    assert np.all(c.rank_tail(p,v)==1)
    assert np.all(c.rank_tail(np.ones((5,3,2)),np.ones((4,3,2)))==1)
    assert c.rank_tail(np.array([[2.],[3.],[3.]]),np.array([[3.]])).item()==.75
    assert c.clopper_pearson(0,16383)[0]==0
    assert c.clopper_pearson(16383,16383)[1]==1
    _,X=c.load()
    for law in ('H_orient','H_Gram'):
        check=c.mc_moments(X,law,n=2048)
        assert check['passed']
