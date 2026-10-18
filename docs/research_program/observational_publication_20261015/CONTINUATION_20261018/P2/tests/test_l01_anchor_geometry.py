import math
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from l01_anchor_geometry import shared_anchor_bounds


def norm(v):
    return math.hypot(*v)


def dist(u, v):
    return norm([x-y for x, y in zip(u, v)])


class AnchorGeometryTests(unittest.TestCase):
    def bounds(self, a, u, v):
        return shared_anchor_bounds(norm(a), norm(u), norm(v), dist(a, u), dist(a, v))

    def test_exact_rational_witnesses_attain_both_distance_endpoints(self):
        a, u = [5., 0., 0.], [3., 4., 0.]
        for sign in (-1., 1.):
            v = [6., sign * 8., 0.]
            r = self.bounds(a, u, v)
            self.assertAlmostEqual(r["matched_reconstructed_distance_interval"][0], 5.)
            self.assertAlmostEqual(r["matched_reconstructed_distance_interval"][1], math.sqrt(153))
            self.assertAlmostEqual(dist(u, v), r["matched_reconstructed_distance_interval"][0 if sign == 1 else 1])

    def test_random_vectors_satisfy_bounds_and_scaling_residual(self):
        rng = random.Random(20261018)
        for _ in range(500):
            a, u, v = [[rng.gauss(0, 1) for j in range(7)] for i in range(3)]
            r = self.bounds(a, u, v)
            lo, hi = r["matched_reconstructed_distance_interval"]
            self.assertGreaterEqual(dist(u, v) + 1e-12, lo)
            self.assertLessEqual(dist(u, v) - 1e-12, hi)
            alpha = max(0., math.fsum(x*y for x, y in zip(u, v))/norm(v)**2)
            residual = dist(u, [alpha*x for x in v])/norm(u)
            self.assertGreaterEqual(residual+1e-12, r["best_nonnegative_scalar_residual_fraction_lower"])

    def test_orthogonal_blocks_simultaneously_attain_combined_endpoints(self):
        a1, u1 = [5., 0., 0.], [3., 4., 0.]
        a2, u2 = [2., 0., 0.], [2., 1., 0.]
        for sign, index in ((1., 0), (-1., 1)):
            v1, v2 = [6., sign*8., 0.], [1., sign*3., 0.]
            first, second = self.bounds(a1, u1, v1), self.bounds(a2, u2, v2)
            endpoint = math.hypot(first["matched_reconstructed_distance_interval"][index],
                                  second["matched_reconstructed_distance_interval"][index])
            self.assertAlmostEqual(endpoint, dist(u1+u2, v1+v2))
            if index == 0:
                b, c = norm(u1+u2), norm(v1+v2)
                cosine = (b*b+c*c-endpoint*endpoint)/(2*b*c)
                gain = max(0., math.fsum(x*y for x, y in zip(u1+u2, v1+v2))/c**2)
                self.assertAlmostEqual(dist(u1+u2, [gain*x for x in v1+v2])/b,
                                       math.sqrt(1-max(0., cosine)**2))

    def test_uniform_units_extreme_scales(self):
        lengths = [5., 5., 10., math.sqrt(20), math.sqrt(65)]
        reference = shared_anchor_bounds(*lengths)
        for factor in (1e-200, 1e-100, 1e100, 1e200):
            result = shared_anchor_bounds(*(x*factor for x in lengths))
            for x, y in zip(reference["matched_reconstructed_angle_degrees_interval"], result["matched_reconstructed_angle_degrees_interval"]):
                self.assertAlmostEqual(x, y, places=11)
            for x, y in zip(reference["matched_reconstructed_distance_interval"], result["matched_reconstructed_distance_interval"]):
                self.assertAlmostEqual(x, y/factor, places=11)

    def test_same_vector_collinear_limit(self):
        r = shared_anchor_bounds(5., 5., 10., 0., 5.)
        self.assertEqual(r["matched_reconstructed_distance_interval"], [5., 5.])
        self.assertEqual(r["best_nonnegative_scalar_residual_fraction_lower"], 0.)
        self.assertEqual(r["best_scalar_gain_interval"], [.5, .5])

    def test_orthogonal_case_requires_full_residual(self):
        r = self.bounds([1., 0., 0.], [1., 0., 0.], [0., 2., 0.])
        self.assertAlmostEqual(r["best_nonnegative_scalar_residual_fraction_lower"], 1.)

    def test_negative_collinear_does_not_use_negative_amplitude(self):
        r = self.bounds([1., 0., 0.], [1., 0., 0.], [-2., 0., 0.])
        self.assertEqual(r["best_scalar_gain_interval"], [0., 0.])
        self.assertEqual(r["best_nonnegative_scalar_residual_fraction_lower"], 1.)

    def test_bad_values_rejected(self):
        cases = [(1., 1., 1., 3., 1.), (1., 1., 1., -1., 1.),
                 (0., 1., 1., 1., 1.), (math.nan, 1., 1., 1., 1.),
                 (math.inf, 1., 1., 1., 1.), (True, 1., 1., 1., 1.),
                 (1e200, 1e-200, 1., 1e200, 1e200)]
        for args in cases:
            with self.subTest(args=args), self.assertRaises(ValueError):
                shared_anchor_bounds(*args)


if __name__ == "__main__":
    unittest.main()
