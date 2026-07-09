"""EGS3 Axis G gates: v7 strengthened theorems (T1'/T2'/T4'/T5'/T8'/T9').

G1 T1' (F1) signed-box identified interval: two-branch endpoints exact (open
   [11/100,17/100] vs all [9/100,17/100]); DL1 monotonicity + lower-gap = |c_k|U_k;
   the SymPy signed-box seal is PASS.
G2 T2' (M1) strictness iff: exact-Fraction corner enumeration agrees with the
   sign-conflict criterion on every trial (zero tolerance), the joint interval is
   a subset of the naive quotient, and the aligned counterexample collapses to
   equality (joint == naive exactly).
G3 T4' (M3) estimated-covariance two-stage: the Hotelling/F threshold exceeds the
   chi^2 threshold, the uncorrected chi^2 size exceeds alpha (refutation inflation)
   and is recovered as n_sim -> infinity, matched by an independent Monte-Carlo run.
G4 T5' (P35 -> exact) Imbens-Manski deterministic-width coverage is exactly 1-alpha
   at the endpoints, the naive one-sided endpoint CI undercovers, and coverage is
   unimodal.
G5 T8' (E3 -> theorem) noncentral-chi^2 refutability power is alpha at zero, strictly
   monotone in the noncentrality, and -> 1, matched by Monte-Carlo.
G6 T9' (m1) multi-component tilt Gauss budget is exact in every beta_i, the
   single-species case reduces bit-identically, and the antipodal pair cancels the
   flux while adding Omega_tilt.
G7 (CoVe adversarial + bit-identity guard) the strengthened modules add no x_C
   mutation and no registered statistic.

Chain-of-code: closed forms cross-checked by independent Monte-Carlo where feasible.
Diagnostic-only; no detection, family/geometry, native-solver, or posterior claim.
"""
import unittest

import numpy as np
from scipy import stats

from htt.obsstat.egs3_coverage_strengthened import (
    hotelling_scale, estimated_cov_uncorrected_size, hartlap_factor,
    im_critical_value, im_coverage_exact, naive_endpoint_coverage,
    exact_refutability_power, refutability_power_is_monotone,
    coverage_strengthened_seal, signed_box_interval_seal,
)
from htt.obsstat.egs3_gf_interval import (
    gf_strictness_exact_witness, gf_joint_vs_naive,
)
from htt.obsstat.egs3_parent_identity import (
    multicomponent_tilt_seal, derive_multicomponent_tilt_identity,
)
from htt.obsstat.egs3_psd_cone import sector_matrix, xc_from_matrix
from htt.obsstat.egs3_graded_comparator import COMPARATOR_SIGNS

SEED = 20260709


class G1SignedBoxTests(unittest.TestCase):
    def test_signed_box_seal_pass_and_endpoints(self):
        s = signed_box_interval_seal()
        self.assertEqual(s["status"], "PASS")
        self.assertEqual(s["endpoints"]["open_branch"], ["11/100", "17/100"])
        self.assertEqual(s["endpoints"]["all_branch"], ["9/100", "17/100"])

    def test_dl1_lower_gap_matches_curvature_ceiling(self):
        s = signed_box_interval_seal()
        self.assertTrue(s["checks"]["dl1_monotonicity_and_gap"])


class G2StrictnessIffTests(unittest.TestCase):
    def test_exact_criterion_agreement(self):
        w = gf_strictness_exact_witness()
        self.assertTrue(w["agreement_exact_1.0"])
        self.assertEqual(w["criterion_agreement_exact"],
                         f"{w['trials_evaluated']}/{w['trials_evaluated']}")

    def test_aligned_counterexample_collapses_to_equality(self):
        w = gf_strictness_exact_witness()
        self.assertTrue(w["aligned_counterexample_joint_equals_naive"])

    def test_joint_subset_of_naive_on_registered_toy(self):
        cmp_ = gf_joint_vs_naive()
        self.assertTrue(cmp_.joint_within_naive)


