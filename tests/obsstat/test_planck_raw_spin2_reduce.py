"""A small independent HEALPix masked NESTED->RING source reduction oracle."""
import healpy as hp
import numpy as np
import pytest

from run_htt_planck_raw_spin2_fit_l01 import raw_nested_masked_mean


def test_nested_masked_scalar_source_exact_reference_and_index_frame():
    nsidein,nsideout=8,2
    n=hp.nside2npix(nsidein);children=(nsidein//nsideout)**2
    rng=np.random.default_rng(1)
    y=rng.normal(size=n)
    valid=rng.random(n)>.3
    # Include native invalid sentinel in an otherwise valid pixel.
    y[10]=-1e30;valid[10]=True
    measured,coverage=raw_nested_masked_mean(
        y,valid,nside_in=nsidein,nside_out=nsideout,chunk=3)
    ref=np.full(hp.nside2npix(nsideout),np.nan)
    cov=np.zeros(len(ref))
    for i in range(len(ref)):
        sub=slice(i*children,(i+1)*children)
        pick=valid[sub] & np.isfinite(y[sub]) & (y[sub]>-1e20)
        cnt=int(pick.sum());cov[i]=cnt/children
        if cnt:ref[i]=np.mean(y[sub][pick])
    np.testing.assert_allclose(measured,hp.reorder(ref,n2r=True),rtol=3e-15,atol=1e-15)
    np.testing.assert_array_equal(coverage,hp.reorder(cov,n2r=True))


def test_coverage_sentinels_do_not_fill_galactic_holes():
    nsidein,nsideout=8,2
    n=hp.nside2npix(nsidein);k=(nsidein//nsideout)**2
    m=np.ones(n,bool)
    m[2*k:3*k]=False
    data=np.ones(n)
    y,c=raw_nested_masked_mean(data,m,nside_in=nsidein,nside_out=nsideout,chunk=1)
    idx=hp.nest2ring(nsideout,2)
    assert c[idx]==0
    assert np.isnan(y[idx])
    assert np.sum(c==0)==1


def test_invalid_native_shape_or_resolution_fails():
    with pytest.raises(ValueError):
        raw_nested_masked_mean(np.ones(20),np.ones(20,bool),nside_in=8,nside_out=2)
    with pytest.raises(ValueError):
        raw_nested_masked_mean(np.ones(hp.nside2npix(8)),
           np.ones(hp.nside2npix(8),bool),nside_in=2,nside_out=8)
