"""Synthetic metadata validation only; no Git or production main execution."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPTS = Path('/mnt/extdrive/workdir/htt_open_data/r29_controller_publication')
spec = importlib.util.spec_from_file_location('baseline', SCRIPTS/'protocol_baseline_v2.py')
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


class BaselineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.prior = {'non_object_metadata': {
            'HEAD': {'size': 20, 'mtime_ns': 1, 'mode': 420, 'sha256': 'head', 'symlink': False},
            'index': {'size': 20, 'mtime_ns': 1, 'mode': 420, 'sha256': 'index', 'symlink': False},
            'config': {'size': 20, 'mtime_ns': 1, 'mode': 420, 'sha256': 'config-old', 'symlink': False},
            'refs/heads/main': {'size': 20, 'mtime_ns': 1, 'mode': 420, 'sha256': 'ref', 'symlink': False}},
            'canonical_object_stat_inventory': {'objects/aa/bb': {'size': 5, 'mtime_ns': 1, 'mode': 292}}}
        self.live = copy.deepcopy(self.prior)
        self.live['non_object_metadata']['config']['sha256'] = 'config-new'
        self.live['canonical_object_stat_inventory']['objects/aa/bb']['mtime_ns'] = 2
        self.anchor = self.write('prior.json', self.prior)
        self.baseline = self.write('fresh.json', self.live)
        self.context = {'tree': 'tree', 'sole_parent': 'parent', 'local_HEAD': 'head',
                        'remote_url': 'https://example.invalid/repo', 'remote_ref': 'refs/heads/main'}
        self.required = [self.write(name+'.json', {'kind': name})
                         for name in ('source1', 'source2', 'state', 'pointer', 'script1', 'script2', 'helper', 'guard')]
        self.evidence = [self.write('independent.json', {'classification': 'reviewed'})]
        self.a = {'protocol': 'R29_EXPLICIT_EXECUTION_BASELINE_V2', 'action': 'commit',
                  'prior_anchor': self.anchor, 'execution_baseline': self.baseline,
                  'review_seals': self.required}
        self.rec = {'status': 'ROOT_RECONCILED_EXACT_TRANSITION', 'action': 'commit',
                    'context': self.context, 'prior_anchor': self.anchor,
                    'execution_baseline': self.baseline, 'review_seals': self.required,
                    'independent_evidence': self.evidence,
                    'metadata_changes': [dict(x, classification='independently classified metadata')
                                         for x in b.metadata_changes(self.prior, self.live)]}
        self.seal_reconciliation()
        self.effects = []

    def write(self, name, value):
        p = self.root/name
        p.write_text(json.dumps(value, sort_keys=True)+'\n')
        return b.seal(p)

    def seal_reconciliation(self):
        self.a['reconciliation'] = self.write('reconciliation.json', self.rec)

    def run_gate(self):
        answer = b.validate_transition(self.a, self.a.get('action', 'commit'), self.live,
                                       context=self.context, prior_descriptor=self.anchor,
                                       required_seals=self.required, evidence=self.evidence)
        self.effects.append('effectful-operation-would-follow')
        return answer

    def reject(self):
        with self.assertRaises((AssertionError, KeyError, FileNotFoundError, TypeError)):
            self.run_gate()
        self.assertEqual(self.effects, [])

    def test_commit_positive_complete_fresh_baseline(self):
        self.assertEqual(self.run_gate(), self.live)
        self.assertNotEqual(self.live, self.prior)

    def test_push_positive_complete_fresh_baseline(self):
        self.a['action'] = self.rec['action'] = 'push'
        self.context['commit'] = 'exact-candidate'
        self.seal_reconciliation()
        self.assertEqual(self.run_gate(), self.live)

    def test_missing_baseline(self):
        del self.a['execution_baseline']; self.reject()

    def test_missing_baseline_file(self):
        Path(self.baseline['path']).unlink(); self.reject()

    def test_changed_baseline_bytes(self):
        Path(self.baseline['path']).write_text('{}'); self.reject()

    def test_changed_baseline_hash(self):
        self.a['execution_baseline'] = dict(self.baseline, sha256='0'*64); self.reject()

    def test_missing_reconciliation(self):
        del self.a['reconciliation']; self.reject()

    def test_changed_reconciliation_bytes(self):
        Path(self.a['reconciliation']['path']).write_text('{}'); self.reject()

    def test_changed_prior_anchor_bytes(self):
        Path(self.anchor['path']).write_text('{}'); self.reject()

    def test_changed_prior_anchor_descriptor(self):
        self.a['prior_anchor'] = dict(self.anchor, sha256='0'*64); self.reject()

    def test_changed_live_head_index_config_refs_and_objects(self):
        for group, key in [('non_object_metadata', x) for x in ('HEAD', 'index', 'config', 'refs/heads/main')] + [('canonical_object_stat_inventory', 'objects/aa/bb')]:
            with self.subTest(group=group, key=key):
                old = copy.deepcopy(self.live[group][key])
                self.live[group][key]['mtime_ns'] += 1
                self.reject()
                self.live[group][key] = old

    def test_live_added_and_removed_ref(self):
        self.live['non_object_metadata']['refs/heads/extra'] = {'sha256': 'new'}
        self.reject()
        del self.live['non_object_metadata']['refs/heads/extra']
        del self.live['non_object_metadata']['refs/heads/main']; self.reject()

    def test_live_status_extension_not_ignored(self):
        self.live['status'] = 'changed'; self.reject()

    def test_no_snapshot_group_omitted(self):
        del self.live['canonical_object_stat_inventory']; self.reject()

    def test_changed_required_source_state_pointer_script_guard(self):
        for row in self.required:
            with self.subTest(path=row['path']):
                p = Path(row['path']); old = p.read_bytes()
                p.write_bytes(old+b' '); self.reject(); p.write_bytes(old)

    def test_missing_required_source_state_pointer_seals(self):
        for row in self.required:
            with self.subTest(path=row['path']):
                self.a['review_seals'] = [x for x in self.required if x is not row]
                self.rec['review_seals'] = self.a['review_seals']
                self.seal_reconciliation(); self.reject()

    def test_changed_independent_evidence(self):
        Path(self.evidence[0]['path']).write_text('{}'); self.reject()

    def test_unclassified_or_incomplete_delta(self):
        del self.rec['metadata_changes'][0]['classification']
        self.seal_reconciliation(); self.reject()
        self.rec['metadata_changes'] = []; self.seal_reconciliation(); self.reject()

    def test_wrong_reconciliation_action_context_or_baseline(self):
        for key, value in [('action', 'push'), ('context', {}), ('execution_baseline', self.anchor), ('prior_anchor', self.baseline)]:
            with self.subTest(key=key):
                old = self.rec[key]; self.rec[key] = value
                self.seal_reconciliation(); self.reject(); self.rec[key] = old

    def test_declared_delta_must_match_entire_snapshot(self):
        self.rec['metadata_changes'][0]['after'] = {'ignored': True}
        self.seal_reconciliation(); self.reject()

    def test_existing_within_action_and_transport_guards_retained(self):
        for name, action in [('create_reviewed_commit', 'commit'), ('push_approved_commit', 'push')]:
            original = (SCRIPTS/(name+'.py')).read_text()
            candidate = (SCRIPTS/(name+'_v2.py')).read_text()
            compile(candidate, str(SCRIPTS/(name+'_v2.py')), 'exec')
            for line in original.splitlines():
                if 'before=m.snapshot();' in line or 'APPROVED_' in line or "packet={'status'" in line:
                    continue
                self.assertIn(line, candidate)
            self.assertIn('assert before==after', candidate)
            self.assertEqual(candidate.count('baseline.validate_action('), 2)
            attempt = "save('COMMIT_PREPARATION_RETURN.json',{'status':'STARTED'" if action=='commit' else "save('PUSH_ATTEMPT_STARTED.json',"
            self.assertLess(candidate.rindex('baseline.validate_action('), candidate.index(attempt))
            self.assertIn('no blind '+action+' retry', candidate)
        push = (SCRIPTS/'push_approved_commit_v2.py').read_text()
        self.assertIn("C+':'+m.REF", push)
        self.assertNotIn('--force', push)


if __name__ == '__main__':
    unittest.main(verbosity=2)
