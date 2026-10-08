#!/usr/bin/env python3
"""Independent exact SymPy certificate for CAS-02-C04.

The algebraic equalities below are universal polynomial identities.  The
inequalities use the positive Euclidean Cauchy--Schwarz, Frobenius, triangle,
and induced operator-norm inequalities, with their hypotheses stated in the
single JSON output.  No numerical sample is used as a universal proof.
"""

import json
import sys

import sympy as sp


def zero(expr):
    return sp.expand(expr) == 0


def symmetric_matrix(tag):
    entries = {}
    for i in range(4):
        for j in range(i, 4):
            entries[i, j] = sp.Symbol(f"{tag}_{i}{j}", real=True)
    return sp.Matrix(4, 4, lambda i, j: entries[min(i, j), max(i, j)])


def frobenius_squared(matrix):
    return sum(entry * entry for entry in matrix)


def vector_squared(vector):
    return sum(entry * entry for entry in vector)


def embedding(h0, h1, h2):
    return sp.Matrix(4, 4, lambda i, j:
        h0 if i == j == 0 else
        -h1[j - 1] / 2 if i == 0 else
        -h1[i - 1] / 2 if j == 0 else
        h2[i - 1, j - 1])


def exact_case(name, s1_scale, s2_scale, d1, d2, r_sinh):
    """Ancillary exact boundary example, within the admitted optical embedding."""
    assert d1 >= 0 and d2 >= 0 and r_sinh >= max(d1, d2)
    s1 = sp.diag(s1_scale, 0, 0, 0)
    s2 = sp.diag(s2_scale, 0, 0, 0)
    u1 = sp.Matrix([sp.sqrt(1 + d1 * d1), d1, 0, 0])
    u2 = sp.Matrix([sp.sqrt(1 + d2 * d2), d2, 0, 0])
    g = sp.diag(-1, 1, 1, 1)
    b1 = s1 + (u1.T * s1 * u1)[0] * g
    b2 = s2 + (u2.T * s2 * u2)[0] * g
    lhs2 = sp.simplify(frobenius_squared(b2 - b1))
    eps_h2 = frobenius_squared(s2 - s1)
    eps_z2 = vector_squared(u2 - u1)
    # cosh(2 asinh(r_sinh)) = 1 + 2 r_sinh**2.
    m = sp.sqrt(1 + 2 * r_sinh * r_sinh)
    l = min(abs(s1_scale), abs(s2_scale))
    rhs = (1 + 2 * m * m) * sp.sqrt(eps_h2) + 4 * m * l * sp.sqrt(eps_z2)
    margin2 = sp.simplify(rhs * rhs - lhs2)
    assert rhs.is_nonnegative is True
    assert margin2.is_nonnegative is True, (name, margin2)
    return {
        "name": name,
        "d1": str(d1),
        "d2": str(d2),
        "sinh_R": str(r_sinh),
        "S1_op": str(abs(s1_scale)),
        "S2_op": str(abs(s2_scale)),
        "lhs_squared": str(lhs2),
        "rhs_squared_minus_lhs_squared": str(margin2),
        "exact_nonnegative": True,
    }


