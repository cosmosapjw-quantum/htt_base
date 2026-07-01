"""EGS3 Axis C gates: kinematic deprojection of the observer-boost quadrupole.

C1 closed-form deprojection alpha + projection zeroes a pure boost / preserves shear;
C2 coupled Fisher off-diagonal ~ beta^2 + covariance inflation 1/(1-r^2) -> 1;
C3 boost/tilt separation identifiability (generic rank 2; aligned degenerate);
C4 synthetic injection-recovery: naive Sigma^2 FPR high on a pure-boost sky vs
   deprojected Sigma_tilde^2 FPR nominal; genuine shear unbiased and covered;
C5 (CoVe) the FPR claim survives a beta/noise/axis sweep;
C6 (bit-identity guard) x_C stays bit-identical and no registered statistic is added.

Chain-of-code: each analytic number is recomputed two independent ways and asserted
equal. Diagnostic-only; no detection, family/geometry, or native-solver claim.
"""
import unittest
import numpy as np

from htt.obsstat import egs3_kinematic_deprojection as kd
from htt.obsstat.egs3_kinematic_deprojection import (
    deprojection_alpha, projected_shear, kinematic_quadrupole_coeff,
    coupled_fisher, response_correlation, covariance_inflation, legendre_p2,
    boost_tilt_identifiability, injection_recovery_experiment,
)
from htt.obsstat.egs3_psd_cone import sector_matrix, xc_from_matrix
from htt.obsstat.egs3_graded_comparator import COMPARATOR_SIGNS, channel_response_design

# gate-fixed injection-recovery regime (boost quadrupole above the amplitude noise)
BETA = 1.0e-3
KAPPA_TILT = 3.0
ALPHA = 1.0
SIGMA_QUAD = 1.0e-6
SIGMA_DIP = 3.0e-4
N_MOCK = 4000
SEED = 20260701

# the six frozen registered low-ell statistics (lowell_precision / morphology)
REGISTERED_STATISTICS = (
    "s_one_half", "parity_even_over_odd_ratio", "parity_asymmetry",
    "planarity_mean", "qo_axis_alignment_deg", "axis_to_cmb_dipole_deg",
)


class C1AlphaClosedFormTests(unittest.TestCase):
    def test_alpha_matches_closed_form_and_is_positive(self):
        for T0, kt, Rs, N2 in [(1.0, 1.0, 1.0, 1.0), (2.72548e6, 3.0, 0.7, 1.3),
                               (0.5, 2.0, 4.0, 2.0)]:
            a = deprojection_alpha(T0=T0, kappa_tilt=kt, R_sigma=Rs, N2=N2)
            expect = kinematic_quadrupole_coeff() * T0 * T0 * N2 / (kt * kt * Rs)
            self.assertAlmostEqual(a, expect, places=12)
            self.assertGreater(a, 0.0)

    def test_alpha_is_beta_independent(self):
        # alpha is a pure constant of the registered response; it takes no beta.
        self.assertNotIn("beta", deprojection_alpha.__code__.co_varnames)

    def test_alpha_eps_normalisation_reduces_to_doppler_boost_coeff(self):
        # registered eps-normalisation (T0=kappa_tilt=R_sigma=1, N2=9/4) -> alpha=1,
        # matching the eps1^2 coefficient in doppler_boost.py:94.
        self.assertAlmostEqual(
            deprojection_alpha(T0=1.0, kappa_tilt=1.0, R_sigma=1.0, N2=9.0 / 4.0),
            1.0, places=12)

    def test_projection_zeroes_a_pure_boost_sky(self):
        omega_tilt = KAPPA_TILT * BETA
        sigma2_naive = ALPHA * omega_tilt * omega_tilt          # pure-boost leakage
        self.assertAlmostEqual(projected_shear(sigma2_naive, omega_tilt, ALPHA), 0.0, places=15)

    def test_projection_preserves_genuine_shear(self):
        # omega_tilt = 0 -> no over-subtraction
        self.assertEqual(projected_shear(3.14e-5, 0.0, ALPHA), 3.14e-5)


class C2CoupledFisherTests(unittest.TestCase):
    def test_offdiagonal_scales_as_beta_squared(self):
        F1 = coupled_fisher(1.0e-3, kappa_tilt=KAPPA_TILT, alpha=ALPHA)
        F2 = coupled_fisher(2.0e-3, kappa_tilt=KAPPA_TILT, alpha=ALPHA)
        self.assertGreater(F1[0, 1], 0.0)
        self.assertAlmostEqual(F2[0, 1] / F1[0, 1], 4.0, places=9)   # (2beta)^2/beta^2

    def test_offdiagonal_vanishes_at_zero_beta(self):
        F0 = coupled_fisher(0.0, kappa_tilt=KAPPA_TILT, alpha=ALPHA)
        self.assertEqual(F0[0, 1], 0.0)

    def test_inflation_is_one_over_one_minus_r_squared(self):
        for beta in (5.0e-4, 1.0e-3, 5.0e-3, 2.0e-2):
            F = coupled_fisher(beta, kappa_tilt=KAPPA_TILT, alpha=ALPHA)
            r = response_correlation(F)
            self.assertAlmostEqual(
                covariance_inflation(beta, kappa_tilt=KAPPA_TILT, alpha=ALPHA),
                1.0 / (1.0 - r * r), places=12)

    def test_inflation_limit_and_monotonicity(self):
        self.assertEqual(covariance_inflation(0.0, kappa_tilt=KAPPA_TILT, alpha=ALPHA), 1.0)
        betas = [0.0, 1e-2, 5e-2, 1e-1, 2e-1]
        infl = [covariance_inflation(b, kappa_tilt=KAPPA_TILT, alpha=ALPHA) for b in betas]
        self.assertTrue(all(y2 >= y1 for y1, y2 in zip(infl, infl[1:])))
        self.assertTrue(all(x >= 1.0 for x in infl))


