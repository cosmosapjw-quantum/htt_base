"""Exact same-sky contrast/spin-2 projection and observational-image algebra."""
import numpy as np
import pytest
from obsstat.htt_multisplit_lowell import (
    multisplit_contrasts, split_power_identity, spin2_design_real,
    fit_spin2_coefficients, finite_real_input, SourceMultiSplitError,
)


def test_fourway_common_sky_cancels_exactly():
    rng=np.random.default_rng(110)
    x=rng.normal(size=(4,32))
    a=multisplit_contrasts(x)
    shift=rng.normal(size=32)
    b=multisplit_contrasts(x+shift[None,:])
    np.testing.assert_allclose(a['hm_difference'],b['hm_difference'],atol=1e-14)
    np.testing.assert_allclose(a['oe_difference'],b['oe_difference'],atol=1e-14)
    np.testing.assert_allclose(a['partition_mean_difference'],b['partition_mean_difference'],atol=1e-14)
    np.testing.assert_allclose(a['fourway_mean']+shift,b['fourway_mean'],atol=1e-14)
    recovered=np.stack([
        a['fourway_mean']+a['partition_mean_difference']/2+a['hm_difference'],
        a['fourway_mean']+a['partition_mean_difference']/2-a['hm_difference'],
        a['fourway_mean']-a['partition_mean_difference']/2+a['oe_difference'],
        a['fourway_mean']-a['partition_mean_difference']/2-a['oe_difference']])
    np.testing.assert_allclose(recovered,x,atol=1e-14)


def test_cross_power_identity_is_exact():
    rng=np.random.default_rng(19)
    x=rng.normal(size=5)
    y=rng.normal(size=5)
    z=split_power_identity(x,y)
    assert z['cross'] == pytest.approx(z['mean_auto']-z['difference_auto'],abs=1e-14)


def test_spin2_real_design_basis_reconstructs_coefficients():
    import healpy as hp
    nside=8
    mask=np.ones(hp.nside2npix(nside),bool)
    mask[:150]=False
    X,cols=spin2_design_real(nside=nside,lmax=4)
    assert X.shape==(2*hp.nside2npix(nside),2*((5**2)-(2**2)))
    rng=np.random.default_rng(184)
    truth=rng.normal(size=X.shape[1])
    values=X@truth
    fitted=fit_spin2_coefficients(values.reshape(2,-1),mask,X)
    np.testing.assert_allclose(fitted['coefficients'],truth,rtol=0,atol=1e-10)
    assert fitted['rank']==len(truth)
    assert fitted['design_identity_residual']<1e-9
    with pytest.raises(SourceMultiSplitError):
        fit_spin2_coefficients(values.reshape(2,-1).astype(complex),mask,X)


def test_no_silent_complex_source_fields():
    with pytest.raises(SourceMultiSplitError):
        finite_real_input(np.ones((3,32),complex),name='sky',shape=(3,32))
