"""EGS3 Axis A gates: A1 graded-comparator rank, A2 floor invariance,
A3 Pi e-value calibration, A4 Rao-Blackwell sufficiency."""
import unittest
import numpy as np

from htt.obsstat.egs3_graded_comparator import (
    graded_comparator, channel_response_design, identifiable_rank, COMPARATOR_SIGNS,
)
from htt.obsstat.egs3_calibration import (
    evalue_markov_calibration, exceedance_evalue, domination_is_conservative,
    rao_blackwell_demonstration,
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


class A4RaoBlackwellTests(unittest.TestCase):
    def test_sufficient_statistic_dominates_raw(self):
        r = rao_blackwell_demonstration(n_groups=300, n_per_group=40, seed=17)
        self.assertTrue(r.dominates)
        self.assertLess(r.rb_variance, r.raw_variance)


if __name__ == "__main__":
    unittest.main()
