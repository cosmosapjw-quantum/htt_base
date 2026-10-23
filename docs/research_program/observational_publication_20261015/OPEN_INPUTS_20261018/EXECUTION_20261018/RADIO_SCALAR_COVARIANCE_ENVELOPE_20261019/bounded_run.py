"""Serialized numerical runner: 60 seconds cumulative, no retries after failure."""
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
LEDGER = HERE / 'NUMERICAL_USAGE.jsonl'


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def run():
    phase = sys.argv[1]
    commands = {'controls': ['test_envelope.py'], 'actual': ['envelope.py'],
                'plots': ['plot_report.py'], 'review': ['test_envelope.py', '--cached-review']}
    if phase not in commands:
        raise ValueError('Unknown unit')
    with (HERE / 'budget.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        records = [json.loads(x) for x in LEDGER.read_text().splitlines() if x] if LEDGER.exists() else []
        starts = {r['run_id'] for r in records if r['event'] == 'START'}
        ends = {r['run_id'] for r in records if r['event'] == 'END'}
        if starts != ends:
            raise RuntimeError('Unreconciled accounting: STOP')
        completed = [r for r in records if r['event'] == 'END']
        if any(r['exit_code'] != 0 or r['killed'] for r in completed):
            raise RuntimeError('Prior numerical failure: STOP, explicit repair required')
        if phase != 'review' and any(r['phase'] == phase for r in records):
            raise RuntimeError('Phase already consumed: no retry')
        required = {'actual': 'controls', 'plots': 'actual', 'review': 'actual'}.get(phase)
        if required and not any(r['phase'] == required for r in completed):
            raise RuntimeError('Missing prerequisite ' + required)
        cumulative = max((r['cumulative_s'] for r in completed), default=0.)
        remaining = 60. - cumulative
        reserve = 8. if phase == 'actual' else 0.25
        if remaining <= reserve:
            raise RuntimeError('Insufficient cumulative budget')
        run_id = phase + '_' + uuid.uuid4().hex[:12]
        argv = [str(ROOT / '.venv/bin/python'), '-B', str(HERE / commands[phase][0]), *commands[phase][1:]]
        if phase == 'review' and len(sys.argv) > 2:
            # Fresh reviewer may supply an inline cached-only check. The caller
            # owns compliance with the contract's no-raw-replay restriction.
            argv = [str(ROOT / '.venv/bin/python'), '-B', *sys.argv[2:]]
        env = os.environ.copy()
        pins = {key: '1' for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
            'OPENBLAS_DEFAULT_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS',
            'NUMEXPR_MAX_THREADS', 'VECLIB_MAXIMUM_THREADS', 'GOTO_NUM_THREADS', 'BLIS_NUM_THREADS')}
        pins.update(MPLBACKEND='Agg', PYTHONDONTWRITEBYTECODE='1')
        env.update(pins)
        record = dict(event='START', run_id=run_id, phase=phase, command=argv, cwd=str(ROOT),
            env=pins, started_at=stamp(), prior_cumulative_s=cumulative,
            timeout_s=remaining-reserve, cap_s=60, reserve_s=reserve,
            framing_numerical_s=0, requested_model='gpt-6.1-sol', requested_effort='high',
            observed_model='UNKNOWN', observed_effort='UNKNOWN',
            code_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.glob('*.py')},
            contract_sha256=hashlib.sha256((HERE/'CONTRACT.md').read_bytes()).hexdigest(),
            raw_log=str(HERE/(run_id+'.log')))
        with LEDGER.open('a') as ledger:
            ledger.write(json.dumps(record)+'\n'); ledger.flush(); os.fsync(ledger.fileno())
        start = time.monotonic()
        max_rss = max_threads = 0
        killed = None
        exit_code = 1
        try:
            with (HERE/(run_id+'.log')).open('x') as out:
                process = subprocess.Popen(argv, cwd=ROOT, env=env, stdout=out,
                    stderr=subprocess.STDOUT, start_new_session=True)
                while process.poll() is None:
                    try:
                        status = Path(f'/proc/{process.pid}/status').read_text()
                        values = {x.split(':')[0]: x.split(':')[1].strip() for x in status.splitlines() if ':' in x}
                        max_rss = max(max_rss, int(values.get('VmHWM','0 kB').split()[0]), int(values.get('VmRSS','0 kB').split()[0]))
                        max_threads = max(max_threads, int(values.get('Threads',0)))
                    except FileNotFoundError:
                        pass
                    elapsed = time.monotonic()-start
                    if elapsed > remaining-reserve or max_rss > 512*1024 or max_threads > 2:
                        killed = 'WALL_CAP' if elapsed > remaining-reserve else ('RSS_CAP' if max_rss > 512*1024 else 'THREAD_CAP')
                        os.killpg(process.pid, signal.SIGKILL)
                        break
                    time.sleep(.01)
                exit_code = process.wait()
        finally:
            elapsed = time.monotonic()-start
            end = dict(event='END', run_id=run_id, phase=phase, ended_at=stamp(), elapsed_s=elapsed,
                cumulative_s=cumulative+elapsed, exit_code=exit_code, killed=killed,
                max_rss_kib_observed=max_rss, max_threads_observed=max_threads,
                resource_observation='/proc child status sampled every 10ms; VmHWM included')
            with LEDGER.open('a') as ledger:
                ledger.write(json.dumps(end)+'\n'); ledger.flush(); os.fsync(ledger.fileno())
            print(json.dumps(end), flush=True)
        sys.exit(exit_code if exit_code >= 0 else 1)


if __name__ == '__main__':
    run()
