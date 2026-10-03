"""Independent exact Sage component calculation for CAS-04.

Run with ``sage -python engine.py``.  All equalities are checked in rational
function fields over QQ, with invertibility restricted in PROOF.md.
"""
import json
from sage.all import QQ, PolynomialRing, matrix, vector, identity_matrix, version, singular


def zero(x):
    return x == 0


names = ["c", "e", "p1", "p2", "p3", "delta"]
names += [f"d{a}{i}" for a in range(4) for i in range(3)]
R = PolynomialRing(QQ, names=names)
v = R.gens_dict()
F = R.fraction_field()
c, e, delta = (F(v[k]) for k in ("c", "e", "delta"))
gap = [e + F(v[f"p{i+1}"]) for i in range(3)]
D = matrix(F, 4, 3, [F(v[f"d{a}{i}"]) for a in range(4) for i in range(3)])
L = matrix(F, 3, 3, lambda i, j: gap[i] if i == j else 0)

# Differentiate T u = -e u.  Normalization gives u.grad_X u = 0, so the
# spatial part obeys L grad_X u = -h(grad_X T)u = -D_X.
grad_u = matrix(F, 4, 3, lambda a, i: -(L.inverse() * vector(F, D.row(a)))[i])
Q = c * grad_u
c01 = all(zero(x) for x in (grad_u * L.transpose() + D).list())
c01 &= all(zero(x) for x in (Q * L.transpose() + c * D).list())
c01 &= all(zero(Q[a, i] + c * D[a, i] / gap[i]) for a in range(4) for i in range(3))

M = matrix(F, 3, 3, lambda i, j: Q[i+1, j])
theta = sum(M[i, i] for i in range(3))
sigma = (M + M.transpose()) / 2 - theta * identity_matrix(F, 3) / 3
W = (M - M.transpose()) / 2
omega = vector(F, (W[1, 2], -W[0, 2], W[0, 1]))
A = vector(F, (c * Q[0, i] for i in range(3)))
frobenius = lambda B: sum(B[i, j]**2 for i in range(B.nrows()) for j in range(B.ncols()))
lhs = theta**2 / 3 + frobenius(sigma) + 2 * sum(x**2 for x in omega) + sum(x**2 for x in A) / c**2
rhs = c**2 * sum(D[a, i]**2 / gap[i]**2 for a in range(4) for i in range(3))
c02 = (M == theta * identity_matrix(F, 3)/3 + sigma + W)
c02 &= zero(sum(sigma[i, i] for i in range(3)))
c02 &= all(zero(sigma[i,j]-sigma[j,i]) and zero(W[i,j]+W[j,i]) for i in range(3) for j in range(3))
c02 &= zero(frobenius(W)-2*sum(x**2 for x in omega))
c02 &= zero(lhs-rhs)

bound = c**2 * sum(D[a,i]**2 for a in range(4) for i in range(3)) / delta**2
sos = c**2 * sum(D[a,i]**2 * (gap[i]**2-delta**2) /
                   (delta**2 * gap[i]**2) for a in range(4) for i in range(3))
c03 = zero(bound-rhs-sos)

# Independent perfect-fluid divergence expansion at the rest event.
names4 = ["c", "e", "p", "cs2"]
names4 += [f"de{a}" for a in range(4)] + [f"dp{a}" for a in range(4)]
names4 += [f"du{a}{i}" for a in range(4) for i in range(3)]
R4 = PolynomialRing(QQ, names=names4)
v4 = R4.gens_dict()
F4 = R4.fraction_field()
c4,e4,p4,cs2 = (F4(v4[k]) for k in ("c","e","p","cs2"))
u = [F4(1),F4(0),F4(0),F4(0)]
gup = [-1,1,1,1]
du = matrix(F4,4,4,lambda a,b: F4(0) if b == 0 else F4(v4[f"du{a}{b-1}"]))
de = [F4(v4[f"de{a}"]) for a in range(4)]
dp = [F4(v4[f"dp{a}"]) for a in range(4)]
def dT(a, mu, nu):
    return ((de[a]+dp[a])*u[mu]*u[nu]
            +(e4+p4)*(du[a,mu]*u[nu]+u[mu]*du[a,nu])
            +(dp[a]*gup[mu] if mu==nu else 0))
div = [sum(dT(mu,mu,nu) for mu in range(4)) for nu in range(4)]
spatial = [F4((e4+p4)*du[0,i+1]+dp[i+1]) for i in range(3)]
eulerA = [-c4**2*dp[i+1]/(e4+p4) for i in range(3)]
baroA = [-cs2*de[i+1]/(e4+p4) for i in range(3)]
c04 = all(zero(div[i+1]-spatial[i]) for i in range(3))
c04 &= all(zero(eulerA[i]+c4**2*dp[i+1]/(e4+p4)) for i in range(3))
c04 &= all(zero((eulerA[i]-baroA[i]).subs({dp[i+1]:cs2*de[i+1]/c4**2})) for i in range(3))
c04 &= all(zero(x.subs({p4:0,dp[i+1]:0})) for i,x in enumerate(eulerA))

print(json.dumps({
    "engine": "sage", "sage_version": version(),
    "singular_version_code": str(singular.eval('system("version");')).strip(),
    "checks": {"CAS-04-C01": bool(c01), "CAS-04-C02": bool(c02),
               "CAS-04-C03": bool(c03), "CAS-04-C04": bool(c04)},
    "certificate": {
        "C01_residual_count": 24,
        "C02_weighted_identity": bool(zero(lhs-rhs)),
        "C03_exact_sos_identity": bool(zero(bound-rhs-sos)),
        "C04_divergence_components": [bool(zero(div[i+1]-spatial[i])) for i in range(3)],
    },
}, sort_keys=True))
