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
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import numpy as np

try:
    import camb  # noqa: F401
    _HAVE_CAMB = True
except Exception:
    _HAVE_CAMB = False

from scripts.oracles import egs2_camb_visibility as vcc
from scripts.oracles.egs2_camb_visibility import (
    seminative_camb_crosscheck_seal, SINGLE_L_FLOOR,
)
from scripts import run_egs2_camb_crosscheck_seal as seal_runner
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

    def test_missing_camb_is_the_only_unavailable_blocker(self):
        missing = ModuleNotFoundError("No module named 'camb'", name="camb")
        with mock.patch.object(vcc, "visibility_crosscheck", side_effect=missing):
            seal = seminative_camb_crosscheck_seal()
        self.assertEqual(seal["status"], "BLOCKED_CAMB_UNAVAILABLE")
        self.assertIn("ModuleNotFoundError", seal["error"])

    def test_missing_camb_submodule_is_a_failed_oracle_not_unavailable_camb(self):
        missing = ModuleNotFoundError(
            "No module named 'camb.model'", name="camb.model"
        )
        with mock.patch.object(vcc, "visibility_crosscheck", side_effect=missing):
            seal = seminative_camb_crosscheck_seal()
        self.assertEqual(seal["status"], "FAIL")
        self.assertIn("camb.model", seal["error"])

    def test_numerical_failure_is_not_laundered_as_camb_unavailable(self):
        with mock.patch.object(
            vcc,
            "visibility_crosscheck",
            side_effect=FloatingPointError("non-finite visibility"),
        ):
            seal = seminative_camb_crosscheck_seal()
        self.assertEqual(seal["status"], "FAIL")
        self.assertIn("FloatingPointError", seal["error"])

    def test_runner_keeps_blocked_and_failed_lifecycles_distinct(self):
        cases = (("BLOCKED_CAMB_UNAVAILABLE", 2), ("FAIL", 1))
        for status, expected_code in cases:
            with self.subTest(status=status), tempfile.TemporaryDirectory() as td:
                output = Path(td) / "seal.json"
                with mock.patch.object(seal_runner, "OUT", output), mock.patch.object(
                    vcc, "seminative_camb_crosscheck_seal", return_value={"status": status}
                ):
                    self.assertEqual(seal_runner.main([]), expected_code)
                self.assertFalse(output.exists())

    def test_runner_executes_without_ambient_pythonpath(self):
        repo = Path(__file__).resolve().parents[3]
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        proc = subprocess.run(
            [sys.executable, "scripts/run_egs2_camb_crosscheck_seal.py", "--check"],
            cwd=repo,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertIn(proc.returncode, (0, 2), proc.stdout + proc.stderr)
        if proc.returncode == 2:
            self.assertIn("REGISTERED BLOCKER: camb unavailable", proc.stderr)
        else:
            self.assertIn("camb cross-check seal current", proc.stdout)

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
