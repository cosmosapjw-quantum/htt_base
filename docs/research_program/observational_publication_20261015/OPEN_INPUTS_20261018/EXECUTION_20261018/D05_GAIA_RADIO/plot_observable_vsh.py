"""Render derived-only D05 figures from RESULTS.json, no raw source rows."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
FOOTER=('obsstat | DIAGNOSTIC_ONLY | observable fit | use: catalogue/frame sensitivity | transfer: none\n'
        'Null: unavailable | covariance: source 2×2, spatial unknown | forbidden: physical cosmic curl / family ID')

def main():
    r=json.loads((HERE/'RESULTS.json').read_text())
    labels=r['convention']['coefficient_order'];b=np.array(r['all']['coefficient_uasyr'])
    se=np.array(r['all']['formal_sigma_uasyr']);s=r['spatial_sensitivity']
    lo=np.array(s['deletion_min_uasyr']);hi=np.array(s['deletion_max_uasyr'])
    keep=np.array([0,1,2,*range(6,16)]);x=np.arange(len(keep))
    fig,ax=plt.subplots(figsize=(11,5))
    ax.vlines(x,lo[keep],hi[keep],color='tab:orange',lw=6,alpha=.5,label='12 angular deletion envelope')
    ax.errorbar(x,b[keep],yerr=se[keep],fmt='o',color='tab:blue',label='Full fit ± formal working σ')
    ax.axhline(0,color='.5',lw=.7);ax.set_xticks(x,[labels[i] for i in keep],rotation=40,ha='right')
    ax.set_ylabel('Cartesian harmonic coefficient [μas/yr]')
    ax.set_title(f"Gaia-CRF3 {r['retention']['valid_sources']:,} sources: frame-projected observable modes")
    ax.legend(fontsize=9)
    fig.text(.02,.07,'B1 physical modes UNKNOWN after frame projection. Angular deletion envelope is not a confidence interval.',fontsize=8)
    fig.text(.02,.015,FOOTER,fontsize=7)
    fig.tight_layout(rect=(0,.11,1,1))
    for ext in ('png','pdf'):fig.savefig(HERE/('OBSERVABLE_VSH.'+ext),dpi=180)
    plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    h=s['heldout'];cells=np.arange(12)
    axes[0].bar(cells,[z['heldout_sources'] for z in h]);axes[0].set_ylabel('Sources held out')
    axes[0].set_xlabel('Equal-area RA × sin(dec) cell')
    axes[1].plot(cells,[z['heldout_null_mean_chi2_per_component'] for z in h],'o-',label='Zero vector')
    axes[1].plot(cells,[z['heldout_working_mean_chi2_per_component'] for z in h],'s-',label='Fit on other 11 cells')
    axes[1].set_ylabel('Held-out working χ² / component');axes[1].set_xlabel('Cell');axes[1].legend(fontsize=8)
    fig.suptitle('Whole-source angular holdout; common Gaia calibration remains')
    fig.text(.02,.015,FOOTER,fontsize=7)
    fig.tight_layout(rect=(0,.10,1,1))
    for ext in ('png','pdf'):fig.savefig(HERE/('ANGULAR_HOLDOUT.'+ext),dpi=180)
    plt.close(fig)

if __name__=='__main__':main()
