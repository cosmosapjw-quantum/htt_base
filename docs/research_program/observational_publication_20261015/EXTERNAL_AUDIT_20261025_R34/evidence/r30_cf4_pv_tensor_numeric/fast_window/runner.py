"""Single-use R32 supervisor. Import is inert; active cap is controller sealed."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
PYTHON = Path('/home/cosmosapjw/Dropbox/bianchi/htt_base/.venv/bin/python')
MAX_WALL = 190.0
CHILD_RESERVE = 5.0
RSS_CAP = 6 * 1024**3
MIN_AVAILABLE = 10 * 1024**3


def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):
            h.update(b)
    return h.hexdigest()


def available_bytes():
    with open('/proc/meminfo') as f:
        for line in f:
            if line.startswith('MemAvailable:'):
                return int(line.split()[1])*1024
    raise RuntimeError('MemAvailable missing')


def group_rss(pgid):
    total=0
    for d in Path('/proc').iterdir():
        if not d.name.isdigit():
            continue
        try:
            stat=(d/'stat').read_text()
            tail=stat[stat.rfind(')')+2:].split()
            if int(tail[2]) != pgid:
                continue
            pages=int((d/'statm').read_text().split()[1])
            total += pages*os.sysconf('SC_PAGE_SIZE')
        except (OSError,ValueError,IndexError):
            continue
    return total


def self_rss():
    return int(Path('/proc/self/statm').read_text().split()[1])*os.sysconf('SC_PAGE_SIZE')


def fsync_path(path):
    with open(path,'rb') as f:
        os.fsync(f.fileno())


def write_receipt(path,receipt):
    tmp=path.with_name(path.name+'.tmp')
    with open(tmp,'w') as f:
        json.dump(receipt,f,indent=2,allow_nan=False)
        f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def terminate_group(child):
    if child is None:
        return
    try:os.killpg(child.pid,signal.SIGTERM)
    except ProcessLookupError:return
    try:child.wait(timeout=1.0)
    except subprocess.TimeoutExpired:
        try:os.killpg(child.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        child.wait(timeout=1.0)
    if group_rss(child.pid):
        try:os.killpg(child.pid,signal.SIGKILL)
        except ProcessLookupError:pass


def main():
    began=time.monotonic();utc_start=time.time()
    p=argparse.ArgumentParser()
    p.add_argument('--input',required=True)
    args=p.parse_args()
    child=None; out=None;err=None
    packet_path=Path(args.input).resolve()
    wall=MAX_WALL
    receipt={'status':'STARTED','utc_start_unix':utc_start,'maximum_wall_cap_seconds':MAX_WALL,
             'rss_cap_bytes':RSS_CAP,'command':[sys.executable,str(Path(__file__).resolve()),'--input',str(packet_path)],
             'requested_runtime':'gpt-6-sol/high','observed_runtime':'UNKNOWN',
             'original_H02_H04':'HOLD','scientific_admission':False}
    output=ROOT/'unbound_output'
    failure=None
    try:
        packet=json.loads(packet_path.read_text())
        wall=float(packet['whole_command_cap_seconds'])
        if not (0 < wall <= MAX_WALL and wall == packet['active_producer_cap_seconds']):
            raise ValueError('sealed active cap must satisfy 0 < cap <= 190')
        receipt['active_wall_cap_seconds']=wall
        output=Path(packet['output_dir']).resolve()
        if not output.is_relative_to(ROOT) or output == ROOT:
            raise ValueError('output must be a child of owned directory')
        output.mkdir(parents=True,exist_ok=True)
        if any(output.iterdir()):
            receipt['rejected_output_dir']=str(output)
            output=ROOT/f'preflight_refusal_{os.getpid()}_{int(utc_start)}'
            output.mkdir()
            raise ValueError('one-use output directory is not empty; preserve the earlier run')
        if packet.get('controller_go') is not True or packet.get('no_overlap_allocation_confirmed') is not True:
            raise ValueError('controller GO or nonoverlap ACK absent')
        if packet.get('task_id') != 'R30-CF4-BAND-PV-FULL-TENSOR-COVARIANCE' or \
           packet.get('original_input_identity') != 'sha256:5da5fe9adeee84d6615cf9127a91ff5bccff6172e43716680ae0792ef480c5d3':
            raise ValueError('original task/input identity mismatch')
        if sha256(packet['method_contract_path']) != packet['method_contract_sha256'] or \
           packet['method_contract_sha256'] != '8765ad540341080dbb6da3ec02a0cc9179447df45448b7a12245954c879b4706':
            raise ValueError('R32 frozen method contract mismatch')
        if sha256(packet['method_result_path']) != packet['method_result_sha256'] or \
           packet['method_result_sha256'] != '066bb51d1b30364a788b1070b5c3d61ed97880436aa8a524d9c69a576b862b25':
            raise ValueError('R32 research decision mismatch')
        if sha256(packet['derived_execution_lineage_path']) != packet['derived_execution_lineage_sha256']:
            raise ValueError('derived executable lineage mismatch')
        if sha256(packet['controller_packet_path']) != packet['controller_packet_sha256']:
            raise ValueError('controller packet SHA mismatch')
        controller_packet=json.loads(Path(packet['controller_packet_path']).read_text())
        if controller_packet.get('packet_id') != packet['packet_id'] or \
           controller_packet.get('task_id') != packet['task_id']:
            raise ValueError('controller packet content mismatch')
        if sha256(packet['root_go_path']) != packet['root_go_sha256']:
            raise ValueError('root GO record mismatch')
        root_go=json.loads(Path(packet['root_go_path']).read_text())
        if root_go.get('controller_go') is not True or \
           root_go.get('packet_id') != packet['packet_id'] or \
           root_go.get('task_id') != packet['task_id']:
            raise ValueError('root GO content mismatch')
        if packet.get('parent_task_id') != 'R26-CF4-FINAL-GROUP-CALIBRATION-RESPONSE':
            raise ValueError('parent allocation identity mismatch')
        if packet.get('rss_cap_bytes') != RSS_CAP:
            raise ValueError('frozen resource cap mismatch')
        if packet.get('account_head_refreshed') is not True:
            raise ValueError('same-account refresh absent')
        if sha256(packet['account_head_path']) != packet['account_head_sha256']:
            raise ValueError('same-account head SHA mismatch')
        for name in ('runner.py','driver.py','science.py','fast_science.py','independent_check.py'):
            if sha256(ROOT/name) != packet['source_sha256'][name]:
                raise ValueError(f'bound source mismatch: {name}')
        dependency=json.loads((ROOT/'DEPENDENCY.json').read_text())
        if sha256(ROOT/'DEPENDENCY.json') != packet['dependency_manifest_sha256']:
            raise ValueError('dependency manifest SHA mismatch')
        if sha256(ROOT/'_deps/finufft-2.5.0.dist-info/RECORD') != dependency['installed_record_sha256']:
            raise ValueError('installed FINUFFT distribution RECORD mismatch')
        if sha256(ROOT/'_deps/finufft/libfinufft.so') != dependency['native_library_sha256']:
            raise ValueError('installed FINUFFT native library mismatch')
    except KeyError as exc:
        failure=f'INVALID_PACKET_MISSING_{exc}'
    except Exception as exc:
        failure=f'{type(exc).__name__}: {exc}'
    # The packet SHA is carried in a distinct controller-created sidecar.
    if failure is None:
        try:
            sidecar=packet_path.with_suffix(packet_path.suffix+'.sha256')
            expected=sidecar.read_text().split()[0]
            if sha256(packet_path) != expected:
                raise ValueError('packet sidecar SHA mismatch')
            receipt['input_sha256']=expected
            receipt['source_sha256']=packet['source_sha256']
            receipt['method_contract_sha256']=packet['method_contract_sha256']
            receipt['method_result_sha256']=packet['method_result_sha256']
            receipt['derived_execution_lineage_sha256']=packet['derived_execution_lineage_sha256']
            receipt['controller_packet_sha256']=packet['controller_packet_sha256']
            receipt['root_go_sha256']=packet['root_go_sha256']
            receipt['dependency_manifest_sha256']=packet['dependency_manifest_sha256']
            receipt['account_head_sha256']=packet['account_head_sha256']
            receipt['account_used_seconds_before']=packet['account_used_seconds_before']
            if packet['account_used_seconds_before']+wall+60 > 600:
                raise ValueError('same-account cap lacks active producer plus independent 60 seconds')
            headroom=available_bytes()
            receipt['MemAvailable_before_bytes']=headroom
            if headroom < MIN_AVAILABLE:
                raise ValueError(f'RESOURCE_HOLD MemAvailable={headroom}')
            if sys.executable != str(PYTHON.resolve()) and Path(sys.executable).resolve() != PYTHON.resolve():
                raise ValueError('wrong Python interpreter')
            env=os.environ.copy()
            for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
                env[key]='1'
            env['R32_CHILD_DEADLINE_MONOTONIC']=str(began+wall-CHILD_RESERVE)
            out=open(output/'stdout.log','wb');err=open(output/'stderr.log','wb')
            cmd=[str(PYTHON),str(ROOT/'driver.py'),'--input',str(packet_path)]
            receipt['child_command']=cmd
            child=subprocess.Popen(cmd,cwd=str(ROOT),env=env,stdout=out,stderr=err,start_new_session=True)
            receipt['child_pid']=child.pid
            peak=0
            while child.poll() is None:
                peak=max(peak,group_rss(child.pid)+self_rss())
                if peak > RSS_CAP:
                    failure=f'RESOURCE_HOLD process_tree_RSS={peak}'
                    break
                if time.monotonic() > began+wall-CHILD_RESERVE:
                    failure='BUDGET_CONVERGENCE_HOLD supervisor_deadline'
                    break
                time.sleep(.1)
            terminate_group(child)
            receipt['process_tree_peak_rss_bytes']=peak
            receipt['child_exit_code']=child.returncode
            if failure is None and child.returncode != 0:
                failure=f'CHILD_EXIT_{child.returncode}'
            out.flush();err.flush();out.close();err.close();out=err=None
            fsync_path(output/'stdout.log');fsync_path(output/'stderr.log')
            receipt['stdout_sha256']=sha256(output/'stdout.log')
            receipt['stderr_sha256']=sha256(output/'stderr.log')
            # FINUFFT can report a warning while returning a finite array.
            # Keep both raw logs, and fail closed on any warning/clamped eps.
            for log in ('stdout.log','stderr.log'):
                diagnostic=(output/log).read_text(errors='replace').lower()
                if any(token in diagnostic for token in ('warning', 'clamp', 'requested tolerance not')):
                    failure=f'NUMERICAL_METHOD_ACCURACY_HOLD library_warning_in_{log}'
                    receipt['library_warning_log']=log
            result=output/'RESULT.json'
            if result.exists():
                receipt['result_sha256']=sha256(result)
                payload=json.loads(result.read_text())
                receipt['result_status']=payload.get('status')
                if payload.get('status') != 'CONDITIONAL_NUMERICAL_PASS_PENDING_INDEPENDENT_REVIEW' and failure is None:
                    failure='CHILD_RESULT_HOLD'
            elif failure is None:
                failure='MISSING_CHILD_RESULT'
        except Exception as exc:
            failure=f'{type(exc).__name__}: {exc}'
    terminate_group(child)
    for f in (out,err):
        if f is not None:
            f.flush();f.close()
    receipt['elapsed_before_receipt_fsync_seconds']=time.monotonic()-began
    receipt['utc_end_unix']=time.time()
    receipt['status']='HOLD' if failure else 'NUMERICAL_COMMAND_COMPLETE_PENDING_REVIEW'
    receipt['first_failure']=failure
    write_receipt(output/'RUN_RECEIPT.json',receipt)
    receipt['elapsed_after_first_receipt_fsync_seconds']=time.monotonic()-began
    receipt['conservative_charge_seconds']=receipt['elapsed_after_first_receipt_fsync_seconds']+1.0
    receipt['whole_command_external_timing']='CONTROLLER_OBSERVATION_REQUIRED_INCLUDES_PYTHON_STARTUP_AND_FINAL_FSYNC'
    if receipt['conservative_charge_seconds'] > wall:
        failure='BUDGET_CONVERGENCE_HOLD conservative whole-command cap'
        receipt['status']='HOLD';receipt['first_failure']=failure
    write_receipt(output/'RUN_RECEIPT.json',receipt)
    if failure:
        raise SystemExit(failure)


if __name__=='__main__':
    main()
