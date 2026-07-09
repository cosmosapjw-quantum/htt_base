"""EGS3 Axis G gates: T3-lin linearized realization of the identified-set endpoints.

G1 realize_endpoint reproduces the two registered identified-interval endpoints
   (x_C = 11/100 and 17/100, open-curvature branch) with Gauss + momentum +
   invariant residuals < 1e-10, correct curvature/WEC branch labels;
G2 antipodal-pair identities: energy-flux cancellation q(beta)+q(-beta)=0 exact
   (SymPy) and tilt additivity Omega_tilt(beta)+Omega_tilt(-beta)=2(1+w)Om sinh^2;
G3 a fixed-seed random small-target sweep keeps every residual < 1e-10 and is
   deterministic (same seed -> identical);
G4 linearized_realization_seal() status PASS, carries seal/status/claim_boundary,
   records the library versions, and is deterministic;
G5 (CoVe adversarial guard) the module performs NO x_C mutation --- the graded
   comparator anchor stays bit-identical (g=(0.12,0,0.03,0) -> x_C = 0.15 exactly,
   np.array_equal) --- and the module docstring carries no forbidden claim string.

Diagnostic-only; the module realizes a linearized (x_C << 1) first jet and makes
no observational, class-identification, geometry, or solver-produced claim.
"""
import unittest

import numpy as np

from htt.obsstat import egs3_linearized_realization as lr
from htt.obsstat.egs3_linearized_realization import (
    realize_endpoint, antipodal_flux_cancellation, linearized_realization_seal,
    REGISTERED_ENDPOINTS, RESIDUAL_TOL, X_MAX,
)
from htt.obsstat.egs3_graded_comparator import COMPARATOR_SIGNS
from htt.obsstat.egs3_psd_cone import sector_matrix, xc_from_matrix


class G1RealizeEndpointTests(unittest.TestCase):
    def test_both_registered_endpoints_have_tiny_residuals(self):
        for name, target in REGISTERED_ENDPOINTS.items():
            rep = realize_endpoint(target)
            self.assertLess(rep["gauss_residual"], RESIDUAL_TOL, name)
            self.assertLess(rep["momentum_residual"], RESIDUAL_TOL, name)
            self.assertLess(rep["invariant_residual"], RESIDUAL_TOL, name)

    def test_endpoint_x_c_values(self):
        lower = realize_endpoint(REGISTERED_ENDPOINTS["lower_xC_11_over_100"])
        upper = realize_endpoint(REGISTERED_ENDPOINTS["upper_xC_17_over_100"])
        self.assertAlmostEqual(lower["x_C"], 0.11, places=12)
        self.assertAlmostEqual(upper["x_C"], 0.17, places=12)

    def test_reconstructed_invariants_match_target(self):
        for name, target in REGISTERED_ENDPOINTS.items():
            rep = realize_endpoint(target)
            recon = rep["reconstructed_invariants"]
            for key in ("Sigma2", "W2", "Omega_tilt", "Omega_k"):
                self.assertAlmostEqual(recon[key], float(target[key]), places=12,
                                       msg=f"{name}:{key}")

    def test_branch_labels(self):
        lower = realize_endpoint(REGISTERED_ENDPOINTS["lower_xC_11_over_100"])
        upper = realize_endpoint(REGISTERED_ENDPOINTS["upper_xC_17_over_100"])
        # lower endpoint uses the W^2 ceiling and no curvature (flat);
        # upper endpoint uses the Omega_k ceiling (open) and no vorticity.
        self.assertEqual(lower["curvature_branch"], "flat")
        self.assertEqual(upper["curvature_branch"], "open")
        self.assertEqual(lower["wec_branch"], "wec_satisfied")
        self.assertEqual(upper["wec_branch"], "wec_satisfied")

    def test_antipodal_flux_is_zero_at_endpoints(self):
        for target in REGISTERED_ENDPOINTS.values():
            rep = realize_endpoint(target)
            self.assertEqual(rep["antipodal_q_net"], 0.0)

    def test_domain_guard_rejects_supercritical_x_c(self):
        with self.assertRaises(ValueError):
            realize_endpoint({"Sigma2": X_MAX + 0.5, "W2": 0.0,
                              "Omega_tilt": 0.0, "Omega_k": 0.0})

    def test_negative_second_moment_rejected(self):
        with self.assertRaises(ValueError):
            realize_endpoint({"Sigma2": -0.01, "W2": 0.0,
                              "Omega_tilt": 0.0, "Omega_k": 0.0})


