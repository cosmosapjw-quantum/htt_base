"""EGS3 Axis G gates (REV-R187/R188): MES-REFREEZE.

G-MR-1  geodesic reduction: the primary-source raw MESa bounds reduce
        (C1/C2, two engines) to sigma (5/3,3,3/7) and omega (10/3,2/15,0);
        the omega triple differs from the previously-registered (3/4,2,2/7);
G-MR-2  hierarchy-preservation theorem: e1_crit = 43 e2/25 + 9 e3/35 exact;
        the observed dipole EXCEEDS it (full-dipole geodesic hierarchy
        VIOLATED) and e1 = 0 restores it -- the constraint that forces the
        re-freeze target;
G-MR-3  the re-frozen anchor: geodesic coeffs + e1 = 0 give
        W2_max = 3.3789e-13 (strict hierarchy), equal to the v9
        branch-registry sag_consistent value;
G-MR-4  freeze discipline: the frozen three_bound_hierarchy W2_max
        (1.3087e-6) is UNCHANGED (successor pattern); the re-freeze is the
        LIVE anchor;
G-MR-5  Wolfram second engine PASS + exact W2_max cross-engine match;
G-MR-6  seal PASS + scope; x_C bit-identity + forbidden-string guard.
"""
import json
from pathlib import Path
import unittest

import numpy as np

from htt.obsstat.egs3_graded_comparator import COMPARATOR_SIGNS
from htt.obsstat.egs3_mes_geodesic_refreeze import (
    REFROZEN_COEFFS,
    REFROZEN_EPS1,
    geodesic_reduction,
    hierarchy_preservation_theorem,
    mes_geodesic_refreeze_seal,
    refrozen_anchor,
)
from htt.obsstat.egs3_psd_cone import sector_matrix, xc_from_matrix
from htt.tsc.admissibility.three_bound_hierarchy import W2_max as W2_max_frozen

REPO = Path(__file__).resolve().parents[3]
_SEAL = mes_geodesic_refreeze_seal()


class GMR1GeodesicReduction(unittest.TestCase):
    def test_reduces_to_geodesic_two_engines(self):
        r = geodesic_reduction()
        self.assertTrue(r["sigma_matches_eq59"])
        self.assertTrue(r["omega_matches_eq60"])
        self.assertTrue(r["sigma_symbolic_ok"])
        self.assertTrue(r["omega_symbolic_ok"])
        self.assertTrue(r["differs_from_previously_registered_omega"])


class GMR2HierarchyTheorem(unittest.TestCase):
    def test_e1_crit_and_forcing(self):
        h = hierarchy_preservation_theorem()
        self.assertTrue(h["e1_crit_matches_derivation"])
        self.assertTrue(h["observed_e1_exceeds_crit"])
        self.assertFalse(h["full_dipole_hierarchy_holds"])
        self.assertTrue(h["e1_zero_hierarchy_holds"])


class GMR3RefrozenAnchor(unittest.TestCase):
    def test_anchor_value_and_hierarchy(self):
        a = refrozen_anchor()
        self.assertAlmostEqual(a["W2_max"], 3.3789222980376e-13, places=20)
        self.assertTrue(a["hierarchy_strict"])
        self.assertEqual(REFROZEN_EPS1, 0)
        self.assertEqual(REFROZEN_COEFFS["omega"][2], 0)   # no octopole
        self.assertEqual(REFROZEN_COEFFS["accel"],
                         (0, 0, 0))                        # geodesic

    def test_matches_branch_registry_sag_consistent(self):
        from htt.obsstat.egs3_mes_branch_registry import w2_ceiling_branches
        br = w2_ceiling_branches()
        sag = br["sag_consistent"]["value_float"]
        self.assertAlmostEqual(refrozen_anchor()["W2_max"], sag, places=20)


class GMR4FreezeDiscipline(unittest.TestCase):
    def test_frozen_anchor_unchanged(self):
        # the frozen three_bound_hierarchy value is preserved byte-identical
        from htt.obsstat.egs3_mes_provenance import eps_registry_provenance
        v = eps_registry_provenance()["ssot_registry"]["values"]
        frozen = W2_max_frozen(v["eps1"], v["eps2"], v["eps3"])
        self.assertAlmostEqual(frozen, 1.308680263683563e-06, places=12)
        # and the re-frozen live anchor is strictly below it
        self.assertLess(refrozen_anchor()["W2_max"], frozen)


class GMR5WolframSecondEngine(unittest.TestCase):
    def test_cross_engine_w2_match(self):
        path = REPO / "docs/generated/mes_geodesic_refreeze_wolfram_seal.json"
        self.assertTrue(path.exists(), "run scripts/run_egs3_v9_seals.py")
        wl = json.loads(path.read_text())
        if wl.get("status", "").startswith("BLOCKED"):
            self.skipTest(f"registered blocker: {wl['status']}")
        self.assertEqual(wl["status"], "PASS")
        self.assertTrue(wl["checks"]["cross_engine_W2_max_match_sympy"])
        self.assertAlmostEqual(wl["W2_max_refrozen"],
                               refrozen_anchor()["W2_max"], places=20)


class GMR6SealAndScope(unittest.TestCase):
    def test_seal_pass_and_scope(self):
        self.assertEqual(_SEAL["status"], "PASS")
        self.assertEqual(_SEAL["theorem_id"], "MES-REFREEZE")
        self.assertIn("re-freeze", _SEAL["scope_not_claimed"])
        self.assertTrue(_SEAL["refreeze_provenance"][
            "matches_v9_branch_registry_sag_consistent"])


class GMRCoVeAdversarialGuard(unittest.TestCase):
    FORBIDDEN_STRINGS = ("posterior", "detection", "native solver",
                         "family assignment")

    def test_x_c_anchor_bit_identical(self):
        g = np.array([0.12, 0.0, 0.03, 0.0])
        via_graded = float(COMPARATOR_SIGNS @ g)
        via_trace = xc_from_matrix(sector_matrix(g))
        self.assertTrue(np.array_equal(via_graded, 0.15))
        self.assertTrue(np.array_equal(via_trace, via_graded))

    def test_module_docstring_guard(self):
        import htt.obsstat.egs3_mes_geodesic_refreeze as mod
        doc = (mod.__doc__ or "").lower()
        for token in self.FORBIDDEN_STRINGS:
            self.assertNotIn(token, doc)
        self.assertIn("re-freeze", doc)
