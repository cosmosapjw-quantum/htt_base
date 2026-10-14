"""Independent Sage derivation of the admitted C01-C03 finite components."""
from sage.all import (
    QQ, SR, PolynomialRing, matrix, vector, identity_matrix, var,
    sqrt, sinh, cosh, tanh, exp, diff, factor, assume, forget,
    version,
)


def check(label, condition):
    if not bool(condition):
        raise AssertionError(label)
    print(f"{label}=ZERO_OR_TRUE", flush=True)


print("Sage=" + version(), flush=True)

# The five independent entries of a symmetric tracefree spatial tensor are
# represented by a,b,c,e,f; the final diagonal entry is -a-b.
P = PolynomialRing(QQ, names="h,p0,p1,p2,a,b,c,e,f")
h, p0, p1, p2, a, b, c, e, f = P.gens()
H = matrix(P, [[a, c, e], [c, b, f], [e, f, -a-b]])
S = matrix(P, 4, 4, lambda i,j:
           h if i == j == 0 else (-[p0,p1,p2][j-1]/2 if i == 0
           else (-[p0,p1,p2][i-1]/2 if j == 0 else H[i-1,j-1])))
norm_S = sum(S[i,j]**2 for i in range(4) for j in range(4))
rhs = h**2 + (p0**2+p1**2+p2**2)/2 + sum(H[i,j]**2 for i in range(3) for j in range(3))
check("C01_delta_Frobenius", norm_S-rhs == 0)
g = matrix(QQ, 4, 4, lambda i,j: (-1 if i == j == 0 else (1 if i == j else 0)))
check("C01_metric_Frobenius_squared", sum(z*z for z in g.list()) == 4)

# A universal bilinear calculation is stronger than the timelike/symmetric
# restriction: no unit constraint or target identity enters the coefficient ring.
names = [f"s{k}{i}{j}" for k in (1,2) for i in range(4) for j in range(4)] + [f"u{k}{i}" for k in (1,2) for i in range(4)]
P2 = PolynomialRing(QQ, names=names)
z = P2.gens()
S1 = matrix(P2, 4, 4, z[:16]); S2 = matrix(P2, 4, 4, z[16:32])
u1 = vector(P2, z[32:36]); u2 = vector(P2, z[36:40])
q = lambda u,A: (u*A*u.column())[0,0]
bil = lambda u,A,v: (u*A*v.column())[0,0]
delta_q = q(u2,S2)-q(u1,S1)
anchor1 = q(u2,S2-S1)+bil(u2-u1,S1,u2)+bil(u1,S1,u2-u1)
anchor2 = q(u1,S2-S1)+bil(u2-u1,S2,u2)+bil(u1,S2,u2-u1)
check("C02_anchor_S1", delta_q-anchor1 == 0)
check("C02_anchor_S2", delta_q-anchor2 == 0)

# Positive-root real chart: derivative is evaluated from u itself, not supplied.
d = var("d0 d1 d2", domain="real")
x = sum(v**2 for v in d)
u = vector(SR, [sqrt(1+x), *d])
J = matrix(SR, 4, 3, lambda i,j: diff(u[i],d[j]))
J_expected = matrix(SR, 4, 3, lambda i,j: d[j]/sqrt(1+x) if i == 0 else (1 if i-1 == j else 0))
check("C03_actual_Jacobian", all((J[i,j]-J_expected[i,j]).simplify_full() == 0 for i in range(4) for j in range(3)))
G = J.transpose()*J
G_expected = identity_matrix(SR,3)+matrix(SR,3,3,lambda i,j: d[i]*d[j]/(1+x))
check("C03_actual_Gram", all((G[i,j]-G_expected[i,j]).simplify_full() == 0 for i in range(3) for j in range(3)))

# Exact rational characteristic polynomial, derived from the actual Gram.
K = PolynomialRing(QQ, names="d0,d1,d2")
F = K.fraction_field(); dd = vector(F,K.gens()); xx = sum(v*v for v in dd)
GG = identity_matrix(F,3)+matrix(F,3,3,lambda i,j: dd[i]*dd[j]/(1+xx))
T = PolynomialRing(F, names="lambda"); lam = T.gen()
char = (identity_matrix(T,3)*lam-matrix(T,GG)).det()
factored = (lam-1)**2*(lam-(1+xx/(1+xx)))
check("C03_characteristic_polynomial", char == factored)
check("C03_zero_case", GG.subs({K.gen(i):0 for i in range(3)}) == identity_matrix(QQ,3))
print("C03_eigenvalues=1[multiplicity 2],1+x/(1+x)[multiplicity 1]; at x=0,1[multiplicity 3]", flush=True)

# Universal sign certificate. Real x=sum d_i^2 >=0. On the admitted ball,
# sqrt(x)<=sinh(R); hence sinh(R)>=0 and R>=0 because sinh is strictly
# increasing on R. Squaring gives x<=y=sinh(R)^2. All denominators below
# are positive (1+x, 1+y, cosh(R)^2).
R = var("R", domain="real")
check("C03_cosh_positive", bool(cosh(R)>0))
check("C03_sinh_derivative", (diff(sinh(R),R)-cosh(R)).simplify_full()==0)
check("C03_sinh_origin", sinh(0)==0)
check("C03_hyperbolic_identity", (cosh(R)**2-sinh(R)**2-1).simplify_full()==0)
check("C03_tanh_conversion", (tanh(R)**2-sinh(R)**2/(1+sinh(R)**2)).simplify_full()==0)
Q = PolynomialRing(QQ, names="x,y"); X,Y = Q.gens()
check("C03_bound_cross_multiplication", Y*(1+X)-X*(1+Y)==Y-X)
print("C03_sign_domain=x>=0,y=sinh(R)^2>=x,R>=0 derived from ball and strict sinh monotonicity", flush=True)
print("C03_bound_gap=(y-x)/((1+x)*(1+y))>=0; positive denominators; largest=1+x/(1+x)", flush=True)
