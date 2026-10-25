"""Render saved fixed-source quotient certificate intervals; no certificate replay."""
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path('/mnt/extdrive/workdir/htt_open_data/r25_gaia_source_quotient_certificate')
EXPECTED='55e9d6bd8d9ca98d5736baf9327a51d00d8c01dac14fa8de63a26cb489022404'
assert hashlib.sha256((ROOT/'MANIFEST.json').read_bytes()).hexdigest()==EXPECTED
manifest=json.loads((ROOT/'MANIFEST.json').read_text())
row=next(r for r in manifest['inventory'] if r['path']=='RESULT.json')
raw=(ROOT/'RESULT.json').read_bytes()
assert hashlib.sha256(raw).hexdigest()==row['sha256'] and len(raw)==row['size_bytes']
r=json.loads(raw)
labels=['T_full (q=13)','T_E1 (q=3)','Delta = T_E1 - T_full']
intervals=np.array([r['T_full'],r['T_E1'],r['Delta']],dtype=float)
assert intervals.shape==(3,2) and np.isfinite(intervals).all() and np.all(intervals[:,0]<=intervals[:,1])
fig,axes=plt.subplots(3,1,figsize=(10,6.4))
for ax,(lo,hi),label in zip(axes,intervals,labels):
    width=hi-lo;mid=(lo+hi)/2
    assert width>0
    ax.plot([lo,hi],[0,0],color='#205a91',lw=4,marker='|',markersize=14)
    ax.scatter([mid],[0],color='#bc5b32',s=28,zorder=3)
    ax.set_xlim(lo-2*width,hi+2*width);ax.set_ylim(-.4,.4)
    ax.set_yticks([]);ax.set_xticks([])
    ax.text(.5,-.25,f'[{lo:.9f}, {hi:.9f}]',transform=ax.transAxes,ha='center',va='top',fontsize=9)
    ax.set_ylabel(label,rotation=0,labelpad=90,va='center')
    ax.spines[['top','left','right']].set_visible(False)
fig.suptitle('Fixed-source C0 Gaussian quotient certificate candidate')
fig.text(.02,.08,f"Stored conditional E1 Delta p upper ≤ {r['conditional_E1_Delta_p_upper']}; independent scientific review pending.",fontsize=9)
fig.text(.02,.045,'Each row has its own zoomed scale. Intervals are saved certified bounds; no new calibration or probability was computed.',fontsize=8)
fig.text(.02,.017,'Fixed source and working covariance only; no physical coverage, astrophysical significance, or detection claim.',fontsize=8)
fig.tight_layout(rect=(.1,.12,1,.95))
stem=Path(sys.argv[1]);stem.parent.mkdir(parents=True,exist_ok=True)
for ext in ('png','pdf'):
    fig.savefig(stem.with_suffix('.'+ext),dpi=180,metadata={'Creator':'HTT frozen-result figure assembler','Description':'Conditional saved quotient intervals'})
plt.close(fig)
print(json.dumps({'source_manifest_sha256':EXPECTED,'output_stem':str(stem),'fits':0}))
