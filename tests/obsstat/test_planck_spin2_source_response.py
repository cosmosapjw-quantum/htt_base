"""Spin-2 E/B masked source response and physical Q/U harmonic basis tests."""
import numpy as np
import pytest

from obsstat.planck_spin2_source_response import (
    Spin2ResponseError,real_spin2_design,fit_spin2_operator,
    finite_spin2_leakage,source_EB_band_powers
)


@pytest.fixture(scope="module")
def sample():
    import healpy as hp
    nside=8
    X,meta=real_spin2_design(nside=nside,lmax=4)
    n=hp.nside2npix(nside)
    keep=np.ones(n,bool)
    keep[np.arange(n)%7==0]=False
    return X[:,:24], X[:,24:],meta[:24],meta[24:],keep


def test_physical_spin2_band_cardinality_and_ordering(sample):
    low,high,lo,hi,mask=sample
    assert low.shape[1]==24 and high.shape[1]==18
    assert [m["spin"] for m in lo[:5]]==["E"]*5
    assert [m["spin"] for m in lo[5:10]]==["B"]*5
    assert [m["ell"] for m in lo[:10]]==[2]*10
    assert mask.dtype==bool


def test_masked_spin2_low_mode_injection_recovered(sample):
    low,high,lo,hi,mask=sample
    op,meta=fit_spin2_operator(low,mask)
    A=low[np.r_[mask,mask]]
    assert meta["rank"]==24
    np.testing.assert_allclose(op@A,np.eye(24),atol=2e-13)


def test_unmodelled_higher_spin_E_and_B_alias_to_retained_modes(sample):
    low,high,lo,hi,mask=sample
    op,_=fit_spin2_operator(low,mask)
    cross,info=finite_spin2_leakage(low,high,lo,hi,mask)
    rng=np.random.default_rng(43)
    a=rng.normal(size=24)
    b=rng.normal(size=18)
    y=(low@a+high@b)[np.r_[mask,mask]]
    np.testing.assert_allclose(op@y-a,cross@b,atol=2e-12)
    assert info["all_high_to_low_spectral_norm"]>0
    assert info["B_from_E_spectral_norm"]>=0


def test_fullsky_low_high_mode_orthogonality_approximation(sample):
    low,high,lo,hi,mask=sample
    full=np.ones(len(mask),bool)
    _,m=finite_spin2_leakage(low,high,lo,hi,full)
    assert m["all_high_to_low_spectral_norm"] < .01


def test_source_band_stats_reproduce_EB_sum(sample):
    low,high,lo,hi,mask=sample
    rng=np.random.default_rng(12)
    c=rng.normal(size=(3,len(lo)))
    p=source_EB_band_powers(c,lo)
    assert set(p)=={"2","3"}
    for row in range(3):
        s2=5*(p["2"]["E"][row]+p["2"]["B"][row])
        s3=7*(p["3"]["E"][row]+p["3"]["B"][row])
        assert s2+s3==pytest.approx(c[row]@c[row],rel=1e-14)


def test_reject_malformed_spin2_mask_and_nside(sample):
    low,high,lo,hi,mask=sample
    with pytest.raises(Spin2ResponseError):
        fit_spin2_operator(low,np.ones(17,bool))
    with pytest.raises(Spin2ResponseError):
        real_spin2_design(nside=3,lmax=5)
    with pytest.raises(Spin2ResponseError):
        source_EB_band_powers(np.ones((5,23)),lo)
