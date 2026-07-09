"""TEFF gates: max-entropy effective-temperature representative theory (v8).

T1  (Thm 3) radial constants a_xi = (2, 2 zeta(4), (7/4) zeta(4)) exact + numeric +
    the Gamma*zeta identity; all strictly positive.
T2  (Def 13) insertion fingerprints c_p = (p-4)/2^{p+1}: c3=-1/16, c4=0 (energy-moment
    invariance anchor), c5=1/64.
T3  (Thm 22) two-temperature ratios: R4(s)=1 pointwise; R3 = 1-(3/2)s^2, R5 = 1+(5/2)s^2
    move in opposite directions.
T4  (Thm 18/19) SO(3) shell Gram is PSD; the discarded-L^2 staircase is exactly
    non-increasing with each drop equal to the omitted shell power.
T5  (Thm 22) equal-information nonidentifiability: identical retained (p=4) moment =>
    same representative + slaved ledger, distinct residual p=3/p=5 fingerprints.
T6  (owner/claim guard) the TEFF owner may emit a teff_representative bundle at the
    diagnostic_only tier and is DISTINCT from the frozen TSC_LEGACY surface; the seal
    makes no affirmative posterior/family/detection claim.

Diagnostic-only; representation theory + exact closed forms; no data/detection/family/
native-solver/posterior claim.
"""
import unittest

from htt.teff.representative import (
    RADIAL_CONSTANTS, radial_fingerprint, two_temperature_ratio,
    gram_ledger_psd, l2_staircase_monotone,
    equal_information_nonidentifiability, teff_representative_seal,
)
import sympy as sp


class TeffRepresentativeTests(unittest.TestCase):
    def test_seal_pass(self):
        self.assertEqual(teff_representative_seal()["status"], "PASS")

    def test_radial_constants_exact(self):
        z4 = sp.zeta(4)
        self.assertEqual(RADIAL_CONSTANTS["MB"], 2)
        self.assertEqual(sp.simplify(RADIAL_CONSTANTS["BE"] / z4), 2)
        self.assertEqual(sp.simplify(RADIAL_CONSTANTS["FD"] / z4), sp.Rational(7, 4))
        self.assertTrue(all(RADIAL_CONSTANTS[k] > 0 for k in RADIAL_CONSTANTS))

    def test_insertion_fingerprints(self):
        self.assertEqual(radial_fingerprint(3), sp.Rational(-1, 16))
        self.assertEqual(radial_fingerprint(4), 0)      # p=4 anchor
        self.assertEqual(radial_fingerprint(5), sp.Rational(1, 64))

    def test_two_temperature_ratios(self):
        R4, _ = two_temperature_ratio(4)
        self.assertEqual(sp.simplify(R4 - 1), 0)         # invariant
        s = sp.symbols("s", real=True)
        R3, _ = two_temperature_ratio(3)
        R5, _ = two_temperature_ratio(5)
        c3 = sp.nsimplify(sp.series(R3, s, 0, 3).removeO().coeff(s, 2))
        c5 = sp.nsimplify(sp.series(R5, s, 0, 3).removeO().coeff(s, 2))
        self.assertEqual(c3, sp.Rational(-3, 2))
        self.assertEqual(c5, sp.Rational(5, 2))
        self.assertTrue(c3 < 0 < c5)                     # opposite directions

    def test_gram_psd_and_staircase(self):
        self.assertTrue(gram_ledger_psd()["psd"])
        stair = l2_staircase_monotone()
        self.assertTrue(stair["discarded_nonincreasing"])
        self.assertTrue(stair["drop_equals_shell_power"])

    def test_equal_information_nonidentifiability(self):
        n = equal_information_nonidentifiability()
        self.assertTrue(n["shared_p4_moment_invariant"])
        self.assertTrue(n["residual_p3_differs"])
        self.assertTrue(n["p3_p5_move_opposite"])


class TeffOwnerGuardTests(unittest.TestCase):
    def test_teff_owner_emits_teff_bundle_only(self):
        from htt.src.common.contracts import (
            Owner, BundleKind, owner_can_emit_bundle)
        self.assertTrue(owner_can_emit_bundle(Owner.TEFF, BundleKind.TEFF_REPRESENTATIVE))
        # TEFF is an active owner distinct from the frozen legacy surface
        self.assertNotEqual(Owner.TEFF, Owner.TSC_LEGACY)
        # and it does NOT get the legacy-reproduction / posterior authorities
        self.assertFalse(owner_can_emit_bundle(Owner.TEFF, BundleKind.POSTERIOR))
        self.assertFalse(owner_can_emit_bundle(Owner.TEFF, BundleKind.LEGACY_REPRODUCTION))

    def test_tsc_legacy_freeze_untouched(self):
        # additive change must not grant the legacy owner any new authority
        from htt.src.common.contracts import (
            Owner, BundleKind, owner_can_emit_bundle)
        self.assertTrue(owner_can_emit_bundle(
            Owner.TSC_LEGACY, BundleKind.LEGACY_REPRODUCTION))
        self.assertFalse(owner_can_emit_bundle(
            Owner.TSC_LEGACY, BundleKind.TEFF_REPRESENTATIVE))

    def test_seal_claim_boundary(self):
        seal = teff_representative_seal()
        self.assertEqual(seal["owner"], "TEFF")
        self.assertEqual(seal["claim_tier"], "diagnostic_only")
        doc = seal["claim_boundary"].lower()
        for banned in ("posterior", "detection", "native-solver"):
            self.assertIn("no data", doc)
            self.assertIn(banned, doc)  # appears only in the "no ... claim" disclaimer


if __name__ == "__main__":
    unittest.main()
