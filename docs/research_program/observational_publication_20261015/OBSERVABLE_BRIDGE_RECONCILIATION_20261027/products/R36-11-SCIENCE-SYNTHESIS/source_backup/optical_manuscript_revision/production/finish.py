import os,sys,pathlib,json,hashlib,shutil
os.environ['GIT_OPTIONAL_LOCKS']='0';sys.path.insert(0,'/mnt/extdrive/workdir/htt_open_data/r35_p5_reviewed_publication');import publish
R=publish.R;sha=publish.sha;B=pathlib.Path('/mnt/extdrive/workdir/htt_open_data');O=B/'r36_optical_manuscript_publication';publish.O=O;run=publish.run;out=publish.out
P=R/'docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027';D=P/'products/R36-11-SCIENCE-SYNTHESIS';Q=D/'optical_manuscript_candidate';C=Q/'candidate';V=B/'r36_optical_manuscript_fresh_review';mh='53c00f723ea81cb88f2a63656444a0054470c422180a517b8ecf403d5373bcaa';m=json.loads((C/'OVERLAY_MANIFEST.json').read_text());contractrow=next(r for r in m['files'] if r['path'].endswith('/EDITOR_CONTRACT.json'));contract=json.loads((C/contractrow['path']).read_text());plan=contract['publication_plan'];root=R/plan['root'];py=str(R/'.venv/bin/python');canonical=(R/'docs/codex_handoff/pr_status.yaml').read_bytes();mirror=(R/'machine_readable/pr_status.yaml').read_bytes()
assert json.loads((O/'PRODUCTION_RETURN.json').read_text())['status']=='APPLIED_INSTALLED_ASSEMBLED_CHECKED_BUILT_PARITY_NOOP';assert not run('RESUME_INDEX',['git','diff','--cached','--name-only','-z']);assert run('RESUME_HEAD',['git','rev-parse','HEAD']).decode().strip()=='8c9e51c06a770f0e327a794918e9d08c061c3824'
selected=set();mapping=[];omitted=[]
def copy(q,dst):
 assert q.is_file() and not q.is_symlink(),str(q);dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.exists():assert sha(q)==sha(dst),str(dst)
 else:shutil.copy2(q,dst)
 assert sha(q)==sha(dst);selected.add(dst);mapping.append({'original_path':str(q),'repository_path':str(dst.relative_to(R)),'sha256':sha(q),'bytes':q.stat().st_size})
for q in Q.rglob('*'):
 if q.is_file() and not q.is_symlink() and '__pycache__' not in q.parts:selected.add(q)
for row in m['files']:selected.add(R/row['path'])
archive=D/'source_backup/optical_manuscript_revision'
for src,label in [(V,'independent_review'),(B/'r36_optical_manuscript_author','actual_author'),(B/'r36_optical_manuscript_framing','framing')]:
 for q in src.rglob('*'):
  rel=q.relative_to(src)
  if q.is_symlink():omitted.append({'path':str(q),'reason':'fixture/source symlink alias excluded; no traversal or raw source download copied'});continue
  if any(x in {'small_manuscript_fixture','small_fixture','fixture','__pycache__','mplconfig','mpl_config','build','candidate','small_p6_fixture','small_p6_fixture_02'} for x in rel.parts):continue
  if q.is_file():copy(q,archive/label/rel)
for q in list(O.rglob('*')):
 if q.is_file() and q.name not in {'STATUS_BEFORE.stdout','execute.py'}:copy(q,archive/'production'/q.relative_to(O))
