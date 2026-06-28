"""EGS2 gates: NT2-A1 genuine Fisher floor, NT2-A2 sufficiency, NT2-B1 bracket."""
import unittest

from htt.obsstat.egs2_fisher import (
    fisher_floor, single_ell_sampling_dispersion, octupole_sufficiency_tail,
    mc_estimator_dispersion,
)
from htt.obsstat.egs2_shear_bracket import filling_bracket


class FisherFloorTests(unittest.TestCase):
    def test_single_ell_recovers_report_value(self):
        self.assertAlmostEqual(single_ell_sampling_dispersion(2, 1.0), (2 / 5) ** 0.5, places=12)
        # quad_only Fisher floor == single-ell sampling dispersion
        self.assertAlmostEqual(fisher_floor(2, 1.0, "quad_only"), (2 / 5) ** 0.5, places=12)

    def test_floor_strictly_below_0632_and_decreasing(self):
        f2 = fisher_floor(2, 1.0)
        f5 = fisher_floor(5, 1.0)
        f20 = fisher_floor(20, 1.0)
        self.assertAlmostEqual(f2, (2 / 5) ** 0.5, places=12)   # l=2 only -> 0.632
        self.assertLess(f5, 0.632)                              # strictly below
        self.assertLess(f20, f5)                                # decreases with L
        # sky cut raises the floor
        self.assertGreater(fisher_floor(5, 0.7), fisher_floor(5, 1.0))

    def test_mc_mle_achieves_floor(self):
        for L in (2, 5, 10):
            res = mc_estimator_dispersion(L, 1.0, n_real=4000, seed=21)
            self.assertTrue(0.9 <= res.ratio <= 1.1, (L, res.ratio))

    def test_octupole_information_saturates(self):
        # NT2-A2: the Fisher information converges (the floor saturates) as more
        # multipoles are added -- diminishing returns beyond the octupole.
        from htt.obsstat.egs2_fisher import fisher_information, response_coeffs
        f40 = fisher_floor(40, 1.0)
        f80 = fisher_floor(80, 1.0)
        self.assertLess(abs(f80 - f40) / f40, 0.01)             # < 1% change -> saturated
        tail = octupole_sufficiency_tail(80, 1.0)
        self.assertGreater(tail["info_total"], tail["info_tail_l_gt_3"])  # a2,a3 carry the majority
        self.assertLess(tail["tail_fraction"], 0.5)
        # convergence shape: the per-multipole Fisher contribution decreases
        # monotonically for l>=3, so the tail sum is convergent.
        r = response_coeffs(80)
        contrib = [(2 * ell + 1) / 2.0 * r[ell] ** 2 for ell in sorted(r) if ell >= 3]
        self.assertTrue(all(contrib[i + 1] < contrib[i] for i in range(len(contrib) - 1)))
        # successive-decade increments shrink (saturation, not divergence)
        inc_2_10 = fisher_information(10, 1.0) - fisher_information(2, 1.0)
        inc_10_80 = fisher_information(80, 1.0) - fisher_information(10, 1.0)
        self.assertLess(inc_10_80, inc_2_10)


class TwoSidedBracketTests(unittest.TestCase):
    def test_nonzero_quadrupole_excludes_zero_filling(self):
        for a2, a3 in [(1e-5, 2e-6), (3e-5, 6e-6), (1e-4, 3e-5)]:
            br = filling_bracket(a2, a3)
            self.assertTrue(br.h3_satisfied)
            self.assertGreater(br.F_lo, 0.0)        # zero shear-filling excluded
            self.assertGreater(br.F_hi, br.F_lo)
            self.assertTrue(br.excludes_zero)

    def test_h3_violation_does_not_exclude_zero(self):
        # a3/a2 > R* (=1): H3 fails, no exclusion asserted
        br = filling_bracket(1e-5, 2e-5)
        self.assertFalse(br.h3_satisfied)
        self.assertFalse(br.excludes_zero)

    def test_zero_quadrupole_no_lower_bound(self):
        br = filling_bracket(0.0, 0.0)
        self.assertEqual(br.F_lo, 0.0)
        self.assertFalse(br.excludes_zero)

    def test_c_up_placeholder_flagged_and_nondegeneracy_robust(self):
        # FM5: C_up=9 is a documented PLACEHOLDER; the published nondegeneracy
        # headline (C_up*kappa>1) must be flagged robust-to-the-exact-constant.
        from htt.obsstat.egs2_shear_bracket import nondegeneracy_threshold, C_UP
        br = filling_bracket(3e-5, 6e-6)
        self.assertEqual(br.c_up_provenance, "placeholder")
        self.assertAlmostEqual(br.nondegeneracy_c_up_min, 1.0 / (4.0 / 21.0))  # 5.25
        self.assertTrue(br.nondegeneracy_robust)              # C_up=9 > 5.25 (margin)
        self.assertGreater(C_UP, nondegeneracy_threshold())
        # a sub-threshold C_up would NOT robustly carry the headline (placeholder-sensitive)
        weak = filling_bracket(3e-5, 6e-6, c_up=4.0)
        self.assertFalse(weak.nondegeneracy_robust)
        # the LOWER-bound zero-exclusion is c_up-independent -> still holds for weak C_up
        self.assertTrue(weak.excludes_zero)


if __name__ == "__main__":
    unittest.main()
