from pathlib import Path
import datetime, hashlib, json, os, subprocess, time
RUN=Path(__file__).resolve().parent
REPO=RUN/'worktree'
OUT=RUN/'evidence'
PY='/mnt/sn850x2t/htt_base_e2e/venvs/htt_base-py312-20260829/bin/python'
BASE='bf09ba531b3afde184ded85c7e147839bf572c85'
PREFIX='artifacts/research_reports/pr450_main_local_HTT_PR450_REGISTERED_SOURCE_REPLAY_V1_20260906T234737Z'
FILES=['scripts/extract_theory_survivor_surface.py','tests/contracts/test_theory_survivor_triage.py','tests/contracts/test_theory_survivor_seed_schema.py','docs/research_program/theory_promotion/closeout/REGISTERED_SURVIVOR_SEED.json','.github/workflows/theory-survivor-triage.yml','docs/codex_handoff/pr408_final/WU-001.yaml','AGENTS.md','pytest.ini','scripts/codex_harness/sync_pr_dag_mirrors.py']
ENV=os.environ.copy(); ENV.update(PYTHONPYCACHEPREFIX=str(RUN/'pycache'),PYTEST_ADDOPTS='-o cache_dir='+str(RUN/'pytest-cache'))
def write(name,value):
 (OUT/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def git(*args): return subprocess.check_output(['git',*args],cwd=REPO)
def identity(raw): return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'git_blob':hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()}
def manifest(name):
 value={'head':git('rev-parse','HEAD').decode().strip(),'tree':git('rev-parse','HEAD^{tree}').decode().strip(),'files':{p:identity((REPO/p).read_bytes()) for p in FILES},'status':git('status','--porcelain=v1','--untracked-files=all').decode()}; write(name,value); return value
HISTORICAL=3.254192363936454
def run(name,argv,expected=0,validation=True):
 assert not (OUT/(name+'.json')).exists(), name
 records=[json.loads(p.read_text()) for p in OUT.glob('*.command.json')]
 consumed=sum(r['elapsed_seconds'] for r in records if r['validation_budget'])
 timeout=900-HISTORICAL-consumed if validation else 120
 assert timeout>0
 start=time.monotonic(); started=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with (OUT/(name+'.stdout')).open('wb') as out, (OUT/(name+'.stderr')).open('wb') as err:
  try:
   p=subprocess.run(argv,cwd=REPO,env=ENV,stdout=out,stderr=err,timeout=timeout); rc=p.returncode; timed=False
  except subprocess.TimeoutExpired:
   rc=None; timed=True
 record={'name':name,'argv':list(map(str,argv)),'cwd':str(REPO),'started_at':started,'elapsed_seconds':time.monotonic()-start,'timeout_seconds':timeout,'timed_out':timed,'exit_code':rc,'expected_exit':expected,'validation_budget':validation,'environment_overrides':{k:ENV[k] for k in ('PYTHONPYCACHEPREFIX','PYTEST_ADDOPTS')},'invocation':1}
 write(name+'.command.json',record)
 print(name,rc,round(record['elapsed_seconds'],3),flush=True)
 assert rc==expected and not timed,(name,rc,expected)
 return record
if __name__=='__main__':
 manifest('source-before.json')
 prior=json.loads((REPO/PREFIX/'pr450_result.json').read_text())
 before=json.loads((REPO/PREFIX/'source-before.json').read_text()); after=json.loads((REPO/PREFIX/'source-after.json').read_text())
 assert {k:v for k,v in before.items() if k != "stage"}=={k:v for k,v in after.items() if k != "stage"}
 assert all(identity((REPO/p).read_bytes())['git_blob']==v['git_blob'] for p,v in prior['execution_source_files'].items())
 write('baseline-reuse.json',{'commit':BASE,'prefix':PREFIX,'tests':prior['tests'],'budget':prior['command_budget'],'before_after_identity_equal_excluding_stage_label':True,'read_evidence':{n:identity((REPO/PREFIX/n).read_bytes()) for n in ['RETURN_TO_MAIN.md','pr450_result.json','source-identity-diagnosis.json','baseline-tests.stdout','pr450-tests.xml','source-before.json','source-after.json']}})
 for name,ref in [('ancestry-wu001','2dce66ca019609e6d07625bc6382bc347fbf5a8c'),('ancestry-pr408','bdad91a204c424030cd6d0e562232b6965a42900')]: run(name,['git','merge-base','--is-ancestor',ref,'HEAD'],validation=False)
 run('runtime',[PY,'-B','-c','import sys,pytest,yaml,importlib.util; print(sys.version); print(sys.executable); print(pytest.__version__,pytest.__file__); print(yaml.__version__,yaml.__file__); print(importlib.util.find_spec("scripts.extract_theory_survivor_surface").origin)'],validation=False)
