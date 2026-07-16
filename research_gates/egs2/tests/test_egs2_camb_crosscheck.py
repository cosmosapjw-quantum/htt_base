"""EGS2 B1 closure gates: semi-native shear transfer vs the REAL CAMB visibility.

CC1 the real CAMB recombination visibility is recovered on the last-scattering
    window (normalised, single-peaked, chi_star ~ 1.38e4 Mpc, MUCH narrower
    than the registered Gaussian stand-in);
CC2 the three load-bearing frozen-lane conclusions hold with the REAL
    visibility: super-horizon floor saturation at sqrt(2/5), strict finite-k
    improvement, band peak tracking l ~ k*chi_star;
CC3 seminative_camb_crosscheck_seal() PASS (or a REGISTERED blocker when camb
    is absent -- never silence), deterministic, records camb version + pinned
    background;
CC-CoVe x_C bit-identity three-route anchor + forbidden-claim-string guard.

Diagnostic-only, single-mode, exact-FLRW-anchored; the frozen Gaussian module
is imported read-only. AWAITING_NATIVE_LOWELL_SOLVER stays partially
discharged.
"""
import unittest

import numpy as np

try:
    import camb  # noqa: F401
    _HAVE_CAMB = True
except Exception:
    _HAVE_CAMB = False

from bass.transfer import visibility_camb_crosscheck as vcc
from bass.transfer.visibility_camb_crosscheck import (
    seminative_camb_crosscheck_seal, SINGLE_L_FLOOR,
)
from htt.obsstat.egs3_graded_comparator import COMPARATOR_SIGNS
from htt.obsstat.egs3_psd_cone import sector_matrix, xc_from_matrix


@unittest.skipUnless(_HAVE_CAMB, "camb not installed in this environment")
class CC1VisibilityRecovery(unittest.TestCase):
    def test_visibility_is_normalised_and_single_peaked(self):
        vis = vcc.camb_visibility_window()
        trap = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
        self.assertAlmostEqual(float(trap(vis["g"], vis["chi"])), 1.0, places=9)
        g = vis["g"]
        i = int(np.argmax(g))
        self.assertTrue(0 < i < g.size - 1)

    def test_camb_chi_star_and_width_vs_registered_standin(self):
        vis = vcc.camb_visibility_window()
        self.assertGreater(vis["chi_star"], 1.3e4)
        self.assertLess(vis["chi_star"], 1.45e4)
        # the real visibility is much narrower than the 250 Mpc stand-in
        self.assertLess(vis["sigma_fwhm_equiv"], 50.0)


@unittest.skipUnless(_HAVE_CAMB, "camb not installed in this environment")
class CC2FrozenLaneConclusionsHold(unittest.TestCase):
    def test_all_crosscheck_booleans(self):
        cc = vcc.visibility_crosscheck()
        for name, ok in cc["checks"].items():
            self.assertTrue(ok, name)

    def test_superhorizon_floor_value(self):
        cc = vcc.visibility_crosscheck()
        row = cc["rows"][0]
        self.assertLess(row["k_chi_star"], 0.05)
        self.assertAlmostEqual(row["floor_camb"], SINGLE_L_FLOOR, places=4)

    def test_finite_k_floor_strictly_below(self):
        cc = vcc.visibility_crosscheck()
        row = cc["rows"][-1]
        self.assertLess(row["floor_camb"], 0.2)


class CC3SealTests(unittest.TestCase):
    def test_seal_status_is_pass_or_registered_blocker(self):
        seal = seminative_camb_crosscheck_seal()
        self.assertIn(seal["status"], ("PASS", "BLOCKED_CAMB_UNAVAILABLE"))
        if _HAVE_CAMB:
            self.assertEqual(seal["status"], "PASS")

    @unittest.skipUnless(_HAVE_CAMB, "camb not installed in this environment")
    def test_seal_is_deterministic_and_records_provenance(self):
        seal = seminative_camb_crosscheck_seal()
        self.assertEqual(seal, seminative_camb_crosscheck_seal())
        self.assertEqual(seal["seal"], "egs2.seminative_camb_crosscheck")
        self.assertIn("camb_version", seal["crosscheck"])
        self.assertIn("residual_blocker", seal)
        self.assertIn("claim_boundary", seal)


class CCCoVeAdversarialGuard(unittest.TestCase):
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

    def test_module_docstring_has_no_forbidden_claim_string(self):
        doc = (vcc.__doc__ or "").lower()
        for token in self.FORBIDDEN_STRINGS:
            self.assertNotIn(token, doc,
                             f"forbidden claim string {token!r} in docstring")

    def test_module_docstring_keeps_the_residual_blocker(self):
        doc = vcc.__doc__ or ""
        self.assertIn("AWAITING_NATIVE_LOWELL_SOLVER", doc)
        self.assertIn("partially discharged", doc)


if __name__ == "__main__":
    unittest.main()
