#!/usr/bin/env python3
"""Generate a deterministic 2x2 legacy-style finite sampling diagnostic."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from htt.infer.conditional_legacy_pushforward import ConditionalDraw, conditional_legacy_image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'docs/observational_upgrade_r2/R2-04'
SOURCES = OUT/'sources'
spec = importlib.util.spec_from_file_location('r204_figure_adapter',SOURCES/'code/legacy_adapter.py')
legacy = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = legacy
spec.loader.exec_module(legacy)
hashes = json.loads((SOURCES/'SOURCE_HASHES.json').read_text())
adapter = legacy.LegacyAdapter(SOURCES/'sources/HTT/HTT', legacy.AnalysisContract(
    'r204-synthetic-v1','synthetic-flow','fixed-flat','conditional-VA02-shear',
    'deterministic-finite-sampling-v1'), expected_hashes={
        'htt/'+name: hashes['sources/HTT/HTT/htt/'+name] for name in ('bounds.py','ssot.py')})
fixture = json.loads((OUT/'fixture.json').read_text())
result = conditional_legacy_image([ConditionalDraw(**row) for row in fixture['draws']],adapter,
    source_id=fixture['source_id'],joint_id=fixture['joint_id'],weights=fixture['weights'],
    law_kind=fixture['law_kind'],q_thresholds=fixture['thresholds'])
# Include every finite Q boundary so the strict event is a true step function.
thresholds = sorted(set(fixture['thresholds']) | {float(a.value) for a in result['Q'].atoms if a.value is not None})
result = conditional_legacy_image([ConditionalDraw(**row) for row in fixture['draws']],adapter,
    source_id=fixture['source_id'],joint_id=fixture['joint_id'],weights=fixture['weights'],
    law_kind=fixture['law_kind'],q_thresholds=thresholds)
fig,axs = plt.subplots(2,2,figsize=(7,7),layout='constrained')
colors = ['#0072B2','#D55E00','#009E73','#CC79A7']
for ax,key in zip(axs[0],('x','Q')):
    atoms = result[key].atoms
    ax.bar(range(len(atoms)),[np.nan if a.value is None else float(a.value) for a in atoms],color=colors)
    for i,a in enumerate(atoms):
        if a.value is None: ax.text(i,0,'undefined',rotation=90,va='bottom',ha='center')
    ax.axhline(0,color='black',linewidth=.7)
    ax.set_xlim(-.6,len(atoms)-.4)
    ax.set_xticks(range(len(atoms)),result['draw_ids'])
    ax.set_title(f'Signed {key}; unknown mass {result[key].undefined_mass:.2f}')
    ax.set_ylabel('dimensionless')
pi=result['Pi_intervals'];x=[p['threshold'] for p in pi]
axs[1,0].plot(x,[p['lower'] for p in pi],color=colors[0],drawstyle='steps-post',label='known exceedance mass')
axs[1,0].fill_between(x,[p['lower'] for p in pi],[p['upper'] for p in pi],alpha=.2,color=colors[0],step='post',label='completion outer range')
axs[1,0].scatter(x,[p['known_boundary_mass'] for p in pi],color=colors[1],label='boundary mass')
axs[1,0].set(xlabel='strict Q threshold',ylabel='finite sampling mass',ylim=(0,1))
axs[1,0].legend(fontsize=7)
axs[1,1].axis('off')
axs[1,1].text(0,1,'Deterministic synthetic fixture\nSAMPLING law; same paired IDs/weights\nSamplewise caller-supplied shear ceiling\nFixed-flat comparator; signed branch\nMissing sectors retain original mass\n\nF4 / filling fraction / physical depth:\nUNAVAILABLE\nActual fit and scientific admission: HOLD',va='top',fontsize=9)
fig.suptitle('Conditional legacy diagnostic — synthetic finite sampling law',fontsize=11)
fig.savefig(OUT/'conditional_legacy_diagnostic.png',dpi=200)
fig.savefig(OUT/'conditional_legacy_diagnostic.pdf')
summary={k:result[k] for k in ('source_id','joint_id','law_kind','draw_ids','Pi_intervals','contract','source_sha256','denominator_mode','units','comparator','branch','event','claim_status','F4','filling_fraction','physical_H_d','physical_q_d')}
summary['fixture_sha256']=hashlib.sha256((OUT/'fixture.json').read_bytes()).hexdigest()
summary['images']={key:{'undefined_mass':result[key].undefined_mass,'atoms':[{'latent_id':a.latent_id,'value':None if a.value is None else float(a.value),'mass':a.mass,'status':a.status} for a in result[key].atoms]} for key in ('x','Q')}
(OUT/'diagnostic_result.json').write_text(json.dumps(summary,indent=2)+'\n')
print('Generated synthetic diagnostic; actual fit HOLD')
