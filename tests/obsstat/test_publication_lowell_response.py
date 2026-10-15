"""Analytic construction checks for finite masked harmonic response."""
import numpy as np
import pytest
from obsstat.publication_lowell_response import (
    LowellResponseError,source_fit_matrix,leakage_matrix,source_map_fit,band_rms,
)


def _design(seed=123):
    rng=np.random.default_rng(seed)
    q,_=np.linalg.qr(rng.normal(size=(180,36)))
    high=rng.normal(size=(180,18))
    mask=np.ones(180,bool)
    mask[:33]=False
    return q,high,mask


def test_mask_operator_exact_on_declared_low_subspace():
    low,hi,m=_design()
    R,info=source_fit_matrix(low,m)
    np.testing.assert_allclose(R@low[m],np.eye(36),atol=2e-14)
    assert info["columns"]==36 and info["sampled_pixels"]==147


def test_highmode_injection_equals_leakage_operator_exactly():
    lo,hi,m=_design()
    R,_=source_fit_matrix(lo,m)
    L,info=leakage_matrix(lo,hi,m)
    v=np.arange(36)/100.
    h=np.linspace(-.3,.3,18)
    mixed=lo@v+hi@h
    actual=R@mixed[m]
    np.testing.assert_allclose(actual[4:16]-v[4:16],L@h,atol=3e-14)
    assert info["spectral_norm"]>0


def test_extra_high_modes_cannot_decrease_operator_norm():
    lo,hi,m=_design()
    L1,_=leakage_matrix(lo,hi[:,:8],m)
    L2,_=leakage_matrix(lo,hi[:,:18],m)
    assert np.linalg.norm(L2,2)>=np.linalg.norm(L1,2)-1e-12


def test_source_full_batched_fit_and_band_rms():
    lo,hi,m=_design()
    a=np.arange(36)*.005
    x=lo@a
    co,info=source_map_fit(np.stack([x,2*x]),lo,m)
    np.testing.assert_allclose(co[0],a,atol=2e-14)
    np.testing.assert_allclose(co[1],2*a,atol=4e-14)
    assert band_rms(co,ell=2)[0]==pytest.approx(np.linalg.norm(a[4:9])/np.sqrt(5))
    assert max(info["residual_rms_microK"])<1e-13


def test_numerical_domain_and_undercoverage_errors():
    lo,hi,m=_design()
    with pytest.raises(LowellResponseError,match="pixels"):
        source_fit_matrix(lo,np.zeros(len(m),bool))
    with pytest.raises(LowellResponseError,match="map"):
        source_map_fit(np.ones(len(m)+2),lo,m)
    with pytest.raises(LowellResponseError):
        band_rms(np.zeros(8),ell=3)
