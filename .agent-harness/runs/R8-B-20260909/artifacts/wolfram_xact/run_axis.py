#!/usr/bin/env python3
"""Run exact Wolfram/xAct O4 checks; stdout is machine JSON only.

Default replay leaves no persistent output changes. --record captures original execution evidence in
this owned directory. Timing lives in execution.json, never in scientific JSON.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import tempfile

HERE = Path(__file__).resolve().parent
CONTRACT = HERE.parent.parent / 'CAS_CONTRACT.json'
EXPECTED_CONTRACT = '430f325399b7caf0e7513cccec64e5bdae114ecafa5ce039747e373936c82f9d'
KERNEL = '/usr/local/Wolfram/WolframEngine/15.0/Executables/WolframKernel'
parser = argparse.ArgumentParser()
parser.add_argument('--record', action='store_true')
args = parser.parse_args()
if hashlib.sha256(CONTRACT.read_bytes()).hexdigest() != EXPECTED_CONTRACT:
    raise SystemExit('contract byte identity changed')
scratch = tempfile.TemporaryDirectory(prefix='replay_', dir=HERE)
payload_file = Path(scratch.name) / 'payload.json'
argv = [KERNEL, '-noprompt', '-script', str(HERE / 'verify.wl'), str(payload_file)]
started = datetime.now(timezone.utc).isoformat()
t0 = time.monotonic()
try:
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=1750)
except subprocess.TimeoutExpired as exc:
    sys.stderr.write('Wolfram exact axis timed out\n')
    raise SystemExit(124) from exc
elapsed = time.monotonic() - t0
completed = datetime.now(timezone.utc).isoformat()

if args.record:
    (HERE / 'engine_transcript.log').write_text(proc.stdout + '\nSTDERR:\n' + proc.stderr)
    (HERE / 'execution.json').write_text(json.dumps({'argv': argv, 'cwd': str(Path.cwd()), 'started_at': started, 'completed_at': completed, 'elapsed_seconds': elapsed, 'exit_code': proc.returncode, 'python': sys.version}, indent=2) + '\n')
if not payload_file.is_file():
    sys.stderr.write(proc.stdout + proc.stderr)
    raise SystemExit(proc.returncode or 2)
payload = json.loads(payload_file.read_text())
scratch.cleanup()
payload['contract_sha256'] = EXPECTED_CONTRACT
scientific = json.dumps(payload, sort_keys=True, separators=(',', ':'))
if args.record:
    (HERE / 'scientific_result.json').write_text(scientific + '\n')
print(scientific)
raise SystemExit(proc.returncode)
