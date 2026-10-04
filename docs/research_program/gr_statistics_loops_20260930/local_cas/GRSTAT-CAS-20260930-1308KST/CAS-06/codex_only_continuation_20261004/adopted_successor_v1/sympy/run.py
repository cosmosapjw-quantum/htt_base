"""Frozen no-argument entrypoint and retained exact SymPy execution receipt."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
S=HERE.parent
COMMON=ROOT/'docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md'
INPUTS=(S/'EXECUTION_CONTRACT.json',S/'ADMITTED_INPUTS.json',COMMON)
EXPECTED=('9936c95ac128126d34688bbd8ece9fb90c92aa7dfeea8fa7b41716ab449e88f3',
          '711de321c374a85b4b0414d5df1f8a62b55368f73c2a3d31e502e209af8793eb',
          '4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897')

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def now():return dt.datetime.now(dt.timezone.utc).isoformat()

def main():
    assert len(sys.argv)==1, 'runner takes no arguments'
    assert Path.cwd()==ROOT, 'frozen cwd mismatch'
    before={str(p.relative_to(ROOT)):sha(p) for p in INPUTS}
    for p,want in zip(INPUTS,EXPECTED):
        assert sha(p)==want, 'frozen input drift: '+str(p)
    source=HERE/'science.py'
    source_hash=sha(source)
    runner_hash=sha(HERE/'run.py')
    attempts=HERE/'attempts'
    attempts.mkdir(exist_ok=True)
    number=1+max([int(p.name.split('_')[1]) for p in attempts.glob('attempt_*') if p.name.split('_')[1].isdigit()] or [0])
    attempt=attempts/f'attempt_{number:03d}'
    attempt.mkdir()
    shutil.copy2(source,attempt/'science.py')
    shutil.copy2(HERE/'run.py',attempt/'run.py')
    command=['/usr/bin/python3.12','-B',str(source.relative_to(ROOT))]
    started=now()
    timed_out=False
    try:
        completed=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=1700,check=False)
        stdout,stderr,exit_code=completed.stdout,completed.stderr,completed.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out=True
        stdout=(exc.stdout or b'').decode(errors='replace') if isinstance(exc.stdout,bytes) else (exc.stdout or '')
        stderr=(exc.stderr or b'').decode(errors='replace') if isinstance(exc.stderr,bytes) else (exc.stderr or '')
        exit_code=None
    ended=now()
    (attempt/'stdout.log').write_text(stdout)
    (attempt/'stderr.log').write_text(stderr)
    after={str(p.relative_to(ROOT)):sha(p) for p in INPUTS}
    source_after=sha(source)
    runner_after=sha(HERE/'run.py')
    payload=None
    parse_error=None
    if exit_code==0:
        try:payload=json.loads(stdout.strip().splitlines()[-1])
        except (ValueError,IndexError) as exc:parse_error=str(exc)
    required={f'CAS-06-C0{i}' for i in range(1,5)}
    shape=(isinstance(payload,dict) and set(payload.get('checks',{}))==required and
           all(type(v) is bool for v in payload['checks'].values()) and
           isinstance(payload.get('domain_assumption_diff'),list) and
           'counterexample' in payload)
    good=(exit_code==0 and shape and before==after and source_hash==source_after
          and runner_hash==runner_after and all(payload['checks'].values()) and not payload['domain_assumption_diff']
          and payload['counterexample'] is None)
    record={'schema_version':1,'axis':'sympy','status':'PASS' if good else 'INCONCLUSIVE',
            'evidence_class':'exact','contract_sha256':EXPECTED[0],
            'completed_at':ended,'started_at':started,
            'commands':[{'argv':['/usr/bin/python3.12','-B',str((HERE/'run.py').relative_to(ROOT))],
                         'cwd':str(ROOT),'exit_code':0 if good else 1},
                        {'argv':command,'cwd':str(ROOT),'exit_code':exit_code,
                         'stdout_path':str((attempt/'stdout.log').relative_to(ROOT)),
                         'stderr_path':str((attempt/'stderr.log').relative_to(ROOT))}],
            'sympy_version':__import__('sympy').__version__,
            'sympy_module':__import__('sympy').__file__,
            'input_hashes_before':before,'input_hashes_after':after,
            'source_sha256_before':source_hash,'source_sha256_after':source_after,
            'runner_sha256_before':runner_hash,'runner_sha256_after':runner_after,
            'attempt':str(attempt.relative_to(ROOT)),
            'payload':payload,'checks':payload['checks'] if shape else {key:False for key in required},
            'domain_assumption_diff':payload['domain_assumption_diff'] if shape else [],
            'counterexample':payload['counterexample'] if shape else None,
            'timed_out':timed_out,'parse_error':parse_error,
            'scope_limit':'finite jets and algebra only; analytic existence and interval/germ claims HOLD'}
    (attempt/'receipt.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
    (HERE/'result.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
    print(json.dumps(payload if payload is not None else {
        'checks':{f'CAS-06-C0{i}':False for i in range(1,5)},
        'domain_assumption_diff':[],'counterexample':None,
        'execution_error':'See '+str((attempt/'stderr.log').relative_to(ROOT))},sort_keys=True))
    return 0 if good else 1

if __name__=='__main__':
    sys.exit(main())
