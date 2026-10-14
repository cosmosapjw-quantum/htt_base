"""Independent exact Sage calculus for CAS-07-C01."""
import json
from sage.all import assume, diff, exp, integrate, limit, sinh, sqrt, var
from sage.version import version as sage_version

K = var("K", domain="positive")
s = var("s", domain="real")
t = var("t", domain="real")
# Maxima's definite-integral backend requires a strict sign decision.
# The endpoint s=0 is checked separately below.
assume(s > 0)
f = sinh(sqrt(K) * s) / sqrt(K)
ft = sinh(sqrt(K) * t) / sqrt(K)

def is_zero(expr):
    # Convert sinh by its exact exponential definition before canonicalizing.
    normalized = expr.subs({sinh(sqrt(K) * s):
                            (exp(sqrt(K) * s) - exp(-sqrt(K) * s)) / 2})
    return bool(normalized.simplify_full() == 0)

initial_f = f.subs({s: 0})
first = diff(f, s)
initial_first = first.subs({s: 0})
second = diff(f, s, 2)
actual_integral = integrate((s - t) * ft, t, 0, s)
right_limit = limit(f, K=0, dir="+")
f0 = s
f0_t = f0.subs({s: t})
actual_flat_integral = integrate((s - t) * f0_t, t, 0, s)

checks = {
    "initial_f_zero": is_zero(initial_f),
    "initial_derivative_one": is_zero(initial_first - 1),
    "ode_all_positive_K_nonnegative_s": is_zero(second - K * f),
    "actual_interval_integral": is_zero(K * actual_integral - (f - s)),
    "interval_integral_at_s_zero": is_zero(
        K * integrate((0 - t) * ft, t, 0, 0) - (f.subs({s: 0}) - 0)
    ),
    "fixed_s_right_limit": is_zero(right_limit - f0),
    "flat_initial_f_zero": is_zero(f0.subs({s: 0})),
    "flat_initial_derivative_one": is_zero(diff(f0, s).subs({s: 0}) - 1),
    "flat_second_derivative_zero": is_zero(diff(f0, s, 2)),
    "flat_integral_unscaled_value": is_zero(actual_flat_integral - s**3 / 6),
    "flat_integral_identity": is_zero(0 * actual_flat_integral - (f0 - s)),
}
integral_residual = K * actual_integral - (f - s)
normalized_integral_residual = integral_residual.subs({
    sinh(sqrt(K) * s): (exp(sqrt(K) * s) - exp(-sqrt(K) * s)) / 2
}).simplify_full()
print(json.dumps({
    "sage_version": sage_version,
    "domain": "real K>0, real s>=0, t in [0,s]; positive square root; K=0 handled separately",
    "expressions": {
        "f": str(f), "first": str(first), "second": str(second),
        "actual_integral": str(actual_integral),
        "integral_residual": str(normalized_integral_residual),
        "integral_residual_before_exp_normalization": str(integral_residual.simplify_full()),
        "right_limit": str(right_limit),
        "flat_f": str(f0),
        "flat_integrand": str((s - t) * f0_t),
        "actual_flat_integral_unscaled": str(actual_flat_integral),
        "flat_integral_residual": str((0 * actual_flat_integral - (f0 - s)).simplify_full()),
    },
    "checks": checks,
}, sort_keys=True))
if not all(checks.values()):
    raise SystemExit(2)
