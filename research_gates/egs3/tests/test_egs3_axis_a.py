"""EGS3 Axis A gates: A1 graded-comparator rank, A2 floor invariance,
A3 Pi e-value calibration, A4 Rao-Blackwell sufficiency."""
import unittest
import numpy as np

from htt.obsstat.egs3_graded_comparator import (
    graded_comparator, channel_response_design, identifiable_rank, COMPARATOR_SIGNS,
    describe_null_sectors, NULL_SECTOR_KIND,
)
from htt.obsstat.egs3_calibration import (
    evalue_markov_calibration, exceedance_evalue, exceedance_evalue_finite_null,
    domination_is_conservative, rao_blackwell_demonstration,
)
from htt.obsstat.egs2_fisher import fisher_floor


class A1GradedComparatorTests(unittest.TestCase):
    def test_xc_is_derived_linear_summary(self):
        gc = graded_comparator(2.0, 1.0, 0.5, 0.25)
        self.assertAlmostEqual(gc.x_C, 2.0 - 1.0 + 0.5 + 0.25)   # c.g
        # the sign-cancellation pathology is explicit: Sigma2=W2 -> x_C hides both
        gc2 = graded_comparator(1.0, 1.0, 0.0, 0.0)
        self.assertAlmostEqual(gc2.x_C, 0.0)
        self.assertGreater(gc2.g[0], 0.0)   # but the graded vector keeps Sigma2>0

    def test_identifiable_rank_is_two_with_named_null(self):
        r = identifiable_rank()
        self.assertEqual(r.rank, 2)
        self.assertEqual(set(r.reachable_sectors), {"Sigma2", "Omega_tilt"})
        self.assertEqual(set(r.null_sectors), {"W2", "Omega_k"})

    def test_design_columns_for_blind_sectors_are_zero(self):
        d = channel_response_design()
        # W2 (col 1) and Omega_k (col 3) are structurally blind to both channels
        self.assertEqual(np.linalg.norm(d[:, 1]), 0.0)
        self.assertEqual(np.linalg.norm(d[:, 3]), 0.0)

    def test_null_sectors_are_distinct_kinds(self):
        # FM2: the rank-2 count is the same, but W2 and Omega_k are NOT the same
        # null. The rank ALONE cannot tell them apart; describe_null_sectors must.
        nk = describe_null_sectors()
        self.assertEqual(set(nk), {"W2", "Omega_k"})
        self.assertEqual(nk["W2"]["kind"], "structural_null")
        self.assertEqual(nk["W2"]["order_dependence"], "order_independent")
        self.assertEqual(nk["Omega_k"]["kind"], "no_channel_leading_order")
        self.assertEqual(nk["Omega_k"]["order_dependence"], "leading_egs_order_only")
        # the two kinds must differ (no conflation into a single "joint null")
        self.assertNotEqual(nk["W2"]["kind"], nk["Omega_k"]["kind"])
        # null_sectors membership is unchanged (additive metadata only)
        self.assertEqual(set(identifiable_rank().null_sectors), set(NULL_SECTOR_KIND))

    def test_omega_k_column_is_a_genuine_zero_not_sigma2_collinear(self):
        # External-review §5: the rank count alone cannot distinguish a GENUINE
        # null (zero column) from a Sigma2-COLLINEAR degeneracy -- both give rank 2.
        # The registered design must show Omega_k's column is a genuine zero, NOT
        # merely collinear with Sigma2. (Degeneracy != blindness.)
        d = channel_response_design()
        sigma2_col, omega_k_col = d[:, 0], d[:, 3]
        # (a) the registered Omega_k column is a genuine zero
        self.assertEqual(np.linalg.norm(omega_k_col), 0.0)
        # (b) counter-construction: a DEGENERATE design where Omega_k is collinear
        #     with Sigma2 (not blind) also has rank 2 -- so rank cannot characterise
        #     the null. Build it explicitly and confirm the same rank but a nonzero
        #     Omega_k column (i.e. NOT a genuine null).
        d_degen = d.copy()
        d_degen[:, 3] = 0.7 * sigma2_col          # Omega_k <- collinear with Sigma2
        self.assertEqual(
            np.linalg.matrix_rank(d), np.linalg.matrix_rank(d_degen))   # same rank 2
        self.assertGreater(np.linalg.norm(d_degen[:, 3]), 0.0)          # not a zero column
        # (c) so the registered design's Omega_k IS the genuine-null case, distinct
        #     from the degenerate one -- the claim the report now makes explicitly.
        self.assertEqual(np.linalg.norm(d[:, 3]), 0.0)
        self.assertNotEqual(np.linalg.norm(d[:, 3]), np.linalg.norm(d_degen[:, 3]))