def main():
    assert sp.__version__ == "1.14.0", sp.__version__
    s1, s2 = symmetric_matrix("S1"), symmetric_matrix("S2")
    u1 = sp.Matrix(sp.symbols("u1_0:4", real=True))
    u2 = sp.Matrix(sp.symbols("u2_0:4", real=True))
    delta_s, delta_u = s2 - s1, u2 - u1
    q1, q2 = (u1.T * s1 * u1)[0], (u2.T * s2 * u2)[0]
    delta_q = q2 - q1
    anchor1 = (u2.T * delta_s * u2)[0] + (delta_u.T * s1 * (u2 + u1))[0]
    anchor2 = (u1.T * delta_s * u1)[0] + (delta_u.T * s2 * (u2 + u1))[0]
    assert zero(delta_q - anchor1)
    assert zero(delta_q - anchor2)
    assert zero(frobenius_squared(u2 * u2.T) - vector_squared(u2) ** 2)
    assert zero(frobenius_squared(u1 * u1.T) - vector_squared(u1) ** 2)

    g = sp.diag(-1, 1, 1, 1)
    b1, b2 = s1 + q1 * g, s2 + q2 * g
    assert b2 - b1 == delta_s + delta_q * g
    assert frobenius_squared(g) == 4

    h0 = sp.Symbol("h0", real=True)
    h1 = sp.Matrix(sp.symbols("h1_0:3", real=True))
    a, b, c, d, e = sp.symbols("a b c d e", real=True)
    h2 = sp.Matrix([[a, c, d], [c, b, e], [d, e, -a - b]])
    embedded = embedding(h0, h1, h2)
    assert embedded == embedded.T and sp.trace(h2) == 0
    assert zero(frobenius_squared(embedded) -
                (h0 ** 2 + vector_squared(h1) / 2 + frobenius_squared(h2)))

    x, y, z, R = sp.symbols("x y z R", real=True)
    dvec = sp.Matrix([x, y, z])
    d2 = vector_squared(dvec)
    chart = sp.Matrix([sp.sqrt(1 + d2), x, y, z])
    assert zero(vector_squared(chart) - (1 + 2 * d2))
    assert sp.simplify((chart.T * g * chart)[0] + 1) == 0
    assert sp.trigsimp(1 + 2 * sp.sinh(R) ** 2 - sp.cosh(2 * R)) == 0

    # Positive norms give |u_j| <= M from |d_j| <= sinh R.  The existence of
    # either admitted d_j forces sinh R >= 0, hence R >= 0 for real R.
    # Frobenius Cauchy: |u^T DeltaS u| <= |DeltaS|F |u u^T|F
    # = epsilonH |u|^2 <= M^2 epsilonH.
    # Operator Cauchy: |Delta_u^T S_anchor (u2+u1)|
    # <= |Delta_u| |S_anchor|op (|u2|+|u1|) <= 2 M L epsilonZ.
    # Exactly one of |S1|op <= |S2|op or |S2|op < |S1|op holds.  In the
    # first case choose anchor1, in the second choose anchor2; equality is
    # assigned to the first case.  Both identities were expanded above.
    # Since |g|F=2, triangle gives the contracted coefficient bound.
    M, eps_h, eps_z, L = sp.symbols("M epsilonH epsilonZ L", nonnegative=True)
    scalar_q_bound = M ** 2 * eps_h + 2 * M * L * eps_z
    derived = eps_h + 2 * scalar_q_bound
    target = (1 + 2 * M ** 2) * eps_h + 4 * M * L * eps_z
    assert zero(derived - target)

    cases = [
        exact_case("R=0_and_epsilonZ=0", sp.Integer(1), sp.Integer(2),
                   sp.Integer(0), sp.Integer(0), sp.Integer(0)),
        exact_case("S1_strictly_smaller", sp.Integer(1), sp.Integer(2),
                   sp.Integer(0), sp.Rational(3, 4), sp.Rational(3, 4)),
        exact_case("S2_strictly_smaller", sp.Integer(2), sp.Integer(1),
                   sp.Integer(0), sp.Rational(3, 4), sp.Rational(3, 4)),
        exact_case("epsilonH=0", sp.Integer(1), sp.Integer(1),
                   sp.Integer(0), sp.Rational(3, 4), sp.Rational(3, 4)),
        exact_case("epsilonZ=0_at_nonzero_d", sp.Integer(1), sp.Integer(2),
                   sp.Rational(3, 4), sp.Rational(3, 4), sp.Rational(3, 4)),
    ]
    payload = {
        "checks": {"CAS-02-C04": True},
        "domain_assumption_diff": [],
        "counterexample": None,
        "engine": {"python": sys.version.split()[0], "sympy": sp.__version__,
                   "sympy_file": sp.__file__},
        "exact_certificate": {
            "matrix_domain": "arbitrary real symmetric 4x4 S1,S2 and arbitrary real 4-vectors u1,u2; admitted optical embedding is a subset",
            "identities": [
                "delta_q = u2^T (S2-S1) u2 + (u2-u1)^T S1 (u2+u1)",
                "delta_q = u1^T (S2-S1) u1 + (u2-u1)^T S2 (u2+u1)",
                "B2-B1 = (S2-S1) + delta_q g",
                "||u u^T||F = ||u||2^2 for real u",
                "||g||F=2",
                "||u(d)||2^2=1+2||d||2^2 and g(u(d),u(d))=-1",
                "1+2 sinh(R)^2=cosh(2R)",
                "||S(h0,h1,h2)||F^2=h0^2+||h1||2^2/2+||h2||F^2",
                "epsilonH+2(M^2 epsilonH+2 M L epsilonZ)=(1+2M^2)epsilonH+4 M L epsilonZ",
            ],
            "inequality_lemmas": [
                "For an admitted pair, 0<=||d||<=sinh R implies R>=0; positive roots give ||u_j||2<=M=sqrt(cosh 2R).",
                "Positive Frobenius Cauchy gives |u^T DeltaS u|<=||DeltaS||F ||u u^T||F<=M^2 epsilonH.",
                "Positive induced operator Cauchy gives |Delta_u^T S_j (u2+u1)|<=epsilonZ ||S_j||op (||u2||+||u1||)<=2 M L epsilonZ when j realizes L.",
                "Exhaustive disjoint cases: ||S1||op<=||S2||op uses first identity; ||S2||op<||S1||op uses second. Equal norms enter the first case.",
                "Positive Frobenius triangle gives ||DeltaB||F<=epsilonH+||g||F |delta_q|=epsilonH+2|delta_q|.",
            ],
            "scope": "finite CAS-02-C04 only; no projection, global extension, statistical or physical claim",
        },
        "exact_boundary_cases": cases,
        "scientific_admission": "HOLD",
    }
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
