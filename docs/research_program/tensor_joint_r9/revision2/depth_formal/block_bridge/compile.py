#!/usr/bin/env python3
"""Source-bound Host Lean execution; no independent-axis or admission claim."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[6]
CACHE = Path('/mnt/sn850x2t/htt_base_e2e/lean-shared/v4.31.0/packages')
PIN = 'fabf563a7c95a166b8d7b6efca11c8b4dc9d911f'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    assert subprocess.check_output(['git', '-C', str(CACHE/'mathlib'), 'rev-parse', 'HEAD'], text=True).strip() == PIN
    assert (CACHE/'mathlib/lean-toolchain').read_bytes() == (ROOT/'formal/lean-toolchain').read_bytes()
    prior = [json.loads(p.read_text()) for p in out.parent.glob('*/execution.json')]
    remaining = 1200 - sum(p.get('seconds', 0) for p in prior)
    if remaining <= 0:
        raise RuntimeError('STOP_BUDGET: compiler wall budget exhausted')
    src = ROOT/'formal/R9Depth/BlockBridge.lean'
    data = src.read_bytes()
    (out/'source.lean').write_bytes(data)
    env = dict(os.environ, LEAN_PATH=os.pathsep.join(str(p) for p in sorted(CACHE.glob('*/.lake/build/lib/lean'))))
    argv = ['lake', 'env', 'lean', 'R9Depth/BlockBridge.lean']
    start = time.monotonic()
    try:
        p = subprocess.run(argv, cwd=ROOT/'formal', env=env, text=True, capture_output=True, timeout=min(180, remaining))
        code, stdout, stderr = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as exc:
        code, stdout, stderr = None, str(exc.stdout), str(exc.stderr)
    record = dict(argv=argv, cwd=str(ROOT/'formal'), source_sha256=hashlib.sha256(data).hexdigest(), exit_code=code, stdout=stdout, stderr=stderr, seconds=time.monotonic()-start, LEAN_PATH=env['LEAN_PATH'], mathlib_commit=PIN)
    (out/'execution.json').write_text(json.dumps(record, indent=2)+'\n')
    print(stdout)
    print(stderr)
    print('exit', code)
    return 0 if code == 0 and 'sorryAx' not in stdout else 1

if __name__ == '__main__':
    raise SystemExit(main())
