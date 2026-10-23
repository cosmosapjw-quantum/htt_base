"""Small falsifiers for the frozen public-release conditional experiment."""

import json
import unittest

import numpy as np
from scipy.linalg import solve_triangular

import compute


class ReleaseExperimentTests(unittest.TestCase):
    def test_frozen_rows_and_covariance_are_in_original_order(self):
        frozen = json.loads(compute.SELECTION.read_text())
        rows, full, _ = compute.checked_sources()
        idx = np.array(frozen["selected_indices_0_based"], dtype=int)
        self.assertEqual(len(idx), 277)
        np.testing.assert_array_equal(idx, np.flatnonzero(rows["USED_IN_SH0ES_HF"] == 1))
        self.assertEqual(compute.digest(compute.ROWS), frozen["row_registry_sha256"])
        sub = full[np.ix_(idx, idx)]
        for i, j in [(0, 0), (0, -1), (31, 19), (-1, -1)]:
            self.assertEqual(sub[i, j], full[idx[i], idx[j]])
        np.linalg.cholesky(sub)

    def test_frozen_flow_sign_against_finite_difference(self):
        zobs = np.array([0.023, 0.04, 0.12])
        _, a = compute.background(zobs)
        k = -compute.M * (1 + a) / compute.C_KM_S
        eps = 0.01  # km/s; fixed observed z and zero background flow
        zp = (1 + zobs) / (1 + eps / compute.C_KM_S) - 1
        zm = (1 + zobs) / (1 - eps / compute.C_KM_S) - 1
        mp, _ = compute.background(zp)
        mm, _ = compute.background(zm)
        np.testing.assert_allclose((mp - mm) / (2 * eps), k, rtol=3e-9, atol=1e-10)
        self.assertTrue(np.all(k < 0))

    def test_permuted_rows_preserve_joint_coefficients(self):
        rows, full, _ = compute.checked_sources()
        idx = np.array(json.loads(compute.SELECTION.read_text())["selected_indices_0_based"], dtype=int)
        r = rows[idx]
        z = r["zCMB"].astype(float)
        mu, a = compute.background(z)
        n = compute.directions(r["RA"].astype(float), r["DEC"].astype(float))
        flow = (-compute.M * (1 + a) / compute.C_KM_S)[:, None] * n
        x = np.column_stack([np.ones(len(z)), n, flow])
        y = r["m_b_corr"].astype(float) - mu
        c = full[np.ix_(idx, idx)]
        labels = ["offset", "cal_x", "cal_y", "cal_z", "flow_x", "flow_y", "flow_z"]

        def solve(x, y, c):
            l = np.linalg.cholesky(c)
            return np.array(compute.fit(solve_triangular(l, y, lower=True), solve_triangular(l, x, lower=True), labels)["beta"])

        baseline = solve(x, y, c)
        perm = np.arange(len(z))[::-1]
        replay = solve(x[perm], y[perm], c[np.ix_(perm, perm)])
        self.assertLess(float(np.max(np.abs(baseline - replay) / np.maximum(1.0, np.abs(baseline)))), 1e-10)
        stored = json.loads((compute.HERE / "RESULT.json").read_text())
        np.testing.assert_allclose(baseline, stored["models"]["joint"]["beta"], rtol=1e-10, atol=1e-10)


if __name__ == "__main__":
    unittest.main()
