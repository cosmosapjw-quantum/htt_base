from pathlib import Path
from importlib.machinery import SourceFileLoader
import json,sys
m=SourceFileLoader('runner','/tmp/pr450-runner.py').load_module(); r=Path(m.ROOT)/'worktree'; o=m.OUT
py='/mnt/sn850x2t/htt_base_e2e/venvs/htt_base-py312-20260829/bin/python'
env={'PYTHONPYCACHEPREFIX':str(Path(m.ROOT)/'pycache'),'PYTEST_ADDOPTS':'-o cache_dir='+str(Path(m.ROOT)/'pytest-cache')}
tests=['tests/contracts/test_theory_survivor_triage.py','tests/contracts/test_theory_survivor_seed_schema.py']
steps=[('dag-check',[py,'-B','scripts/codex_harness/sync_pr_dag_mirrors.py','--check']),('compile',[py,'-m','py_compile','scripts/extract_theory_survivor_surface.py']),('collect',[py,'-B','-m','pytest','--collect-only','-q',*tests]),('tests',[py,'-B','-m','pytest','-q',*tests,'--junitxml='+str(o/'pr450-tests.xml')])]
for name,cmd in steps:
 rec=m.run('baseline-'+name,cmd,cwd=r,validation=True,timeout=300,env=env)
 print((o/('baseline-'+name+'.stdout')).read_text()); print((o/('baseline-'+name+'.stderr')).read_text())
 if rec['exit_code']!=0: sys.exit(1)
for suffix in ('a','b'):
 output=o/('surface-'+suffix+'.json'); assert not output.exists()
 rec=m.run('baseline-replay-'+suffix,[py,'-B','scripts/extract_theory_survivor_surface.py','--repo',str(r),'--matrix-ref','463f0999949bf8534c60ad7973b7342705c2e3d6','--matrix-path','docs/research_program/theory_promotion/THEORY_PROMOTION_MATRIX_V1.json','--expect-git-blob','56af1713ef8c4718598e10012819d5ab62c6e37a','--output',str(output)],cwd=r,validation=True,timeout=120,env=env)
 print((o/('baseline-replay-'+suffix+'.stdout')).read_text()); print((o/('baseline-replay-'+suffix+'.stderr')).read_text())
 if rec['exit_code']!=0: sys.exit(2)
m.run('baseline-cmp',['cmp',str(o/'surface-a.json'),str(o/'surface-b.json')],cwd=r,validation=True,env=env)
