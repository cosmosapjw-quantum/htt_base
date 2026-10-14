"""Exact Sage controls for the CAS-07 M05 determinant/distance bridge.

This file checks only algebraic identities and scope controls.  The M01, M04,
and C02 results are consumed as opaque accepted theorem statements; they are
not reproved here.
"""

from sage.all import Matrix, PolynomialRing, QQ, SR, sinh, sqrt, var


# The definition eta = f/s - 1 is used only on the admitted domain s > 0.
P = PolynomialRing(QQ, names=("f", "s", "eta", "etaL"))
f, s, eta, etaL = P.gens()
definition_ideal = P.ideal([s * eta - (f - s)])
assert definition_ideal.reduce((f - s) - s * eta) == 0

# The same rewrite is checked directly for the K > 0 branch of f_K.
Ksym, ssym = var("Ksym ssym", domain="positive")
f_positive = sinh(sqrt(Ksym) * ssym) / sqrt(Ksym)
eta_positive = f_positive / ssym - 1
assert ((f_positive - ssym) - ssym * eta_positive).simplify_full() == 0

# M01 supplies 0 <= eta <= etaL < 1.  This identity exposes the exact
# transitivity step: 1-eta=(1-etaL)+(etaL-eta)>0.
assert (1 - eta) - ((1 - etaL) + (etaL - eta)) == 0

# Keep the C02 matrix scope genuinely arbitrary and nonsymmetric: b and c are
# independent indeterminates and no relation b=c is placed in the ring.
Q = PolynomialRing(QQ, names=("a", "b", "c", "d", "sigma", "eps"))
a, b, c, d, sigma, eps = Q.gens()
D = Matrix(Q, [[a, b], [c, d]])
assert D.det() == a * d - b * c
assert D[0, 1] - D[1, 0] == b - c
assert D[0, 1] - D[1, 0] != 0

# Boundary control K=0: f=s and eta=0 collapse both C02 endpoints to s.
k0_ideal = P.ideal([f - s, eta])
assert k0_ideal.reduce((f - s) - s * eta) == 0
assert k0_ideal.reduce(s * (1 - eta) - s) == 0
assert k0_ideal.reduce(s * (1 + eta) - s) == 0

print("SAGE_REWRITE_EXACT=true")
print("SAGE_C02_PREMISE_GAP_IDENTITY=true")
print("SAGE_ARBITRARY_NONSYMMETRIC_SCOPE=true")
print("SAGE_K0_CONTROL=true")