class G2AntipodalPairTests(unittest.TestCase):
    def test_flux_cancellation_exact(self):
        flux = antipodal_flux_cancellation()
        self.assertTrue(flux["q_cancels"])
        self.assertEqual(flux["q_net"], "0")

    def test_tilt_additivity_exact(self):
        flux = antipodal_flux_cancellation()
        self.assertTrue(flux["omega_tilt_additive"])
        self.assertEqual(flux["omega_tilt_additivity_residual"], "0")


class G3RandomSweepTests(unittest.TestCase):
    def test_sweep_residuals_below_tolerance(self):
        sweep = lr._random_small_target_sweep()
        self.assertLess(sweep["max_gauss_residual"], RESIDUAL_TOL)
        self.assertLess(sweep["max_momentum_residual"], RESIDUAL_TOL)
        self.assertLess(sweep["max_invariant_residual"], RESIDUAL_TOL)
        self.assertLessEqual(sweep["max_x_C"], X_MAX)

    def test_sweep_is_deterministic(self):
        self.assertEqual(lr._random_small_target_sweep(),
                         lr._random_small_target_sweep())


class G4SealTests(unittest.TestCase):
    def test_seal_passes(self):
        seal = linearized_realization_seal()
        self.assertEqual(seal["status"], "PASS")

    def test_seal_shape_mirrors_parent_identity(self):
        seal = linearized_realization_seal()
        for key in ("seal", "status", "sympy_version", "numpy_version",
                    "claim_boundary"):
            self.assertIn(key, seal)
        self.assertEqual(seal["seal"], "egs3.linearized_realization")

    def test_seal_records_all_residuals_below_tolerance(self):
        seal = linearized_realization_seal()
        self.assertLess(seal["max_gauss_residual"], RESIDUAL_TOL)
        self.assertLess(seal["max_momentum_residual"], RESIDUAL_TOL)
        self.assertLess(seal["max_invariant_residual"], RESIDUAL_TOL)

    def test_seal_is_deterministic(self):
        self.assertEqual(linearized_realization_seal(),
                         linearized_realization_seal())


class G5CoVeAdversarialGuard(unittest.TestCase):
    """Bit-identity guard on x_C + forbidden-claim-string guard on the docstring."""

    FORBIDDEN_STRINGS = ("posterior", "family", "native solver", "detection")

    def test_x_c_anchor_is_bit_identical_and_exactly_0p15(self):
        g = np.array([0.12, 0.0, 0.03, 0.0])
        inline = 0.12 - 0.0 + 0.03 + 0.0            # the value computed inline
        # recompute two independent ways: the graded comparator <c,g> and the
        # PSD-cone trace functional tr(C diag(g)); both must be bit-identical.
        via_graded = float(COMPARATOR_SIGNS @ g)
        via_trace = xc_from_matrix(sector_matrix(g))
        self.assertTrue(np.array_equal(via_graded, 0.15))
        self.assertTrue(np.array_equal(via_graded, inline))
        self.assertTrue(np.array_equal(via_trace, via_graded))

    def test_realize_endpoint_does_not_mutate_the_comparator(self):
        before = COMPARATOR_SIGNS.copy()
        rep = realize_endpoint({"Sigma2": 0.12, "W2": 0.0,
                                "Omega_tilt": 0.03, "Omega_k": 0.0})
        # the module's own x_C for this g is bit-identical to the 0.15 anchor
        self.assertTrue(np.array_equal(rep["x_C"], 0.15))
        # and it left the shared comparator sign vector untouched
        self.assertTrue(np.array_equal(COMPARATOR_SIGNS, before))

    def test_module_docstring_has_no_forbidden_claim_string(self):
        doc = (lr.__doc__ or "").lower()
        for token in self.FORBIDDEN_STRINGS:
            self.assertNotIn(token, doc, f"forbidden claim string {token!r} in docstring")

    def test_module_docstring_states_linearized_scope(self):
        doc = (lr.__doc__ or "").lower()
        self.assertIn("linearized", doc)
        self.assertIn("not a full nonlinear gr sharpness theorem", doc)


if __name__ == "__main__":
    unittest.main()
