"""Descriptive figure for the source-bound staged four-frequency carrier."""
import json,pathlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=pathlib.Path(__file__).resolve().parent
with np.load(P/'FULL_CARRIER_AND_CONTRASTS.npz') as z:
    carrier=z['carrier_canonical_96'].copy()
    bands=z['bands_GHz'].copy()
    pairs=z['pair_bands_GHz'].copy()
    contrasts=z['pair_contrasts_canonical_6x24'].copy()
    Q=z['Q_computational'].copy()
fig,axs=plt.subplots(2,1,figsize=(11,6.5),layout='constrained',height_ratios=[2.3,1])
scale=1e-5
m=float(np.max(np.abs(carrier/scale)))
im=axs[0].imshow(carrier/scale,aspect='auto',cmap='RdBu_r',vmin=-m,vmax=m)
axs[0].set_yticks(range(4),[f'{b} GHz' for b in bands])
axs[0].set_xticks([2,8,14,20],['E2','E3','B2','B3'])
for x in (4.5,11.5,16.5):axs[0].axvline(x,color='black',lw=.6)
axs[0].set_title('Delivered native pseudo-mode canonical coordinates on common S4')
fig.colorbar(im,ax=axs[0],label=r'canonical coefficient / $10^{-5}$ K')
xx=np.arange(6)
norm=np.linalg.norm(contrasts,axis=1)/scale
axs[1].bar(xx,norm,color='#435c89')
axs[1].set_xticks(xx,[f'{a}-{b}' for a,b in pairs])
axs[1].set_ylabel(r'$\|\Delta c\|_2 / 10^{-5}$ K')
axs[1].set_xlabel('Oriented pair, GHz (lower minus higher)')
fig.savefig(P/'figure.png',dpi=170)
plt.close(fig)
