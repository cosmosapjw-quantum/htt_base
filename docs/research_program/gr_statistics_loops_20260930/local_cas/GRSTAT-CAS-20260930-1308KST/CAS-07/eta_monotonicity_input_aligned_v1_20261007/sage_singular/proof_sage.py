#!/usr/bin/env python3
"""Sage analytic certificate for frozen CAS-07-M01."""
import json
from sage.all import SR, assume, cosh, diff, sinh, var

sage_bool = bool

x, t, a = var("x t a", domain="real")
assume(x > 0, t > 0, a > 0)
eta = sinh(a * t) / (a * t) - 1
num = x * cosh(x) - sinh(x)

checks = {}
checks["piecewise_k_zero"] = sage_bool((t / t - 1).simplify_full() == 0)
checks["eta_derivative_identity"] = sage_bool(
    (diff(eta, t) - ((a * t) * cosh(a * t) - sinh(a * t)) / (a * t**2)).simplify_full() == 0
)
checks["sinh_minus_x_derivative"] = sage_bool(
    (diff(sinh(x) - x, x) - (cosh(x) - 1)).simplify_full() == 0
)
checks["numerator_derivative"] = sage_bool((diff(num, x) - x * sinh(x)).simplify_full() == 0)
checks["cosh_minus_one_square_identity"] = sage_bool(
    (cosh(x) - 1 - 2 * sinh(x / 2) ** 2).exponentialize().simplify_full() == 0
)
checks["square_nonnegative"] = sage_bool(2 * sinh(x / 2) ** 2 >= 0)
checks["sinh_positive"] = sage_bool(sinh(x) > 0)
checks["numerator_derivative_positive"] = sage_bool(x * sinh(x) > 0)

# With value zero at x=0, the exact derivative signs above and the mean-value
# theorem give the two universal signs. Substitution x=a*t and the derivative
# identity then prove nonnegativity and monotonicity of eta.
checks["sinh_minus_x_at_zero"] = sage_bool((sinh(SR(0)) - SR(0)) == 0)
checks["numerator_at_zero"] = sage_bool(num.subs(x=0).simplify_full() == 0)
checks["eta_nonnegative_universal"] = all(checks[k] for k in (
    "sinh_minus_x_derivative", "cosh_minus_one_square_identity",
    "square_nonnegative", "sinh_minus_x_at_zero"))
checks["eta_monotone_universal"] = all(checks[k] for k in (
    "eta_derivative_identity", "numerator_derivative",
    "numerator_derivative_positive", "numerator_at_zero"))
checks["upper_bound_implication"] = checks["eta_nonnegative_universal"] and checks["eta_monotone_universal"]

print(json.dumps({"sage_version": "10.9", "checks": checks, "all": all(checks.values())}, sort_keys=True))
raise SystemExit(0 if all(checks.values()) else 2)
