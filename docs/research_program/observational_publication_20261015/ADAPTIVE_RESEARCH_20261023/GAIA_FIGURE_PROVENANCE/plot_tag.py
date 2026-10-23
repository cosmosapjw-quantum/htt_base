"""Render frozen Gaia TAG contrasts; no fit, replay, or new statistical calibration."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path('/mnt/extdrive/workdir/htt_open_data/r25_gaia_release_tag_association')
EXPECTED = '3d2e96774c28cb5c3aa4d00757e022d61d1d696f50ff50e1b4dcdd31fc181793'
p = argparse.ArgumentParser(); p.add_argument('mode', choices=('points','correlation')); p.add_argument('stem',type=Path); a=p.parse_args()
assert hashlib.sha256((ROOT/'MANIFEST.json').read_bytes()).hexdigest() == EXPECTED
manifest=json.loads((ROOT/'MANIFEST.json').read_text())
def verified(name):
    f=ROOT/name; row=manifest['files'][name]
    assert f.stat().st_size==row['bytes'] and hashlib.sha256(f.read_bytes()).hexdigest()==row['sha256']
    return f
names=json.loads(verified('COEFFICIENT_ORDER.json').read_text())['FULL13_order']
if a.mode=='points':
    with np.load(verified('M0_OBSERVED.npz'),allow_pickle=False) as z0, np.load(verified('M1_OBSERVED.npz'),allow_pickle=False) as z1:
        d0=z0['delta']; d1=z1['delta']; e0=np.sqrt(np.diag(z0['delta_covariance'])); e1=np.sqrt(np.diag(z1['delta_covariance']))
    assert d0.shape==d1.shape==e0.shape==e1.shape==(13,) and np.isfinite([d0,d1,e0,e1]).all()
    fig,ax=plt.subplots(figsize=(11,6.2)); x=np.arange(13)
    ax.errorbar(x-.14,d0,yerr=e0,fmt='o',capsize=2.5,label='M0',color='#205a91')
    ax.errorbar(x+.14,d1,yerr=e1,fmt='s',capsize=2.5,label='M1',color='#bc5b32')
    ax.axhline(0,color='0.5',linewidth=.8);ax.set_xticks(x,names,rotation=65,ha='right',fontsize=8)
    ax.set_ylabel('Tag contrast (microarcseconds/year)')
    ax.set_title('Released AGN tag: FULL13 contrasts (same Gaia outcomes)')
    ax.legend();fig.text(.02,.01,'Bars: ±1 marginal C0 working-covariance SD; correlated estimates, not independent or coverage-calibrated. Numerical components checked; historical pre-PM criterion HOLD.',fontsize=8)
    fig.tight_layout(rect=(0,.055,1,1))
else:
    with np.load(verified('COMPARISON.npz'),allow_pickle=False) as z:
        V=np.block([[z['V00'],z['V01']],[z['V10'],z['V11']]])
    assert V.shape==(26,26) and np.isfinite(V).all()
    assert np.all(np.diag(V)>0)
    scale=np.sqrt(np.diag(V)); R=V/np.outer(scale,scale)
    assert np.max(np.abs(R))<=1+1e-8
    fig,ax=plt.subplots(figsize=(8.5,7.5));im=ax.imshow(R,cmap='RdBu_r',vmin=-1,vmax=1,interpolation='nearest')
    ax.axhline(12.5,color='k',linewidth=.8);ax.axvline(12.5,color='k',linewidth=.8)
    ax.set_xticks([6,19],['M0 FULL13','M1 FULL13']);ax.set_yticks([6,19],['M0 FULL13','M1 FULL13'])
    ax.set_title('Joint M0/M1 contrast correlation, C0 working model')
    fig.colorbar(im,ax=ax,label='Correlation')
    fig.text(.02,.015,'All 26 coordinates, including cross-model blocks; same outcomes. Cross-source covariance unknown; historical pre-PM criterion HOLD.',fontsize=8)
    fig.tight_layout(rect=(0,.04,1,1))
a.stem.parent.mkdir(parents=True,exist_ok=True)
for ext in ('png','pdf'):
    fig.savefig(a.stem.with_suffix('.'+ext),dpi=180,metadata={'Creator':'HTT frozen-result figure assembler','Description':'Conditional descriptive plot from saved Gaia TAG arrays'})
plt.close(fig)
print(json.dumps({'mode':a.mode,'source_manifest_sha256':EXPECTED,'output_stem':str(a.stem),'fits':0}))
