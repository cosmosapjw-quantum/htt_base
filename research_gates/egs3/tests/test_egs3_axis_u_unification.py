"""EGS3 Axis U gates: the MES / comparator / Teff unification lane (U1/U2/U3).

U1a the antipodal boost reduction is exact: T_+/- = T_0 e^{+/-beta},
    s = tanh(beta), and the elimination s^2 = t/(2+t) on the comparator tilt
    coordinate t = Omega_tilt/((1+w) Omega_m);
U1b the exact series pins: R_3 - 1 = -(3/4) t + (87/32) t^2, R_5 - 1 =
    +(5/4) t - (185/32) t^2, R_4 == 1 identically, and the ANTIPODAL
    SPECIFICITY pin (single-species tilt gives -(3/2), not -(3/4));
U2a the envelope proofs (polynomial root isolation, exact): 0 <= 1 - R_3 <=
    (3/2) s^2 and 0 <= R_5 - 1 <= (5/2) s^2 on 0 < s < 1;
U2b exact rational ceilings at the registered MES dipole amplitude and the
    strictly-increasing ceiling map carrying the MES ordering; the former CF4
    numeric instantiation is quarantined and excluded;
U3  the rank-deficiency schema correspondence: comparator design rank 2 with
    null {W2, Omega_k} (kinds carried), Teff response
    {{-1/16,-3/2},{0,0},{1/64,5/2}} with the retained p=4 selector exactly
    annihilating both enrichment directions, all schema predicates hold;
U-CoVe x_C bit-identity three-route anchor + no-mutation + forbidden-string
    guard + the disclosed-caveat block must be present in both seals.

Diagnostic-only; exact symbolic correspondences between registered in-repo
objects; the frozen MES/comparator modules are imported read-only.
"""
import unittest
from fractions import Fraction

import numpy as np
import sympy as sp

from htt.obsstat import egs3_teff_unification as uni
from htt.obsstat import egs3_unification_schema as sch
from htt.obsstat.egs3_teff_unification import (
    antipodal_boost_reduction, beta_channel_correspondence,
    fingerprint_envelope_proofs, fingerprint_ceilings, teff_unification_seal,
)
from htt.obsstat.egs3_unification_schema import (
    comparator_schema_instance, teff_schema_instance, schema_correspondence,
    unification_schema_seal,
)
from htt.obsstat.egs3_graded_comparator import COMPARATOR_SIGNS
from htt.obsstat.egs3_psd_cone import sector_matrix, xc_from_matrix


class U1aBoostReduction(unittest.TestCase):
    def test_reduction_identities_exact(self):
        red = antipodal_boost_reduction()
        self.assertTrue(red["boost_pole_identity_exact"])
        self.assertTrue(red["s_equals_tanh_beta_exact"])
        self.assertTrue(red["s_squared_equals_t_over_2_plus_t_exact"])

    def test_reduction_discloses_the_toy_anchor(self):
        red = antipodal_boost_reduction()
        self.assertIn("toy anchor", red["reduction_caveat"])


class U1bSeriesPins(unittest.TestCase):
    def test_leading_and_second_order_coefficients(self):
        cor = beta_channel_correspondence()
        self.assertEqual(cor["leading_R3_coeff"], "-3/4")
        self.assertEqual(cor["leading_R5_coeff"], "5/4")
        self.assertEqual(cor["second_order_R3_coeff"], "87/32")
        self.assertEqual(cor["second_order_R5_coeff"], "-185/32")
        self.assertTrue(cor["leading_coeffs_exact"])

    def test_r4_invariance_and_antipodal_specificity(self):
        cor = beta_channel_correspondence()
        self.assertTrue(cor["R4_identically_one"])
        self.assertEqual(cor["single_species_R3_coeff"], "-3/2")
        self.assertTrue(cor["antipodal_specificity_pin"])


class U2aEnvelopeProofs(unittest.TestCase):
    def test_all_four_envelopes_proved_exactly(self):
        env = fingerprint_envelope_proofs()
        self.assertTrue(env["all_envelopes_proved"])
        for name, ok in env["proofs"].items():
            self.assertTrue(ok, name)

    def test_pointwise_ordering_is_numeric_only_and_positive(self):
        env = fingerprint_envelope_proofs()
        self.assertGreater(env["pointwise_sum_ordering_numeric_min"], 0.0)
        self.assertIn("numerically", env["pointwise_sum_ordering_note"])


