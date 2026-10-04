"""Independent Sage differentiation of the contracted positive-real scalar power."""

import json

from sage.all import diff, exp, log, var
from sage.version import version as sage_version


X, Pstar, s, alpha = var("X Pstar s alpha")
P = Pstar * exp(s * log(X))  # X > 0 fixes the real logarithm branch.
first = diff(P, X)
second = diff(first, X)
energy = 2 * X * first - P
denominator = first + 2 * X * second
exponent = (1 + alpha) / (2 * alpha)


def zero(expression):
    return expression.simplify_full().is_zero()


checks = {
    "first_from_differentiation": zero(first - Pstar * s * X ** (s - 1)),
    "second_from_differentiation": zero(second - Pstar * s * (s - 1) * X ** (s - 2)),
    "energy_identity": zero(energy - (2 * s - 1) * P),
    "denominator_factorization": zero(
        denominator - Pstar * s * (2 * s - 1) * X ** (s - 1)
    ),
    "exponent_relation": zero((2 * s - 1).subs(s=exponent) - 1 / alpha),
    "ratio_identity": zero((first / denominator).subs(s=exponent) - alpha),
}

print(json.dumps({
    "sage_version": sage_version,
    "branch": "Pstar*exp(s*log(X)), X>0",
    "first": str(first),
    "second": str(second),
    "energy": str(energy),
    "denominator": str(denominator),
    "checks": checks,
}, sort_keys=True))
if not all(checks.values()):
    raise SystemExit(1)
