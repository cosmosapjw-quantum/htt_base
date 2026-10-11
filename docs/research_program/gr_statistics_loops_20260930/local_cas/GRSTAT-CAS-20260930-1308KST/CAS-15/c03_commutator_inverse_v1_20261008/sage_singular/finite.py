"""CAS-15-C03 exact finite polynomial checks in Sage 10.9.

The inequalities whose hypotheses include operator norms and ordered real
eigenvalues are derived in DERIVATION.md; this program certifies their exact
finite polynomial/projection identities without replacing universal proofs by
numeric sampling.
"""
from sage.all import QQ, PolynomialRing, diagonal_matrix, matrix, zero_matrix

P = PolynomialRing(QQ, names=("m1", "m2", "m3", "x12", "x13", "x23"))
m1, m2, m3, x12, x13, x23 = P.gens()
M = diagonal_matrix(P, [m1, m2, m3])
X = matrix(P, 3, 3, [0, x12, x13, -x12, 0, x23, -x13, -x23, 0])
C = M * X - X * M
assert C == C.transpose()
assert all(C[i, i] == 0 for i in range(3))
assert [C[0, 1], C[0, 2], C[1, 2]] == [
    (m1 - m2) * x12,
    (m1 - m3) * x13,
    (m2 - m3) * x23,
]
D = diagonal_matrix(P, [m1 - m2, m1 - m3, m2 - m3])
assert D.det() == (m1 - m2) * (m1 - m3) * (m2 - m3)
assert D.change_ring(P.fraction_field()).rank() == 3
assert D.transpose() * D == diagonal_matrix(
    P, [(m1 - m2) ** 2, (m1 - m3) ** 2, (m2 - m3) ** 2]
)
for vals, expected in [((1, 1, 2), 2), ((1, 1, 1), 0)]:
    specialized = D.subs(dict(zip((m1, m2, m3), vals)))
    assert specialized.rank() == expected
print("SAGE_COMMUTATOR_POLYNOMIAL_AND_RANK_OK")

Q = PolynomialRing(
    QQ,
    names=(
        "l1", "l2", "l3", "y12", "y13", "y23",
        "r11", "r12", "r13", "r21", "r22", "r23", "r31", "r32", "r33",
    ),
)
(l1, l2, l3, y12, y13, y23,
 r11, r12, r13, r21, r22, r23, r31, r32, r33) = Q.gens()
L = diagonal_matrix(Q, [l1, l2, l3])
Y = matrix(Q, 3, 3, [0, y12, y13, -y12, 0, y23, -y13, -y23, 0])
Rhat = matrix(Q, 3, 3, [r11, r12, r13, r21, r22, r23, r31, r32, r33])
Lmap = L * Y - Y * L
Poff = matrix(Q, 3, 3, [
    0, (r12+r21)/2, (r13+r31)/2,
    (r12+r21)/2, 0, (r23+r32)/2,
    (r13+r31)/2, (r23+r32)/2, 0,
])
assert Poff == Poff.transpose()
assert all(Poff[i, i] == 0 for i in range(3))
assert sum((Lmap[i,j]-Rhat[i,j])**2 for i in range(3) for j in range(3)) == (
    2*((l1-l2)*y12-(r12+r21)/2)**2
    + 2*((l1-l3)*y13-(r13+r31)/2)**2
    + 2*((l2-l3)*y23-(r23+r32)/2)**2
    + ((r12-r21)**2+(r13-r31)**2+(r23-r32)**2)/2
    + r11**2+r22**2+r33**2
)
assert sum((Poff[i,j]*(Rhat[i,j]-Poff[i,j])) for i in range(3) for j in range(3)) == 0
F = Q.fraction_field()
Wfit = matrix(F, 3, 3, [
    0, (r12+r21)/(2*(l1-l2)), (r13+r31)/(2*(l1-l3)),
    -(r12+r21)/(2*(l1-l2)), 0, (r23+r32)/(2*(l2-l3)),
    -(r13+r31)/(2*(l1-l3)), -(r23+r32)/(2*(l2-l3)), 0,
])
assert L.change_ring(F)*Wfit-Wfit*L.change_ring(F) == Poff.change_ring(F)
assert Wfit == -Wfit.transpose()
print("SAGE_LEAST_SQUARES_PROJECTION_AND_INVERSE_OK")
print("SAGE_C03_EXACT_CONTENT_OK")
