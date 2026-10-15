"""FFP10 native RING vs observed NESTED: source identity and injection tests."""
import numpy as np
import healpy as hp
import pytest
from astropy.io import fits

from obsstat.planck_ffp10_polarized_lowell import (
    PlanckFFPPolarError,build_parent_lookup,coarse_selected_mean_rings,
    load_ffp10_pol_projected,split_source_contrasts,
    projected_covariance_and_rank
)
from obsstat.planck_spin2_source_response import (
    real_spin2_design,fit_spin2_operator
)


def _synthetic_source(nside_in=32,nside_out=8,seed=11):
    rng=np.random.default_rng(seed)
    n=hp.nside2npix(nside_in)
    chosen=np.ones(hp.nside2npix(nside_out),bool)
    chosen[np.arange(len(chosen))%7==0]=False
    fine=rng.random(n)>.13
    # Guarantee all selected parents have at least 1 valid pixel.
    k=(nside_in//nside_out)**2
    fine[::k]=True
    return build_parent_lookup(nside_in,nside_out,chosen,fine),fine


def test_native_ring_parent_average_matches_healpy_udgrade_no_mask():
    look,fine=_synthetic_source()
    rng=np.random.default_rng(7)
    raw=rng.normal(size=hp.nside2npix(look.nside_in)).astype('f4')
    ours=coarse_selected_mean_rings(raw,look,use_source_mask=False)
    # Our reducer deliberately accumulates in float64; hp.ud_grade preserves
    # float32 dtype when given float32, so it has a separate <1e-7 rounding
    # envelope. The exact double-precision NESTED parent mean is the oracle.
    nested=hp.reorder(raw,r2n=True).astype(float)
    parent=nested.reshape(-1,look.nested_children).mean(axis=1)
    exact=hp.reorder(parent,n2r=True)[look.selected_ring]
    np.testing.assert_allclose(ours,exact,atol=1e-14,rtol=0)
    approximate=hp.ud_grade(raw,nside_out=look.nside_out)[look.selected_ring]
    assert np.max(np.abs(ours-approximate))<1e-7


def test_source_masked_ring_parent_average_matches_explicit_nested_reference():
    look,fine=_synthetic_source()
    rng=np.random.default_rng(2)
    raw=rng.normal(size=hp.nside2npix(look.nside_in)).astype('f4')
    native_nested=hp.reorder(raw,r2n=True)
    k=look.nested_children
    val=native_nested.reshape(-1,k)
    mask=fine.reshape(-1,k)
    top=np.sum(np.where(mask,val,0),axis=1,dtype=float)
    count=mask.sum(axis=1)
    ref=hp.reorder(np.divide(top,count,out=np.full(len(count),np.nan),where=count>0),n2r=True)
    got=coarse_selected_mean_rings(raw,look)
    np.testing.assert_allclose(got,ref[look.selected_ring],atol=2e-15)


def test_selected_map_simulation_fits_same_orthonormal_spin_chart(tmp_path):
    look,fine=_synthetic_source(seed=8)
    nside=look.nside_out
    X,meta=real_spin2_design(nside=nside,lmax=3)
    rng=np.random.default_rng(37)
    a=rng.normal(size=X.shape[1])*.15
    sky=X@a
    npix=hp.nside2npix(nside)
    Q=sky[:npix]
    U=sky[npix:]
    n=hp.nside2npix(look.nside_in)
    ring_fine=np.arange(n)
    ring_parent=hp.nest2ring(nside,
        hp.ring2nest(look.nside_in,ring_fine)//look.nested_children)
    native_Q=(Q[ring_parent]/1e6).astype('f4')
    native_U=(U[ring_parent]/1e6).astype('f4')
    file=tmp_path/"synthetic_test_only.fits"
    fits.BinTableHDU.from_columns([
        fits.Column(name="INTENSITY",format="E",array=np.zeros(n,dtype='f4')),
        fits.Column(name="Q-POLARISATION",format="E",array=native_Q),
        fits.Column(name="U-POLARISATION",format="E",array=native_U),
    ]).writeto(file)
    op,info=fit_spin2_operator(X,
         np.isin(np.arange(npix),look.selected_ring))
    plus=load_ffp10_pol_projected(file,look,op,check_header=False,u_sign=1)
    minus=load_ffp10_pol_projected(file,look,op,check_header=False,u_sign=-1)
    np.testing.assert_allclose(plus["coefficients_microK"],a,atol=4e-8)
    assert np.linalg.norm(minus["coefficients_microK"]-a)>0.01
    assert plus["u_sign_chart"]==1 and minus["u_sign_chart"]==-1


def test_separate_halfmission_oddeven_contrasts_have_no_fake_noise_covariance():
    rows=np.array([[1.,2.],[-1.,0.],[2.,3.],[-2.,-1.]])
    names=("SMICA_HM1","SMICA_HM2","SMICA_OE1","SMICA_OE2")
    vals=split_source_contrasts(rows,names)
    np.testing.assert_allclose(vals["HM_half_difference"],[1.,1.])
    np.testing.assert_allclose(vals["OE_half_difference"],[2.,2.])
    assert len(vals)==5


def test_empirical_noise_covariance_rank_bound_and_mixed_frame_rejection():
    X=np.arange(21.).reshape(7,3)
    cov=projected_covariance_and_rank(X)
    assert cov["max_empirical_rank"]==3
    assert cov["empirical_rank"]==1
    assert cov["one_sky_variants_are_not_MC_samples"]
    assert cov["number_distinct_input_rows"]==7
    assert cov["statistical_independence"].startswith("MUST_BE_CERTIFIED")
    look,fine=_synthetic_source()
    with pytest.raises(PlanckFFPPolarError):
        coarse_selected_mean_rings(np.ones(20),look)
    with pytest.raises(PlanckFFPPolarError):
        build_parent_lookup(32,8,np.ones(13,bool),fine)
    with pytest.raises(PlanckFFPPolarError):
        split_source_contrasts(np.ones((4,5)),("SMICA_HM1","SMICA_HM2","SMICA_OE1","SMICA_OE1"))


def test_split_covariance_wolfram_scalar_and_correlated_case():
    from obsstat.planck_ffp10_polarized_lowell import split_covariance_transport
    from numpy.testing import assert_allclose
    A=np.array([[1.]])
    B=np.array([[1.]])
    C=np.array([[.4]])
    result=split_covariance_transport(A,B,C)
    assert_allclose(result["half_difference_covariance"],[[.3]],atol=1e-15)
    assert_allclose(result["coadd_noise_covariance"],[[.7]],atol=1e-15)
    assert_allclose(result["coadd_minus_halfdiff_covariance"],[[.4]],atol=1e-15)
    uncorrelated=split_covariance_transport(A,B,np.array([[0.]]))
    assert_allclose(uncorrelated["half_difference_covariance"],
                    uncorrelated["coadd_noise_covariance"])
    with pytest.raises(PlanckFFPPolarError):
        split_covariance_transport(A,B,np.array([[2.]]))


def test_two_split_covariance_matrix_and_indefinite_response_refused():
    from obsstat.planck_ffp10_polarized_lowell import split_covariance_transport
    A=np.diag([1.,2.])
    B=np.diag([2.,1.])
    D=np.array([[.1,.3],[-.1,.2]])
    q=split_covariance_transport(A,B,D)
    assert np.linalg.eigvalsh(q["coadd_noise_covariance"]).min()>0
    assert np.linalg.eigvalsh(q["half_difference_covariance"]).min()>0
    np.testing.assert_allclose(q["coadd_minus_halfdiff_covariance"],(D+D.T)/2)
