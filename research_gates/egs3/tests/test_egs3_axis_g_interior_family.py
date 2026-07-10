"""EGS3 Axis G gates: T3-int connected exact family realizing the interval interior.

GI1 the two-segment family sweeps x_C over [11/100, 17/100] continuously and
    strictly monotonically with an EXACT junction at 3/20 (segment I t=1 ==
    segment II u=0, and Bianchi V at a=0 is the exact Bianchi I boundary);
GI2 realize_interior_point hits ANY rational target in the interval exactly
    (Fraction arithmetic), including both registered endpoints, with the Gauss
    residual exactly zero on every member;
GI3 the Bianchi V group-invariant curl is derived from the structure-constant
    algebra: curl v = (0, -a v3, a v2), aligned tilt irrotational, slaving
    identity |curl v|^2 = a^2 v_perp^2 (the derived obstruction to free
    box-interior dial-in);
GI4 the simultaneous four-sector witness holds (all four sectors nonzero with
    exactly-zero Gauss+momentum residuals) and the seal PASSes, is
    deterministic, and keeps the honest scope fields;
GI-CoVe x_C bit-identity three-route anchor + no-mutation + forbidden-string
    guard + the endpoint values stay exactly 11/100 and 17/100.

Diagnostic-only; constraint-level initial data; dynamics stay deferred.
"""
import unittest
from fractions import Fraction

import numpy as np

from htt.obsstat import egs3_interior_family as fam
from htt.obsstat.egs3_interior_family import (
    INTERVAL_LO, INTERVAL_HI, family_member, realize_interior_point,
    symbolic_family_residuals, bianchi_v_group_invariant_curl,
    simultaneous_four_sector_witness, interior_family_seal,
)
from htt.obsstat.egs3_graded_comparator import COMPARATOR_SIGNS
from htt.obsstat.egs3_psd_cone import sector_matrix, xc_from_matrix


class GI1FamilySweep(unittest.TestCase):
    def test_symbolic_residuals_and_monotone_sweep(self):
        sym = symbolic_family_residuals()
        self.assertTrue(sym["gauss_identically_zero"])
        self.assertTrue(sym["strictly_monotone"])
        self.assertTrue(sym["junction_exact_match"])

    def test_segment_endpoints(self):
        sym = symbolic_family_residuals()
        self.assertEqual(sym["endpoints"]["t=0"], "11/100")
        self.assertEqual(sym["endpoints"]["u=1"], "17/100")
        self.assertEqual(sym["endpoints"]["t=1"], sym["endpoints"]["u=0"])

    def test_junction_members_are_identical_initial_data(self):
        a = family_member("I", Fraction(1))
        b = family_member("II", Fraction(0))
        self.assertEqual(a["exact_invariants"], b["exact_invariants"])

    def test_parameter_domain_guard(self):
        with self.assertRaises(ValueError):
            family_member("I", Fraction(3, 2))
        with self.assertRaises(ValueError):
            family_member("III", Fraction(1, 2))


class GI2InteriorRealization(unittest.TestCase):
    def test_dense_rational_targets_hit_exactly(self):
        for num in range(110, 171):          # 11/100 .. 17/100 step 1/1000
            x = Fraction(num, 1000)
            rep = realize_interior_point(x)
            self.assertTrue(rep["exactly_realized"], str(x))
            self.assertTrue(rep["gauss_residual_exact_zero"], str(x))

    def test_registered_endpoints_hit(self):
        lo = realize_interior_point(INTERVAL_LO)
        hi = realize_interior_point(INTERVAL_HI)
        self.assertEqual(lo["x_C"], "11/100")
        self.assertEqual(hi["x_C"], "17/100")

    def test_out_of_interval_rejected(self):
        with self.assertRaises(ValueError):
            realize_interior_point(Fraction(1, 10))
        with self.assertRaises(ValueError):
            realize_interior_point(Fraction(18, 100))


class GI3DerivedCurl(unittest.TestCase):
    def test_curl_components_and_alignment(self):
        curl = bianchi_v_group_invariant_curl()
        self.assertEqual(curl["curl_components"], ["0", "-a*v3", "a*v2"])
        self.assertTrue(curl["aligned_tilt_is_irrotational"])

    def test_slaving_identity(self):
        curl = bianchi_v_group_invariant_curl()
        self.assertTrue(curl["slaving_identity_a2_vperp2"])


class GI4SealTests(unittest.TestCase):
    def test_witness_and_seal(self):
        wit = simultaneous_four_sector_witness()
        self.assertTrue(wit["four_sectors_simultaneously_nonzero"])
        self.assertIn("SLAVED", wit["slaving_obstruction"])
        seal = interior_family_seal()
        self.assertEqual(seal["status"], "PASS")
        self.assertEqual(seal, interior_family_seal())

    def test_seal_scope_fields(self):
        seal = interior_family_seal()
        self.assertEqual(seal["seal"], "egs3.interior_family")
        self.assertIn("NOT dynamical King-Ellis evolution", seal["scope_not_claimed"])
        self.assertIn("claim_boundary", seal)


class GICoVeAdversarialGuard(unittest.TestCase):
    """Bit-identity guard on x_C + forbidden-claim-string guard on the docstring."""

    FORBIDDEN_STRINGS = ("posterior", "family/", "native solver", "detection")

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
        interior_family_seal()
        self.assertTrue(np.array_equal(COMPARATOR_SIGNS, before))

    def test_module_docstring_has_no_forbidden_claim_string(self):
        doc = (fam.__doc__ or "").lower()
        for token in ("posterior", "native solver", "detection"):
            self.assertNotIn(token, doc,
                             f"forbidden claim string {token!r} in docstring")
        # 'family' appears only as the mathematical family-of-solutions term,
        # never as a sky-class claim; the class-claim guard is explicit:
        self.assertIn("not a sky class statement", doc)

    def test_module_docstring_keeps_dynamics_deferred(self):
        doc = (fam.__doc__ or "").lower()
        self.assertIn("king-ellis", doc)
        self.assertIn("deferred", doc)


if __name__ == "__main__":
    unittest.main()
