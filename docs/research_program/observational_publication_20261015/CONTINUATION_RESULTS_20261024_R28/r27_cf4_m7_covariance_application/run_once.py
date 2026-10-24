"""One acknowledged scientific child, with whole-lifetime wait4/RSS/accounting receipt."""
import argparse
import datetime as dt
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
CONSUMER=ROOT/'consume.py'
RUNNER=ROOT/'run_once.py'
INPUT_SHA='f04c2253bd33daafab55963793135b70a2aabbd35f2eeb356ad4a625a32b65db'
CONTRACT_SHA='54006747ecd39827ed9022031a9f03aaf0c1f90474f014dcf22e37a5b49c13e6'
PACKET_ID='4a4830fdd9b239f6edb5334b2a213a135305c9e726ce39de3cc730ba6746b2f6'
TASK_ID='R27-CF4-M7-ACTUAL-COVARIANCE-APPLICATION'
RSS_CAP=2147483648

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def candidate():
    hashes={'consume.py':sha(CONSUMER),'run_once.py':sha(RUNNER)}
    return hashes,hashlib.sha256(json.dumps(hashes,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def utc():return dt.datetime.now(dt.timezone.utc).isoformat()

def rss(pid):
    try:
        for line in Path(f'/proc/{pid}/status').read_text().splitlines():
            if line.startswith('VmRSS:'):return int(line.split()[1])*1024
    except (FileNotFoundError,ProcessLookupError): pass
    return 0

def save(path,obj):
    with open(path,'w') as f:
        json.dump(obj,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True);p.add_argument('--ack',default=str(ROOT/'ACK.json'));args=p.parse_args()
    inp=Path(args.input).resolve();out=Path(args.output).resolve();ackpath=Path(args.ack).resolve()
    hashes,cid=candidate()
    if sha(inp)!=INPUT_SHA:raise SystemExit('INPUT_SHA_MISMATCH')
    if out.exists():raise SystemExit('OUTPUT_ALREADY_EXISTS')
    if not ackpath.is_file():raise SystemExit('ACK_REQUIRED')
    ack=json.loads(ackpath.read_text())
    needed={'go':True,'task_id':TASK_ID,'packet_id':PACKET_ID,'input_sha256':INPUT_SHA,'contract_sha256':CONTRACT_SHA,'candidate_sha256':cid}
    if any(ack.get(k)!=v for k,v in needed.items()):raise SystemExit('ACK_BINDING_MISMATCH')
    if ack.get('consumer_subcap_seconds')!=50 or not (0<float(ack.get('cf4_remaining_seconds',0))<=600):raise SystemExit('ACK_BUDGET_MISMATCH')
    cap=min(50.,float(ack['cf4_remaining_seconds']),float(ack.get('application_remaining_seconds',0)))
    if cap<=0:raise SystemExit('NO_REMAINING_BUDGET')
    if any(os.environ.get(k)!='1' for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')):raise SystemExit('BLAS_THREAD_BINDING_MISSING')
    out.mkdir(parents=True)
    stdout=out/'RAW_STDOUT.txt';stderr=out/'RAW_STDERR.txt'
    cmd=[sys.executable,str(CONSUMER),'--input',str(inp),'--output',str(out/'products')]
    start=time.monotonic();start_utc=utc();pid=None;peak=0;reaped=False;exit_code=None;termination=None;ru=None
    try:
        with open(stdout,'wb') as so,open(stderr,'wb') as se:
            proc=subprocess.Popen(cmd,stdout=so,stderr=se,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},start_new_session=True)
            pid=proc.pid
            while True:
                peak=max(peak,rss(pid))
                waited,status,usage=os.wait4(pid,os.WNOHANG)
                if waited==pid:
                    reaped=True;ru=usage
                    exit_code=os.waitstatus_to_exitcode(status)
                    break
                elapsed=time.monotonic()-start
                if elapsed>=cap or peak>RSS_CAP:
                    termination='TIME_CAP' if elapsed>=cap else 'RSS_CAP'
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
                        reaped=(waited==pid);ru=usage;exit_code=os.waitstatus_to_exitcode(status)
                    break
                time.sleep(.02)
            so.flush();os.fsync(so.fileno());se.flush();os.fsync(se.fileno())
    except BaseException as exc:
        termination=termination or f'RUNNER_EXCEPTION:{type(exc).__name__}:{exc}'
        if pid is not None and not reaped:
            try:os.killpg(pid,signal.SIGKILL)
            except ProcessLookupError:pass
            try:
                waited,status,usage=os.wait4(pid,0)
                reaped=(waited==pid);ru=usage;exit_code=os.waitstatus_to_exitcode(status)
            except ChildProcessError:pass
    children_rss=ru.ru_maxrss*1024 if ru is not None else None
    peak=max(peak,children_rss or 0)
    products=out/'products';product_hashes={p.name:sha(p) for p in products.iterdir() if p.is_file()} if products.is_dir() else {}
    raw={'task_id':TASK_ID,'packet_id':PACKET_ID,'input_sha256':INPUT_SHA,'contract_sha256':CONTRACT_SHA,'candidate_sha256':cid,'source_hashes':hashes,'ack_sha256':sha(ackpath),'command':cmd,'environment_threads':{k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')},'start_utc':start_utc,'end_utc':utc(),'pid':pid,'reaped':reaped,'exit_code':exit_code,'termination':termination,'peak_rss_bytes':peak,'rss_cap_bytes':RSS_CAP,'child_ru_maxrss_bytes':children_rss,'consumer_cap_seconds':cap,'product_sha256':product_hashes,'stdout_sha256':sha(stdout),'stderr_sha256':sha(stderr),'observed_runtime':'NOT_INDEPENDENTLY_OBSERVED','scientific_admission':'PENDING_INDEPENDENT_REVIEW'}
    raw['elapsed_seconds_through_products_and_raw_stream_persistence']=time.monotonic()-start
    save(out/'RUN_RECEIPT.json',raw)
    # This final accounting stamp is made after the receipt has been durably flushed.
    end=time.monotonic();end_utc=utc();debit=end-start
    save(out/'ACCOUNTING_END.json',{'start_utc':start_utc,'end_utc':end_utc,'elapsed_seconds_including_receipt_persistence':debit,'conservative_debit_seconds':debit+0.05,'source':'parent monotonic before Popen through wait4, output hashing and receipt fsync','task_id':TASK_ID,'packet_id':PACKET_ID,'consumer_cap_seconds':cap,'within_cap':debit<=cap,'reaped':reaped,'exit_code':exit_code})
    if exit_code!=0 or termination or not reaped or peak>RSS_CAP or debit>cap:raise SystemExit(f'HELD: exit={exit_code} termination={termination} reaped={reaped} peak={peak} elapsed={debit}')
    required={'RESULT.json','MATRIX_CERTIFICATES.json','covariance_profiles.npz','sensitivity.pdf','REPORT.md'}
    if not required.issubset(product_hashes):raise SystemExit('HELD:INCOMPLETE_PRODUCTS')
    print(json.dumps({'status':'EXECUTED_PENDING_REVIEW','elapsed_seconds':debit,'conservative_debit_seconds':debit+0.05,'peak_rss_bytes':peak,'products':product_hashes},sort_keys=True))
if __name__=='__main__':main()
