from sage.all import RealField, SR, assume, diff, exp, log, var


p, y = var("p y")
assume(p > 4)
assume(y > 0)

c0 = (p - 3) * (p - 4) / 12
c3 = p * (4 - p) / 3
c4 = p * (p - 3) / 4
q = c0 + c3 * y**3 + c4 * y**4
psi = exp(p * log(y))


def exact_zero(name, value):
    simplified = SR(value).simplify_full()
    print(f"{name}={simplified}")
    if simplified != 0:
        raise AssertionError(f"{name} is nonzero: {simplified}")


exact_zero("power_first", diff(psi, y) - p * exp((p - 1) * log(y)))
exact_zero("power_second", diff(psi, y, 2) - p * (p - 1) * exp((p - 2) * log(y)))
exact_zero("power_third", diff(psi, y, 3) - p * (p - 1) * (p - 2) * exp((p - 3) * log(y)))

exact_zero("jet_value", q.subs({y: 1}) - psi.subs({y: 1}))
exact_zero("jet_first", diff(q, y).subs({y: 1}) - diff(psi, y).subs({y: 1}))
exact_zero("jet_second", diff(q, y, 2).subs({y: 1}) - diff(psi, y, 2).subs({y: 1}))

q3_target = 2 * p * (4 - p) + 6 * p * (p - 3) * y
exact_zero("q_third", diff(q, y, 3) - q3_target)

mismatch = diff(psi, y, 3) - diff(q, y, 3)
mismatch_target = p * (p - 1) * (p - 2) * exp((p - 3) * log(y)) - q3_target
exact_zero("third_mismatch", mismatch - mismatch_target)
exact_zero("unit_factor", mismatch.subs({y: 1}) - p * (p - 3) * (p - 4))

# On the declared domain every factor of p(p-3)(p-4) is positive.
assert 5 * (5 - 3) * (5 - 4) > 0

R = RealField(320)
for pv, yv in ((5, R(4) / 5), (6, R(6) / 5), (R(9) / 2, R(9) / 10)):
    observed = R(mismatch.subs({p: pv, y: yv}))
    expected = R(mismatch_target.subs({p: pv, y: yv}))
    error = abs(observed - expected)
    bound = R("1e-50") + R("1e-40") * max(abs(observed), abs(expected))
    print(f"numeric p={pv} y={yv} observed={observed} expected={expected} error={error} bound={bound}")
    if error > bound:
        raise AssertionError("high-precision mismatch control failed")

print("SAGE_CHECKS_PASS")
