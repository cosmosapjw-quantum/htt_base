from importlib.machinery import SourceFileLoader
from pathlib import Path
import hashlib,json,subprocess,sys
m=SourceFileLoader('runner','/tmp/pr450-runner.py').load_module(); r=Path(m.ROOT)/'worktree'; stage=sys.argv[1]
expected={
'scripts/extract_theory_survivor_surface.py':'9d5bee9b1926e35216b95ab1384dc28f7a25592f',
 'tests/contracts/test_theory_survivor_triage.py':'26ab6150de552bd7d083cdb0118b1d251bcf17fd',
 'tests/contracts/test_theory_survivor_seed_schema.py':'dd31c5e9f5d2e8348a6c8405de04a5b8685594fa',
 'docs/research_program/theory_promotion/closeout/REGISTERED_SURVIVOR_SEED.json':'76d0a2396c2cb7e0b514264fe6322a2316adfa69',
 '.github/workflows/theory-survivor-triage.yml':'c0a165c1d150c522b946e47c253f41ab53090b09',
 'docs/codex_handoff/pr408_final/WU-001.yaml':'45ee133372bcc7256887c6300c37b2cc6ef8c32d',
 'AGENTS.md':'24e666c89e38159790b659b4b4e75502e50b5f2c'}
def git(label,*args):
 rec=m.run(stage+'-'+label,['git',*args],cwd=r)
 assert rec['exit_code']==0,rec
 return (m.OUT/(stage+'-'+label+'.stdout')).read_bytes()
head=git('head','rev-parse','HEAD').decode().strip(); tree=git('tree','rev-parse','HEAD^{tree}').decode().strip()
assert head=='ba84912bea165896ec8f0c0e5793b47d1736f512'; assert tree=='55065b3b9ff075f8a58a5bda5f3d11d85ba21ab5'
status=git('status','status','--porcelain=v1','--untracked-files=all').decode(); assert not status
for name,sha in [('pr408','2dce66ca019609e6d07625bc6382bc347fbf5a8c'),('wu001','bdad91a204c424030cd6d0e562232b6965a42900')]: git('ancestry-'+name,'merge-base','--is-ancestor',sha,head)
entries={}
extra=['pytest.ini','scripts/codex_harness/sync_pr_dag_mirrors.py']
for p in [r/'tests/conftest.py',r/'tests/contracts/conftest.py']:
 if p.is_file(): extra.append(str(p.relative_to(r)))
for i,(name,expected_blob) in enumerate(list(expected.items())+[(x,None) for x in extra]):
 raw=(r/name).read_bytes(); blob=git('blob-'+str(i),'rev-parse',head+':'+name).decode().strip()
 actual=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
 assert actual==blob
 if expected_blob: assert blob==expected_blob
 entries[name]={'git_blob':blob,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'expected_blob':expected_blob}
matrix_path='docs/research_program/theory_promotion/THEORY_PROMOTION_MATRIX_V1.json'
blob=git('matrix-blob','rev-parse','463f0999949bf8534c60ad7973b7342705c2e3d6:'+matrix_path).decode().strip(); assert blob=='56af1713ef8c4718598e10012819d5ab62c6e37a'
raw=git('matrix','show','463f0999949bf8534c60ad7973b7342705c2e3d6:'+matrix_path)
a=json.loads(raw)
result={'stage':stage,'head':head,'tree':tree,'status_porcelain':status,'ancestry_pr408':True,'ancestry_wu001':True,'files':entries,'matrix':{'commit':'463f0999949bf8534c60ad7973b7342705c2e3d6','path':matrix_path,'git_blob':blob,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'counts':a['counts'],'candidate_coverage_proof':a['candidate_coverage_proof'],'rows_measured':len(a['rows']),'scoped_measured':len(a['supplemental_scoped_candidates'])}}
(m.OUT/('source-'+stage+'.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
