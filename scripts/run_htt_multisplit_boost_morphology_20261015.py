#!/usr/bin/env python3
"""Observed same-sky component-separation changes versus ideal local Q->O boost.

An algebraic normalized-response sensitivity comparison, NOT a bound on true
physical boost or a fully masked frequency-dependent Planck instrument model.
"""
from __future__ import annotations
import argparse,json,time,resource
from pathlib import Path
import numpy as np
from obsstat.reboot_tensor_features import tensors_from_real,feature_vector
from obsstat.boost_response import quadrupole_boost_octupole

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'docs/research_program/theory_obs_application_20261015/loop5/results/planck_multisplit_spin_v1/retained_common_support_coefficients.npz'
BETA=ROOT/'docs/observational_reboot_20261014/results/physical_dipole_v2/result.json'


def run(out):
    if out.exists():raise ValueError('create-only output required')
    t=time.perf_counter()
    with np.load(SOURCE,allow_pickle=False) as f:
        names=list(f['names_T'])
        rows=np.asarray(f['coeff_T'],float)
    if len(names)!=len(rows) or set(names)!={'SMICA_HM1','SMICA_HM2','SMICA_OE1','SMICA_OE2','NILC_HM1','NILC_HM2','SMICA_FULL','NILC_FULL','SMICA_noSZ_FULL'}:
        raise ValueError('fixed Planck source selection mismatch')
    X={name:rows[i] for i,name in enumerate(names)}
    beta=np.asarray(json.loads(BETA.read_text())['beta_xyz'],float)
    q,o=tensors_from_real(X['SMICA_FULL'])
    oct_boost=quadrupole_boost_octupole(q,beta)
    b=float(np.linalg.norm(oct_boost))
    if b==0:raise ValueError('reference source-beta surrogate zero')
    scenarios={}
    base_o=np.linalg.norm(o)
    for name in names:
        qq,oo=tensors_from_real(X[name])
        morphology=feature_vector(X[name])
        delta=np.linalg.norm(oo-o)
        scenarios[name]={
          'actual_octupole_STF_change_vs_SMICA_full_norm':float(delta),
          'actual_octupole_STF_change_relative_to_SMICA_full_octupole':float(delta/base_o),
          'actual_QO_feature_vector':morphology.tolist(),
          'ratio_change_in_octupole_to_reference_fullsky_Q_to_O_beta_tangent':
                        float(delta/b),
          'algebraic_boost_proxy_octupole_norm_using_own_quadrupole':
                        float(np.linalg.norm(quadrupole_boost_octupole(qq,beta))),
        }
    out.mkdir(parents=True)
    d={
      'schema':'htt.smica-nilc-noSZ-QO-vs-reference-boost/1',
      'status':'SOURCE_BOUND_STF_MORPHOLOGY_AND_ALGEBRAIC_FIRST_ORDER_REFERENCE_ONLY',
      'input_coefficient_source':str(SOURCE.relative_to(ROOT)),
      'kinematic_beta_source':str(BETA.relative_to(ROOT)),
      'beta_reference_norm':float(np.linalg.norm(beta)),
      'norm_Q_microK_tensor':float(np.linalg.norm(q)),
      'norm_O_microK_tensor':base_o,
      'ideal_fullsky_quadrupole_to_octupole_response_norm_same_units':b,
      'ideal_response_to_observed_O_relative_ratio':b/base_o,
      'actual_matched_mask_same_sky_map_changes':scenarios,
      'science_boundary':'Q and O are derived from actual masked fitted low-l coefficients, whereas algebraic beta response is full-sky STF and has NOT been passed through Planck physical beam/compsep/mask response',
      'not':'not a claim about actual solar dipole contamination, source tilt or CMB anomaly significance',
      'seconds':time.perf_counter()-t,
      'peak_rss_kib_linux':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    }
    (out/'result.json').write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
    lines=['# 실제 SMICA/NILC low-ell morphology와 ideal local boost Q->O 수치 비교',
       '',f"beta={d['beta_reference_norm']:.8g}, nominal boost-generated STF octupole norm={b:.8g}, relative to fitted O={100*b/base_o:.6g}%.",
       '| processed map | change in octupole / nominal O (%) | same change / ideal Q->O beta response |',
       '|---|---:|---:|']
    for name,row in scenarios.items():
        lines.append(f"| {name} | {100*row['actual_octupole_STF_change_relative_to_SMICA_full_octupole']:.5g}% | {row['ratio_change_in_octupole_to_reference_fullsky_Q_to_O_beta_tangent']:.5g} |")
    lines +=['','This is a contrast of the size of actual algorithm-dependent Q/O changes against a fixed purely algebraic full-sky response. It is NOT a noise covariance or physical boost contamination budget.',
      'The observed map is already processed; frequency weights and higher harmonic transfer are not included in the algebraic denominator.',
      'Neither numerical ratio nor morphology chirality change creates an anomaly p-value or a Bianchi shear observation.']
    (out/'REPORT_KO.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'status':d['status'],'beta':d['beta_reference_norm'],
     'ideal_beta_octupole_fraction':d['ideal_response_to_observed_O_relative_ratio'],
     'smica_noSZ_vs_full':scenarios['SMICA_noSZ_FULL']['ratio_change_in_octupole_to_reference_fullsky_Q_to_O_beta_tangent'],
     'nilc_vs_smica':scenarios['NILC_FULL']['ratio_change_in_octupole_to_reference_fullsky_Q_to_O_beta_tangent']},indent=2))
    return d


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    run(args.output_dir)
