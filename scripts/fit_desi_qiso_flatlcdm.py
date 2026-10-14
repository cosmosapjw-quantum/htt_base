#!/usr/bin/env python3
"""Profile the one released DESI BGS qiso datum in a flat-LCDM background.

The result is a conditional likelihood ridge, not a posterior or a catalogue
refit. H0*r_d remains one free positive parameter in km/s.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm

ROOT=Path(__file__).resolve().parents[1]
for path in (ROOT/'htt/src',ROOT/'htt',ROOT/'htt/htt'):
    sys.path.insert(0,str(path))
from htt.infer.r7_desi_law import build_flat_lcdm_bao_law, flat_lcdm_qiso


def analyze(analysis, omega_values):
    payload=analysis['source']
    law=build_flat_lcdm_bao_law(payload)
    observed=float(law.observed[0]); sigma=math.sqrt(float(law.covariance[0,0]))
    if observed-1.959963984540054*sigma <= 0:
        raise ValueError('positive-qiso 95-percent inversion is unavailable')
    out=[]
    for omega in omega_values:
        scale=flat_lcdm_qiso(float(omega),1.,zeff=payload['zeff'],
                             dv_over_rd_fid=payload['DV_over_rd_fid'])
        best=scale/observed
        lower=scale/(observed+1.959963984540054*sigma)
        upper=scale/(observed-1.959963984540054*sigma)
        out.append({'Omega_m':float(omega),'H0_r_d_mle_km_s':best,
                    'H0_r_d_95_lower_km_s':lower,'H0_r_d_95_upper_km_s':upper,
                    'profile_log_density':law.loglik((float(omega),best))})
    return {'task':'OA07','owner':'htt','status':'CONDITIONAL_PHYSICAL_RESPONSE_PROFILE',
            'claim_tier':'C1','source_id':payload['source_id'],
            'source_sha256':payload['source_sha256'],
            'input_analysis':'docs/observational_analysis_20261014/results/desi/analysis.json',
            'model':'flat matter+Lambda FLRW; free H0*r_d; no early-universe sound-horizon calculation',
            'formula':'E=sqrt(Omega_m*(1+z)^3+1-Omega_m); I=int_0^z dz/E; qiso=(c/(H0*r_d))*cbrt(z*I^2/E)/(DV/rd)_fid',
            'units':{'Omega_m':'1','H0_r_d':'km/s','qiso':'1'},
            'conditioning_target':law.conditioning_target,
            'covariance_status':'FIXED_RELEASED_GAUSSIAN_SUMMARY_CONDITIONAL',
            'likelihood_name':'normalized density in observed qiso at fixed physical prediction',
            'prior':'NONE; profile and pointwise Gaussian inversion, not posterior/evidence',
            'selection':'released scalar compressed BGS_BRIGHT syst product used once; no new catalogue selection',
            'observed_qiso':observed,'sigma_qiso':sigma,'zeff':payload['zeff'],
            'DV_over_rd_fid':payload['DV_over_rd_fid'],
            'grid':out,
            'interpretation':'Every listed Omega_m reaches the same maximum by adjusting H0*r_d; one qiso cannot identify both.',
            'scope_limits':['No CMB/CF4 likelihood or joint posterior.','No angular DESI response or window refit.',
                            'No H0 or r_d separately and no native Bianchi family claim.'],
            'references':['https://data.desi.lbl.gov/doc/releases/dr1/vac/full-shape-bao-clustering/',
                          'https://academic.oup.com/mnras/article/534/1/544/7750629']}


def render(result, output_dir):
    output_dir.mkdir(parents=True,exist_ok=False)
    rows=result['grid']
    with (output_dir/'profile.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=rows[0].keys(),lineterminator='\n')
        writer.writeheader();writer.writerows(rows)
    (output_dir/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    omega=np.array([row['Omega_m'] for row in rows])
    mle=np.array([row['H0_r_d_mle_km_s'] for row in rows])
    low=np.array([row['H0_r_d_95_lower_km_s'] for row in rows])
    high=np.array([row['H0_r_d_95_upper_km_s'] for row in rows])
    fig,ax=plt.subplots(figsize=(6.2,4.2))
    ax.fill_between(omega,low,high,color='#56B4E9',alpha=.38,label='pointwise 95% Gaussian inversion')
    ax.plot(omega,mle,color='#0072B2',lw=2,label='conditional maximum')
    ax.set(xlabel=r'$\Omega_m$ (flat $\Lambda$CDM scenario)',ylabel=r'$H_0r_d$ (km s$^{-1}$)',
           title='DESI DR1 BGS scalar BAO: one-datum likelihood ridge')
    ax.legend(frameon=False,fontsize=8)
    fig.text(.01,.01,'Released qiso Gaussian law; free sound-horizon product; no posterior or angular fit.',fontsize=7)
    fig.tight_layout(rect=(0,.035,1,1))
    for suffix in ('png','pdf'):
        fig.savefig(output_dir/f'flatlcdm_profile.{suffix}',dpi=180)
    plt.close(fig)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--analysis',type=Path,default=ROOT/'docs/observational_analysis_20261014/results/desi/analysis.json')
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    analysis=json.loads(args.analysis.read_text())
    omega=np.linspace(.15,.45,121)
    result=analyze(analysis,omega)
    render(result,args.output_dir)
    center=min(result['grid'],key=lambda r:abs(r['Omega_m']-.3))
    print(json.dumps({'output':str(args.output_dir),'Omega_m_reference':center['Omega_m'],
                      'H0_r_d_mle_km_s':center['H0_r_d_mle_km_s'],
                      'H0_r_d_95_km_s':[center['H0_r_d_95_lower_km_s'],center['H0_r_d_95_upper_km_s']]},
                     allow_nan=False))


if __name__=='__main__':main()
