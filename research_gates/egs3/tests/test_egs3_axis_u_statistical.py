"""EGS3 Axis U gates (U4): statistical closure over the Teff fingerprint lane
+ the K5 v8 card extension.

US1 the forward model's population anchors are exact: the moment-ratio
    estimators are centered on the Teff two_temperature_ratio values;
US2 IM coverage holds on the identified fingerprint interval at the
    endpoints and interior (seeded, binomial 3-sigma band);
US3 the estimated-covariance joint fingerprint over-rejects under the naive
    chi^2 threshold and is calibrated by the Hotelling/F correction (the T4'
    phenomenon reproduced on the Teff observables);
US4 the K5 v8 card artifact is check-current, keeps the plugin firewall
    (observational_claim_allowed False, Omega_k PLUGIN + documented null) and
    carries the deterministic Teff fingerprint row below the MES ceiling;
US-CoVe x_C bit-identity three-route anchor + forbidden-string guard.

Diagnostic-only; display-scale experiments disclosed; no measurement claim.
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

import numpy as np

from htt.obsstat import egs3_teff_statistical as ts
from htt.obsstat.egs3_teff_statistical import (
    true_ratio, sample_fingerprints, im_fingerprint_coverage,
    hotelling_fingerprint_calibration, teff_statistical_seal,
)
from htt.obsstat.egs3_graded_comparator import COMPARATOR_SIGNS
from htt.obsstat.egs3_psd_cone import sector_matrix, xc_from_matrix

REPO = Path(__file__).resolve().parents[3]


class US1PopulationAnchors(unittest.TestCase):
    def test_estimator_centered_on_teff_ratio(self):
        rng = np.random.default_rng(7)
        s = 0.3
        r3 = np.mean([sample_fingerprints(s, 4000, rng)[0]
                      for _ in range(300)])
        self.assertAlmostEqual(r3, true_ratio(3, s), places=2)

    def test_true_ratio_monotone_down_in_s(self):
        self.assertLess(true_ratio(3, 0.3), true_ratio(3, 0.15))
        self.assertLess(true_ratio(3, 0.15), 1.0)
        self.assertGreater(true_ratio(5, 0.3), 1.0)


class US2Coverage(unittest.TestCase):
    def test_im_coverage_everywhere(self):
        cov = im_fingerprint_coverage()
        self.assertTrue(cov["coverage_holds_everywhere"])
        floor = cov["nominal"] - cov["binomial_3sigma_tol"]
        for name, row in cov["rows"].items():
            self.assertGreaterEqual(row["coverage"], floor, name)


class US3Hotelling(unittest.TestCase):
    def test_naive_over_rejects_hotelling_calibrates(self):
        hot = hotelling_fingerprint_calibration()
        self.assertTrue(hot["naive_over_rejects"])
        self.assertTrue(hot["hotelling_calibrated"])
        self.assertGreater(hot["empirical_size_naive_chi2"],
                           hot["empirical_size_hotelling_F"])


class US4CardExtension(unittest.TestCase):
    def test_card_check_current(self):
        import os
        r = subprocess.run(
            [sys.executable, "scripts/k5_cf4_identified_interval_card_v8.py",
             "--check"], cwd=REPO, capture_output=True, text=True, timeout=300,
            env={**os.environ,
                 "PYTHONPATH": f"{REPO}:{REPO}/htt:{REPO}/htt/htt"})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_card_firewall_and_fingerprint_row(self):
        card = json.loads(
            (REPO / "docs/generated/k5_cf4_identified_interval_card_v8.json")
            .read_text())
        self.assertFalse(card["observational_claim_allowed"])
        row = card["v8_teff_fingerprint_row"]
        self.assertTrue(row["not_a_measurement"])
        self.assertTrue(row["fingerprint_below_ceiling"])
        self.assertIn("PLUGIN/BLOCKED", card["v8_omega_k_status"]["input_mode"])
        self.assertIn("DOCUMENTED NULL",
                      card["v8_omega_k_status"]["external_prior_branch"])

    def test_card_references_frozen_v7_base(self):
        card = json.loads(
            (REPO / "docs/generated/k5_cf4_identified_interval_card_v8.json")
            .read_text())
        base = card["based_on_frozen_v7_card"]
        self.assertEqual(len(base["sha256"]), 64)
        frozen = REPO / base["path"]
        import hashlib
        self.assertEqual(hashlib.sha256(frozen.read_bytes()).hexdigest(),
                         base["sha256"])


class USSealTests(unittest.TestCase):
    def test_seal_passes(self):
        seal = teff_statistical_seal()
        self.assertEqual(seal["status"], "PASS")
        self.assertEqual(seal["seal"], "egs3.teff_statistical")
        self.assertIn("scale_honesty", seal)


class USCoVeAdversarialGuard(unittest.TestCase):
    FORBIDDEN_STRINGS = ("posterior", "native solver", "detection")

    def test_x_c_anchor_is_bit_identical_and_exactly_0p15(self):
        g = np.array([0.12, 0.0, 0.03, 0.0])
        inline = 0.12 - 0.0 + 0.03 + 0.0
        via_graded = float(COMPARATOR_SIGNS @ g)
        via_trace = xc_from_matrix(sector_matrix(g))
        self.assertTrue(np.array_equal(via_graded, 0.15))
        self.assertTrue(np.array_equal(via_graded, inline))
        self.assertTrue(np.array_equal(via_trace, via_graded))

    def test_module_docstring_has_no_forbidden_claim_string(self):
        doc = (ts.__doc__ or "").lower()
        for token in self.FORBIDDEN_STRINGS:
            self.assertNotIn(token, doc,
                             f"forbidden claim string {token!r} in docstring")

    def test_scale_honesty_disclosed(self):
        doc = " ".join((ts.__doc__ or "").lower().split())
        self.assertIn("never as a pretended measurement", doc)


if __name__ == "__main__":
    unittest.main()
