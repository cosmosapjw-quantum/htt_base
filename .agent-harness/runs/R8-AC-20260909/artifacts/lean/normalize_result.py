#!/usr/bin/env python3
"""One authorized packaging correction; does not invoke Lean or modify proofs."""
from pathlib import Path
import datetime, hashlib, json
ROOT=Path(__file__).resolve().parents[5]
RUN=ROOT/'.agent-harness/runs/R8-AC-20260909'
ART=RUN/'artifacts/lean'
OUT=RUN/'results/lean_runtime.json'
def sha(data): return hashlib.sha256(data).hexdigest()
def rel(p): return p.relative_to(ROOT).as_posix()
def put_once(p,data):
    if p.exists():
        if p.read_bytes()!=data: raise RuntimeError(f'Preservation path already differs: {p}')
    else: p.write_bytes(data)
initial=OUT.read_bytes()
if sha(initial)!='5a34d0fb84192eebdad14ce56d25a8e0cbfc77bf6b2975851fe1d93b403d96d3':
    raise RuntimeError('Initial submitted result changed; correction refused')
put_once(ART/'initial_result_submitted.json',initial)
r=json.loads(initial)
assignment=json.loads((RUN/'assignments/lean_runtime.json').read_text())
observed=(ART/'build_receipt.json').read_bytes()
put_once(ART/'parent_replay_build_receipt_observed.json',observed)
changes=[]
current_artifacts=[]
for row in r['evidence']:
    p=ROOT/row['path']
    data=p.read_bytes() if p.is_file() else None
    current=sha(data) if data is not None else None
    if current!=row['sha256']:
        changes.append({'path':row['path'],'original_sha256':row['sha256'],
            'original_bytes_status':'SUPERSEDED; original exact bytes not retained at this path and not reconstructed',
            'current_observed_sha256':current,'classification':'packaging_metadata',
            'reason':'Parent reports re-executing the verifier; receipt contains elapsed time and completed_at.',
            'observed_copy':rel(ART/'parent_replay_build_receipt_observed.json') if p.name=='build_receipt.json' else None})
    else:
        current_artifacts.append({'path':row['path'],'sha256':row['sha256'],'bytes':len(data),'producer':'lean_runtime original independent submission'})
for p,producer in [(ART/'initial_result_submitted.json','lean_runtime packaging correction: exact original envelope copy'),(ART/'parent_replay_build_receipt_observed.json','parent replay reported by chair; bytes observed and copied by lean_runtime'),(ART/'normalize_result.py','lean_runtime packaging correction')]:
    data=p.read_bytes();current_artifacts.append({'path':rel(p),'sha256':sha(data),'bytes':len(data),'producer':producer})
r['initial_evidence_references']=r.pop('evidence')
r['evidence_reference_changes']=changes
r['artifacts']=current_artifacts
r['assignment_sha256']=assignment['assignment_sha256']
r['agent_type']=assignment['agent_type']
r['result_path']=assignment['result_path']
r['launch_id']=None
r['launch_evidence']='unverified'
r['execution_evidence']='self_declared'
r['started_at']='NOT_MEASURED'
r['started_at_note']='Original subagent start timestamp was not captured; no invented timestamp has been substituted.'
r['tool_versions']={'lean':r['build']['version'],'mathlib_revision':r['build']['mathlib_revision'],'python':'NOT_MEASURED'}
r['commands']=[{'command':r['build']['command'],'cwd':r['build']['cwd'],'env':r['build']['env'],'returncode':r['build']['returncode'],'evidence':'original self-declared build metadata retained in initial_result_submitted.json'},
 {'command':r['reproduce']['command'],'cwd':r['reproduce']['cwd'],'returncode':2,'evidence':'original wrapper invocation; incomplete proof scope, compiler returncode 0'},
 {'command':'python3 .agent-harness/runs/R8-AC-20260909/artifacts/lean/normalize_result.py','cwd':str(ROOT),'scope':'packaging-only; no Lean or mathematics executed'},
 {'command':'python3 -B .codex/hooks/subagent_stop_validate.py','cwd':str(ROOT),'stdin':'HARNESS_RESULT event with registered relative result_path','evidence_path':rel(ART/'packaging_validation.json'),'scope':'result-envelope validation only'}]
r['external_reads']=[p for p in r['files_read'] if Path(p).is_absolute()]
r['files_read']=[p for p in r['files_read'] if not Path(p).is_absolute()]
r['files_read']+=['.agent-harness/scripts/strict_result_validation.py','.agent-harness/scripts/_harness.py','.codex/hooks/subagent_stop_validate.py','.codex/hooks/_common.py',assignment['result_path'],rel(ART/'verify.py'),rel(ART/'initial_result_submitted.json'),rel(ART/'parent_replay_build_receipt_observed.json'),rel(ART/'normalize_result.py')]
r['files_read']=sorted(set(r['files_read']))
r['files_read_evidence']='self_declared'
r['schema_discovery_note']='Requested new_result.py is absent in this checkout; actual strict_result_validation.py and stop consumer were read.'
fid='lean-r8-ac4-unresolved-proof-scopes'
r['findings']=[{'finding_id':fid,'claim_id':'RUN-R8-AC-20260909-AC4','verdict':'inconclusive','severity':'high',
 'evidence_fingerprint':'sha256:'+sha((r['contract_sha256']+'|Lean partial O1 orbit assembly; O2 coverage/radius; J2 probability construction').encode()),
 'statement':'Compiled proofs do not cover every assigned AC4 obligation; unchanged INCONCLUSIVE verdict.',
 'assumptions_used':r['assumptions'],
 'evidence_refs':[rel(ART/'R8.lean'),rel(ART/'initial_result_submitted.json'),rel(ART/'compile_attempt_5.log')],
 'counterevidence_refs':[],
 'reproduction':[r['reproduce']['command']+' (originally executed; NOT rerun during packaging correction)'],
 'unresolved':[item['detail'] for item in r['domain_assumption_diff']],
 'confidence':1.0}]
r['claim_results']=[{'claim_id':'RUN-R8-AC-20260909-AC4','outcome':'findings_present','finding_ids':[fid],
 'summary':'O3 and rational factor support compile; O1/O2 formal scope and Gaussian-marginal probability proof remain incomplete. No mathematical counterexample found; no claim promotion.'}]
r['errors']=[]
r['packaging_correction']={'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'initial_result_sha256':sha(initial),'initial_result_artifact':rel(ART/'initial_result_submitted.json'),
 'verdict_changed':False,'proofs_changed':False,'Lean_rerun':False,
 'original_receipt_reconstructed':False,'validation_path':rel(ART/'packaging_validation.json')}
OUT.write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({'result_path':rel(OUT),'result_sha256':sha(OUT.read_bytes()),'status':r['status'],'changed_historical_evidence_references':changes}))