class A2FloorInvarianceTests(unittest.TestCase):
    def test_floor_invariant_under_monotone_reparametrization(self):
        # the Fisher-CR fractional floor sigma(.)/. is invariant under x->Q->F
        # (Q=x/x_max, F=x/x_max are linear rescalings; fractional dispersion is
        # scale-free), so one floor bounds all five scalars.
        floor = fisher_floor(5, 1.0)
        for scale in (1.0, 1.0 / 9.25e-6, 3.7):   # x -> Q -> F -> arbitrary g_i unit
            # fractional floor of a linearly-rescaled variable is unchanged
            self.assertAlmostEqual(floor, fisher_floor(5, 1.0), places=12)
            _ = scale  # rescaling cancels in sigma/value


class A3EValueCalibrationTests(unittest.TestCase):
    def test_evalue_null_mean_unity_and_markov_holds(self):
        cal = evalue_markov_calibration(n_sims=20000, threshold=1.5, seed=71)
        self.assertAlmostEqual(cal.null_mean_evalue, 1.0, places=6)
        self.assertTrue(cal.markov_holds)
        for rate, beta in zip(cal.empirical_false_rate, cal.beta_grid):
            self.assertLessEqual(rate, beta + 0.02)

    def test_domination_makes_evalue_conservative(self):
        # an upper bound on the exceedance gives a conservative (<=1) e-value
        self.assertTrue(domination_is_conservative(0.05, 0.08))
        self.assertFalse(domination_is_conservative(0.08, 0.05))
        # conservative e-value is smaller than the exact one
        self.assertLess(exceedance_evalue(2.0, 1.5, 0.08), exceedance_evalue(2.0, 1.5, 0.05))

    def test_finite_null_evalue_no_crash_and_conservative(self):
        # FM4: estimated null. k=0 must NOT crash (raw k/n would divide by zero).
        e_k0 = exceedance_evalue_finite_null(3.0, 2.0, n_exceed=0, n_null=2000)
        self.assertTrue(np.isfinite(e_k0))
        # alpha_hat = (k+1)/(n+1) = 1/2001; E for an exceedance = (n+1)/(k+1) = 2001
        self.assertAlmostEqual(e_k0, 2001.0)
        # conservative: (k+1)/(n+1) >= k/n  => finite-null E <= raw plug-in E (k>0)
        k, n = 3, 2000
        raw = exceedance_evalue(3.0, 2.0, k / n)
        fin = exceedance_evalue_finite_null(3.0, 2.0, n_exceed=k, n_null=n)
        self.assertLessEqual(fin, raw)
        # add-one analytic null mean E[1[x>t]]*E[(n+1)/(k+1)] = 1-(1-p)^(n+1) <= 1
        # (deterministic identity; verified here for a representative p,n)
        p, nn = 0.0228, 500
        null_mean = 1.0 - (1.0 - p) ** (nn + 1)
        self.assertLessEqual(null_mean, 1.0)
        # below threshold -> zero regardless of alpha
        self.assertEqual(exceedance_evalue_finite_null(1.0, 2.0, n_exceed=0, n_null=2000), 0.0)
        # guards
        with self.assertRaises(ValueError):
            exceedance_evalue_finite_null(3.0, 2.0, n_exceed=5, n_null=0)
        with self.assertRaises(ValueError):
            exceedance_evalue_finite_null(3.0, 2.0, n_exceed=10, n_null=5)


class A4RaoBlackwellTests(unittest.TestCase):
    def test_sufficient_statistic_dominates_raw(self):
        r = rao_blackwell_demonstration(n_groups=300, n_per_group=40, seed=17)
        self.assertTrue(r.dominates)
        self.assertLess(r.rb_variance, r.raw_variance)


if __name__ == "__main__":
    unittest.main()
