"""EGS2 gates: NT2-B2 sourced depth transport, NT2-B3 vorticity blind sector."""
import unittest

from htt.obsstat.egs2_transport import (
    sourced_depth_transport, vorticity_blind_sector, radial_vorticity_projection,
    cmb_temperature_vorticity_sensitivity,
)


class SourcedTransportTests(unittest.TestCase):
    def test_steady_pi_flat_growing_pi_sourced(self):
        r = sourced_depth_transport()
        self.assertLess(r.steady_gap_spread, 1e-6)      # steady tilt stress -> flat G_F
        self.assertGreater(r.growing_gap_spread, 1.0)   # growing Pi(z) -> depth-evolving G_F
        self.assertTrue(r.sourced)


class BlindSectorTests(unittest.TestCase):
    def test_cmb_channel_blind_to_vorticity(self):
        for W2 in (1e-6, 1e-3, 1.0, 1e3):
            self.assertEqual(cmb_temperature_vorticity_sensitivity(W2), 0.0)

    def test_radial_projection_identically_zero(self):
        # n^a Omega_ab n^b = 0 for any antisymmetric Omega.
        self.assertAlmostEqual(radial_vorticity_projection([0.3, -0.2, 0.5], [0.0, 0.0, 1.0]), 0.0, places=15)

    def test_joint_blind_sector(self):
        b = vorticity_blind_sector(n_configs=1000, seed=33)
        self.assertEqual(b.cmb_max_sensitivity, 0.0)
        self.assertLess(b.radial_max_projection, 1e-12)
        self.assertTrue(b.joint_blind)


if __name__ == "__main__":
    unittest.main()
