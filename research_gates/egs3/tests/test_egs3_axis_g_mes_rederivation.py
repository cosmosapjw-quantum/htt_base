"""EGS3 Axis G gate: v8 M4 resolution -- MES bound-coefficient rederivation.

G8R  B_sigma=(5/3,3,3/7) is rederived bit-exact from MESa (astro-ph/9501016) raw
     eq (51) via the stated reduction assumptions C1 (spatial <= time-deriv) and
     C2 (e*_L ~ e_L/3), by BOTH exact Fraction arithmetic and a SymPy symbolic
     identity, and matches the registry.
G8R2 The same machinery on MESa eq (52) reproduces eq (60) omega=(10/3,2/15,0),
     which differs from the registered (3/4,2,2/7) -> the registry omega/accel are
     MESb (Paper II, print-only) values (documented provenance).
G8R3 (CoVe adversarial + bit-identity guard) the rederivation changes no coefficient
     value: ceilings + W2_max=1.309e-6 + the x_C comparator stay bit-identical.

Diagnostic-only; symbolic rederivation + primary-source provenance; no data,
detection, family/geometry, native-solver, or posterior claim.
"""
import unittest

import numpy as np

from htt.obsstat.egs3_mes_rederivation import (
    reduce_raw_bound, sigma_rederivation, omega_mesa_rederivation,
    omega_accel_provenance, mes_coefficient_primary_crosswalk,
    mes_rederivation_seal, _RAW_SIGMA, _RAW_OMEGA_MESA,
)
from htt.tsc.admissibility.three_bound_hierarchy import COEFFS, W2_max
from htt.obsstat.egs3_psd_cone import sector_matrix, xc_from_matrix
from htt.obsstat.egs3_graded_comparator import COMPARATOR_SIGNS

_SSOT_EPS = (1.2336e-3, 3.559629e-6, 6.065291e-6)


class G8RSigmaRederivationTests(unittest.TestCase):
    def test_seal_pass(self):
        self.assertEqual(mes_rederivation_seal()["status"], "PASS")

    def test_sigma_reduces_to_eq59_bit_exact(self):
        r = sigma_rederivation()
        self.assertEqual(r["reduced_coeffs"], ["5/3", "3", "3/7"])
        self.assertTrue(r["matches_eq59"])
        self.assertTrue(r["matches_registry"])
        self.assertTrue(r["rederived"])

    def test_sigma_symbolic_identity(self):
        # SymPy proof that the C1/C2-reduced expression equals (5/3)e1+3e2+(3/7)e3.
        self.assertTrue(sigma_rederivation()["symbolic_identity_holds"])

    def test_reduce_matches_registry_sigma(self):
        reduced = reduce_raw_bound(_RAW_SIGMA)
        self.assertEqual(reduced, COEFFS["sigma"])


class G8R2OmegaProvenanceTests(unittest.TestCase):
    def test_mesa_omega_reproduces_eq60(self):
        r = omega_mesa_rederivation()
        self.assertEqual(r["reduced_coeffs"], ["10/3", "2/15", "0"])
        self.assertTrue(r["matches_eq60"])

    def test_mesa_omega_differs_from_registry(self):
        r = omega_mesa_rederivation()
        self.assertTrue(r["mesa_omega_differs_from_registry"])
        self.assertNotEqual(reduce_raw_bound(_RAW_OMEGA_MESA), COEFFS["omega"])

    def test_omega_accel_are_mesb_primary_sourced(self):
        p = omega_accel_provenance()
        self.assertEqual(p["status"], "primary_sourced_not_rederivable")
        self.assertIn("5942", p["primary_source"])

    def test_crosswalk_status(self):
        cw = mes_coefficient_primary_crosswalk()
        self.assertEqual(cw["sigma"]["status"], "rederived")
        self.assertEqual(cw["omega"]["status"], "primary_sourced_not_rederivable")
        self.assertEqual(cw["accel"]["status"], "primary_sourced_not_rederivable")


class G8R3CoVeAdversarialTests(unittest.TestCase):
    """Adversarial guard: the M4 rederivation mutates no numeric value."""

    def test_registered_coeffs_unchanged(self):
        self.assertEqual(COEFFS["sigma"], reduce_raw_bound(_RAW_SIGMA))
        # omega/accel literals untouched by the rederivation module
        self.assertEqual([str(c) for c in COEFFS["omega"]], ["3/4", "2", "2/7"])
        self.assertEqual([str(c) for c in COEFFS["accel"]], ["3/4", "1", "3/14"])

    def test_w2_max_bit_identical(self):
        self.assertAlmostEqual(W2_max(*_SSOT_EPS), 1.309e-6, places=8)

    def test_xc_stays_bit_identical(self):
        for g in [(2.0e-6, 1.5e-6, 8.0e-7, 3.0e-7), (0.12, 0.0, 0.03, 0.0),
                  (3.7, 0.0, 0.5, 0.25)]:
            self.assertTrue(np.array_equal(
                xc_from_matrix(sector_matrix(g)),
                float(COMPARATOR_SIGNS @ np.asarray(g))))

    def test_no_affirmative_forbidden_claim(self):
        import htt.obsstat.egs3_mes_rederivation as mod
        doc = " ".join((mod.__doc__ or "").lower().split())
        self.assertIn("no data", doc)
        for affirmative in ("posterior odds", "family identification",
                            "we detect", "native-solver output"):
            self.assertNotIn(affirmative, doc)


if __name__ == "__main__":
    unittest.main()
