import os,sys,json,pathlib,hashlib,shutil,time,yaml,subprocess
os.environ['GIT_OPTIONAL_LOCKS']='0';os.environ['PYTHONDONTWRITEBYTECODE']='1'
sys.path.insert(0,'/mnt/extdrive/workdir/htt_open_data/r35_p5_reviewed_publication');import publish
R=publish.R;sha=publish.sha;B=pathlib.Path('/mnt/extdrive/workdir/htt_open_data');O=B/'r36_synthesis_publication';publish.O=O;run=publish.run;out=publish.out
P=R/'docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027';D=P/'products/R36-11-SCIENCE-SYNTHESIS';C=D/'repair_01';V=B/'r36_synthesis_repair_fresh_review';A=R/'docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-06-P4-DESIGN'
assert run('PUBLICATION_HEAD_BEFORE',['git','rev-parse','HEAD']).decode().strip()=='2a7c81355f5830384d1a27976fc1c08d1be2a329';assert not run('PUBLICATION_INDEX_BEFORE',['git','diff','--cached','--name-only','-z']);out('PUBLICATION_PROTECTION_BEFORE.json',publish.protection())
selected=set();mapping=[];omitted=[];frozen=[]
def ref(q):return {'path':str(q),'sha256':sha(q),'bytes':q.stat().st_size}
def copy(q,to):
 assert q.is_file() and not q.is_symlink() and not to.exists(),str(to);to.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(q,to);assert sha(q)==sha(to);selected.add(to);mapping.append({'original_path':str(q),'repository_path':str(to.relative_to(R)),**{k:v for k,v in ref(q).items() if k!='path'}})
def write(q,text):q.parent.mkdir(parents=True,exist_ok=True);q.write_text(text);selected.add(q)
for q in D.rglob('*'):
 if q.is_file() and '__pycache__' not in q.parts:selected.add(q);frozen.append(ref(q))
manifest=json.loads((C/'ARTIFACT_MANIFEST.json').read_text());assert sha(C/'ARTIFACT_MANIFEST.json')=='83b167a9388071a1a82500716d338473bd8ac5c9abb3c978974a914a37066519'
for name,v in manifest['artifacts'].items():
 q=C/name;assert sha(q)==v['sha256'],name
F=V/'formal_binding_01/CONTROLLER_RETURN.json';assert sha(F)=='c32e8b71932e957f0af625ec86965d732da633694d307b6ff8138d3a21dbd0b1';formal=json.loads(F.read_text());assert formal['acceptance_met'] and formal['qualified_products']==['observable_bridge_manuscript_update']
assert sha(V/'CLAIM_LOCATOR_ERRATUM.json')=='e8931e5f37fc8bfe28a6a8c4a1319a21383560175cbf1ea7d9cec0fb45e467fc'
# Exact top-level evidence only: fixture repository copies are redundant and omitted.
for src,dst in [(B/'r36_science_synthesis_actual',D/'source_backup/base_actual'),(B/'r36_science_synthesis_repair_actual',D/'source_backup/repair_actual'),(V,D/'independent_review/repair_review')]:
 for q in sorted(src.iterdir()):
  if q.is_file() and q.name!='git_status_before.txt':copy(q,dst/q.name)
  elif q.is_dir() and q.name!='formal_binding_01':omitted.append({'path':str(q),'reason':'redundant disposable workflow fixture/cache; frozen candidate and original baseline are published separately'})
 for q in (src/'formal_binding_01').rglob('*') if (src/'formal_binding_01').exists() else []:
  if q.is_file():copy(q,dst/'formal_binding_01'/q.relative_to(src/'formal_binding_01'))
for n in ['NEXT_028.json','ACK_028_GO.json']:copy(B/'r36_controller'/n,D/'source_backup/actual_controller'/n)
# Historical production baseline and actual apply/consumer/check/build/idempotence evidence.
for q in (O/'preproduction_preimages').rglob('*'):
 if q.is_file():copy(q,D/'source_backup/production_preimages'/q.relative_to(O/'preproduction_preimages'))
for q in sorted(O.iterdir()):
 if q.is_file() and q.name not in {'STATUS_BEFORE.stdout','package_publish.py'} and not q.name.startswith('PUBLICATION_'):copy(q,D/'source_backup/production_application'/q.name)
