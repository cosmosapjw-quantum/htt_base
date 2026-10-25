#!/usr/bin/env python3
"""Single-use bounded R30 repair supervisor; records failures without retries."""
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent
DISPATCH=ROOT.parent/'r30_spectral_dispatch'
OUT=ROOT/'attempt_38cdf6b948a41ee9'
PACKET='38cdf6b948a41ee93372fb48be413f7617e0de5bc2b6b3a704b153cc4ef011d3'
BASE='b7adef654c4a44203860dc5206b80b0ebf67457709d16d46db22e2d534d40ca8'
INPUT='sha256:cfe7be664ca43841e1197653dc4391b9c64c239cca54eebce9a06def80d916be'
TASK='R30-CMB-NOMINAL-BANDPASS-MOMENT-IDENTIFIABILITY'
GO_SHA='355fe2f05ea1bcc11af5b4e6945db4c1548b86c6e78407ddaf20a4e7378d034b'
CONTRACT_SHA='d43c4e62d7bf643e895f5eae8cfd7d9f82ee2842a61047ac23846e7a91216bb7'
ACCOUNT_SHA='5ccda7d603762994fcfbed9d8c484895a4b71d333b899379f039cabc9b9859b1'
SOURCE_SHA={'LFI_RIMO_R3.31.fits':'a4794d80b378e00aef1b5e324e2759c3fa791873f2a3edcb53c93678a48dd94b','HFI_RIMO_R3.00.fits':'deb55a5c6f76a8578e86c122f56c3f61998b803818b09c4f3e709897881fe222'}
CAP=174.0

def sha(path):
    dig=hashlib.sha256()
    with open(path,'rb') as f:
        for part in iter(lambda:f.read(1<<20),b''):dig.update(part)
    return dig.hexdigest()

def sync_dir(path):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)

def child_setup():
    os.setsid()
    resource.setrlimit(resource.RLIMIT_AS,(1<<30,1<<30))

