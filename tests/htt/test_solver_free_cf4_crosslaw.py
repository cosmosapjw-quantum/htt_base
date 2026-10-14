#!/usr/bin/env python3
"""Narrow scientific tests for new eta semantics and unchanged preselection generator."""
import argparse, importlib, sys, unittest, tempfile, subprocess
from unittest import mock
from pathlib import Path
from dataclasses import replace
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
import run_solver_free_cf4_crosslaw as x
REPO=Path(__file__).resolve().parents[2]
class TestCrossLaw(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=x.load_repo(REPO)
        cls.packet,cls.design,_=cls.d.intake(REPO,REPO/'docs/observational_reboot_20261014/task_packets/RB07_selected_scenario.json')
        cls.scenario=cls.d.Scenario(**cls.packet['baseline'])
    def test_preselection_generator_matches_original(self):
        original=importlib.import_module('run_reboot_cf4_injections')
        model=self.d.SelectedLaw(self.design,self.scenario,256,64)
        saved_seed=original.SEED
        try:
            original.SEED=12345
            prior=original.generate(model,n=1);now=x.generate(model,12345)
        finally:original.SEED=saved_seed
        for key in ('mu','Vh','x_log_dA','t_km_s'):np.testing.assert_array_equal(now[key],prior[key][0])
        self.assertEqual(now['eta'],prior['eta'][0])
    def test_postselection_eta_prior_and_preselection_tilt(self):
        pre=self.d.SelectedLaw(self.design,replace(self.scenario,selection_semantics=x.LABELS[0]),256,64)
        post=self.d.SelectedLaw(self.design,replace(self.scenario,selection_semantics=x.LABELS[1]),256,64)
        pp,_=x.eta_weights(pre);pq,_=x.eta_weights(post)
        self.assertAlmostEqual(float(pq@post.eta),0.,places=12)
        self.assertAlmostEqual(float(pq@(post.eta**2)),self.scenario.s_eta_mag**2,places=12)
        self.assertGreater(float(np.linalg.norm(pp-pq)),1e-5)
        for model,p in ((pre,pp),(post,pq)):
            expected=float(p@model.eta);var=float(p@(model.eta-expected)**2)
            drawn=np.random.default_rng(935).choice(model.eta,size=20000,p=p)
            self.assertLess(abs(float(drawn.mean())-expected),6*np.sqrt(var/len(drawn)))
    def test_selected_law_formula_and_generator_grid_moments(self):
        rows=x.semantic_tests(self.design,self.scenario)
        self.assertEqual(len(rows),2)
        for row in rows:self.assertLess(row['moment_grid_max_scaled_delta'],1e-4)
    def test_descendant_head_with_pinned_sources_is_admitted(self):
        with mock.patch.object(x.subprocess,'check_output',return_value='a'*40+'\n'),mock.patch.object(x.subprocess,'run',return_value=subprocess.CompletedProcess([],0)) as ancestor:
            result=x.source_identity(REPO,self.d)
        self.assertEqual(result['actual_head'],'a'*40)
        self.assertEqual(result['base_head'],x.EXPECTED_HEAD)
        self.assertIn('--is-ancestor',ancestor.call_args[0][0])
    def test_changed_scientific_source_or_nonancestor_is_rejected(self):
        with mock.patch.dict(x.SOURCE_PINS,{'law':'0'*64}):
            with self.assertRaisesRegex(ValueError,'scientific source changed'):x.source_identity(REPO,self.d)
        with mock.patch.object(x.subprocess,'run',side_effect=subprocess.CalledProcessError(1,['git'])):
            with self.assertRaises(subprocess.CalledProcessError):x.source_identity(REPO,self.d)
    def test_nonempty_output_is_rejected_and_empty_output_admitted(self):
        with tempfile.TemporaryDirectory() as temporary:
            out=Path(temporary)/'new';x.prepare_output(out)
            (out/'old.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'output directory must be empty'):x.prepare_output(out)
if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--repo',type=Path,required=True);args,rest=parser.parse_known_args()
    REPO=args.repo.resolve()
    unittest.main(argv=[sys.argv[0],*rest])
