import numpy as np
import pytest
from obsstat.r7_cmb_product_response import (build_product_response,build_tensor_record,real_design,
    stored_to_real, pixel_fit_geometry)

PRODUCT=dict(product_id="thermal-fixture",release="1",frame="OUTWARD",units="K",correction="NONE",
    channel_convention="BLACKBODY_WEIGHT_ONE",beam="IDENTITY")

def source(coefficients):
    return dict(source_id="fixture",units="K",temperature=lambda n:real_design(n)@coefficients)

def test_simultaneous_fit_beta_zero_and_finite_monopole_quadrupole():
    coefficients=np.zeros(36);coefficients[0]=2.7*np.sqrt(4*np.pi);coefficients[4:]=np.arange(32)*1e-7
    r=build_product_response(PRODUCT,source(coefficients),[0,0,0],{})
    np.testing.assert_allclose(r.full_coefficients,coefficients,atol=2e-14)
    assert r.response_kind=="THERMAL_RESPONSE" and r.fit_rank==36
    coefficients[4:]=0;beta=.001
    r=build_product_response(PRODUCT,source(coefficients),[0,0,beta],{})
    expected=2.7*beta**2*(2/3)*np.sqrt(4*np.pi/5)
    assert abs(r.retained[0]/expected-1)<2e-6
    assert r.full_coefficients[1]>0
    assert abs(r.full_coefficients[1]/(2.7*beta*np.sqrt(4*np.pi/3))-1)<2e-6


def test_layout_and_full_cross_covariance():
    row=np.zeros(32);row[1:3]=[2.,3.]
    meta=dict(sample_id="a",units="microK",harmonic_layout="STORED_RE_IM",frame="GALACTIC",
        product_id="p",release="r",processing_id="fit",mask_id="m")
    c=np.eye(32);c[1,13]=c[13,1]=.2
    provider=lambda m:dict(covariance=c,sample_id="a",units="microK",harmonic_layout="STORED_RE_IM",covariance_id="known")
    r=build_tensor_record(row,meta,provider)
    assert r.covariance.shape==(32,32) and r.covariance[1,13]!=0
    assert np.isclose(np.linalg.norm(r.Q)**2,(15/(8*np.pi))*26e-12)
    assert r.retained[2]<0


def test_absolute_temperature_and_product_processing_required():
    with pytest.raises(ValueError):
        build_product_response(PRODUCT,dict(source_id="bad",units="K",temperature=lambda n:-np.ones(len(n))),[0,0,0],{})
    with pytest.raises(ValueError,match="actual pixel"):
        build_product_response(dict(PRODUCT,beam="NAMED"),dict(source_id="s",units="K",temperature=lambda n:np.ones(len(n))),[0,0,0],{})
