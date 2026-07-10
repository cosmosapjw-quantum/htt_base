"""EGS3 Axis E gates (v9 successor): T2G general fractional-program theorem.

E-T2G-1 the 2026-07-10 refuting instance (S=[0,1], N=s, D=1+s) is INSIDE the
        retracted criterion's hypotheses and defeats it at the LOWER endpoint
        exactly (joint [0,1/2] vs product [0,1]; lower equal, upper strict);
E-T2G-2 containment I_joint subseteq I_prod holds exactly on every draw of
        the three-domain survey (positive / forced N_min=0 / signed);
E-T2G-3 the argmin/argmax per-endpoint iff holds on EVERY positive-domain
        draw and raises outside its N>0 proof domain;
E-T2G-4 the retracted sign criterion is exact on the positive domain and is
        defeated on the forced-degeneracy domain (nonempty mispredict count);
E-T2G-5 vertex attainment: an interior rational grid never beats the corner
        optimum (exact survey);
E-T2G-6 fractional_program_seal() PASS + deterministic;
E-T2G-CoVe x_C bit-identity three-route anchor + forbidden-claim-string guard.

Diagnostic-only interval algebra; frozen modules imported read-only.
"""
import unittest
from fractions import Fraction

import numpy as np

from htt.obsstat.egs3_fractional_program import (
    COUNTEREXAMPLE,
    argmin_argmax_corollary,
    counterexample_symbolic,
    endpoint_equality_report,
    fractional_program_seal,
    fractional_program_survey,
    joint_interval,
    product_interval,
    reviewer_counterexample,
    vertex_attainment_survey,
)
from htt.obsstat.egs3_graded_comparator import COMPARATOR_SIGNS
from htt.obsstat.egs3_psd_cone import sector_matrix, xc_from_matrix


class ET2G1ReviewerCounterexample(unittest.TestCase):
    def test_counterexample_defeats_retracted_criterion_at_lower_endpoint(self):
        ce = reviewer_counterexample()
        self.assertTrue(ce["retracted_criterion_predicts_strict_lower"])
        self.assertFalse(ce["strict_lower_observed"])
        self.assertTrue(ce["retracted_criterion_mispredicts_lower"])
        self.assertTrue(ce["strict_upper_observed"])

    def test_exact_interval_values(self):
        joint = joint_interval(**COUNTEREXAMPLE)
        prod = product_interval(**COUNTEREXAMPLE)
        self.assertEqual(joint, (Fraction(0), Fraction(1, 2)))
        self.assertEqual(prod, (Fraction(0), Fraction(1)))

    def test_symbolic_closure(self):
        sym = counterexample_symbolic()
        for key, val in sym.items():
            if isinstance(val, bool):
                self.assertTrue(val, key)


class ET2G2Containment(unittest.TestCase):
    def test_containment_on_all_three_domains(self):
        survey = fractional_program_survey()
        self.assertTrue(survey["containment_holds_everywhere"])
        for domain, t in survey["tally"].items():
            self.assertGreater(t["draws"], 50, domain)
            self.assertEqual(t["containment_fail"], 0, domain)


class ET2G3ArgminArgmaxCorollary(unittest.TestCase):
    def test_iff_on_positive_domain(self):
        survey = fractional_program_survey()
        self.assertTrue(survey["corollary_iff_holds_on_positive_domain"])
        self.assertGreater(survey["tally"]["positive"]["corollary_checked"], 100)

    def test_raises_outside_proof_domain(self):
        with self.assertRaises(ValueError):
            argmin_argmax_corollary(**COUNTEREXAMPLE)  # N_min == 0

    def test_pinned_positive_instance_both_strict(self):
        inst = dict(n_pt=(Fraction(1), Fraction(1)),
                    d_pt=(Fraction(1), Fraction(1)),
                    bounds=((Fraction(0), Fraction(1)),),
                    c_num=(Fraction(2),), c_den=(Fraction(1),))
        cor = argmin_argmax_corollary(**inst)
        self.assertFalse(cor["predicted_equal_lower"])
        self.assertFalse(cor["predicted_equal_upper"])
        self.assertTrue(cor["iff_holds_lower"] and cor["iff_holds_upper"])
        rep = endpoint_equality_report(**inst)
        self.assertEqual(rep["joint"], (Fraction(1), Fraction(3, 2)))
        self.assertEqual(rep["product"], (Fraction(1, 2), Fraction(3)))


class ET2G4SignCriterionDemotion(unittest.TestCase):
    def test_exact_on_positive_defeated_on_degenerate(self):
        survey = fractional_program_survey()
        self.assertTrue(survey["sign_criterion_exact_on_positive_domain"])
        self.assertTrue(survey["degenerate_domain_defeats_sign_criterion"])
        self.assertGreater(
            survey["tally"]["forced_nmin_zero"]["sign_criterion_lower_mispredicts"], 0)


class ET2G5VertexAttainment(unittest.TestCase):
    def test_interior_grid_never_beats_corners(self):
        vertex = vertex_attainment_survey()
        self.assertTrue(vertex["vertex_attainment_holds"])
        self.assertEqual(vertex["vertex_optimum_beaten"], 0)


class ET2G6Seal(unittest.TestCase):
    def test_seal_pass_and_deterministic(self):
        seal = fractional_program_seal()
        self.assertEqual(seal["status"], "PASS")
        self.assertEqual(seal["theorem_id"], "T2G")
        self.assertEqual(seal, fractional_program_seal())


class ET2GCoVeAdversarialGuard(unittest.TestCase):
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

    def test_module_docstring_carries_no_forbidden_claim_strings(self):
        import htt.obsstat.egs3_fractional_program as mod
        doc = (mod.__doc__ or "").lower()
        for token in self.FORBIDDEN_STRINGS:
            self.assertNotIn(token, doc)

    def test_survey_does_not_mutate_the_comparator(self):
        before = COMPARATOR_SIGNS.copy()
        fractional_program_survey(n_trials=30, seed=7)
        self.assertTrue(np.array_equal(before, COMPARATOR_SIGNS))
