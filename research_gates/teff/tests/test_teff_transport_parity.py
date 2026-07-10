"""TEFF v8-update gates: transport application (C5a) + Rust twin parity (C5b).

TP1 the BGK transport harness is consistent: retained (E, N) conserved to
    machine precision (grid-consistent Newton matching), the insertion-
    resolved residual decays monotonically, and the free-expansion limit
    scales T exactly as 1/a;
TP2 the predictivity answer is RECORDED HONESTLY: in the single-mode toy the
    residual and the unretained-moment error are the same functional (exact
    by construction) and this is NOT claimed as Boltzmann-closure evidence;
TP3 Rust twin parity: 3 a_BE = pi^4/15 and 3 a_FD = 7 pi^4/120 exactly, the
    Rust zeta table matches closed forms, the monopole Gram closed forms
    zeta(3)/(3 zeta(4)) and zeta(2)/(2 zeta(3)) are exact with nonzero
    determinant, and the cargo lane (when live) reports zero failures;
TP4 both seals PASS, are deterministic modulo the cargo lane, and carry the
    nonclaim/claim-boundary fields;
TP-CoVe forbidden-claim-string guard on both module docstrings.

Diagnostic-only; BGK toy != Boltzmann closure; the transport-closure nonclaim
of the Teff lane stands unchanged.
"""
import unittest

import numpy as np

from htt.teff import transport_application as ta
from htt.teff import rust_twin_parity as rp
from htt.teff.transport_application import (
    bgk_evolution, expansion_exact_limit, teff_transport_application_seal,
)
from htt.teff.rust_twin_parity import (
    constant_parity_checks, gram_structure_parity, teff_rust_parity_seal,
)


class TP1TransportHarness(unittest.TestCase):
    def test_bgk_conserves_retained_moments_and_decays(self):
        b = bgk_evolution()
        self.assertTrue(b["retained_EN_conserved_machine"])
        self.assertTrue(b["residual_decays_monotonically"])
        self.assertLess(abs(b["residual_p5_final"]),
                        abs(b["residual_p5_initial"]))

    def test_expansion_exact_limit(self):
        e = expansion_exact_limit()
        self.assertTrue(e["T_scales_exactly_one_over_a"])
        self.assertTrue(e["quadrature_T_recovery_ok"])


class TP2HonestPredictivity(unittest.TestCase):
    def test_answer_recorded_not_overclaimed(self):
        b = bgk_evolution()
        self.assertTrue(b["residual_equals_unretained_error_by_construction"])
        self.assertIn("NOT Boltzmann-closure evidence", b["finding"])
        seal = teff_transport_application_seal()
        self.assertFalse(
            seal["recorded_predictivity_answer"]["boltzmann_closure_evidence"])


class TP3RustParity(unittest.TestCase):
    def test_exact_constant_parity(self):
        p = constant_parity_checks()
        self.assertTrue(p["three_a_be_equals_pi4_over_15_exact"])
        self.assertTrue(p["three_a_fd_equals_7pi4_over_120_exact"])
        self.assertTrue(p["rust_expectations_present"])
        self.assertTrue(all(p["zeta_table_exact"].values()))
        self.assertTrue(p["apery_float_matches_mpmath_1e15"])
        self.assertTrue(p["zeta5_float_matches_mpmath_1e15"])

    def test_gram_structure_parity(self):
        g = gram_structure_parity()
        self.assertTrue(g["closed_forms_exact"])
        self.assertTrue(g["det_nonzero_wellposed"])
        self.assertTrue(g["numeric_matches_mpmath_1e14"])


class TP4SealTests(unittest.TestCase):
    def test_transport_seal(self):
        seal = teff_transport_application_seal()
        self.assertEqual(seal["status"], "PASS")
        self.assertEqual(seal["seal"], "teff.transport_application")
        self.assertEqual(seal["claim_tier"], "diagnostic_only")
        self.assertIn("NONCLAIM stands unchanged", seal["discharges"])
        self.assertEqual(seal, teff_transport_application_seal())

    def test_parity_seal(self):
        seal = teff_rust_parity_seal()
        self.assertEqual(seal["status"], "PASS")
        self.assertEqual(seal["seal"], "teff.rust_twin_parity")
        self.assertIn(seal["cargo_lane"]["mode"],
                      ("CARGO_LIVE", "REGISTERED_FALLBACK_SOURCE_ANCHORED"))
        if seal["cargo_lane"]["mode"] == "CARGO_LIVE":
            self.assertEqual(seal["cargo_lane"]["failed"], 0)


class TPCoVeAdversarialGuard(unittest.TestCase):
    FORBIDDEN_STRINGS = ("posterior", "family", "native solver", "detection")

    def test_module_docstrings_have_no_forbidden_claim_string(self):
        for mod in (ta, rp):
            doc = (mod.__doc__ or "").lower()
            for token in self.FORBIDDEN_STRINGS:
                self.assertNotIn(token, doc,
                                 f"{mod.__name__}: forbidden {token!r}")

    def test_transport_docstring_keeps_the_nonclaim(self):
        doc = " ".join((ta.__doc__ or "").lower().split())
        self.assertIn("bgk toy != boltzmann closure", doc)
        self.assertIn("nonclaim", doc)


if __name__ == "__main__":
    unittest.main()
