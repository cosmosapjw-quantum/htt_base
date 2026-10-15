"""Non-inferential figures from source-locked Planck same-sky diagnostics."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument('--result',type=Path,required=True)
    p.add_argument('--ffp-pairs',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    r=json.loads(a.result.read_text())
    a.output.mkdir(parents=True,exist_ok=True)

    rows=r['loop5_nine_same_sky_same_mask']['rows']
    labels=list(rows); x=np.arange(len(labels))
    fig,ax=plt.subplots(figsize=(10,4.8))
    for ell in [2,3]:
        ax.plot(x,[rows[name][f'eps{ell}_proxy']*1e6 for name in labels],marker='o',label=rf'$\ell={ell}$')
    ax.set_xticks(x,labels,rotation=35,ha='right')
    ax.set_ylabel(r'$10^6\sqrt{\widehat C_\ell}/T_0$')
    ax.set_title('Planck PR3: nine correlated processing images, common fit mask')
    ax.legend();ax.grid(alpha=.2);fig.tight_layout()
    fig.savefig(a.output/'same_sky_nine_eps.png',dpi=160);plt.close(fig)

    pipeline=r['ffp10_six_pipeline_one_sky']['pipelines']; labels=list(pipeline)
    fig,ax=plt.subplots(figsize=(9.5,4.8));x=np.arange(len(labels))
    for ell in [2,3]:
        ax.plot(x,[pipeline[name][f'eps{ell}_proxy']*1e6 for name in labels],marker='o',label=rf'$\ell={ell}$')
    ax.set_xticks(x,labels,rotation=35,ha='right')
    ax.set_ylabel(r'$10^6\sqrt{\widehat C_\ell}/T_0$')
    ax.set_title(r'FFP first-pair processing: mask threshold and finite $\ell_{max}$')
    ax.legend();ax.grid(alpha=.2);fig.tight_layout()
    fig.savefig(a.output/'ffp_six_processing_eps.png',dpi=160);plt.close(fig)

    # One paired latent sky is the unit, NOT six independent map draws.
    with np.load(a.ffp_pairs,allow_pickle=False) as packet:
        paired=np.asarray(packet['paired'],float)
    t0=float(r['harmonic_contract']['T0_microK'])
    fig,ax=plt.subplots(figsize=(9,4.5))
    for ell,sl in [(2,slice(0,5)),(3,slice(5,12))]:
        eps=np.linalg.norm(paired[:,:,sl],axis=2)/(np.sqrt(2*ell+1)*t0)
        span=np.ptp(eps,axis=0)[60:]*1e6
        ax.hist(span,bins=32,histtype='step',density=True,label=rf'$\ell={ell}$ held-out')
        observed=r['ffp10_six_pipeline_one_sky']['paired_calibration'][f'ell{ell}']['observed_eps_spread']*1e6
        ax.axvline(observed,linestyle='--',label=rf'$\ell={ell}$ observed span')
    ax.set_xlabel(r'$10^6\,\Delta(\sqrt{\widehat C_\ell}/T_0)$ across six pipelines')
    ax.set_ylabel('Conditional relative frequency density')
    ax.set_title('Same-sky paired FFP10, 240 holdouts (retrospective diagnostic)')
    ax.legend(fontsize=9);fig.tight_layout()
    fig.savefig(a.output/'ffp_paired_sky_spread.png',dpi=160);plt.close(fig)

if __name__=='__main__':
    main()