class C3IdentifiabilityTests(unittest.TestCase):
    def test_generic_axis_separates_rank_two(self):
        idr = boost_tilt_identifiability((1.0, 0.0, 0.0), (0.0, 0.0, 1.0), BETA)  # 90 deg
        self.assertEqual(idr.augmented_rank, 2)
        self.assertTrue(idr.separable)
        self.assertFalse(idr.degenerate)
        self.assertGreater(idr.gram_determinant, 0.0)
        self.assertEqual(set(idr.reachable_sectors), {"Sigma2", "Omega_tilt"})

    def test_parallel_axis_is_degenerate(self):
        idr = boost_tilt_identifiability((0.0, 0.0, 1.0), (0.0, 0.0, 1.0), BETA)
        self.assertTrue(idr.degenerate)
        self.assertFalse(idr.separable)
        self.assertAlmostEqual(idr.gram_determinant, 0.0, places=12)
        self.assertEqual(idr.augmented_rank, 1)

    def test_gram_determinant_matches_legendre_addition(self):
        for ang in (15.0, 45.0, 60.0, 89.0):
            th = np.radians(ang)
            vh = (np.sin(th), 0.0, np.cos(th))
            idr = boost_tilt_identifiability(vh, (0.0, 0.0, 1.0), BETA)
            self.assertAlmostEqual(idr.gram_determinant,
                                   1.0 - legendre_p2(np.cos(th)) ** 2, places=12)


class C4InjectionRecoveryTests(unittest.TestCase):
    def _run(self, sigma2_true, seed=SEED):
        return injection_recovery_experiment(
            beta=BETA, sigma2_true=sigma2_true, alpha=ALPHA, kappa_tilt=KAPPA_TILT,
            sigma_quad=SIGMA_QUAD, sigma_dip=SIGMA_DIP, n_mock=N_MOCK, seed=seed)

    def test_naive_fpr_high_deprojected_nominal_on_pure_boost(self):
        r = self._run(0.0)
        self.assertGreater(r["fpr_naive"], 0.30)
        self.assertLessEqual(r["fpr_deprojected"], 0.08)
        self.assertGreater(r["fpr_naive"], r["fpr_deprojected"])

    def test_genuine_shear_unbiased_and_covered(self):
        sig = 5.0e-5
        r = self._run(sig)
        self.assertLessEqual(abs(r["shear_bias"]), 0.05 * sig)
        self.assertGreaterEqual(r["shear_coverage"], 0.60)
        self.assertLessEqual(r["shear_coverage"], 0.75)

    def test_deterministic_under_seed(self):
        self.assertEqual(self._run(0.0), self._run(0.0))


class C5CoVeAdversarialTests(unittest.TestCase):
    """Chain-of-verification: try to break the FPR claim across a beta/noise/axis grid.
    Every non-degenerate cell must keep the deprojected FPR nominal and below naive."""

    def test_fpr_claim_survives_beta_noise_axis_sweep(self):
        failures = []
        for beta in (5.0e-4, 1.0e-3, 2.0e-3):
            for scale in (0.5, 1.0, 2.0):
                for ang in (15.0, 45.0, 89.0):     # exclude the aligned (degenerate) case
                    th = np.radians(ang)
                    vh = (np.sin(th), 0.0, np.cos(th))
                    r = injection_recovery_experiment(
                        beta=beta, sigma2_true=0.0, alpha=ALPHA, kappa_tilt=KAPPA_TILT,
                        sigma_quad=SIGMA_QUAD * scale, sigma_dip=SIGMA_DIP * scale,
                        v_hat=vh, sigma_axis=(0.0, 0.0, 1.0), n_mock=3000, seed=11)
                    if not (r["fpr_deprojected"] <= 0.08 and r["fpr_naive"] > r["fpr_deprojected"]):
                        failures.append((beta, scale, ang, r["fpr_naive"], r["fpr_deprojected"]))
        self.assertEqual(failures, [], f"FPR claim broke in {len(failures)} cells: {failures[:3]}")


class C6BitIdentityGuardTests(unittest.TestCase):
    """The deprojection is a SEPARATE surface: x_C stays bit-identical, the response
    design is untouched, and no new registered statistic is introduced."""

    def test_xc_from_matrix_unchanged_by_deprojection_module(self):
        for g in [(2.0e-6, 1.5e-6, 8.0e-7, 3.0e-7), (1.0, 1.0, 0.0, 0.0), (3.7, 0.0, 0.5, 0.25)]:
            self.assertTrue(np.array_equal(
                xc_from_matrix(sector_matrix(g)),
                float(COMPARATOR_SIGNS @ np.asarray(g))))

    def test_channel_response_design_is_the_registered_block_diagonal(self):
        D = channel_response_design()
        self.assertTrue(np.array_equal(
            D, np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 1, 0]], dtype=float)))

    def test_module_adds_no_registered_statistic(self):
        names = set(dir(kd))
        self.assertEqual(names.intersection(REGISTERED_STATISTICS), set())
        # and defines no response-design symbols (it never mutates the comparator)
        self.assertNotIn("channel_response_design", names)
        self.assertNotIn("_RESPONSE_SUPPORT", names)


if __name__ == "__main__":
    unittest.main()
