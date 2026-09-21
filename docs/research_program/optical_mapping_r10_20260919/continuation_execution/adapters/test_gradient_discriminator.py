"""Exact finite convention discriminator; Host diagnostic, not a CAS axis.

P1=x and S=diag(1,-1,0). Homogenize sphere polynomials to degree 3,
then remove their traces using H3(f)=f-r^2 Laplacian(f)/10.
The general-ell theorem and engine-independent proofs remain outstanding.
"""
from fractions import Fraction as Q
import unittest


def add(*polynomials):
    result = {}
    for polynomial in polynomials:
        for power, coefficient in polynomial.items():
            result[power] = result.get(power, Q(0)) + coefficient
    return {power: coefficient for power, coefficient in result.items() if coefficient}


def scale(polynomial, coefficient):
    return {power: Q(coefficient) * value for power, value in polynomial.items() if value * coefficient}


def multiply(left, right):
    return add(*[
        {tuple(a + b for a, b in zip(p, q)): c * d}
        for p, c in left.items() for q, d in right.items()
    ])


def derivative(polynomial, axis):
    result = {}
    for powers, coefficient in polynomial.items():
        if powers[axis]:
            reduced = list(powers)
            reduced[axis] -= 1
            result[tuple(reduced)] = coefficient * powers[axis]
    return result


def laplacian(polynomial):
    return add(*(derivative(derivative(polynomial, axis), axis) for axis in range(3)))


X, Y, Z = ({powers: Q(1)} for powers in [(1, 0, 0), (0, 1, 0), (0, 0, 1)])
R2 = add(*(multiply(v, v) for v in (X, Y, Z)))
S_E = (X, scale(Y, -1), {})
S_E_E = add(multiply(X, X), scale(multiply(Y, Y), -1))


def dot(left, right):
    return add(*(multiply(a, b) for a, b in zip(left, right)))


def upper_harmonic(cubic):
    return add(cubic, scale(multiply(R2, laplacian(cubic)), Q(-1, 10)))


class GradientConventionTest(unittest.TestCase):
    def test_ambient_and_tangent_generators_agree(self):
        ambient = tuple(derivative(X, axis) for axis in range(3))
        euler = dot((X, Y, Z), ambient)
        self.assertEqual(euler, X)
        # r^2 grad(P1)-e P1 restricts to grad_S2(P1) on the unit sphere.
        tangent_cubic = dot(S_E, tuple(
            add(multiply(R2, d), scale(multiply(e, euler), -1))
            for e, d in zip((X, Y, Z), ambient)
        ))
        shear_product = multiply(S_E_E, X)
        ambient_generator = add(multiply(R2, dot(S_E, ambient)), scale(shear_product, -5))
        tangent_generator = add(tangent_cubic, scale(shear_product, -4))
        wrong_generator = add(tangent_cubic, scale(shear_product, -5))
        self.assertEqual(ambient_generator, tangent_generator)
        reference = upper_harmonic(shear_product)
        self.assertTrue(reference)
        self.assertEqual(laplacian(reference), {})
        self.assertEqual(upper_harmonic(ambient_generator), scale(reference, -5))
        self.assertEqual(upper_harmonic(wrong_generator), scale(reference, -6))
        self.assertNotEqual(upper_harmonic(wrong_generator), scale(reference, -5))

    def test_trace_removal_defines_a_nonzero_rank_three_reference(self):
        cubic = multiply(S_E_E, X)
        self.assertEqual(laplacian(cubic), scale(X, 4))
        self.assertEqual(laplacian(multiply(R2, X)), scale(X, 10))
        expected = add(cubic, scale(multiply(R2, X), Q(-2, 5)))
        self.assertEqual(upper_harmonic(cubic), expected)
        self.assertEqual(expected[(3, 0, 0)], Q(3, 5))


if __name__ == "__main__":
    unittest.main()
