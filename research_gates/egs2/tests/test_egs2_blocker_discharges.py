"""EGS2 gates: BLOCK-K1 E2E max-scan discharge, BLOCK-K6 Hoffman-Ribak CR posterior."""
import unittest
import numpy as np

from htt.obsstat.lowell_global_calibration import e2e_maxscan_from_summaries
from htt.obsstat.constrained_realizations import curl_posterior, wiener_filter_mean


class K1E2EDischargeTests(unittest.TestCase):
    def test_global_p_ge_min_local_with_plus_one(self):
        rng = np.random.default_rng(1234)
        n_e2e, n_stat = 300, 6
        e2e = rng.normal(size=(n_e2e, n_stat))
        observed = rng.normal(size=n_stat)
        observed[1] = 3.5  # a locally extreme statistic
        directions = ["high"] + ["two-sided"] * (n_stat - 1)
        out = e2e_maxscan_from_summaries(observed, e2e, directions)
        self.assertEqual(out["n_e2e"], n_e2e)
        self.assertGreaterEqual(out["global_p"], min(out["local_p"]))   # no LEE undercount
        self.assertGreater(out["global_p"], 0.0)
        self.assertLessEqual(out["global_p"], 1.0)
        self.assertEqual(out["blocker_until_real_maps"], "BLOCKED_MISSING_PR4_E2E_ACCESS")


class K6CRPosteriorTests(unittest.TestCase):
    def test_wf_curl_suppressed_cr_carries_posterior(self):
        post = curl_posterior(signal_var=1.0, noise_var=0.5, n_cr=400, seed=4242)
        # WF mean of an unconstrained curl mode is exactly suppressed
        self.assertEqual(post.wf_estimate, 0.0)
        self.assertEqual(wiener_filter_mean(0.0, 1.0, 0.5), 0.0)
        # the CR ensemble has a nonzero prior-width spread (the posterior)
        self.assertGreater(post.cr_sd, 0.3)
        self.assertLess(abs(post.cr_mean), 0.5)        # posterior mean ~0
        self.assertLess(post.cr_p16, post.cr_p84)


if __name__ == "__main__":
    unittest.main()
