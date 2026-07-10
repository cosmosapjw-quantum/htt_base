"""EGS3 Axis B gates (v8 successor): Volterra depth-memory with real H(z).

B-HZ-1 kernel universality: exp(-3 int H dt) == (a(s)/a(t))^3 symbolically for
        generic positive a(t) (the real-H(z) closure is an exact change of
        clock, not an approximation);
B-HZ-2 Einstein-de Sitter symbolic limit K = (s/t)^2;
B-HZ-3 LambdaCDM numeric: e-fold Volterra solution matches an independent RK4
        integration; e-fold Gronwall envelope holds; kernel decays;
B-HZ-4 volterra_hz_seal() PASS, deterministic, records the closed ledger caveat;
B-HZ-CoVe x_C bit-identity three-route anchor + forbidden-claim-string guard.

Diagnostic-only; the frozen constant-H v7 module is not modified.
"""
import unittest

import numpy as np

from htt.obsstat import egs3_volterra_hz as vh
from htt.obsstat.egs3_volterra_hz import (
    kernel_universality_symbolic, eds_kernel_limit_symbolic,
    volterra_hz_check, volterra_hz_seal, hubble_lcdm,
)
from htt.obsstat.egs3_graded_comparator import COMPARATOR_SIGNS
from htt.obsstat.egs3_psd_cone import sector_matrix, xc_from_matrix


class BHZ1KernelUniversality(unittest.TestCase):
    def test_kernel_is_a_cubed_dilution_for_generic_expansion(self):
        sym = kernel_universality_symbolic()
        self.assertTrue(sym["identity_holds"])
        self.assertEqual(sym["kernel"], sym["target"])


class BHZ2EdSLimit(unittest.TestCase):
    def test_eds_kernel_is_s_over_t_squared(self):
        eds = eds_kernel_limit_symbolic()
        self.assertTrue(eds["equals_s_over_t_squared"])
        self.assertEqual(eds["H"], "2/(3*t)")


class BHZ3LcdmNumeric(unittest.TestCase):
    def test_volterra_matches_rk4(self):
        chk = volterra_hz_check()
        self.assertLess(chk.max_abs_diff_vs_rk4, 5e-6)

    def test_gronwall_and_kernel_decay(self):
        chk = volterra_hz_check()
        self.assertTrue(chk.gronwall_holds)
        self.assertTrue(chk.kernel_decays)

    def test_hubble_is_monotone_decreasing_toward_today(self):
        x = np.linspace(-1.0, 0.0, 50)
        H = hubble_lcdm(x)
        self.assertTrue(np.all(np.diff(H) < 0.0))
        self.assertAlmostEqual(float(H[-1]), 1.0, places=12)


class BHZ4SealTests(unittest.TestCase):
    def test_seal_passes_and_is_deterministic(self):
        seal = volterra_hz_seal()
        self.assertEqual(seal["status"], "PASS")
        self.assertEqual(seal, volterra_hz_seal())

    def test_seal_records_closed_caveat_and_provenance(self):
        seal = volterra_hz_seal()
        self.assertEqual(seal["seal"], "egs3.volterra_hz")
        self.assertIn("constant-H stand-in", seal["closes_caveat"])
        self.assertIn("egs3_volterra_memory.py", seal["successor_of"])
        self.assertIn("claim_boundary", seal)


class BHZCoVeAdversarialGuard(unittest.TestCase):
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

    def test_seal_does_not_mutate_the_comparator(self):
        before = COMPARATOR_SIGNS.copy()
        volterra_hz_seal()
        self.assertTrue(np.array_equal(COMPARATOR_SIGNS, before))

    def test_module_docstring_has_no_forbidden_claim_string(self):
        doc = (vh.__doc__ or "").lower()
        for token in self.FORBIDDEN_STRINGS:
            self.assertNotIn(token, doc,
                             f"forbidden claim string {token!r} in docstring")

    def test_module_docstring_states_successor_scope(self):
        doc = (vh.__doc__ or "").lower()
        self.assertIn("byte-frozen", doc)
        self.assertIn("e-fold", doc)


if __name__ == "__main__":
    unittest.main()
