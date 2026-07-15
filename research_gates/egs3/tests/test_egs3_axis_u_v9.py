"""EGS3 Axis U gates (v9 successors): TSUM sum theorem + U4-v9 rerun.

U-TSUM-1 exact factorization mu3*mu5 - mu4^2 = s^2 (1-s^2)^3 and the AM-GM
         chain R_3 + R_5 >= 2 with equality iff s = 0 (symbolic, fail-closed);
U-TSUM-2 the mu-form equals the registered two_temperature_ratio expressions
         for p in {3,4,5} (no drift from the Teff lane);
U-V9-1   coverage lane: pre-registered acceptance met; the s=0 boundary row
         carries a REPORTED negative deviation within the disclosed band and
         a nonempty se-meaning label (the R2-V4 provenance repair);
U-V9-2   size lane: naive over-rejection and the Hotelling correction are
         established with disjoint Wilson CIs; the residual deviation is
         reported, not claimed away;
U-V9-3   exact-regime witnesses: known-se IM coverage analytic-exact + MC
         consistent; Gaussian/Wishart Hotelling size CI contains alpha
         (the F law exact where it claims exactness);
U-V9-4   seals PASS + deterministic provenance fields present (seeds, N,
         DGP, acceptance criterion) — the fields the v8 artifact lacked;
U-CoVe   x_C bit-identity three-route anchor + forbidden-claim-string guard.

Diagnostic-only synthetic statistics; frozen v8 modules imported read-only.
"""
import unittest

import numpy as np

from htt.obsstat.egs3_fingerprint_sum_theorem import (
    fingerprint_sum_theorem_seal,
    product_factorization,
    representative_consistency,
    sum_bound_symbolic,
)
from htt.obsstat.egs3_teff_statistical_v9 import (
    ACCEPTANCE_CRITERION,
    teff_statistical_v9_seal,
    wilson_interval,
)
from htt.obsstat.egs3_graded_comparator import COMPARATOR_SIGNS
from htt.obsstat.egs3_psd_cone import sector_matrix, xc_from_matrix

# the U4-v9 seal is Monte-Carlo heavy (~80 s); compute ONCE per gate run
_SEAL_V9 = teff_statistical_v9_seal()


class UTSUM1ExactTheorem(unittest.TestCase):
    def test_factorization_and_amgm_chain(self):
        fact = product_factorization()
        self.assertTrue(fact["factorization_exact"])
        sym = sum_bound_symbolic()
        self.assertTrue(sym["product_identity_holds"])
        self.assertTrue(sym["amgm_identity_holds"])
        self.assertTrue(sym["both_ratios_one_at_s0"])
        self.assertTrue(sym["sum_at_s1_exceeds_two"])

    def test_seal_pass_and_deterministic(self):
        seal = fingerprint_sum_theorem_seal()
        self.assertEqual(seal["status"], "PASS")
        self.assertEqual(seal["theorem_id"], "TSUM")
        self.assertEqual(seal, fingerprint_sum_theorem_seal())


class UTSUM2RepresentativeConsistency(unittest.TestCase):
    def test_mu_form_matches_registered_ratios(self):
        rep = representative_consistency()
        for key, val in rep.items():
            self.assertTrue(val, key)


class UV91CoverageLane(unittest.TestCase):
    def test_acceptance_met_with_boundary_deviation_reported(self):
        cov = _SEAL_V9["im_fingerprint_coverage_v9"]
        self.assertTrue(cov["acceptance_met"])
        s0 = cov["rows"]["endpoint_s0"]
        self.assertLess(s0["measured_deviation_from_nominal"], 0.0)
        self.assertLessEqual(abs(s0["measured_deviation_from_nominal"]), 0.01)
        self.assertIn("NOT a binomial coverage SE", s0["se_meaning"])
        for row in cov["rows"].values():
            self.assertEqual(row["n_rep"], 8000)
            self.assertLessEqual(row["wilson_halfwidth"], 0.006)