plan=json.loads((C/'APPLICATION_PLAN.json').read_text())
for name,v in plan['files'].items():assert sha(A/name)==v['final_sha256'];selected.add(A/name)
selected.add(A/'report/main.pdf')
copy(V/'CLAIM_LOCATOR_ERRATUM.json',A/'source_backup/r36_11/CLAIM_LOCATOR_ERRATUM.json')
copy(A/'PUBLICATION_STATUS.json',A/'source_backup/r36_11/PUBLICATION_STATUS_BEFORE.json')
readme='''# Current reviewed observable-bridge manuscript update

The applied paper is [main.pdf](report/main.pdf), 24 pages, with [main.tex](report/main.tex), bibliography, five figures and the cached-statistic consumer [assemble.py](report/r36_11/assemble.py). The repaired R36-11 candidate and all historical baseline/source evidence remain under the R36-11 product. Its actual independent and formal review qualifies only observable_bridge_manuscript_update: a conditional C0 observable/response/design integration. Source-dependent distance/history, optical-centroid to matter transport, empirical spatial covariance, selection and frame laws remain required inputs. No native solver, ODE, family identification, original17/42 or analytic18/42 promotion follows.

Production application was followed by a new applied consumer, check, 24-page LaTeX build, final check and a second apply with zero changes. PDF text matches the sealed reviewed candidate. The original ten numerical JSON artifacts and three original figures are retained; no old science producer was rerun. Historical original paper manifests describe the earlier frozen release; current applied source identity is the reviewed R36-11 APPLICATION_PLAN plus production application receipt, rather than a rewrite of those old manifests.

## Consumed locator correction

The exact [CLAIM_LOCATOR_ERRATUM.json](source_backup/r36_11/CLAIM_LOCATOR_ERRATUM.json) corrects historical C09–C11 claim-map locators without changing frozen maps. C09 (complete carrier) and C10 (physical comparator x) occur in section 8, Physical interpretation, at manuscript lines449 and451 in the reviewed source. C11 administrative acceptance is outside the physics manuscript: the authoritative false physical/native admission flags are in repair_01/RESULT.json and applied report/r36_11/SOURCE_CONTRACT.json hard_scope. The related additional physical input requirements are section8 line453. Section8 is not an administrative acceptance claim.
'''
write(A/'README_R36_11_UPDATE.md',readme)
status=json.loads((A/'PUBLICATION_STATUS.json').read_text());status['current_manuscript_update']={'status':'FORMALLY_QUALIFIED_SCOPED_CONDITIONAL_PRODUCT','candidate_identity':formal['candidate_identity'],'qualified_products':formal['qualified_products'],'formal_packet':formal['packet_id'],'reader_entry':'README_R36_11_UPDATE.md','pdf':'report/main.pdf','tex':'report/main.tex','original42_effect':'none'};write(A/'PUBLICATION_STATUS.json',json.dumps(status,indent=2)+'\n')
write(D/'PUBLICATION_STATUS.json',json.dumps({'status':'FORMALLY_QUALIFIED_SCOPED_CONDITIONAL_PRODUCT','candidate_identity':formal['candidate_identity'],'acceptance_met':True,'qualified_products':formal['qualified_products'],'formal_packet':formal['packet_id'],'formal_return_sha256':sha(F),'current_manuscript_reader':str((A/'README_R36_11_UPDATE.md').relative_to(R)),'old_scientific_producer_runs':0,'STATE_writes':0,'original42_effect':'none'},indent=2)+'\n')
write(D/'source_backup/README.md','''# Reviewed manuscript update and production application

The current 24-page paper/PDF/TeX and cached-statistic consumer are in the existing R32-06-P4-DESIGN report directory; its README_R36_11_UPDATE.md consumes the precise historical claim-locator correction. Base failed candidate, repaired frozen candidate, baseline preimages, raw first failures, independent negative fixtures/checkers, formal review and actual production apply/consumer/check/build/idempotence receipts are preserved here. Frozen proposal-stage metadata remains historical. Qualification is conditional C0 observable/response/design integration only; physical/native/original42 admission remains unchanged. SOURCE_MAP.json resolves historical absolute cache/source paths to exact repository copies. Duplicate disposable fixture trees and unrelated dirty-status dumps are omitted; no raw observations or full STATE export is included.
''')
write(D/'source_backup/SOURCE_MAP.json',json.dumps(mapping,indent=2)+'\n');write(D/'source_backup/OMITTED_INPUTS.json',json.dumps(omitted,indent=2)+'\n');write(A/'source_backup/r36_11/SOURCE_MAP.json',json.dumps([m for m in mapping if m['repository_path'].startswith(str(A.relative_to(R)))],indent=2)+'\n')
canonical=R/'docs/codex_handoff/pr_status.yaml';before=canonical.read_text();(O/'PUBLICATION_STATUS_CANONICAL_BEFORE.yaml').write_text(before);text=before;node='PR-R36-11-SCIENCE-SYNTHESIS';assert text.count('- '+node+'\n')==1;text=text.replace('- '+node+'\n','').replace('completed:\n','completed:\n- '+node+'\n',1);text=text.replace('execution_resolutions:\n','execution_resolutions:\n  '+node+':\n    resolution: COMPLETED_SUCCESS\n    receipt: '+str((D/'independent_review/repair_review/formal_binding_01/CONTROLLER_RETURN.json').relative_to(R))+'\n    scientific_status_effect: scoped_conditional_product_only_original42_unchanged\n    success_dependency_satisfied: true\n',1);write(canonical,text)
a=yaml.safe_load(before);b=yaml.safe_load(text);b['completed'].remove(node);del b['execution_resolutions'][node];b['pending']=a['pending'];assert a==b
q=P/'PR_DELTA.md';write(q,q.read_text()+'''\n## PR-R36-11 reviewed production manuscript update (2026-10-27)\n\nRecord only observable_bridge_manuscript_update as completed from actual formal SCOPED_PASS candidate83b167a9388071a1a82500716d338473bd8ac5c9abb3c978974a914a37066519. Apply the reviewed overlay into the existing P4 paper; actual new applied consumer/check/build/check succeeded, PDF24pages/fivefigures and text equal sealed candidate, reapply zero changes. Preserve failed base/repaired manifests, baseline preimages, first failures and exact independent/formal/source/production receipts. Outer current README/map consumes CLAIM_LOCATOR_ERRATUM C09/C10 section8 and C11 administrative locus outside physics manuscript, without frozen map edits. Original numerical outputs retained, no old producer or STATE write; conditional C0 scope only, original17/42 and analytic18/42 unchanged. All other statuses/protected edits unchanged.\n''')
run('PUBLICATION_MIRRORS_SYNC',[str(R/'.venv/bin/python'),'scripts/codex_harness/sync_pr_dag_mirrors.py','--write']);run('PUBLICATION_MIRRORS_CHECK',[str(R/'.venv/bin/python'),'scripts/codex_harness/sync_pr_dag_mirrors.py','--check']);run('PUBLICATION_DAG_VALIDATE',[str(R/'.venv/bin/python'),'scripts/codex_harness/validate_pr_dag.py','docs/codex_handoff/pr_backlog.yaml','--status','docs/codex_handoff/pr_status.yaml']);selected.add(R/'machine_readable/pr_status.yaml')
for v in frozen:assert sha(pathlib.Path(v['path']))==v['sha256']
rows=[]
for q in sorted(selected):
 z=q.read_bytes();rows.append({'path':str(q.relative_to(R)),'bytes':len(z),'sha256':sha(q),'git_mode':'100755' if q.stat().st_mode&0o111 else '100644','git_blob_oid':hashlib.sha1(b'blob '+str(len(z)).encode()+b'\0'+z).hexdigest()})
