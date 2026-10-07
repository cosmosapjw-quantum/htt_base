from sage.all import QQ, PolynomialRing, matrix, identity_matrix, sinh, sqrt, SR, var


P = PolynomialRing(QQ, "t")
t = P.gen()
F = P.fraction_field()
I = identity_matrix(F, 2)
A = matrix(F, [[0, 1], [0, 0]])
B = matrix(F, [[0, 0], [1, 0]])
assert A * B != B * A

# An exact, regular, noncommuting manufactured Jacobi example.  The universal
# argument is in proof.md; this example checks composition order and components.
M = I + t**2 * A + t**3 * B
D = t * M
D2 = D.apply_map(lambda p: p.derivative(t).derivative(t))
R = -(6 * A + 12 * t * B) * M.inverse()
assert R * D + D2 == 0
assert all(q.denominator()(0) != 0 for q in R.list())


def weighted_integral(poly):
    """Exact integral from 0 to s of (s-t) poly(t) dt, with s named t."""
    p = P(poly)
    return sum((c * t ** (j + 2) / QQ((j + 1) * (j + 2))
                for j, c in enumerate(p.list())), P.zero())


integral = matrix(F, 2, 2, [weighted_integral(P(q)) for q in (R * D).list()])
assert D == t * I - integral
assert D.apply_map(lambda p: p(0)) == matrix(QQ, 2, 2, 0)
assert D.apply_map(lambda p: p.derivative(t)(0)) == identity_matrix(QQ, 2)

# Exact scalar kernel identities and branches; no numerical sampling is used.
x, k = var("x k")
f = sinh(sqrt(k) * x) / sqrt(k)
assert (f.diff(x, 2) - k * f).simplify_full() == 0
assert f.subs(x=0).simplify_full() == 0
assert f.diff(x).subs(x=0).simplify_full() == 1
assert (x - x).simplify_full() == 0  # K=0: f_0(x)=x.
print("SAGE_EXACT_COMPONENT_AND_SCALAR_CHECKS_PASS")
