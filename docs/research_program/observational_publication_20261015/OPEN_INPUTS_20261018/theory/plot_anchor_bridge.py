from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from anchor_bridge import directions

p=Path(__file__).resolve().parent
j=json.loads((p/'results/ANCHOR_BRIDGE.json').read_text())
n=directions(); e=np.array(j['design_augmentation']['new_directions_PROSPECTIVE_ONLY'])
fig=plt.figure(figsize=(11,4.5),layout='constrained')
ax=fig.add_subplot(121,projection='mollweide')
for v,mark,col,label in [(n,'o','#286f9b','Published maser directions'),(e,'*','#d57a27','Prospective design points')]:
    lon=np.arctan2(v[:,1],v[:,0]); lat=np.arcsin(v[:,2])
    ax.scatter(lon,lat,marker=mark,color=col,s=70,label=label,zorder=3)
ax.grid(alpha=.3); ax.set_title('J2000 anchor geometry'); ax.legend(loc='lower left',fontsize=8)
ax2=fig.add_subplot(122)
labels=['6 masers: dipole only','9 directions: dipole + quadrupole']
gain0=j['dipole_only_unit_l2_anchor_error_to_x_gain']; gain1=j['design_augmentation']['dipole_unit_l2_error_gains'][0]
sig=np.geomspace(1e-4,.2,200)
ax2.loglog(sig,1.96*sig*gain0,label=labels[0],color='#286f9b')
ax2.loglog(sig,1.96*sig*gain1,label=labels[1],color='#d57a27')
ax2.axhline(.0099562061,color='black',ls='--',label='H02 conditional x lower endpoint')
ax2.set_xlabel('Assumed independent per-anchor scale [mag]')
ax2.set_ylabel('Gaussian planning halfwidth for common x dipole [mag]')
ax2.set_title('Ideal precision: relative method calibration known')
ax2.legend(fontsize=7); ax2.grid(alpha=.2)
fig.suptitle('Finite calibration design · known relative calibration · C0 diagnostic',fontsize=12)
fig.savefig(p/'results/ANCHOR_BRIDGE.png',dpi=180)
print(p/'results/ANCHOR_BRIDGE.png')
