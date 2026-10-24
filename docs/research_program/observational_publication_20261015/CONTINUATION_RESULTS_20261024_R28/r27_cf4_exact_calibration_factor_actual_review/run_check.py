"""One timed independent check; outer receipt includes persistence and reap."""
import time
START=time.monotonic_ns()
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

HERE=Path(__file__).resolve().parent
PY='/home/cosmosapjw/Dropbox/bianchi/htt_base/.venv/bin/python'
CAP=20.
CHILD_DEADLINE=15.
RSS_CAP=2*1024**3

def elapsed():
    return (time.monotonic_ns()-START)/1e9

def rss(pid):
    try:
        text=Path(f'/proc/{pid}/status').read_text()
    except FileNotFoundError:
        return 0
    for line in text.splitlines():
        if line.startswith('VmRSS:'):
            return int(line.split()[1])*1024
    return 0

def main():
    guard=HERE/'STARTED_ONCE'
    with guard.open('x') as handle:
        handle.write(str(START)+'\n');handle.flush();os.fsync(handle.fileno())
    receipt={'status':'STARTED','whole_cap_seconds':CAP,'child_deadline_seconds':CHILD_DEADLINE,
      'rss_cap_bytes':RSS_CAP,'numeric_groups_started':0,'official_interpreter':PY,
      'requested_runtime':{'model':'gpt-6-astra','effort':'xhigh'},'observed_runtime':'UNKNOWN',
      'source_sha256':{name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in ['check.py','run_check.py','REVIEW_INPUT.json']}}
    env=dict(os.environ)
    for key in ['OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:
        env[key]='1'
    env['PYTHONDONTWRITEBYTECODE']='1'
    argv=[PY,'-B',str(HERE/'check.py')]
    receipt['argv']=argv
    with (HERE/'check.stdout').open('x') as out,(HERE/'check.stderr').open('x') as err:
        child=subprocess.Popen(argv,cwd=HERE,env=env,stdout=out,stderr=err,start_new_session=True)
        receipt['numeric_groups_started']=1
        peak=0; reason=None
        while True:
            pid,status,usage=os.wait4(child.pid,os.WNOHANG)
            if pid:
                child.returncode=os.waitstatus_to_exitcode(status)
                break
            peak=max(peak,rss(child.pid)+rss(os.getpid()))
            if peak>RSS_CAP:
                reason='RSS_LIMIT_EXCEEDED'
            if elapsed()>=CHILD_DEADLINE:
                reason=reason or 'CHILD_DEADLINE'
            if reason:
                os.killpg(child.pid,signal.SIGKILL)
                _,status,usage=os.wait4(child.pid,0)
                child.returncode=os.waitstatus_to_exitcode(status)
                break
            time.sleep(.02)
        receipt.update({'status':'CHILD_EXITED_ZERO' if child.returncode==0 and reason is None else 'FIRST_CHECK_FAILURE',
          'returncode':child.returncode,'reason':reason,'polled_combined_peak_rss_bytes':peak,
          'wait4_child_lifetime_maxrss_kib':usage.ru_maxrss,'child_reaped_elapsed_seconds':elapsed()})
        out.flush();err.flush();os.fsync(out.fileno());os.fsync(err.fileno())
    for path in HERE.iterdir():
        if path.is_file():
            with path.open('rb') as handle:os.fsync(handle.fileno())
    fd=os.open(HERE,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)
    receipt['monotonic_through_products_fsync_seconds']=elapsed()
    receipt['charge_rule']='Root takes maximum overlapping whole observations once; conservative padding must be labelled.'
    with (HERE/'WHOLE_COMMAND_RECEIPT.json').open('x') as handle:
        json.dump(receipt,handle,indent=2);handle.write('\n');handle.flush();os.fsync(handle.fileno())
    final=elapsed()
    print(json.dumps({'status':receipt['status'],'outer_monotonic_after_receipt_fsync_seconds':final}),flush=True)
    return 0 if receipt['status']=='CHILD_EXITED_ZERO' and final<=CAP else 1

if __name__=='__main__':
    sys.exit(main())
