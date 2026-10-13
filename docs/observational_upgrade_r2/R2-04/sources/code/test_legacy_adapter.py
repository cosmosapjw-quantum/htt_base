"""Meaningful contract/semantic regression checks; no observational fit."""
import hashlib
from pathlib import Path
import sys
import unittest
import numpy as np
from legacy_adapter import AnalysisContract, LegacyAdapter, multipole_rms

ROOT = Path(__file__).resolve().parents[1] / "sources" / "HTT" / "HTT"


class TestLegacyAdapter(unittest.TestCase):
    def setUp(self):
        self.contract = AnalysisContract("synthetic-contract", "specified-flow", "fixed-flat",
                                         "conditional-proof-scope", "synthetic-discrete-posterior")
        self.adapter = LegacyAdapter(ROOT, self.contract)

    def test_spectral_convention_and_units(self):
        ell = np.array([1, 2, 3])
        cl = np.array([1.0, 2.0, 4.0])
        dl = ell * (ell + 1) * cl / (2 * np.pi)
        a = multipole_rms(cl, ell, power_kind="C_ell", power_unit="K2", T0_K=2.0)
        b = multipole_rms(dl * 1e12, ell, power_kind="D_ell", power_unit="uK2", T0_K=2.0)
        np.testing.assert_allclose(a, b, rtol=3e-16)
        np.testing.assert_allclose(a, np.sqrt((2*ell+1)*cl/(4*np.pi))/2)
        with self.assertRaises(ValueError):
            multipole_rms(1, 2, power_kind="unknown", power_unit="K2", T0_K=2)
        with self.assertRaises(ValueError):
            multipole_rms(1, 2.5, power_kind="C_ell", power_unit="K2", T0_K=2)

    def test_actual_legacy_bounds_explicit_no_defaults(self):
        a = self.adapter.bounds_from_epsilon(0.01, 0.02, 0.03, frame_correction=False)
        b = self.adapter.bounds_from_epsilon(0.01, 0.02, 0.03, frame_correction=True)
        self.assertAlmostEqual(a["B_sigma"], 5/3*0.01 + 3*0.02 + 3/7*0.03)
        self.assertAlmostEqual(b["B_sigma"] / a["B_sigma"], 1 + 2.69*0.01)
        self.assertAlmostEqual(a["Sigma2_shear_ceiling"], 1.5*a["B_sigma"]**2)
        self.assertNotIn("x_ceiling", a)

    def test_signed_x_boundary_and_missing_mass(self):
        kwargs = dict(Sigma2=[0.1,0.2,np.nan], W2=[0.5,0,0], Omega_tilt=0,
                      curvature_delta=0, weights=[2,3,5], x_ceiling=1,
                      identifiable=True, q_thresholds=[0,0.2])
        a = self.adapter.departure_pushforward(**kwargs)
        self.assertLess(a["x"][0], 0)
        self.assertTrue(np.isnan(a["x"][2]))
        self.assertEqual(a["Q_unknown_mass"], 0.5)
        self.assertEqual(a["Pi_intervals"][0]["lower"], 0.3)
        self.assertEqual(a["Pi_intervals"][0]["upper"], 0.8)
        self.assertEqual(a["Pi_intervals"][1]["lower"], 0)
        self.assertEqual(a["Pi_intervals"][1]["known_boundary_mass"], 0.3)
        kwargs["weights"] = np.array([2,3,5])*1e100
        b = self.adapter.departure_pushforward(**kwargs)
        for left, right in zip(a["Pi_intervals"], b["Pi_intervals"]):
            for field in ("lower", "upper", "known_boundary_mass"):
                self.assertAlmostEqual(left[field], right[field])

    def test_zero_ceiling_and_physical_support_flag(self):
        a = self.adapter.departure_pushforward(Sigma2=[1,2,3], W2=0, Omega_tilt=0,
                curvature_delta=0, weights=[1,1,2], x_ceiling=[0,1,1],
                identifiable=[True,True,False], q_thresholds=[1])
        self.assertEqual(a["Q_known_mass"], 0.25)
        self.assertEqual(a["Pi_intervals"][0]["lower"], 0.25)
        self.assertEqual(a["Pi_intervals"][0]["upper"], 1.0)
        self.assertEqual(a["x_known_mass"], 0.5)

    def test_large_weights_are_stable(self):
        a = self.adapter.departure_pushforward(Sigma2=[1,2], W2=0, Omega_tilt=0,
                curvature_delta=0, weights=[1e308,1e308], x_ceiling=1,
                identifiable=True, q_thresholds=[1])
        self.assertEqual(a["Pi_intervals"][0]["lower"], 0.5)

    def test_sources_not_mutated_or_global_imports_polluted(self):
        before = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in self.adapter.hashes}
        old_ssot = sys.modules.get("ssot")
        second = LegacyAdapter(ROOT, self.contract, expected_hashes=before)
        self.assertIs(sys.modules.get("ssot"), old_ssot)
        self.assertEqual(before, second.hashes)
        self.assertEqual(before, {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before})
        with self.assertRaises(ValueError):
            LegacyAdapter(ROOT, self.contract, expected_hashes={})

    def test_invalid_inputs_do_not_create_posteriors(self):
        with self.assertRaises(ValueError):
            self.adapter.departure_pushforward(Sigma2=1,W2=0,Omega_tilt=0,
              curvature_delta=0,weights=0,x_ceiling=1,identifiable=True)
        with self.assertRaises(ValueError):
            self.adapter.departure_pushforward(Sigma2=-1,W2=0,Omega_tilt=0,
              curvature_delta=0,weights=1,x_ceiling=1,identifiable=True)
        with self.assertRaises(ValueError):
            self.adapter.departure_pushforward(Sigma2=[1,2],W2=0,Omega_tilt=0,
              curvature_delta=0,weights=[[1],[1]],x_ceiling=1,identifiable=True)


if __name__ == "__main__":
    unittest.main()
