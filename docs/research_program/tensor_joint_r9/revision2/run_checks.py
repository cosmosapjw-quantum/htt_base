#!/usr/bin/env python3
"""Replay revision-2 reference science and structural gates with command receipts."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
OUT=HERE/'evidence'
OUT.mkdir(exist_ok=True)
commands=[
    [sys.executable,str(HERE/'validate_revision2.py')],
    [sys.executable,str(HERE.parent/'validate_dag.py')],
    [sys.executable,'scripts/codex_harness/validate_pr_dag.py','docs/codex_handoff/pr_backlog.yaml'],
]
receipts=[]
for i,command in enumerate(commands):
    started=time.monotonic()
    result=subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
    (OUT/f'check_{i}.stdout').write_text(result.stdout)
    (OUT/f'check_{i}.stderr').write_text(result.stderr)
    receipts.append({'command':command,'cwd':str(ROOT),'exit_code':result.returncode,
                     'elapsed_seconds':time.monotonic()-started,'stdout':f'check_{i}.stdout','stderr':f'check_{i}.stderr'})
    print(f'check {i}: exit={result.returncode}')
    if result.returncode:
        print(result.stderr[-2000:])
        break
inputs=[HERE/'validate_revision2.py',HERE.parent/'validate_dag.py',HERE.parent/'campaign_dag.json',HERE.parent/'REVISION_SPEC.md']
receipt={'scope':'reference/graph checks only; no scientific capability promotion',
         'status':'PASS' if len(receipts)==len(commands) and all(r['exit_code']==0 for r in receipts) else 'FAIL',
         'inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
         'commands':receipts}
(OUT/'execution_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
if receipt['status']!='PASS':raise SystemExit(1)