class UV92SizeLane(unittest.TestCase):
    def test_over_rejection_and_correction_with_disjoint_cis(self):
        hot = _SEAL_V9["hotelling_fingerprint_calibration_v9"]
        self.assertTrue(hot["acceptance_met"])
        nv = hot["naive_chi2"]["wilson95"]
        ht = hot["hotelling_F"]["wilson95"]
        self.assertGreater(nv[0], hot["alpha"])          # naive over-rejects
        self.assertLess(ht[1], nv[0])                    # CIs disjoint
        self.assertLessEqual(
            abs(hot["hotelling_F"]["measured_deviation_from_alpha"]), 0.025)


class UV93ExactRegimeWitnesses(unittest.TestCase):
    def test_known_se_im_witness_exact(self):
        ex = _SEAL_V9["im_exact_regime_witness"]
        self.assertTrue(ex["coverage_is_exact"])
        self.assertTrue(ex["mc_consistent_with_analytic"])

    def test_gaussian_wishart_hotelling_witness_contains_alpha(self):
        eh = _SEAL_V9["hotelling_gaussian_exact_witness"]
        self.assertTrue(eh["acceptance_met"])
        lo, hi = eh["wilson95"]
        self.assertLessEqual(lo, eh["alpha"])
        self.assertGreaterEqual(hi, eh["alpha"])


class UV94SealProvenance(unittest.TestCase):
    def test_seal_pass_with_full_provenance(self):
        self.assertEqual(_SEAL_V9["status"], "PASS")
        self.assertTrue(
            _SEAL_V9["pre_registered_acceptance"]["pre_registered"])
        cov = _SEAL_V9["im_fingerprint_coverage_v9"]
        for field in ("dgp", "seed_coverage", "seed_se_block", "n_events",
                      "n_rep", "n_se_block"):
            self.assertIn(field, cov)
        hot = _SEAL_V9["hotelling_fingerprint_calibration_v9"]
        for field in ("dgp", "seed_hotelling", "wishart_dof",
                      "mean_handling", "independence"):
            self.assertIn(field, hot)
        self.assertIn("v_ensemble_splitting",
                      _SEAL_V9["t4_assumptions_block"])

    def test_wilson_interval_sane(self):
        lo, hi = wilson_interval(95, 100)
        self.assertLess(lo, 0.95)
        self.assertGreater(hi, 0.95)
        self.assertGreater(lo, 0.85)


class UV9CoVeAdversarialGuard(unittest.TestCase):
    """Bit-identity guard on x_C + forbidden-claim-string guard."""

    FORBIDDEN_STRINGS = ("posterior", "family", "native solver", "detection")

    def test_x_c_anchor_is_bit_identical_and_exactly_0p15(self):
        g = np.array([0.12, 0.0, 0.03, 0.0])
        inline = 0.12 - 0.0 + 0.03 + 0.0
        via_graded = float(COMPARATOR_SIGNS @ g)
        via_trace = xc_from_matrix(sector_matrix(g))
        self.assertTrue(np.array_equal(via_graded, 0.15))
        self.assertTrue(np.array_equal(via_graded, inline))
        self.assertTrue(np.array_equal(via_trace, via_graded))

    def test_module_docstrings_carry_no_forbidden_claim_strings(self):
        import htt.obsstat.egs3_fingerprint_sum_theorem as m1
        import htt.obsstat.egs3_teff_statistical_v9 as m2
        for mod in (m1, m2):
            doc = (mod.__doc__ or "").lower()
            for token in self.FORBIDDEN_STRINGS:
                self.assertNotIn(token, doc)

    def test_acceptance_criterion_is_pre_registered_constant(self):
        self.assertTrue(ACCEPTANCE_CRITERION["pre_registered"])
        self.assertIn("deviation band", ACCEPTANCE_CRITERION["size_lane"])

    def test_statistical_seal_excludes_observational_instantiations(self):
        self.assertIn("excluded", _SEAL_V9["scale_honesty"])
        self.assertNotIn("CF4", _SEAL_V9["scale_honesty"])
