"""Plot the actual-Y algebraic response as conditional sensitivity only."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path('/mnt/extdrive/workdir/htt_open_data/r36_foreground_budget_actual')
g=json.loads((ROOT/'GEOMETRY.json').read_text())
x=[row['rho_K_CMB']*1e6 for row in g['conditional_curves']]
y=[row['s_ball_radius_K_CMB']*1e6 for row in g['conditional_curves']]
fig,ax=plt.subplots(figsize=(6.8,4.6),layout='constrained')
ax.plot(x[1:],y[1:],'o-',color='#1c5c8a',label='Actual 7-band conditional center radius')
ax.axvline(x[0],color='#1c5c8a',linestyle=':',alpha=.7,
           label=r'Algebraic minimum $\rho_{min}$ (zero radius)')
ax.axhline(g['SMICA_B_comparator_K_CMB']*1e6,color='#bb4e31',linestyle='--',
           label='Saved SMICA B residual scale (different fitted statistic)')
ax.set_xscale('log');ax.set_yscale('log');ax.set_ylim(.2,600)
ax.set_xlabel(r'Algebraic moment budget $\rho$ ($\mu$K$_{CMB}$)')
ax.set_ylabel(r'Conditional 24-coordinate center radius ($\mu$K$_{CMB}$)')
ax.set_title('Actual PR3 coefficients: common-response sensitivity')
ax.text(.02,.97,'No physical upper radius calibrated\nSMICA is a derived comparator',
        transform=ax.transAxes,va='top',fontsize=9,
        bbox={'facecolor':'white','alpha':.85,'edgecolor':'none'})
ax.grid(True,alpha=.25)
ax.legend(loc='lower right',fontsize=8)
fig.savefig(ROOT/'conditional_geometry.png',dpi=180)
fig.savefig(ROOT/'conditional_geometry.pdf')
print(ROOT/'conditional_geometry.png')