out('PUBLICATION_SELECTED_PATHS.json',rows);out('PUBLICATION_PROTECTION_PRE_STAGE.json',publish.protection());run('PUBLICATION_STAGE',['git','add','--pathspec-from-file=-','--pathspec-file-nul'],input=b''.join(r['path'].encode()+b'\0' for r in rows));entries=run('PUBLICATION_STAGED_ENTRIES',['git','ls-files','--stage','-z','--']+[r['path'] for r in rows]);got={}
for line in entries.split(b'\0'):
 if line:
  meta,path=line.split(b'\t',1);mode,blob,stage=meta.decode().split();assert stage=='0';got[path.decode()]=(mode,blob)
for r in rows:assert got[r['path']]==(r['git_mode'],r['git_blob_oid']),r['path']
changed=run('PUBLICATION_STAGED_PATHS',['git','diff','--cached','--name-only','-z']);assert set(changed.decode().strip('\0').split('\0'))=={r['path'] for r in rows}
out('PUBLICATION_PROTECTION_PRE_COMMIT.json',publish.protection());run('PUBLICATION_COMMIT',['git','commit','-m','PR-R36-11: Publish reviewed proper-motion manuscript update']);commit=run('PUBLICATION_HEAD_AFTER',['git','rev-parse','HEAD']).decode().strip();tree=run('PUBLICATION_TREE',['git','rev-parse','HEAD^{tree}']).decode().strip();run('PUBLICATION_PUSH',['git','push','origin','HEAD:refs/heads/research/htt-adaptive-methods-20261023']);remote=run('PUBLICATION_REMOTE',['git','ls-remote','--exit-code','origin','refs/heads/research/htt-adaptive-methods-20261023']).decode().strip();assert remote.split()[0]==commit
url='https://github.com/cosmosapjw-quantum/htt_base/blob/'+commit+'/'+str(A.relative_to(R))+'/'
out('PUBLICATION_RETURN.json',{'status':'PUBLISHED_R1_VERIFIED','commit':commit,'tree':tree,'remote_oid':remote.split()[0],'paths':len(rows),'bytes':sum(r['bytes'] for r in rows),'selected_manifest_sha256':sha(O/'PUBLICATION_SELECTED_PATHS.json'),'provider_receipt_sha256':sha(O/'PUBLICATION_PUSH.json'),'remote_receipt_sha256':sha(O/'PUBLICATION_REMOTE.json'),'pdf_url':url+'report/main.pdf','tex_url':url+'report/main.tex','production_application':json.loads((O/'PRODUCTION_APPLICATION_RETURN.json').read_text()),'protected':publish.protection(),'STATE_writes':0,'unmeasured_intervals':'UNKNOWN','requested':'gpt-6.1-sol/medium','observed':'UNKNOWN'});print((O/'PUBLICATION_RETURN.json').read_text())
