#!/usr/bin/env python3
"""One acknowledged CF4 source-layout test/consumer/render continuation."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

ROOT = Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
OUT = Path('/mnt/extdrive/workdir/htt_open_data/r26_cf4_release_stage_seven_channel')
RUN = OUT / 'actual_run'
LAYOUT = OUT
PY = str(ROOT / '.venv/bin/python')
TASK = 'R26-CF4-RELEASE-STAGE-SEVEN-CHANNEL-RESPONSE'
INPUT_SHA = '2fe3811319d2dd7b6b1d43507339f410c559036ab8b0e044a5dcfa413830f004'
FRONTIER_SHA = 'a431b485c2269f75cc388c372aaa6828b1fa6900e7e92b35855045e091275a89'
CONTRACT_SHA = 'cdf94aaf6d39a01baae0d2fc03342032b1eb5f82ef34555e83ca8631d43f7992'
REVIEW_SHA = '5b3998c322d8262b96b7922f90e0b30011ab10c73b2ffb8365ff812262ccfc13'
FROZEN_SHA = 'bdb71210368d44cf4fc52e844d4d1e2577e07d306fb25a1de3d202c04b0e2adf'
PREDECESSOR_RECEIPT_SHA = '42f1b99d0825eb303e9850d5b2187cb3601afa30d9b89bd5496c7da6b115fef5'
BASELINE_FLOOR = 103.50328065082431
CAP_SECONDS = 600.0
INVOCATION_SECONDS = 120.0
RSS_BYTES = 2 * 1024**3
PRODUCTS = ('LOCKED_PARAMETERS.json', 'RESULT.json', 'GROUP_OPERATOR.npz',
            'REPORT.md', 'response.png')


class RunTerminated(Exception):
    pass


def _term(_signum: int, _frame: object) -> None:
    raise RunTerminated('SIGTERM')


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def log(stream: object, record: dict) -> None:
    stream.write(json.dumps(record, sort_keys=True) + '\n')
    stream.flush()
    os.fsync(stream.fileno())


def _sealed(path: Path, seal: dict) -> bool:
    return str(path) == seal.get('path') and path.is_file() and sha(path) == seal.get('sha256')


def preflight(frozen: Path, ack: Path) -> tuple[float, float, dict]:
    if frozen != OUT/'INPUT.json' or not ack.is_file() or not frozen.is_file():
        raise RuntimeError('EXACT_INPUT_AND_ACTUAL_ACK_REQUIRED')
    fixed = {
        frozen: INPUT_SHA,
        OUT/'EXECUTION_FRONTIER.json': FRONTIER_SHA,
        Path('/mnt/extdrive/workdir/htt_open_data/r26_cf4_actual_source_model_review/CONTRACT.md'): CONTRACT_SHA,
        Path('/mnt/extdrive/workdir/htt_open_data/r26_cf4_actual_source_model_review/ACTUAL_RESULT_REVIEW.json'): REVIEW_SHA,
        Path('/mnt/extdrive/workdir/htt_open_data/r26_cf4_final_group_operator_consumer/FROZEN_INPUT_SOURCE_LAYOUT.json'): FROZEN_SHA,
        Path('/mnt/extdrive/workdir/htt_open_data/r26_cf4_final_group_operator_consumer/source_layout_run/RUN_RECEIPT.json'): PREDECESSOR_RECEIPT_SHA,
    }
    for path, expected in fixed.items():
        if not path.is_file() or sha(path) != expected:
            raise RuntimeError(f'IMMUTABLE_INPUT_MISMATCH {path}')
    source_hashes = {name: sha(OUT/name) for name in ('consume.py', 'test_consume.py', 'plot.py', 'run_once.py')}
    a = json.loads(ack.read_text())
    if (a.get('decision') != 'GO' or a.get('task_id') != TASK or
            a.get('input_identity') != 'sha256:'+INPUT_SHA or
            a.get('frontier_sha256') != FRONTIER_SHA or
            a.get('source_sha256') != source_hashes):
        raise RuntimeError('ACK_IDENTITY_OR_SOURCE_MISMATCH')
    packet_seal = a.get('controller_packet')
    if not isinstance(packet_seal, dict) or not _sealed(Path(packet_seal.get('path', '')), packet_seal):
        raise RuntimeError('ACTUAL_CONTROLLER_PACKET_SEAL_REQUIRED')
    packet = json.loads(Path(packet_seal['path']).read_text())
    if (packet.get('task_id') != TASK or packet.get('input_identity') != 'sha256:'+INPUT_SHA or
            packet.get('packet_id') != a.get('packet_id') or
            not isinstance(packet.get('packet_id'), str) or len(packet['packet_id']) != 64):
        raise RuntimeError('CONTROLLER_PACKET_IDENTITY_MISMATCH')
    append = a.get('controller_append')
    if not isinstance(append, dict) or not _sealed(Path(append.get('path', '')), append):
        raise RuntimeError('CONTROLLER_APPEND_SEAL_REQUIRED')
    if a.get('controller_append_sha256') != append['sha256']:
        raise RuntimeError('CONTROLLER_APPEND_IDENTITY_MISMATCH')
    baseline = float(a['baseline_cumulative_seconds'])
    remaining = float(a['remaining_seconds'])
    if (baseline < BASELINE_FLOOR or baseline >= CAP_SECONDS or
            remaining <= 0 or remaining > CAP_SECONDS-baseline+1e-9):
        raise RuntimeError('SHARED_ALLOCATION_LIMIT_UNAVAILABLE')
    return baseline, min(INVOCATION_SECONDS, remaining, CAP_SECONDS-baseline), a


def group_rss(pgid: int) -> int:
    total = 0
    for entry in Path('/proc').iterdir():
        if not entry.name.isdecimal():
            continue
        try:
            fields = (entry/'stat').read_text().rsplit(')', 1)[1].split()
            if int(fields[2]) != pgid:
                continue
            for line in (entry/'status').read_text().splitlines():
                if line.startswith('VmRSS:'):
                    total += int(line.split()[1])*1024
                    break
        except (FileNotFoundError, ProcessLookupError, PermissionError, IndexError, ValueError):
            continue
    return total


def group_live_members(pgid: int) -> list[int]:
    members = []
    for entry in Path('/proc').iterdir():
        if not entry.name.isdecimal():
            continue
        try:
            fields = (entry/'stat').read_text().rsplit(')', 1)[1].split()
            if int(fields[2]) == pgid and fields[0] != 'Z':
                members.append(int(entry.name))
        except (FileNotFoundError, ProcessLookupError, PermissionError, IndexError, ValueError):
            continue
    return members


def kill_group(pgid: int) -> None:
    try:
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def run_stage(name: str, command: list[str], env: dict, deadline: float,
              stream: object, start: float, baseline: float,
              stage_peaks: dict[str, int]) -> None:
    stage_start = time.monotonic()
    if stage_start >= deadline:
        log(stream, {'event': 'CHILD_NOT_STARTED', 'stage': name, 'utc': stamp(),
                     'reason': 'WALL_CAP_BEFORE_LAUNCH',
                     'elapsed_from_entry_seconds': stage_start-start,
                     'cumulative_seconds': baseline+stage_start-start})
        raise RuntimeError(f'{name} WALL_CAP_BEFORE_LAUNCH')
    log(stream, {'event': 'CHILD_START', 'stage': name, 'utc': stamp(), 'command': command,
                 'cwd': str(ROOT), 'elapsed_from_entry_seconds': stage_start-start,
                 'cumulative_at_start_seconds': baseline+stage_start-start})
    peak = 0
    outcome = 'INTERRUPTED'
    exitcode = None
    child = None
    reaped = False
    completed = False
    interrupted = False
    group_remaining: list[int] = []
    with (RUN/f'{name}.stdout').open('x') as stdout, (RUN/f'{name}.stderr').open('x') as stderr:
        try:
            if time.monotonic() >= deadline:
                outcome = 'WALL_CAP_BEFORE_LAUNCH'
                raise RuntimeError(f'{name} WALL_CAP_BEFORE_LAUNCH')
            child = subprocess.Popen(command, cwd=ROOT, env=env, stdout=stdout,
                                     stderr=stderr, start_new_session=True)
            while True:
                # WNOWAIT keeps the group leader's PID reserved until group cleanup.
                info = os.waitid(os.P_PID, child.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
                peak = max(peak, group_rss(child.pid))
                if info is not None:
                    completed = True
                    break
                if peak > RSS_BYTES:
                    outcome = 'RSS_CAP'
                    break
                if time.monotonic() >= deadline:
                    outcome = 'WALL_CAP'
                    break
                time.sleep(.05)
        except BaseException:
            interrupted = True
            raise
        finally:
            if child is not None:
                # The unreaped leader prevents PGID reuse while signaling the own group.
                kill_group(child.pid)
                cleanup_until = time.monotonic() + 1.0
                while True:
                    group_remaining = group_live_members(child.pid)
                    if not group_remaining or time.monotonic() >= cleanup_until:
                        break
                    time.sleep(.01)
                try:
                    _, status, usage = os.wait4(child.pid, 0)
                    reaped = True
                    exitcode = os.waitstatus_to_exitcode(status)
                    peak = max(peak, usage.ru_maxrss*1024)
                except ChildProcessError:
                    outcome = 'CHILD_REAP_FAILURE'
                if group_remaining:
                    outcome = 'PG_CLEANUP_INCOMPLETE'
                elif completed and reaped and not interrupted:
                    if peak > RSS_BYTES:
                        outcome = 'RSS_CAP'
                    elif time.monotonic() >= deadline:
                        outcome = 'WALL_CAP'
                    else:
                        outcome = 'PASS' if exitcode == 0 else 'FAILED'
            terminal = time.monotonic()
            stage_peaks[name] = peak
            log(stream, {'event': 'CHILD_TERMINAL', 'stage': name, 'utc': stamp(),
                         'outcome': outcome, 'exitcode': exitcode,
                         'child_reaped': reaped, 'group_live_remaining': group_remaining,
                         'debit_seconds': terminal-stage_start,
                         'elapsed_from_entry_seconds': terminal-start,
                         'cumulative_seconds': baseline+terminal-start,
                         'peak_rss_bytes': peak,
                         'stdout': str(RUN/f'{name}.stdout'),
                         'stderr': str(RUN/f'{name}.stderr')})
    if outcome != 'PASS':
        raise RuntimeError(f'{name} {outcome} exit={exitcode}')


def run(frozen: Path, ack: Path) -> None:
    entered = time.monotonic()
    RUN.mkdir(exist_ok=True)
    ledger = RUN/'EXECUTION.jsonl'
    if os.path.lexists(ledger) or os.path.lexists(RUN/'RUN_RECEIPT.json'):
        raise FileExistsError('one-use continuation already started or receipted')
    with ledger.open('x') as stream:
        old_handler = signal.signal(signal.SIGTERM, _term)
        baseline = BASELINE_FLOOR
        limit = 0.0
        peak = 0
        stage_peaks: dict[str, int] = {}
        outcome = 'INTERRUPTED'
        failure = None
        candidate = RUN/'.candidate'
        phase_start = entered
        log(stream, {'event': 'ENTRY', 'utc': stamp(), 'task_id': TASK,
                     'frozen_input': str(frozen), 'ack': str(ack),
                     'inherited_baseline_floor_seconds': BASELINE_FLOOR})
        try:
            baseline, limit, a = preflight(frozen, ack)
            deadline = entered+limit
            now = time.monotonic()
            log(stream, {'event': 'PREFLIGHT_TERMINAL', 'utc': stamp(), 'status': 'PASS',
                         'debit_seconds': now-phase_start,
                         'cumulative_seconds': baseline+now-entered,
                         'input_sha256': sha(frozen), 'ack_sha256': sha(ack),
                         'controller_packet_sha256': a['controller_packet']['sha256'],
                         'packet_id': a['packet_id'], 'agent_id': a.get('agent_id', 'UNKNOWN'),
                         'invocation_limit_seconds': limit, 'rss_cap_bytes': RSS_BYTES})
            if now >= deadline:
                raise RuntimeError('WALL_CAP_PREFLIGHT')
            phase_start = now
            if candidate.exists() or (RUN/'products').exists() or (RUN/'FAILED_PARTIAL').exists():
                raise FileExistsError('unresolved earlier candidate or products')
            candidate.mkdir()
            env = dict(os.environ)
            env.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                       NUMEXPR_NUM_THREADS='1', PYTHONPATH='htt', PYTHONDONTWRITEBYTECODE='1')
            steps = [
                ('tests', [PY, '-B', '-m', 'unittest', 'discover', '-s', str(LAYOUT),
                           '-p', 'test_*.py']),
                ('consumer', [PY, '-B', str(LAYOUT/'consume.py'), '--out', str(candidate)]),
                ('render', [PY, '-B', str(OUT/'plot.py'), '--out', str(candidate)]),
            ]
            now = time.monotonic()
            log(stream, {'event': 'CONTROL_TERMINAL', 'utc': stamp(), 'status': 'PASS',
                         'debit_seconds': now-phase_start,
                         'cumulative_seconds': baseline+now-entered,
                         'steps': [name for name, _ in steps]})
            if now >= deadline:
                raise RuntimeError('WALL_CAP_BEFORE_TESTS')
            for name, command in steps:
                run_stage(name, command, env, deadline, stream, entered, baseline,
                          stage_peaks)
            cleanup_start = time.monotonic()
            if cleanup_start >= deadline:
                raise RuntimeError('WALL_CAP_AFTER_RENDER')
            scientific_status = json.loads((candidate/'RESULT.json').read_text())['status']
            expected = (tuple(name for name in PRODUCTS if name != 'GROUP_OPERATOR.npz')
                        if scientific_status == 'SINGLETON_IDENTIFICATION_REJECTED' else PRODUCTS)
            for name in expected:
                if not (candidate/name).is_file():
                    raise RuntimeError(f'INCOMPLETE_OUTPUT {name}')
            if sorted(p.name for p in candidate.iterdir()) != sorted(expected):
                raise RuntimeError('CANDIDATE_OUTPUT_SET_MISMATCH')
            os.replace(candidate, RUN/'products')
            now = time.monotonic()
            log(stream, {'event': 'CLEANUP_TERMINAL', 'utc': stamp(), 'status': 'PASS',
                         'debit_seconds': now-cleanup_start,
                         'cumulative_seconds': baseline+now-entered,
                         'products_path': str(RUN/'products')})
            if now >= deadline:
                raise RuntimeError('WALL_CAP_AFTER_PROMOTION')
            outcome = 'SCIENTIFIC_HOLD' if scientific_status in (
                'SINGLETON_IDENTIFICATION_REJECTED', 'HELDOUT_REPRESENTATIVE_REJECTED') else 'PASS'
        except BaseException as exc:
            failure = f'{type(exc).__name__}: {exc}'
            cleanup_start = time.monotonic()
            if candidate.exists():
                os.replace(candidate, RUN/'FAILED_PARTIAL')
            elif (RUN/'products').exists() and outcome != 'PASS':
                os.replace(RUN/'products', RUN/'FAILED_PARTIAL')
            now = time.monotonic()
            log(stream, {'event': 'CLEANUP_TERMINAL', 'utc': stamp(), 'status': 'FAILED',
                         'debit_seconds': now-cleanup_start,
                         'cumulative_seconds': baseline+now-entered,
                         'first_failure': failure})
            raise
        finally:
            signal.signal(signal.SIGTERM, old_handler)
            terminal_start = time.monotonic()
            peak = max(stage_peaks.values(), default=0)
            receipt = {'schema': 'htt.r26.cf4_release_stage_run/1',
                       'task_id': TASK, 'utc': stamp(), 'status': outcome,
                       'first_failure': failure, 'input_sha256': sha(frozen) if frozen.is_file() else None,
                       'ack_sha256': sha(ack) if ack.is_file() else None,
                       'historical_baseline_seconds': baseline,
                       'new_charged_seconds': terminal_start-entered,
                       'cumulative_seconds': baseline+terminal_start-entered,
                       'cap_seconds': CAP_SECONDS, 'invocation_limit_seconds': limit,
                       'peak_rss_bytes_seen': peak, 'rss_cap_bytes': RSS_BYTES,
                       'threads': 1, 'requested_runtime': 'gpt-6-sol/high',
                       'observed_runtime': 'UNKNOWN', 'original_H02': 'HOLD_UNCHANGED',
                       'products_path': str(RUN/'products') if outcome in ('PASS', 'SCIENTIFIC_HOLD') else None}
            log(stream, {'event': 'RUN_TERMINAL', **receipt,
                         'terminal_debit_seconds': time.monotonic()-terminal_start})
            receipt['new_charged_seconds'] = time.monotonic()-entered
            receipt['cumulative_seconds'] = baseline+receipt['new_charged_seconds']
            with (RUN/'RUN_RECEIPT.json').open('x') as out:
                out.write(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
                out.flush()
                os.fsync(out.fileno())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--frozen-input', type=Path, default=OUT/'INPUT.json')
    parser.add_argument('--ack-json', type=Path, default=RUN/'ACTUAL_ACK.json')
    args = parser.parse_args()
    run(args.frozen_input, args.ack_json)
