#!/usr/bin/env python3
"""Actual CF4 method-cohort and survey-depth STF2 morphology consistency.

Same-coordinate but not independent cosmological realizations.
Cross-variance uses diagonal-Gaussian conditional cohort covariance only:
it is a descriptive distance under this declared mathematical model,
NOT a valid cross-survey physical significance.
"""
import argparse,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

REPO=Path(__file__).resolve().parents[1]
BASE=REPO/'docs/research_program/theory_obs_application_20261015/loop6_kinematics/results/cf4_rawgroup_appHubble_STF2_pooled_methods_v2/result.json'

PAIRS=[
 ('FP_only','TF_only'),
 ('FP_only','SN_only'),
 ('TF_only','SN_only'),
 ('low_depth_001_005','high_depth_005_010'),
 ('fiducial_slope_f015_v250_z01_10','FP_only'),
 ('fiducial_slope_f015_v250_z01_10','TF_only')
]


def run(out):
    if out.exists():raise ValueError('create-only')
    src=json.loads(BASE.read_text())
    profiles=src['cases']
    comparisons={}
    for a,b in PAIRS:
        x=profiles[a];y=profiles[b]
        c=np.asarray(x['five_STF_apparent_shear_directional_H_fraction_coordinates'],float)
        d=np.asarray(y['five_STF_apparent_shear_directional_H_fraction_coordinates'],float)
        u=np.asarray(x['five_STF_conditional_covariance'],float)
        v=np.asarray(y['five_STF_conditional_covariance'],float)
        cos=float(c@d/(np.linalg.norm(c)*np.linalg.norm(d)))
        # Uses sum of marginal Gaussian covariance. For overlapping
        # fiducial method rows, that is a deliberately naive scenario.
        delta=c-d
        mah=float(np.sqrt(delta@np.linalg.solve(u+v,delta)))
        comparisons[a+'__'+b]={
          'first':a,'second':b,
          'frobenius_STF2_cosine':cos,
          'five_coefficient_difference_norm':float(np.linalg.norm(delta)),
          'formal_separate_diagonal_gaussian_mahalanobis_distance':mah,
          'first_norm':float(np.linalg.norm(c)),
          'second_norm':float(np.linalg.norm(d)),
          'sample_groups':[x['source_count'],y['source_count']],
          'statistic_scope':'source-conditional; method and bulk response selection/cosmic covariance unavailable; no significance'
        }
    out.mkdir(parents=True)
    res={'schema':'htt.CF4_STF2_method-cohort-consistency/1',
      'status':'OBSERVED_SOURCE_CONDITIONAL_STF_SHAPE_DIAGNOSTIC_NOT_PHYSICAL_NULL_TEST',
      'source_parent':str(BASE.relative_to(REPO)),
      'source_nonlinear_model':src['approximate_linear_response'],
      'comparisons':comparisons,
      'claim_limits':[
        'FP/TF separate source groups still share underlying cosmic velocity and selection',
        'marginal covariance sum ignores shared signal/cosmic variance/survey calibration',
        'same 5D STF basis and ICRS direction convention is used for all scenarios',
        'cross-method tensor cosine is a useful observable-consistency descriptor only']}
    (out/'result.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n')
    lines=['# CF4 source-specific STF2 directional morphology consistency',
      '','The actual 5-component tensor orientations matter, not only the norm.',
      '| comparison | STF2 normalized cosine | formal diagonal-only Mahalanobis |',
      '|---|---:|---:|']
    for k,p in comparisons.items():
        lines.append(f"| {p['first']} vs {p['second']} | {p['frobenius_STF2_cosine']:.6f} | {p['formal_separate_diagonal_gaussian_mahalanobis_distance']:.4f} |")
    lines+=['','Gaussian Mahalanobis is NOT a calibrated physical sigma or p-value: missing cosmic velocity covariance, method selection and common calibration.',
     'FP vs TF can have similar tensor norms while their patterns are nearly orthogonal in the five-dimensional STF space.',
     'The local source patterns cannot be interpreted as a single global shear tensor without a physics-qualified transfer.']
    (out/'REPORT_KO.md').write_text('\n'.join(lines)+'\n')
    fig,axs=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    labels=['FP_only','TF_only','SN_only','low_depth_001_005','high_depth_005_010']
    X=np.asarray([profiles[k]['five_STF_apparent_shear_directional_H_fraction_coordinates'] for k in labels])
    for k in range(5):
        axs[0].plot(np.arange(len(labels)),X[:,k],marker='o',lw=.8,label=f'STF component {k+1}')
    axs[0].set_xticks(range(len(labels)),labels,rotation=32,ha='right',fontsize=7)
    axs[0].set(ylabel='Dimensionless STF2 directional coefficient',
        title='Same-norm but different 5D source morphology')
    axs[0].legend(fontsize=6)
    keys=list(comparisons)
    axs[1].barh(range(len(keys)),
        [comparisons[k]['frobenius_STF2_cosine'] for k in keys])
    axs[1].set_yticks(range(len(keys)),
        [k.replace('_only','').replace('__',' vs ') for k in keys],fontsize=6)
    axs[1].set(xlabel='Normalized STF2 tensor cosine',xlim=(-1,1),
               title='Method/depth window dependence')
    axs[1].axvline(0,color='k',lw=.6)
    fig.savefig(out/'cf4_STF_method_depth_directional_consistency.png',dpi=160)
    plt.close(fig)
    print(json.dumps({
      'FP_TF_STF_cosine':comparisons['FP_only__TF_only']['frobenius_STF2_cosine'],
      'FP_TF_formal_conditional_mahalanobis':comparisons['FP_only__TF_only']['formal_separate_diagonal_gaussian_mahalanobis_distance'],
      'low_high_STF_cosine':comparisons['low_depth_001_005__high_depth_005_010']['frobenius_STF2_cosine'],
      'status':res['status']},indent=2))
    return res


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--output-dir',type=Path,required=True)
    z=p.parse_args()
    run(z.output_dir)
