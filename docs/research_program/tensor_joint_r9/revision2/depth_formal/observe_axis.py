#!/usr/bin/env python3
"""Capture exact submitted engine execution for the existing CAS gate, without status rewriting."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[5]
ART=ROOT/'.agent-harness/runs/R9-THEORY-20260914/artifacts'
BASE=Path(__file__).resolve().parent
axis,prop=sys.argv[1:]
if prop not in ('D1','D3','D2','D4'):
    raise ValueError(prop)
commands={
 'wolfram_xact':['WolframKernel','-noprompt','-script',str(ART/'depth_wolfram_xact/verify_depth_repaired.wl'),prop],
 'sympy':['/usr/bin/python3',str(ART/'depth_sympy/depth_sympy_runner.py'),prop],
 'sage_singular':['/usr/local/bin/sage','-python',str(ART/'depth_sage_singular/depth_sage_singular_runner_repaired.py'),prop],
 'lean':['/usr/bin/bash',str(ART/'depth_lean/run_depth_lean.sh'),prop],
}
cmd=commands[axis]
out=BASE/'host_execution'/prop/axis
out.mkdir(parents=True,exist_ok=False)
start=time.monotonic();timed_out=False
proc=subprocess.Popen(cmd,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True,
                      env={**os.environ,'OPENBLAS_NUM_THREADS':'1','PYTHONDONTWRITEBYTECODE':'1'})
try:
 stdout,stderr=proc.communicate(timeout=180)
except subprocess.TimeoutExpired:
 timed_out=True
 os.killpg(proc.pid,signal.SIGTERM)
 try:stdout,stderr=proc.communicate(timeout=5)
 except subprocess.TimeoutExpired:
  os.killpg(proc.pid,signal.SIGKILL);stdout,stderr=proc.communicate()
(out/'stdout.txt').write_text(stdout);(out/'stderr.txt').write_text(stderr)
sources=[Path(arg) for arg in cmd if Path(arg).is_file()]
if axis=='lean':sources.append(ART/'depth_lean/DepthCore.lean')
meta={'axis':axis,'proposition':prop,'argv':cmd,'cwd':str(ROOT),'exit_code':proc.returncode,
      'timed_out':timed_out,'elapsed_seconds':time.monotonic()-start,
      'source_sha256':{str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
(out/'execution.json').write_text(json.dumps(meta,indent=2)+'\n')
sys.stdout.write(stdout);sys.stderr.write(stderr)
sys.exit(124 if timed_out else proc.returncode)
