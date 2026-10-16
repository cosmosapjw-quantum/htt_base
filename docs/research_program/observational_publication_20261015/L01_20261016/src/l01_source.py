"""Six-paper P2/L01: immutable real Planck T/EB source-image crosswalk.

Observed Planck products share ONE sky, and no true E/B physical likelihood,
beam transfer or exchangeable FFP10 end-to-end null is inferred.
"""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import numpy as np

EXPECTED={
'retained_common_support_coefficients.npz':'900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459',
'baseline_response_matrices.npz':'a9aaeb393deba03c97ecf45bf4e1ab74e98e3a8747de7c4bc7a96bff27014007',
'ell17_32_mask_response.npz':'91f496ca7cd1cbaed65153c64d83cf7abf84b21c141d8955d0cd8e07ed480a35',
'processing_coefficients.npz':'0c104e41b2cbd979bbb92b61a43744fb0e17376d26dd8a534cc90ab79ca23b08',
}
SOURCE_T=('SMICA_HM1','SMICA_HM2','SMICA_OE1','SMICA_OE2','NILC_HM1','NILC_HM2','SMICA_FULL','SMICA_noSZ_FULL','NILC_FULL')
SOURCE_EB=tuple(x for x in SOURCE_T if x!='SMICA_noSZ_FULL')


