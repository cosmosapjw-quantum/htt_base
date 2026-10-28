"""Focused algebra and failure controls for the fixed conditional-location script."""
import copy
import json
import math
import unittest
from pathlib import Path

import numpy as np
from scipy.stats import f

import compute


class ConditionalLocationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.Yk, cls.source = compute.load_rows()

    def test_full_input_reality_norm_and_fixed_ids(self):
        self.assertEqual(self.Yk.shape, (48, 42))
        self.assertEqual([x["mc_id"] for x in self.source["inputs"]["rows"]], list(range(300, 348)))
        self.assertTrue(np.isfinite(self.Yk).all())
        for item, vector in zip(self.source["inputs"]["rows"], self.Yk):
            row = json.loads(Path(item["path"]).read_text())
            self.assertTrue(np.array_equal(vector, compute.signed_alm_to_real(row)))
        row = json.loads(Path(self.source["inputs"]["rows"][0]["path"]).read_text())
        bad = copy.deepcopy(row)
        bad["E_l2_l3_l4_full_signed_m"]["2,-1"][0] += 1e-8
        with self.assertRaisesRegex(ValueError, "reality violation"):
            compute.signed_alm_to_real(bad)
        bad = copy.deepcopy(row)
        bad["B_l2_l3_l4_full_signed_m"]["2,0"][1] = 1e-8
        with self.assertRaisesRegex(ValueError, "m=0 reality"):
            compute.signed_alm_to_real(bad)

    def test_invariances_on_actual_rows(self):
        Y = self.Yk * 1e6
        rng = np.random.default_rng(77)
        base = compute.hotelling(Y)
        self.assertEqual(base["status"], "NOMINAL_GAUSSIAN_WORKING_LAW")
        row = compute.hotelling(Y[rng.permutation(48)])
        self.assertAlmostEqual(base["T2"], row["T2"], delta=1e-8 * (1 + base["T2"]))
        unit = compute.hotelling(self.Yk)
        self.assertAlmostEqual(base["T2"], unit["T2"], delta=1e-8 * (1 + base["T2"]))
        self.assertTrue(np.allclose(compute.descriptive(Y)["mean"], compute.descriptive(self.Yk)["mean"] * 1e6, rtol=1e-12, atol=1e-12))
        self.assertTrue(np.allclose(compute.descriptive(Y)["covariance"], compute.descriptive(self.Yk)["covariance"] * 1e12, rtol=1e-12, atol=1e-12))
        P = np.eye(42)[:, rng.permutation(42)]
        signs = rng.choice([-1.0, 1.0], 42)
        P = P * signs
        other = compute.hotelling(Y @ P)
        self.assertAlmostEqual(base["T2"], other["T2"], delta=1e-8 * (1 + base["T2"]))
        self.assertTrue(np.allclose(base["mean_norm_conservative_bounds_microK"], other["mean_norm_conservative_bounds_microK"], rtol=1e-8, atol=1e-8))
        Q, _ = np.linalg.qr(rng.standard_normal((42, 42)))
        rotated = compute.hotelling(Y @ Q)
        self.assertAlmostEqual(base["T2"], rotated["T2"], delta=1e-8 * (1 + base["T2"]))
        self.assertTrue(np.allclose(base["mean_norm_conservative_bounds_microK"], rotated["mean_norm_conservative_bounds_microK"], rtol=1e-8, atol=1e-8))

    def test_scalar_exact_f_and_predictive_factor(self):
        rng = np.random.default_rng(3)
        x = rng.standard_normal((48, 1)) + 0.2
        res = compute.hotelling(x)
        n = len(x)
        s = np.var(x[:, 0], ddof=1)
        exact_t2 = n * np.mean(x[:, 0])**2 / s
        self.assertAlmostEqual(res["T2"], exact_t2, places=11)
        self.assertAlmostEqual(res["F0"], exact_t2, places=11)
        self.assertAlmostEqual(res["critical_c"], f.ppf(.95, 1, n-1), places=11)
        self.assertGreater(abs(np.mean(x[:, 0])**2 / s - exact_t2), 0.1)  # missing n witness
        self.assertGreater(abs(n * np.mean(x[:, 0])**2 / np.var(x[:, 0], ddof=0) - exact_t2), 1e-4)  # ddof=n witness
        obs = 0.8
        D = (obs - np.mean(x[:, 0]))**2 / s
        predictive_F = n * (n-1) * D / ((n-1) * (n+1))
        self.assertAlmostEqual(predictive_F, D/(1 + 1/n), places=12)
        self.assertGreater(abs(predictive_F - D), 1e-6)

    def test_singular_abstains(self):
        rng = np.random.default_rng(8)
        x = rng.standard_normal((48, 42))
        x[:, -1] = x[:, 0]
        res = compute.hotelling(x)
        self.assertEqual(res["status"], "NOT_EVALUABLE")
        self.assertEqual(res["reason"], "RANK_OR_CONDITION_GATE")
        self.assertLess(res["diagnostics"]["rank"], 42)
        self.assertNotIn("T2", res)

    def test_foreground_processing_counterexample(self):
        rng = np.random.default_rng(4)
        noise = rng.standard_normal((48, 42))
        v = rng.standard_normal(42)
        # Foreground zero, processing v versus foreground v, processing zero.
        lhs = noise + np.zeros(42) + v
        rhs = noise + v + np.zeros(42)
        self.assertTrue(np.array_equal(lhs, rhs))
        for t in (1.0, 1e9):
            h = t * v
            self.assertTrue(np.allclose(noise + v + h - h, lhs, rtol=1e-12, atol=1e-6))


if __name__ == "__main__":
    unittest.main(verbosity=2)
