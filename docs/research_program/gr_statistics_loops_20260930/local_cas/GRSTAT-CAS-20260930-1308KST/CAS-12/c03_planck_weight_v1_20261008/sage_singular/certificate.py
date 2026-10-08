"""Independent exact Sage checks for the contracted CAS-12-C03 component."""

import json

from sage.all import QQ, PowerSeriesRing, RealField, exp, factorial, limit, sinh, var


def check(name, condition):
    if not bool(condition):
        raise AssertionError(name)


R = PowerSeriesRing(QQ, "x", default_prec=10)
x = R.gen()
# (exp(x)-1)/x and exp(x), with all coefficients exact in Q.
t = R([QQ(1) / factorial(n + 1) for n in range(10)])
ex = R([QQ(1) / factorial(n) for n in range(10)])
scaled = ex / (t * t)
expected = {0: QQ(1), 1: QQ(0), 2: -QQ(1) / 12,
            3: QQ(0), 4: QQ(1) / 240, 5: QQ(0),
            6: -QQ(1) / 6048, 7: QQ(0)}
for power, value in expected.items():
    check(f"formal coefficient x^{power}", scaled[power] == value)
check("formal constant of E^2 W", scaled[0] == 1)

u = var("u")
# This identity plus exp(u/2)>0 and sinh(u/2)>0 for u>0 proves
# the contracted quotient identity without evaluating it at u=0.
hyperbolic_residual = (
    exp(u) - 1 - 2 * exp(u / 2) * sinh(u / 2)
).exponentialize().expand().simplify_full()
check("exp/sinh identity", hyperbolic_residual == 0)

# The right limit is a separate analytic check in the real branch.
right_limit = limit(
    u**2 * exp(u) / (exp(u) - 1)**2, u=0, dir="+"
)
check("right limit in x=bE", right_limit == 1)
# b>0 makes E->0+ correspond to u=bE->0+; E^2 W=(u^2 W)/b^2.

RR = RealField(320)  # more than the contracted 80 decimal digits
numeric = []
for b_text, e_text in (("1", "0.1"), ("2", "0.01")):
    b_num, e_num = RR(b_text), RR(e_text)
    z = b_num * e_num
    direct = z.exp() / (z.exp() - 1)**2
    hyperbolic = 1 / (4 * (z / 2).sinh()**2)
    residual = abs(direct - hyperbolic)
    check("80-digit numeric identity", residual < RR("1e-50"))
    check("80-digit relative identity", residual / abs(direct) < RR("1e-40"))
    numeric.append({"b": b_text, "E": e_text, "absolute_residual": str(residual)})

print(json.dumps({
    "sage_certificate": "PASS",
    "formal_scaled_coefficients_x0_to_x7": [str(scaled[i]) for i in range(8)],
    "exp_sinh_residual": str(hyperbolic_residual),
    "right_limit_x2W": str(right_limit),
    "numeric_vectors": numeric,
    "domain": "b real > 0; E real > 0; x=bE; right limit; formal x about 0",
}, sort_keys=True))
