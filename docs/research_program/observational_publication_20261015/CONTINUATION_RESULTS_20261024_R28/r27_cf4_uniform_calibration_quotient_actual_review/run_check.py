#!/usr/bin/env python3
import time
START=time.monotonic_ns()
import json
import os
from pathlib import Path
import resource
import signal
import sys
HERE=Path(__file__).resolve().parent
PY='/home/cosmosapjw/Dropbox/bianchi/htt_base/.venv/bin/python'
receipt={'task':'R27-CF4-UNIFORM-SUPPORT-CALIBRATION-QUOTIENT','kind':'ONE_INDEPENDENT_NUMERIC_GROUP','limit_seconds':30,'child_deadline_seconds':24,'rss_limit_bytes':2*1024**3,'clock':'time.monotonic_ns; child wait4 lifetime RSS; external time and API wall retained separately'}
env=dict(os.environ)
for key in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'): env[key]='1'
env['PYTHONDONTWRITEBYTECODE']='1'
out=os.open(HERE/'check.stdout',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
err=os.open(HERE/'check.stderr',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
pid=os.fork()
if pid==0:
    os.dup2(out,1);os.dup2(err,2)
    resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
    os.execve(PY,[PY,'-B',str(HERE/'check.py')],env)
stop=None
while True:
    ended,status,usage=os.wait4(pid,os.WNOHANG)
    if ended: break
    if (time.monotonic_ns()-START)/1e9>24 and stop is None:
        stop='CHILD_DEADLINE_EXCEEDED';os.kill(pid,signal.SIGKILL)
    time.sleep(.02)
for fd in (out,err): os.fsync(fd);os.close(fd)
code=os.waitstatus_to_exitcode(status)
receipt.update({'child_returncode':code,'stop_reason':stop,'wait4_lifetime_maxrss_kib':usage.ru_maxrss,'observed_monotonic_through_child_reap_and_logs_fsync_seconds':(time.monotonic_ns()-START)/1e9})
with (HERE/'WHOLE_COMMAND_RECEIPT.json').open('x') as f:
    json.dump(receipt,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
fd=os.open(HERE,os.O_RDONLY);os.fsync(fd);os.close(fd)
final=(time.monotonic_ns()-START)/1e9
print(json.dumps({'status':'CHECK_EXITED_ZERO' if code==0 and stop is None else 'CHECK_FAILURE','whole_monotonic_after_receipt_fsync_seconds':final,'wait4_lifetime_maxrss_kib':usage.ru_maxrss}),flush=True)
sys.exit(0 if code==0 and stop is None and final<=30 else 1)
