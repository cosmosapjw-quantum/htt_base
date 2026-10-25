#!/usr/bin/env python3
import time
START=time.monotonic()
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import sys

ROOT=Path(__file__).resolve().parent
BASE=Path('/mnt/extdrive/workdir/htt_open_data')
DISPATCH=BASE/'r30_spectral_dispatch'
PACKET='f03a06d84c471fd3d03fc2435cafdd81ba21697c1b30259d1fa8ba8a0e0ad41c'
CANDIDATE='sha256:b4c20f3595fc1148ff387df3b012ce7fd87dae4098be16a0d24dd914d183291f'
TASK='R30-CMB-NOMINAL-BANDPASS-MOMENT-IDENTIFIABILITY'
INPUT='sha256:cfe7be664ca43841e1197653dc4391b9c64c239cca54eebce9a06def80d916be'
CHILD=None
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def insist(test,msg):
    if not test: raise RuntimeError(msg)
def durable(path,value):
    with path.open('x') as f:
        json.dump(value,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
def alarm(sig,frame):
    if CHILD is not None and CHILD.poll() is None:
        os.killpg(CHILD.pid,signal.SIGKILL)
    raise TimeoutError('supervisor whole-enclosure alarm')
signal.signal(signal.SIGALRM,alarm)
signal.setitimer(signal.ITIMER_REAL,max(.001,78-(time.monotonic()-START)))
record={'packet_id':PACKET,'task_id':TASK,'input_identity':INPUT,'candidate_identity':CANDIDATE,'agent_id':'/root/r30_cmb_fresh_actual_result_review','status':'STARTED','science_started':False,'whole_cap_seconds':80,'first_conservative_debit_seconds':10,'cumulative_checker_hard_cap_seconds':90,'clock':'time.monotonic','requested_runtime':{'model':'gpt-6-astra','effort':'xhigh'},'observed_runtime':'UNKNOWN'}
rc=1
try:
    insist(not (ROOT/'RAW_RECEIPT.json').exists() and not (ROOT/'CHECK_RESULT.json').exists(),'one-use destination exists')
    for path,expected in [
        (BASE/'r30_cmb_spectral_response_framing/SPECTRAL_ONLY_CONTRACT.md','fb137b19b2ec901604691f5d4aa62f05a29e5cbe86404c3c748bf8c8c40386df'),
        (BASE/'r30_spectral_guard_repair_framing/REPAIR_CONTRACT.md','d43c4e62d7bf643e895f5eae8cfd7d9f82ee2842a61047ac23846e7a91216bb7'),
        (DISPATCH/'INPUT.json','cfe7be664ca43841e1197653dc4391b9c64c239cca54eebce9a06def80d916be'),
        (DISPATCH/'ROOT_ACCOUNT_HEAD_AFTER_REPAIRED_PRODUCER.json','a16b43284fe4a5c240092145d10f0fa802b00a6511680c35b64d1b73f560471a')]:
        insist(digest(path)==expected,'immutable binding '+str(path))
    packet=json.loads((DISPATCH/'ACTUAL_NEXT_REVIEW_PACKET.json').read_text())
    ack=json.loads((DISPATCH/'ACTUAL_ACKNOWLEDGED_REVIEW_PACKET.json').read_text())
    go=json.loads((DISPATCH/'ROOT_INDEPENDENT_REVIEW_RESUME_GO.json').read_text())
    for item in (packet,ack,go):
        insist(item['packet_id']==PACKET and item['task_id']==TASK and item['input_identity']==INPUT and item['candidate_identity']==CANDIDATE,'fresh packet/GO identity')
    insist(ack['launch_performed'] is True and ack['agent_id']==record['agent_id'],'actual ACK identity')
    insist(go['status']=='ROOT_GO_BOUNDED_SAME_REVIEW_CHECKER_REPAIR','GO status')
    insist(go['agent_id']==record['agent_id'] and go['checker_whole_hard_cap_seconds']==80,'GO reviewer/cap')
    insist(go['source_sha256']==digest(ROOT/'independent_check.py') and go['supervisor_sha256']==digest(Path(__file__)),'GO checker/supervisor source binding')
    insist(go['first_conservative_debit_seconds']==10 and go['cumulative_checker_hard_cap_seconds']==90,'GO cumulative checker cap')
    head=json.loads((DISPATCH/'ROOT_ACCOUNT_HEAD_AFTER_REPAIRED_PRODUCER.json').read_text())
    accounts=head['cumulative_charged_seconds']
    insist(all(accounts[k]+180/7<=900 for k in ('30','44','70','100','143','217','353')),'same-bank reserves')
    mem={line.split(':')[0]:int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines()}
    disk=shutil.disk_usage(ROOT).free
    insist(mem['MemAvailable']>=4*1024**2 and disk>=2*1024**3,'resource preflight')
    env=os.environ.copy()
    threads={k:'1' for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}
    env.update(threads)
    command=[sys.executable,str(ROOT/'independent_check.py')]
    record.update({'command':command,'source_sha256':digest(ROOT/'independent_check.py'),'supervisor_sha256':digest(Path(__file__)),'packet_file_sha256':digest(DISPATCH/'ACTUAL_NEXT_REVIEW_PACKET.json'),'go_sha256':digest(DISPATCH/'ROOT_INDEPENDENT_REVIEW_RESUME_GO.json'),'account_head_sha256':digest(DISPATCH/'ROOT_ACCOUNT_HEAD_AFTER_REPAIRED_PRODUCER.json'),'MemAvailable_KiB':mem['MemAvailable'],'disk_free_bytes':disk,'thread_environment':threads,'memory_enforcement':'Supervisor RLIMIT_AS 64 MiB plus sole checker RLIMIT_AS 960 MiB; aggregate virtual ceilings 1 GiB. Checker starts no processes. Single-thread numerical libraries.','child_deadline_seconds':75})
    def limit_child():
        resource.setrlimit(resource.RLIMIT_AS,(960*1024**2,960*1024**2))
        resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    with (ROOT/'CHECK.stdout').open('xb') as out,(ROOT/'CHECK.stderr').open('xb') as err:
        CHILD=subprocess.Popen(command,stdout=out,stderr=err,env=env,start_new_session=True,preexec_fn=limit_child)
        record['science_started']=True;record['child_pid']=CHILD.pid
        resource.setrlimit(resource.RLIMIT_AS,(64*1024**2,64*1024**2))
        try:
            rc=CHILD.wait(timeout=max(.001,75-(time.monotonic()-START)))
            record['timed_out']=False
        except subprocess.TimeoutExpired:
            os.killpg(CHILD.pid,signal.SIGKILL)
            CHILD.wait(timeout=max(.001,78-(time.monotonic()-START)))
            rc=124;record['timed_out']=True
        out.flush();os.fsync(out.fileno());err.flush();os.fsync(err.fileno())
    record['exit_code']=rc
    record['peak_child_RSS_KiB']=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    record['peak_supervisor_RSS_KiB']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    record['stdout_sha256']=digest(ROOT/'CHECK.stdout');record['stderr_sha256']=digest(ROOT/'CHECK.stderr')
    if (ROOT/'CHECK_RESULT.json').exists():
        record['check_result_sha256']=digest(ROOT/'CHECK_RESULT.json')
        status=json.loads((ROOT/'CHECK_RESULT.json').read_text())['status']
    else: status='CHECK_RESULT_MISSING'
    record['status']='CHECK_COMPLETE' if rc==0 and status=='INDEPENDENT_NUMERICAL_CHECK_PASS' else 'CHECK_FAILED_OR_INCOMPLETE'
except BaseException as exc:
    record['status']='FIRST_EXECUTION_FAILURE';record['failure']={'type':type(exc).__name__,'message':str(exc)}
    if CHILD is not None and CHILD.poll() is None:
        os.killpg(CHILD.pid,signal.SIGKILL);CHILD.wait(timeout=max(.001,79-(time.monotonic()-START)))
finally:
    record['monotonic_before_receipt_seconds']=time.monotonic()-START
    durable(ROOT/'RAW_RECEIPT.json',record)
    fd=os.open(ROOT,os.O_DIRECTORY);os.fsync(fd);os.close(fd)
    tail={'monotonic_through_receipt_directory_fsync_seconds':time.monotonic()-START,'whole_cap_seconds':80,'status':record['status'],'raw_receipt_sha256':digest(ROOT/'RAW_RECEIPT.json')}
    tail['within_cap']=tail['monotonic_through_receipt_directory_fsync_seconds']<=80
    durable(ROOT/'SUPERVISOR_RETURN.json',tail)
    fd=os.open(ROOT,os.O_DIRECTORY);os.fsync(fd);os.close(fd)
    elapsed=time.monotonic()-START
    print(json.dumps({'status':record['status'],'actual_full_monotonic_seconds':elapsed,'cap_seconds':80,'within_cap':elapsed<=80,'raw_receipt_sha256':digest(ROOT/'RAW_RECEIPT.json'),'supervisor_return_sha256':digest(ROOT/'SUPERVISOR_RETURN.json')}),flush=True)
    signal.setitimer(signal.ITIMER_REAL,0)
sys.exit(rc)
