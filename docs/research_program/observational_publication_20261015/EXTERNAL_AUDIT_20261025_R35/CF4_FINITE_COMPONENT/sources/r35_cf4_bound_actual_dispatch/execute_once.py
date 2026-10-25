"""One externally bounded saved-artifact invocation and its durable return receipt."""
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

BASE = Path('/mnt/extdrive/workdir/htt_open_data')
PREP = BASE / 'r35_cf4_saved_bound_repair'
OUT = BASE / 'r35_cf4_bound_actual_dispatch'
PACKET = BASE / 'r35_publication_acceleration_controller/NEXT_AFTER_P5_CANDIDATE.json'
GO = PREP / 'ROOT_ACK_GO.json'
SOURCE = PREP / 'postprocess_repaired.py'
OLD_PRODUCT = BASE / 'r30_cf4_pv_tensor_numeric/fast_window_fixture_repair/actual_run/PRODUCT.npz'
APPROVAL = BASE / 'r32_cf4_fresh_scientific_review/r35_saved_bound_source/RESULT.json'
PACKET_ID = '9afeff7cfb514f0be293b369307f6345f18151486c390dc8e80b1958991777ca'
TASK_ID = 'R30-CF4-BAND-PV-FULL-TENSOR-COVARIANCE'
INPUT = 'sha256:5da5fe9adeee84d6615cf9127a91ff5bccff6172e43716680ae0792ef480c5d3'
OLD = 'ae5d4a97c433c998e5777e6c4372ccb3dd3f800d29d5a52576fc183ea2fc5985'
SOURCE_SHA = 'a419c75cc62ff2707f90030010eb83daffbc19e7e57a74e0dd715ba0cf4b8dab'
APPROVAL_SHA = '34205664ce3c690863a87dcb3cd730b1597119980135101f6c0f7e77edb0f65d'
PRODUCT_SHA = 'cfec008002fea776611d6abb70448a8b5cbed0d774a49d3377a5cfcf828a857d'


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def write(path, data):
    tmp = path.with_name(path.name + '.tmp')
    with open(tmp, 'w') as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)
    descriptor = os.open(path.parent, os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def need(condition, code):
    if not condition:
        raise RuntimeError(code)


def main():
    began = time.monotonic()
    receipt_path = OUT / 'ACTUAL_RUN_RECEIPT.json'
    return_path = OUT / 'CONTROLLER_RETURN.json'
    need(not receipt_path.exists() and not return_path.exists(), 'ONE_SHOT_ALREADY_RECORDED')
    packet = json.loads(PACKET.read_text())
    need(packet['packet_id'] == PACKET_ID and packet['task_id'] == TASK_ID and
         packet['input_identity'] == INPUT and
         packet['candidate_identity'] == 'sha256:' + OLD and
         packet['attempt'] == 11, 'SELECTED_PACKET_DRIFT')
    need(sha(SOURCE) == SOURCE_SHA, 'PREPARED_SOURCE_DRIFT')
    need(sha(APPROVAL) == APPROVAL_SHA, 'ASTRA_DECISION_DRIFT')
    need(sha(OLD_PRODUCT) == PRODUCT_SHA, 'ORIGINAL_PRODUCT_DRIFT_BEFORE')
    go = json.loads(GO.read_text())
    need(go.get('controller_go') is True and go.get('actual_ack') is True and
         go.get('candidate_sha256') == OLD, 'MISSING_FRESH_ACK_GO')
    for key, expected in (('packet_id', PACKET_ID), ('task_id', TASK_ID),
                          ('input_identity', INPUT)):
        if key in go:
            need(go[key] == expected, 'GO_' + key.upper() + '_MISMATCH')
    ack_path = go.get('actual_ack_receipt_path') or go.get('ack_receipt_path')
    need(isinstance(ack_path, str) and Path(ack_path).is_file(), 'ACTUAL_ACK_RECEIPT_MISSING')
    ack_sha = sha(Path(ack_path))
    if 'actual_ack_receipt_sha256' in go:
        need(ack_sha == go['actual_ack_receipt_sha256'], 'ACTUAL_ACK_RECEIPT_DRIFT')
    need(go.get('whole_command_cap_seconds') == 10 and
         go.get('child_reaping_and_receipt_inside_cap') is True,
         'TEN_SECOND_FUNDING_MISSING')
    account = Path(go.get('account_path', ''))
    need(account.is_file() and sha(account) == go.get('account_sha256'),
         'ROOT_ACCOUNT_SEAL_MISMATCH')
    funding = json.loads(account.read_text())
    need(funding.get('cf4_cumulative_used_seconds') == 599.8927776466445 and
         funding.get('cf4_lifetime_cap_seconds') == 600 and
         funding.get('prospective_fixed_precharges_seconds', {}).get('postprocess_whole') == 10 and
         funding.get('actual_agent_id') == '/root/rc_9afeff7cfb514f0b',
         'ROOT_ACCOUNT_FUNDING_MISMATCH')
    source_receipt = json.loads((PREP / 'SOURCE_REPAIR_RECEIPT.json').read_text())
    need(source_receipt['new_source_sha256'] == SOURCE_SHA and
         source_receipt['decision_sha256'] == APPROVAL_SHA,
         'SOURCE_REPAIR_RECEIPT_DRIFT')
    need(not (PREP / 'CORRECTED_BOUNDS.npz').exists() and
         not (PREP / 'RESULT.json').exists() and
         not (PREP / 'RUN_RECEIPT.json').exists(), 'PREEXISTING_POSTPROCESS_OUTPUT')

    env = os.environ.copy()
    env['OPENBLAS_NUM_THREADS'] = '1'
    env['OMP_NUM_THREADS'] = '1'
    command = [sys.executable, str(SOURCE), '--go', str(GO)]
    child_started = time.monotonic()
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=env, start_new_session=True)
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=max(.01, 8.2 - (child_started - began)))
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(proc.pid, signal.SIGKILL)
        stdout, stderr = proc.communicate()
    child_ended = time.monotonic()
    for name, data in (('stdout.txt', stdout), ('stderr.txt', stderr)):
        with open(OUT / name, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    result_path = PREP / 'RESULT.json'
    result = json.loads(result_path.read_text()) if result_path.is_file() else None
    product_after = sha(OLD_PRODUCT)
    result_valid = (not timed_out and proc.returncode == 0 and
                    isinstance(result, dict) and result.get('all_original_gates_pass') is True and
                    result.get('status') == 'SAVED_BOUND_REPAIRED_PENDING_INDEPENDENT_CLOSEOUT' and
                    result.get('unchanged_product_sha256') == PRODUCT_SHA and
                    (PREP / 'CORRECTED_BOUNDS.npz').is_file())
    if result_valid:
        result_valid = (sha(PREP / 'CORRECTED_BOUNDS.npz') == result['corrected_bounds_sha256'] and
                        product_after == PRODUCT_SHA)
    candidate = None
    if result_valid:
        binding = {'packet_id': PACKET_ID, 'task_id': TASK_ID, 'input_identity': INPUT,
                   'old_candidate_sha256': OLD, 'source_sha256': SOURCE_SHA,
                   'result_sha256': sha(result_path),
                   'corrected_bounds_sha256': result['corrected_bounds_sha256'],
                   'unchanged_product_sha256': PRODUCT_SHA}
        write(OUT / 'CANDIDATE_BINDING.json', binding)
        candidate = 'sha256:' + sha(OUT / 'CANDIDATE_BINDING.json')
        need(candidate != 'sha256:' + OLD, 'NEW_CANDIDATE_REUSES_OLD_IDENTITY')
    first_failure = None if result_valid else (
        'EXTERNAL_WHOLE_CAP_CHILD_DEADLINE' if timed_out else
        result.get('first_failure') if isinstance(result, dict) and result.get('first_failure') else
        'POSTPROCESS_RETURN_OR_ORIGINAL_GATE_FAILURE')
    receipt = {'packet_id': PACKET_ID, 'task_id': TASK_ID, 'input_identity': INPUT,
               'attempt': 11, 'actual_ack_receipt_path': ack_path,
               'actual_ack_receipt_sha256': ack_sha, 'go_path': str(GO),
               'go_sha256': sha(GO), 'source_sha256': SOURCE_SHA,
               'command': command, 'whole_cap_seconds': 10,
               'child_deadline_from_outer_start_seconds': 8.2,
               'child_wall_seconds': child_ended - child_started,
               'wall_before_receipt_seconds': time.monotonic() - began,
               'child_returncode': proc.returncode, 'child_timed_out': timed_out,
               'child_maxrss_kib_as_available': resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
               'stdout_path': str(OUT / 'stdout.txt'), 'stdout_sha256': sha(OUT / 'stdout.txt'),
               'stderr_path': str(OUT / 'stderr.txt'), 'stderr_sha256': sha(OUT / 'stderr.txt'),
               'source_result_path': str(result_path) if result_path.is_file() else None,
               'source_result_sha256': sha(result_path) if result_path.is_file() else None,
               'product_sha256_after': product_after,
               'outcome': 'success' if result_valid else 'blocker',
               'first_failure': first_failure,
               'candidate_identity': candidate}
    write(receipt_path, receipt)
    controller_return = {'packet_id': PACKET_ID, 'task_id': TASK_ID,
                         'input_identity': INPUT, 'attempt': 11, 'phase': 'repair',
                         'outcome': receipt['outcome'], 'candidate_identity': candidate,
                         'old_candidate_identity': 'sha256:' + OLD,
                         'raw_receipt': str(receipt_path), 'raw_receipt_sha256': sha(receipt_path),
                         'validation_paths': [str(result_path), str(PREP / 'CORRECTED_BOUNDS.npz')]
                         if result_valid else [],
                         'proposed_original_products': [str(OLD_PRODUCT)] if result_valid else [],
                         'first_failure': first_failure,
                         'scientific_admission': False, 'H02': 'HOLD', 'H04': 'HOLD',
                         'global_rigorous_type3_error_enclosure': 'NOT_ESTABLISHED',
                         'independent_closeout': 'PENDING' if result_valid else 'BLOCKED'}
    write(return_path, controller_return)
    print(json.dumps({'outcome': receipt['outcome'], 'first_failure': first_failure,
                      'candidate_identity': candidate,
                      'outer_wall_seconds': time.monotonic() - began}, allow_nan=False))
    return 0 if result_valid else 1


if __name__ == '__main__':
    raise SystemExit(main())
