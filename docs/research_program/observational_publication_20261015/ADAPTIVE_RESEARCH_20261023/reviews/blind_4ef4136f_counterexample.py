"""Source-only fixture: all native acknowledgements below are simulated."""
import copy
import json
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, '/home/cosmosapjw/Dropbox/bianchi/htt_base/scripts/codex_harness')
import research_controller as rc
from test_research_controller import POLICY, PROFILES, task

with tempfile.TemporaryDirectory(prefix='r25-blind-fixture-') as tmp:
    root = Path(tmp)
    counter = 0
    state = rc.initialize({'campaign_id': 'same-origin-two-distinct-issues',
        'approved_scientific_repairs': ['old-budget'],
        'tasks': [task('A', approved_repair_id='old-budget')]}, 'owner')
    def launch():
        global counter
        counter += 1
        packet = rc.next_packet(state, POLICY, PROFILES)
        rc.acknowledge(state, packet['packet_id'], 'fixture-agent-' + str(counter))
        return packet
    def record(packet, **fields):
        raw = root / ('raw-' + str(counter) + '.json')
        result = {'packet_id': packet['packet_id'], 'task_id': packet['task_id'],
            'input_identity': packet['input_identity'], 'agent_id': 'fixture-agent-' + str(counter),
            'raw_receipt': str(raw), **fields}
        raw.write_text(json.dumps(result))
        rc.record(state, result, POLICY)
        return result
    issue1 = {'class': 'numeric', 'question': 'Does factorization preserve positive definiteness?',
        'exact_missing_or_defect': 'negative covariance eigenvalue', 'input_identity': 'input-v1',
        'substantive': True, 'high_consequence': True, 'risk': 'false covariance admission'}
    issue2 = {'class': 'numeric', 'question': 'Does full tensor support retain the null direction?',
        'exact_missing_or_defect': 'rank loss in a distinct tensor-support map',
        'input_identity': 'input-v1', 'substantive': True,
        'counterexample': {'matrix': [[1, 0], [0, 0]], 'expected_rank': 1, 'observed_rank': 0}}
    record(launch(), outcome='blocker', issue=issue1)
    ultra = launch()
    assert ultra['phase'] == 'escalation'
    assert state['packets'][ultra['packet_id']]['launch_performed'] is True
    record(ultra, outcome='success', repair_plan='Repair covariance factorization')
    record(launch(), outcome='blocker', issue=issue2)
    assert state['tasks']['A']['state'] == 'held'
    assert set(state['ultra_repairs']) == {'old-budget'}
    assert not state['ultra_pending']
    rc.enable_adaptive(state, 'owner distinct issue research')
    discovery = launch()
    delta = {'kind': 'validation_counterexample',
        'before': {'operator': 'covariance-factorization', 'rank': 2},
        'after': {'operator': 'tensor-support-map', 'expected_rank': 1, 'observed_rank': 0},
        'scope': 'distinct tensor support issue', 'discriminator': 'independent tensor rank calculation'}
    auth = {'repair_id': 'new-budget', 'issue': issue2,
        'issue_identity': rc.digest(rc._semantic_meaning(issue2)),
        'operative_question': issue2['question'], 'scope': delta['scope'], 'origin_task_id': 'A',
        'origin_issue_identity': rc.digest(rc._semantic_meaning(issue2)),
        'claim_target': state['tasks']['A']['spec']['acceptance'], 'semantic_delta': delta,
        'cumulative_budget_link': state['campaign_identity']}
    evidence = root / 'counterexample.json'
    evidence.write_text(json.dumps(issue2['counterexample']))
    auth['evidence_refs'] = [str(evidence)]
    bindings = {key: auth[key] for key in ('origin_task_id', 'origin_issue_identity',
        'issue_identity', 'claim_target', 'cumulative_budget_link')}
    decision = record(discovery, outcome='no_action', examined_branches=['A'],
        methods=['Full tensor rank comparison'], source_refs=[str(evidence)],
        exact_residuals=['Distinct bounded tensor issue requires allowance'],
        decision='distinct_scoped_issue', semantic_delta_identity=rc.digest(rc._semantic_projection(delta)),
        **bindings)
    auth['research_decision_receipt'] = decision['raw_receipt']
    before = copy.deepcopy(state)
    try:
        rc.authorize_repair(state, auth, 'owner authorizes genuine distinct issue')
    except rc.ControllerError as exc:
        print('AUTHORIZATION_REJECTED:', exc)
    else:
        print('AUTHORIZATION_ACCEPTED')
    print('original_issue_acknowledged_ultra:', state['ultra_repairs']['old-budget'])
    print('new_issue_ultra_count:', int('new-budget' in state['ultra_repairs']))
    print('state_unchanged_after_rejection:', state == before)
