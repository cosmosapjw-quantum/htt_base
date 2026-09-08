from pathlib import Path
import json,hashlib,datetime
root=Path.cwd(); base=root/'.agent-harness/runs/R8-AC-20260909'; out=base/'artifacts/sage_singular'
p=base/'results/sage_singular_runtime.json'; initial=out/'initial_result_before_packaging_correction.json'
with initial.open('xb') as f: f.write(p.read_bytes())
a=json.loads((base/'assignments/sage_singular_runtime.json').read_text()); r=json.loads(initial.read_text())
observed=out/'checks_observed_after_parent_reported_rerun.json'
with observed.open('xb') as f: f.write((out/'checks.json').read_bytes())
old_rows=r['artifacts']; old_checks=next(x for x in old_rows if x['path'].endswith('/checks.json'))
current_bytes=observed.read_bytes(); current_sha=hashlib.sha256(current_bytes).hexdigest()
r['evidence_attempts']={'original_axis_submission':{'declared_checks_path':old_checks['path'],'declared_checks_sha256':old_checks['sha256'],'original_envelope_preserved_at':str(initial.relative_to(root)),'engine_run_status':'PASS','mathematical_checks_embedded_in_original_result':True},'parent_reported_rerun_observation':{'source_path':old_checks['path'],'snapshot_path':str(observed.relative_to(root)),'observed_sha256':current_sha,'observed_bytes':len(current_bytes),'differs_from_original_declared_hash':current_sha!=old_checks['sha256'],'evidence_origin':'parent reported rerun; current bytes copied by this subagent, not an engine rerun in this packaging correction'},'classification':'Dynamic generated checks JSON includes completion timestamp; preserve attempts separately. Original declared hash remains in initial result and this record; no silent replacement.'}
r.update(assignment_sha256=a['assignment_sha256'],agent_type=a['agent_type'],result_path=a['result_path'],launch_id=None,launch_evidence='unverified',execution_evidence='self_declared',started_at='UNKNOWN_NOT_RECORDED',tool_versions=r['tools'],files_read_evidence='self_declared',findings=[],errors=[])
r['started_at_evidence']='Original start timestamp was not recorded; UNKNOWN_NOT_RECORDED is deliberate and no start time is inferred from file metadata.'
r['commands']=[{'command':'sage -python .agent-harness/runs/R8-AC-20260909/artifacts/sage_singular/verify.py','cwd':str(root),'attempt':1,'exit_code':1,'transcript':str((out/'sage_transcript_attempt1.txt').relative_to(root)),'source':str((out/'verify_attempt1.py').relative_to(root))},{'command':'sage -python .agent-harness/runs/R8-AC-20260909/artifacts/sage_singular/verify.py','cwd':str(root),'attempt':2,'exit_code':0,'transcript':str((out/'sage_transcript_attempt2.txt').relative_to(root)),'source':str((out/'verify.py').relative_to(root))},{'command':r['standalone_singular_command'],'cwd':str(root),'exit_code':0,'transcript':str((out/'singular_transcript.txt').relative_to(root))}]
r['claim_results']=[{'claim_id':'RUN-R8-AC-20260909-AC4','outcome':'examined_no_findings','finding_ids':[],'summary':'SageMath/Singular axis independently passes the five registered exact obligations. Generic inequalities retain named premises; rational scaling/support are fixed fixtures. No aggregate four-axis or physical/product admission. Packaging delivery remains separate.','evidence_refs':[str((out/'proof_scope.md').relative_to(root)),str((out/'sage_transcript_attempt2.txt').relative_to(root)),str((out/'singular_transcript.txt').relative_to(root)),str(initial.relative_to(root))],'evidence_fingerprint':'R8-ORBIT-RANK-JOINT-JET-V1:sage_singular:five-obligations:independent-attempt2'}]
r['external_reads']=[{'path':x,'evidence':'self_declared'} for x in r['files_read'] if Path(x).is_absolute()]
reads=[x for x in r['files_read'] if not Path(x).is_absolute()]
reads += ['.agent-harness/scripts/strict_result_validation.py','.agent-harness/scripts/_harness.py','.codex/hooks/subagent_stop_validate.py','.codex/hooks/_common.py','.agent-harness/HISTORICAL_RUNS.json','.agent-harness/runtime/ACTIVE_RUN','.agent-harness/ACTIVE_RUN']
# Mutable checks.json is deliberately not re-bound as if it were the original
# attempt; a frozen snapshot is the separately labeled currently observed attempt.
artifacts=[]
for f in sorted(out.iterdir()):
 if not f.is_file() or f.name=='checks.json': continue
 data=f.read_bytes(); rel=str(f.relative_to(root))
 artifacts.append({'path':rel,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'producer':'sage_singular_runtime packaging correction' if f.name in {initial.name,observed.name,'correct_envelope.py'} else 'sage_singular_runtime original independent axis execution'})
 reads.append(rel)
r['artifacts']=artifacts
r['files_read']=sorted(set(x for x in reads if (root/x).is_file()))
r['packaging_correction']={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Envelope schema and immutable snapshots only; no engine/scientific rerun. Mathematical verdict unchanged.','missing_constructor':'.agent-harness/scripts/new_result.py does not exist in assigned checkout; strict_result_validation.py supplies the schema.','new_result_attempted_read':'missing file, no contents read'}
p.write_text(json.dumps(r,indent=2)+'\n')
print('Corrected result bytes:',p.stat().st_size)
