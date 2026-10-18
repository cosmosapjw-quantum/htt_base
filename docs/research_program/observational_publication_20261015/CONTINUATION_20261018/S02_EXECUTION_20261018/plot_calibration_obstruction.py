"""Standalone scientific figure; reads the actual preserved finite measure."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parent


def main():
    with np.load(ROOT/'results/calibration_obstruction_arrays.npz',allow_pickle=False) as data:
        rho=data['erasure_radius_mag']; eta=data['common_residual_radius_mag'];pair=data['pair_lower_radius_mag']
        weights=data['weights'];centers=data['centers']
    t=np.linspace(0,.12,481)
    fig,axes=plt.subplots(1,3,figsize=(14,4.4))
    for j,z in enumerate(centers):
        axes[0].step(t,[weights@(rho[:,j]>v) for v in t],where='post',label=f'z={z:.3f}')
    axes[0].set(xlabel='Allowed directional distance correction [mag]',ylabel='Strict finite-law mass requiring more',title='Each fitted even angular field')
    axes[0].legend(frameon=False)
    axes[1].step(t,[weights@(eta>v) for v in t],where='post',label='Exact four-window minimax')
    axes[1].step(t,[weights@(pair>v) for v in t],where='post',label='Largest pair lower bound',linestyle='--')
    axes[1].set(xlabel='Allowed differential correction [mag]',title='One arbitrary common angular calibration',xlim=(0,.07))
    axes[1].legend(frameon=False,fontsize=8)
    for label,color in [('Physical x_C','#555555'),('Physical Q','#999999'),('Certified F','#bbbbbb'),('Physical G_F','#dddddd')]:
        axes[2].barh(label,1.,color=color,edgecolor='black')
    axes[2].set(xlim=(0,1),xlabel='Unmeasured/domain-uncertified mass',title='Physical mapping remains unavailable')
    for ax in axes[:2]:ax.set_ylim(0,1);ax.grid(alpha=.2)
    fig.suptitle('Actual CF4 summary-conditioned 2048 coupled draws; working diagnostics only',fontsize=12)
    fig.text(.5,.01,'Exact angular-field calibration algebra; no raw-catalogue refit, calibrated probability or physical shear admission.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.045,1,.94))
    for suffix in ['png','pdf']:fig.savefig(ROOT/f'results/calibration_obstruction.{suffix}',dpi=170)
    plt.close(fig)


if __name__=='__main__':main()
