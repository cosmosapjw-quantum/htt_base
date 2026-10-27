#!/usr/bin/env python3
"""Plot the signed released-chart coefficients from RESULT_RAW.json."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
RAW=Path('/mnt/extdrive/workdir/htt_open_data/r36_public_sn_actual/RESULT_RAW.json')
x=json.loads(RAW.read_text())
fig,axes=plt.subplots(1,2,figsize=(11,4.3),constrained_layout=True)
labels=['$n_x$','$n_y$','$n_z$','$E_1$','$E_2$','$E_3$','$E_4$','$E_5$']
for ax,key,title in zip(axes,('primary','lower_z_sensitivity'),
    ('$0.0233\\leq z_{HD}\\leq0.15$','$0.01\\leq z_{HD}\\leq0.15$')):
    q=x[key];b=np.array(q['fits']['full']['coefficients_mag']);C=np.array(q['full_16x16_covariance_mag2'])
    xx=np.arange(8)
    ax.errorbar(xx-.09,b[:8],yerr=np.sqrt(np.diag(C)[:8]),fmt='o',capsize=2,label='low depth')
    ax.errorbar(xx+.09,b[8:],yerr=np.sqrt(np.diag(C)[8:]),fmt='s',capsize=2,label='high depth')
    ax.axhline(0,color='.35',lw=.8)
    ax.set_xticks(xx,labels);ax.set_ylabel('Apparent magnitude coefficient [mag]')
    ax.set_title(title+'; n='+str(q['fits']['full']['n']))
    ax.grid(alpha=.18)
axes[0].legend(loc='best',fontsize=8)
fig.suptitle('Pantheon+ released-magnitude chart: signed dipole and STF coordinates\n'
             'Marginal 1$\\sigma$ bars are descriptive; primary test is joint 16D GLS')
fig.savefig(HERE/'PUBLIC_SN_SIGNED_COORDINATES.pdf',metadata={'Creator':'R36-08 plot_result.py'})
fig.savefig(HERE/'PUBLIC_SN_SIGNED_COORDINATES.png',dpi=180)
print(HERE/'PUBLIC_SN_SIGNED_COORDINATES.pdf')