def write(q,text):q.parent.mkdir(parents=True,exist_ok=True);q.write_text(text);selected.add(q)
write(archive/'SOURCE_MAP.json',json.dumps(mapping,indent=2)+'\n');write(archive/'OMITTED_INPUTS.json',json.dumps(omitted,indent=2)+'\n')
write(archive/'README.md','''# Reviewed conditional P6 optical manuscript revision

Current paper: R32-05-P6-OPTICAL/repair_01/report/main.pdf and main.tex, 20 pages. The failed predecessor root/report is untouched. The exact 20-path overlay53c00f723ea81cb88f2a63656444a0054470c422180a517b8ecf403d5373bcaa has actual independent PASS_SCOPED_CONDITIONAL. Existing11 qualification, frozen83b/P4, prior d845 three-document revision, original17/42 and separate alternate18/42 are unchanged. This revision grants no new scientific-node completion.

Actual production apply, newly installed cached assembler/check, isolated LaTeX build r36_optical/build, built check, exact reviewed PDF-text parity and zero-change reapply passed. Rebuilt PDF bytes may differ only as permitted by the reviewed CLI's text-equivalence rule. The original35 equation tags/main.tex and old PDF remain recoverable from exact baseline preimages. Source/review/framer/author firstfailures and production evidence are retained with SOURCE_MAP. Fixture trees and symlink aliases are omitted without traversing raw downloads.

Scope is a conditional joint optical methods appendix: full signed tensor response, separate direct-dipole constraint, declared synthetic correlated covariance, finite-response certificate controls and two source figures. Missing empirical joint law, physical finite-distance/selection bounds, common source/congruence/frame transfer, absolute H/history and owner-specific x/Q/F/Pi/G inputs remain explicit. No scientific producer, optimizer, fit, new MC, ODE, raw observation download or STATE write occurred. The reviewed nonblocking manual-equation duplicate PDF destination/navigation limitation is retained without an unreviewed editorial repair.
''')
q=D/'PUBLICATION_STATUS.json';selected.add(archive/'PUBLICATION_STATUS_BEFORE.json');status=json.loads(q.read_text());status['optical_manuscript_publication_revision']={'candidate_identity':'sha256:'+mh,'review':'source_backup/optical_manuscript_revision/independent_review/CONTROLLER_RETURN.json','reader_entry':str((root/plan['reader_entry']).relative_to(R)),'production':'source_backup/optical_manuscript_revision/production/PRODUCTION_RETURN.json','qualification_count_change':0};write(q,json.dumps(status,indent=2)+'\n')
run('MIRRORS_CHECK',[py,'scripts/codex_harness/sync_pr_dag_mirrors.py','--check']);run('DAG_VALIDATE',[py,'scripts/codex_harness/validate_pr_dag.py','docs/codex_handoff/pr_backlog.yaml','--status','docs/codex_handoff/pr_status.yaml']);assert (R/'docs/codex_handoff/pr_status.yaml').read_bytes()==canonical;assert (R/'machine_readable/pr_status.yaml').read_bytes()==mirror
rows=[]
for q in sorted(selected):
 z=q.read_bytes();rows.append({'path':str(q.relative_to(R)),'sha256':sha(q),'bytes':len(z),'git_mode':'100755' if q.stat().st_mode&0o111 else '100644','git_blob_oid':hashlib.sha1(b'blob '+str(len(z)).encode()+b'\0'+z).hexdigest()})
out('SELECTED_PATHS.json',rows);out('PROTECTION_PRE_STAGE.json',publish.protection());assert not run('INDEX_PRE_STAGE',['git','diff','--cached','--name-only','-z']);run('STAGE',['git','add','--pathspec-from-file=-','--pathspec-file-nul'],input=b''.join(r['path'].encode()+b'\0' for r in rows));entries=run('STAGED_ENTRIES',['git','ls-files','--stage','-z','--']+[r['path'] for r in rows]);got={}
for line in entries.split(b'\0'):
 if line:
  meta,path=line.split(b'\t',1);mode,blob,stage=meta.decode().split();assert stage=='0';got[path.decode()]=(mode,blob)
for r in rows:assert got[r['path']]==(r['git_mode'],r['git_blob_oid'])
changed=run('STAGED_PATHS',['git','diff','--cached','--name-only','-z']);actual=set(changed.decode().strip('\0').split('\0'));assert actual<={r['path'] for r in rows};out('UNCHANGED_SELECTED_PATHS.json',sorted({r['path'] for r in rows}-actual));out('PROTECTION_PRE_COMMIT.json',publish.protection());run('COMMIT',['git','commit','-m','PR-R36-11: Integrate reviewed joint optical methods into P6 manuscript']);commit=run('HEAD_AFTER',['git','rev-parse','HEAD']).decode().strip();tree=run('TREE',['git','rev-parse','HEAD^{tree}']).decode().strip();changed=run('COMMITTED_PATHS',['git','diff-tree','--no-commit-id','--name-only','-r','-z','HEAD']);assert set(changed.decode().strip('\0').split('\0'))==actual
run('PUSH',['git','push','origin','HEAD:refs/heads/research/htt-adaptive-methods-20261023']);remote=run('REMOTE',['git','ls-remote','--exit-code','origin','refs/heads/research/htt-adaptive-methods-20261023']).decode().strip();assert remote.split()[0]==commit
url='https://github.com/cosmosapjw-quantum/htt_base/blob/'+commit+'/'+plan['root']+'/'
seconds=sum(json.loads(q.read_text()).get('elapsed_seconds',0) for q in O.glob('*.json') if isinstance(json.loads(q.read_text()),dict));out('PUBLICATION_RETURN.json',{'status':'PUBLISHED_R1_VERIFIED','commit':commit,'tree':tree,'remote_oid':remote.split()[0],'selected_paths':len(rows),'committed_paths':len(actual),'committed_bytes':sum(r['bytes'] for r in rows if r['path'] in actual),'selected_manifest_sha256':sha(O/'SELECTED_PATHS.json'),'provider_receipt_sha256':sha(O/'PUSH.json'),'remote_receipt_sha256':sha(O/'REMOTE.json'),'PDF_url':url+plan['pdf'],'TeX_url':url+plan['main'],'PDF_pages':20,'production_return_sha256':sha(O/'PRODUCTION_RETURN.json'),'canonical_and_mirrors_unchanged':True,'old_qualifications_and_original42':'unchanged','protected':publish.protection(),'observed_command_seconds':seconds,'unmeasured_intervals':'UNKNOWN','STATE_writes':0,'producer_runs':0,'requested':'gpt-6.1-sol/medium','observed':'UNKNOWN'});print((O/'PUBLICATION_RETURN.json').read_text())
