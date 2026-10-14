"""Exact small laws + misuse rejection, independent of synthetic PASS cutoffs."""
import copy
import importlib.util
import itertools
from pathlib import Path
import unittest

import numpy as np
from scipy.stats import binom

SPEC = importlib.util.spec_from_file_location("reboot_statistics", Path(__file__).resolve().parents[1]/"scripts"/"calibrate_reboot_statistics.py")
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def declaration(B=3, d=2):
    return {"analysis_label":"SYNTHETIC TEST ONLY", "declaration_id":"test-v1", "null_model_id":"test-fixed-null",
        "fixed_B":B,"fixed_budget_before_scores":True,"statistics_predeclared":True,
        "joint_row_generation":True,"observed_exchangeable_under_null":True,
        "null_draw_law":"iid_joint_vectors","independence_unit":"latent_sky_realization",
        "observed_realization_id":"observed","null_realization_ids":[f"null-{i}" for i in range(B)],
        "observation_pipeline":"test-v1","null_pipeline":"test-v1","transformation":"fixed_affine",
        "statistics":[{"name":f"feature-{i}","tail":"upper"} for i in range(d)]}


class CalibrationTests(unittest.TestCase):
    def test_ties_and_minimum_rank(self):
        self.assertEqual(m.conservative_rank(2,[1,2,3])["p_rank"], .75)
        self.assertEqual(m.conservative_rank(5,[1,2,3])["p_rank"], .25)
        self.assertEqual(m.conservative_rank(1,[1,1,1])["p_rank"], 1)

    def test_exact_exchangeable_superuniform_with_ties(self):
        # Uniformly designate the observation within a fixed exchangeable pool.
        # Enumerating all index permutations includes multiplicity of tied values.
        for pool in ([0,1,2,3],[0,0,1,2],[1,1,1,1]):
            ps = [m.conservative_rank(pool[p[0]],[pool[i] for i in p[1:]])["p_rank"]
                  for p in itertools.permutations(range(4))]
            for alpha in (.1,.25,.5,.75,1):
                self.assertLessEqual(np.mean(np.array(ps)<=alpha),alpha+1e-15)

    def test_clopper_pearson_target_and_exact_coverage(self):
        n = 12
        for q in np.linspace(0,1,41):
            intervals = [m.null_tail_interval(k,n) for k in range(n+1)]
            coverage = sum(binom.pmf(k,n,q) for k,(lo,hi) in enumerate(intervals) if lo <= q <= hi)
            self.assertGreaterEqual(coverage, .95-1e-12)
        self.assertEqual(m.null_tail_interval(0,n)[0],0)
        self.assertEqual(m.null_tail_interval(n,n)[1],1)
        rank = m.conservative_rank(10,[0,1,2])
        self.assertEqual(rank["q_hat"],0)
        self.assertEqual(rank["p_rank"],.25)

    def test_joint_max_adjustment_and_duplicate_channels(self):
        observed = np.array([2.,-1.])
        null = np.array([[0.,3.],[1.,2.],[3.,0.]])
        result = m.calibrate(observed,null,declaration())
        self.assertEqual(result["global_joint_null"]["p_rank"],1)
        self.assertTrue(all(f["joint_max_adjusted"]["p_rank"] >= f["unadjusted"]["p_rank"] for f in result["features"]))
        duplicate = m.calibrate([2,2],np.array([[0,0],[1,1],[3,3]]),declaration())
        self.assertEqual(duplicate["global_joint_null"]["p_rank"],.5)
        self.assertEqual(duplicate["features"][0]["unadjusted"]["p_rank"],.5)

    def test_signed_lower_and_two_sided(self):
        meta = declaration()
        meta["statistics"][0]["tail"]="lower"
        meta["statistics"][1]["tail"]="two-sided"
        result = m.calibrate([-3.,-2.],np.array([[0,0],[-1,1],[1,-3]]),meta)
        self.assertEqual(result["features"][0]["signed_transformed_observed"],-3)
        self.assertEqual(result["features"][0]["unadjusted"]["observed_score"],3)
        self.assertEqual(result["features"][1]["unadjusted"]["p_rank"],.5)

    def test_affine_unit_invariance(self):
        meta = declaration()
        a = m.calibrate([2,-1],[[0,3],[1,2],[3,0]],meta)
        meta["statistics"][0].update(center=1000,scale=.0001)
        meta["statistics"][1].update(center=-15,scale=20)
        b = m.calibrate([1000+2*.0001,-15-20],[[1000,-15+60],[1000+.0001,-15+40],[1000+.0003,-15]],meta)
        self.assertEqual(a["global_joint_null"]["p_rank"],b["global_joint_null"]["p_rank"])

    def test_budget_nonfinite_and_false_attestations(self):
        meta = declaration()
        for key in ("fixed_budget_before_scores","statistics_predeclared","joint_row_generation","observed_exchangeable_under_null"):
            bad = copy.deepcopy(meta); bad[key] = False
            with self.assertRaises(ValueError):
                m.calibrate([0,0],np.zeros((3,2)),bad)
        with self.assertRaises(ValueError):
            m.calibrate([0,0],np.zeros((2,2)),meta)
        with self.assertRaises(ValueError):
            m.calibrate([np.nan,0],np.zeros((3,2)),meta)
        with self.assertRaises(ValueError):
            m.calibrate([0,0],np.zeros((3,2)),meta,alpha=0)

    def test_same_sky_pseudoreplication_rejected(self):
        meta = declaration()
        meta["null_realization_ids"]=["sky-1","sky-1","sky-2"]
        with self.assertRaisesRegex(ValueError,"pseudo-replication"):
            m.calibrate([0,0],np.zeros((3,2)),meta)
        meta = declaration(); meta["independence_unit"]="map_product"
        with self.assertRaisesRegex(ValueError,"never map product"):
            m.calibrate([0,0],np.zeros((3,2)),meta)

    def test_training_split_and_singular_channels(self):
        meta = declaration()
        meta.update(transformation="independent_training_z",training_pipeline="test-v1",
                    training_independent_of_observed_and_calibration=True,
                    training_realization_ids=["train-1","train-2","train-3"])
        training = np.array([[1,1],[2,2],[3,3.]])
        result = m.calibrate([4,4],[[1,1],[2,2],[3,3]],meta,training)
        self.assertFalse(result["transformation"]["covariance_inverse_used"])
        # Exactly singular joint covariance is harmless: correlated columns retained.
        self.assertEqual(result["global_joint_null"]["p_rank"], .25)
        bad = copy.deepcopy(meta); bad["training_realization_ids"][0]="null-0"
        with self.assertRaisesRegex(ValueError,"overlap"):
            m.calibrate([4,4],[[1,1],[2,2],[3,3]],bad,training)
        with self.assertRaisesRegex(ValueError,"constant or numerically unresolved"):
            m.calibrate([4,4],[[1,1],[2,2],[3,3]],meta,np.ones((3,2)))

    def test_observation_reuse_and_pipeline_mismatch(self):
        meta = declaration(); meta["null_realization_ids"][0]="observed"
        with self.assertRaisesRegex(ValueError,"observation reused"):
            m.calibrate([0,0],np.zeros((3,2)),meta)
        meta = declaration(); meta["null_pipeline"]="different"
        with self.assertRaisesRegex(ValueError,"pipelines must match"):
            m.calibrate([0,0],np.zeros((3,2)),meta)


if __name__ == "__main__":
    unittest.main()
