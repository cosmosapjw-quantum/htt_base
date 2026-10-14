"""Independent exact SageMath verification of frozen CAS-10-C03 v2."""

from sage.all import QQ, PolynomialRing, identity_matrix, matrix, vector, diagonal_matrix
from sage.version import version as sage_version


names = (
    "H", "z0", "z1a", "z1b", "z1c", "m", "t1", "t2", "t3", "t4", "t5",
    "s0", "s1", "sm", "sp", "st",
)
P = PolynomialRing(QQ, names=names)
K = P.fraction_field()
H, z0, z1a, z1b, z1c, m, t1, t2, t3, t4, t5, s0, s1, sm, sp, st = map(K, P.gens())

R = matrix(K, [[0, -1, 0], [1, 0, 0], [0, 0, 1]])
assert R.transpose() * R == identity_matrix(K, 3)
assert R.det() == 1
print("R_ORTHOGONAL=true DET_R=1")

block_dims = (1, 3, 1, 3, 5)
B = identity_matrix(K, 13)
for i in range(3):
    for j in range(3):
        B[5+i, 5+j] = R[i, j]
assert B.transpose() * B == identity_matrix(K, 13)
assert B.det() == 1
for i in list(range(5)) + list(range(8, 13)):
    assert B[i, i] == 1
    assert all(B[i, j] == 0 for j in range(13) if j != i)
print("DIRECT_SUM_ORDER=Z0,Z1,m,p,T DIRECT_SUM_ORTHOGONAL=true UNCHANGED_IDENTITY=true DET_B=1")

mu = vector(K, [z0, z1a, z1b, z1c, m, 15*H/8, 0, 0, t1, t2, t3, t4, t5])
mu_prime = vector(K, [z0, z1a, z1b, z1c, m, 0, 15*H/8, 0, t1, t2, t3, t4, t5])
assert B * mu == mu_prime
assert R * vector(K, [15*H/8, 0, 0]) == vector(K, [0, 15*H/8, 0])
offsets = (0, 1, 4, 5, 8, 13)
for j in range(5):
    a, b = offsets[j], offsets[j+1]
    lhs = sum(mu[k]**2 for k in range(a, b))
    rhs = sum(mu_prime[k]**2 for k in range(a, b))
    assert lhs == rhs
    print(f"BLOCK_NORM_{j+1}=equal dimension={block_dims[j]} norm_squared={lhs}")

covdiag = [s0**2] + [s1**2]*3 + [sm**2] + [sp**2]*3 + [st**2]*5
Sigma = diagonal_matrix(K, covdiag)
Sigma_inv = diagonal_matrix(K, [1/x for x in covdiag])
assert Sigma * Sigma_inv == identity_matrix(K, 13)
delta = mu - mu_prime
quadratic = delta.dot_product(Sigma_inv * delta)
kl = quadratic / 2
assert kl == 225*H**2/(64*sp**2)
assert kl.subs({H: K(0), sp: K(1)}) == 0
assert kl.subs({H: K(1), sp: K(1)}) == QQ(225)/64
print(f"COVARIANCE_INVERSE=true QUADRATIC={quadratic} KL={kl}")
print("CONTROL_H0_KL=0 CONTROL_H1_SP1_KL=225/64")
print("ASSUMPTIONS=H_real; all five scales positive; sp_nonzero_for_inverse")
print("EXCLUSIONS=compressed_law_equality,test_power,measure_theoretic_gaussian,science")
print(f"SAGE_VERSION={sage_version}")
print("SAGE_EXACT_PASS=true")
