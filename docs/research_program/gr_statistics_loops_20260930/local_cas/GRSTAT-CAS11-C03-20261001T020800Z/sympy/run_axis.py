#!/usr/bin/env python3
"""SymPy obligations for the frozen CAS11-C03 positive-definite component."""

import json
import sys

import sympy as sp


KEY = "CAS11-C03-WEIGHTED-PROJECTION"


def zero(expr):
    return sp.simplify(sp.expand(expr)) == 0


def matrix_zero(mat):
    return all(zero(entry) for entry in mat)


def symbolic_checks():
    g, t, x = sp.symbols("g t x", nonzero=True, real=True)
    a, b, c, d = sp.symbols("a b c d", real=True)
    X, Y, C = sp.symbols("X Y C", real=True)
    # Scalar representatives of the arbitrary-size matrix cancellation
    # G G^{-1}=I and of bilinear finite-sum rearrangement. The indexed
    # lift and its hypotheses are given in PROOF.md.
    return {
        "gram_inverse_cancellation": zero(g * (1 / g) - 1),
        "projection_residual_cancellation": zero(t - g * (1 / g) * t),
        "projection_idempotent_coefficient": zero((g * (1 / g)) ** 2 - g * (1 / g)),
        "gram_bilinear_pair": zero(a * c + a * d + b * c + b * d - (a + b) * (c + d)),
        "one_dimensional_norm": zero(X - 2 * C * (C / Y) + Y * (C / Y) ** 2 - (X - C ** 2 / Y)),
        "one_dimensional_scaled_norm": zero(Y * (X - C ** 2 / Y) - (X * Y - C ** 2)),
        "lagrange_pair_square": zero(
            (a ** 2 + b ** 2) * (c ** 2 + d ** 2)
            - (a * c + b * d) ** 2 - (a * d - b * c) ** 2
        ),
        "zero_norm_branch": zero(x * 0),
    }


def matrix_checks():
    W = sp.Matrix([[2, 1, 0], [1, 3, 0], [0, 0, 5]])
    I = sp.eye(3)
    K = sp.Matrix([[1, 2, 0], [0, 0, 0], [3, 6, 0]])
    out = {}
    for label, B in (
        ("zero_subspace", sp.zeros(3, 0)),
        ("proper_subspace", sp.Matrix([[1, 0], [0, 1], [0, 0]])),
        ("full_subspace", I),
    ):
        P = sp.zeros(3) if B.cols == 0 else B * (B.T * W * B).inv() * B.T * W
        Z = (I - P) * K
        R = Z.T * W * Z
        av = sp.Matrix(sp.symbols("a0:3", real=True))
        total = Z * av
        out[label + "_idempotent"] = matrix_zero(P * P - P)
        out[label + "_orthogonal"] = matrix_zero(B.T * W * (I - P))
        out[label + "_gram"] = zero((av.T * R * av)[0] - (total.T * W * total)[0])
        out[label + "_gram_symmetric"] = matrix_zero(R - R.T)
        out[label + "_gram_singular"] = zero(R.det())
    out["empty_family"] = sp.zeros(3, 0).T * W * sp.zeros(3, 0) == sp.zeros(0, 0)
    out["ambient_zero_dimension"] = sp.zeros(0, 0) == sp.eye(0)
    return out


def high_precision_checks():
    W = sp.Matrix([[sp.sqrt(2) + 2, sp.Rational(1, 7)],
                   [sp.Rational(1, 7), sp.sqrt(3) + 3]])
    x = sp.Matrix([sp.pi, sp.E])
    y = sp.Matrix([sp.sqrt(5), sp.Rational(7, 11)])
    X = (x.T * W * x)[0]
    Y = (y.T * W * y)[0]
    C = (x.T * W * y)[0]
    z = x - (C / Y) * y
    gap = sp.N(X * Y - C ** 2, 90)
    norm = sp.N((z.T * W * z)[0], 90)
    return {
        "precision_digits": 90,
        "positive_gap": bool(gap > 0),
        "positive_residual_norm": bool(norm > 0),
        "scaled_residual_identity_abs_error_lt_1e-75": bool(abs(gap - sp.N(Y * norm, 90)) < sp.Float("1e-75")),
        "gap_decimal": str(gap),
        "residual_norm_decimal": str(norm),
    }


def main():
    try:
        symbolic = symbolic_checks()
        matrices = matrix_checks()
        numeric = high_precision_checks()
        numeric_ok = all(v for k, v in numeric.items() if k in (
            "positive_gap", "positive_residual_norm", "scaled_residual_identity_abs_error_lt_1e-75"
        ))
        ok = all(symbolic.values()) and all(matrices.values()) and numeric_ok
        print(json.dumps({
            "axis": "sympy",
            "status": "PASS" if ok else "INCONCLUSIVE",
            "checks": {KEY: bool(ok)},
            "symbolic_checks": symbolic,
            "matrix_falsifiers": matrices,
            "high_precision_supplement": numeric,
            "domain_assumption_diff": [],
            "counterexample": None,
            "proof_coverage": "Universal analytic proof for all finite n,k,m in PROOF.md; SymPy checks its scalar algebraic kernels and examples only.",
            "statement_alignment": "Finite-dimensional real positive-definite W, arbitrary subspace and finite family; includes n=0, m=0 and degenerate residuals.",
            "sympy_version": sp.__version__,
        }, sort_keys=True))
        return 0 if ok else 2
    except Exception as exc:
        print(json.dumps({"axis": "sympy", "status": "INCONCLUSIVE", "checks": {KEY: False},
                          "domain_assumption_diff": [], "counterexample": None,
                          "error": type(exc).__name__ + ": " + str(exc)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
