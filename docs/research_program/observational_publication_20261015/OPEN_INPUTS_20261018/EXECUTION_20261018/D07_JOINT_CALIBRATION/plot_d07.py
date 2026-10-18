from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent
r=json.loads((HERE/'D07_RESULT.json').read_text())
fig,axes=plt.subplots(2,1,figsize=(12,8),layout='constrained',sharex=True)
colors=['#3366aa','#dd8833','#228866']
for k,row in enumerate(r['projections']):
    for j,ax in enumerate(axes):
        p=row['projections'][j*8:(j+1)*8]
        lo=np.array([x['lower_mag'] for x in p]);hi=np.array([x['upper_mag'] for x in p]);mid=(lo+hi)/2
        pos=np.arange(8)+.16*(k-1)
        # Preserve raw endpoints, including solver-precision ordering ambiguity.
        # Direct segments do not clamp or reorder the recorded LP objectives.
        ax.vlines(pos,lo,hi,color=colors[k],linewidth=1.5)
        ax.scatter(pos,mid,color=colors[k],s=25,label=f"t = tmin + {row['reference_increment']}")
        ax.scatter(pos,lo,color=colors[k],marker='_',s=65)
        ax.scatter(pos,hi,color=colors[k],marker='_',s=65)
        ax.axhline(0,color='gray',lw=.7);ax.grid(alpha=.2);ax.set(ylabel='Compatible coordinate projection (mag)')
axes[0].set_title('ζ = η − κP: relative calibration field; shared γ bounded ±0.02 mag')
axes[1].set_title('ψbase = θbase + κP: relative latent apparent field; physical interpretation unavailable')
axes[0].legend(ncol=3);axes[1].set_xticks(np.arange(8),r['basis']);axes[1].set_xlabel('Original J2000 raw dipole / STF quadrupole coefficient basis')
fig.suptitle(f"D07 actual joint calibration contrasts • {r['pair_rows_retained']} pairs / {r['calibrator_direction_support']} supported calibrator rows\nC0 / CONDITIONAL • tmin={r['minimum_compatible_reference_t']:.5f} reference units; 97 bounded LPs",fontsize=13)
fig.text(.5,-.045,'Segments preserve raw LP endpoints; tiny tmin crossings unresolved at solver precision, not confidence intervals.\nAbsolute common calibration η and latent apparent θ are unbounded in this declared model; physical interpretation unavailable; science HOLD.',ha='center',fontsize=8)
for suffix in ['png','pdf']:fig.savefig(HERE/('D07_JOINT_CALIBRATION.'+suffix),dpi=180,bbox_inches='tight')
plt.close(fig)
print('one D07 figure emitted as PNG/PDF')
