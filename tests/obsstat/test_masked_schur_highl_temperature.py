"""Independent exact masked normal-block, nuisance profile and beam contracts."""
import numpy as np
import pytest

from obsstat.masked_schur_highl_temperature import (
    MaskSchurError,make_geometry,fit_source_batches,nominal_beam_window,
)


def design(seed=40,n=600,p=169):
    rng=np.random.default_rng(seed)
    A=rng.normal(size=(n,p))
    m=np.ones(n,bool);m[np.arange(n)%5==0]=False
    return A,m


def test_source_injected_low_and_high_reconstruct_identity():
    X,m=design()
    G=make_geometry(X,m)
    rng=np.random.default_rng(7)
    a=rng.normal(size=(5,36))
    b=rng.normal(size=(5,133))
    y=np.concatenate((a,b),axis=1)@X.T
    z=fit_source_batches(y,G,chunk=2)
    np.testing.assert_allclose(z["joint"][:,:36],a,atol=2e-13,rtol=1e-13)
    np.testing.assert_allclose(z["joint"][:,36:],b,atol=2e-13,rtol=1e-13)
    np.testing.assert_allclose(z["restricted"]-a,b@G.K.T,atol=2e-13,rtol=1e-13)
    assert z["max_relative_schur_identity"]<1e-12
    assert G.diagnostics["selected_pixels"]==480


def test_profile_information_reduction_relative_metric_leq_one():
    X,m=design()
    G=make_geometry(X,m)
    assert 0 < G.diagnostics["profile_information_min"]<=1
    assert G.diagnostics["profile_information_max"]<=1+1e-10
    assert G.diagnostics["profile_information_min"]<1
    assert G.diagnostics["high_columns"]==133
    np.testing.assert_allclose(G.K,
        np.linalg.solve(G.x[:,:36].T@G.x[:,:36],G.x[:,:36].T@G.x[:,36:]),
        atol=2e-13)


def test_source_noise_response_identity_no_source_signal_prior():
    X,m=design()
    G=make_geometry(X,m)
    rng=np.random.default_rng(300)
    sig=rng.normal(size=(7,len(X)))
    noi=rng.normal(size=(7,len(X)))
    s=fit_source_batches(sig,G)
    n=fit_source_batches(noi,G)
    p=fit_source_batches(sig+noi,G)
    np.testing.assert_allclose(p["restricted"],s["restricted"]+n["restricted"],atol=3e-13)
    np.testing.assert_allclose(p["joint"],s["joint"]+n["joint"],atol=3e-13)


def test_nominal_transfer_is_not_claimed_as_actual_instrument_deconvolution():
    X,m=design()
    G=make_geometry(X,m)
    b=nominal_beam_window(G)
    assert b["scope"]=="DECLARED_NOMINAL_NOT_ACTUAL_RELEASE_TRANSFER"
    assert b["gaussian_beam_window"]["12"]<b["gaussian_beam_window"]["2"]
    assert b["native_pixel_window"]["12"]>b["analysis_pixel_window"]["12"]
    assert abs(b["relative_norm_change"])<.005
    assert b["nominal_intrinsic_high_to_low_ell2to3_spectral_norm"]>0


def test_reject_insufficient_or_bad_source_design():
    X,m=design()
    with pytest.raises(MaskSchurError):
        make_geometry(X,np.zeros(len(m),bool))
    with pytest.raises(MaskSchurError):
        make_geometry(X,np.ones(19,bool))
    with pytest.raises(MaskSchurError):
        fit_source_batches(np.full((2,len(X)),np.nan),make_geometry(X,m))
    with pytest.raises(MaskSchurError):
        nominal_beam_window(make_geometry(X,m),fwhm_arcmin=-2)



def test_nested_lmax_block_fit_matches_independent_masked_likelihood_OLS():
    from obsstat.masked_schur_highl_temperature import nested_lmax_source_coefficients
    X,m=design(seed=150)
    geo=make_geometry(X,m)
    rng=np.random.default_rng(12)
    A=rng.normal(size=(8,169))
    maps=A@X.T
    ans=nested_lmax_source_coefficients(maps,geo,chunk=3)
    assert ans["rows"]==8
    assert ans["Schur_identity_relative_max"]<2e-12
    for ell in (5,8,10,12):
        p=(ell+1)**2
        chart=X[m,:p]
        oracle=(np.linalg.lstsq(chart,maps[:,m].T,rcond=None)[0]).T[:,:36]
        np.testing.assert_allclose(ans["lowl_by_lmax"][str(ell)],oracle,atol=2e-13)
    np.testing.assert_allclose(ans["lowl_by_lmax"]["12"],A[:,:36],atol=2e-13)


def test_nested_rejects_unlocked_lmax_methods():
    from obsstat.masked_schur_highl_temperature import nested_lmax_source_coefficients
    X,m=design()
    geo=make_geometry(X,m)
    with pytest.raises(MaskSchurError):
        nested_lmax_source_coefficients(np.ones((3,len(X))),geo,lmax_set=(5,12))
