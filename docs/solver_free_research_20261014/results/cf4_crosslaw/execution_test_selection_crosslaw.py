#!/usr/bin/env python3
"""Narrow scientific tests for new eta semantics and unchanged preselection generator."""
import argparse, importlib, sys, unittest
from pathlib import Path
from dataclasses import replace
import numpy as np
import run_selection_crosslaw as x
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
if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--repo',type=Path,required=True);args,rest=parser.parse_known_args()
    REPO=args.repo.resolve()
    unittest.main(argv=[sys.argv[0],*rest])
