"""Budget orchestration only; execute the independent reviewer's exact -c body once."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
TASK = HERE.parent.parent
sys.path.insert(0, str(TASK))
from run_source_analysis import CAP, LEDGER, append_ledger, ledger_state, write_json

PHASE = 'INDEPENDENT_CACHED_SUMMARY_VALIDATION_ONCE'
CANONICAL = TASK.parents[5] / '.venv' / 'bin' / 'python'
if Path(sys.executable).absolute() != CANONICAL:
    raise SystemExit(f'Use canonical interpreter {CANONICAL}')
body_bytes = (HERE / 'REVIEWER_BODY.py').read_bytes()
body = body_bytes.decode('utf-8')
body_sha = hashlib.sha256(body_bytes).hexdigest()
command = [str(CANONICAL), '-B', '-c', body]
environment = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1',
                   MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1')
with LEDGER.open('a+', encoding='utf-8') as ledger:
    fcntl.flock(ledger, fcntl.LOCK_EX | fcntl.LOCK_NB)
    records, used = ledger_state(ledger)
    if any(row.get('phase') == PHASE for row in records):
        raise SystemExit('HOLD: cached validation already launched; no rerun')
    if used != 40.71262605697848 or used >= CAP:
        raise SystemExit('HOLD: shared budget differs from authorized starting state')
    remaining = CAP - used
    timeout = min(10., remaining)
    run_id = str(time.time_ns())
    write_json(HERE / 'COMMAND.json', {
        'command': command, 'body_sha256': body_sha, 'cwd': str(Path.cwd()),
        'phase': PHASE, 'run_id': run_id, 'prior_cumulative_s': used,
        'remaining_s': remaining, 'reserved_s': timeout,
        'requested_model': 'gpt-6.1-sol', 'requested_effort': 'high',
        'observed_model': 'UNKNOWN', 'numerical_thread_limits': {
            key: environment[key] for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS',
                'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS')}})
    with (HERE / 'RAW_STDOUT_STDERR.txt').open('xb') as raw:
        append_ledger(ledger, {
            'event': 'START', 'run_id': run_id, 'phase': PHASE,
            'command': command, 'body_sha256': body_sha, 'prior_cumulative_s': used,
            'remaining_s': remaining, 'reserved_s': timeout, 'unit_timeout_s': timeout,
            'requested_model': 'gpt-6.1-sol', 'requested_effort': 'high',
            'observed_model': 'UNKNOWN'})
        exit_code = 1
        started = time.monotonic()
        try:
            exit_code = subprocess.run(command, env=environment, stdout=raw,
                stderr=subprocess.STDOUT, timeout=timeout).returncode
        except subprocess.TimeoutExpired:
            exit_code = 124
            raw.write(f'\nTIMEOUT after {timeout}s; first partial retained; no retry.\n'.encode())
        except BaseException:
            raw.write(traceback.format_exc().encode())
            raise
        finally:
            elapsed = time.monotonic() - started
            append_ledger(ledger, {
                'event': 'END', 'run_id': run_id, 'phase': PHASE, 'elapsed_s': elapsed,
                'cumulative_s': used + elapsed, 'exit_code': exit_code,
                'body_sha256': body_sha})
            write_json(HERE / 'RETURN.json', {
                'run_id': run_id, 'phase': PHASE, 'body_sha256': body_sha,
                'exit_code': exit_code, 'elapsed_s': elapsed, 'cumulative_s': used + elapsed,
                'scientific_admission': 'HOLD', 'source_refits': 0,
                'status': 'EXECUTED_AWAITING_INDEPENDENT_REVIEW' if exit_code == 0
                          else 'FIRST_FAILURE_OR_PARTIAL_PRESERVED',
                'requested_model': 'gpt-6.1-sol', 'requested_effort': 'high',
                'observed_model': 'UNKNOWN'})
print(json.dumps({'exit_code': exit_code, 'body_sha256': body_sha,
                 'elapsed_s': elapsed, 'cumulative_s': used + elapsed}, sort_keys=True))
raise SystemExit(exit_code)
