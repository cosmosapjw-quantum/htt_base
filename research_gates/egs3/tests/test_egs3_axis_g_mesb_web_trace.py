"""EGS3 Axis G gates (REV-R190): MES-MESB-TRACE.

G-MT-1  primary-source transcriptions: sigma (5/3,3,3/7) confirmed by three
        sources; geodesic omega (10/3,2/15,0) by two primary; the frozen
        C1/C2 reduction reproduces eq 59 and eq 60; MESb eq(24) == MESa eq(51);
G-MT-2  companion reduced bounds: eq (8) sigma rounds to 4 alpha 1e-5; the
        vorticity envelope is an order-of-magnitude (alpha-dependent) bound;
G-MT-3  REFUTATION: in-house omega (3/4,2,2/7) at e1=0 EXCEEDS the companion
        cap (nominal AND loosest), appears in no accessible source, and the
        accel bound has no accessible source; geodesic is consistent;
G-MT-4  two candidate anchors: geodesic (precise, 3.3789e-13) and companion
        envelope (1.90e-11); freeze discipline (frozen W2_max unchanged);
G-MT-5  Wolfram second engine PASS + cross-engine anchor match;
G-MT-6  seal PASS + scope; x_C bit-identity + forbidden-string guard.
"""
import json
from pathlib import Path
import unittest

import numpy as np

from htt.obsstat.egs3_graded_comparator import COMPARATOR_SIGNS
from htt.obsstat.egs3_mesb_web_trace import (
    IN_HOUSE_COEFFS,
    candidate_anchors,
    companion_reduced_bounds,
    in_house_refutation,
    mesb_web_trace_seal,
    primary_source_transcriptions,
)
from htt.obsstat.egs3_psd_cone import sector_matrix, xc_from_matrix
from htt.tsc.admissibility.three_bound_hierarchy import W2_max as W2_max_frozen

REPO = Path(__file__).resolve().parents[3]
_SEAL = mesb_web_trace_seal()


class GMT1PrimaryTranscriptions(unittest.TestCase):
    def test_sources_confirm_sigma_and_geodesic_omega(self):
        p = primary_source_transcriptions()
        self.assertTrue(p["sigma_confirmed_by_three_sources"])
        self.assertTrue(p["geodesic_omega_confirmed_by_two_primary"])
        self.assertTrue(p["MESa"]["reduction_reproduces_eq59"])
        self.assertTrue(p["MESa"]["reduction_reproduces_eq60"])
        self.assertTrue(p["companion_deltaT"]["mesb_eq24_equals_mesa_eq51"])
        self.assertEqual(p["SAG1997"]["eq4_omega"], "(10/3) eps1 + (2/15) eps2")


class GMT2CompanionBounds(unittest.TestCase):
    def test_companion_envelope_is_order_of_magnitude(self):
        c = companion_reduced_bounds()
        self.assertTrue(c["sigma_rounding_consistent"])
        self.assertTrue(c["is_order_of_magnitude_not_coefficient_triple"])
        # faithful reading = max(eps2,eps3) = eps3 -> 5.52e-11 (not the
        # understating eps2 nominal); COBE alpha~1 -> 1.50e-10
        self.assertAlmostEqual(c["W2_companion_faithful"], 5.51816323720215e-11,
                               places=18)
        self.assertAlmostEqual(c["W2_companion_cobe_alpha1"], 1.5e-10, places=15)
        lo, hi = c["W2_companion_range"]
        self.assertLess(lo, hi)   # faithful < COBE-loose
        # faithful must NOT understate below the retired eps2 reading
        self.assertGreater(c["W2_companion_faithful"],
                           c["W2_companion_eps2_lower_only"])


