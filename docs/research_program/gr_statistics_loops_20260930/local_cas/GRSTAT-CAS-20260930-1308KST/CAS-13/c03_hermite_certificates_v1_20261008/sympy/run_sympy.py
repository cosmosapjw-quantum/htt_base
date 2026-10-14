#!/usr/bin/env python3
"""Independent CAS-13-C03 finite Hermite certificate, SymPy axis."""

import argparse
import hashlib
import json
from pathlib import Path

import sympy as sp


EXPECTED = {
    "contract": "d9b1e59d9e8648e74db64bdf9e7ef82d23e409c9456a5f307fb30dabb0e8e21e",
    "inputs": "916055a8eff4787ff56bd4e7629cef837333890a9dc5c1a9e8a33aa82c1665b4",
    "teff": "bc055d391d3231c634a14e146f228d3b8179a043485c41ce08754cdeac4fd0fe",
    "common": "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def positive_coefficients(expr, variables):
    """Sufficient ordered-positive-cone certificate for a polynomial."""
    poly = sp.Poly(sp.expand(expr), *variables, domain=sp.QQ)
    assert poly.terms() and all(coefficient > 0 for _, coefficient in poly.terms())
    return {str(monomial): str(coefficient) for monomial, coefficient in poly.terms()}


def main():
    parser = argparse.ArgumentParser()
    for name in EXPECTED:
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    assert sp.__version__ == "1.14.0", sp.__version__
    paths = {name: getattr(args, name) for name in EXPECTED}
    assert all(sha256(paths[name]) == digest for name, digest in EXPECTED.items())
    assert args.evidence.resolve().parent == Path(__file__).resolve().parent

    contract = json.loads(paths["contract"].read_text())
    admitted = json.loads(paths["inputs"].read_text())
    assert contract["identity"]["contract_id"] == "GRSTAT-20260930-CAS-13-C03-HERMITE-V1"
    assert contract["semantics"]["symbol_type_domain_map"] == admitted["domain"]
    assert contract["semantics"]["exact_statement"] == admitted["target"]
    assert contract["target"]["numeric_precision_digits"] == 80
    assert contract["target"]["exact_test_obligations"] == ["CAS-13-C03"]

    A, U, y = sp.symbols("A U y", real=True)
    c0, c3, c4 = sp.symbols("c0 c3 c4")
    delta = 3*A**2 + 2*A*U + U**2
    matrix = sp.Matrix([[1, A**3, A**4], [1, U**3, U**4], [0, 3*U**2, 4*U**3]])
    determinant = sp.factor(matrix.det())
    assert sp.expand(determinant - U**2*(A-U)**2*delta) == 0
    positive_coefficients(delta, (A, U))
    # The interior solve uses A,U>0 and A!=U. The boundary is specialized later.
    target_locals = {"A": A, "U": U, "y": y, "Delta": delta}
    evidence = {
        "engine": "SymPy",
        "version": sp.__version__,
        "input_sha256": {name: sha256(path) for name, path in paths.items()},
        "assumptions": ["A>0", "U>0", "A!=U for interpolation solve", "y>=0", "lower: A=a<U=u<=b and a<=y<=b", "upper: 0<U=d<A=b and a<=y<=b"],
        "determinant": str(determinant),
        "delta_positive_monomials": positive_coefficients(delta, (A, U)),
        "powers": {},
    }

    for p in (5, 6):
        rhs = sp.Matrix([A**p, U**p, p*U**(p-1)])
        solved = [sp.cancel(value) for value in matrix.inv()*rhs]
        Q = sp.cancel(solved[0] + solved[1]*y**3 + solved[2]*y**4)
        assert sp.cancel(Q.subs(y, A) - A**p) == 0
        assert sp.cancel(Q.subs(y, U) - U**p) == 0
        assert sp.cancel(sp.diff(Q, y).subs(y, U) - p*U**(p-1)) == 0

        numerator = sp.cancel(delta*(y**p-Q))
        assert sp.denom(numerator) == 1
        quotient, remainder = sp.div(sp.Poly(numerator, y), sp.Poly((y-A)*(y-U)**2, y))
        assert remainder.is_zero
        P = sp.expand(quotient.as_expr())
        target = sp.sympify(admitted["target"][f"P{p}"], locals=target_locals)
        assert sp.expand(P-target) == 0
        assert sp.cancel(y**p-Q-(y-A)*(y-U)**2*P/delta) == 0
        assert sp.degree(P, y) == p-3

        y_coeffs = sp.Poly(P, y).all_coeffs()
        positivity = [positive_coefficients(coeff, (A, U)) for coeff in y_coeffs]
        # P>0 for A,U,y>0. Delta>0. Thus the defect has sign(y-A).
        assert sp.cancel((y**p-Q).subs(y, A)) == 0
        assert sp.cancel((y**p-Q).subs(y, U)) == 0

        w = sp.symbols("w", real=True)
        m3_pair = (1-w)*A**3 + w*U**3
        m4_pair = (1-w)*A**4 + w*U**4
        affine_expectation = sp.cancel(solved[0] + solved[1]*m3_pair + solved[2]*m4_pair)
        pair_moment = (1-w)*A**p + w*U**p
        assert sp.cancel(affine_expectation-pair_moment) == 0
        # For any normalized measure with these m3,m4, linearity gives the same
        # affine expectation. Pair attainment is conditional on admitted weights.

        t = sp.symbols("t", positive=True)
        Q_boundary = sp.cancel(Q.subs({A: t, U: t}))
        P_boundary = sp.expand(P.subs({A: t, U: t}))
        delta_boundary = sp.expand(delta.subs({A: t, U: t}))
        assert delta_boundary == 6*t**2
        assert sp.cancel(y**p-Q_boundary-(y-t)**3*P_boundary/delta_boundary) == 0
        boundary_positive = [positive_coefficients(coeff, (t,)) for coeff in sp.Poly(P_boundary, y).all_coeffs()]

        numeric = []
        for node_A, node_U in ((1, 2), (3, 2)):
            for yy in (sp.Rational(1), sp.Rational(3, 2), sp.Rational(2), sp.Rational(5, 2), sp.Rational(3)):
                if node_A == 1 and not 1 <= yy <= 3:
                    continue
                subs = {A: node_A, U: node_U, y: yy}
                direct = sp.N((y**p-Q).subs(subs), 80)
                factored = sp.N(((y-A)*(y-U)**2*P/delta).subs(subs), 80)
                error = abs(direct-factored)
                scale = max(sp.Float(1, 80), abs(direct), abs(factored))
                assert error <= sp.Float("1e-50", 80) + sp.Float("1e-40", 80)*scale
                if node_A == 1:
                    assert direct >= 0
                else:
                    assert direct <= 0
                numeric.append({"A": node_A, "U": node_U, "y": str(yy), "defect_80d": str(direct), "factor_80d": str(factored), "abs_error_80d": str(error)})

        evidence["powers"][str(p)] = {
            "coefficients": {"c0": str(solved[0]), "c3": str(solved[1]), "c4": str(solved[2])},
            "P_from_polynomial_division": str(P),
            "P_coefficient_positive_monomials": positivity,
            "interpolation_exact": True,
            "SE3_SE4_SE5_exact": True,
            "lower_upper_sign_from_factorization": True,
            "conditional_pair_moment_identity_exact": True,
            "boundary_polynomial_specialization": {"Q": str(Q_boundary), "P": str(P_boundary), "delta": str(delta_boundary), "positive_monomials": boundary_positive},
            "numeric_80_digit_controls": numeric,
        }

    args.evidence.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": {"CAS-13-C03": True}, "domain_assumption_diff": [], "counterexample": None}, separators=(",", ":")))


if __name__ == "__main__":
    main()
