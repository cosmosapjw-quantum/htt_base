#!/usr/bin/env python3
"""Capture one short-lived Wolfram execution; emit exactly one strict JSON object."""
import hashlib, json, os, subprocess, sys, time
from pathlib import Path
axis = Path(__file__).resolve().parent
repo = axis.parents[4]
contract_path = repo / '.agent-harness/runs/TENSOR-JOINT-R7-20260908/CAS_CONTRACT.json'
contract = json.loads(contract_path.read_text())
checks = {k: False for k in contract['target']['exact_test_obligations']}
expected_contract = '377c7be24bd070c3bd0dd0e39be003de0ac37f66fe205eaa8cb9d283019113a2'
hash_file = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
if hash_file(contract_path) != expected_contract:
    print(json.dumps({'checks': checks, 'domain_assumption_diff': ['contract hash mismatch'], 'counterexample': None})); sys.exit(2)
for pin in contract['identity']['source_input_hashes']:
    if hash_file(repo / pin['path']) != pin['sha256']:
        print(json.dumps({'checks': checks, 'domain_assumption_diff': ['source hash mismatch: '+pin['path']], 'counterexample': None})); sys.exit(2)
argv = ['/usr/bin/wolframscript', '-file', str(axis / 'verify.wl')]
execution_id = time.strftime('%Y%m%dT%H%M%S', time.gmtime())+'-'+str(os.getpid())
started = time.monotonic()
try:
    proc = subprocess.run(argv, cwd=repo, capture_output=True, text=True, timeout=420)
    stdout, stderr, returncode = proc.stdout, proc.stderr, proc.returncode
except subprocess.TimeoutExpired as exc:
    stdout = exc.stdout or b''; stderr = exc.stderr or b''; returncode = 124
    stdout = stdout.decode(errors='replace') if isinstance(stdout, bytes) else stdout
    stderr = stderr.decode(errors='replace') if isinstance(stderr, bytes) else stderr
(axis / (execution_id+'.stdout.log')).write_text(stdout)
(axis / (execution_id+'.stderr.log')).write_text(stderr)
receipt = {'argv': argv, 'cwd': str(repo), 'returncode': returncode, 'wall_seconds': time.monotonic()-started, 'stdout_path': str(axis/(execution_id+'.stdout.log')), 'stderr_path': str(axis/(execution_id+'.stderr.log')), 'source_sha256': hash_file(axis/'verify.wl')}
(axis / (execution_id+'.execution.json')).write_text(json.dumps(receipt, indent=2)+'\n')
marker = 'R7_RESULT_JSON='
marked = [line[len(marker):] for line in stdout.splitlines() if line.startswith(marker)]
if len(marked) == 1:
    result = json.loads(marked[0])
else:
    result = {'checks': checks, 'domain_assumption_diff': [], 'counterexample': None, 'execution_error': 'No unique engine result marker', 'status': 'BLOCKED_RESOURCE_LIMIT' if returncode==124 else 'INCONCLUSIVE'}
result['execution_receipt'] = receipt
print(json.dumps(result, sort_keys=True, allow_nan=False))
sys.exit(returncode)
