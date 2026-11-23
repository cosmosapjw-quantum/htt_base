from itertools import combinations
import numpy as np
import unittest
from scripts.r103.gaia_frame_curvature import curvature_rows, delete_covariance, shared_patch_refits


class GaiaFrameTests(unittest.TestCase):
    def test_affine_frames_and_quadratic_response(self):
        z = np.array([0.6, 1.15, 1.76, 2.46])
        w = curvature_rows(z)
        np.testing.assert_allclose(w @ np.column_stack([np.ones(4), z]), 0, atol=1e-14)
        np.testing.assert_allclose(w @ (z * z), 2)
        with self.assertRaises(ValueError):
            curvature_rows([0., 1., 1., 2.])


    def test_every_pair_matches_explicit_stacked_normal_equations(self):
        rng = np.random.default_rng(11)
        a = rng.normal(size=(4, 8, 7, 3))
        y = rng.normal(size=(4, 8, 7))
        fisher = np.einsum("spbi,spbj->spij", a, a)
        rhs = np.einsum("spbi,spb->spi", a, y)
        f, one, two, pairs = shared_patch_refits(fisher, rhs)
        for deleted, fit in [((), f)] + [((i,), v) for i, v in enumerate(one)] + list(zip(pairs, two)):
            keep = [i for i in range(8) if i not in deleted]
            ref = [1000 * np.linalg.lstsq(x[keep].reshape(-1, 3), yy[keep].ravel(), rcond=None)[0] for x, yy in zip(a, y)]
            np.testing.assert_allclose(fit, ref, rtol=1e-10, atol=1e-10)
        np.testing.assert_array_equal(pairs, list(combinations(range(8), 2)))


    def test_delete_covariance_normalization_matches_mean(self):
        data = np.array([2., 3., -1., 4., 7., 9.])
        for d in [1, 2]:
            samples = np.array([np.delete(data, idx).mean() for idx in combinations(range(len(data)), d)])
            np.testing.assert_allclose(delete_covariance(samples, len(data), d)[0, 0], np.var(data, ddof=1) / len(data))


    def test_unidentified_retained_design_fails(self):
        with self.assertRaises(np.linalg.LinAlgError):
            shared_patch_refits(np.zeros((4, 4, 2, 2)), np.zeros((4, 4, 2)))


if __name__ == "__main__":
    unittest.main()
