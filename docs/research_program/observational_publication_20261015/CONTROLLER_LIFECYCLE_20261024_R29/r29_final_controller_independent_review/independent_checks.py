"""R29 independent metadata-only controller probes; no scientific execution."""
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
from contextlib import redirect_stdout
from unittest.mock import patch

ROOT = Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
OWN = Path('/mnt/extdrive/workdir/htt_open_data/r29_final_controller_independent_review')
sys.path.insert(0, str(ROOT / 'scripts/codex_harness'))
spec = importlib.util.spec_from_file_location('independent_candidate', ROOT / 'scripts/codex_harness/research_controller.py')
rc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rc)
POLICY = rc.load_policy()
PROFILES = {(row['requested']['model'], row['requested']['effort']) for row in POLICY['routes'].values()}
checks = []

def passed(name):
    checks.append(name)
    print('PASS', name)

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    return str(path)

def fresh():
    s = rc.initialize({'campaign_id': 'independent-metadata-probe', 'tasks': [
        {'id': 'A', 'kind': 'code', 'goal': 'metadata lifecycle', 'acceptance': 'independent review',
         'input_identity': 'frozen-input', 'approved_repair_id': None},
        {'id': 'OLD', 'goal': 'preserved history', 'acceptance': 'preserved acceptance',
         'input_identity': 'old-input', 'initial_state': 'completed', 'reuse_evidence': ['fixture-only']}
    ]}, 'metadata fixture only; no actual native dispatch')
    s['tasks']['A']['accounting'] = {'seconds': 18.6652202853, 'cap': 30, 'tokens': 187}
    s['tasks']['OLD']['history'] = [{'fixture': 'prior evidence preserved'}]
    s['ultra_repairs']['used-old'] = {'task_id': 'OLD', 'packet_id': 'old-used'}
    s['ultra_pending']['pending-other'] = {'task_id': 'OTHER', 'packet_id': 'old-pending'}
    return s

def packet(s, agent):
    p = rc.next_packet(s, POLICY, PROFILES)
    rc.acknowledge(s, p['packet_id'], agent)
    return p

def result(s, p, directory, outcome='success', **extra):
    value = {'packet_id': p['packet_id'], 'task_id': 'A', 'input_identity': 'frozen-input',
             'agent_id': s['packets'][p['packet_id']]['agent_id'], 'outcome': outcome, **extra}
    raw = write(directory / (p['packet_id'] + '.raw.json'), value)
    value['raw_receipt'] = raw
    rc.record(s, value, POLICY)
    return value

def initial(directory, plan, issue_class='numeric'):
    s = fresh()
    first = packet(s, 'initial-author')
    result(s, first, directory, 'blocker', issue={'class': issue_class, 'substantive': True,
        'input_identity': 'frozen-input', 'question': 'fixture control?', 'exact_missing_or_defect': 'fixture control failed'})
    research = packet(s, 'research-reader')
    result(s, research, directory, repair_plan=plan)
    p = rc.next_packet(s, POLICY, PROFILES)
    data = {'status': 'dispatched', 'native_tool': 'collaboration.followup_task', 'task_id': 'A',
        'agent_id': 'initial-author', 'phase': 'repair', 'packet_id': p['packet_id'],
        'input_identity': 'frozen-input', 'repair_plan_identity': rc.digest(plan),
        'base_packet_id': first['packet_id'], 'base_raw_receipt': s['tasks']['A']['history'][0]['receipt'],
        'requested': p['route']['requested'], 'transport_selected': p['route']['transport_selected']}
    host = write(directory / 'host.json', {'dispatch_accepted': True, **{k: data[k] for k in
        ('native_tool', 'agent_id', 'packet_id', 'task_id', 'input_identity')}})
    data.update(host_call_receipt=host, host_call_receipt_sha256=rc._receipt(host)['sha256'])
    evidence = write(directory / 'followup.json', data)
    return s, first, p, data, evidence

