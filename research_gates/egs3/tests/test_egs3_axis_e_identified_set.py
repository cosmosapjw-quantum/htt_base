"""EGS3 Axis E gates: identified-set semantics for the signed comparator (P26/P31/P35/P36/P28/P29, A8).

E1 two-stage tau + A8 status classification (feasible/empty/unbounded/ceiling_unfit)
   with the population interval reproducing the registered [0.11, 0.17] example and
   a closed-form cross-check of the constrained endpoints;
E2 Imbens-Manski endpoint semantics: defining equation, z-bracket, and MC coverage
   ordering (projection conservative > IM nominal > naive endpoint undercovers);
E3 refutability: empty-set rate = specification-test size at zero injection, power
   monotone in the injected misfit amplitude, -> 1;
E4 G_F joint-feasible-set interval is a subset of (never wider than) the naive
   quotient; degenerate shared box collapses to equality; positivity guard;
E5 e-value merging: arithmetic mean stays an e-value under maximal dependence
   (linearity), Ville anytime-validity crossing rates within bounds;
E6 prior exposure: posterior marginal on a null response direction == prior
   (KL = 0 exactly); coupled-prior movement is prior-driven, not data-driven;
E7 (CoVe adversarial + bit-identity guard) the semantics survive alpha/m/seed
   sweeps; x_C stays bit-identical; no registered statistic is added.

Chain-of-code: analytic numbers recomputed two independent ways where available.
Diagnostic-only; no detection, family/geometry, native-solver, or posterior claim.
"""
import math
import unittest

import numpy as np
from scipy import stats

from htt.obsstat import egs3_identified_set as ids
from htt.obsstat.egs3_identified_set import (
    two_stage_tau, identified_set_report, reachable_endpoints_closed_form,
    im_critical_value, im_interval, projection_interval, endpoint_interval,
    im_coverage_experiment, refutability_power_experiment, toy_design,
    STATUS_FEASIBLE, STATUS_EMPTY, STATUS_UNBOUNDED, STATUS_CEILING_UNFIT,
)
from htt.obsstat.egs3_gf_interval import (
    gf_naive_quotient, gf_joint_interval, gf_joint_vs_naive,
)
from htt.obsstat.egs3_evalue_merge import arithmetic_merge_mc, test_martingale_ville_mc
from htt.obsstat.egs3_prior_exposure import gaussian_prior_exposure_witness
from htt.obsstat.egs3_psd_cone import sector_matrix, xc_from_matrix
from htt.obsstat.egs3_graded_comparator import COMPARATOR_SIGNS, channel_response_design

SEED = 20260708

# the six frozen registered low-ell statistics (lowell_precision / morphology)
REGISTERED_STATISTICS = (
    "s_one_half", "parity_even_over_odd_ratio", "parity_asymmetry",
    "planarity_mean", "qo_axis_alignment_deg", "axis_to_cmb_dipole_deg",
)


def _toy_y(toy, scale=1.0):
    return toy["R"] @ (toy["g_true"] * scale)