def main():
    begin=time.monotonic()
    go_path=DISPATCH/'ROOT_REPAIR_GO.json'
    assert sha(go_path)==GO_SHA
    go=json.loads(go_path.read_text())
    assert go['packet_id']==PACKET and go['input_identity']==INPUT
    assert go['task_id']==TASK and go['agent_id']=='/root/rc_b7adef654c4a4420'
    assert go['status']=='ROOT_GO_BOUNDED_REPAIR' and go['producer_whole_cap_seconds']==174
    assert go['base_packet_id']==BASE and go['base_candidate_identity'] is None
    assert go['repair_plan_identity']=='bed6207a978d4bd747e3addcc21b9f6d3278fd6425d403ad3a8558c6851c818b'
    assert sha(go['base_raw_receipt']['path'])==go['base_raw_receipt']['sha256']=='de3e9bfd950804dfffde883cac54191aea6d7a05b753c28bae142df012b35e1f'
    assert sha(go['repair_contract']['path'])==go['repair_contract']['sha256']==CONTRACT_SHA
    assert sha(go['account_head']['path'])==go['account_head']['sha256']==ACCOUNT_SHA
    assert sha(ROOT/'produce.py.preimage')=='074b7148e6c7ca3d13d693639453795d69d9f142bea5e323ad5fa66780644dc0'
    for name,expected in SOURCE_SHA.items():assert sha(ROOT/'source'/name)==expected
    assert not OUT.exists(),'Fresh attempt directory already exists; no overwrite or retry'
    available_kib=int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))
    free_bytes=shutil.disk_usage(ROOT).free
    assert available_kib>=4*1024**2 and free_bytes>=2*1024**3,(available_kib,free_bytes)
    OUT.mkdir(mode=0o700)
    sync_dir(ROOT)
    env=os.environ.copy()
    env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
    cmd=[str(Path('/home/cosmosapjw/Dropbox/bianchi/htt_base/.venv/bin/python')),str(ROOT/'produce.py'),'--output-dir',str(OUT)]
    info={'packet_id':PACKET,'task_id':TASK,'input_identity':INPUT,'agent_id':'/root/rc_b7adef654c4a4420','base_packet_id':BASE,'base_candidate_identity':None,'base_raw_receipt':go['base_raw_receipt'],'repair_plan_identity':go['repair_plan_identity'],'go_sha256':GO_SHA,'account_head_sha256':ACCOUNT_SHA,'repair_contract_sha256':CONTRACT_SHA,'source_sha256':SOURCE_SHA,'producer_source_sha256':sha(ROOT/'produce.py'),'command':cmd,'environment_threads':{k:env[k] for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')},'memory_limit':'single producer process RLIMIT_AS 1 GiB; producer source launches no child processes','available_memory_prelaunch_KiB':available_kib,'free_disk_prelaunch_bytes':free_bytes,'whole_supervisor_cap_seconds':CAP,'first_producer_conservative_seconds':5.6,'cumulative_producer_cap_seconds':180,'checker_reserved_seconds':90,'started_producer':False,'observed_runtime':'UNKNOWN','requested_runtime':{'model':'gpt-6-sol','effort':'high'}}
    with open(OUT/'PRODUCER.stdout','wb') as stdout,open(OUT/'PRODUCER.stderr','wb') as stderr:
        proc=subprocess.Popen(cmd,stdout=stdout,stderr=stderr,env=env,preexec_fn=child_setup)
        info['started_producer']=True
        info['pid']=proc.pid
        try:
            code=proc.wait(timeout=max(0.1,CAP-9-(time.monotonic()-begin)))
            timed_out=False
        except subprocess.TimeoutExpired:
            timed_out=True
            os.killpg(proc.pid,signal.SIGTERM)
            try:code=proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL)
                code=proc.wait(timeout=2)
        stdout.flush();os.fsync(stdout.fileno())
        stderr.flush();os.fsync(stderr.fileno())
    info['exit_code']=code
    info['timed_out']=timed_out
    info['peak_child_RSS_KiB']=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    info['stdout_sha256']=sha(OUT/'PRODUCER.stdout')
    info['stderr_sha256']=sha(OUT/'PRODUCER.stderr')
    result=OUT/'RESULT.json'
    if code==0 and not timed_out and result.exists():
        info['candidate_identity']='sha256:'+sha(result)
        info['status']='PRODUCER_COMPLETE_PENDING_INDEPENDENT_CHECK'
    else:
        info['candidate_identity']=None
        info['status']='PRODUCER_FAILED_PRESERVE_FIRST_REPAIR_FAILURE'
    info['monotonic_seconds_before_receipt_write']=time.monotonic()-begin
    info['cap_observed_before_receipt_write']=info['monotonic_seconds_before_receipt_write']<=CAP
    receipt=OUT/'RAW_RECEIPT.json'
    with open(receipt,'x') as f:
        json.dump(info,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    sync_dir(OUT)
    end=time.monotonic()-begin
    terminal={'packet_id':PACKET,'task_id':TASK,'input_identity':INPUT,'status':info['status'] if end<=CAP else 'WHOLE_CAP_EXCEEDED','candidate_identity':info['candidate_identity'] if end<=CAP else None,'raw_receipt':str(receipt),'raw_receipt_sha256':sha(receipt),'monotonic_seconds_through_receipt_directory_fsync':end,'cap_seconds':CAP,'exit_code':code,'peak_child_RSS_KiB':info['peak_child_RSS_KiB']}
    with open(OUT/'SUPERVISOR_RETURN.json','x') as f:
        json.dump(terminal,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    sync_dir(OUT)
    print(json.dumps(terminal))
    if terminal['status']!='PRODUCER_COMPLETE_PENDING_INDEPENDENT_CHECK':sys.exit(1)

if __name__=='__main__':main()
