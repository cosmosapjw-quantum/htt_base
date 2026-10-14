"""Sage-only exact coefficient checks, called by the stdlib axis wrapper."""

import json
import sys

from sage.all import QQ, PolynomialRing, PowerSeriesRing, factorial
from sage.version import version as sage_version


K_ring = PolynomialRing(QQ, "k")
k = K_ring.gen()
R = PolynomialRing(K_ring, "x")
x = R.gen()


def T(poly):
    # Exact action of K integral_0^x (x-t) t^m dt on each monomial.
    return sum((c * k * x ** (m + 2) / ((m + 1) * (m + 2))
                for m, c in enumerate(poly.list())), R.zero())


def main():
    term = x
    seed_residuals = []
    for n in range(17):
        expected = k ** n * x ** (2 * n + 1) / factorial(2 * n + 1)
        residual = term - expected
        seed_residuals.append(str(residual))
        if residual != 0:
            raise AssertionError(f"seed coefficient n={n}: {residual}")
        term = T(term)

    S = PowerSeriesRing(QQ, "z", default_prec=37)
    z = S.gen()
    sinh_coefficients = [z.sinh()[2 * n + 1] for n in range(17)]
    for n, coeff in enumerate(sinh_coefficients):
        if coeff != 1 / factorial(2 * n + 1):
            raise AssertionError(f"sinh coefficient n={n}: {coeff}")

    remainder_coefficients = []
    for n in range(1, 17):
        coeff = QQ(1) / factorial(2 * n - 1) / (2 * n)
        remainder_coefficients.append(str(coeff))
        if coeff != 1 / factorial(2 * n):
            raise AssertionError(f"remainder coefficient n={n}")

    print(json.dumps({
        "ok": True,
        "sage_version": sage_version,
        "python_executable": sys.executable,
        "seed_residuals_n0_16": seed_residuals,
        "sinh_coefficients_n0_16": [str(c) for c in sinh_coefficients],
        "remainder_coefficients_n1_16": remainder_coefficients,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