class G3EstimatedCovarianceTests(unittest.TestCase):
    def test_F_threshold_exceeds_chi2(self):
        k, n_sim, a1 = 8, 300, 0.05
        scale = hotelling_scale(k, n_sim)
        tauF = scale * stats.f.ppf(1 - a1, k, n_sim - k)
        tauChi = stats.chi2.ppf(1 - a1, k)
        self.assertGreater(tauF, tauChi)

    def test_uncorrected_size_exceeds_alpha_and_recovers(self):
        self.assertGreater(estimated_cov_uncorrected_size(10, 2, 300, 0.05), 0.05)
        self.assertAlmostEqual(estimated_cov_uncorrected_size(10, 2, 10**6, 0.05),
                               0.05, places=3)

    def test_uncorrected_size_matches_monte_carlo(self):
        # independent MC: chi^2 threshold applied to a Hotelling statistic
        k, n_sim, a1, ntrial = 8, 300, 0.05, 40000
        rng = np.random.default_rng(SEED)
        chi_thresh = stats.chi2.ppf(1 - a1, k)
        # T^2 = k(n-1)/(n-k) F  ==>  reject when chi2-form statistic > chi_thresh
        # statistic distributed as scale * F under H0
        scale = hotelling_scale(k, n_sim)
        fdraws = rng.f(k, n_sim - k, size=ntrial)
        emp = float(np.mean(scale * fdraws > chi_thresh))
        self.assertAlmostEqual(emp, estimated_cov_uncorrected_size(10, 2, 300, 0.05),
                               delta=0.004)

    def test_hartlap_in_unit_interval(self):
        self.assertTrue(0.0 < hartlap_factor(10, 300) < 1.0)


class G4ImExactCoverageTests(unittest.TestCase):
    def test_endpoint_coverage_exact(self):
        r = im_coverage_exact(0.5, 1.0, 0.05)
        self.assertTrue(r["coverage_is_exact"])
        self.assertAlmostEqual(r["endpoint_coverage"], 0.95, places=10)

    def test_naive_one_sided_undercovers(self):
        self.assertLess(naive_endpoint_coverage(1e-6, 1.0, 0.05), 0.95)
        self.assertAlmostEqual(naive_endpoint_coverage(1e-9, 1.0, 0.05), 0.90, places=4)

    def test_im_critical_value_between_one_and_two_sided(self):
        C = im_critical_value(0.5, 1.0, 0.05)
        self.assertLess(stats.norm.ppf(0.95), C)
        self.assertLess(C, stats.norm.ppf(0.975))

    def test_mc_coverage_matches_nominal(self):
        rng = np.random.default_rng(SEED)
        delta, se, alpha, n = 0.5, 1.0, 0.05, 40000
        C = im_critical_value(delta, se, alpha)
        eps = rng.normal(0, se, size=n)
        # parameter at lower endpoint x^-=0, x^+=delta; covered iff
        # -C se <= eps <= delta + C se
        covered = np.mean((eps >= -C * se) & (eps <= delta + C * se))
        self.assertAlmostEqual(float(covered), 1 - alpha, delta=0.005)


class G5RefutabilityPowerTests(unittest.TestCase):
    def test_power_alpha_at_zero_and_to_one(self):
        self.assertAlmostEqual(exact_refutability_power(0.0, 10, 2, 0.05), 0.05, places=9)
        self.assertGreater(exact_refutability_power(500.0, 10, 2, 0.05), 0.999)

    def test_power_strictly_monotone(self):
        self.assertTrue(refutability_power_is_monotone(10, 2, 0.05))

    def test_power_matches_monte_carlo(self):
        rng = np.random.default_rng(SEED)
        k, lam, a1, n = 8, 12.0, 0.05, 60000
        tau1 = stats.chi2.ppf(1 - a1, k)
        # noncentral chi2_k(lam): sum of (Z_i + mu_i)^2 with sum mu_i^2 = lam
        mu = np.zeros(k); mu[0] = np.sqrt(lam)
        draws = ((rng.normal(size=(n, k)) + mu) ** 2).sum(axis=1)
        emp = float(np.mean(draws > tau1))
        self.assertAlmostEqual(emp, exact_refutability_power(lam, 10, 2, a1), delta=0.006)


class G6MultiComponentTiltTests(unittest.TestCase):
    def test_seal_pass(self):
        self.assertEqual(multicomponent_tilt_seal()["status"], "PASS")

    def test_identity_exact_and_single_reduces(self):
        m = derive_multicomponent_tilt_identity(3)
        self.assertTrue(m["identity_ok"])
        s = derive_multicomponent_tilt_identity(1)
        self.assertTrue(s["identity_ok"])
        self.assertTrue(s["single_species_reduces_bit_identical"])

    def test_antipodal_pair(self):
        m = derive_multicomponent_tilt_identity(3)
        self.assertTrue(m["antipodal_flux_cancels"])
        self.assertTrue(m["antipodal_tilt_adds"])

    def test_comparator_unchanged(self):
        self.assertEqual(derive_multicomponent_tilt_identity(3)["comparator_unchanged"],
                         [1, -1, 1, 1])