class E1IdentifiedSetSemanticsTests(unittest.TestCase):
    def test_two_stage_tau_matches_chi2_two_ways(self):
        tau = two_stage_tau(6, 2, alpha1=0.05, alpha2=0.05)
        self.assertAlmostEqual(tau.tau1, float(stats.chi2.ppf(0.95, 4)), places=10)
        self.assertAlmostEqual(tau.tau2, float(stats.chi2.ppf(0.95, 2)), places=10)
        # independent route: chi2 ppf via isf
        self.assertAlmostEqual(tau.tau1, float(stats.chi2.isf(0.05, 4)), places=10)

    def test_population_interval_reproduces_registered_example(self):
        toy = toy_design()
        rep = identified_set_report(_toy_y(toy), toy["R"], toy["c"],
                                    toy["lower"], toy["upper"], alpha2=1.0)
        self.assertEqual(rep.status, STATUS_FEASIBLE)
        self.assertAlmostEqual(rep.x_lo, 0.11, places=9)
        self.assertAlmostEqual(rep.x_hi, 0.17, places=9)
        self.assertEqual(rep.rank, 2)

    def test_constrained_endpoints_match_closed_form_when_box_inactive(self):
        # scale the truth far from the cone boundary so the box is inactive
        toy = toy_design()
        y = _toy_y(toy, scale=100.0)
        rep = identified_set_report(y, toy["R"], toy["c"],
                                    toy["lower"], toy["upper"], alpha2=0.05)
        A = toy["R"][:, [0, 2]]
        lo_cf, hi_cf = reachable_endpoints_closed_form(
            A, y, np.array([1.0, 1.0]), rep.tau.tau2)
        self.assertAlmostEqual(rep.reachable_lo, lo_cf, places=6)
        self.assertAlmostEqual(rep.reachable_hi, hi_cf, places=6)

    def test_empty_on_orthogonal_misfit(self):
        toy = toy_design()
        A = toy["R"][:, [0, 2]]
        q, _ = np.linalg.qr(A, mode="complete")
        u = q[:, -1]
        rep = identified_set_report(_toy_y(toy) + 10.0 * u, toy["R"], toy["c"],
                                    toy["lower"], toy["upper"])
        self.assertEqual(rep.status, STATUS_EMPTY)
        self.assertFalse(rep.spec_pass)
        self.assertGreater(rep.spec_stat, rep.spec_threshold)

    def test_empty_when_ellipsoid_misses_the_cone(self):
        toy = toy_design()
        A = toy["R"][:, [0, 2]]
        y = A @ np.array([-5.0, -5.0])       # truth deep outside the cone
        rep = identified_set_report(y, toy["R"], toy["c"],
                                    toy["lower"], toy["upper"])
        self.assertEqual(rep.status, STATUS_EMPTY)
        self.assertTrue(rep.spec_pass)        # stage 1 passes; the CONE rejects

    def test_unbounded_when_a_null_ceiling_is_missing(self):
        toy = toy_design()
        upper = toy["upper"].copy()
        upper[1] = np.inf                     # drop the W^2 MES ceiling
        rep = identified_set_report(_toy_y(toy), toy["R"], toy["c"],
                                    toy["lower"], upper, alpha2=1.0)
        self.assertEqual(rep.status, STATUS_UNBOUNDED)
        self.assertTrue(math.isinf(rep.null_lo))

    def test_ceiling_unfit_clips_f_above_one(self):
        toy = toy_design()
        rep = identified_set_report(_toy_y(toy), toy["R"], toy["c"],
                                    toy["lower"], toy["upper"], alpha2=1.0,
                                    ceiling_U=0.05)
        self.assertEqual(rep.status, STATUS_CEILING_UNFIT)
        self.assertGreater(rep.F_hi, 1.0)
        # a consistent ceiling keeps the report feasible with F in [0, 1]
        rep2 = identified_set_report(_toy_y(toy), toy["R"], toy["c"],
                                     toy["lower"], toy["upper"], alpha2=1.0,
                                     ceiling_U=0.5)
        self.assertEqual(rep2.status, STATUS_FEASIBLE)
        self.assertLessEqual(rep2.F_hi, 1.0)

    def test_non_axis_aligned_null_raises_not_implemented(self):
        # rank-deficient ACTIVE block (duplicated column) -> honest refusal
        R = np.zeros((6, 4))
        R[:3, 0] = 1.0
        R[:3, 2] = 1.0                        # collinear with column 0
        toy = toy_design()
        with self.assertRaises(NotImplementedError):
            identified_set_report(np.zeros(6), R, toy["c"],
                                  toy["lower"], toy["upper"])

    def test_deterministic(self):
        toy = toy_design()
        a = identified_set_report(_toy_y(toy), toy["R"], toy["c"],
                                  toy["lower"], toy["upper"], alpha2=0.05)
        b = identified_set_report(_toy_y(toy), toy["R"], toy["c"],
                                  toy["lower"], toy["upper"], alpha2=0.05)
        self.assertEqual(a, b)


