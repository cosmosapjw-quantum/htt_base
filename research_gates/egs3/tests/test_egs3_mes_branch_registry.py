"""EGS3 gates: MES-BR branch registry + K5 v9 three-ceiling card (v9,
REV-R173).

BR-1 branch table: MES_G verified geodesic (sigma rederived; omega SAG eq 4;
     accel absent), MES_NG unverified (registered omega/accel), accel
     WITHHELD; registered values unchanged;
BR-2 eps1 attribution triple: observer_boost == conservative_total ==
     771/625000, numerically the solar kinematic dipole; cosmological == 0
     (SAG convention);
BR-3 W^2 ceilings: registered bit-identical to the frozen W2_max anchor;
     hybrid matches the mes_rederivation comparison value; SAG-consistent
     collapses ~12 orders; ordering sag < registered < hybrid; eps1
     dominance shares ~99% disclosed;
BR-4 seal PASS + deterministic;
BR-5 K5 v9 card artifact: 3 W^2 branches x 2 curvature branches, lower
     endpoint keyed to -U_W on the open branch, firewall intact, frozen
     v7/v8 cards referenced by SHA;
BR-CoVe x_C bit-identity three-route anchor + forbidden-claim-string guard.

Frozen modules imported read-only; no registered value is modified.
"""
import json
import unittest
from pathlib import Path

import numpy as np

from htt.obsstat.egs3_mes_branch_registry import (
    EPS1_TRIPLE,
    GEODESIC_OMEGA_TRIPLE,
    branch_table,
    eps1_attribution_triple,
    mes_branch_registry_seal,
    w2_ceiling_branches,
)
from htt.obsstat.egs3_mes_provenance import eps_registry_provenance
from htt.obsstat.egs3_graded_comparator import COMPARATOR_SIGNS
from htt.obsstat.egs3_psd_cone import sector_matrix, xc_from_matrix

REPO = Path(__file__).resolve().parents[3]
V9_CARD = REPO / "docs/generated/k5_cf4_identified_interval_card_v9.json"


class BR1BranchTable(unittest.TestCase):
    def test_branches_and_statuses(self):
        t = branch_table()
        self.assertEqual(t["MES_G"]["status"], "VERIFIED_GEODESIC")
        self.assertEqual(t["MES_NG"]["status"], "UNVERIFIED_NON_GEODESIC")
        self.assertEqual(t["ACCEL_WITHHELD"]["status"], "WITHHELD")
        self.assertIsNone(t["MES_G"]["accel"]["triple"])
        self.assertEqual(t["MES_G"]["omega"]["triple"], ("10/3", "2/15", "0"))
        self.assertEqual(t["MES_NG"]["omega"]["triple"], ("3/4", "2", "2/7"))
        self.assertTrue(t["registered_values_unchanged"])


class BR2Eps1Triple(unittest.TestCase):
    def test_attribution_triple(self):
        self.assertEqual(EPS1_TRIPLE["eps1_observer_boost"],
                         EPS1_TRIPLE["eps1_conservative_total"])
        self.assertEqual(EPS1_TRIPLE["eps1_cosmological"], 0)
        eps = eps1_attribution_triple()
        self.assertTrue(eps["numeric_coincidence_confirmed"])
        self.assertLess(eps["relative_difference_to_solar_beta"], 2e-4)
        self.assertEqual(eps["consumed_by_frozen_evaluators"],
                         "eps1_conservative_total")


