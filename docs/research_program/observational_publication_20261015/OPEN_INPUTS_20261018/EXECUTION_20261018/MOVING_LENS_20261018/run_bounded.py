"""Capture bounded local generation/tests and freeze their review candidate."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / '.git').exists())
PYTHON = ROOT / '.venv/bin/python'
HISTORICAL_HEAD = 'ad27f4cb5f84dfaccc322e53f2810ad29dc72276'


def verify_replay_inputs():
    """Bind replay to the reviewed local code and acquisition, not live HEAD."""
    candidate = json.loads((HERE / 'CANDIDATE.json').read_text())
    if candidate['base_head'] != HISTORICAL_HEAD:
        raise ValueError('Historical campaign identity mismatch')
    for name in ['moving_lens.py', 'test_moving_lens.py', 'run_bounded.py',
                 'acquire_source.py', 'ACQUISITION.json']:
        data = (HERE / name).read_bytes()
        expected = candidate['files'][name]
        if len(data) != expected['bytes'] or hashlib.sha256(data).hexdigest() != expected['sha256']:
            raise ValueError(f'Reviewed replay input mismatch: {name}')
    # moving_lens.main additionally verifies both original source byte identities.
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()


def main():
    if Path(sys.executable) != PYTHON:
        raise RuntimeError('Use the existing canonical .venv/bin/python')
    execution_head = verify_replay_inputs()
    env = dict(os.environ, OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', MKL_NUM_THREADS='2',
               NUMEXPR_NUM_THREADS='2', PYTHONDONTWRITEBYTECODE='1')
    start = time.monotonic()
    commands = [[str(PYTHON), str(HERE / 'moving_lens.py')],
                [str(PYTHON), str(HERE / 'test_moving_lens.py')]]
    receipts = []
    for label, command in zip(['GENERATE', 'TARGETED_TESTS'], commands):
        before = time.monotonic()
        run = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True,
                             timeout=max(.1, 120-(before-start)))
        log = HERE / f'{label}.log'
        log.write_text('COMMAND: ' + json.dumps(command) + '\nCWD: ' + str(ROOT) + '\n' +
                       'STDOUT:\n' + run.stdout + '\nSTDERR:\n' + run.stderr +
                       f'\nEXIT: {run.returncode}\n')
        receipt = dict(label=label, argv=command, cwd=str(ROOT), exit_status=run.returncode,
                       elapsed_seconds=time.monotonic()-before, log=log.name)
        receipts.append(receipt)
        print(json.dumps(receipt), flush=True)
        if run.returncode:
            raise RuntimeError(f'{label} failed; preserve {log}')
    validation = dict(commands=receipts, total_finite_compute_seconds=time.monotonic()-start,
                      hard_limit_seconds=120, thread_caps=2, canonical_interpreter=str(PYTHON),
                      historical_campaign_base_head=HISTORICAL_HEAD,
                      current_execution_head=execution_head,
                      no_ode_or_mcmc=True, independent_review_status='PENDING')
    (HERE / 'VALIDATION.json').write_text(json.dumps(validation, indent=2)+'\n')
    files = {}
    for p in sorted(HERE.iterdir()):
        if p.is_file() and p.name != 'CANDIDATE.json':
            data = p.read_bytes()
            files[p.name] = dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    candidate = dict(base_head=HISTORICAL_HEAD, current_execution_head=execution_head,
                     scope=str(HERE.relative_to(ROOT)), files=files,
                     scientific_admission='HOLD', review_status='PENDING_FRESH_INDEPENDENT_REVIEW')
    (HERE / 'CANDIDATE.json').write_text(json.dumps(candidate, indent=2)+'\n')


if __name__ == '__main__':
    main()
