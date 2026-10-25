import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import time

import numpy as np
from scipy.stats import f, chi2

ROOT = Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
BASE = ROOT / 'docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025'
CAND = BASE / 'products/R32-02-P1-SELECTED'
OUT = Path(__file__).resolve().parent
START = time.time()
checks = {}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def record(name, value): checks[name] = value
def run(label, command, cwd=CAND):
    t = time.monotonic()
    r = subprocess.run(command, cwd=cwd, capture_output=True, text=True,
                       env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    (OUT / (label + '.stdout')).write_text(r.stdout)
    (OUT / (label + '.stderr')).write_text(r.stderr)
    record(label, {'command': command, 'cwd': str(cwd), 'returncode': r.returncode,
                   'elapsed_seconds': time.monotonic()-t})
    assert r.returncode == 0, label

manifest = load(CAND / 'ARTIFACT_MANIFEST.json')
bad = [r['path'] for r in manifest['files']
       if sha(CAND/r['path']) != r['sha256'] or (CAND/r['path']).stat().st_size != r['bytes']]
record('candidate_manifest', {'files': len(manifest['files']), 'mismatches': bad})
assert not bad
record('candidate_identity', {n: sha(CAND/n) for n in ['ARTIFACT_MANIFEST.json', 'RESULT.json', 'main.pdf']})
sources = load(CAND / 'SOURCE_INPUTS.json')
for spec in sources.values(): assert sha(Path(spec['path'])) == spec['sha256']
source = load(sources['selected_law']['path'])
selected = source['r24_selected_C_union']
radius = 274*15/259*f.ppf(.95,15,259)
record('radii', {'finite_F': radius, 'chi2_algebraic_reference': chi2.ppf(.95,15)})
assert abs(radius-27.058502419705658) < 1e-11
rows = []
for shape, x in selected['scenarios'].items():
    q, scale = x['rss_saved'], x['sigma2_ML_saved']
    G = np.asarray(x['likelihood']['G_full'])
    C = np.asarray(x['covariance_ML_full_including_cross_blocks'])
    beta = np.asarray(x['beta_hat_full_signed'])
    l = -.5*(274*math.log(2*math.pi*scale)+x['likelihood']['logdet_V']+q/scale)
    cb = C[-5:,-5:]; zeroq = float(beta[-5:] @ np.linalg.solve(cb,beta[-5:]))
    ci = np.stack([beta[-5:]-np.sqrt(radius*np.diag(cb)),beta[-5:]+np.sqrt(radius*np.diag(cb))],axis=1)
    scale_error = abs(scale-q/274)
    ll_error = abs(l-x['likelihood']['logL_at_saved_beta_and_sigma2_ML'])
    inv_error = float(np.max(np.abs(C/scale - np.linalg.inv(G)) / np.maximum(1.,np.abs(C/scale))))
    assert scale_error < 1e-12 and ll_error < 1e-9 and inv_error < 1e-8
    assert np.linalg.eigvalsh(cb).min() > 0 and zeroq < radius
    assert np.allclose(ci,x['exact_F_region']['STF5_coordinate_bounds_mag'],rtol=1e-10,atol=1e-10)
    rows.append({'shape':shape,'logL':l,'scale_error':scale_error,'logL_error':ll_error,
                 'inverse_information_scaled_error':inv_error,'zero_STF_quadratic':zeroq,
                 'zero_inside_full15_projected_region': bool(zeroq < radius)})
record('selected_likelihood_and_tensor',rows)
tails=[]
for row in selected['fold_diagnostics']['pivots']:
    p=2*min(f.cdf(row['f_pivot'],row['n_test'],row['nu_train']),f.sf(row['f_pivot'],row['n_test'],row['nu_train']))
    assert abs(p-row['two_sided_tail'])<1e-10
    tails.append(p)
record('fold_reference_tails',{'count':len(tails),'minimum':min(tails),'crossings_below_retrospective_0025':sum(p<.0025 for p in tails)})
selection=load(sources['selection']['path'])
widths={}
for row in selection['fixed_surface']:
    if row['threshold_mag']!=.5 or row['gamma'] not in [1,2,4]: continue
    g,e=row['gamma'],row['event_count']/274
    lo=max(e/g,1-g*(1-e)); hi=min(g*e,1-(1-e)/g)
    expected=(274*lo/628,(274*hi+354)/628)
    assert np.allclose(expected,[row['frame628_lower'],row['frame628_upper']],atol=1e-12,rtol=1e-12)
    widths.setdefault(str(g),[]).append(expected[1]-expected[0])
record('missingness_width_ranges',{k:[min(v),max(v),len(v)] for k,v in widths.items()})
finite=load(BASE/'evidence/P1/results/results_FUNCTIONAL_SENSITIVITY_RESULT.json')
event=next(x for x in finite['strict_exceedance'] if x['threshold']==.05)
assert event['any_window']==1235/2048
e=event['any_window']; envelope=[max(e/2,1-2*(1-e)),min(2*e,1-(1-e)/2)]
assert envelope==event['selection_envelopes']['2.0']
floors=[x for x in finite['floor_depth_sensitivity'] if math.isclose(x['amplitude_floor'],.005) or math.isclose(x['amplitude_floor'],.05) or math.isclose(x['amplitude_floor'],.075)]
record('coupled_finite_measure',{'sample_count':finite['sample_count'],'weight_sum':finite['weight_sum'],'seed':finite['seed'],'event_mass':e,'gamma2_envelope':envelope,'floor_summaries':floors})
hubble=load(BASE/'evidence/P1/results/source_H03_SOURCE_TOMOGRAPHY.json')
H=np.asarray(hubble['joint_covariance_36x36']); c=H[0,9]/math.sqrt(H[0,0]*H[9,9])
record('cross_window_monopoles',{'correlation':c,'difference_sd_joint':math.sqrt(H[0,0]+H[9,9]-2*H[0,9]),'difference_sd_without_cross_covariance':math.sqrt(H[0,0]+H[9,9])})
run('retained_consumer',['python3',str(CAND/'consume_retained.py'),'--out',str(OUT/'replayed_tables')])
table_parity={n:sha(CAND/'tables'/n)==sha(OUT/'replayed_tables'/n) for n in ['likelihood.csv','stf_projection.csv','model_scores.csv','missingness.csv']}
record('table_byte_parity',table_parity)
assert all(table_parity.values())
run('latex_build',['latexmk','-pdf','-interaction=nonstopmode','-halt-on-error','-file-line-error','-outdir='+str(OUT/'build'),'main.tex'])
log=(OUT/'build/main.log').read_text()
issues=[line for line in log.splitlines() if re.search(r'undefined|multiply defined|Overfull|^!|LaTeX Error|not found',line,re.I)]
record('final_build_log_blockers',issues)
assert not issues
run('rebuilt_pdf_text',['pdftotext','-layout',str(OUT/'build/main.pdf'),str(OUT/'rebuilt_extracted.txt')])
record('candidate_rebuilt_text_parity',(OUT/'candidate_extracted.txt').read_bytes()==(OUT/'rebuilt_extracted.txt').read_bytes())
run('pdfinfo',['pdfinfo',str(CAND/'main.pdf')])
for page in [1,5,7,9,11,14,17]:
    run('render_page_'+str(page),['pdftoppm','-f',str(page),'-l',str(page),'-scale-to','1500','-png','-singlefile',str(CAND/'main.pdf'),str(OUT/f'page_{page:02d}')])
record('elapsed_seconds',time.time()-START)
(OUT/'INDEPENDENT_VALIDATION.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps({'status':'CHECKS_COMPLETED','elapsed_seconds':time.time()-START,'radii':checks['radii'],'manifest':checks['candidate_manifest'],'table_parity':table_parity,'pdf_text_parity':checks['candidate_rebuilt_text_parity']}))
