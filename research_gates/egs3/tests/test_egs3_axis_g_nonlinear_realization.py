"""EGS3 Axis G gate: v8 T3-full exact (nonlinear) endpoint realization.

G-T3F  Both registered identified-interval ENDPOINTS are realized by EXACT
       homogeneous cosmologies (Bianchi I for the Omega_k=0 lower endpoint,
       Bianchi V for the Omega_k>0 upper endpoint) whose full Gauss and momentum
       CONSTRAINTS have EXACTLY-zero residuals (symbolic/rational, all orders in
       the tilt rapidity) -- endpoint attainability at exact order (NOT, by itself,
       a full nonlinear interval-sharpness theorem; the box bound + interior filling
       stay at the convex P31 level, and the King-Ellis dynamical realization is deferred).
G-T3F2 The Bianchi V (0i) momentum constraint 3 a_b sigma^{ab}+kappa q^a=0 is
       satisfied exactly by a shear transverse to the a-vector (sigma_1=0) plus
       the antipodal (zero-flux) tilt pair; the flux cancels to all orders.
G-T3F3 (CoVe adversarial + bit-identity guard) the exact realization mutates no
       x_C comparator value and makes no affirmative posterior/family/detection claim.

Diagnostic-only; exact symbolic GR realization; Bianchi I/V are the realizing
construction, not a sky class claim; no data/detection/family/native-solver claim.
"""
import unittest

import numpy as np

from htt.obsstat.egs3_nonlinear_realization import (
    antipodal_flux_exact, bianchi_V_momentum_constraint,
    realize_endpoint_exact, nonlinear_realization_seal,
)
from htt.obsstat.egs3_linearized_realization import REGISTERED_ENDPOINTS
from htt.obsstat.egs3_psd_cone import sector_matrix, xc_from_matrix
from htt.obsstat.egs3_graded_comparator import COMPARATOR_SIGNS


class GT3FExactRealizationTests(unittest.TestCase):
    def test_seal_pass(self):
        self.assertEqual(nonlinear_realization_seal()["status"], "PASS")

    def test_both_endpoints_exactly_realized(self):
        for name, tgt in REGISTERED_ENDPOINTS.items():
            ep = realize_endpoint_exact(name, tgt)
            self.assertTrue(ep["gauss_residual_exact_zero"], name)
            self.assertTrue(ep["momentum_exact_zero"], name)
            self.assertTrue(ep["realized"], name)

    def test_endpoint_bianchi_classes(self):
        lo = realize_endpoint_exact("lo", REGISTERED_ENDPOINTS["lower_xC_11_over_100"])
        hi = realize_endpoint_exact("hi", REGISTERED_ENDPOINTS["upper_xC_17_over_100"])
        self.assertEqual(lo["bianchi_class"], "I")   # Omega_k = 0
        self.assertEqual(hi["bianchi_class"], "V")   # Omega_k > 0

    def test_antipodal_flux_exact_zero(self):
        f = antipodal_flux_exact()
        self.assertEqual(f["q_net_symbolic"], "0")
        self.assertTrue(f["q_net_is_exact_zero"])
        self.assertTrue(f["tilt_additive_exact"])

    def test_bianchi_v_transverse_momentum_exact_zero(self):
        m = bianchi_V_momentum_constraint()
        self.assertTrue(m["momentum_exact_zero"])
        # transverse trace-free shear gives Sigma^2 = s_+^2/(3 H^2)
        self.assertEqual(m["Sigma2_from_transverse_shear"], "s_plus**2/(3*H**2)")


class GT3FCoVeAdversarialTests(unittest.TestCase):
    def test_xc_unchanged(self):
        for g in [(0.12, 0.04, 0.03, 0.0), (0.12, 0.0, 0.03, 0.02)]:
            self.assertTrue(np.array_equal(
                xc_from_matrix(sector_matrix(g)),
                float(COMPARATOR_SIGNS @ np.asarray(g))))

    def test_registered_endpoint_xc_values(self):
        lo = realize_endpoint_exact("lo", REGISTERED_ENDPOINTS["lower_xC_11_over_100"])
        hi = realize_endpoint_exact("hi", REGISTERED_ENDPOINTS["upper_xC_17_over_100"])
        self.assertEqual(lo["x_C"], "11/100")
        self.assertEqual(hi["x_C"], "17/100")

    def test_no_affirmative_forbidden_claim(self):
        import htt.obsstat.egs3_nonlinear_realization as mod
        doc = " ".join((mod.__doc__ or "").lower().split())
        self.assertIn("no data", doc)
        for affirmative in ("posterior odds", "we detect", "native-solver output"):
            self.assertNotIn(affirmative, doc)


if __name__ == "__main__":
    unittest.main()
