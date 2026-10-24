"""GO-bound one-attempt outer host; timer starts before each Python child Popen."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent
ACCOUNTS=('30','44','70','100','143','217','353','SMICA')
THREADS=('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')
RSS_CAP=2*1024**3
MEM_BEFORE=10*1024**3
MEM_FLOOR=4*1024**3
FINAL_TAIL_BOUND=0.5


def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()


def seal(ref):
    p=Path(ref['path'])
    if p.stat().st_size!=ref['bytes'] or sha(p)!=ref['sha256']:
        raise RuntimeError('SEALED_INPUT_DRIFT:'+str(p))
    return p


def write(path,obj):
    with open(path,'x') as f:
        json.dump(obj,f,indent=2,sort_keys=True,allow_nan=False)
        f.write('\n');f.flush();os.fsync(f.fileno())


def durable_files(directory):
    for path in directory.iterdir():
        if path.is_file():
            with open(path,'rb') as f:os.fsync(f.fileno())
    fd=os.open(directory,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)


def mem_available():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):return int(line.split()[1])*1024
    raise RuntimeError('MEMAVAILABLE_UNOBSERVED')


def group_rss(pgid):
    total=0; members=[]
    for path in Path('/proc').iterdir():
        if not path.name.isdigit():continue
        try:
            stat=(path/'stat').read_text(); tail=stat[stat.rfind(')')+2:].split()
            if int(tail[2])!=pgid:continue
            members.append(int(path.name))
            for line in (path/'status').read_text().splitlines():
                if line.startswith('VmRSS:'):
                    total+=int(line.split()[1])*1024;break
        except (FileNotFoundError,ProcessLookupError,PermissionError,ValueError):pass
    return total,members


def stage(stage_name,script,input_path,out,cap):
    if mem_available()<MEM_BEFORE:raise RuntimeError('PRELAUNCH_MEMAVAILABLE_BELOW_10GIB:'+stage_name)
    cmd=[sys.executable,'-B',str(ROOT/script),'--input',str(input_path),'--output',str(out/'products')]
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
    env.update({key:'1' for key in THREADS})
    started=time.monotonic(); start_utc=datetime.now(timezone.utc).isoformat()
    pid=None; reaped=False; ru=None; exit_code=None; stop_reason=None; max_rss=0
    min_mem=2**63-1; samples=0; last_members=[]
    try:
        with open(out/(stage_name+'.stdout'),'xb') as stdout,open(out/(stage_name+'.stderr'),'xb') as stderr:
            proc=subprocess.Popen(cmd,stdout=stdout,stderr=stderr,env=env,start_new_session=True)
            pid=proc.pid
            while True:
                rss,members=group_rss(pid);last_members=members;samples+=1
                max_rss=max(max_rss,rss)
                available=mem_available();min_mem=min(min_mem,available)
                waited,status,usage=os.wait4(pid,os.WNOHANG)
                if waited==pid:
                    reaped=True;ru=usage;exit_code=os.waitstatus_to_exitcode(status);break
                elapsed=time.monotonic()-started
                if elapsed>=cap-2 or max_rss>RSS_CAP or available<MEM_FLOOR:
                    stop_reason='TIME_RESERVE' if elapsed>=cap-2 else ('RSS_CAP' if max_rss>RSS_CAP else 'MEM_FLOOR')
                    try:os.killpg(pid,signal.SIGTERM)
                    except ProcessLookupError:pass
                    deadline=time.monotonic()+1.
                    while time.monotonic()<deadline:
                        waited,status,usage=os.wait4(pid,os.WNOHANG)
                        if waited==pid:
                            reaped=True;ru=usage;exit_code=os.waitstatus_to_exitcode(status);break
                        time.sleep(.02)
                    if not reaped:
                        try:os.killpg(pid,signal.SIGKILL)
                        except ProcessLookupError:pass
                        waited,status,usage=os.wait4(pid,0)
                        reaped=waited==pid;ru=usage;exit_code=os.waitstatus_to_exitcode(status)
                    break
                time.sleep(.02)
            stdout.flush();os.fsync(stdout.fileno());stderr.flush();os.fsync(stderr.fileno())
    except BaseException as exc:
        stop_reason=stop_reason or 'OUTER_EXCEPTION:'+type(exc).__name__+':'+str(exc)
        if pid and not reaped:
            try:os.killpg(pid,signal.SIGKILL)
            except ProcessLookupError:pass
            try:
                waited,status,usage=os.wait4(pid,0)
                reaped=waited==pid;ru=usage;exit_code=os.waitstatus_to_exitcode(status)
            except ChildProcessError:pass
    # The stage is charged through complete owned output checks and its receipt fsync.
    remaining=[]
    if pid:_,remaining=group_rss(pid)
    highwater=(ru.ru_maxrss*1024 if ru else None)
    max_rss=max(max_rss,highwater or 0)
    products=out/'products'
    if products.is_dir():durable_files(products)
    hashes={p.name:sha(p) for p in products.iterdir() if p.is_file()} if products.is_dir() else {}
    record={'stage':stage_name,'command':cmd,'start_utc':start_utc,'end_utc_before_receipt':datetime.now(timezone.utc).isoformat(),
            'pid':pid,'process_group_id':pid,'reaped':reaped,'exit_code':exit_code,'stop_reason':stop_reason,
            'sample_count':samples,'sampled_group_peak_rss_bytes':max_rss,'child_ru_maxrss_bytes':highwater,
            'last_sampled_members':last_members,'remaining_group_members':remaining,
            'minimum_mem_available_bytes':None if min_mem==2**63-1 else min_mem,
            'loaded_threadpool_limit_environment':{key:env[key] for key in THREADS},
            'product_sha256':hashes,'consumer_stdout_sha256':sha(out/(stage_name+'.stdout')) if (out/(stage_name+'.stdout')).exists() else None,
            'consumer_stderr_sha256':sha(out/(stage_name+'.stderr')) if (out/(stage_name+'.stderr')).exists() else None,
            'stage_cap_seconds':cap,'receipt_tail_conservative_seconds':FINAL_TAIL_BOUND,
            'timing_scope':'outer host monotonic before Python Popen through wait4, group inspection, product hashes, stream and receipt fsync; receipt write tail bounded conservatively'}
    record['measured_before_receipt_seconds']=time.monotonic()-started
    record['conservative_debit_seconds']=record['measured_before_receipt_seconds']+FINAL_TAIL_BOUND
    write(out/(stage_name+'.RECEIPT.json'),record)
    observed_after_write=time.monotonic()-started
    # A real post-fsync observation establishes that the labelled tail bound covered this write.
    if observed_after_write>record['conservative_debit_seconds']:
        raise RuntimeError('RECEIPT_TAIL_BOUND_EXCEEDED:'+stage_name)
    if not reaped or exit_code!=0 or stop_reason or remaining or max_rss>RSS_CAP or min_mem<MEM_FLOOR or record['conservative_debit_seconds']>cap:
        raise RuntimeError('STAGE_HOLD:'+stage_name+':'+json.dumps(record,sort_keys=True))
    return record


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--ack',required=True);ap.add_argument('--output',required=True)
    args=ap.parse_args();inp_path=Path(args.input);ack_path=Path(args.ack);out=Path(args.output)
    inp=json.loads(inp_path.read_text());ack=json.loads(ack_path.read_text())
    candidate={key:sha(ROOT/key) for key in ('consume.py','AUTHOR_DECIMAL_ORACLE.py','run_once.py')}
    if candidate!=inp['source_sha256']:raise SystemExit('PREPARED_SOURCE_DRIFT')
    if sha(inp_path)!=ack.get('input_sha256'):
        raise SystemExit('INPUT_OR_ACK_BINDING')
    if ack.get('status')!='GO' or ack.get('task_id')!=inp['task_id'] or not ack.get('packet_id') or not ack.get('launch_performed'):
        raise SystemExit('GENUINE_ACK_GO_REQUIRED')
    if ack.get('source_sha256')!=candidate or ack.get('contract_sha256')!=inp['contract']['sha256']:
        raise SystemExit('ACK_SOURCE_CONTRACT_BINDING')
    if ack.get('latest_head_sha256')!=inp['latest_account_head']['sha256']:
        raise SystemExit('LATEST_HEAD_BINDING')
    if ack.get('consumer_cap_seconds')!=60 or ack.get('checker_cap_seconds')!=10 or ack.get('aggregate_cap_seconds')!=70:
        raise SystemExit('ACK_SUBCAPS')
    for ref in inp['frozen_inputs'].values():seal(ref)
    seal(inp['contract']);head=json.loads(seal(inp['latest_account_head']).read_text())
    base=head['cumulative_charged_seconds']
    if any(900-base[key] < 70/8 for key in ACCOUNTS):raise SystemExit('SAME_ACCOUNT_BALANCE')
    if out.exists():raise SystemExit('OUTPUT_ALREADY_EXISTS_ONE_ATTEMPT_ONLY')
    if mem_available()<MEM_BEFORE:raise SystemExit('PRELAUNCH_MEMAVAILABLE_BELOW_10GIB')
    out.mkdir(parents=True)
    write(out/'STARTED.json',{'task_id':inp['task_id'],'packet_id':ack['packet_id'],'input_sha256':sha(inp_path),
                              'ack_sha256':sha(ack_path),'source_sha256':candidate,
                              'latest_head_sha256':inp['latest_account_head']['sha256'],
                              'same_account_base':base,'start_utc':datetime.now(timezone.utc).isoformat(),
                              'status':'ONE_ATTEMPT_STARTED'})
    records=[]
    try:
        records.append(stage('consumer','consume.py',inp_path,out,60.))
        required={'FULL8_COMPARISON.npz','DESCRIPTIVE_RESULT.json','REPORT.md','signed24.png','heldout_B12.png','cross_terms.png'}
        if not required.issubset(records[-1]['product_sha256']):raise RuntimeError('CONSUMER_OUTPUT_INCOMPLETE')
    except BaseException as exc:
        write(out/'FIRST_FAILURE.json',{'type':type(exc).__name__,'message':str(exc),
                                        'completed_stage_receipts':[r['stage'] for r in records],
                                        'status':'HOLD_FIRST_FAILURE_STOP'})
        raise
    total=records[0]['conservative_debit_seconds']
    if total>60:raise SystemExit('CONSUMER_SUBCAP_EXCEEDED')
    candidate_result={'status':'EXECUTED_PENDING_INDEPENDENT_REVIEW','task_id':inp['task_id'],
                      'packet_id':ack['packet_id'],'input_sha256':sha(inp_path),'ack_sha256':sha(ack_path),
                      'source_sha256':candidate,'base_head_sha256':inp['latest_account_head']['sha256'],
                      'stage_debits_conservative_seconds':{'consumer':total},
                      'consumer_conservative_seconds':total,'shared_debit_each_account_seconds':total/8,
                      'cumulative_charged_seconds':{k:base[k]+total/8 for k in ACCOUNTS},
                      'independent_numeric_checker':'RESERVED_NOT_RUN; fresh reviewer owns the separate 10s stage',
                      'aggregate_new_question_cap_seconds':70,
                      'note':'External whole-command wall observation must be compared with this inner bound; charge MAX once across eight accounts. Startup/final host tail never inferred from internal phase timers.',
                      'observed_runtime':'NOT_INDEPENDENTLY_OBSERVED','scientific_admission':'HOLD'}
    write(out/'CANDIDATE_RESULT.json',candidate_result)
    print(json.dumps({'status':candidate_result['status'],'inner_conservative_seconds':total}),flush=True)


if __name__=='__main__':main()
