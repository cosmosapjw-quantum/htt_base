"""Preserve real bounded subprocess outputs for the D03 reviewer."""
from pathlib import Path
import datetime, hashlib, json, os, subprocess, sys, platform
import numpy, scipy, matplotlib, astropy
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'AGENTS.md').exists())
receipt_path=HERE/'RUN_RECEIPT.json'
commands=[['d03.py'],['-m','unittest','discover','-s',str(HERE),'-p','test_d03.py','-v'],['plot_d03.py']]
if '--plot-only' in sys.argv:commands=[['plot_d03.py']]
if '--tests-only' in sys.argv:commands=[['-m','unittest','discover','-s',str(HERE),'-p','test_d03.py','-v']]
receipt={'task':'D03_PANTHEON_CF4_20261018','cwd':str(ROOT),'base_head':'1528ebd3c4ace48a561b9dcaa6d5f891121a22a5',
         'requested_model':'gpt-6-sol','requested_effort':'high','observed_model':'UNKNOWN','observed_effort':'UNKNOWN',
         'python':sys.executable,'python_version':platform.python_version(),
         'packages':{m.__name__:m.__version__ for m in [numpy,scipy,matplotlib,astropy]},
         'threads':2,'commands':[]}
if receipt_path.exists():receipt['previous_runs']=json.loads(receipt_path.read_text()).get('previous_runs',[])+[json.loads(receipt_path.read_text())]
for spec in commands:
    args=[sys.executable]+([str(HERE/spec[0])] if spec[0].endswith('.py') else spec)
    start=datetime.datetime.now(datetime.timezone.utc).isoformat()
    proc=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,env={**os.environ,'OPENBLAS_NUM_THREADS':'2','OMP_NUM_THREADS':'2'})
    receipt['commands'].append({'argv':args,'started_utc':start,'exit_code':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr})
    receipt['code_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.glob('*.py')}
    receipt_path.write_text(json.dumps(receipt,indent=2)+'\n')
    print(spec[0],proc.returncode,proc.stdout[-1700:],proc.stderr[-1700:],flush=True)
    if proc.returncode:sys.exit(proc.returncode)
