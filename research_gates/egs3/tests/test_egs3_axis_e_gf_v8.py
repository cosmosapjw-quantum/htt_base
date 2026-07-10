"""EGS3 Axis E gates (v8 successor): signed-numerator exact quotient path (T2'').

E-V8-1 the registered negative-numerator configuration exhibits the frozen v7
        pairing defect exactly (frozen interval fails containment of the true
        extremes) while the v8 four-candidate path matches the independent
        dense-grid Fraction verifier bit-exactly;
E-V8-2 on the documented nonnegative-shifted-numerator domain the v8 selector
        reproduces the frozen v7 selector bit-exactly (every frozen v7 result
        is unaffected);
E-V8-3 joint subseteq naive containment holds EXACTLY on every signed-domain
        draw; the v7 sign-conflict strictness criterion is only measured there
        (its proof domain stays the nonnegative-numerator region);
E-V8-4 gf_interval_v8_seal() PASS, deterministic, records the successor
        provenance and never mutates the frozen module;
E-V8-CoVe x_C bit-identity three-route anchor + forbidden-claim-string guard.

Diagnostic-only interval algebra; the frozen v7 module is imported read-only.
"""
import unittest
from fractions import Fraction

import numpy as np

from htt.obsstat import egs3_gf_interval as frozen
from htt.obsstat import egs3_gf_interval_v8 as v8
from htt.obsstat.egs3_gf_interval_v8 import (
    exact_joint_interval_v8, exact_naive_quotient_v8,
    negative_numerator_discrepancy_witness,
    positive_domain_containment_witness,
    signed_domain_strictness_survey, gf_interval_v8_seal,
)
from htt.obsstat.egs3_graded_comparator import COMPARATOR_SIGNS
from htt.obsstat.egs3_psd_cone import sector_matrix, xc_from_matrix


class EV81NegativeNumeratorDefect(unittest.TestCase):
    def test_registered_case_shows_v7_defect_and_v8_correctness(self):
        wit = negative_numerator_discrepancy_witness()
        self.assertTrue(wit["v8_matches_brute_force_exactly"])
        self.assertTrue(wit["v7_fails_containment_on_negative_domain"])

    def test_exact_interval_values_on_registered_case(self):
        wit = negative_numerator_discrepancy_witness()
        self.assertEqual(wit["v8_interval"], ["-3/4", "-19/49"])
        self.assertEqual(wit["v7_frozen_interval"], ["-3/5", "-19/39"])

    def test_frozen_module_behavior_is_unchanged(self):
        # the frozen pairing still returns its historical (defective) interval
        # on the registered case -- proof the frozen source was not edited.
        cfg = v8._NEG_CASE
        got = frozen._exact_joint_interval(cfg["n_pt"], cfg["d_pt"],
                                           cfg["bounds"], cfg["c_num"],
                                           cfg["c_den"])
        self.assertEqual(got, (Fraction(-3, 5), Fraction(-19, 39)))


class EV82PositiveDomainBitExact(unittest.TestCase):
    def test_bit_exact_agreement_on_documented_domain(self):
        wit = positive_domain_containment_witness()
        self.assertTrue(wit["all_bit_exact"])
        self.assertGreater(wit["trials_evaluated"], 100)


class EV83SignedDomainContainment(unittest.TestCase):
    def test_containment_holds_on_every_signed_draw(self):
        survey = signed_domain_strictness_survey()
        self.assertTrue(survey["containment_always"])
        self.assertGreater(survey["trials_evaluated"], 200)

    def test_criterion_is_measured_not_claimed_on_signed_domain(self):
        survey = signed_domain_strictness_survey()
        self.assertIn("observation", survey["criterion_claim_domain"])

    def test_denominator_positivity_guard_returns_no_result(self):
        got = exact_joint_interval_v8(
            (Fraction(1), Fraction(2)), (Fraction(1, 10), Fraction(1, 5)),
            ((Fraction(0), Fraction(1)),), (Fraction(0),), (Fraction(-1),))
        self.assertIsNone(got)

    def test_naive_guard_returns_no_result(self):
        got = exact_naive_quotient_v8(
            (Fraction(1), Fraction(2)), (Fraction(1, 10), Fraction(1, 5)),
            ((Fraction(0), Fraction(1)),), (Fraction(0),), (Fraction(-1),))
        self.assertIsNone(got)


class EV84SealTests(unittest.TestCase):
    def test_seal_passes_and_is_deterministic(self):
        seal = gf_interval_v8_seal()
        self.assertEqual(seal["status"], "PASS")
        self.assertEqual(seal, gf_interval_v8_seal())

    def test_seal_records_successor_provenance(self):
        seal = gf_interval_v8_seal()
        self.assertEqual(seal["seal"], "egs3.gf_interval_v8")
        self.assertIn("egs3_gf_interval.py", seal["successor_of"])
        self.assertTrue(seal["frozen_module_untouched"])
        self.assertIn("claim_boundary", seal)


class EV8CoVeAdversarialGuard(unittest.TestCase):
    """Bit-identity guard on x_C + forbidden-claim-string guard on the docstring."""

    FORBIDDEN_STRINGS = ("posterior", "family", "native solver", "detection")

    def test_x_c_anchor_is_bit_identical_and_exactly_0p15(self):
        g = np.array([0.12, 0.0, 0.03, 0.0])
        inline = 0.12 - 0.0 + 0.03 + 0.0
        via_graded = float(COMPARATOR_SIGNS @ g)
        via_trace = xc_from_matrix(sector_matrix(g))
        self.assertTrue(np.array_equal(via_graded, 0.15))
        self.assertTrue(np.array_equal(via_graded, inline))
        self.assertTrue(np.array_equal(via_trace, via_graded))

    def test_seal_does_not_mutate_the_comparator(self):
        before = COMPARATOR_SIGNS.copy()
        gf_interval_v8_seal()
        self.assertTrue(np.array_equal(COMPARATOR_SIGNS, before))

    def test_module_docstring_has_no_forbidden_claim_string(self):
        doc = (v8.__doc__ or "").lower()
        for token in self.FORBIDDEN_STRINGS:
            self.assertNotIn(token, doc,
                             f"forbidden claim string {token!r} in docstring")

    def test_module_docstring_documents_the_domain(self):
        doc = (v8.__doc__ or "").lower()
        self.assertIn("signed", doc)
        self.assertIn("frozen", doc)


if __name__ == "__main__":
    unittest.main()