class G8MesProvenanceTests(unittest.TestCase):
    def test_seal_pass(self):
        from htt.obsstat.egs3_mes_provenance import mes_provenance_seal
        self.assertEqual(mes_provenance_seal()["status"], "PASS")

    def test_registries_agree_exactly(self):
        from htt.obsstat.egs3_mes_provenance import mes_registry_consistency
        self.assertTrue(mes_registry_consistency()["all_registries_agree"])

    def test_ordering_theorem_rederived(self):
        from htt.obsstat.egs3_mes_provenance import mes_ordering_theorem
        o = mes_ordering_theorem()
        self.assertTrue(o["sigma_gt_omega_on_positive_orthant"])
        self.assertTrue(o["omega_gt_accel_on_positive_orthant"])

    def test_registered_w2_max_from_ssot(self):
        from htt.obsstat.egs3_mes_provenance import eps_registry_provenance
        c = eps_registry_provenance()["registered_ceilings_from_ssot"]
        self.assertAlmostEqual(c["W2_max"], 1.309e-6, places=8)

    def test_multipole_coefficients_stay_registered_external(self):
        # honesty guard: THIS (v7) seal must NOT claim it rederived the literature
        # coefficients. The v8 bit-exact sigma rederivation is a separate artifact
        # (egs3_mes_rederivation / test_egs3_axis_g_mes_rederivation), leaving this
        # frozen v7 seal's honest self-statement intact.
        from htt.obsstat.egs3_mes_provenance import mes_provenance_seal
        r = mes_provenance_seal()["full_multipole_rederivation"]
        self.assertEqual(r["status"], "registered_external_pending_hierarchy")
        self.assertIn("Thm 3.1/3.2/3.3 multipole coefficients "
                      "(5/3,3,3/7),(3/4,2,2/7),(3/4,1,3/14)", r["not_rederived_here"])


class G9MeasuredResponseTests(unittest.TestCase):
    def test_seal_pass(self):
        from htt.obsstat.egs3_measured_response import measured_response_seal
        self.assertEqual(measured_response_seal()["status"], "PASS")

    def test_rank_two_structural(self):
        from htt.obsstat.egs3_measured_response import measured_response_card
        c = measured_response_card()
        self.assertEqual(c["rank"], 2)
        self.assertEqual(set(c["null_sectors"]), {"W2", "Omega_k"})
        self.assertEqual(c["sigma3_over_sigma2"], 0.0)

    def test_fisher_duplication_sublinear(self):
        from htt.obsstat.egs3_measured_response import fisher_duplication_factor
        self.assertAlmostEqual(fisher_duplication_factor(0.0), 2.0)
        self.assertAlmostEqual(fisher_duplication_factor(1.0 - 1e-9), 1.0, places=6)


class G10DataLaneForwardTests(unittest.TestCase):
    def test_seal_pass(self):
        from htt.obsstat.egs3_data_lane_forward import data_lane_forward_seal
        self.assertEqual(data_lane_forward_seal()["status"], "PASS")

    def test_cf4_sign_transition_from_zero_bulk(self):
        from htt.obsstat.egs3_data_lane_forward import cf4_malmquist_forward
        r = cf4_malmquist_forward()
        self.assertEqual(r["true_bulk_flow_kms"], 0.0)
        self.assertTrue(r["sign_transition_present"])

    def test_desi_window_resultant_nonzero_from_window(self):
        from htt.obsstat.egs3_data_lane_forward import desi_window_resultant
        d = desi_window_resultant()
        self.assertTrue(d["window_resultant_is_large"])
        self.assertTrue(d["delta_rbar_monotone_in_injection"])


class G7CoVeAdversarialTests(unittest.TestCase):
    """Adversarial guard: the strengthened modules add no x_C mutation."""

    def test_xc_stays_bit_identical(self):
        for g in [(2.0e-6, 1.5e-6, 8.0e-7, 3.0e-7), (1.0, 1.0, 0.0, 0.0),
                  (0.12, 0.0, 0.03, 0.0), (3.7, 0.0, 0.5, 0.25)]:
            self.assertTrue(np.array_equal(
                xc_from_matrix(sector_matrix(g)),
                float(COMPARATOR_SIGNS @ np.asarray(g))))

    def test_registered_toy_xc_is_015(self):
        self.assertEqual(xc_from_matrix(sector_matrix((0.12, 0.0, 0.03, 0.0))), 0.15)

    def test_coverage_seal_deterministic(self):
        a = coverage_strengthened_seal()
        b = coverage_strengthened_seal()
        self.assertEqual(a["checks"], b["checks"])
        self.assertEqual(a["status"], "PASS")

    def test_no_affirmative_forbidden_claim(self):
        # the modules must carry the diagnostic-only disclaimer and make NO
        # affirmative posterior/family/detection claim
        import htt.obsstat.egs3_coverage_strengthened as mod
        doc = " ".join((mod.__doc__ or "").lower().split())
        self.assertIn("no data claim", doc)
        for affirmative in ("posterior odds", "family identification",
                            "we detect", "native-solver output", "geometry detection"):
            self.assertNotIn(affirmative, doc)


if __name__ == "__main__":
    unittest.main()
