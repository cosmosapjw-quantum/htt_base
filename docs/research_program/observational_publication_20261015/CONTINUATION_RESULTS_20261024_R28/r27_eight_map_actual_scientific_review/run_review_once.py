"""One-shot child supervision; outer tool/caller wall is authoritative for debit.

This supervisor's internal clock excludes its own startup and settlement tail.
Neither is claimed measured here. The controller must settle MAX(authentic
whole-tool wall, authentic caller monotonic wall) once across eight accounts.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent


def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def memavail():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'): return int(line.split()[1])*1024
    raise RuntimeError('MEMAVAILABLE_MISSING')


def group(pid):
    found=[];rss=0
    for p in Path('/proc').iterdir():
        if not p.name.isdigit(): continue
        try:
            data=(p/'stat').read_text();fields=data[data.rfind(')')+2:].split()
            if int(fields[2])==pid:
                found.append(int(p.name));rss+=int(fields[21])*os.sysconf('SC_PAGE_SIZE')
        except (FileNotFoundError,ProcessLookupError,PermissionError): pass
    return found,rss


def main(args):
    begin=time.monotonic();pre=memavail()
    if pre<10*1024**3: raise RuntimeError('PRELAUNCH_MEMORY')
    binding=json.loads(Path(args.binding).read_text());ack=json.loads(Path(args.ack).read_text())
    if ack.get('action')!='GO' or ack.get('binding_sha256')!=digest(args.binding):
        raise RuntimeError('NO_GENUINE_BOUND_REVIEW_ACK')
    for key in ('independent_check.py','run_review_once.py'):
        if binding['review_source_sha256'][key]!=digest(HERE/key): raise RuntimeError('REVIEW_SOURCE_DRIFT:'+key)
    marker=HERE/'REVIEW_STARTED.json'
    with marker.open('x') as f:
        json.dump({'supervisor_pid':os.getpid(),'monotonic_internal_begin':begin,
                   'ack_sha256':digest(args.ack),'binding_sha256':digest(args.binding)},f)
    env=dict(os.environ)
    for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS','BLIS_NUM_THREADS'):
        env[key]='1'
    env['PYTHONDONTWRITEBYTECODE']='1'
    command=[sys.executable,'-B',str(HERE/'independent_check.py'),'--binding',args.binding]
    peak=0;minimum=pre;samples=0;stop=None
    with (HERE/'checker.stdout').open('xb') as stdout,(HERE/'checker.stderr').open('xb') as stderr:
        spawn_start=time.monotonic()
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,env=env,start_new_session=True)
        while True:
            reaped,status,ru=os.wait4(child.pid,os.WNOHANG)
            if reaped: break
            members,rss=group(child.pid);peak=max(peak,rss);minimum=min(minimum,memavail());samples+=1
            if time.monotonic()-begin>=7.0: stop='CHILD_DEADLINE_7_SECONDS_RESERVED_CLEANUP_3_SECONDS'
            if rss>2*1024**3: stop='OWNED_GROUP_RSS_CAP'
            if minimum<4*1024**3: stop='RUNTIME_MEMAVAILABLE_FLOOR'
            if stop:
                os.killpg(child.pid,signal.SIGKILL)
                reaped,status,ru=os.wait4(child.pid,0);break
            time.sleep(.025)
        child.returncode=os.waitstatus_to_exitcode(status)
        remaining,_=group(child.pid)
        if remaining:
            os.killpg(child.pid,signal.SIGKILL)
            stop=stop or 'UNEXPECTED_DESCENDANTS'
            for _ in range(10):
                remaining,_=group(child.pid)
                if not remaining: break
                time.sleep(.01)
    before_receipt=time.monotonic()
    persisted=[]
    for name in ('REVIEW_STARTED.json','NUMERICAL_CHECKS.json','NUMERICAL_FIRST_FAILURE.json','checker.stdout','checker.stderr'):
        path=HERE/name
        if path.exists():
            with path.open('rb') as f: os.fsync(f.fileno())
            persisted.append(name)
    after_owned_output_fsync=time.monotonic()
    receipt={'status':'COMPLETED' if child.returncode==0 and not stop and not remaining else 'HOLD',
             'command':command,'supervisor_pid':os.getpid(),'child_pid':child.pid,'process_group_id':child.pid,
             'child_exit_code':child.returncode,'reaped':bool(reaped),'remaining_group_members':remaining,
             'stop_reason':stop,'prelaunch_mem_available_bytes':pre,'minimum_mem_available_bytes':minimum,
             'sample_count':samples,'sampled_group_peak_rss_bytes':peak,'wait4_child_ru_maxrss_bytes':ru.ru_maxrss*1024,
             'monotonic_internal_begin':begin,'monotonic_before_Popen':spawn_start,'monotonic_before_receipt':before_receipt,
             'observed_internal_through_reap_stream_close_seconds':before_receipt-begin,
             'monotonic_after_owned_output_fsync':after_owned_output_fsync,
             'fsynced_before_receipt':persisted,
             'receipt_and_directory_fsync':'Performed after receipt close and before terminal monotonic observation',
             'whole_wall_debit':'PENDING_ROOT_AUTHENTIC_TOOL_AND_CALLER_CLOCK_MAX',
             'startup_and_receipt_tail':'NOT_MEASURED_BY_INTERNAL_CLOCK; included only by outer whole-tool/caller clock',
             'binding_sha256':digest(args.binding),'ack_sha256':digest(args.ack),
             'requested_runtime':{'model':'gpt-6-astra','reasoning_effort':'xhigh'},'observed_runtime':'UNKNOWN',
             'rss_evidence_limit':'sampled RSS and wait4 high-water; no continuous all-instants certificate'}
    (HERE/'EXECUTION_RECEIPT.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    with (HERE/'EXECUTION_RECEIPT.json').open('rb') as f: os.fsync(f.fileno())
    directory_fd=os.open(HERE,os.O_RDONLY|os.O_DIRECTORY)
    try: os.fsync(directory_fd)
    finally: os.close(directory_fd)
    end=time.monotonic()
    print(json.dumps({'status':receipt['status'],'child_exit_code':child.returncode,
                     'observed_internal_through_all_output_and_receipt_fsync_seconds':end-begin,
                     'monotonic_after_receipt_and_directory_fsync':end,
                     'internal_whole_10s_limit_met':end-begin<=10.0,
                     'whole_wall_debit':'OUTER_CLOCK_PENDING'}),flush=True)
    return 0 if receipt['status']=='COMPLETED' else 1


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--binding',required=True);p.add_argument('--ack',required=True)
    raise SystemExit(main(p.parse_args()))
