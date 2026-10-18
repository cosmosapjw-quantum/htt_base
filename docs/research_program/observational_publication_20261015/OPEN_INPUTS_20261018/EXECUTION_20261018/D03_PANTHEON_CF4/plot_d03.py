"""Standalone source-conditioned D03 figures, no significance calibration."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE=Path(__file__).resolve().parent
OUT=HERE/'results'
result=json.loads((OUT/'D03_RESULT.json').read_text())
fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
colors=['#3366aa','#bb5533','#228866']
for k,c in enumerate(result['comparisons']):
    with np.load(OUT/(c['mode']+'.npz'),allow_pickle=False) as f:
        z=f['zCMB'];y=f['y_mag'];res=f['residual_rho0']
        axes[0,0].scatter(z,y,s=8,alpha=.35,color=colors[k],label=c['mode']+f" ({c['rows']} rows)")
        ax=axes[0,1]
        if k==1:
            sc=ax.scatter(np.remainder(f['RA']+180,360)-180,f['DEC'],c=res,s=16,cmap='coolwarm',vmin=-.3,vmax=.3)
            fig.colorbar(sc,ax=ax,label='Group SN profiled residual (mag), ρ=0 control')
    for j,fit in enumerate(c['fits']):
        b=np.array(fit['beta_direction_depth'])
        axes[1,0].scatter(np.arange(3)+.08*(k-1)+.012*(j-1),b[:3],color=colors[k],marker=['v','o','^'][j],s=45)
        axes[1,1].scatter(fit['rho'],b[3],color=colors[k],marker=['v','o','^'][j],s=50)
    axes[1,1].plot([x['rho'] for x in c['fits']],[x['beta_direction_depth'][3] for x in c['fits']],color=colors[k],label=c['mode'])
axes[0,0].set(xlabel='Published Pantheon zCMB (depth coordinate)',ylabel='MU_SH0ES − released CF4 modulus (mag)',title='Actual rows and shared host/group counterparts')
axes[0,0].legend(fontsize=8)
axes[0,1].set(xlabel='RA wrapped at 180° (deg, J2000)',ylabel='DEC (deg, J2000)',title='Matched host/group SN sky; repeated rows retained')
axes[1,0].set(xticks=[0,1,2],xticklabels=['nx','ny','nz'],ylabel='Conditional direction response (mag)',title='Joint nuisance quotient; v/o/^ are ρ=−.75/0/+.75')
axes[1,1].set(xlabel='Designed cross-covariance ρ',ylabel='Conditional depth response (mag per Δz=0.02)',title='One PSD sensitivity family; unknown law remains UNKNOWN')
axes[1,1].legend(fontsize=8)
for ax in axes.flat:
    ax.grid(alpha=.2)
    if ax!=axes[0,1]:ax.axhline(0,color='gray',lw=.7)
fig.suptitle('HTT D03 • source-conditioned shared-calibration diagnostics • C0 / CONDITIONAL',fontsize=13)
fig.text(.5,-.018,'Full Pantheon symmetric-part covariance; CF4 shared-incidence working errors. No directional null, PTE, physical anisotropy, or independent validation.',ha='center',fontsize=8)
for suffix in ['png','pdf']:fig.savefig(OUT/('D03_COMPARISON.'+suffix),dpi=180,bbox_inches='tight',metadata={'Title':'D03 conditional Pantheon CF4 distance comparison','Author':'HTT'})
plt.close(fig)
print('D03_COMPARISON.png PDF generated; metadata in D03_RESULT.json')
