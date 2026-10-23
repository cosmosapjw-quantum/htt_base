"""Pure finite fixtures only; no source archive rows or original D07 campaign."""
import ast
from pathlib import Path
import unittest

import numpy as np

from sdss_estimator import (ATOL_MAG, RTOL, directions, fit_source_errors,
                            independent_full_intercept_lstsq, shape8)


class FiniteEstimator(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(20261018)
        self.ra = rng.uniform(0, 360, 300)
        self.dec = np.rad2deg(np.arcsin(rng.uniform(-1, 1, 300)))
        self.z = rng.uniform(.01, .1, 300)
        self.true = rng.normal(0, .01, 300)
        self.eta = self.true + rng.normal(0, .03, 300)
        self.sd = rng.uniform(.02, .06, 300)

    def fit(self, eta=None, sd=None):
        return fit_source_errors(self.ra, self.dec, self.z, self.true,
                                 self.eta if eta is None else eta, self.sd if sd is None else sd)

    def assertMagClose(self, a, b):
        np.testing.assert_allclose(a, b, atol=ATOL_MAG, rtol=RTOL)

    def test_exact_d07_pure_basis_parity(self):
        path = Path(__file__).parent.parent / "D07_JOINT_CALIBRATION/d07.py"
        tree = ast.parse(path.read_text())
        node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "shape8")
        namespace = {"np": np}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(path), "exec"), namespace)
        n = directions(self.ra, self.dec)
        np.testing.assert_array_equal(shape8(n), namespace["shape8"](n))

    def test_zero_error(self):
        fit = self.fit(self.true)
        self.assertMagClose(fit["coefficients_mag"], np.zeros(16))
        self.assertMagClose(fit["weighted_scalar_mean_errors_mag"], np.zeros(2))

    def test_constant_eta_shift_changes_only_scalar_mean(self):
        before, after = self.fit(), self.fit(self.eta + .01)
        self.assertMagClose(after["coefficients_mag"], before["coefficients_mag"])
        self.assertMagClose(after["weighted_scalar_mean_errors_mag"] - before["weighted_scalar_mean_errors_mag"], [-.05, -.05])

    def test_nx_eta_shift(self):
        nx = directions(self.ra, self.dec)[:, 0]
        before, after = self.fit(), self.fit(self.eta + .002*nx)
        expected = np.zeros(16)
        expected[[0, 8]] = -.01
        self.assertMagClose(after["coefficients_mag"]-before["coefficients_mag"], expected)

    def test_profiled_solution_agrees_independent_full_intercept(self):
        fit = self.fit()
        for i, kernel in enumerate(fit["window_kernels"]):
            full = independent_full_intercept_lstsq(fit["design"], fit["error_mag"], fit["sigma_mag"], kernel)
            self.assertMagClose(fit["coefficients_mag"][i*8:(i+1)*8], full[1:])
            self.assertMagClose(fit["profiled_intercepts_mag"][i], full[0])

    def test_shared_window_covariance_matches_independent_sum(self):
        fit = self.fit()
        A, sigma = fit["slope_maps"], fit["sigma_mag"]
        cross = sum(np.outer(A[:8, i], A[8:, i])*sigma[i]**2 for i in range(len(sigma)))
        self.assertMagClose(fit["working_covariance_mag2"][:8, 8:], cross)
        self.assertGreater(np.max(np.abs(cross)), 0)
        # Gaussian-window covariance is not its inverse weighted Gram matrix.
        kernel = fit["window_kernels"][1]
        weights = kernel / sigma**2
        X = fit["design"]
        centered = X - weights@X/weights.sum()
        inverse_gram = np.linalg.inv(centered.T@(weights[:, None]*centered))
        self.assertGreater(np.max(np.abs(inverse_gram-fit["working_covariance_mag2"][8:, 8:])), 1e-6)

    def test_rank_deficiency_rejected_without_ridge(self):
        with self.assertRaisesRegex(ValueError, "Rank-deficient"):
            fit_source_errors(np.zeros(300), np.zeros(300), self.z, self.true, self.eta, self.sd)

    def test_invalid_values_never_dropped(self):
        for bad in (0., -1., np.nan, np.inf):
            sd = self.sd.copy()
            sd[4] = bad
            with self.assertRaises(ValueError):
                self.fit(sd=sd)
        eta = self.eta.copy()
        eta[3] = np.nan
        with self.assertRaises(ValueError):
            self.fit(eta=eta)


if __name__ == "__main__":
    unittest.main()
