"""EGS3 Axis G gates (v9 follow-on, REV-R182): KE-DYN items 8-10.

G-KD-1  u-frame conservation identities exact (energy + Euler) on
        transverse and rotating oblique configurations, both types;
G-KD-2  Raychaudhuri identity DERIVED by undetermined coefficients
        (u(Theta) = -Theta^2/3 - sigma_ab sigma^ab + omega_ab omega^ab
        + div A - R_uu; A_a A^a coefficient exactly 0 because div is the
        full covariant divergence) and verified symbolically on rotating
        configurations;
G-KD-3  type-V rotating development: 7x7 first-principles system,
        constraint-satisfying non-vacuum oblique initial data, three
        constraints MONITORED below 1e-8, omega^2[u] > 0 throughout
        (dust AND radiation);
G-KD-4  the double Omega_k = 0 obstruction: (a) single stream excluded by
        the momentum constraint (G_ti = 0 identically, symbolic);
        (b) the antipodal pair is DYNAMICALLY irrotational (covector
        direction conserved -- structural identity on random states;
        omega^2 = 0 along the pair development);
G-KD-5  aligned BV-DYN trajectory in u-frame variables (energy
        conservation along the trajectory) + the radiation
        center-manifold drift law d(beta)/d(ln a) = +(2/3) beta^2 and the
        dust 3 gamma - 4 = -1 linear rate (literature-anchored reading of
        the R178 finding);
G-KD-6  seal PASS, net verdict recorded, withdrawal stays asserted;
G-KD-CoVe  x_C bit-identity + forbidden-string guard.
"""
import unittest

import numpy as np

from htt.obsstat.egs3_graded_comparator import COMPARATOR_SIGNS
from htt.obsstat.egs3_king_ellis_dynamics import (
    king_ellis_dynamics_seal,
    rotating_initial_data,
)
from htt.obsstat.egs3_psd_cone import sector_matrix, xc_from_matrix

_SEAL = king_ellis_dynamics_seal()   # heavy derivation cached once


class GKD1UFrameConservation(unittest.TestCase):
    def test_energy_and_euler_exact(self):
        c = _SEAL["uframe_conservation"]
        self.assertTrue(c["all_exact"])
        self.assertTrue(c["bianchi_i_oblique"]["energy_identity"])
        self.assertTrue(c["bianchi_i_oblique"]["euler_identity"])


class GKD2Raychaudhuri(unittest.TestCase):
    def test_derived_coefficients_standard_form(self):
        r = _SEAL["raychaudhuri_identity"]
        self.assertEqual(r["alpha_sigma2"], "-1")
        self.assertEqual(r["beta_omega2"], "1")
        self.assertEqual(r["gamma_A2"], "0")
        self.assertEqual(r["delta_divA"], "1")
        self.assertEqual(r["epsilon_Ruu"], "-1")
        self.assertTrue(all(r["checks"].values()))


class GKD3RotatingDevelopmentTypeV(unittest.TestCase):
    def test_dust_and_radiation(self):
        for key in ("rotating_development_bianchi_v_dust",
                    "rotating_development_bianchi_v_radiation"):
            row = _SEAL[key]
            self.assertTrue(row["preserved_at_tolerance"], key)
            self.assertTrue(row["nonvacuum_throughout"], key)
            self.assertTrue(row["omega2_positive_throughout"], key)
            self.assertLess(max(row["max_constraint_residuals"]), 1e-8)
            self.assertGreater(row["omega2_initial"], 0)

    def test_vacuum_request_rejected(self):
        with self.assertRaises(ValueError):
            rotating_initial_data(w=0.0, rho0=0.0)


class GKD4OmegaKZeroDoubleObstruction(unittest.TestCase):
    def test_single_stream_momentum_obstruction_symbolic(self):
        ob = _SEAL["type_i_single_stream_obstruction"]
        self.assertTrue(ob["g_tx_identically_zero"])
        self.assertTrue(ob["g_ty_identically_zero"])
        self.assertTrue(ob["obstruction_established"])

    def test_pair_dynamical_irrotationality(self):
        ir = _SEAL["type_i_dynamical_irrotationality"]
        self.assertTrue(ir["covector_direction_conserved"])
        self.assertLess(ir["max_rel_bilinear_residual"], 1e-10)
        pair = _SEAL["rotating_development_bianchi_i_antipodal_pair"]
        self.assertTrue(pair["preserved_at_tolerance"])
        self.assertLess(abs(pair["omega2_initial"]), 1e-25)
        self.assertLess(abs(pair["omega2_final"]), 1e-25)


class GKD5TrajectoryAndCenterManifold(unittest.TestCase):
    def test_aligned_uframe_energy_conservation(self):
        al = _SEAL["aligned_uframe_trajectory"]
        self.assertTrue(al["holds_at_grid_accuracy"])
        self.assertLess(al["u_frame_energy_conservation_max_rel_residual"],
                        5e-4)

    def test_radiation_center_manifold_law(self):
        cm = _SEAL["radiation_center_manifold"]
        self.assertTrue(cm["radiation"]["matches_quadratic_drift"])
        self.assertTrue(cm["dust"]["close_to_minus_one"])


class GKD6SealAndScope(unittest.TestCase):
    def test_seal_pass_verdict_withdrawal(self):
        self.assertEqual(_SEAL["status"], "PASS")
        self.assertEqual(_SEAL["theorem_id"], "KE-DYN")
        self.assertIn("8-10", _SEAL["items_discharged"])
        self.assertIn("DOUBLY obstructed", _SEAL["net_verdict"])
        self.assertIn("withdrawal STANDS", _SEAL["scope_not_claimed"])


class GKDCoVeAdversarialGuard(unittest.TestCase):
    FORBIDDEN_STRINGS = ("posterior", "detection", "native solver",
                         "family assignment")

    def test_x_c_anchor_bit_identical(self):
        g = np.array([0.12, 0.0, 0.03, 0.0])
        via_graded = float(COMPARATOR_SIGNS @ g)
        via_trace = xc_from_matrix(sector_matrix(g))
        self.assertTrue(np.array_equal(via_graded, 0.15))
        self.assertTrue(np.array_equal(via_trace, via_graded))

    def test_module_docstring_guard(self):
        import htt.obsstat.egs3_king_ellis_dynamics as mod
        doc = (mod.__doc__ or "").lower()
        for token in self.FORBIDDEN_STRINGS:
            self.assertNotIn(token, doc)
        self.assertIn("withdrawal", doc)
