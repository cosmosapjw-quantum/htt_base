"""Execute only this bounded upstream unit and preserve raw command outcomes."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import platform
import subprocess
import sys
import numpy
import matplotlib

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
steps=[]
commands=[[sys.executable,str(HERE/'upstream_selection.py')],
          [sys.executable,'-m','unittest','discover','-s',str(HERE),'-p','test_upstream_selection.py','-v'],
          [sys.executable,str(HERE/'plot_upstream_selection.py')]]
if sys.argv[1:] == ['--plot-only']:
    # Caption-only changes reuse already successful source and test executions.
    steps=json.loads((HERE/'RUN_RECEIPT.json').read_text())['steps']
    commands=commands[-1:]
for command in commands:
    begin=datetime.now(timezone.utc).isoformat()
    result=subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
    steps.append({'command':command,'cwd':str(ROOT),'started_utc':begin,'exit_status':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
    print(result.stdout,end='');print(result.stderr,end='',file=sys.stderr)
    if result.returncode:break
receipt={'task':'H02 upstream actual selection/contributors','base_head':'9616f5341e215fcea21b7977a128162842a4f3a4',
         'requested_runtime':'gpt-6.1-sol/high','observed_runtime':'UNKNOWN',
         'python':platform.python_version(),'numpy':numpy.__version__,'matplotlib':matplotlib.__version__,'steps':steps,
         'source_code_sha256':{name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in ('acquire_upstream.py','upstream_selection.py','test_upstream_selection.py','plot_upstream_selection.py','run_validation.py')},
         'H02_acceptance':'HOLD: source selection/shared calibration-velocity law and source null pipeline missing'}
(HERE/'RUN_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
raise SystemExit(steps[-1]['exit_status'])
