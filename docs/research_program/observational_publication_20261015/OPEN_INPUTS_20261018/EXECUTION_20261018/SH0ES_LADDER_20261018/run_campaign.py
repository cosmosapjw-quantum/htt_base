"""One bounded campaign. Existing RUN_RECEIPT prevents accidental relaunch."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent


def main():
    receipt_path = HERE/'RUN_RECEIPT.json'
    if receipt_path.exists():
        raise SystemExit('existing finite campaign receipt: do not relaunch')
    start = time.monotonic()
    env = dict(os.environ,OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
    records = []
    receipt = {'campaign':'SH0ES_LADDER_20261018','distinct_from':'D07 (97/97 unchanged)',
               'cap_seconds':300,'max_threads':2,'cwd':os.getcwd(),'interpreter':sys.executable,
               'requested_runtime':'gpt-6.1-sol/high','observed_runtime':'UNKNOWN',
               'commands':records,'status':'RUNNING',
               'git_head_at_start':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
               'source_code_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.glob('*.py')}}
    receipt_path.write_text(json.dumps(receipt,indent=2)+'\n')
    try:
        for command in ([sys.executable,str(HERE/'ladder.py')],
                        [sys.executable,'-m','pytest','-q','-o','addopts=',str(HERE/'test_ladder.py')]):
            completed = subprocess.run(command,env=env,capture_output=True,text=True,timeout=max(.1,300-(time.monotonic()-start)))
            record = dict(command=command,exit_code=completed.returncode,stdout=completed.stdout,stderr=completed.stderr)
            records.append(record)
            print(completed.stdout,flush=True)
            print(completed.stderr,file=sys.stderr,flush=True)
            if completed.returncode:
                raise RuntimeError('campaign command failed; no automatic rerun')
        receipt['status'] = 'FINITE_EXECUTION_PASS_REVIEW_PENDING'
    except Exception:
        receipt['status'] = 'HOLD'
        receipt['failure'] = traceback.format_exc()
        with (HERE/'FIRST_FAILURE.txt').open('a') as stream:
            stream.write('\nFinite campaign first failure:\n'+receipt['failure'])
            stream.write(json.dumps(records,indent=2)+'\n')
    finally:
        receipt['elapsed_seconds'] = time.monotonic()-start
        receipt_path.write_text(json.dumps(receipt,indent=2)+'\n')
    return 0 if receipt['status'].startswith('FINITE_EXECUTION_PASS') else 1


if __name__ == '__main__':
    raise SystemExit(main())
