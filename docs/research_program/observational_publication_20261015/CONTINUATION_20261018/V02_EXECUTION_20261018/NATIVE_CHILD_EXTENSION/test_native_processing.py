"""Independent finite controls for native synthesis and fixed child reduction."""
import healpy as hp
import numpy as np
import pytest
from native_processing import (design, explicit_parent_means, real_to_alm,
                               ring_reduce, fit_operator, nuisance_projected_response)


def test_real_sine_and_cosine_synthesis():
    c=np.random.default_rng(92018).normal(size=49)
    rr=np.arange(hp.nside2npix(8))
    direct=design(np.column_stack(hp.pix2vec(8,rr)),6)@c
    actual=hp.alm2map(real_to_alm(c),8,lmax=6,pol=False,pixwin=False,fwhm=0.)
    assert np.max(np.abs(actual-direct)) < 1e-12


def test_ring_reduction_matches_explicit_partial_children_and_constant():
    ni,no=8,2
    valid=np.ones(hp.nside2npix(ni),bool)
    valid[[0,1,19,61,74]]=False
    selected=np.ones(hp.nside2npix(no),bool)
    v=np.sin(np.arange(len(valid))*.37)
    actual,count=ring_reduce(v,valid,selected,ni,no,chunk=37)
    expected=explicit_parent_means(v,valid,np.arange(len(selected)),ni,no)
    assert np.max(np.abs(hp.reorder(actual,r2n=True)-expected)) < 1e-14
    assert np.array_equal(hp.reorder(count,r2n=True),valid.reshape(-1,16).sum(axis=1))
    ones,_=ring_reduce(np.ones_like(v)*3.25,valid,selected,ni,no,chunk=37)
    assert np.array_equal(ones,np.ones_like(ones)*3.25)


def test_joint_fwl_and_constant_monopole():
    n=np.column_stack(hp.pix2vec(8,np.arange(hp.nside2npix(8))))
    y=design(n,5)
    selected=(n[:,2] > -.65)&(n[:,0] < .8)
    op=fit_operator(y,selected)[4:]
    g=design(n[selected],6)@np.random.default_rng(72).normal(size=(49,3))
    fwl,_=nuisance_projected_response(y,selected,g)
    assert np.max(np.abs(op@g-fwl)) < 1e-11
    assert np.max(np.abs(op@np.ones(selected.sum()))) < 1e-12


def test_reject_invalid_fixed_geometry():
    with pytest.raises(ValueError,match='FIXED_NATIVE_GEOMETRY'):
        ring_reduce(np.ones(12),np.ones(12,bool),np.ones(48,bool),1,2)