def rejected_atomic(s, operation):
    before = copy.deepcopy(s)
    try:
        operation()
    except rc.ControllerError:
        assert s == before, 'rejection mutated controller state'
    else:
        raise AssertionError('transition unexpectedly admitted')

for index, plan in enumerate(('  exact plan representation  ', {'steps': ['repair fixture'], 'limit': 1})):
    directory = OWN / 'tmp' / ('followup' + str(index))
    s, first, p, data, evidence = initial(directory, plan, ('numeric', 'code')[index])
    preserved = copy.deepcopy(s)
    for field in ('repair_plan_identity', 'input_identity', 'base_packet_id', 'agent_id'):
        changed = {**data, field: 'wrong'}
        bad = write(directory / (field + '.json'), changed)
        rejected_atomic(s, lambda: rc.acknowledge(s, p['packet_id'], 'initial-author', followup_evidence=bad))
    # A recorded blocker followed by an acknowledged but unresolved packet must never qualify.
    unknown = copy.deepcopy(s)
    unknown['packets']['unresolved-author'] = {**unknown['packets'][first['packet_id']], 'packet_id': 'unresolved-author'}
    rejected_atomic(unknown, lambda: rc.acknowledge(unknown, p['packet_id'], 'initial-author', followup_evidence=evidence))
    rc.acknowledge(s, p['packet_id'], 'initial-author', followup_evidence=evidence)
    rejected_atomic(s, lambda: rc.acknowledge(s, p['packet_id'], 'initial-author', followup_evidence=evidence))
    assert s['tasks']['A']['repair_plan'] == plan
    assert s['tasks']['A']['history'][1]['result']['repair_plan'] == plan
    assert s['packets'][p['packet_id']]['continuation']['repair_plan_identity'] == rc.digest(plan)
    for field in ('campaign', 'campaign_identity', 'ultra_repairs', 'ultra_pending', 'turn'):
        assert s[field] == preserved[field]
    for field in ('accounting', 'authors', 'contributors', 'failures', 'attempt', 'history'):
        assert s['tasks']['A'][field] == preserved['tasks']['A'][field]
    assert s['tasks']['OLD'] == preserved['tasks']['OLD']
    assert s['packets'][p['packet_id']]['observed_runtime'] == 'UNKNOWN'
    final = result(s, p, directory, candidate_identity='real-fixture-candidate', validation_evidence=['fixture passes'],
        base_packet_id=first['packet_id'], base_candidate_identity=None, base_raw_receipt=data['base_raw_receipt'])
    rejected_atomic(s, lambda: rc.record(s, final, POLICY))
    review = rc.next_packet(s, POLICY, PROFILES)
    rejected_atomic(s, lambda: rc.acknowledge(s, review['packet_id'], 'initial-author'))
    rejected_atomic(s, lambda: rc.acknowledge(s, review['packet_id'], 'research-reader'))
    rc.acknowledge(s, review['packet_id'], 'fresh-independent-reader')
    result(s, review, directory, candidate_identity='real-fixture-candidate', acceptance_met=True,
        validation_evidence=['fresh fixture review'])
    assert s['tasks']['A']['state'] == 'completed'
    assert s['tasks']['A']['accounting'] == preserved['tasks']['A']['accounting']
    assert s['ultra_repairs'] == preserved['ultra_repairs'] and s['ultra_pending'] == preserved['ultra_pending']
    passed('initial-failure end-to-end, exact plan, atomic bad bindings, UNKNOWN, duplicate, independent review: ' + str(index))

