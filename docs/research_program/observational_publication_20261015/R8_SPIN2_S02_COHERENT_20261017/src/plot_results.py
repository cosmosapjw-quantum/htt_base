"""Research plots: optional; no inferred physical cosmological likelihood."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np,json
ROOT=Path(__file__).resolve().parents[1]

def main():
 p=json.loads((ROOT/'results/S02_COHERENT_STF_SOURCE_BOUNDS.json').read_text())['transfer_gap_sensitivity']
 entries=sorted(p.values(),key=lambda x:x['max_interwindow_transfer_gap'])
 x=[z['max_interwindow_transfer_gap'] for z in entries]
 y=[z['coherent_certified_lower_mass'] for z in entries]
 r=[z['rectangle_lower_mass'] for z in entries]
 fig,ax=plt.subplots(figsize=(6.6,4.1))
 ax.plot(x,y,marker='o',label='pairwise coherent transfer certificate')
 ax.plot(x,r,linestyle='--',label='independent-window rectangle lower')
 ax.set(xlabel='assumed norm bound on T_i-T_j',ylabel='certified lower joint draw mass',title='CF4 working draws: b=3, t=0.02, 2048 joint draws')
 ax.set_ylim(0,1);ax.grid(True,alpha=.2);ax.legend(fontsize=8)
 fig.tight_layout();fig.savefig(ROOT/'results/S02_INTERWINDOW_TRANSFER_CERTIFICATE.png',dpi=160);plt.close(fig)
 with np.load(ROOT/'results/R8_T_MASK_SPIN2_PILOT.npz') as data: K=data['K_lowhigh']
 fig,ax=plt.subplots(figsize=(7,4.1));im=ax.imshow(K,aspect='auto',origin='lower',interpolation='nearest')
 ax.set(xlabel='high ell 6-8 E/B coefficients',ylabel='low ell 2-5 E/B coefficients',title='R8 actual PR3 T-mask geometry, injected spin2 basis')
 fig.colorbar(im,ax=ax,label='finite masked fit response');fig.tight_layout();fig.savefig(ROOT/'results/R8_SOURCE_T_MASK_SPIN2_OPERATOR.png',dpi=145);plt.close(fig)
if __name__=='__main__':main()