def sha256_file(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()


def load_inputs(source_dir:Path):
 source_dir=Path(source_dir)
 for k,v in EXPECTED.items():
  f=source_dir/k
  if not f.is_file() or sha256_file(f)!=v:
   raise ValueError(f'Source SHA-256 mismatch or absent: {k}')
 with np.load(source_dir/'retained_common_support_coefficients.npz',allow_pickle=False) as z:
  nT=tuple(z['names_T'].tolist());nP=tuple(z['names_EB'].tolist())
  aT=np.asarray(z['coeff_T'],float);aP=np.asarray(z['coeff_EB'],float)
  meta=json.loads(str(z['column_spin_metadata_json'].item()))
 if nT!=SOURCE_T or nP!=SOURCE_EB or aT.shape!=(9,32) or aP.shape!=(8,64) or len(meta)!=64 or not np.isfinite(aT).all() or not np.isfinite(aP).all():
  raise ValueError('Source T / EB product identity or shape mismatch')
 expected=[]
 for ell in range(2,6):
  for eb in ['E','B']:
   expected.append({'ell':ell,'m':0,'phase':'m0','E_or_B':eb})
   for m in range(1,ell+1):
    for phase in ['cos','sin']:expected.append({'ell':ell,'m':m,'phase':phase,'E_or_B':eb})
 if expected!=meta:raise ValueError('Source physical spin column convention mismatch')
 with np.load(source_dir/'baseline_response_matrices.npz',allow_pickle=False) as z:
  K16=np.asarray(z['K_ell2to5_32x253'],float);Tfull=np.asarray(z['SMICA_FULL_retained_32_microK'],float)
 with np.load(source_dir/'ell17_32_mask_response.npz',allow_pickle=False) as z:
  K32=np.asarray(z['K_ell2to5_32x800'],float)
 with np.load(source_dir/'processing_coefficients.npz',allow_pickle=False) as z:
  ffp_observed=np.asarray(z['observed'],float);ffp_pairs=np.asarray(z['paired'],float)
 if K16.shape!=(32,253) or K32.shape!=(32,800) or Tfull.shape!=(32,) or ffp_observed.shape!=(6,32) or ffp_pairs.shape!=(6,300,32):raise ValueError('Source T K shell and FFP layout mismatch')
 if np.max(abs(Tfull-aT[nT.index('SMICA_FULL')]))>5e-11:raise ValueError('SMICA full T source different sky or mask')
 return {'names_t':nT,'names_eb':nP,'T':aT,'EB':aP,'meta':meta,'K16':K16,'K32':K32,'ffp_observed':ffp_observed,'ffp_pairs':ffp_pairs}


def spectrum_by_ell(row,meta):
 row=np.asarray(row,float)
 if row.shape!=(64,) or not np.isfinite(row).all():raise ValueError('64 real E/B coefficients required')
 out=[]
 for ell in range(2,6):
  e=np.array([i for i,r in enumerate(meta) if r['ell']==ell and r['E_or_B']=='E'])
  b=np.array([i for i,r in enumerate(meta) if r['ell']==ell and r['E_or_B']=='B'])
  E=row[e];B=row[b]
  if len(e)!=2*ell+1 or len(b)!=len(e):raise ValueError('per ell metadata mismatch')
  ee=float(E@E/len(e));bb=float(B@B/len(e));eb=float(E@B/len(e));
  if eb*eb>ee*bb*(1+1e-12)+1e-25:raise ArithmeticError('Cauchy Schwarz broken')
  out.append(dict(ell=ell,ee=ee,bb=bb,eb=eb,cauchy_ratio=None if ee*bb==0 else float(eb*eb/(ee*bb))))
 return out


def polar_product_deltas(x):
 a={n:x['EB'][i] for i,n in enumerate(x['names_eb'])}
 def half(l,r):return (a[l]-a[r])/2
 def means(l,r):return (a[l]+a[r])/2
 sm_hm=means('SMICA_HM1','SMICA_HM2');sm_oe=means('SMICA_OE1','SMICA_OE2');nilc_hm=means('NILC_HM1','NILC_HM2')
 defs={
 'SMICA_HM_half':half('SMICA_HM1','SMICA_HM2'),
 'SMICA_OE_half':half('SMICA_OE1','SMICA_OE2'),
 'NILC_HM_half':half('NILC_HM1','NILC_HM2'),
 'SMICA_HM_OE_mean':sm_hm-sm_oe,
 'NILC_HM_minus_SMICA_HM':nilc_hm-sm_hm,
 'SMICA_FULL_minus_HMmean':a['SMICA_FULL']-sm_hm,
 'NILC_FULL_minus_SMICA_FULL':a['NILC_FULL']-a['SMICA_FULL'],
 }
 return {name:{'norm_64_microK':float(np.linalg.norm(v)),'E_norm_microK':float(np.linalg.norm(v[[i for i,j in enumerate(x['meta']) if j['E_or_B']=='E']])),
                'B_norm_microK':float(np.linalg.norm(v[[i for i,j in enumerate(x['meta']) if j['E_or_B']=='B']]))} for name,v in defs.items()}


def same_sky_rowspace(x):
 coeff=np.asarray(x['EB'],float)
 centered=coeff-coeff.mean(axis=0,keepdims=True)
 sing=np.linalg.svd(centered,compute_uv=False)
 return {'n_distinct_physical_sky_realizations':1,'n_polarization_processing_products':len(coeff),
         'source_processing_contrast_rank':int(np.linalg.matrix_rank(centered)),
         'nonzero_processing_singular_values_microK':sing[:-1].tolist(),
         'does_not_estimate_cosmic_covariance':True}


def parity_transform(row,meta):
 """Expected E even and B odd parity, retaining phase and m labels."""
 a=np.asarray(row,float)
 if a.shape!=(64,) or not np.isfinite(a).all():raise ValueError('physical 64 coeff row')
 signs=np.array([(-1.)**(j['ell']+(j['E_or_B']=='B')) for j in meta]);return a*signs


def mask_tail_contract(x):
 a=x['K16'];b=x['K32']
 vals={'ell6_16':float(np.linalg.norm(a,2)),'ell17_32':float(np.linalg.norm(b,2)),'combined':float(np.linalg.norm(np.concatenate((a,b),axis=1),2)),
       'ell6_16_frob_sq':float(np.sum(a*a)),'ell17_32_frob_sq':float(np.sum(b*b))}
 if not(vals['ell6_16']<=vals['combined']+1e-13 and vals['ell17_32']<=vals['combined']+1e-13 and vals['combined']<=np.hypot(vals['ell6_16'],vals['ell17_32'])+1e-12):raise AssertionError('horizontal PSD Gram upper/lower violated')
 vals['ell_gt32_T']='UNKNOWN_NOT_ZERO';vals['spin2_ell_gt5_EB']='UNKNOWN_NOT_ZERO'; vals['transfer']='MASK_GEOMETRY_ONLY_NOT_BEAM_FOREGROUND_E2E'
 return vals


def summarize(x):
 ebi={name:spectrum_by_ell(x['EB'][i],x['meta']) for i,name in enumerate(x['names_eb'])}
 return {'schema':'htt.six_paper.P2_L01.source_response_crosswalk/1','claim_tier':'SOURCE_CONDITIONAL_FINITE_OPERATOR_AND_ONE_SKY_PROCESSING_ONLY',
 'input_sha256':EXPECTED,'source_products':{'temperature':list(x['names_t']),'polarization_EB':list(x['names_eb']),'common_temp_selected':26846,'common_pol_selected':30021,'total_nside64_pixels':49152,
 'source_processing_pixels_native_order':'NESTED_NSIDE2048_TO_RING_NSIDE64','two_masks_different':True,'smica_noSZ_polarization':'NOT_DELIVERED_NOT_ZERO'},
 'temperature_source_geometry':mask_tail_contract(x),'polarization_products':ebi,'polarization_same_sky_differences':polar_product_deltas(x),
 'same_sky_rowspace':same_sky_rowspace(x),
 'ffp':{'statistical_independent_unit':'latent CMB sky paired by row','different_processing_conditions':6,'number_latent_sky_rows':int(x['ffp_pairs'].shape[1]),'not_independent_conditions':True},
 'physical_gates':{'source_Q_U_pixel_maps':'NOT_PRESENT_IN_THIS_SANDBOX','raw_native_POL_mask_and_sky_pixel_coordinates':'NOT_PRESENT_IN_THIS_SANDBOX',
 'full_Planck_spin2_higher_ell_response':'NOT_MEASURED','source_beam_component_sep_foreground_noise_transfer':'UNKNOWN','published_PTE_covariance':'NOT_ESTIMATED',
 'anomaly_p_value':'NOT_ADMITTED','cosmological_B_or_parity_detection':'NOT_ADMITTED'}}
