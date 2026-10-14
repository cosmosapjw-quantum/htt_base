#!/usr/bin/env python3
"""Build source-bound claim/figure inventory for the finite solver-free delivery."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'docs/solver_free_research_20261014'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,x):(D/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
LANES={
 'observation_bounds':('scripts/solver_free_observation_bounds.py','saved CLASS score error sensitivity and synthetic selected fold; assumed bounds only','fixed 160 calibration scores; synthetic Gaussian measurement kernel'),
 'gaia_geometry':('scripts/run_solver_free_gaia_geometry.py','fixed-cohort operator supports and simultaneous Gaussian-proxy geometry','saved block-independent covariance; synthetic known Gaussian law only'),
 'union_prior':('scripts/run_solver_free_union_prior.py','assumed node-prior sensitivity; source binding unresolved','frozen Union3 precision, rho=0, same DESI product and proper parameter priors'),
 'cf4_crosslaw':('scripts/run_solver_free_cf4_crosslaw.py','conditional two-law generation/fitting comparison; no empirical survey coverage','fixed 24-slot design and declared PRE/POST shared-calibration laws')}
figs=[];claims=[]
for i,(lane,(script,claim,law)) in enumerate(LANES.items(),1):
 r=D/'results'/lane/'result.json'
 assert r.is_file(),r
 sources=[{'path':str(r.relative_to(ROOT)),'sha256':sha(r)},{'path':script,'sha256':sha(ROOT/script)}]
 claims.append(dict(id=f'SFC{i:02d}',owner='HTT',claim_tier='C0_CONDITIONAL_DIAGNOSTIC',statement=claim,sources=sources,law=law,publication='METHODS_OR_SENSITIVITY_CANDIDATE_NOT_READY_TO_SUBMIT',forbidden=['physical detection','native Bianchi family admission','empirical coverage without source-qualified law','historical HOLD promotion']))
 for f in sorted(r.parent.glob('*')):
  if f.suffix not in {'.svg','.png'}:continue
  figs.append(dict(path=str(f.relative_to(ROOT)),sha256=sha(f),bytes=f.stat().st_size,claim_id=f'SFC{i:02d}',owner='HTT',claim_tier='C0_CONDITIONAL_DIAGNOSTIC',artifact_mode=lane,transfer_source='NONE_NATIVE',allowed_interpretation=claim,covariance_and_null=law,source_result=sources[0],replay_script=sources[1]))
write('CLAIM_LEDGER.json',dict(schema='htt.solver-free-claims/1',date='2026-10-14',base_commit='89621f4c9a6f63449813587a0fadeb13287f8e10',claims=claims,theory={'file':'research/THEOREM.md','sha256':sha(D/'research/THEOREM.md'),'novelty':'application of standard calculus, norm and perturbation identities; not an established new theorem'},historical_holds='UNCHANGED'))
write('FIGURE_MANIFEST.json',dict(schema='htt.solver-free-figures/1',figures=figs,visual_review='review/INDEPENDENT_REVIEW.md',campaign_source_note='CF4 campaign was produced with retained results/cf4_crosslaw/execution_run_selection_crosslaw.py; installed replay guards changed later. Read results/cf4_crosslaw/INTEGRATION_PROVENANCE.json.'))
print(json.dumps({'claims':len(claims),'figures':len(figs)}))
