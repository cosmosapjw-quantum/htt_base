"""PR07-001 gate: unit-safe anisotropic-stress ownership (real bass modules)."""
import unittest
import numpy as np

from bass.background.bi_continuation import SpeciesPrimitive, tilt_moments
from bass.background.bi_continuation.moments import (
    normalize_anisotropic_stress,
    physical_anisotropic_stress,
)
from bass.background.bi_continuation.dynamics import (
    shear_rhs_from_physical,
    shear_rhs_from_normalized,
)


class UnitConventionTests(unittest.TestCase):
    def test_physical_normalized_roundtrip(self):
        pi = np.array([[0.2, 0.03, 0.0], [0.03, -0.12, 0.01], [0.0, 0.01, -0.08]])
        H = 0.73
        kappa = 1.7
        Pi = normalize_anisotropic_stress(pi, H, kappa)
        self.assertTrue(np.allclose(physical_anisotropic_stress(Pi, H, kappa), pi, rtol=3e-13, atol=3e-13))

    def test_shear_rhs_conventions_agree(self):
        sigma = np.diag([0.04, -0.01, -0.03])
        pi = np.array([[0.1, 0.02, 0.0], [0.02, -0.06, 0.01], [0.0, 0.01, -0.04]])
        H = 0.81
        kappa = 2.3
        Pi = normalize_anisotropic_stress(pi, H, kappa)
        a = shear_rhs_from_physical(H, sigma, pi, kappa)
        b = shear_rhs_from_normalized(H, sigma, Pi)
        self.assertLess(np.max(np.abs(a - b)), 3e-13)

    def test_shear_rhs_derivatives(self):
        sigma = np.diag([0.04, -0.01, -0.03])
        pi = np.array([[0.1, 0.02, 0.0], [0.02, -0.06, 0.01], [0.0, 0.01, -0.04]])
        H = 0.81
        kappa = 2.3
        Pi = normalize_anisotropic_stress(pi, H, kappa)
        eps = 1e-6
        dpi = np.zeros((3, 3)); dpi[0, 1] = dpi[1, 0] = eps
        dp = (shear_rhs_from_physical(H, sigma, pi + dpi, kappa)
              - shear_rhs_from_physical(H, sigma, pi - dpi, kappa)) / (2 * eps)
        dPi = np.zeros((3, 3)); dPi[0, 1] = dPi[1, 0] = eps
        dn = (shear_rhs_from_normalized(H, sigma, Pi + dPi)
              - shear_rhs_from_normalized(H, sigma, Pi - dPi)) / (2 * eps)
        self.assertAlmostEqual(dp[0, 1], kappa, places=6)       # d sigma_dot / d pi = kappa
        self.assertAlmostEqual(dn[0, 1], 3 * H * H, places=6)   # d sigma_dot / d Pi = 3 H^2

    def test_invalid_inputs_rejected(self):
        pi = np.eye(3) * 0.0
        with self.assertRaises(ValueError):
            normalize_anisotropic_stress(pi, -1.0, 1.0)
        with self.assertRaises(ValueError):
            normalize_anisotropic_stress(pi, 1.0, -1.0)

    def test_tilt_moment_pi_relation(self):
        species = (
            SpeciesPrimitive(0.6, 0.0, np.array([0.22, 0.0, 0.0])),
            SpeciesPrimitive(0.6, 0.0, np.array([-0.22, 0.0, 0.0])),
        )
        H = 0.9
        kappa = 1.4
        m = tilt_moments(species, H, kappa)
        self.assertTrue(np.allclose(m.Pi_normalized, normalize_anisotropic_stress(m.pi_physical, H, kappa), atol=2e-14))
        self.assertTrue(np.allclose(m.Pi, m.Pi_normalized))  # legacy alias preserved


if __name__ == '__main__':
    unittest.main()