class E2ImbensManskiCoverageTests(unittest.TestCase):
    def test_critical_value_satisfies_defining_equation(self):
        for delta, se in [(0.06, 0.12), (0.0, 1.0), (2.0, 0.5)]:
            cn = im_critical_value(delta, se, alpha=0.05)
            resid = (stats.norm.cdf(cn + delta / se) - stats.norm.cdf(-cn)) - 0.95
            self.assertLess(abs(resid), 1e-10)

    def test_critical_value_brackets_between_one_and_two_sided_z(self):
        z1 = float(stats.norm.ppf(0.95))
        z2 = float(stats.norm.ppf(0.975))
        for delta in (0.0, 0.05, 0.5, 5.0):
            cn = im_critical_value(delta, 1.0, alpha=0.05)
            self.assertLessEqual(z1 - 1e-9, cn)
            self.assertLessEqual(cn, z2 + 1e-9)
        # limits: delta=0 -> two-sided; delta huge -> one-sided
        self.assertAlmostEqual(im_critical_value(0.0, 1.0), z2, places=6)
        self.assertAlmostEqual(im_critical_value(50.0, 1.0), z1, places=6)

    def test_interval_orderings_are_structural(self):
        lo_p, hi_p = projection_interval(0.11, 0.17, 0.1, 0.1)
        lo_i, hi_i, _ = im_interval(0.11, 0.17, 0.1, 0.1)
        lo_e, hi_e = endpoint_interval(0.11, 0.17, 0.1, 0.1)
        # projection superset of IM superset of endpoint (z2 >= C_N >= z1)
        self.assertLessEqual(lo_p, lo_i)
        self.assertLessEqual(lo_i, lo_e)
        self.assertLessEqual(hi_e, hi_i)
        self.assertLessEqual(hi_i, hi_p)

    def test_mc_coverage_ordering_and_nominal_level(self):
        cov = im_coverage_experiment(n_mc=2000, seed=SEED)
        se3 = 3.0 * cov.se_binomial
        # IM within 3 SE of the nominal 95%
        self.assertLess(abs(cov.coverage_im - 0.95), se3)
        # projection conservative (at or above nominal)
        self.assertGreaterEqual(cov.coverage_projection, 0.95 - se3)
        self.assertGreaterEqual(cov.coverage_projection, cov.coverage_im)
        # the naive endpoint construction undercovers in the small-Delta regime
        self.assertLess(cov.coverage_endpoint, cov.coverage_im)
        self.assertLess(cov.coverage_endpoint, 0.95 - cov.se_binomial)


class E3RefutabilityPowerTests(unittest.TestCase):
    def test_size_power_and_monotonicity(self):
        pw = refutability_power_experiment(n_mc=1000, seed=SEED)
        # size: empty rate at zero injection within 3 SE of alpha1
        self.assertLess(abs(pw.empty_rate[0] - pw.alpha1), 3.0 * max(pw.se[0], 7e-3))
        # power: monotone nondecreasing within 2-SE slack, and -> 1
        for r0, r1, s0, s1 in zip(pw.empty_rate, pw.empty_rate[1:], pw.se, pw.se[1:]):
            self.assertGreaterEqual(r1, r0 - 2.0 * (s0 + s1))
        self.assertGreaterEqual(pw.empty_rate[-1], 0.99)


class E4GFJointIntervalTests(unittest.TestCase):
    def test_joint_is_subset_of_naive_and_narrower(self):
        cmp_ = gf_joint_vs_naive()
        self.assertTrue(cmp_.joint_within_naive)
        self.assertLessEqual(cmp_.width_ratio, 1.0)
        self.assertLess(cmp_.width_ratio, 0.9)   # strict gain on the registered toy

    def test_degenerate_shared_box_collapses_to_equality(self):
        cmp_ = gf_joint_vs_naive(shared_bounds=((0.0, 0.0), (0.0, 0.0)))
        self.assertAlmostEqual(cmp_.joint[0], cmp_.naive[0], places=12)
        self.assertAlmostEqual(cmp_.joint[1], cmp_.naive[1], places=12)

    def test_no_shared_components_reduces_to_naive_quotient(self):
        joint = gf_joint_interval((0.11, 0.17), (0.2, 0.26), (), (), ())
        naive = gf_naive_quotient((0.11, 0.17), (0.2, 0.26))
        self.assertEqual(joint, naive)

    def test_denominator_positivity_guard(self):
        with self.assertRaises(ValueError):
            gf_naive_quotient((0.1, 0.2), (-0.1, 0.3))
        with self.assertRaises(ValueError):
            gf_joint_interval((0.1, 0.2), (0.01, 0.05), ((0.0, 0.2),),
                              (1.0,), (-1.0,))


