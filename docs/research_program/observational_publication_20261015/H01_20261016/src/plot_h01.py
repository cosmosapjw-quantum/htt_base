"""Visualize conditional source-window sensitivity, NOT cosmological H(z)."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
v=json.loads((ROOT/'results/H01_SOURCE_WINDOW_RESULT.json').read_text())
series=v['scenarios']
fig,ax=plt.subplots(figsize=(7.6,4.3))
for group in series:
    rows=group['windows'];zs=[x['redshift_center'] for x in rows];h=[x['H_app_working_km_s_Mpc'] for x in rows]
    ax.plot(zs,h,marker='o',label=group['model'])
ax.set(xlabel='Declared radial window center z',ylabel=r'$H_W$ working proxy [km s$^{-1}$ Mpc$^{-1}$]',title='CF4 source-conditional radial and angular window sensitivity')
ax.legend();fig.tight_layout();fig.savefig(ROOT/'figures/H01_WINDOW_TRAJECTORIES.png',dpi=170);plt.close(fig)
fig,ax=plt.subplots(figsize=(6.4,5.5))
cor=np.asarray(v['cross_window_correlation_diagonal_working_law'])
im=ax.imshow(cor,origin='upper',vmin=-1,vmax=1);fig.colorbar(im,ax=ax,label='Working-law conditional correlation')
names=[f"{g['model'][:3]}-{r['id']}" for g in series for r in g['windows']]
ax.set_xticks(range(8),names,rotation=55,ha='right');ax.set_yticks(range(8),names)
ax.set_title('Shared-CF4-groups window covariance, diagonal noise model')
fig.tight_layout();fig.savefig(ROOT/'figures/H01_WINDOW_CORRELATION.png',dpi=170);plt.close(fig)
