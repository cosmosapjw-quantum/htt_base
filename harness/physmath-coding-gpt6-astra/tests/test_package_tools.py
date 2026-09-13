import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]


class HarnessBehavior(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / 'package'
        shutil.copytree(PACKAGE, self.root)

    def tearDown(self):
        self.temp.cleanup()

    def command(self, name, *args):
        return subprocess.run([sys.executable, str(self.root / 'tools' / name), *args], capture_output=True, text=True)

    def test_valid_package_separates_structure_from_scientific_acceptance(self):
        r = self.command('validate_harness.py', '--json')
        self.assertEqual(r.returncode, 0, r.stderr)
        result = json.loads(r.stdout)
        self.assertEqual(result['package_structure'], 'PASS')
        self.assertEqual(result['scientific_acceptance'], 'NOT_EVALUATED')
        self.assertEqual(result['model_performance'], 'NOT_EVALUATED')

    def test_version_disagreement_is_rejected(self):
        (self.root / 'VERSION').write_text('999.0.0\n')
        r = self.command('validate_harness.py')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('version', r.stderr.lower())

    def test_broken_manifest_is_rejected_without_traceback(self):
        (self.root / 'manifest.json').write_text('{broken')
        r = self.command('validate_harness.py', '--json')
        self.assertNotEqual(r.returncode, 0)
        result = json.loads(r.stdout)
        self.assertEqual(result['package_structure'], 'FAIL')
        self.assertNotIn('Traceback', r.stderr)

    def test_escaping_entrypoint_is_rejected(self):
        path = self.root / 'manifest.json'
        value = json.loads(path.read_text())
        value['entrypoints'] = ['../outside.md']
        path.write_text(json.dumps(value))
        r = self.command('validate_harness.py')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('entrypoint', r.stderr.lower())

    def test_initializer_preserves_existing_bytes_and_is_idempotent(self):
        for name, contents in [('RUN_STATE.md', b'actual current state\n'), ('DECISION_LOG.md', b''), ('FAILURE_LOG.md', b'first failure evidence\n')]:
            (self.root / name).write_bytes(contents)
        names = ['RUN_STATE.md', 'DECISION_LOG.md', 'FAILURE_LOG.md']
        before = {name: hashlib.sha256((self.root / name).read_bytes()).hexdigest() for name in names}
        for _ in range(2):
            r = self.command('init_harness.py')
            self.assertEqual(r.returncode, 0, r.stderr)
        after = {name: hashlib.sha256((self.root / name).read_bytes()).hexdigest() for name in names}
        self.assertEqual(before, after)

    def test_initializer_creates_missing_state_in_selected_root(self):
        target = Path(self.temp.name) / 'project'
        target.mkdir()
        r = self.command('init_harness.py', '--root', str(target))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((target / 'RUN_STATE.md').is_file())
        self.assertTrue((target / 'DECISION_LOG.md').is_file())
        self.assertTrue((target / 'FAILURE_LOG.md').is_file())


if __name__ == '__main__':
    unittest.main()
