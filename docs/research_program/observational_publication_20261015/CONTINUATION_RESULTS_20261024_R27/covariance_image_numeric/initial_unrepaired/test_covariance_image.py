"""Synthetic exact finite fixtures for the frozen covariance-image contract."""

import math
import unittest

import sympy as s

from covariance_image import (
    ABSENT_BOUND, EXACT_NULL, NEAR_NULL, UNAVAILABLE_MAP, UNBOUNDED,
    cone_membership, directional_support, floating_directional_diagnostic,
    joint_congruence, loewner_membership, marginal_directional_bounds,
    matrix_support, trace_membership,
    physical_response_status,
)


def same(actual, expected):
    assert s.simplify(actual - expected) == s.zeros(*actual.shape), (actual, expected)


class SyntheticExactFixtures(unittest.TestCase):
    def test_zero_and_range_gate(self):
        z = s.zeros(2)
        self.assertTrue(cone_membership(z, z)["member"])
        self.assertEqual(cone_membership(z, z)["protected_output_dimension"], 2)
        self.assertFalse(cone_membership(z, s.diag(1, 0))["member"])
        m = s.diag(1, 0)
        hit = cone_membership(m, s.diag(2, 0))
        self.assertTrue(hit["member"])
        same(hit["canonical_lift"], s.diag(2, 0))
        self.assertEqual(hit["minimum_trace"], 2)
        miss = cone_membership(m, s.diag(0, 1))
        self.assertFalse(miss["member"])
        self.assertEqual(miss["diagnostic_pseudoinverse_cost"], 0)
        self.assertFalse(trace_membership(m, s.diag(0, 1), 100)["trace_member"])

    def test_unique_minimum_trace_and_null_projector_family(self):
        m = s.Matrix([[1, 1]])
        c = s.Matrix([[1]])
        base = cone_membership(m, c)
        same(base["canonical_lift"], s.ones(2) / 4)
        self.assertEqual(base["minimum_trace"], s.Rational(1, 2))
        null_projector = s.Matrix([[1, -1], [-1, 1]]) / 2
        for t in (0, 1, 3):
            lift = base["canonical_lift"] + t * null_projector
            same(m * lift * m.T, c)
            self.assertEqual(s.trace(lift), s.Rational(1, 2) + t)
        self.assertTrue(trace_membership(m, c, s.Rational(1, 2))["trace_member"])
        self.assertFalse(trace_membership(m, c, s.Rational(1, 3))["trace_member"])

    def test_rectangular_rank_deficient_trace_and_orthogonal_change(self):
        m = s.Matrix([[1, 2, 0], [2, 4, 0]])
        k = s.Matrix([[1, 1], [2, 0], [0, 1]])
        c = m * k * k.T * m.T
        result = cone_membership(m, c)
        self.assertTrue(result["member"])
        lift = result["canonical_lift"]
        same(m * lift * m.T, c)
        self.assertTrue(all(e.is_nonnegative for e in lift.eigenvals()))
        self.assertEqual(result["minimum_trace"], s.trace(lift))
        row_permutation = s.Matrix([[0, 1], [1, 0]])
        column_permutation = s.Matrix([[0, 1, 0], [1, 0, 0], [0, 0, 1]])
        changed = cone_membership(row_permutation * m * column_permutation,
                                  row_permutation * c * row_permutation.T)
        self.assertTrue(changed["member"])
        self.assertEqual(changed["minimum_trace"], result["minimum_trace"])
        same(changed["canonical_lift"], column_permutation.T * lift * column_permutation)

    def test_trace_spectral_support_and_matrix_membership(self):
        eye = s.eye(2)
        h = s.diag(2, -3)
        trace = matrix_support(eye, h, covariance_class="trace", tau_squared=1)
        self.assertEqual(trace["value"], 2)
        same(trace["attainer"], s.diag(1, 0))
        self.assertEqual(s.trace(h * trace["attainer"]), trace["value"])
        self.assertEqual(matrix_support(eye, -eye, covariance_class="trace", tau_squared=1)["value"], 0)
        self.assertEqual(matrix_support(eye, s.zeros(2), covariance_class="trace", tau_squared=1)["value"], 0)
        self.assertEqual(matrix_support(eye, eye, covariance_class="trace", tau_squared=1)["value"], 1)
        self.assertEqual(matrix_support(eye, eye, covariance_class="spectral", tau_squared=1)["value"], 2)
        self.assertFalse(trace_membership(eye, eye, 1)["trace_member"])
        self.assertTrue(loewner_membership(eye, eye, eye)["member"])
        for u in (s.Matrix([1, 0]), s.Matrix([0, 1])):
            self.assertEqual(directional_support(eye, u, covariance_class="trace", tau_squared=1)["value"], 1)
            self.assertEqual(directional_support(eye, u, covariance_class="spectral", tau_squared=1)["value"], 1)

    def test_singular_loewner_cap_and_attainment(self):
        eye, g, h = s.eye(2), s.diag(4, 0), s.diag(2, -3)
        support = matrix_support(eye, h, covariance_class="loewner", G=g)
        self.assertEqual(support["value"], 8)
        same(support["attainer"], g)
        self.assertEqual(s.trace(h * support["attainer"]), 8)
        for value in (0, 1, 4):
            entry = loewner_membership(eye, s.diag(value, 0), g)
            self.assertTrue(entry["member"])
            same(eye * entry["lift"] * eye, s.diag(value, 0))
        self.assertFalse(loewner_membership(eye, s.diag(0, 1), g)["member"])

    def test_unbounded_support_null_and_nonzero_ray(self):
        m = s.Matrix([[s.Rational(1, 10**12)]])
        u = s.Matrix([1])
        result = directional_support(m, u, covariance_class="unbounded_psd")
        self.assertEqual(result["status"], UNBOUNDED)
        self.assertEqual(result["null_status"], "EXACT_NONZERO")
        self.assertGreater((m * result["ray"] * m.T)[0], 0)
        self.assertEqual(directional_support(s.zeros(1), u, covariance_class="unbounded_psd")["null_status"], EXACT_NULL)
        self.assertEqual(directional_support(s.zeros(1), u, covariance_class="unbounded_psd")["value"], 0)
        self.assertEqual(matrix_support(s.eye(2), -s.eye(2), covariance_class="unbounded_psd")["value"], 0)
        self.assertEqual(matrix_support(s.eye(2), s.eye(2), covariance_class="trace")["status"], ABSENT_BOUND)

    def test_seven_channel_gauge_is_not_a_left_null(self):
        m = s.Matrix.hstack(s.eye(5), s.zeros(5, 1), -s.ones(5, 1))
        a = s.eye(7)
        same(m * a * s.ones(7, 1), s.zeros(5, 1))
        self.assertEqual(m.rank(), 5)
        same(m[:, :6] * s.ones(6, 1), s.ones(5, 1))
        same(m[:, 6], -s.ones(5, 1))
        self.assertEqual(cone_membership(m, s.eye(5))["protected_output_dimension"], 0)

    def test_cross_block_retention_and_complete_psd(self):
        m = s.Matrix([[1, 1]])
        for rho, expected in ((-1, 0), (0, 2), (1, 4)):
            gamma = s.Matrix([[1, rho], [rho, 1]])
            result = joint_congruence(m, gamma, block_sizes=(1, 1),
                                      latent_units=("mag", "mag"), output_unit="mag",
                                      class_identity=f"synthetic-rho-{rho}")
            self.assertEqual(result["covariance"][0], expected)
            same(result["complete_Omega"], gamma)
        bad = s.ones(3) * s.Rational(-3, 4) + s.eye(3) * s.Rational(7, 4)
        self.assertEqual((bad * s.ones(3, 1))[0], -s.Rational(1, 2))
        with self.assertRaises(ValueError):
            joint_congruence(s.Matrix([[1, 1, 1]]), bad, block_sizes=(1, 1, 1),
                             latent_units=("mag",) * 3, output_unit="mag",
                             class_identity="pairwise-is-not-joint")

    def test_three_marginal_extremizers(self):
        maps = [s.eye(1)] * 3
        u = s.Matrix([1])
        for variances, lower, lower_coefficients in (
            ((1, 4, 9), 0, (1, 2, -3)),
            ((16, 1, 1), 4, (4, -1, -1)),
        ):
            marginals = [s.Matrix([[v]]) for v in variances]
            bounds = marginal_directional_bounds(maps, marginals, u)
            self.assertEqual(bounds["upper"], 36)
            self.assertEqual(bounds["lower"], lower)
            for coefficients, expected in ((tuple(s.sqrt(v) for v in variances), 36),
                                           (lower_coefficients, lower)):
                column = s.Matrix(coefficients)
                omega = column * column.T
                self.assertEqual(tuple(omega[i, i] for i in range(3)), variances)
                result = joint_congruence(s.Matrix([[1, 1, 1]]), omega,
                                          block_sizes=(1, 1, 1), latent_units=("mag",) * 3,
                                          output_unit="mag", class_identity="synthetic-marginal")
                self.assertEqual(result["covariance"][0], expected)

    def test_vector_marginals_have_no_common_pointwise_maximizer(self):
        c1, c2 = s.diag(1, 0), s.diag(0, 1)
        maps = [s.eye(2), s.eye(2)]
        for direction in (s.Matrix([1, 1]), s.Matrix([1, -1])):
            self.assertEqual(marginal_directional_bounds(maps, [c1, c2], direction)["upper"], 4)
        for rho, direction in ((1, s.Matrix([1, 1])), (-1, s.Matrix([1, -1]))):
            omega = s.zeros(4)
            omega[0, 0] = omega[3, 3] = 1
            omega[0, 3] = omega[3, 0] = rho
            result = joint_congruence(s.Matrix.hstack(*maps), omega,
                                      block_sizes=(2, 2), latent_units=("mag", "mag"),
                                      output_unit="mag", class_identity="synthetic-vector")
            self.assertEqual((direction.T * result["covariance"] * direction)[0], 4)
            other = s.Matrix([1, -direction[1]])
            self.assertEqual((other.T * result["covariance"] * other)[0], 0)

    def test_covariance_does_not_define_strict_tail(self):
        first = ((s.Integer(-1), s.Rational(1, 2)), (s.Integer(1), s.Rational(1, 2)))
        second = ((s.Integer(0), s.Rational(1, 2)),
                  (-s.sqrt(2), s.Rational(1, 4)), (s.sqrt(2), s.Rational(1, 4)))
        for law in (first, second):
            self.assertEqual(sum(x * p for x, p in law), 0)
            self.assertEqual(sum(x*x*p for x, p in law), 1)
        self.assertEqual(sum(p for x, p in first if abs(x) > 1), 0)
        self.assertEqual(sum(p for x, p in second if abs(x) > 1), s.Rational(1, 2))

    def test_floating_near_null_does_not_protect(self):
        result = floating_directional_diagnostic([[1e-12]], [1], covariance_class="unbounded_psd")
        self.assertEqual(result["status"], NEAR_NULL)
        self.assertTrue(math.isinf(result["upper"]))
        self.assertFalse(result["exact_protection_proved"])
        self.assertEqual(floating_directional_diagnostic([[0]], [1], covariance_class="unbounded_psd")["upper"], 0)
        self.assertEqual(floating_directional_diagnostic([[1]], [1], covariance_class="trace")["status"], ABSENT_BOUND)

    def test_missing_physical_response_and_undefined_exact_domain(self):
        self.assertEqual(physical_response_status(None), UNAVAILABLE_MAP)
        with self.assertRaisesRegex(ValueError, "UNDEFINED_INPUT_DOMAIN"):
            cone_membership(s.Matrix([[1.0]]), s.Matrix([[1]]))


if __name__ == "__main__":
    unittest.main()
