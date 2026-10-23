"""Render the source-bound conditional diagnostic from stored results only."""
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE=Path(__file__).resolve().parent
r=json.loads((HERE/'RESULT.json').read_text())
rows=list(csv.DictReader((HERE/'ROWS.csv').open(newline='')))
x=np.array([float(row['fitted_mean_mag']) for row in rows])
y=np.array([float(row['residual_mag']) for row in rows])
fig,axes=plt.subplots(1,2,figsize=(11.2,4.4),layout='constrained')
colors={'accepted':'#277da1','other_quality':'#f9c74f','confused':'#f3722c','nondetection':'#9d4edd'}
for name,color in colors.items():
    mask=np.array([row['outcome']==name for row in rows])
    axes[0].scatter(x[mask],y[mask],s=15 if name=='accepted' else 45,
                    alpha=.75,edgecolor='none',color=color,label=f'{name} ({sum(mask)})')
axes[0].axhline(0,color='black',lw=.8)
axes[0].set(xlabel='Fitted conditional mean DMbest (mag)',ylabel='Actual minus fitted DMbest (mag)',
            title='274 released distances; authored law')
axes[0].legend(fontsize=7,loc='lower right')
d=r['fit']['delta_width_0p1_dex_mag'];lo,hi=r['fit']['delta_t95_interval_mag']
axes[1].errorbar([d],[1],xerr=[[d-lo],[hi-d]],fmt='o',capsize=5,color='#277da1')
axes[1].axvline(0,color='black',lw=.8,ls='--')
axes[1].set(xlabel='Conditional mean contrast for +0.1 dex measured width (mag)',
            title='GLS conditional t interval, 95%',yticks=[],ylim=(.6,1.4))
axes[1].text(.02,.07,f'Mock coverage: {r["mock"]["covered"]}/{r["mock"]["B"]} (conditional PASS)\n'
             f'Actual residual diagnostic: T={r["diagnostic"]["T_actual"]:.3f}, '
             f'p={r["diagnostic"]["p_plus_one"]:.4g}\n'
             'Adopted conditional law criticized by actual rows',transform=axes[1].transAxes,
             fontsize=9,va='bottom',bbox={'facecolor':'#fff2e8','edgecolor':'#f3722c'})
fig.suptitle('R23-DISTANCE • selected-cohort conditional diagnostic (HTT C0)')
for ext in ('png','pdf'):
    fig.savefig(HERE/f'CONDITIONAL_DIAGNOSTIC.{ext}',dpi=180,bbox_inches='tight')
plt.close(fig)
