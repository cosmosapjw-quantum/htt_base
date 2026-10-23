"""Adaptive planning never counts as science, and never replays unknown work."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from test_research_controller import POLICY, PROFILES, task
import research_controller as rc

ROOT = Path(__file__).resolve().parents[2]
LIVE = ROOT / '.agent-harness/runtime/r23-continuous/r25/STATE_BEFORE.json'


class AdaptiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.receipt = Path(self.tmp.name) / 'actual.json'
        self.receipt.write_text('{"actual":"bounded source investigation"}')
        self.state = rc.initialize({'campaign_id': 'bounded', 'tasks': [task('held')]}, 'owner')
        self.state['tasks']['held'].update(state='held', hold={'exact_missing_or_defect': 'cohort'})
        rc.enable_adaptive(self.state, 'current owner adaptive methods scope')

    def result(self, p, **extra):
        return {'packet_id': p['packet_id'], 'task_id': p['task_id'],
                'input_identity': p['input_identity'], 'agent_id': 'actual-discovery-agent',
                'raw_receipt': str(self.receipt), 'outcome': 'no_action',
                'examined_branches': ['held'], 'methods': ['matched-cohort nuisance projection'],
                'source_refs': [str(self.receipt)], 'exact_residuals': ['cohort payload unavailable'], **extra}

    def launch(self):
        p = rc.next_packet(self.state, POLICY, PROFILES)
        rc.acknowledge(self.state, p['packet_id'], 'actual-discovery-agent')
        return p

    def test_idempotence_no_selftrigger_and_no_unknown_replay(self):
        p = rc.next_packet(self.state, POLICY, PROFILES)
        f = rc.adaptive_fingerprint(self.state)
        self.assertEqual(p, rc.next_packet(self.state, POLICY, PROFILES))
        self.assertEqual(f, rc.adaptive_fingerprint(self.state))
        rc.acknowledge(self.state, p['packet_id'], 'actual-discovery-agent')
        self.assertNotIn('spawn_args', rc.next_packet(self.state, POLICY, PROFILES))
        with self.assertRaises(rc.ControllerError):
            rc.acknowledge(self.state, p['packet_id'], 'another')
        rc.record(self.state, self.result(p), POLICY)
        self.state['turn'] += 10
        self.state['events'].append({'type': 'arbitrary planning'})
        rc.enable_adaptive(self.state, 'same authorization again')
        self.assertEqual(f, rc.adaptive_fingerprint(self.state))
        self.assertNotIn('spawn_args', rc.next_packet(self.state, POLICY, PROFILES))
        self.assertEqual(rc.summary(self.state)['completed'], 0)
        self.assertEqual(rc.summary(self.state)['planning']['checkpoints'], 1)

    def test_refused_discovery_does_not_fabricate_agent_or_repeat_transport(self):
        p = rc.next_packet(self.state, POLICY, PROFILES)
        rc.launch_failed(self.state, p['packet_id'], str(self.receipt), 'transport', 'quota exhausted')
        nxt = rc.next_packet(self.state, POLICY, PROFILES)
        self.assertEqual(nxt['status'], 'HOLD_TRANSPORT_UNAVAILABLE')
        self.assertNotIn('spawn_args', nxt)
        self.assertFalse(self.state['adaptive']['packets'][p['packet_id']]['launch_performed'])

    def test_no_discovery_while_scientific_packet_pending(self):
        self.state['tasks']['held']['state'] = 'ready'
        p = rc.next_packet(self.state, POLICY, PROFILES)
        self.assertNotEqual(p['phase'], 'discovery')
        self.assertEqual(p, rc.next_packet(self.state, POLICY, PROFILES))
        rc.acknowledge(self.state, p['packet_id'], 'worker')
        self.assertNotIn('spawn_args', rc.next_packet(self.state, POLICY, PROFILES))
        self.assertEqual(self.state['adaptive']['packets'], {})

    def test_new_actual_result_or_explicit_method_reopens(self):
        p = self.launch()
        rc.record(self.state, self.result(p), POLICY)
        before = rc.adaptive_fingerprint(self.state)
        self.state['tasks']['held']['history'].append({'result': {'counterexample': 'changed actual observation'}})
        self.assertNotEqual(before, rc.adaptive_fingerprint(self.state))
        self.assertIn('spawn_args', rc.next_packet(self.state, POLICY, PROFILES))
        delta = Path(self.tmp.name) / 'delta.json'
        delta.write_text(json.dumps({'kind': 'method', 'before': {'method': 'diagonal'},
            'after': {'method': 'full covariance'}, 'discriminator': 'residual', 'scope': 'cohort',
            'source_refs': [str(self.receipt)]}))
        rc.adaptive_evidence(self.state, str(delta))
        with self.assertRaises(rc.ControllerError):
            rc.adaptive_evidence(self.state, str(delta))

    def test_fake_frontier_and_invalid_source_rejected_atomically(self):
        p = self.launch()
        original = copy.deepcopy(self.state)
        with self.assertRaises(rc.ControllerError):
            rc.record(self.state, self.result(p, outcome='proposal', frontier={'frontier_id': 'fake',
                      'tasks': [{'id': 'fake', 'input_sources': ['/missing/source']}]}), POLICY)
        self.assertEqual(original, self.state)
        with self.assertRaises(rc.ControllerError):
            rc.record(self.state, self.result(p, source_refs=['invented-source']), POLICY)
        self.assertEqual(original, self.state)

    def test_proposal_requires_real_lower_tier_execution(self):
        p = self.launch()
        new = task('new', approved_repair_id=None, implementation_route='general_code',
            input_sources=[str(self.receipt)], owned_paths=['scoped/'], requires={'all': []},
            contract_origin='new_conditional_research', promotes_original_acceptance=False,
            semantic_delta={'kind': 'method', 'before': {'method': 'diagonal'},
                'after': {'method': 'full covariance'}, 'discriminator': 'residual', 'scope': 'cohort'})
        rc.record(self.state, self.result(p, outcome='proposal', frontier={'frontier_id': 'bounded-new', 'tasks': [new]}), POLICY)
        self.assertEqual(self.state['tasks']['new']['state'], 'ready')
        self.assertIn('actual-discovery-agent', self.state['tasks']['new']['contributors'])
        nxt = rc.next_packet(self.state, POLICY, PROFILES)
        self.assertEqual(nxt['task_id'], 'new')
        self.assertEqual(nxt['phase'], 'execute')
        self.assertEqual(rc.summary(self.state)['completed'], 0)

    @unittest.skipUnless(LIVE.is_file(), 'owner live snapshot unavailable')
    def test_actual_stalled_snapshot_preserves_historical_identity(self):
        state = json.loads(LIVE.read_text())
        baseline = copy.deepcopy(state)
        self.assertEqual(len(state['tasks']), 62)
        self.assertNotIn('spawn_args', rc.next_packet(state, POLICY, PROFILES))
        rc.enable_adaptive(state, 'current owner R25 adaptive continuation')
        p = rc.next_packet(state, POLICY, PROFILES)
        self.assertEqual(p['phase'], 'discovery')
        self.assertEqual(p['route']['requested'], {'model': 'gpt-6-astra', 'effort': 'xhigh'})
        for key in baseline:
            self.assertEqual(state[key], baseline[key], key)
        self.assertEqual(len(state['campaign']['tasks']), 48)
        self.assertIn('R23', json.dumps(state['ultra_repairs']))




class BlindRepairTests(unittest.TestCase):
    """Exact as-shipped blind counterexamples, with simulated host receipts only."""
    import test_research_controller as base_tests
    import test_research_controller_frontier as frontier_tests
    setUp = base_tests.ControllerTests.setUp
    state = base_tests.ControllerTests.state
    launch = base_tests.ControllerTests.launch
    result = base_tests.ControllerTests.result
    issue = base_tests.ControllerTests.issue
    followup_fixture = frontier_tests.FrontierTests.followup_fixture

    def conditional(self, key):
        return self.frontier_tests.spec(key)

    def test_scientific_classification_labels_survive_but_note_only_is_rejected(self):
        rc._semantic_delta({'kind': 'method', 'before': {'classification_labels': ['positive']},
            'after': {'classification_labels': ['negative']}, 'scope': 'test', 'discriminator': 'sign'})
        for key in ('note', 'notes', 'timestamp', 'name', 'metadata', 'input_identity'):
            with self.subTest(key=key), self.assertRaises(rc.ControllerError):
                rc._semantic_delta({'kind': 'method', 'before': {key: 'old'}, 'after': {key: 'new'},
                                    'scope': 'test', 'discriminator': 'naming'})

    def test_same_logical_action_cannot_reset_attempts_via_new_frontier_id(self):
        state = self.state([task('OLD')])
        one = self.conditional('NEW1')
        rc.append_frontier(state, {'frontier_id': 'one', 'tasks': [one]}, 'owner')
        state['tasks']['NEW1'].update(state='held', attempt=7, hold={'exact_missing_or_defect': 'exhausted'})
        old = copy.deepcopy(state)
        two = self.conditional('NEW2')
        with self.assertRaisesRegex(rc.ControllerError, 'logical research action'):
            rc.append_frontier(state, {'frontier_id': 'two', 'tasks': [two]}, 'owner')
        self.assertEqual(old, state)
        two['semantic_delta']['after']['method'] = 'full tensor joint-covariance estimator'
        rc.append_frontier(state, {'frontier_id': 'new-estimator', 'tasks': [two]}, 'owner')
        self.assertEqual(state['tasks']['NEW1'], old['tasks']['NEW1'])
        self.assertIn('NEW2', rc.summary(state)['ready'])

    def authorization_fixture(self, successor=None):
        state = self.state([task('A', approved_repair_id=None), task('OLD')])
        state['ultra_repairs']['R23-COMMON-E1'] = {'task_id': 'OLD', 'agent_id': 'historical'}
        state['tasks']['OLD'].update(state='held', issue=self.issue())
        state['ultra_repairs']['R23-COMMON-E1']['operative_issue_identity'] = rc._operative_issue_identity(self.issue())
        new_issue = self.issue(exact_missing_or_defect='independent tensor-support rank counterexample',
                               question='Does the tensor support map preserve this null direction?')
        state['tasks']['A'].update(issue=new_issue, phase='research')
        scope = 'new tensor rank issue'
        delta = {'kind': 'validation_counterexample', 'before': {'operator': 'scalar support'},
                 'after': {'operator': 'tensor joint support', 'matrix_rank': 0},
                 'scope': scope, 'discriminator': 'rank under exact joint support'}
        receipt = Path(self.tmp.name) / 'counterexample.json'
        receipt.write_text(json.dumps({'observed': [0, 1], 'expected': [0, 0]}))
        auth = {'repair_id': 'R25-DISTINCT-TENSOR', 'issue': new_issue,
                'issue_identity': rc.digest(rc._semantic_meaning(new_issue)),
                'operative_question': new_issue['question'], 'scope': scope,
                'origin_task_id': 'A', 'origin_issue_identity': rc.digest(rc._semantic_meaning(new_issue)),
                'claim_target': state['tasks']['A']['spec']['acceptance'], 'semantic_delta': delta,
                'evidence_refs': [str(receipt)], 'cumulative_budget_link': state['campaign_identity']}
        if successor is not None:
            auth['successor_bindings'] = [{'task_id': successor['id'], 'task_spec_identity': rc.digest(successor),
                'claim_target': successor['acceptance'], 'issue_identity': auth['issue_identity'],
                'semantic_delta_identity': rc.digest(rc._semantic_projection(successor['semantic_delta']))}]
        research = rc.next_packet(state, POLICY, PROFILES)
        rc.acknowledge(state, research['packet_id'], 'actual-readonly-astra-research')
        bindings = {key: auth[key] for key in ('origin_task_id', 'origin_issue_identity', 'issue_identity',
                                              'claim_target', 'cumulative_budget_link')}
        raw = Path(self.tmp.name) / 'actual-astra-research.json'
        result = {'packet_id': research['packet_id'], 'task_id': 'A',
            'input_identity': research['input_identity'], 'agent_id': 'actual-readonly-astra-research',
            'raw_receipt': str(raw), 'outcome': 'success', 'repair_plan': 'Bounded tensor-support comparison',
            'decision': 'distinct_scoped_issue', 'semantic_delta_identity': rc.digest(rc._semantic_projection(delta)),
            **bindings}
        if successor is not None:
            result['successor_bindings'] = auth['successor_bindings']
        raw.write_text(json.dumps(result))
        rc.record(state, result, POLICY)
        auth['research_decision_receipt'] = str(raw)
        return state, auth

    def test_distinct_append_only_repair_authorization_preserves_consumed_budget(self):
        state, auth = self.authorization_fixture()
        old = copy.deepcopy(state)
        rc.authorize_repair(state, auth, 'current owner solver-free scientific repair scope')
        for key in old:
            self.assertEqual(old[key], state[key])
        self.assertIsNone(state['tasks']['A']['spec']['approved_repair_id'])
        self.assertEqual(rc._task_repair_id(state, 'A'), auth['repair_id'])
        self.assertEqual(state['repair_authorizations'][auth['repair_id']]['observed_research_runtime'], 'UNKNOWN')
        with self.assertRaises(rc.ControllerError):
            rc.authorize_repair(state, {**auth, 'repair_id': 'RENAMED'}, 'owner')
        with self.assertRaises(rc.ControllerError):
            rc.authorize_repair(state, {**auth, 'repair_id': 'REPLENISH', 'issue': self.issue(),
                'operative_question': self.issue()['question'],
                'issue_identity': rc.digest(rc._semantic_meaning(self.issue()))}, 'owner')
        new = self.conditional('distinct')
        new['approved_repair_id'] = auth['repair_id']
        with self.assertRaisesRegex(rc.ControllerError, 'origin/successor'):
            rc.append_frontier(state, {'frontier_id': 'distinct', 'tasks': [new]}, 'owner')
        self.assertNotIn(auth['repair_id'], state['ultra_repairs'])
        self.assertNotIn(auth['repair_id'], state['ultra_pending'])
        self.assertEqual(state['ultra_repairs'], old['ultra_repairs'])

    def test_unapproved_current_issue_can_receive_first_authorization_but_prose_alias_cannot(self):
        state, auth = self.authorization_fixture()
        # First authorization is valid although this defect is already the current issue.
        old = copy.deepcopy(state)
        for change in ({'origin_issue_identity': 'stale'}, {'claim_target': 'weakened acceptance'},
                       {'research_decision_receipt': auth['evidence_refs'][0]}):
            with self.assertRaises(rc.ControllerError):
                rc.authorize_repair(state, {**auth, **change}, 'owner')
            self.assertEqual(old, state)
        alias_issue = {**auth['issue'], 'question': 'Paraphrased tensor support query'}
        delta = {**auth['semantic_delta'], 'before': {'question': auth['issue']['question']},
                 'after': {'question': alias_issue['question']}}
        with self.assertRaisesRegex(rc.ControllerError, 'wording alone'):
            rc.authorize_repair(state, {**auth, 'issue': alias_issue, 'operative_question': alias_issue['question'],
                'issue_identity': rc.digest(rc._semantic_meaning(alias_issue)), 'semantic_delta': delta}, 'owner')
        self.assertEqual(old, state)
        rc.authorize_repair(state, auth, 'owner')
        self.assertIn(auth['repair_id'], state['repair_authorizations'])

    def test_registered_current_issue_has_eligible_future_route_without_rewriting_spec(self):
        state, auth = self.authorization_fixture()
        rc.authorize_repair(state, auth, 'owner')
        old_ultra = copy.deepcopy(state['ultra_repairs'])
        repair = self.launch(state)
        self.assertEqual(repair['approved_repair_id'], auth['repair_id'])
        issue = {**auth['issue'], 'high_consequence': True, 'risk': 'False tensor support admission'}
        self.result(state, repair, 'blocker', issue=issue)
        self.assertEqual(state['tasks']['A']['phase'], 'escalation')
        packet = rc.next_packet(state, POLICY, PROFILES)
        self.assertEqual(packet['approved_repair_id'], auth['repair_id'])
        self.assertIn('repair_authorization_identity', packet)
        self.assertEqual(state['ultra_repairs'], old_ultra)
        self.assertIsNone(state['tasks']['A']['spec']['approved_repair_id'])

    def test_registered_held_issue_resume_retains_frozen_approved_id(self):
        state, auth = self.authorization_fixture()
        rc.authorize_repair(state, auth, 'owner')
        state['tasks']['A']['state'] = 'held'
        delta = Path(self.tmp.name) / 'held-method-delta.json'
        delta.write_text(json.dumps(auth['semantic_delta']))
        rc.resume(state, 'A', str(delta), 'input-v2', auth['repair_id'])
        self.assertIsNone(state['tasks']['A']['spec']['approved_repair_id'])
        self.assertEqual(state['tasks']['A']['active_repair_id'], auth['repair_id'])
        self.assertEqual(state['tasks']['A']['phase'], 'research')

    def test_input_wrapper_path_or_metadata_cannot_reset_same_action(self):
        state = self.state([task('OLD')])
        source = Path(self.tmp.name) / 'source.json'
        copied = Path(self.tmp.name) / 'renamed-wrapper.json'
        source.write_text('{"cohort":"same","metadata":"first wrapper"}')
        copied.write_bytes(source.read_bytes())
        first = self.conditional('NEW1')
        first['input_sources'] = [str(source)]
        rc.append_frontier(state, {'frontier_id': 'one', 'tasks': [first]}, 'owner')
        state['tasks']['NEW1'].update(state='held', attempt=7)
        new = self.conditional('NEW2')
        new['input_sources'] = [str(copied)]
        for content in (source.read_text(), '{"cohort":"same","metadata":"changed wrapper only"}'):
            copied.write_text(content)
            with self.assertRaisesRegex(rc.ControllerError, 'logical research action'):
                rc.append_frontier(state, {'frontier_id': 'renamed', 'tasks': [new]}, 'owner')
        new['semantic_delta']['after']['source_release'] = 'genuine new selected cohort release'
        rc.append_frontier(state, {'frontier_id': 'new-scientific-source', 'tasks': [new]}, 'owner')
        self.assertEqual(state['tasks']['NEW1']['attempt'], 7)

    def test_second_distinct_deterministic_counterexample_does_not_need_new_ultra(self):
        state = self.state([task('A')])
        self.result(state, self.launch(state))
        self.result(state, self.launch(state), 'blocker',
                    issue=self.issue(high_consequence=True, risk='False scientific support'))
        ultra = self.launch(state)
        self.assertEqual(ultra['phase'], 'escalation')
        self.result(state, ultra, repair_plan='Bounded relative whitening')
        self.result(state, self.launch(state), candidate_identity='c2')
        issue1 = self.issue(exact_missing_or_defect='first concrete original-zero underflow')
        self.result(state, self.launch(state), 'blocker', candidate_identity='c2', issue=issue1,
                    repair_plan='Check original zero first')
        self.result(state, self.launch(state), candidate_identity='c3')
        issue2 = self.issue(exact_missing_or_defect='second concrete tensor rank-one overflow')
        counterexample = {'matrix': [[1e308, 1e308]], 'expected_rank': 1, 'observed_rank': 0}
        self.result(state, self.launch(state), 'blocker', candidate_identity='c3', issue=issue2,
                    counterexample=counterexample, repair_plan='Rescale tensor support before rank test')
        self.assertEqual(state['tasks']['A']['phase'], 'repair')
        self.assertEqual(len(state['tasks']['A']['targeted_repairs']), 2)
        self.assertEqual(len(state['ultra_repairs']), 1)
        history_len = len(state['tasks']['A']['history'])
        self.result(state, self.launch(state), candidate_identity='c4')
        self.result(state, self.launch(state), 'blocker', candidate_identity='c4', issue=issue2,
                    counterexample=counterexample, repair_plan='Rescale tensor support before rank test')
        self.assertEqual(state['tasks']['A']['state'], 'held')
        self.assertEqual(len(state['tasks']['A']['targeted_repairs']), 2)
        self.assertGreater(len(state['tasks']['A']['history']), history_len)
        self.assertEqual(len(state['ultra_repairs']), 1)

    def test_nonexternal_input_research_stall_leads_to_adaptive_method_search(self):
        state = self.state([task('A', kind='input')])
        issue = self.issue(**{'class': 'input', 'true_external': False})
        self.result(state, self.launch(state), 'blocker', issue=issue)
        self.assertEqual(state['tasks']['A']['phase'], 'research')
        self.result(state, self.launch(state), 'blocker', issue=issue)
        self.assertEqual(state['tasks']['A']['state'], 'held')
        rc.enable_adaptive(state, 'current owner new methods discovery')
        self.assertEqual(rc.next_packet(state, POLICY, PROFILES)['phase'], 'discovery')

    def test_dispatch_followup_ack_precedes_result_and_keeps_unknown_outstanding(self):
        state, author, repair, agent, evidence, data = self.followup_fixture()
        Path(data['raw_receipt']).unlink()  # Result does not exist when the host acknowledges dispatch.
        data = {k: v for k, v in data.items() if k not in
                {'candidate_identity', 'raw_receipt', 'raw_receipt_sha256'}}
        host = Path(self.tmp.name) / 'host-followup-call.json'
        host.write_text(json.dumps({**data, 'dispatch_accepted': True}))
        data.update(status='dispatched', host_call_receipt=str(host),
                    host_call_receipt_sha256=rc._receipt(str(host))['sha256'],
                    requested=repair['route']['requested'],
                    transport_selected=repair['route']['transport_selected'])
        evidence.write_text(json.dumps(data))
        old = copy.deepcopy(state)
        for change in ({'base_candidate_identity': 'stale'}, {'repair_plan_identity': 'stale'},
                       {'requested': {'model': 'gpt-6-astra', 'effort': 'ultra'}}):
            evidence.write_text(json.dumps({**data, **change}))
            with self.assertRaises(rc.ControllerError):
                rc.acknowledge(state, repair['packet_id'], agent, followup_evidence=str(evidence))
            self.assertEqual(old, state)
        evidence.write_text(json.dumps(data))
        rc.acknowledge(state, repair['packet_id'], agent, followup_evidence=str(evidence))
        self.assertEqual(state['tasks']['A']['state'], 'running')
        self.assertNotIn('spawn_args', rc.next_packet(state, POLICY, PROFILES))
        self.assertEqual(state['packets'][repair['packet_id']]['observed_runtime'], 'UNKNOWN')
        result = {'packet_id': repair['packet_id'], 'task_id': 'A', 'agent_id': agent,
            'input_identity': 'input-v1', 'outcome': 'success', 'candidate_identity': 'candidate-v2',
            'base_packet_id': author['packet_id'], 'base_candidate_identity': 'candidate-v1',
            'validation_evidence': ['finite independent reference']}
        raw = Path(self.tmp.name) / 'later-native-outcome.json'
        raw.write_text(json.dumps(result))
        result['raw_receipt'] = str(raw)
        with self.assertRaises(rc.ControllerError):
            rc.record(state, {**result, 'candidate_identity': 'candidate-v1'}, POLICY)
        rc.record(state, result, POLICY)
        review = rc.next_packet(state, POLICY, PROFILES)
        with self.assertRaises(rc.ControllerError):
            rc.acknowledge(state, review['packet_id'], agent)
        rc.acknowledge(state, review['packet_id'], 'fresh-disjoint-review')
        self.result(state, review, candidate_identity='candidate-v2', acceptance_met=True)
        self.assertEqual(state['tasks']['A']['state'], 'completed')

    def test_fresh_session_hook_reads_only_host_installed_active_pointer(self):
        import subprocess
        import sys
        directory = Path(self.tmp.name) / 'hook-root'
        hooks = directory / '.codex/hooks'
        hooks.mkdir(parents=True)
        hook = hooks / 'session_start_context.py'
        hook.write_bytes((ROOT / '.codex/hooks/session_start_context.py').read_bytes())
        def fresh():
            proc = subprocess.run([sys.executable, str(hook)], text=True, capture_output=True, check=True)
            return json.loads(proc.stdout)['hookSpecificOutput']['additionalContext']
        self.assertIn('No active-controller pointer', fresh())
        runtime = directory / '.agent-harness/runtime'
        runtime.mkdir(parents=True)
        state = self.state([task('A')])
        p = rc.next_packet(state, POLICY, PROFILES)
        state_path = runtime / 'STATE.json'
        state_path.write_text(json.dumps(state))
        pointer = runtime / 'ACTIVE_CONTROLLER.json'
        pointer.write_text(json.dumps({'state_path': str(state_path), 'campaign_id': state['campaign_id'],
                                      'campaign_identity': state['campaign_identity']}))
        before = state_path.read_bytes(), pointer.read_bytes()
        text = fresh()
        self.assertIn(p['packet_id'], text)
        self.assertIn('Reconcile every planned packet', text)
        self.assertEqual(before, (state_path.read_bytes(), pointer.read_bytes()))
        rc.acknowledge(state, p['packet_id'], 'actual-running-unknown')
        state_path.write_text(json.dumps(state))
        text = fresh()
        self.assertIn('actual-running-unknown', text)
        self.assertIn('never replayed', text)
        self.assertLessEqual(len(text), 12000)
        pointer.write_text(json.dumps({'state_path': str(state_path), 'campaign_id': 'wrong',
                                      'campaign_identity': state['campaign_identity']}))
        self.assertIn('unavailable or invalid', fresh())


    def test_registered_repair_cannot_be_borrowed_by_other_origin_resume_or_reservation(self):
        state, auth = self.authorization_fixture()
        rc.authorize_repair(state, auth, 'owner')
        delta = Path(self.tmp.name) / 'borrowed-delta.json'
        delta.write_text(json.dumps(auth['semantic_delta']))
        old = copy.deepcopy(state)
        with self.assertRaisesRegex(rc.ControllerError, 'origin/successor'):
            rc.resume(state, 'OLD', str(delta), 'input-v2', auth['repair_id'])
        self.assertEqual(state, old)
        # Imported/forged active IDs cannot bypass reservation or launch guards.
        state['tasks']['OLD'].update(state='ready', phase='research', last_turn=-1000)
        packet = rc.next_packet(state, POLICY, PROFILES)
        rc.acknowledge(state, packet['packet_id'], 'old-branch-research')
        state['tasks']['OLD']['active_repair_id'] = auth['repair_id']
        old = copy.deepcopy(state)
        with self.assertRaisesRegex(rc.ControllerError, 'origin/successor'):
            self.result(state, packet, 'blocker',
                        issue=self.issue(high_consequence=True, risk='Old consumed scalar issue'))
        self.assertEqual(state, old)
        self.assertNotIn(auth['repair_id'], state['ultra_pending'])
        self.assertNotIn(auth['repair_id'], state['ultra_repairs'])

    def test_registered_repair_cannot_be_borrowed_at_escalation_ack(self):
        state, auth = self.authorization_fixture()
        rc.authorize_repair(state, auth, 'owner')
        state['tasks']['OLD'].update(state='ready', phase='escalation', last_turn=-1000)
        packet = rc.next_packet(state, POLICY, PROFILES)
        state['tasks']['OLD']['active_repair_id'] = auth['repair_id']
        old = copy.deepcopy(state)
        with self.assertRaisesRegex(rc.ControllerError, 'origin/successor'):
            rc.acknowledge(state, packet['packet_id'], 'cannot-borrow-authorized-ultra')
        self.assertEqual(state, old)

    def test_origin_repair_semantic_delta_and_claim_are_bound_before_resume(self):
        state, auth = self.authorization_fixture()
        rc.authorize_repair(state, auth, 'owner')
        state['tasks']['A']['state'] = 'held'
        changed = copy.deepcopy(auth['semantic_delta'])
        changed['after']['operator'] = 'different unreviewed operator'
        delta = Path(self.tmp.name) / 'unreviewed-method.json'
        delta.write_text(json.dumps(changed))
        old = copy.deepcopy(state)
        with self.assertRaisesRegex(rc.ControllerError, 'semantic delta changed'):
            rc.resume(state, 'A', str(delta), 'input-v2', auth['repair_id'])
        self.assertEqual(state, old)
        state['tasks']['A']['spec']['acceptance'] = 'weakened target'
        delta.write_text(json.dumps(auth['semantic_delta']))
        old = copy.deepcopy(state)
        with self.assertRaisesRegex(rc.ControllerError, 'claim target changed'):
            rc.resume(state, 'A', str(delta), 'input-v2', auth['repair_id'])
        self.assertEqual(state, old)

    def test_only_explicitly_decided_exact_successor_can_share_allowance(self):
        successor = self.conditional('BOUND-SUCCESSOR')
        successor['approved_repair_id'] = 'R25-DISTINCT-TENSOR'
        state, auth = self.authorization_fixture(successor)
        rc.authorize_repair(state, auth, 'owner')
        changed = copy.deepcopy(successor)
        changed['acceptance'] = 'weakened successor acceptance'
        old = copy.deepcopy(state)
        with self.assertRaisesRegex(rc.ControllerError, 'successor spec'):
            rc.append_frontier(state, {'frontier_id': 'changed-target', 'tasks': [changed]}, 'owner')
        self.assertEqual(state, old)
        rc.append_frontier(state, {'frontier_id': 'explicit-successor', 'tasks': [successor]}, 'owner')
        state['tasks'][successor['id']]['last_turn'] = -1000
        state['tasks']['A']['last_turn'] = 1000
        packet = self.launch(state)
        self.assertEqual(packet['task_id'], successor['id'])
        self.result(state, packet, 'blocker',
                    issue={**auth['issue'], 'high_consequence': True, 'risk': 'Exact authorized tensor issue'})
        self.assertEqual(state['ultra_pending'][auth['repair_id']]['task_id'], successor['id'])
        escalation = rc.next_packet(state, POLICY, PROFILES)
        rc.acknowledge(state, escalation['packet_id'], 'bound-successor-astra-ultra-fixture')
        self.assertEqual(state['ultra_repairs'][auth['repair_id']]['task_id'], successor['id'])
        self.assertIn('R23-COMMON-E1', state['ultra_repairs'])

    def test_registered_successor_records_new_defect_without_funding_it(self):
        successor = self.conditional('BOUND-SUCCESSOR')
        successor['approved_repair_id'] = 'R25-DISTINCT-TENSOR'
        state, auth = self.authorization_fixture(successor)
        rc.authorize_repair(state, auth, 'owner')
        rc.append_frontier(state, {'frontier_id': 'successor-new-defect', 'tasks': [successor]}, 'owner')
        state['tasks'][successor['id']]['last_turn'] = -1000
        packet = self.launch(state)
        self.result(state, packet, 'blocker', issue=self.issue(
            exact_missing_or_defect='genuinely different observed support-domain defect',
            high_consequence=True, risk='New unrelated question needs its own research'))
        self.assertEqual(state['tasks'][successor['id']]['phase'], 'research')
        self.assertNotIn(auth['repair_id'], state['ultra_pending'])
        self.assertNotIn(auth['repair_id'], state['ultra_repairs'])
        self.assertEqual(len(state['tasks'][successor['id']]['history']), 1)

    def test_same_batch_aliases_rejected_atomically(self):
        state = self.state([task('OLD')])
        before = copy.deepcopy(state)
        with self.assertRaisesRegex(rc.ControllerError, 'logical research action'):
            rc.append_frontier(state, {'frontier_id': 'batch-aliases',
                'tasks': [self.conditional('NEW1'), self.conditional('NEW2')]}, 'owner')
        self.assertEqual(state, before)

    def test_no_action_cannot_suppress_unexamined_assigned_branch(self):
        state = self.state([task('A'), task('B')])
        for value in state['tasks'].values():
            value['state'] = 'held'
        rc.enable_adaptive(state, 'owner')
        packet = rc.next_packet(state, POLICY, PROFILES)
        rc.acknowledge(state, packet['packet_id'], 'actual-discovery-agent')
        receipt = Path(self.tmp.name) / 'discovery.json'
        receipt.write_text('{"actual":"source intake"}')
        result = {'packet_id': packet['packet_id'], 'task_id': packet['task_id'],
            'input_identity': packet['input_identity'], 'agent_id': 'actual-discovery-agent',
            'raw_receipt': str(receipt), 'outcome': 'no_action', 'examined_branches': ['A'],
            'methods': ['bounded cohort projection'], 'source_refs': [str(receipt)],
            'exact_residuals': ['held A source gap']}
        before = copy.deepcopy(state)
        with self.assertRaisesRegex(rc.ControllerError, 'every exact assigned eligible branch'):
            rc.record(state, result, POLICY)
        self.assertEqual(state, before)
        self.assertEqual(packet['eligible_branches'], ['A', 'B'])
        rc.record(state, {**result, 'examined_branches': ['A', 'B'],
                         'exact_residuals': ['held A source gap', 'held B method gap']}, POLICY)
        self.assertNotIn('spawn_args', rc.next_packet(state, POLICY, PROFILES))

    def restoration_fixture(self, reason='native capacity temporarily unavailable', prohibited=False):
        state = self.state([task('A')])
        state['tasks']['A']['state'] = 'held'
        rc.enable_adaptive(state, 'owner')
        packet = rc.next_packet(state, POLICY, PROFILES)
        receipt = Path(self.tmp.name) / 'actual-native-refusal.json'
        receipt.write_text(json.dumps({'reason': reason}))
        if prohibited:
            rc.launch_failed(state, packet['packet_id'], str(receipt), 'transport', reason, retry_prohibited=True)
        else:
            rc.launch_failed(state, packet['packet_id'], str(receipt), 'transport', reason)
        restored = Path(self.tmp.name) / 'actual-native-restoration.json'
        restored.write_text(json.dumps({'packet_id': packet['packet_id'], 'fingerprint': packet['fingerprint'],
            'native_tool': packet['native_tool'], 'transport_available': True, 'retry_permitted': True}))
        delta = Path(self.tmp.name) / 'discovery-restoration.json'
        delta.write_text(json.dumps({'kind': 'prelaunch_transport', 'packet_id': packet['packet_id'],
            'fingerprint': packet['fingerprint'], 'before': {'transport': 'refused'},
            'after': {'transport': 'available'}, 'scope': 'same bounded discovery',
            'discriminator': 'actual native host capacity restored', 'restoration_receipt': str(restored)}))
        return state, packet, delta

    def test_refused_discovery_restores_exact_transport_without_science_replay(self):
        state, packet, delta = self.restoration_fixture()
        before = copy.deepcopy(state)
        rc.restore_discovery(state, packet['packet_id'], str(delta))
        next_packet = rc.next_packet(state, POLICY, PROFILES)
        self.assertNotEqual(next_packet['packet_id'], packet['packet_id'])
        self.assertEqual(next_packet['fingerprint'], packet['fingerprint'])
        self.assertEqual(state['adaptive']['packets'][packet['packet_id']]['hold'],
                         before['adaptive']['packets'][packet['packet_id']]['hold'])
        for key in before:
            if key != 'adaptive':
                self.assertEqual(state[key], before[key])
        rc.acknowledge(state, next_packet['packet_id'], 'actual-restored-discovery-agent')
        acknowledged = copy.deepcopy(state)
        with self.assertRaises(rc.ControllerError):
            rc.restore_discovery(state, next_packet['packet_id'], str(delta))
        self.assertEqual(acknowledged, state)
        self.assertNotIn('spawn_args', rc.next_packet(state, POLICY, PROFILES))

    def test_discovery_restoration_rejects_exhaustion_staleness_and_wrong_packet(self):
        for reason, prohibited in [('monthly quota exhausted', False), ('explicit no-retry', True)]:
            state, packet, delta = self.restoration_fixture(reason, prohibited)
            before = copy.deepcopy(state)
            with self.assertRaisesRegex(rc.ControllerError, 'cannot retry'):
                rc.restore_discovery(state, packet['packet_id'], str(delta))
            self.assertEqual(state, before)
            state['tasks']['A']['candidate_identity'] = 'new science does not restore exhausted transport'
            self.assertNotIn('spawn_args', rc.next_packet(state, POLICY, PROFILES))
        state, packet, delta = self.restoration_fixture()
        data = json.loads(delta.read_text())
        delta.write_text(json.dumps({**data, 'packet_id': 'wrong'}))
        before = copy.deepcopy(state)
        with self.assertRaises(rc.ControllerError):
            rc.restore_discovery(state, packet['packet_id'], str(delta))
        self.assertEqual(state, before)
        delta.write_text(json.dumps(data))
        state['tasks']['A']['candidate_identity'] = 'new actual evidence'
        before = copy.deepcopy(state)
        with self.assertRaisesRegex(rc.ControllerError, 'science fingerprint changed'):
            rc.restore_discovery(state, packet['packet_id'], str(delta))
        self.assertEqual(state, before)


    def test_restore_discovery_cli_keeps_same_science_and_issues_new_unlaunched_packet(self):
        import subprocess
        import sys
        state, packet, delta = self.restoration_fixture()
        checkpoint = Path(self.tmp.name) / 'discovery-state.json'
        policy = Path(self.tmp.name) / 'routing-policy.json'
        rc.save(checkpoint, state)
        policy.write_text(json.dumps(POLICY))
        command = [sys.executable, str(ROOT / 'scripts/codex_harness/research_controller.py'),
                   '--state', str(checkpoint), '--policy', str(policy)]
        result = subprocess.run(command + ['restore-discovery', '--packet-id', packet['packet_id'],
                                '--evidence', str(delta)], text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout)['planning']['outstanding'], 0)
        result = subprocess.run(command + ['next', '--available-profile', 'gpt-6-astra/xhigh'],
                                text=True, capture_output=True, check=True)
        new_packet = json.loads(result.stdout)
        self.assertNotEqual(packet['packet_id'], new_packet['packet_id'])
        self.assertEqual(packet['fingerprint'], new_packet['fingerprint'])
        self.assertFalse(new_packet['launch_performed'])
        restored = json.loads(checkpoint.read_text())
        for key in state:
            if key != 'adaptive':
                self.assertEqual(restored[key], state[key])


    def test_same_task_distinct_unspent_issue_authorizes_but_consumed_sibling_alias_does_not(self):
        state = rc.initialize({'campaign_id': 'same-origin-distinct-issues',
            'approved_scientific_repairs': ['old-budget'],
            'tasks': [task('A', approved_repair_id='old-budget'), task('SIBLING', approved_repair_id=None)]}, 'owner')
        state['tasks']['SIBLING']['state'] = 'held'
        issue1 = self.issue(question='Does factorization preserve positive definiteness?',
            exact_missing_or_defect='negative covariance eigenvalue', high_consequence=True,
            risk='false covariance admission')
        issue2 = self.issue(question='Does full tensor support retain the null direction?',
            exact_missing_or_defect='rank loss in a distinct tensor-support map',
            counterexample={'matrix': [[1, 0], [0, 0]], 'expected_rank': 1, 'observed_rank': 0})
        self.result(state, self.launch(state), 'blocker', issue=issue1)
        ultra = self.launch(state)
        self.assertEqual(ultra['phase'], 'escalation')
        self.result(state, ultra, repair_plan='Repair covariance factorization')
        self.result(state, self.launch(state), 'blocker', issue=issue2)
        self.assertEqual(state['tasks']['A']['state'], 'held')
        spent = copy.deepcopy(state['ultra_repairs'])
        self.assertFalse(state['ultra_pending'])
        rc.enable_adaptive(state, 'owner distinct issue research')
        discovery = self.launch(state)

        def actual_decision(packet, origin, issue, repair_id, scope, after, discovery=False):
            delta = {'kind': 'validation_counterexample', 'before': {'operator': 'covariance-factorization', 'rank': 2},
                     'after': after, 'scope': scope, 'discriminator': 'independent exact rank comparison'}
            evidence = Path(self.tmp.name) / (repair_id + '-counterexample.json')
            evidence.write_text(json.dumps(after))
            authorization = {'repair_id': repair_id, 'issue': issue,
                'issue_identity': rc.digest(rc._semantic_meaning(issue)), 'operative_question': issue['question'],
                'scope': scope, 'origin_task_id': origin, 'origin_issue_identity': rc.digest(rc._semantic_meaning(issue)),
                'claim_target': state['tasks'][origin]['spec']['acceptance'], 'semantic_delta': delta,
                'cumulative_budget_link': state['campaign_identity'], 'evidence_refs': [str(evidence)]}
            bindings = {key: authorization[key] for key in ('origin_task_id', 'origin_issue_identity',
                        'issue_identity', 'claim_target', 'cumulative_budget_link')}
            raw = Path(self.tmp.name) / (repair_id + '-actual-astra-decision.json')
            store = state['adaptive']['packets'] if discovery else state['packets']
            result = {'packet_id': packet['packet_id'], 'task_id': packet['task_id'],
                'input_identity': packet['input_identity'], 'agent_id': store[packet['packet_id']]['agent_id'],
                'raw_receipt': str(raw), 'decision': 'distinct_scoped_issue',
                'semantic_delta_identity': rc.digest(rc._semantic_projection(delta)), **bindings}
            if discovery:
                result.update(outcome='no_action', examined_branches=['A', 'SIBLING'],
                    methods=['Full tensor support rank comparison'], source_refs=[str(evidence)],
                    exact_residuals=['A distinct tensor defect needs its first allowance', 'SIBLING not yet executed'])
            else:
                result.update(outcome='success', repair_plan='Proposed deterministic covariance correction')
            raw.write_text(json.dumps(result))
            rc.record(state, result, POLICY)
            authorization['research_decision_receipt'] = str(raw)
            return authorization

        auth = actual_decision(discovery, 'A', issue2, 'new-budget', 'distinct tensor support issue',
            {'operator': 'tensor-support-map', 'matrix': [[1, 0], [0, 0]], 'expected_rank': 1, 'observed_rank': 0}, True)
        # Historical receipts remain valid without the new optional issue field.
        legacy = copy.deepcopy(state)
        legacy['ultra_repairs']['old-budget'].pop('operative_issue_identity')
        legacy_spent = copy.deepcopy(legacy['ultra_repairs'])
        rc.authorize_repair(legacy, auth, 'owner distinct issue authorization')
        self.assertEqual(legacy['ultra_repairs'], legacy_spent)
        self.assertNotIn('new-budget', legacy['ultra_pending'])
        rc.authorize_repair(state, auth, 'owner distinct issue authorization')
        self.assertEqual(state['ultra_repairs'], spent)
        self.assertNotIn('new-budget', state['ultra_pending'])
        self.assertEqual(state['tasks']['A']['spec']['approved_repair_id'], 'old-budget')
        self.assertEqual(rc._task_repair_id(state, 'A'), 'new-budget')
        # The same consumed I1 cannot get another allowance through an exact sibling alias,
        # even with a fresh actual read-only decision and a differently named delta.
        state['tasks']['SIBLING'].update(state='ready', phase='execute')
        self.result(state, self.launch(state), 'blocker', issue=issue1)
        research = self.launch(state)
        alias = actual_decision(research, 'SIBLING', issue1, 'old-budget-sibling-alias',
            'sibling covariance issue', {'operator': 'covariance-factorization', 'matrix': [[-1]], 'minimum_eigenvalue': -1})
        before = copy.deepcopy(state)
        with self.assertRaisesRegex(rc.ControllerError, 'operative issue cannot replenish an alias'):
            rc.authorize_repair(state, alias, 'owner distinct issue authorization')
        self.assertEqual(state, before)
        self.assertEqual(state['ultra_repairs'], spent)


if __name__ == "__main__":
    unittest.main()
