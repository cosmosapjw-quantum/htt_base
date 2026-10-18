"""Aggregate membership/composition plots; no sky rows or statistical claims."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
r=json.loads((HERE/'results/UPSTREAM_SELECTION.json').read_text())
fig,axes=plt.subplots(1,2,figsize=(11.4,4.1),layout='constrained')
total=np.array([x['data_count'] for x in r['quality_cells']]).reshape(6,6)
used=np.array([x['has_DMbest_count'] for x in r['quality_cells']]).reshape(6,6)
fraction=np.divide(used,total,out=np.full((6,6),np.nan),where=total>0)
im=axes[0].imshow(fraction,origin='lower',vmin=0,vmax=1,cmap='viridis')
for qs in range(6):
    for qw in range(6):
        if total[qs,qw]:
            axes[0].text(qw,qs,f'{used[qs,qw]}/{total[qs,qw]}',ha='center',va='center',fontsize=7,color='white' if fraction[qs,qw]<.5 else 'black')
axes[0].set(xlabel='WISE quality QWflag',ylabel='SDSS quality QSflag',title='Published DMbest entries / data entries\nin the Table 1 PGC cohort')
fig.colorbar(im,ax=axes[0],label='Descriptive inclusion fraction')
for route,label in [('has_DMbest','Any measured upstream DMbest'),('optical_only','Optical, W1 unavailable'),('optical_and_W1','Optical + W1 available'),('W1_only','W1 only')]:
    val=r['band_contributors'][route]['windows']
    axes[1].plot(range(5),[100*x['working_inverse_variance_mass_fraction'] for x in val],marker='o',label=label)
axes[1].set(xticks=range(5),xticklabels=['all','.025','.040','.060','.080'],xlabel='Selected-group Gaussian window center z',ylabel='Pooled working weight in supported groups (%)',title='Source identity support in 35,970 CF4 groups\nGroups can support several band routes')
axes[1].grid(alpha=.2);axes[1].legend(fontsize=7)
fig.suptitle('H02 actual upstream membership diagnostics — selection law and covariance remain unknown',fontsize=10)
for suffix in ('png','pdf'):
    fig.savefig(HERE/f'results/UPSTREAM_SELECTION.{suffix}',dpi=180)
plt.close(fig)