class BR3Ceilings(unittest.TestCase):
    def test_three_ceilings_and_anchor(self):
        from htt.tsc.admissibility.three_bound_hierarchy import W2_max
        c = w2_ceiling_branches()
        prov = eps_registry_provenance()
        vals = prov["ssot_registry"]["values"]
        frozen_fn = W2_max(vals["eps1"], vals["eps2"], vals["eps3"])
        self.assertTrue(c["registered"]["bit_identical_to_frozen_W2_max"])
        # the authoritative anchor is the W2_max FUNCTION at the ssot eps
        self.assertTrue(np.array_equal(c["registered"]["value_float"],
                                       frozen_fn))
        # the provenance dict stores a separately-computed float one ULP
        # away (float vs exact evaluation path); documented, not hidden
        prov_val = prov["registered_ceilings_from_ssot"]["W2_max"]
        self.assertLessEqual(abs(prov_val - frozen_fn),
                             np.finfo(float).eps * frozen_fn)
        self.assertTrue(
            c["hybrid_literature"]["matches_mes_rederivation_report"])
        self.assertTrue(c["ordering"]["sag_lt_registered_lt_hybrid"])
        self.assertGreater(c["registered"]["eps1_term_share_of_B_omega"], 0.98)
        self.assertGreater(
            c["hybrid_literature"]["eps1_term_share_of_B_omega"], 0.99)
        self.assertLess(c["sag_consistent"]["value_float"], 1e-12)
        self.assertFalse(c.get("no_branch_promoted") is False)


class BR4Seal(unittest.TestCase):
    def test_seal_pass_and_deterministic(self):
        seal = mes_branch_registry_seal()
        self.assertEqual(seal["status"], "PASS")
        self.assertEqual(seal["theorem_id"], "MES-BR")
        self.assertEqual(seal, mes_branch_registry_seal())


class BR5CardV9(unittest.TestCase):
    def test_card_structure_and_firewall(self):
        card = json.loads(V9_CARD.read_text())
        self.assertEqual(card["schema"],
                         "htt.k5.cf4_identified_interval_card.v2")
        self.assertFalse(card["observational_claim_allowed"])
        branches = card["w2_ceiling_branches"]
        self.assertEqual(set(branches), {"W2_registered",
                                         "W2_hybrid_literature",
                                         "W2_sag_consistent"})
        for wrow in branches.values():
            self.assertEqual(set(wrow["curvature_branches"]),
                             {"open_branch[0,Uk]", "all_branch[-Uk,Uk]"})
        # null lower extreme keyed to -U_W on the open branch (c_W = -1;
        # the curvature open branch contributes 0 to the lower null extreme)
        for wrow in branches.values():
            null_lo = wrow["curvature_branches"]["open_branch[0,Uk]"][
                "null_extremes"][0]
            self.assertTrue(np.array_equal(null_lo, -wrow["w2_upper"]))
        reg = branches["W2_registered"]
        from htt.tsc.admissibility.three_bound_hierarchy import W2_max
        vals = eps_registry_provenance()["ssot_registry"]["values"]
        self.assertTrue(np.array_equal(
            reg["w2_upper"], W2_max(vals["eps1"], vals["eps2"], vals["eps3"])))
        self.assertIn("sha256", card["based_on_frozen_cards"]["v7"])
        self.assertIn("sha256", card["based_on_frozen_cards"]["v8"])

    def test_branch_spread_is_monotone_in_ceiling(self):
        card = json.loads(V9_CARD.read_text())
        branches = card["w2_ceiling_branches"]
        lows = {k: branches[k]["curvature_branches"]
                ["open_branch[0,Uk]"]["interval"][0] for k in branches}
        self.assertGreater(lows["W2_sag_consistent"], lows["W2_registered"])
        self.assertGreater(lows["W2_registered"],
                           lows["W2_hybrid_literature"])


class BRCoVeAdversarialGuard(unittest.TestCase):
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
        import htt.obsstat.egs3_mes_branch_registry as mod
        doc = (mod.__doc__ or "").lower()
        for token in self.FORBIDDEN_STRINGS:
            self.assertNotIn(token, doc)

    def test_frozen_coeffs_not_mutated(self):
        from htt.tsc.admissibility.three_bound_hierarchy import COEFFS
        before = {k: tuple(v) for k, v in COEFFS.items()}
        mes_branch_registry_seal()
        after = {k: tuple(v) for k, v in COEFFS.items()}
        self.assertEqual(before, after)
        self.assertEqual(GEODESIC_OMEGA_TRIPLE[2], 0)