class U2bCeilings(unittest.TestCase):
    def test_exact_rational_ceilings(self):
        ceil = fingerprint_ceilings()
        self.assertEqual(ceil["eps1_exact_rational"], "771/625000")
        self.assertEqual(ceil["ceiling_R3_exact"], "1783323/781250000000")
        self.assertEqual(ceil["ceiling_R5_exact"], "594441/156250000000")
        self.assertTrue(ceil["endpoints_within_quadratic_envelopes"])

    def test_mes_ordering_carries_to_ceilings(self):
        ceil = fingerprint_ceilings()
        self.assertTrue(ceil["ceiling_map_strictly_increasing"])
        self.assertTrue(ceil["mes_ordering_holds"])
        self.assertTrue(ceil["ordered_ceiling_triple_from_mes_budgets"])
        self.assertIn("NOT three physical rapidity ceilings",
                      ceil["ordered_ceiling_disclosure"])

    def test_cf4_numeric_instantiation_is_quarantined(self):
        ceil = fingerprint_ceilings()
        blocked = ceil["cf4_numeric_instantiation"]
        self.assertEqual(blocked["status"], "QUARANTINED_OPEN_P0")
        self.assertIsNone(blocked["replacement_value"])
        self.assertEqual(
            blocked["finding_ids"],
            ["C1-K5-MV-F1", "N-DATA-CF4-DOWNSTREAM"],
        )


class U3Schema(unittest.TestCase):
    def test_comparator_instance(self):
        comp = comparator_schema_instance()
        self.assertEqual(comp["rank_exact"], 2)
        self.assertEqual(sorted(comp["null_sectors"]), ["Omega_k", "W2"])
        self.assertEqual(comp["null_sector_kinds"]["W2"], "structural_null")
        self.assertEqual(comp["null_sector_kinds"]["Omega_k"],
                         "no_channel_leading_order")

    def test_teff_instance(self):
        teff = teff_schema_instance()
        self.assertTrue(teff["matches_registered_constants"])
        self.assertTrue(teff["retained_selector_annihilates_both_directions"])
        self.assertTrue(teff["R4_identically_one"])
        self.assertEqual(teff["rank_exact_full_response"], 2)

    def test_all_schema_predicates(self):
        cor = schema_correspondence()
        self.assertTrue(cor["all_predicates_hold"])
        self.assertIn("MATHEMATICAL", cor["correspondence_kind"])


class USealTests(unittest.TestCase):
    def test_both_seals_pass_and_are_deterministic(self):
        s1 = teff_unification_seal()
        s2 = unification_schema_seal()
        self.assertEqual(s1["status"], "PASS")
        self.assertEqual(s2["status"], "PASS")
        self.assertEqual(s1, teff_unification_seal())
        self.assertEqual(s2, unification_schema_seal())

    def test_seal_names_and_caveats(self):
        s1 = teff_unification_seal()
        s2 = unification_schema_seal()
        self.assertEqual(s1["seal"], "egs3.teff_unification")
        self.assertEqual(s2["seal"], "egs3.unification_schema")
        self.assertGreaterEqual(len(s1["disclosed_caveats"]), 5)
        self.assertIn("claim_boundary", s1)
        self.assertIn("claim_boundary", s2)


class UCoVeAdversarialGuard(unittest.TestCase):
    """Bit-identity guard on x_C + forbidden-claim-string guard on docstrings."""

    FORBIDDEN_STRINGS = ("posterior", "native solver", "detection")

    def test_x_c_anchor_is_bit_identical_and_exactly_0p15(self):
        g = np.array([0.12, 0.0, 0.03, 0.0])
        inline = 0.12 - 0.0 + 0.03 + 0.0
        via_graded = float(COMPARATOR_SIGNS @ g)
        via_trace = xc_from_matrix(sector_matrix(g))
        self.assertTrue(np.array_equal(via_graded, 0.15))
        self.assertTrue(np.array_equal(via_graded, inline))
        self.assertTrue(np.array_equal(via_trace, via_graded))

    def test_seals_do_not_mutate_the_comparator(self):
        before = COMPARATOR_SIGNS.copy()
        teff_unification_seal()
        unification_schema_seal()
        self.assertTrue(np.array_equal(COMPARATOR_SIGNS, before))

    def test_module_docstrings_have_no_forbidden_claim_string(self):
        for mod in (uni, sch):
            doc = (mod.__doc__ or "").lower()
            for token in self.FORBIDDEN_STRINGS:
                self.assertNotIn(token, doc,
                                 f"{mod.__name__}: forbidden {token!r}")

    def test_docstrings_carry_the_disclosures(self):
        doc = " ".join((uni.__doc__ or "").lower().split())
        self.assertIn("toy anchor", doc)
        self.assertIn("not a predicted cmb spectral distortion", doc)
        doc2 = " ".join((sch.__doc__ or "").lower().split())
        self.assertIn("mathematical", doc2)


if __name__ == "__main__":
    unittest.main()
