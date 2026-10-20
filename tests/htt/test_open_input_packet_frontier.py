"""Regression checks for frozen scientific gates and current continuation dispatch."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('htt_open_input_packet', ROOT / 'scripts/htt_open_input_packet.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FrontierPacketTests(unittest.TestCase):
    def setUp(self):
        self.dag = {'nodes': [
            {'id': 'A', 'acceptance': 'frozen A', 'depends_on': [], 'state': 'completed_scoped', 'external_missing': []},
            {'id': 'B', 'acceptance': 'physical law', 'depends_on': ['A'], 'state': 'pending', 'external_missing': ['joint law']},
        ]}
        self.plan = {
            'all_original_nodes': [dict(n, input_routes=['D01']) for n in self.dag['nodes']],
            'tasks': [{'id': 'D01', 'goal': 'Reuse a completed acquisition', 'status': 'executed_scoped_reuse', 'depends_on': []}],
            'frontier_actions': [
                {'id': 'F01', 'nodes': ['B'], 'status': 'completed_scoped'},
                {'id': 'F02', 'nodes': ['B'], 'status': 'ready'},
                {'id': 'F03', 'nodes': ['B'], 'status': 'blocked_input'},
            ],
            'current_acquisition_manifest': 'new_manifest.json',
        }

    def test_completed_acquisition_does_not_promote_science(self):
        result = module.packet(self.dag, self.plan)
        self.assertEqual(result['scientific_completed'], 1)
        self.assertEqual(result['scientific_ready'], [])
        self.assertEqual(result['direct_external'], ['B'])
        self.assertEqual([x['id'] for x in result['available_frontier_actions']], ['F02'])

    def test_one_blocked_lane_does_not_hide_an_available_action(self):
        result = module.packet(self.dag, self.plan)
        self.assertEqual([x['id'] for x in result['conditional_frontier_actions']], ['F03'])
        self.assertEqual(len(result['available_frontier_actions']), 1)

    def test_changed_scientific_acceptance_rejected(self):
        changed = copy.deepcopy(self.dag)
        changed['nodes'][1]['acceptance'] = 'download succeeded'
        with self.assertRaises(ValueError): module.packet(changed, self.plan)

    def test_changed_scientific_dependencies_rejected(self):
        changed = copy.deepcopy(self.dag)
        changed['nodes'][1]['depends_on'] = []
        with self.assertRaises(ValueError): module.packet(changed, self.plan)

    def test_node_uses_current_manifest_and_keeps_live_gate(self):
        result = module.packet(self.dag, self.plan, node='B')
        self.assertEqual(result['data_manifest'], 'new_manifest.json')
        self.assertEqual(result['live_node']['external_missing'], ['joint law'])
        self.assertEqual(len(result['frontier_actions']), 3)

    def test_packet_is_read_only(self):
        before = copy.deepcopy((self.dag, self.plan))
        module.packet(self.dag, self.plan)
        module.packet(self.dag, self.plan, node='B')
        self.assertEqual((self.dag, self.plan), before)

    def test_frontier_and_legacy_task_ids_resolve_without_aliasing(self):
        self.assertEqual(module.packet(self.dag, self.plan, task='F02')['status'], 'ready')
        self.assertEqual(module.packet(self.dag, self.plan, task='D01')['status'], 'executed_scoped_reuse')
        self.plan['frontier_actions'].append({'id': 'D01', 'status': 'ready'})
        with self.assertRaises(ValueError): module.packet(self.dag, self.plan, task='D01')


if __name__ == '__main__':
    unittest.main()
