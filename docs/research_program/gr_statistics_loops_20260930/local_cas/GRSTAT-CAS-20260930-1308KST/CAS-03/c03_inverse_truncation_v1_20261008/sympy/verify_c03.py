#!/usr/bin/env python3
"""Independent exact SymPy check of CAS-03-C03's finite matrix component."""

import json
import sys

import sympy as sp


def is_zero_matrix(matrix):
    return all(sp.cancel(entry) == 0 for entry in matrix)


def require(name, condition):
    print(f"{name}: {'PASS' if condition else 'FAIL'}", flush=True)
    if not condition:
        raise AssertionError(name)


def main():
    print(f"python={sys.version}", flush=True)
    print(f"sympy={sp.__version__}", flush=True)
    print(f"sympy_file={sp.__file__}", flush=True)

    d = sp.symbols("d0:9", real=True)
    b = sp.symbols("b0:3", real=True)
    D = sp.Matrix(3, 3, d)
    beta = sp.Matrix(b)
    I = sp.eye(3)
    H = sp.trace(D) / 3
    sigma = D - H * I
    h1 = -2 * D * beta
    determinant = D.det()

    require("trace_split", sp.cancel(sp.trace(sigma)) == 0)
    require("adjugate_inverse_identity", is_zero_matrix(D.adjugate() * D - determinant * I))
    # On det(D) != 0 the adjugate identity permits division by det(D).
    beta_exact = -D.adjugate() * h1 / (2 * determinant)
    require("exact_inverse_all_invertible_D", is_zero_matrix(beta_exact - beta))

    # H is divided out only on H != 0. Matrix multiplication keeps its order.
    beta_trunc = -(I - sigma / H) * h1 / (2 * H)
    defect = sigma * sigma * beta / H**2
    require("truncation_defect_H_nonzero", is_zero_matrix(beta - beta_trunc - defect))
    require(
        "factorized_defect_identity_H_nonzero",
        is_zero_matrix(I - (I - sigma / H) * (D / H) - sigma * sigma / H**2),
    )

    D0 = sp.diag(1, 1, -2)
    H0 = sp.trace(D0) / 3
    beta0 = sp.Matrix(b)
    h10 = -2 * D0 * beta0
    exact0 = -D0.inv() * h10 / 2
    require("H_zero_control", H0 == 0 and D0.det() == -2 and is_zero_matrix(exact0 - beta0))
    print("H_zero_truncation=undefined (division by H)", flush=True)

    epsilon = sp.symbols("epsilon", real=True)
    Dr = sp.diag(6, 3, 3)
    Hr = sp.trace(Dr) / 3
    sigmar = Dr - Hr * I
    betar = sp.Matrix([epsilon, 0, 0])
    h1r = -2 * Dr * betar
    trunc_r = -(I - sigmar / Hr) * h1r / (2 * Hr)
    defect_r = sigmar * sigmar * betar / Hr**2
    require(
        "rational_diagonal_control",
        Hr == 4
        and Dr / Hr == sp.diag(sp.Rational(3, 2), sp.Rational(3, 4), sp.Rational(3, 4))
        and sigmar / Hr == sp.diag(sp.Rational(1, 2), -sp.Rational(1, 4), -sp.Rational(1, 4))
        and trunc_r == sp.Matrix([3 * epsilon / 4, 0, 0])
        and defect_r == sp.Matrix([epsilon / 4, 0, 0])
        and betar - trunc_r == defect_r,
    )
    print(json.dumps({"component": "CAS-03-C03", "status": "PASS", "exact": True}), flush=True)


if __name__ == "__main__":
    main()
