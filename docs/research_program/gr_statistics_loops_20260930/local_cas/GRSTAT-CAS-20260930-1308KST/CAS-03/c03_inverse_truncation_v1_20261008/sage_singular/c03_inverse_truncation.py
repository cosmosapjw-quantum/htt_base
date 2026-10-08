"""Independent exact SageMath check of frozen CAS-03-C03."""

from sage.all import QQ, PolynomialRing, matrix, vector, identity_matrix
from sage.version import version as sage_version


def check(condition, label):
    if not condition:
        raise AssertionError(label)
    print("CHECK", label, "PASS")


print("SAGE_VERSION", sage_version)
R = PolynomialRing(QQ, names=("H", "a", "b", "c", "d", "e", "f", "g", "j", "x", "y", "z"))
H, a, b, c, d, e, f, g, j, x, y, z = R.gens()
sigma = matrix(R, [[a, b, c], [d, e, f], [g, j, -a-e]])
I = identity_matrix(R, 3)
D = H*I + sigma
beta = vector(R, [x, y, z])
h1 = -2*D*beta
detD = D.det()
adjD = D.adjugate()
check(sigma.trace() == 0 and D.trace() == 3*H, "trace_split")
check(detD != 0, "generic_det_not_zero_polynomial")
check(D*adjD == detD*I and adjD*D == detD*I, "adjugate_identity")
K = R.fraction_field()
DK = D.change_ring(K)
betaK = beta.change_ring(K)
h1K = h1.change_ring(K)
sigmaK = sigma.change_ring(K)
IK = identity_matrix(K, 3)
HK = K(H)
check(-DK.inverse()*h1K/2 == betaK, "exact_inverse_det_nonzero")
beta_trunc = -(IK-sigmaK/HK)*h1K/(2*HK)
check(betaK-beta_trunc == (sigmaK*sigmaK)*betaK/(HK*HK), "truncation_defect_H_nonzero")

# Independent boundary control: H=0 is admitted for the exact inverse only.
D0 = matrix(QQ, [[1, 0, 0], [0, 1, 0], [0, 0, -2]])
beta0 = vector(QQ, [2, -3, 5])
h10 = -2*D0*beta0
check(D0.trace() == 0 and D0.det() == -2, "H_zero_invertible_control")
check(-D0.inverse()*h10/2 == beta0, "H_zero_exact_inverse")

# Exact rational control, with epsilon represented as a polynomial variable.
S = PolynomialRing(QQ, "epsilon")
epsilon = S.gen()
Dr = matrix(S, [[S(3)/2, 0, 0], [0, S(3)/4, 0], [0, 0, S(3)/4]])
Ir = identity_matrix(S, 3)
br = vector(S, [epsilon, 0, 0])
sr = Dr-Ir
h1r = -2*Dr*br
br_trunc = -(Ir-sr)*h1r/2
check(Dr.trace() == 3 and sr.trace() == 0 and Dr.det() == S(27)/32, "rational_control_domain")
check(br_trunc == vector(S, [3*epsilon/4, 0, 0]), "rational_control_truncation")
check(br-br_trunc == vector(S, [epsilon/4, 0, 0]), "rational_control_defect")
print("RESULT exact finite CAS-03-C03 identities and controls PASS")
