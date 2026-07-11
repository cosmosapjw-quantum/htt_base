"""EGS3 Axis G gates (REV-R184/R185): OMK-REOPEN.

G-OMK-1  exact expansion-normalized reduction of the LRS-III/KS class
         (Gauss 1 = Omega + Sigma^2 + K; q closed form; curvature source
         coefficient in dSigma/dN exactly -1; dK = 2K(q+Sigma));
G-OMK-2  slaving theorem: kappa = -2/(5+3w) = -1/(2+q0) exact; transient
         rate (3/2)(1-w); vacuum anchor (-1/2, 3/4) with dust eigenvalues
         (-3/2, 0) (center direction honestly separated -- the numerical
         deep run carries the attraction statement);
G-OMK-3  structural-null repair: the certified instantaneous Omega_k null
         is UNTOUCHED (re-asserted from measured_response_card); the
         dynamical linear response is nonzero;
G-OMK-4  metric-level dynamics (Gauss MONITORED < 1e-7, non-vacuum):
         Sigma/K plateaus at kappa within 1% for LRS-III dust/radiation
         and the KS mirror; reduced lane cross-checks the metric level to
         < 1e-5 and reaches the vacuum anchor at deep N;
G-OMK-5  ceiling map: 6 labeled attribution x era rows, two-sided,
         frozen U_k plugin untouched, observational_claim_allowed False;
G-OMK-6  seal PASS + the NEW card artifact is consistent with the seal;
G-OMK-CoVe  x_C bit-identity + forbidden-string guard.
"""
import json
from pathlib import Path
import unittest

import numpy as np

from htt.obsstat.egs3_graded_comparator import COMPARATOR_SIGNS
from htt.obsstat.egs3_omega_k_reopening import (
    ceiling_map,
    omega_k_reopening_seal,
    reduced_system,
    slaving_coefficient,
    structural_null_repair,
)
from htt.obsstat.egs3_psd_cone import sector_matrix, xc_from_matrix

REPO = Path(__file__).resolve().parents[3]
_SEAL = omega_k_reopening_seal()   # heavy derivation cached once


class GOMK1Reduction(unittest.TestCase):
    def test_exact_reduction(self):
        rs = reduced_system()
        self.assertTrue(all(rs["checks"].values()),
                        [k for k, v in rs["checks"].items() if not v])


class GOMK2Slaving(unittest.TestCase):
    def test_kappa_and_anchor(self):
        sl = slaving_coefficient()
        self.assertTrue(all(sl["checks"].values()),
                        [k for k, v in sl["checks"].items() if not v])
        self.assertEqual(sl["kappa_dust"], "-2/5")
        self.assertEqual(sl["kappa_radiation"], "-1/3")
        self.assertEqual(sl["kappa_of_q"], "-1/(2 + q)")


class GOMK3NullRepair(unittest.TestCase):
    def test_instantaneous_null_untouched_dynamical_nonzero(self):
        r = structural_null_repair()
        self.assertTrue(r["instantaneous_null_still_certified"])
        self.assertTrue(r["dynamical_linear_response_nonzero"])
        self.assertIn("slaved submanifold", r["statement"])


class GOMK4Dynamics(unittest.TestCase):
    def test_plateaus_and_deep_run(self):
        dyn = _SEAL["dynamical_verification"]
        for key in ("lrs3_dust", "lrs3_radiation", "ks_dust"):
            row = dyn[key]
            self.assertTrue(row["slaving_verified"], key)
            self.assertTrue(row["gauss_monitored_ok"], key)
            self.assertTrue(row["nonvacuum_throughout"], key)
            self.assertLess(row["max_rel_dev_in_window"], 0.01)
        red = dyn["reduced_lane"]
        self.assertTrue(red["cross_check_ok"])
        self.assertTrue(red["late_time_vacuum_anchor"]["approaches_anchor"])


class GOMK5CeilingMap(unittest.TestCase):
    def test_rows_and_discipline(self):
        ceil = ceiling_map()
        self.assertEqual(len(ceil["rows"]), 6)
        self.assertFalse(ceil["observational_claim_allowed"])
        self.assertTrue(ceil["frozen_plugin_untouched"])
        for key, row in ceil["rows"].items():
            self.assertGreater(row["omega_k_ceiling_abs"], 0.0, key)
            self.assertLess(row["omega_k_ceiling_abs"], 1.0, key)
        # conservative ordering: radiation-era row is the largest per branch
        for b in ("mes_registered", "mes_cosmological",
                  "saadeh_model_conditional"):
            self.assertGreater(
                ceil["rows"][f"{b}__radiation_era"]["omega_k_ceiling_abs"],
                ceil["rows"][f"{b}__matter_era"]["omega_k_ceiling_abs"])


class GOMK6SealAndCard(unittest.TestCase):
    def test_seal_pass_and_scope(self):
        self.assertEqual(_SEAL["status"], "PASS")
        self.assertEqual(_SEAL["theorem_id"], "OMK-REOPEN")
        self.assertIn("branch 1", _SEAL["exit_gate"])
        self.assertIn("class-conditional", _SEAL["scope_not_claimed"])

    def test_card_consistent_with_seal(self):
        path = REPO / "docs/generated/k5_omega_k_ceiling_card.json"
        self.assertTrue(path.exists(), "run scripts/k5_omega_k_ceiling_card.py")
        card = json.loads(path.read_text())
        self.assertFalse(card["observational_claim_allowed"])
        self.assertEqual(card["ceiling_rows"],
                         _SEAL["ceiling_map"]["rows"])
        self.assertIn("NOT modified", card["frozen_surfaces_untouched"][
            "registered_T1p_half_width_U_k"])


class GOMKCoVeAdversarialGuard(unittest.TestCase):
    FORBIDDEN_STRINGS = ("posterior", "detection", "native solver",
                         "family assignment")

    def test_x_c_anchor_bit_identical(self):
        g = np.array([0.12, 0.0, 0.03, 0.0])
        via_graded = float(COMPARATOR_SIGNS @ g)
        via_trace = xc_from_matrix(sector_matrix(g))
        self.assertTrue(np.array_equal(via_graded, 0.15))
        self.assertTrue(np.array_equal(via_trace, via_graded))

    def test_module_docstring_guard(self):
        import htt.obsstat.egs3_omega_k_reopening as mod
        doc = (mod.__doc__ or "").lower()
        for token in self.FORBIDDEN_STRINGS:
            self.assertNotIn(token, doc)
        self.assertIn("class-conditional", doc)
