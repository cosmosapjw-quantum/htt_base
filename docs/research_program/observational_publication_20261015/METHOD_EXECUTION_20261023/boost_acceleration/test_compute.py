"""Independent falsifiers for the R24 response quotient calculation."""
import importlib.util
import json
import math
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("boost_compute", HERE / "compute.py")
boost = importlib.util.module_from_spec(spec)
spec.loader.exec_module(boost)


class ResponseChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.answer = boost.compute()

    def test_linearized_response_and_physical_domain(self):
        result = self.answer
        self.assertEqual(result["cohort"]["released"], 274)
        self.assertEqual(result["cohort"]["undefined"], 354)
        self.assertTrue(result["cohort"]["PGC_9031_present"])
        self.assertEqual(result["cohort"]["min_Vcmb_km_s"], 317.0)
        self.assertIn("LINEARIZED_DESIGN_COLUMNS",result["optical_response_relation"]["identifiability"])
        # A physical H is deliberately absent. A synthetic unit witness checks
        # only the first-order coefficient and SI conversion at fixed H.
        c = 299792458.0
        mpc_m = 3.085677581491367e22
        h = 70_000.0/mpc_m
        dmag = 0.01
        accel = dmag * math.log(10) * c * h / 5
        self.assertAlmostEqual((5/math.log(10))*accel/(c*h), dmag, places=14)
        self.assertLessEqual(result["t1"]["perturbation_error_m_s2"],
                             result["t1"]["perturbation_bound_m_s2"])

    def test_finite_q_counterexample_and_zero_limit(self):
        witness = boost.optical_counterexample(0.1)
        self.assertAlmostEqual(witness["plus_n_mag"], 0.2287874528, places=9)
        self.assertAlmostEqual(witness["linear_plus_n_mag"], 0.2171472410, places=9)
        self.assertAlmostEqual(witness["antipodal_sum_mag"], 0.0218240270, places=9)
        self.assertGreater(witness["plus_linear_difference_mag"], 0.01)
        self.assertEqual(boost.optical_counterexample(0)["plus_linear_difference_mag"], 0)
        q = 1e-5
        remainder = boost.optical_counterexample(q)["plus_linear_difference_mag"]
        self.assertLess(abs(remainder/q**2-5/(2*math.log(10))), 1e-5)
        self.assertEqual(self.answer["optical_response_relation"]["finite_q_counterexample"],
                         witness)

    def test_original_numerical_scenarios_unchanged(self):
        prior = json.loads((HERE/"first_candidate/RESULT.json").read_text())
        self.assertEqual(self.answer["scenarios"], prior["scenarios"])
        self.assertEqual(self.answer["cohort"], prior["cohort"])
        self.assertEqual(self.answer["t1"], prior["t1"])

    def test_exact_null_and_thresholds(self):
        for scenario in self.answer["scenarios"].values():
            svd = scenario["nuisance_profiled_response_svd"]
            self.assertEqual(svd["rank_sensitivity"],
                             {"1e-08":12,"1e-10":12,"1e-12":12})
            self.assertLess(svd["null_residual_norm_max"],1e-10)
            angles = scenario["canonical_K_vs_depth"]["degrees"]
            self.assertEqual(len(angles),3)
            self.assertTrue(all(0 <= x <= 90 for x in angles))
            self.assertLess(max(angles),5)
            for fit in scenario["conditional_fits"].values():
                self.assertLess(fit["normal_residual_relative"],1e-10)
                self.assertTrue(np.linalg.eigvalsh(fit["information_conditional"]).min()>0)

    def test_dense_actual_cohort_schur_reference(self):
        # Independent dense GLS Schur form, based on the first authored V.
        distance = boost.checked_sources()
        rows, ledger, ids, groups, folds, _, coords, n = distance.load()
        y, errors, v, feat = distance.features(rows,n)
        cov = distance.covariance(errors, groups,0.,0.)
        nuisance = np.column_stack((np.ones(274),np.log10(v),feat["measured_logWmxi"],
                                    feat["e_logWmxi"],*[feat[x] for x in distance.STF_NAMES]))
        k = (-5/(math.log(10)*v))[:,None]*n
        # Dense inverse is independent of triangular whitening used by compute.
        vinv_n = np.linalg.solve(cov,nuisance)
        vinv_k = np.linalg.solve(cov,k)
        projection = nuisance.T@vinv_n
        info = k.T@vinv_k-(k.T@vinv_n)@np.linalg.solve(projection,nuisance.T@vinv_k)
        reported = np.array(self.answer["scenarios"]["a_0.000_b_0.000"]["conditional_fits"]["K_given_nuisance"]["information_conditional"])
        np.testing.assert_allclose(info,reported,rtol=1e-10,atol=1e-12)


if __name__ == "__main__":
    unittest.main()
