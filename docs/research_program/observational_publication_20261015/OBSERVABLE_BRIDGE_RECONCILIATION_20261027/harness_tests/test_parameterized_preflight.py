"""Focused integration tests using the full pinned controller/router imports."""
from pathlib import Path
import copy
import hashlib
import json
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
WORK=HERE.parents[1]
SOURCE_ROOT=next((p for p in HERE.parents if (p/'scripts/codex_harness/research_controller.py').is_file()), WORK/'baseline')
PREFLIGHT_FILE=HERE/'publication_frontier_preflight.py'
if not PREFLIGHT_FILE.is_file():
    PREFLIGHT_FILE=SOURCE_ROOT/'scripts/codex_harness/publication_frontier_preflight.py'
sys.path.insert(0,str(SOURCE_ROOT/'scripts/codex_harness'))
import research_controller as rc
sys.path.insert(0,str(PREFLIGHT_FILE.parent))
import publication_frontier_preflight as pf

def digest_bytes(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.input=self.root/'inputs/source.json'
        self.input.parent.mkdir()
        self.input.write_text('{"measurement": 4}\n')

    def tearDown(self):
        self.temp.cleanup()

    def make(self, folder=None):
        folder=Path(pf.REL if folder is None else folder)
        p=self.root/folder;p.mkdir(parents=True)
        row={'path':'inputs/source.json','sha256':digest_bytes(self.input)}
        spec={'id':'NEW','kind':'theory','goal':'Compute new covariance response',
              'acceptance':'Exact response and independent check','input_identity':row['sha256'],
              'contract_origin':'new_conditional_research','promotes_original_acceptance':False,
              'requires':{'all':[]},'input_sources':[row],
              'owned_paths':[str(folder/'products/NEW')],
              'semantic_delta':{'kind':'method','before':{'covariance':'diagonal'},
                  'after':{'covariance':'cross-window'},'discriminator':'operator comparison',
                  'scope':'conditional study'}}
        frontier={'frontier_id':'TEST_FRONTIER','authorization':'disposable test','tasks':[spec]}
        (p/'FRONTIER.json').write_text(json.dumps(frontier))
        (p/'EVIDENCE_MANIFEST.json').write_text(json.dumps({'files':[row]}))
        return folder,frontier

    def old_state(self):
        s=rc.initialize({'campaign_id':'TEST','tasks':[{'id':'OLD','goal':'Original task',
            'acceptance':'Original physics','input_identity':'old'}]},'disposable test')
        s['tasks']['OLD'].update(state='held',attempt=5,hold={'reason':'exhausted'},history=[{'legacy':True}])
        s['ultra_repairs']['USED']={'task_id':'OLD'}
        return s

    def test_default_signature_and_static_path(self):
        self.make()
        r=pf.check(self.root)
        self.assertEqual(r['status'],'STATIC_VALIDATED')
        self.assertEqual(r['frontier_path'],pf.REL+'/FRONTIER.json')
        self.assertFalse(r['writes_state'])

    def test_custom_path_preserves_old_state(self):
        folder,_=self.make('docs/new_bridge')
        state=self.old_state();before=copy.deepcopy(state)
        r=pf.check(self.root,state,frontier_path=folder/'FRONTIER.json',manifest_path=folder/'EVIDENCE_MANIFEST.json')
        self.assertEqual(r['status'],'APPEND_READY')
        self.assertEqual(r['candidate_root_tasks'],['NEW'])
        self.assertEqual(state,before)

    def test_custom_manifest_default_beside_frontier(self):
        folder,_=self.make('docs/new_bridge')
        r=pf.check(self.root,frontier_path=folder/'FRONTIER.json')
        self.assertEqual(r['manifest_path'],'docs/new_bridge/EVIDENCE_MANIFEST.json')

    def test_selected_path_escape_rejected(self):
        self.make()
        for bad in ['../FRONTIER.json',str(self.root/'FRONTIER.json')]:
            with self.assertRaisesRegex(ValueError,'repository-relative'):
                pf.check(self.root,frontier_path=bad)
        with self.assertRaisesRegex(ValueError,'repository-relative'):
            pf.check(self.root,manifest_path='../manifest.json')

    def test_input_path_escape_rejected(self):
        folder,f=self.make('docs/new_bridge')
        f['tasks'][0]['input_sources'][0]['path']='../source.json'
        (self.root/folder/'FRONTIER.json').write_text(json.dumps(f))
        with self.assertRaisesRegex(ValueError,'repository-relative'):
            pf.check(self.root,frontier_path=folder/'FRONTIER.json')

    def test_changed_source_hash_rejected(self):
        folder,_=self.make('docs/new_bridge')
        self.input.write_text('{"measurement": 5}\n')
        with self.assertRaisesRegex(ValueError,'changed evidence'):
            pf.check(self.root,frontier_path=folder/'FRONTIER.json')

    def test_already_appended_identity_and_changed_frontier(self):
        folder,f=self.make('docs/new_bridge');state=self.old_state()
        rc.append_frontier(state,f,'disposable test')
        before=copy.deepcopy(state)
        r=pf.check(self.root,state,frontier_path=folder/'FRONTIER.json')
        self.assertEqual(r['status'],'ALREADY_APPENDED')
        self.assertEqual(state,before)
        f['tasks'][0]['acceptance']='Changed acceptance'
        (self.root/folder/'FRONTIER.json').write_text(json.dumps(f))
        with self.assertRaisesRegex(ValueError,'different frozen content'):
            pf.check(self.root,state,frontier_path=folder/'FRONTIER.json')
        self.assertEqual(state,before)

    def test_active_writer_overlap_rejected(self):
        folder,_=self.make('docs/new_bridge');state=self.old_state()
        state['tasks']['OLD']['state']='running'
        state['tasks']['OLD']['spec']['owned_paths']=[str(folder/'products')]
        before=copy.deepcopy(state)
        with self.assertRaisesRegex(ValueError,'active writer overlaps'):
            pf.check(self.root,state,frontier_path=folder/'FRONTIER.json')
        self.assertEqual(state,before)

    def test_custom_owned_path_outside_task_rejected(self):
        folder,f=self.make('docs/new_bridge')
        f['tasks'][0]['owned_paths']=['docs/unrelated']
        (self.root/folder/'FRONTIER.json').write_text(json.dumps(f))
        with self.assertRaisesRegex(ValueError,'write ownership outside'):
            pf.check(self.root,frontier_path=folder/'FRONTIER.json')

    def test_symlink_escape_rejected(self):
        folder,f=self.make('docs/new_bridge')
        with tempfile.TemporaryDirectory() as outside:
            out=Path(outside)/'source.json';out.write_text('{}')
            link=self.root/'inputs/escaped.json';link.symlink_to(out)
            f['tasks'][0]['input_sources'][0]={'path':'inputs/escaped.json','sha256':digest_bytes(out)}
            (self.root/folder/'FRONTIER.json').write_text(json.dumps(f))
            with self.assertRaisesRegex(ValueError,'path escapes repository'):
                pf.check(self.root,frontier_path=folder/'FRONTIER.json')

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(PreflightTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    receipt={'test_count':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
        'successful':result.wasSuccessful(),'full_controller_and_router_import':True,
        'live_state_read':False,'live_state_mutation':False,
        'candidate_sha256':digest_bytes(PREFLIGHT_FILE),
        'controller_sha256':digest_bytes(SOURCE_ROOT/'scripts/codex_harness/research_controller.py'),
        'router_sha256':digest_bytes(SOURCE_ROOT/'scripts/codex_harness/native_routing.py')}
    (HERE/'parameterized_preflight_results.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))
    sys.exit(0 if result.wasSuccessful() else 1)
