"""Bounded source and mathematical regression tests, not physical Planck PTE."""
import sys
from pathlib import Path
import json
import numpy as np
import pytest
from scipy.special import sph_harm_y
from scipy.linalg import lstsq
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE/'src'))
from spin2_finite import spin_y,spin2_shell,block_design,response_from_design
from l01_source import load_inputs,parity_transform,summarize,spectrum_by_ell,polar_product_deltas,mask_tail_contract

@pytest.fixture(scope='module')
def input_source():return load_inputs(HERE/'source')

@pytest.fixture(scope='module')
def manufactured_sky():
 n=768;i=np.arange(n);z=1-2*(i+.5)/n;ph=(i*np.pi*(3-np.sqrt(5)))%(2*np.pi);theta=np.arccos(z)
 low=block_design(theta,ph,2,5);high=block_design(theta,ph,6,8)
 x=np.sin(theta)*np.cos(ph)
 ma=np.zeros(n,bool);mb=np.zeros(n,bool)
 ma[np.argsort(z)[-700:]]=True;mb[np.argsort(x)[-700:]]=True
 return theta,ph,low,high,ma,mb

def test_spin_zero_matches_scipy_condon_shortley():
 th=np.linspace(.15,2.87,19);ph=np.linspace(-2.3,3.,19)
 for ell in range(5):
  for m in range(-ell,ell+1):
   np.testing.assert_allclose(spin_y(ell,m,0,th,ph),sph_harm_y(ell,m,th,ph),atol=3e-14,rtol=0)

def test_spin2_parity_stokes_map_at_antipodes():
 rng=np.random.default_rng(441);theta=rng.uniform(.2,np.pi-.2,34);phi=rng.uniform(-np.pi,np.pi,34)
 for ell in range(2,6):
  a=spin2_shell(theta,phi,ell);b=spin2_shell(np.pi-theta,phi+np.pi,ell)
  n=len(theta);q=2*ell+1
  for block,tag in [(slice(0,q),0),(slice(q,2*q),1)]:
   sign=(-1)**(ell+tag)
   np.testing.assert_allclose(b[:n,block],sign*a[:n,block],atol=2e-14)
   np.testing.assert_allclose(b[n:,block],-sign*a[n:,block],atol=2e-14)

def test_full_and_masked_joint_eb_finite_response(manufactured_sky):
 _,_,low,high,ma,mb=manufactured_sky
 k_full,full=response_from_design(low,high,np.ones(len(ma),bool));k_mask,mask=response_from_design(low,high,ma)
 assert low.shape==(1536,64) and high.shape==(1536,90)
 assert full['low_condition']<1.02 and mask['low_condition']<10
 assert full['low_identity_residual']<1e-12 and mask['low_identity_residual']<1e-12
 assert np.linalg.norm(k_mask,2)>100*np.linalg.norm(k_full,2)
 rng=np.random.default_rng(48);h=rng.normal(size=90)
 rows=np.r_[ma,ma];L=low[rows];H=high[rows]
 got=np.linalg.lstsq(L,H@h,rcond=None)[0]
 np.testing.assert_allclose(got,k_mask@h,atol=2e-12)

def test_mask_pixel_count_does_not_fix_eb_response(manufactured_sky):
 _,_,low,high,ma,mb=manufactured_sky
 assert ma.sum()==mb.sum()==700
 a,_=response_from_design(low,high,ma);b,_=response_from_design(low,high,mb)
 assert np.linalg.norm(a-b)>0.5

def test_synthetic_EB_mixing_is_not_zero_under_mask(manufactured_sky):
 _,_,low,high,ma,mb=manufactured_sky
 k,_=response_from_design(low,high,ma)
 elow=[];blow=[];ehigh=[];bhigh=[];off=0
 for ell in range(2,6):
  t=2*ell+1;elow+=list(range(off,off+t));blow+=list(range(off+t,off+2*t));off+=2*t
 off=0
 for ell in range(6,9):
  t=2*ell+1;ehigh+=list(range(off,off+t));bhigh+=list(range(off+t,off+2*t));off+=2*t
 assert np.linalg.norm(k[np.ix_(blow,ehigh)],2)>1e-2
 assert np.linalg.norm(k[np.ix_(elow,bhigh)],2)>1e-2

def test_actual_source_sha_and_schema(input_source):
 x=input_source
 assert len(x['names_t'])==9 and len(x['names_eb'])==8
 assert x['EB'].shape==(8,64) and x['T'].shape==(9,32)
 assert all(x['names_t'][k] !='SMICA_noSZ_FULL' for k in range(0,4))
 assert 'SMICA_noSZ_FULL' not in x['names_eb']

def test_actual_eb_split_norms_match_upstream(input_source):
 x=input_source;d=polar_product_deltas(x)
 assert np.isclose(d['SMICA_HM_half']['norm_64_microK'],.4312803816570206,atol=2e-13)
 assert np.isclose(d['SMICA_OE_half']['norm_64_microK'],.3458641865397831,atol=2e-13)
 assert np.isclose(d['SMICA_HM_OE_mean']['norm_64_microK'],.14584836061591308,atol=2e-13)
 assert np.isclose(d['NILC_HM_minus_SMICA_HM']['norm_64_microK'],.7373481945029908,atol=2e-13)
 assert np.isclose(d['SMICA_FULL_minus_HMmean']['norm_64_microK'],.5907753987428048,atol=2e-13)

def test_source_eb_cauchy_and_parity(input_source):
 x=input_source;idx=x['names_eb'].index('SMICA_FULL');row=x['EB'][idx];meta=x['meta']
 a=spectrum_by_ell(row,meta)
 for z in a:
  assert z['ee']>=0 and z['bb']>=0 and abs(z['eb'])<=np.sqrt(z['ee']*z['bb'])*(1+1e-12)
 flip=parity_transform(row,meta);b=spectrum_by_ell(flip,meta)
 for xx,yy in zip(a,b):
  np.testing.assert_allclose([xx['ee'],xx['bb'],xx['eb']],[yy['ee'],yy['bb'],-yy['eb']],atol=1e-14)

def test_mask_bound_temp_real_K16_K32(input_source):
 x=input_source;z=mask_tail_contract(x)
 assert np.isclose(z['ell6_16'],2.255720291177002,atol=2e-12)
 assert np.isclose(z['ell17_32'],.9208432350171425,atol=2e-12)
 assert np.isclose(z['combined'],2.4328695605629207,atol=2e-12)
 assert z['spin2_ell_gt5_EB']=='UNKNOWN_NOT_ZERO'

def test_synthetic_source_same_sky_contrast_rank(input_source):
 s=summarize(input_source)
 assert s['same_sky_rowspace']['n_distinct_physical_sky_realizations']==1
 assert s['same_sky_rowspace']['source_processing_contrast_rank']<=7
 assert s['source_products']['common_temp_selected'] !=s['source_products']['common_pol_selected']
 assert s['ffp']['number_latent_sky_rows']==300
 assert s['physical_gates']['full_Planck_spin2_higher_ell_response']=='NOT_MEASURED'

def test_invalid_source_or_payload_fails_closed(input_source,tmp_path):
 assert input_source['EB'].shape==(8,64)
 with pytest.raises((ValueError,FileNotFoundError)):load_inputs(tmp_path)
 with pytest.raises(ValueError):spectrum_by_ell(np.zeros(63),input_source['meta'])
 with pytest.raises(ValueError):parity_transform(np.zeros(63),input_source['meta'])
 with pytest.raises(ValueError):spin2_shell(np.array([0.1]),np.array([0.2]),1)
