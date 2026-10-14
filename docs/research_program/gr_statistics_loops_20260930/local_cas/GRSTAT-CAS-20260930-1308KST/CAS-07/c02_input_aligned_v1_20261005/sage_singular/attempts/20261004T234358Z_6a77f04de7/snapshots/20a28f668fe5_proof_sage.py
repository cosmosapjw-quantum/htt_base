"""Exact algebraic certificates for the universal Euclidean C02 argument.

All variables are indeterminates over QQ.  The accompanying proof in
PROOF.md explains the order implications; these polynomial checks contain
neither a sampled matrix nor a target inequality among their premises.
"""

import json
from sage.all import PolynomialRing, QQ, matrix, vector, identity_matrix


R = PolynomialRing(QQ, names=("s", "r", "a", "b", "c", "d", "u", "v", "n", "p", "q", "t"))
s, r, a, b, c, d, u, v, n, p, q, t = R.gens()
D = matrix(R, [[a, b], [c, d]])
A = D - s * identity_matrix(R, 2)
x = vector(R, [u, v])
Ax = A * x
Dx = D * x
nv = x.dot_product(x)
pv = x.dot_product(Ax)
qv = Ax.dot_product(Ax)
cross = u * Ax[1] - v * Ax[0]
B = (D + D.transpose()) / 2
k = (b - c) / 2
w = vector(R, [-B[0, 1], B[0, 0]])

certificates = {
    "euclidean_lagrange_cauchy": nv * qv - pv**2 - cross**2,
    "gram_vector_expansion": Dx.dot_product(Dx) - (s**2 * nv + 2 * s * pv + qv),
    "gram_det_is_detD_squared": (D.transpose() * D).det() - D.det()**2,
    "symmetric_part_quadratic": x.dot_product(B * x) - (s * nv + pv),
    "detD_symmetric_skew_decomposition": D.det() - B.det() - k**2,
    "symmetric_part_det_witness": w.dot_product(B * w) - B[0, 0] * B.det(),
    "upper_gap_decomposition": ((s+r)**2*n - (s**2*n+2*s*p+q)) - (2*s*(r*n-p)+(r**2*n-q)),
}

# For t=sqrt(n*q), n>0, the lower gap has this exact nonnegative
# factorization modulo t^2=n*q.  The reduction must be exactly zero.
lower_gap = (s**2*n + 2*s*p + q) - (s-r)**2*n
lower_rhs = 2*s*n*(p+t) + (r*n-t)*((2*s-r)*n-t)
certificates["lower_gap_factor_mod_t2_eq_nq"] = (n*lower_gap - lower_rhs).reduce(R.ideal(t**2-n*q).groebner_basis())

for name, residual in certificates.items():
    print(json.dumps({"certificate": name, "residual": str(residual), "zero": residual == 0}, sort_keys=True))
    if residual != 0:
        raise AssertionError(f"nonzero universal polynomial residual: {name}: {residual}")

print(json.dumps({"sage_exact_certificates": len(certificates), "all_zero": True}, sort_keys=True))