class E5EvalueMergeTests(unittest.TestCase):
    def test_arithmetic_merge_stays_evalue_under_maximal_dependence(self):
        res = arithmetic_merge_mc(seed=SEED)
        self.assertEqual(res.dependence, "common_factor")
        self.assertTrue(res.mean_le_one)
        # linearity: the mean is 1 EXACTLY in expectation; 4 SE two-sided check
        self.assertLess(abs(res.merged_mean - 1.0), 4.0 * res.se)

    def test_independent_case_also_calibrated(self):
        res = arithmetic_merge_mc(dependence="independent", seed=SEED)
        self.assertLess(abs(res.merged_mean - 1.0), 4.0 * res.se)

    def test_ville_anytime_validity(self):
        res = test_martingale_ville_mc(seed=SEED)
        self.assertTrue(res.ville_holds)
        margin = 3.0 / math.sqrt(res.n_paths)
        for beta, rate in zip(res.beta_grid, res.crossing_rate):
            self.assertLessEqual(rate, beta + margin)


class E6PriorLeakTests(unittest.TestCase):
    def test_null_direction_posterior_equals_prior_exactly(self):
        wit = gaussian_prior_exposure_witness(seed=SEED)
        self.assertEqual(wit.kl_null_block, 0.0)          # closed form, EXACT zero
        self.assertLess(wit.max_abs_moment_diff, 1.0)     # 3-sigma-normalized MC

    def test_coupled_prior_movement_is_prior_driven(self):
        wit = gaussian_prior_exposure_witness(seed=SEED)
        self.assertGreater(wit.coupled_prior_kl, 0.0)


class E7CoVeAdversarialTests(unittest.TestCase):
    """Adversarial sweeps + the bit-identity guard (mirrors C6)."""

    def test_population_interval_invariant_across_alpha_and_m(self):
        for m in (4, 6, 10):
            toy = toy_design(m=m)
            for a1 in (0.01, 0.05, 0.1):
                rep = identified_set_report(_toy_y(toy), toy["R"], toy["c"],
                                            toy["lower"], toy["upper"],
                                            alpha1=a1, alpha2=1.0)
                self.assertEqual(rep.status, STATUS_FEASIBLE)
                self.assertAlmostEqual(rep.x_lo, 0.11, places=9)
                self.assertAlmostEqual(rep.x_hi, 0.17, places=9)

    def test_refutability_size_stable_across_seeds(self):
        for seed in (SEED, SEED + 1, SEED + 2):
            pw = refutability_power_experiment(amplitudes=(0.0,), n_mc=800,
                                               seed=seed)
            self.assertLess(abs(pw.empty_rate[0] - 0.05), 4.0 * max(pw.se[0], 8e-3))

    def test_im_critical_value_monotone_in_delta(self):
        cns = [im_critical_value(d, 1.0) for d in (0.0, 0.2, 0.5, 1.0, 3.0)]
        for a, b in zip(cns, cns[1:]):
            self.assertGreaterEqual(a, b - 1e-12)         # C_N decreases with delta

    def test_xc_stays_bit_identical(self):
        for g in [(2.0e-6, 1.5e-6, 8.0e-7, 3.0e-7), (1.0, 1.0, 0.0, 0.0),
                  (3.7, 0.0, 0.5, 0.25)]:
            self.assertTrue(np.array_equal(
                xc_from_matrix(sector_matrix(g)),
                float(COMPARATOR_SIGNS @ np.asarray(g))))

    def test_channel_response_design_untouched(self):
        D = channel_response_design()
        self.assertTrue(np.array_equal(
            D, np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 1, 0]], dtype=float)))

    def test_module_adds_no_registered_statistic(self):
        names = set(dir(ids))
        self.assertEqual(names.intersection(REGISTERED_STATISTICS), set())
        self.assertNotIn("channel_response_design", names)
        self.assertNotIn("_RESPONSE_SUPPORT", names)


if __name__ == "__main__":
    unittest.main()
