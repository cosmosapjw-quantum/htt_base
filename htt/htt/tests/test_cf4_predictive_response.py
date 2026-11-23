"""Independent GLS, integral normalization and response checks for the R101 law."""
import numpy as np
import unittest
from numpy.testing import assert_allclose
from scipy.integrate import quad
from scipy.special import ndtr
from scipy.stats import norm

from htt.infer.cf4_predictive_response import (
    predictive_contrasts, predictive_covariance_response, selected_probit_field_response,
)


from scripts.r101.benchmark_cf4_response import direct_kriging


class TestCF4Responses(unittest.TestCase):
    def test_predictive_contrasts_equal_gls_and_its_finite_differences(self):
        rng = np.random.default_rng(43)
        n, m, p = 12, 7, 4
        x, h = rng.normal(size=(n, p)), rng.normal(size=(m, p))
        y = rng.normal(size=n + m)
        noise, delta = rng.normal(size=(2, n + m, n + m))
        c = noise @ noise.T + np.eye(n + m)
        dc = (delta + delta.T) / 2
        contrasts = predictive_contrasts(x, h)
        result = predictive_covariance_response(y, c, dc, contrasts)
        step = 1e-5
        baseline = direct_kriging(y, c, x, h)
        plus = direct_kriging(y, c+step*dc, x, h)
        minus = direct_kriging(y, c-step*dc, x, h)
        for i, key in enumerate(("mean", "covariance", "chi2", "log_density")):
            assert_allclose(result[key], baseline[i], rtol=1e-11, atol=1e-12)
            assert_allclose(result[key+"_tangent"], (plus[i]-minus[i])/(2*step),
                            rtol=2e-7, atol=5e-9)
        drift = rng.normal(size=p)
        shifted = predictive_covariance_response(y+np.r_[x@drift, h@drift], c, dc, contrasts)
        assert_allclose(shifted["log_density"], result["log_density"])
        assert_allclose(shifted["mean_tangent"], result["mean_tangent"], atol=1e-12)
        y[n:] += 1e10
        changed = predictive_covariance_response(y, c, dc, contrasts)
        assert_allclose(changed["mean"], result["mean"])
        assert_allclose(changed["mean_tangent"], result["mean_tangent"])

    def test_free_and_saturated_common_mean(self):
        for p in [0, 3]:
            with self.subTest(p=p):
                x = np.eye(3)[:, :p]
                h = np.ones((2, p))
                y = np.arange(5.)
                c = np.eye(5)
                result = predictive_covariance_response(y, c, c, predictive_contrasts(x, h))
                assert_allclose(result["mean"], h @ (x.T @ y[:3]))
                assert_allclose(result["covariance"], np.eye(2) + h @ h.T)
                assert_allclose(result["mean_tangent"], 0, atol=1e-15)
                assert_allclose(result["covariance_tangent"], result["covariance"])
                assert_allclose(result["chi2_tangent"], -result["chi2"])
                assert_allclose(result["log_density_tangent"], 0.5*(result["chi2"]-2))

    def test_fail_closed_on_design_rank_asymmetry_or_invalid_covariance(self):
        with self.assertRaisesRegex(ValueError, "rank"):
            predictive_contrasts(np.ones((4, 2)), np.ones((1, 2)))
        x = predictive_contrasts([[1]], [[1]])
        with self.assertRaisesRegex(ValueError, "symmetric"):
            predictive_covariance_response([1, 2], [[2, 1], [0, 2]], np.eye(2), x)
        with self.assertRaises(np.linalg.LinAlgError):
            predictive_covariance_response([1, 2], [[-.1, 0], [0, 1]], np.eye(2), x)

    def test_shared_field_normalizer_and_score(self):
        for slope in [-1.1, 0, 3.2]:
            with self.subTest(slope=slope):
                means = np.array([[-.5, .1], [.2, -.7], [1.2, .4]])
                tangent = np.array([[.6, -.2], [-.1, -.4], [.8, .2]])
                sig = [.3, .45]
                a = np.array([-.6, .7])
                y = np.array([.2, -.3])
                p = np.array([.3, .1, .6])
                out = selected_probit_field_response(y, means, sig, a, slope, p, mean_tangent=tangent)
                # Direct continuous mark integral separately per object and shared field.
                component_p = np.array([np.prod([
                    quad(lambda v: norm.pdf(v, loc=mu, scale=sig[j])*ndtr(a[j]+slope*v),
                         -np.inf, np.inf, epsabs=1e-12)[0] for j, mu in enumerate(row)])
                    for row in means])
                numerator = np.sum(p * np.prod(norm.pdf(y, means, sig) * ndtr(a + slope*y), axis=1))
                assert_allclose(out["log_joint_inclusion"], np.log(p @ component_p), atol=2e-12)
                assert_allclose(out["log_density"], np.log(numerator/(p@component_p)), atol=2e-12)
                assert_allclose(out["included_field_weights"], p*component_p/(p@component_p), atol=2e-12)
                step = 1e-5
                for q in ("log_joint_inclusion", "log_density"):
                    plus = selected_probit_field_response(y, means+step*tangent, sig, a, slope, p)[q]
                    minus = selected_probit_field_response(y, means-step*tangent, sig, a, slope, p)[q]
                    assert_allclose(out[q+"_tangent"], (plus-minus)/(2*step), atol=1e-8)

    def test_native_eta_magnitude_change_of_measure_and_r100_cut(self):
        y = np.array([-.1, .05, .15])
        mean = np.array([[-.01, .03, -.04], [.06, -.03, .01]])
        sigma = np.array([.08, .06, .10])
        fiducial = np.array([34.1, 33.0, 35.1])
        p = [.3, .7]
        eta = selected_probit_field_response(y, mean, sigma, .55/.30, 5/.30, p)
        mag = selected_probit_field_response(fiducial-5*y, fiducial-5*mean, 5*sigma,
                                             (fiducial+.55)/.30, -1/.30, p)
        assert_allclose(eta["log_density"]-len(y)*np.log(5), mag["log_density"], atol=3e-12)
        assert_allclose(eta["log_joint_inclusion"], mag["log_joint_inclusion"], atol=3e-12)

    def test_negative_indicators_reweight_the_shared_field_and_integrate_out_marks(self):
        means = np.array([[-.8, .5], [.9, -.3]])
        widths = np.array([.5, .4])
        p = np.array([.3, .7])
        a, b = np.array([-.2, .3]), np.array([1.4, -.9])
        marks, kept = np.array([.2, np.nan]), np.array([True, False])

        def conditional(scale, tangent=False):
            return selected_probit_field_response(marks, scale*means, widths, a, b, p,
                                                  included=kept, mean_tangent=means if tangent else None)
        out = conditional(1, True)
        # Direct integration over the unobserved negative mark for each field.
        missed = np.asarray([quad(lambda v: norm.pdf(v, mu, widths[1])*ndtr(-a[1]-b[1]*v),
                                  -np.inf, np.inf)[0] for mu in means[:, 1]])
        positive = np.asarray([quad(lambda v: norm.pdf(v, mu, widths[0])*ndtr(a[0]+b[0]*v),
                                    -np.inf, np.inf)[0] for mu in means[:, 0]])
        w = p*missed*positive
        num = np.sum(p*missed*norm.pdf(marks[0], means[:, 0], widths[0])*ndtr(a[0]+b[0]*marks[0]))
        assert_allclose(out["included_field_weights"], w / w.sum(), atol=1e-12)
        assert_allclose(out["log_density"], np.log(num / w.sum()), atol=1e-12)
        for key in ("log_density", "log_inclusion_pattern"):
            fd = (conditional(1+1e-5)[key]-conditional(1-1e-5)[key]) / 2e-5
            assert_allclose(fd, out[key+"_tangent"], atol=1e-9)
        none = selected_probit_field_response([np.nan, np.nan], means, widths, a, b, p,
                                              included=[False, False], mean_tangent=means)
        assert_allclose([none["log_density"], none["log_density_tangent"]], [0, 0], atol=1e-15)

    def test_selected_tail_and_input_validation(self):
        r = selected_probit_field_response([1.], [[.1]], [1.], [-42.], [1.2], [1.],
                                           mean_tangent=[[.2]])
        self.assertTrue(np.isfinite(r["log_density_tangent"]))
        with self.assertRaisesRegex(ValueError, "probabilities"):
            selected_probit_field_response([.1], [[0.]], .2, 0, 1, [.8])
        with self.assertRaisesRegex(ValueError, "width"):
            selected_probit_field_response([.1], [[0.]], 0, 0, 1, [1.])


if __name__ == "__main__":
    unittest.main()
