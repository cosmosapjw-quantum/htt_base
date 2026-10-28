"""Opt-in delivery ordering; synthetic controller fixtures never launch native work."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import research_controller as rc
from test_research_controller import POLICY, PROFILES, task
import test_research_controller_checkpoint as checkpoint_fixtures


class ConvergenceTests(unittest.TestCase):
    def state(self, rows=None):
        return rc.initialize({'campaign_id': 'convergence-fixture', 'tasks': rows or [
            task('R36-OLD', approved_repair_id=None, priority=100),
            task('R37-REPORT', approved_repair_id=None, priority=0)]}, 'fixture authorization')

    def test_default_fair_order_is_unchanged(self):
        state = self.state()
        explicit = copy.deepcopy(state)
        first = rc.next_packet(state, POLICY, PROFILES)
        second = rc.next_packet(explicit, POLICY, PROFILES, preferred_tasks=(),
                                deferred_tasks=(), allow_discovery=True)
        self.assertEqual(first['task_id'], 'R36-OLD')
        self.assertEqual(first, second)
        self.assertEqual(state, explicit)

    def test_preference_overrides_old_ready_order_and_follows_argument_order(self):
        state = self.state()
        packet = rc.next_packet(state, POLICY, PROFILES, preferred_tasks=('R37-REPORT', 'R36-OLD'))
        self.assertEqual(packet['task_id'], 'R37-REPORT')
        self.assertEqual(state['tasks']['R36-OLD']['attempt'], 0)

    def test_preference_applies_to_review_without_qualifying_it(self):
        state = self.state()
        report = state['tasks']['R37-REPORT']
        report.update(phase='review', last_turn=25, candidate_identity='fixture-candidate')
        packet = rc.next_packet(state, POLICY, PROFILES, preferred_tasks=('R37-REPORT',))
        self.assertEqual((packet['task_id'], packet['phase']), ('R37-REPORT', 'review'))
        self.assertEqual(report['state'], 'planned')
        self.assertNotIn('qualified_products', report)

    def test_preferred_task_does_not_bypass_dependencies(self):
        state = self.state([task('A'), task('REPORT', ['A'])])
        self.assertEqual(rc.next_packet(state, POLICY, PROFILES,
                         preferred_tasks=('REPORT',))['task_id'], 'A')

    def test_nonpreferred_legacy_continues_after_report(self):
        state = self.state()
        state['tasks']['R37-REPORT']['state'] = 'completed'
        self.assertEqual(rc.next_packet(state, POLICY, PROFILES,
                         preferred_tasks=('R37-REPORT',), allow_discovery=False)['task_id'], 'R36-OLD')

    def test_deferred_final_follows_other_ready_work_then_runs_with_old_hold(self):
        state = self.state([task('A-FINAL'), task('Z-LEGACY')])
        packet = rc.next_packet(state, POLICY, PROFILES, deferred_tasks=('A-FINAL',))
        self.assertEqual(packet['task_id'], 'Z-LEGACY')
        # Separate fixture represents a valid prior outcome; no live packet is cancelled.
        held = self.state([task('A-FINAL'), task('Z-LEGACY')])
        held['tasks']['Z-LEGACY'].update(state='held', hold={'class': 'input'})
        self.assertEqual(rc.next_packet(held, POLICY, PROFILES,
                         deferred_tasks=('A-FINAL',), allow_discovery=False)['task_id'], 'A-FINAL')

    def test_pending_packet_replays_without_preemption_or_accounting_change(self):
        state = self.state()
        packet = rc.next_packet(state, POLICY, PROFILES)
        before = copy.deepcopy(state)
        self.assertEqual(rc.next_packet(state, POLICY, PROFILES,
                         preferred_tasks=('R37-REPORT',), allow_discovery=False), packet)
        self.assertEqual(state, before)

    def test_running_writer_is_preserved(self):
        state = self.state()
        packet = rc.next_packet(state, POLICY, PROFILES)
        rc.acknowledge(state, packet['packet_id'], 'actual-fixture-agent')
        before = copy.deepcopy(state)
        result = rc.next_packet(state, POLICY, PROFILES,
                                preferred_tasks=('R37-REPORT',), allow_discovery=False)
        self.assertEqual(result['status'], 'AWAITING_NATIVE_OUTCOME')
        self.assertEqual(state, before)

    def test_no_discovery_preserves_adaptive_history(self):
        state = self.state()
        for row in state['tasks'].values(): row['state'] = 'held'
        rc.enable_adaptive(state, 'historical adaptive authorization')
        before = copy.deepcopy(state)
        result = rc.next_packet(state, POLICY, PROFILES, allow_discovery=False)
        self.assertEqual(result['status'], 'HOLD_UNRESOLVED_BRANCHES')
        self.assertEqual(state, before)
        self.assertEqual(rc.next_packet(state, POLICY, PROFILES)['phase'], 'discovery')

    def test_no_discovery_still_replays_existing_discovery(self):
        state = self.state()
        for row in state['tasks'].values(): row['state'] = 'held'
        rc.enable_adaptive(state, 'historical adaptive authorization')
        packet = rc.next_packet(state, POLICY, PROFILES)
        before = copy.deepcopy(state)
        self.assertEqual(rc.next_packet(state, POLICY, PROFILES, allow_discovery=False), packet)
        self.assertEqual(state, before)

    def test_unknown_duplicate_and_conflicting_hints_rejected_atomically(self):
        for kwargs in ({'preferred_tasks': ('MISSING',)}, {'deferred_tasks': ('MISSING',)},
                       {'preferred_tasks': ('R37-REPORT', 'R37-REPORT')},
                       {'preferred_tasks': ('R37-REPORT',), 'deferred_tasks': ('R37-REPORT',)}):
            with self.subTest(kwargs=kwargs):
                state = self.state(); before = copy.deepcopy(state)
                with self.assertRaises(rc.ControllerError):
                    rc.next_packet(state, POLICY, PROFILES, **kwargs)
                self.assertEqual(state, before)

    def test_acquisition_resume_reservation_remains_exclusive(self):
        fixture = checkpoint_fixtures.CheckpointTests(methodName='test_missing_actual_handoff_and_host_observation_waits')
        fixture.setUp(); self.addCleanup(fixture.doCleanups)
        fixture.prepare()
        before = copy.deepcopy(fixture.state)
        result = rc.next_packet(fixture.state, POLICY, PROFILES,
                                preferred_tasks=('SMICA',), allow_discovery=False)
        self.assertEqual(result['status'], 'AWAITING_NATIVE_OUTCOME')
        self.assertEqual(fixture.state, before)

    def test_cli_options_and_unknown_id_error(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'state.json'; path.write_text(json.dumps(self.state()))
            script = Path(__file__).with_name('research_controller.py')
            command = [sys.executable, str(script), '--state', str(path), 'next',
                       '--prefer-task', 'R37-REPORT', '--no-discovery']
            for model, effort in sorted(PROFILES): command += ['--available-profile', model+'/'+effort]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['task_id'], 'R37-REPORT')
            before = path.read_bytes()
            result = subprocess.run([sys.executable, str(script), '--state', str(path), 'next',
                                     '--defer-task', 'MISSING'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('unknown deferred task ID', result.stderr)
            self.assertEqual(path.read_bytes(), before)


if __name__ == '__main__': unittest.main()
