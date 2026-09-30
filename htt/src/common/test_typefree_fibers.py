import unittest
from fractions import Fraction

import numpy as np

from common.typefree_fibers import (ellipsoid_quotient_gauge, ellipsoid_fiber_image,
    BoundedRationalPolytope, rational_polytope_fiber_support)


class FunctionalFiberTests(unittest.TestCase):
    def test_quotient_minimum_witness_and_hidden_lifts(self):
        result = ellipsoid_quotient_gauge(np.eye(2), [[1, 0]], [.5])
        self.assertEqual(result.status, "DEFINED")
        self.assertEqual(result.gauge, .5)
        np.testing.assert_array_equal(result.witness, [.5, 0])
        self.assertGreater(np.linalg.norm([.5, 2]), result.gauge)
        scaled = ellipsoid_quotient_gauge(np.diag([4., 1.]), [[1, 0]], [4])
        self.assertEqual((scaled.gauge, scaled.radius_sq), (2, 4))

    def test_zero_quotient_and_psd_range(self):
        zero = ellipsoid_quotient_gauge(np.eye(2), [[0, 0]], [0])
        self.assertEqual((zero.status, zero.gauge), ("NO_DIRECTIONS", 0))
        self.assertEqual(ellipsoid_quotient_gauge(np.eye(2), [[0, 0]], [1]).status,
                         "OUTSIDE_RESPONSE_RANGE")
        outside = ellipsoid_quotient_gauge(np.diag([1., 0.]), np.eye(2), [0, 1])
        self.assertEqual(outside.status, "OUTSIDE_RESPONSE_RANGE")
        self.assertEqual(ellipsoid_quotient_gauge(np.diag([1., 1e-18]), [[1, 0]], [0]).status,
                         "NUMERICALLY_UNRESOLVED")

    def test_disk_fiber_support_and_feasible_lift(self):
        image = ellipsoid_fiber_image(np.eye(2), [[1, 0]], [.5], np.eye(2))
        self.assertEqual(image.status, "DEFINED")
        np.testing.assert_allclose(image.target_center, [.5, 0])
        support = image.support([0, 1])
        self.assertAlmostEqual(support.value, np.sqrt(.75))
        self.assertAlmostEqual(support.witness[0], .5)
        self.assertAlmostEqual(np.linalg.norm(support.witness), 1)
        np.testing.assert_allclose(image.target_shape, np.diag([0, .75]))
        self.assertEqual(ellipsoid_fiber_image(np.eye(2), [[1, 0]], [2], np.eye(2)).status, "EMPTY_SET")
        self.assertEqual(ellipsoid_fiber_image(np.eye(2), [[1, 0]], [1], np.eye(2)).status,
                         "BOUNDARY_NUMERICALLY_UNRESOLVED")

    def test_bounded_domain_survives_ambient_kernel_failure(self):
        image = ellipsoid_fiber_image([[1]], [[0]], [0], [[1]])
        self.assertEqual(image.support([1]).value, 1)
        self.assertEqual(image.support([-1]).value, 1)
        interval = BoundedRationalPolytope((), (), (-1,), (1,))
        result = rational_polytope_fiber_support(interval, [[0]], [0], [1])
        self.assertEqual((result.lower, result.upper), (Fraction(-1), Fraction(1)))
        self.assertEqual(rational_polytope_fiber_support(interval, [[0]], [1], [1]).status,
                         "EMPTY_SET")

    def test_point_image_is_distinct_from_zero_quotient(self):
        point = ellipsoid_fiber_image([[1]], [[1]], [.5], [[1]])
        self.assertEqual(point.status, "POINT_IMAGE")
        self.assertEqual(point.support([1]).value, .5)
        zero = ellipsoid_fiber_image([[1]], [[0]], [0], [[0]])
        self.assertEqual(zero.status, "NO_DIRECTIONS")

    def test_exact_rational_coupled_fiber_not_marginal_box(self):
        box = BoundedRationalPolytope((), (), (-1, -1), (1, 1))
        result = rational_polytope_fiber_support(box, [[1, 1]], [0], [1, 1])
        self.assertEqual((result.lower, result.upper), (0, 0))
        point = rational_polytope_fiber_support(box, [[1, 1], [1, -1]], [1, 0], [1, 0])
        self.assertEqual((point.lower, point.upper), (Fraction(1, 2), Fraction(1, 2)))
        self.assertEqual(rational_polytope_fiber_support(box, [[1, 0]], [2], [1, 0]).status,
                         "EMPTY_SET")


if __name__ == "__main__":
    unittest.main()