class GMT3Refutation(unittest.TestCase):
    def test_in_house_refuted(self):
        r = in_house_refutation()
        # PRIMARY ground: no accessible source (alpha-independent)
        self.assertEqual(r["in_house_in_accessible_sources"], [])
        self.assertTrue(r["accel_bound_has_no_accessible_source"])
        self.assertEqual(r["in_house_omega_coeffs"], ("3/4", "2", "2/7"))
        # SECONDARY corroboration: exceeds the faithful cap, fits COBE-loose
        self.assertTrue(r["in_house_exceeds_faithful_cap"])
        self.assertTrue(r["in_house_within_cobe_cap"])   # honest: reading-dep
        self.assertTrue(r["companion_corroboration_is_reading_dependent"])
        self.assertGreater(r["excess_factor_over_faithful_cap"], 1.0)
        # geodesic stays consistent with the faithful cap
        self.assertTrue(r["geodesic_consistent_with_companion_faithful"])
        self.assertIn("REFUTED", r["verdict"])

    def test_in_house_matches_frozen_registered(self):
        # the refuted in-house omega IS the frozen registered coefficient set
        from htt.tsc.admissibility.three_bound_hierarchy import COEFFS
        self.assertEqual(IN_HOUSE_COEFFS["omega"], COEFFS["omega"])
        self.assertEqual(IN_HOUSE_COEFFS["accel"], COEFFS["accel"])


class GMT4AnchorsAndFreeze(unittest.TestCase):
    def test_two_candidate_anchors(self):
        a = candidate_anchors()
        self.assertAlmostEqual(a["A_geodesic"]["W2_max"], 3.3789222980376e-13,
                               places=20)
        self.assertTrue(a["A_geodesic"]["precise"])
        self.assertFalse(a["B_companion_envelope"]["precise"])
        self.assertIn("REFUTED", a["REFUTED_in_house"]["status"])
        # ordering geodesic < companion faithful < in-house
        self.assertLess(a["A_geodesic"]["W2_max"],
                        a["B_companion_envelope"]["W2_max_faithful"])
        self.assertLess(a["B_companion_envelope"]["W2_max_faithful"],
                        a["REFUTED_in_house"]["W2_max"])

    def test_frozen_w2_max_unchanged(self):
        from htt.obsstat.egs3_mes_provenance import eps_registry_provenance
        v = eps_registry_provenance()["ssot_registry"]["values"]
        self.assertAlmostEqual(
            W2_max_frozen(v["eps1"], v["eps2"], v["eps3"]),
            1.308680263683563e-06, places=12)


class GMT5WolframSecondEngine(unittest.TestCase):
    def test_cross_engine_match(self):
        path = REPO / "docs/generated/mesb_web_trace_wolfram_seal.json"
        self.assertTrue(path.exists(), "run scripts/run_egs3_v9_seals.py")
        wl = json.loads(path.read_text())
        if wl.get("status", "").startswith("BLOCKED"):
            self.skipTest(f"registered blocker: {wl['status']}")
        self.assertEqual(wl["status"], "PASS")
        self.assertTrue(wl["sigma_reduction_reproduces_eq59"])
        self.assertTrue(wl["omega_reduction_reproduces_eq60"])
        self.assertTrue(wl["in_house_exceeds_companion_faithful"])
        self.assertAlmostEqual(
            wl["W2_geodesic"],
            candidate_anchors()["A_geodesic"]["W2_max"], places=20)


class GMT6SealAndScope(unittest.TestCase):
    def test_seal_pass_and_scope(self):
        self.assertEqual(_SEAL["status"], "PASS")
        self.assertEqual(_SEAL["theorem_id"], "MES-MESB-TRACE")
        self.assertIn("refutation", _SEAL["scope_not_claimed"])


class GMTCoVeAdversarialGuard(unittest.TestCase):
    FORBIDDEN_STRINGS = ("posterior", "detection", "native solver",
                         "family assignment")

    def test_x_c_anchor_bit_identical(self):
        g = np.array([0.12, 0.0, 0.03, 0.0])
        via_graded = float(COMPARATOR_SIGNS @ g)
        via_trace = xc_from_matrix(sector_matrix(g))
        self.assertTrue(np.array_equal(via_graded, 0.15))
        self.assertTrue(np.array_equal(via_trace, via_graded))

    def test_module_docstring_guard(self):
        import htt.obsstat.egs3_mesb_web_trace as mod
        doc = (mod.__doc__ or "").lower()
        for token in self.FORBIDDEN_STRINGS:
            self.assertNotIn(token, doc)
        self.assertIn("refut", doc)


if __name__ == "__main__":
    unittest.main()
