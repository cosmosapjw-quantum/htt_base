#!/usr/bin/env python3
"""Source-gated P2/L01 T+E/B crosswalk and manufactured mask-spin check."""
from __future__ import annotations
import argparse,json,hashlib,sys
from pathlib import Path
import numpy as np
from spin2_finite import block_design,response_from_design
from l01_source import load_inputs,summarize

UPSTREAM_LOOP5_SHA='abbc49075634899499f1ba615c5f2ba0192e4f949d3d6cc8bfe2171bf862312a'
UPSTREAM_RESULT16_SHA='85b82fac9e108280d1386bee0ba24cceb8e3e3d7a6a3bb4b4ca5559d285f9248'
UPSTREAM_RESULT32_SHA='not_pinned_result_json_npz_is_exact'


def sha256(p):
 h=hashlib.sha256();
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(2<<20),b''):h.update(b)
 return h.hexdigest()


def validate_upstream(source_json):
 p=Path(source_json)
 for file,sha in [('result.json',UPSTREAM_LOOP5_SHA),('result_2.json',UPSTREAM_RESULT16_SHA)]:
  if sha256(p/file)!=sha:raise ValueError('upstream JSON original SHA mismatch '+file)
 a=json.loads((p/'result.json').read_text());b=json.loads((p/'result_2.json').read_text())
 if a['common_T_nside64_pixel_count']!=26846 or a['common_POL_nside64_pixel_count']!=30021 or b['cases'][0]['selected_pixels']!=26846:
  raise ValueError('upstream mask geometry contract mismatch')
 return {'original_Loop5_json_sha256':UPSTREAM_LOOP5_SHA,
         'original_Loop9_mask_response_json_sha256':UPSTREAM_RESULT16_SHA,
         'source_T_P_support_pixels':[a['common_T_nside64_pixel_count'],a['common_POL_nside64_pixel_count']],
         'source_T_ell0to5_condition':a['T_ell0_to5_full_rank_condition']['design_condition'],
         'source_POL_spin2_condition':a['spin2_ell2_to5_rank_condition']['condition'],
         'upstream_POL_identity_residual':a['spin2_ell2_to5_rank_condition']['identity_residual']}


def spin2_manufactured_case(n=768,mask_size=700):
 idx=np.arange(n,dtype=float)
 z=1-2*(idx+.5)/n
 phi=(idx*np.pi*(3-np.sqrt(5)))%(2*np.pi)
 theta=np.arccos(z);x=np.sin(theta)*np.cos(phi)
 low=block_design(theta,phi,2,5);high=block_design(theta,phi,6,8)
 allmask=np.ones(n,dtype=bool)
 az=np.zeros(n,dtype=bool);bx=np.zeros(n,dtype=bool)
 az[np.argsort(z)[-mask_size:]]=True
 bx[np.argsort(x)[-mask_size:]]=True
 ee=[];bb=[];hei=[];hbi=[];offs=0
 for ell in range(2,6):
  q=2*ell+1;ee.extend(range(offs,offs+q));bb.extend(range(offs+q,offs+2*q));offs+=2*q
 offs=0
 for ell in range(6,9):
  q=2*ell+1;hei.extend(range(offs,offs+q));hbi.extend(range(offs+q,offs+2*q));offs+=2*q
 def case(label,mask):
  k,meta=response_from_design(low,high,mask)
  return {'case':label,'selected_spatial_pixels':int(mask.sum()),'low_design_condition':meta['low_condition'],
          'low_identity_residual':meta['low_identity_residual'],
          'full_high_ell6_8_to_low_ell2_5_operator_norm':float(np.linalg.norm(k,2)),
          'B_low_from_E_high_norm':float(np.linalg.norm(k[np.ix_(bb,hei)],2)),
          'E_low_from_B_high_norm':float(np.linalg.norm(k[np.ix_(ee,hbi)],2)),
          'matrix':k}
 a,b,c=[case(*x) for x in [('full_all',allmask),('z_top700',az),('x_top700',bx)]]
 difference=float(np.linalg.norm(b['matrix']-c['matrix']))
 for i in (a,b,c):i.pop('matrix')
 return {'statistics':[a,b,c], 'same_size_mask_response_difference_Frobenius':difference,
         'source_type':'MANUFACTURED_FIBONACCI_SKY_CONTRAST_NOT_PLANCK',
         'finite_spin2_ell2_5_cols':64,'finite_spin2_ell6_8_cols':90,
         'conditioned_on_local_polarization_frame':True}


def run(base_dir,output_dir):
 base=Path(base_dir);output=Path(output_dir)
 if output.exists():raise FileExistsError('create-only output required')
 x=load_inputs(base/'source')
 legacy=validate_upstream(base/'source_sourcejson')
 result=summarize(x)
 result['source_comparison_legacy']=legacy
 result['source_mask_mathematical_experiment']=spin2_manufactured_case()
 result['readiness']='L01_COMPLETE_ONLY_IF_T_EB_OPERATORS_CONTRACT_SOURCE_MATCHED;BEAM_E2E_HOLD'
 result['scientific_disposition']='T_AND_FINITE_EB_COEFFICIENT_SOURCE_BOUND_MASK_GEOMETRY;ACTUAL_POL_HIGH_ELL_LEAKAGE_UNIDENTIFIED'
 output.mkdir(parents=True)
 (output/'L01_T_EB_SOURCE_LEDGER.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
 return result

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--base-dir',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--output-dir',required=True,type=Path);a=p.parse_args()
 r=run(a.base_dir,a.output_dir)
 print(json.dumps({'source_t':len(r['source_products']['temperature']),'source_eb':len(r['source_products']['polarization_EB']),
                   'source_pol_mask_selected':r['source_products']['common_pol_selected'],
                   'T_K6_32_norm':r['temperature_source_geometry']['combined'],
                   'spin2_manufactured_cut_k_norm':r['source_mask_mathematical_experiment']['statistics'][1]['full_high_ell6_8_to_low_ell2_5_operator_norm'],
                   'scientific_disposition':r['scientific_disposition']}))
