"""EGS3 Axis B gates: B1 semi-native transfer, B2 Volterra memory, B3 vorticity re-opening."""
import unittest

from bass.transfer.shear_quadrupole_seminative import (
    shear_multipole_response, fisher_floor_from_transfer, floor_profile_vs_k,
)
from htt.obsstat.egs3_volterra_memory import volterra_memory_check
from htt.obsstat.egs3_vorticity_channels import (
    vorticity_reopening, radial_response, transverse_response,
)


class B1TransferTests(unittest.TestCase):
    def test_superhorizon_response_normalised_bounded_and_decaying(self):
        # super-horizon shear (k*chi_star << 1): quadrupole-dominated, decaying
        resp = shear_multipole_response(k=7.0e-5, lmax=20)   # k*chi_star ~ 1
        self.assertAlmostEqual(resp.r_ell[2], 1.0, places=12)   # r_2 normalised
        self.assertTrue(resp.bounded)                           # bounded operator
        self.assertTrue(resp.monotone_decay_from_l2)            # r_2 is the max
        for ell in resp.ell:
            self.assertGreaterEqual(resp.r_ell[ell], 0.0)

    def test_floor_is_a_k_profile_saturating_at_0632(self):
        # the genuine floor saturates at the single-l 0.632 in the homogeneous
        # (k->0) shear limit and drops below it at finite k (multi-l band).
        prof = floor_profile_vs_k([1e-5, 7e-5, 5e-4, 2e-3], lmax=40)
        floors = {v["k_chi_star"]: v["floor"] for v in prof.values()}
        kchi = sorted(floors)
        # smallest k*chi_star -> ~0.632 (quadrupole-dominated)
        self.assertAlmostEqual(floors[kchi[0]], (2 / 5) ** 0.5, places=2)
        # larger k*chi_star -> floor strictly below 0.632 (multi-l band)
        self.assertLess(floors[kchi[-1]], 0.6324555)


class B2VolterraTests(unittest.TestCase):
    def test_volterra_equals_ode_and_gronwall_holds(self):
        r = volterra_memory_check()
        self.assertLess(r.max_abs_diff_vs_ode, 1e-3)   # integral form == ODE
        self.assertTrue(r.gronwall_holds)
        self.assertTrue(r.kernel_decays)


class B3VorticityReopenTests(unittest.TestCase):
    def test_radial_blind_transverse_reopens(self):
        r = vorticity_reopening(n_configs=500, seed=91)
        self.assertLess(r.radial_max_abs, 1e-12)        # radial no-go
        self.assertGreater(r.transverse_max_abs, 1e-3)  # transverse re-opens
        self.assertEqual(r.transverse_design_rank, 3)   # all 3 curl modes reachable
        self.assertTrue(r.reopens)

    def test_radial_identity_zero(self):
        self.assertAlmostEqual(radial_response([0.3, -0.2, 0.5], [0, 0, 1]), 0.0, places=15)
        self.assertNotAlmostEqual(transverse_response([0, 0, 1], [1, 0, 0], [0, 1, 0]), 0.0, places=6)


if __name__ == "__main__":
    unittest.main()