for index, (reason, prohibited, legacy) in enumerate((('owner restriction', True, False),
        ('EXHAUSTED monthly quota', False, False), ('monthly quota refusal', False, True), ('temporary outage', False, False))):
    s = fresh(); p = rc.next_packet(s, POLICY, PROFILES)
    directory = OWN / 'tmp' / ('transport' + str(index))
    raw = write(directory / 'refused.json', {'reason': reason})
    rc.launch_failed(s, p['packet_id'], raw, 'transport', reason, prohibited)
    if legacy:
        del s['tasks']['A']['hold']['retry_prohibited']
    ev = write(directory / 'restore.json', {'kind': 'prelaunch_transport', 'packet_id': p['packet_id'],
        'before': {'transport': 'unavailable'}, 'after': {'transport': 'available'},
        'scope': 'same transport fixture', 'discriminator': 'actual restored availability'})
    if index < 3:
        rejected_atomic(s, lambda: rc.resume(s, 'A', ev, 'frozen-input'))
    else:
        before = copy.deepcopy(s)
        rc.resume(s, 'A', ev, 'frozen-input')
        assert s['tasks']['A']['state'] == 'ready'
        assert s['tasks']['A']['attempt'] == before['tasks']['A']['attempt']
        assert s['tasks']['A']['accounting'] == before['tasks']['A']['accounting']
        assert s['packets'] == before['packets']
    passed('transport refusal and restoration ' + str(index))

# Mid-operation pointer switching must not move this operation to a second state.
directory = OWN / 'tmp' / 'pin-race'; directory.mkdir(parents=True, exist_ok=True)
target = directory / 'durable' / 'state.json'; other = directory / 'other.json'
s = fresh(); p = packet(s, 'cli-fixture-author')
rc.save(target, s); rc.save(other, {'untouched': 'other target'})
middle = directory / 'middle'; middle.symlink_to(target)
alias = directory / 'active'; alias.symlink_to(middle)
outcome = {'packet_id': p['packet_id'], 'task_id': 'A', 'input_identity': 'frozen-input',
    'agent_id': 'cli-fixture-author', 'outcome': 'success', 'candidate_identity': 'cli-new', 'validation_evidence': ['fixture']}
outcome['raw_receipt'] = write(directory / 'raw.json', {'raw': 'fixture actual outcome'})
result_path = write(directory / 'result.json', outcome)
original_read = Path.read_text; switched = []
def switch_alias(path, *args, **kwargs):
    text = original_read(path, *args, **kwargs)
    if path == target and not switched:
        middle.unlink(); middle.symlink_to(other); switched.append(True)
    return text
with patch.object(sys, 'argv', ['controller', '--state', str(alias), 'record', '--result', result_path]), \
     patch.object(Path, 'read_text', switch_alias), redirect_stdout(io.StringIO()):
    assert rc.main() == 0
assert switched and alias.is_symlink() and middle.is_symlink()
assert json.loads(target.read_text())['tasks']['A']['phase'] == 'review'
assert json.loads(other.read_text()) == {'untouched': 'other target'}
assert (target.parent / 'state.json.results' / (rc.digest(outcome) + '.json')).is_file()
assert not (directory / 'active.results').exists()
passed('CLI target pinned before read, survives alias switch, sidecar follows original target')

# Save failure leaves durable target and both aliases intact and removes the temporary file.
middle.unlink(); middle.symlink_to(target)
before = target.read_bytes()
with patch.object(rc.os, 'replace', side_effect=OSError('fixture replacement refusal')):
    try:
        rc.save(alias, {'should': 'not commit'})
    except OSError:
        pass
    else:
        raise AssertionError('replace failure was hidden')
assert target.read_bytes() == before and alias.is_symlink() and middle.is_symlink()
assert not list(target.parent.glob('.controller-*'))
passed('atomic save replacement refusal preserves target and aliases')

# Synthetic AST scope controls exercise frozen validator behavior without old evidence replay.
old = 'def parse_table3(x):\n    return x\n\ndef protected(y):\n    return y\n'
rc._cf4_parser_ast(old.encode(), old.replace('return x', 'return x + 1').encode())
try:
    rc._cf4_parser_ast(old.encode(), old.replace('return y', 'return y + 1').encode())
except rc.ControllerError:
    passed('frozen parser AST guard retains non-parser scope')
else:
    raise AssertionError('extra AST edit admitted')

write(OWN / 'INDEPENDENT_CHECKS.json', {'passed': len(checks), 'checks': checks,
    'scope': 'synthetic metadata and AST controls only; no actual dispatch or scientific producer'})
