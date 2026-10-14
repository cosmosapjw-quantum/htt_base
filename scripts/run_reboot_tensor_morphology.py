#!/usr/bin/env python3
"""New tensor descriptors from accepted pilot coefficients, no repeated map fit."""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
import numpy as np
from obsstat.reboot_tensor_features import FEATURE_NAMES,feature_vector,feature_matrix,tensors_from_real
from calibrate_reboot_statistics import calibrate,write_result,file_sha256

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/observational_reboot_20261014'


def run(out):
    start=time.perf_counter()
    if out.exists():raise ValueError('fresh output directory required')
    source=BASE/'results/smica_pilot/pilot_features_coefficients.npz'
    with np.load(source,allow_pickle=False) as data:
        row=data['observed_retained_coefficients'];rows=data['paired_retained_coefficients']
        if rows.shape!=(300,32):raise ValueError('accepted pilot 300x32 required')
        obs=feature_vector(row);features=feature_matrix(rows)
        q,o=tensors_from_real(row)
        qs,os=zip(*(tensors_from_real(x) for x in rows))
    meta=json.loads((BASE/'results/smica_pilot/declaration.json').read_text())
    meta.update(declaration_id='retrospective-STF-family8-pilot-coefficients-v1',
        analysis_label='Retrospective temperature tensor family; conditional delivered-simulation ranks',
        statistics=[{'name':name,'tail':'two-sided' if i<5 or i==7 else 'upper'}
                    for i,name in enumerate(FEATURE_NAMES)],
        current_selection={'mask':['K1 common_mask >0.5'],'fit_lmax':[5],
            'retained_ells':[2,3,4,5],'features':list(FEATURE_NAMES),'axes':'rotation invariants only',
            'residual_dipole':'not in retained cache; unavailable, never physical dipole',
            'historical_selection':'same observed sky; unknown complete historical trial family, not corrected by this max'},
        feature_conventions={'coefficients':'orthonormal real [m0,cos,sin] microK',
            'power':'C_l=sum(c_l^2)/(2l+1) microK²; D_l=l(l+1)C_l/(2pi)',
            'Q':'T2=Q_ij*n_i*n_j; Q:Q=15/(8pi) sum(c2²)',
            'O':'T3=O_ijk*n_i*n_j*n_k; O:O=35/(8pi) sum(c3²)',
            'quadrupole_shape':'tr(Q³)/(Q:Q)^1.5; parity even',
            'octupole_concentration':'lambda_max(A)/(O:O), A_ij=O_iab*O_jab; parity even',
            'QO_contraction':'tr(Q² A)/[(Q:Q)(O:O)]; parity even',
            'chirality':'v dot (Qv cross Av)/[|v||Qv||Av|], v_i=O_ijk Q_jk; parity odd',
            'frame':'Galactic Cartesian; shapes SO(3) invariant; full tensors retained'})
    out.mkdir(parents=True)
    (out/'declaration.json').write_text(json.dumps(meta,indent=2)+'\n')
    result=calibrate(obs,features[60:],meta,features[:60])
    result['scientific_admission']={'status':'EXPLORATORY_RETROSPECTIVE_CONDITIONAL_ONLY',
        'physical_null_adequacy':'UNVERIFIED','reused_rows':'same 60 training/240 calibration as RB00, no new independent evidence',
        'historical_p_comparison':'not an improvement or independent confirmation',
        'observed_temperature_tensors_not_physical_shear':True}
    result['interpretation']['rank']='Conditional exploratory rank for this eight-feature family only; full historical selection and physical sky exchangeability remain unverified.'
    write_result(result,obs,features[60:],features[:60],out)
    np.savez(out/'tensor_features.npz',observed=obs,training=features[:60],null=features[60:],
        observed_Q=q,observed_O=o,paired_Q=np.array(qs),paired_O=np.array(os),
        observed_coefficients=row,paired_coefficients=rows)
    receipt={'task':'RB02','source':str(source.relative_to(ROOT)),'source_sha256':file_sha256(source),
        'code_sha256':file_sha256(__file__),'feature_code_sha256':file_sha256(ROOT/'htt/obsstat/reboot_tensor_features.py'),
        'elapsed_seconds':time.perf_counter()-start,'seed':'no new random draws','batch':'300 retained pilot rows',
        'requested_parent':'gpt-6.1-sol/high','observed_parent':'UNKNOWN','status':'ACTUAL_CACHED_COEFFICIENT_EXECUTION'}
    (out/'execution_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,required=True)
    a=parser.parse_args();r=run(a.output_dir)
    print(json.dumps(r['global_joint_null']))
