"""Exact Sage algebra for the frozen CAS-03-C01 real matrix statement.

Polynomial identities below hold over QQ, hence after substitution of arbitrary
real entries. The only ordered-field step is the explicitly stated positive
square-root branch, explained in the emitted certificate.
"""
import json
from sage.all import QQ, PolynomialRing, matrix, vector, identity_matrix, zero_matrix


R = PolynomialRing(QQ, names=(
    "s00", "s01", "s02", "s03", "s11", "s12", "s13", "s22", "s23", "s33",
    "u0", "u1", "u2", "u3", "a"))
(s00, s01, s02, s03, s11, s12, s13, s22, s23, s33,
 u0, u1, u2, u3, a) = R.gens()
g = matrix(R, 4, 4, [-1, 0, 0, 0,
                      0, 1, 0, 0,
                      0, 0, 1, 0,
                      0, 0, 0, 1])
S = matrix(R, 4, 4, [[s00, s01, s02, s03],
                      [s01, s11, s12, s13],
                      [s02, s12, s22, s23],
                      [s03, s13, s23, s33]])
u = vector(R, [u0, u1, u2, u3])
mass = u.dot_product(g * u) + 1
sigma = u.dot_product(S * u)
st = -sigma
B = S - st*g
mixed = g*S

# Multiplication by invertible g gives the exact covariant/mixed equivalence.
assert g*g == identity_matrix(R, 4)
assert B == B.transpose()
assert B*u == g*(mixed*u - st*u)
assert mixed*u - st*u == g*(B*u)
# If (S-a*g)u=0 and mass=0, contraction gives sigma+a=0.
# The identity is polynomial, with no division by a spectral gap or det(S).
eigen_residual = (S-a*g)*u
assert u.dot_product(eigen_residual) == sigma+a-a*mass
assert (S-a*g)*u + (a-st)*g*u == B*u

# Rest specialization: the input u=e0 is unit. Its time column vanishes from
# Bu=0, and symmetry then forces its time row to vanish. No block premise.
e0 = vector(R, [1, 0, 0, 0])
Srest = S
st_rest = -e0.dot_product(Srest*e0)
Brest = Srest-st_rest*g
assert e0.dot_product(g*e0) == -1
assert Brest*e0 == vector(R, [0, s01, s02, s03])
assert Brest == Brest.transpose()
assert all(Brest[0,j] == (Brest*e0)[j] for j in range(4))
# On the rest-kernel locus s01=s02=s03=0, the obtained block is exact.
rest_zero = {s01:0,s02:0,s03:0}
Br = Brest.apply_map(lambda p: p.subs(rest_zero))
Drest = Br.submatrix(1,1,3,3)
assert all(Br[0,j] == 0 and Br[j,0] == 0 for j in range(4))
assert Br.submatrix(1,1,3,3) == Drest

# Parametrize arbitrary trace-zero symmetric D; trace zero is the additional
# zero-expansion condition, and no rank is assumed.
T = PolynomialRing(QQ, names=("d11","d22","d12","d13","d23","w1","w2","w3","t"))
d11,d22,d12,d13,d23,w1,w2,w3,t = T.gens()
D = matrix(T, 3, 3, [[d11,d12,d13],
                     [d12,d22,d23],
                     [d13,d23,-d11-d22]])
Bt = zero_matrix(T,4,4)
for i in range(3):
    for j in range(3):
        Bt[i+1,j+1] = D[i,j]
w = vector(T,[w1,w2,w3])
v = vector(T,[t,w1,w2,w3])
gt = g.change_ring(T)
q = t*t - (1+w.dot_product(w))
assert D.trace() == 0
assert Bt*v == vector(T,[0]+list(D*w))
assert v.dot_product(gt*v)+1 == -q
# Thus on Dw=0 and q=0, v is in ker(B), unit. For every real w,
# 1+|w|^2>0 has a unique t>0 root; that is Phi(w). Conversely any future
# unit ker(B) vector has Dw=0, q=0, t>0 and hence t=sqrt(1+|w|^2).
# Projection to its last three components is a two-sided inverse, so Phi is
# injective. These ordered-field implications use no nonzero D eigenvalue.

controls = []
for name, entries, rank_expected in [
    ("full_sheet_D_zero", [0,0,0], 0),
    ("rank_two_single_kernel", [0,1,-1], 2),
    ("singleton_full_rank", [1,1,-2], 3),
]:
    Dc = matrix(QQ, 3, 3, lambda i,j: entries[i] if i == j else 0)
    Bc = zero_matrix(QQ,4,4)
    for i in range(3): Bc[i+1,i+1] = Dc[i,i]
    kernel = Dc.right_kernel()
    assert Dc.trace() == 0
    assert Dc.rank() == rank_expected
    assert kernel.dimension() == 3-rank_expected
    assert Bc.right_kernel().dimension() == 1+kernel.dimension()
    assert all(Dc*b == vector(QQ,[0,0,0]) for b in kernel.basis())
    controls.append({"case":name,"rank_D":Dc.rank(),"dim_ker_D":kernel.dimension(),
                     "dim_ker_B":Bc.right_kernel().dimension(),
                     "kernel_basis":[list(map(str,b)) for b in kernel.basis()]})

print(json.dumps({
    "engine":"SageMath", "CAS-03-C01":True,
    "polynomial_identities":["g^2=I", "Bu=g(g^-1Su-s_tu)",
        "u.(S-a g)u=(a+u.S.u)-a(g(u,u)+1)",
        "rest Bu=0 and symmetry give zero time row and column",
        "trace D=0", "B(t,w)=(0,Dw)", "g((t,w),(t,w))+1=-q"],
    "real_branch_argument":"For each real w, 1+sum(w_i^2)>0; its unique positive root t gives future unit Phi(w). Conversely future t>0 and q=0 force that root; projection w is its inverse and proves injectivity. Every rank is admitted.",
    "controls":controls,
    "scope":"conditional rest-frame fibre only; no assertion that every S admits a timelike eigenvector"
},sort_keys=True))
