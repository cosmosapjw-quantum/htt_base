"""Independent finite-dimensional split/half difference covariance identities."""
import numpy as np
import pytest
from obsstat.planck_split_joint_law import (
    PlanckSplitLawError,split_covariance,conditional_split_covariance,
    nested_coarse_masked_mean,half_sum_difference)


def test_exact_gaussian_split_covariance_block_oracle():
    rng=np.random.default_rng(7)
    a=rng.normal(size=(4,4));b=rng.normal(size=(4,4))
    latent=rng.normal(size=(8,8))
    c=latent@latent.T + np.eye(8)
    c11,c12,c22=c[:4,:4],c[:4,4:],c[4:,4:]
    cm,cd,cross=split_covariance(c11,c22,c12)
    transform=np.block([[np.eye(4),np.eye(4)],
                        [np.eye(4),-np.eye(4)]])/2
    target=transform@c@transform.T
    np.testing.assert_allclose(cm,target[:4,:4],atol=1e-11)
    np.testing.assert_allclose(cd,target[4:,4:],atol=1e-11)
    np.testing.assert_allclose(cross,target[:4,4:],atol=1e-11)
    np.testing.assert_allclose(
        conditional_split_covariance(c11,c22,c12),
        cm-cross@np.linalg.solve(cd,cross.T),atol=1e-12)


def test_independent_equal_noise_halfdifference_and_shared_systematic_blindness():
    cn=np.diag([1.,2.,3.])
    cc=np.diag([4.,5.,6.])
    cm,cd,cross=split_covariance(cn+cc,cn+cc,cc)
    np.testing.assert_allclose(cm,cn/2+cc)
    np.testing.assert_allclose(cd,cn/2)
    np.testing.assert_allclose(cross,0)
    _,cd0,_=split_covariance(cn,cn,np.zeros_like(cn))
    np.testing.assert_allclose(cd0,cd)


def test_nested_mask_average_matches_healpy_allvalid():
    hp=pytest.importorskip('healpy')
    rng=np.random.default_rng(12)
    sky=rng.normal(size=hp.nside2npix(16)).astype(np.float64)
    count=np.ones_like(sky,dtype=bool)
    mean,fraction=nested_coarse_masked_mean(sky,count,nside_in=16,nside_out=4,chunk_lowpix=15)
    target=hp.ud_grade(sky,4,order_in='NESTED',order_out='RING',power=0)
    np.testing.assert_allclose(mean,target,atol=1e-12)
    np.testing.assert_allclose(fraction,1)


def test_missing_pixels_excluded_and_coverage_reported():
    hp=pytest.importorskip('healpy')
    sky=np.arange(hp.nside2npix(8),dtype=float)
    mask=np.ones(len(sky),bool)
    mask[0]=False
    mean,fraction=nested_coarse_masked_mean(sky,mask,nside_in=8,nside_out=2,chunk_lowpix=9)
    back=hp.reorder(fraction,r2n=True)
    assert np.min(back)==pytest.approx(15/16)
    assert np.max(back)==1
    coarse_nested=(np.arange(len(sky))[1:16]).mean()
    m=hp.reorder(mean,r2n=True)
    assert m[0]==pytest.approx(coarse_nested)


def test_sumdiff_identity_preserves_same_sky_vectors():
    rng=np.random.default_rng(34)
    a=rng.normal(size=(3,32));b=rng.normal(size=(3,32))
    m,d=half_sum_difference(a,b)
    np.testing.assert_allclose(m+d,a)
    np.testing.assert_allclose(m-d,b)
    with pytest.raises(PlanckSplitLawError):
        split_covariance(np.eye(3),-np.eye(3),np.zeros((3,3)))
