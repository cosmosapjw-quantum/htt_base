"""Metadata fixture only. Does not dispatch workers or import numerical sources."""
from pathlib import Path
import copy
import itertools
import json
import sys

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "metadata_fixture"
FIXTURE.mkdir(exist_ok=False)
sys.dont_write_bytecode = True
sys.path.insert(0, "/home/cosmosapjw/Dropbox/bianchi/htt_base/scripts/codex_harness")
import research_controller as rc

packet = json.loads(Path('/mnt/extdrive/workdir/htt_open_data/r30_cf4_pv_dispatch/ACTUAL_RESEARCH_PACKET.json').read_text())
assignment = json.loads(packet['spawn_args']['message'].split('Assignment:\n', 1)[1])
plan = json.loads(Path('/mnt/extdrive/workdir/htt_open_data/r30_cf4_pv_normalization_repair_framing/RESULT.json').read_text())['repair_plan']
policy = rc.load_policy()
profiles = {(r['requested']['model'], r['requested']['effort']) for r in policy['routes'].values()}
key = assignment['spec']['id']
state = rc.initialize({'campaign_id': 'SYNTHETIC_METADATA_ONLY', 'tasks': [copy.deepcopy(assignment['spec'])]}, 'synthetic fixture only')
state['tasks'][key]['accounting'] = {'used_seconds': 244.59277764664455, 'parent_task_id': 'R26-CF4-FINAL-GROUP-CALIBRATION-RESPONSE', 'lifetime_cap_seconds': 600}
state['ultra_repairs']['historical_fixture'] = {'task_id': 'old_fixture'}
original_spec = copy.deepcopy(state['tasks'][key]['spec'])
accounting = copy.deepcopy(state['tasks'][key]['accounting'])
ultra = copy.deepcopy(state['ultra_repairs'])
serial = itertools.count()

def write(label, value):
    path = FIXTURE / (str(next(serial)) + '_' + label + '.json')
    path.write_text(json.dumps(value, indent=2) + '\n')
    return str(path)

def result(p, agent, outcome='success', **fields):
    r = {'synthetic_only': True, 'packet_id': p['packet_id'], 'task_id': key,
         'input_identity': p['input_identity'], 'agent_id': agent, 'outcome': outcome, **fields}
    r['raw_receipt'] = write('RAW_NOT_ACTUAL', r)
    return r

def rejection(call, expected):
    before = copy.deepcopy(state)
    try:
        call()
    except rc.ControllerError as exc:
        assert expected in str(exc), str(exc)
        assert state == before
        return str(exc)
    raise AssertionError('unexpected acceptance')

author, researcher, reviewer = 'SYNTHETIC_author', 'SYNTHETIC_researcher', 'SYNTHETIC_reviewer'
first = rc.next_packet(state, policy, profiles)
rc.acknowledge(state, first['packet_id'], author)
rc.record(state, result(first, author, 'blocker', candidate_identity=None, issue=assignment['issue']), policy)
research = rc.next_packet(state, policy, profiles)
rc.acknowledge(state, research['packet_id'], researcher)
rc.record(state, result(research, researcher, candidate_identity=None, repair_plan=plan), policy)
repair = rc.next_packet(state, policy, profiles)
base_raw = copy.deepcopy(state['tasks'][key]['history'][0]['receipt'])
numeric = write('EXECUTION_INPUT_NO_GO', {'synthetic_only': True, 'controller_go': False,
    'input_identity': repair['input_identity'], 'packet_id': repair['packet_id']})
lineage = rc._receipt(write('EXECUTION_LINEAGE', {'synthetic_only': True,
    'controller_input_identity': repair['input_identity'], 'execution_input': rc._receipt(numeric),
    'repair_plan_identity': rc.digest(plan), 'base_packet_id': first['packet_id'], 'base_raw_receipt': base_raw}))
follow = {'synthetic_only': True, 'status': 'dispatched', 'native_tool': 'collaboration.followup_task',
    'task_id': key, 'agent_id': author, 'phase': 'repair', 'packet_id': repair['packet_id'],
    'input_identity': repair['input_identity'], 'repair_plan_identity': rc.digest(plan),
    'base_packet_id': first['packet_id'], 'base_candidate_identity': None, 'base_raw_receipt': base_raw,
    'requested': repair['route']['requested'], 'transport_selected': repair['route']['transport_selected'],
    'execution_lineage': lineage}
host = rc._receipt(write('HOST_CALL_NOT_ACTUAL', {'synthetic_only': True, 'dispatch_accepted': True,
    **{k: follow[k] for k in ('native_tool', 'task_id', 'agent_id', 'packet_id', 'input_identity', 'execution_lineage')}}))
follow.update(host_call_receipt=host['path'], host_call_receipt_sha256=host['sha256'])
bad = write('STALE_PLAN', {**follow, 'repair_plan_identity': 'wrong'})
negative = {'stale_plan': rejection(lambda: rc.acknowledge(state, repair['packet_id'], author, followup_evidence=bad), 'stale followup assignment/plan')}
rc.acknowledge(state, repair['packet_id'], author, followup_evidence=write('FOLLOWUP_NOT_ACTUAL', follow))
fields = {'candidate_identity': 'SYNTHETIC_candidate', 'validation_evidence': ['metadata fixture only'],
    'base_packet_id': first['packet_id'], 'base_candidate_identity': None, 'base_raw_receipt': base_raw,
    'execution_lineage': lineage}
wrong = result(repair, author, **fields)
wrong['input_identity'] = 'wrong'
negative['changed_controller_input'] = rejection(lambda: rc.record(state, wrong, policy), 'stale task/input identity')
rc.record(state, result(repair, author, **fields), policy)
review = rc.next_packet(state, policy, profiles)
negative['self_review'] = rejection(lambda: rc.acknowledge(state, review['packet_id'], author), 'reviewer must be independent')
rc.acknowledge(state, review['packet_id'], reviewer)
rc.record(state, result(review, reviewer, candidate_identity='SYNTHETIC_candidate', acceptance_met=True,
    validation_evidence=['metadata lifecycle only; no scientific evidence'], qualified_products=[]), policy)
task = state['tasks'][key]
assert task['spec'] == original_spec and task['accounting'] == accounting and state['ultra_repairs'] == ultra
assert task['state'] == 'completed' and len(task['history']) == 4 and len(task['failures']) == 1
for event in task['history']:
    assert rc._receipt(event['receipt']['path']) == event['receipt']
receipt = {'status': 'PURE_METADATA_LIFECYCLE_ACCEPTED', 'not_actual_dispatch': True,
    'not_scientific_pass': True, 'numeric_commands_started': 0, 'production_state_mutated': False,
    'task_spec_unchanged': True, 'accounting_unchanged': True, 'ultra_history_unchanged': True,
    'first_failure_retained': True, 'all_four_raw_receipts_still_match': True,
    'path': 'execute blocker -> research approval -> same-author repair ACK -> candidate record -> independent review ACK -> review record',
    'negative_checks_atomic': negative,
    'limitation': 'Companion scientific/source semantics need host and independent review validation; controller acceptance alone does not validate arbitrary extra fields.'}
(ROOT / 'LIFECYCLE_CHECK_FINAL.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
