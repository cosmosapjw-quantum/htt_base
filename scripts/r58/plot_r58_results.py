#!/usr/bin/env python3
"""Plot committed R58 conditional calibration and joint-set direction images."""
from pathlib import Path
import argparse,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
 p=argparse.ArgumentParser();p.add_argument('--results',type=Path,required=True);a=p.parse_args()
 data=json.loads((a.results/'OWNED_TENSOR_RESULT.json').read_text());v=json.loads((a.results/'FIVE_VIEW_RESULT.json').read_text())
 fig,axs=plt.subplots(1,2,figsize=(12,5.2),layout='constrained')
 names=list(data['variants']); vals=[data['variants'][n]['block_diagonal_uncertainty_calibration'] for n in names]
 cov=np.array([x['coverage_of_nominal_95_ellipsoid_under_full_covariance'] for x in vals]);err=np.array([x['simulation']['mc_standard_error'] for x in vals])
 y=np.arange(len(names));axs[0].errorbar(100*cov,y,xerr=100*err,fmt='o',color='#b34437',capsize=3,label='Cross-block covariance removed')
 axs[0].axvline(95,color='#555555',ls='--',lw=1,label='Nominal 95%')
 axs[0].axvline(100*vals[0]['full_GLS_reference_coverage_same_draws'],color='#176b89',lw=1.5,label='Full GLS, same draws')
 axs[0].set(yticks=y,yticklabels=[n.replace('log_','') for n in names],xlabel='Conditional Gaussian coverage (%)',title='Same design, different covariance')
 axs[0].legend(fontsize=8,loc='center right');axs[0].invert_yaxis()
 dirs=v['directional_observable']['directions'];ls=list(dirs)
 for i,k in enumerate(ls):
  d=dirs[k]['simultaneous_95_union_interval_hull'];lo,hi=d['lower'],d['upper']
  axs[1].plot([100*lo,100*hi],[i,i],lw=3,color='#176b89');axs[1].plot([100*lo,100*hi],[i,i],'|',ms=10,color='#176b89')
 axs[1].axvline(0,color='#555555',lw=1,ls='--');axs[1].set(yticks=range(6),yticklabels=ls,xlabel='100 × apparent log-H anisotropy',title='95% simultaneous union: fixed ICRS directions');axs[1].invert_yaxis()
 for ax in axs:ax.spines[['top','right']].set_visible(False);ax.grid(axis='x',alpha=.15)
 fig.suptitle('R58 · Existing selected CF4 sample · 35,970 groups / 7 nuisance models',fontsize=13)
 fig.supxlabel('Left: 20,000 fixed-Gaussian draws; bars are Monte Carlo ±1σ.  Right: dH·n + κ:nn; velocity and monopole excluded.',fontsize=8)
 fig.savefig(a.results/'R58_OBSERVABLE_SUMMARY.png',dpi=170)
 print(a.results/'R58_OBSERVABLE_SUMMARY.png')
if __name__=='__main__':main()
