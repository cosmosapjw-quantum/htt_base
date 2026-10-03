#!/usr/bin/env sage -python
"""Independent exact finite CAS-01 certificate (SageMath and Singular)."""

import json
from pathlib import Path

from sage.all import PolynomialRing, QQ, matrix, vector, identity_matrix, singular, version


HERE = Path(__file__).resolve().parent
TRANSCRIPT = []


def seval(command):
    response = singular.eval(command)
    TRANSCRIPT.append({"command": command, "response": response})
    return response


def sing_zero(poly, ideal="G"):
    response = seval(f"reduce(({poly}),{ideal});").strip()
    return response == "0"


names = (
    [f"u{i}" for i in range(4)]
    + [f"s{i}{j}" for i in range(4) for j in range(i, 4)]
    + [f"t{i}{j}" for i in range(4) for j in range(i + 1, 4)]
    + ["a", "c", "z"]
    + [f"x{i}" for i in range(4)]
)
R = PolynomialRing(QQ, names, order="degrevlex")
q = R.gens_dict()
u = vector(R, [q[f"u{i}"] for i in range(4)])
g = matrix(R, 4, 4, lambda i, j: (-1 if i == j == 0 else 1 if i == j else 0))
uf = g * u
shell = u.dot_product(uf) + 1
S = matrix(R, 4, 4, lambda i, j: q[f"s{min(i,j)}{max(i,j)}"])
T = matrix(R, 4, 4, lambda i, j: 0 if i == j else (q[f"t{i}{j}"] if i < j else -q[f"t{j}{i}"]))
P = identity_matrix(R, 4) + u.column() * uf.row()
B = S + u.dot_product(S * u) * g
b = B * u
W = P.transpose() * T * P
Q = B + b.column() * uf.row() - uf.column() * b.row() + W
c, z, a = q["c"], q["z"], q["a"]
ideal = R.ideal([shell, c * z - 1])

# The direct Singular calls reduce the actual target polynomials. The ideal
# contains only the mass-shell equation and the inverse witness c*z=1.
seval(f"ring cas01=0,({','.join(names)}),dp;")
seval(f"ideal I={shell},c*z-1;")
seval("ideal G=std(I);")


def cert(label, polys):
    polys = list(polys)
    sage_remainders = [p.reduce(ideal.groebner_basis()) for p in polys]
    sage_ok = all(p == 0 for p in sage_remainders)
    singular_ok = all(sing_zero(p) for p in polys)
    certificate[label] = {
        "count": len(polys),
        "sage_remainders_zero": sage_ok,
        "singular_remainders_zero": singular_ok,
    }
    return sage_ok and singular_ok


certificate = {}

# C01: generic u; invariance is checked from the shifted S definition.
shift = S + a * g
Bshift = shift + u.dot_product(shift * u) * g
c01_shell = cert("c01_shell_and_shift", [u.dot_product(B * u)] + (Bshift - B).list())

# Null-cone kernel: eliminate n modulo its sphere ideal, extract coefficient
# constraints on an independently generic symmetric form, then prove those
# constraints imply every component equals lambda*g. This does not assume the
# kernel conclusion as an ideal generator.
N = PolynomialRing(QQ, ["n1", "n2", "n3"] + [f"m{i}{j}" for i in range(4) for j in range(i, 4)], order="degrevlex")
nq = N.gens_dict()
n = vector(N, [-1, nq["n1"], nq["n2"], nq["n3"]])
M = matrix(N, 4, 4, lambda i, j: nq[f"m{min(i,j)}{max(i,j)}"])
sphere = sum(nq[f"n{i}"] ** 2 for i in range(1, 4)) - 1
F = n.dot_product(M * n)
seval("ring nullcone=0,(n1,n2,n3," + ",".join(f"m{i}{j}" for i in range(4) for j in range(i, 4)) + "),dp;")
seval(f"ideal NI={sphere};")
seval("ideal NG=std(NI);")
cone_remainder = N(F).reduce([sphere])
# Group terms by n-monomial. The m variables are coefficient indeterminates,
# so taking dict().values() directly would incorrectly return rational scalars.
coefficient_map = {}
mvars = [nq[f"m{i}{j}"] for i in range(4) for j in range(i, 4)]
for powers, scalar in cone_remainder.dict().items():
    spatial_powers = tuple(powers[:3])
    term = N(scalar)
    for mv, power in zip(mvars, powers[3:]):
        term *= mv ** power
    coefficient_map[spatial_powers] = coefficient_map.get(spatial_powers, N.zero()) + term
cone_coeffs = list(coefficient_map.values())
# Independently test Singular's quotient remainder and generated kernel ideal.
sing_cone = seval(f"reduce(({F}),NG);")
sing_cone_same = N(sing_cone) == cone_remainder
seval("ideal KC=" + ",".join(map(str, cone_coeffs)) + ";")
seval("ideal KG=std(KC);")
kernel_targets = [M[i, j] + (nq["m00"] if i == j and i > 0 else 0) for i in range(4) for j in range(i, 4) if (i, j) != (0, 0)]
kernel_forward_sage = all(N(p).reduce(N.ideal(cone_coeffs).groebner_basis()) == 0 for p in kernel_targets)
kernel_forward_singular = all(sing_zero(p, "KG") for p in kernel_targets)
# Converse: form lambda*g with lambda=-m00 vanishes identically on the cone.
kernel_converse = all(N(p).reduce(N.ideal(kernel_targets).groebner_basis()) == 0 for p in cone_coeffs)
seval("ideal KT=" + ",".join(map(str, kernel_targets)) + ";")
seval("ideal KTG=std(KT);")
kernel_converse_singular = all(sing_zero(p, "KTG") for p in cone_coeffs)
certificate["null_cone_kernel"] = {
    "remainder_coefficient_count": len(cone_coeffs),
    "singular_cone_remainder": sing_cone,
    "singular_cone_remainder_agrees_with_sage": sing_cone_same,
    "forward_sage": kernel_forward_sage,
    "forward_singular": kernel_forward_singular,
    "converse_sage": kernel_converse,
    "converse_singular": kernel_converse_singular,
}
c01 = c01_shell and sing_cone_same and kernel_forward_sage and kernel_forward_singular and kernel_converse and kernel_converse_singular

# Restore generic ring for C02/C04. Spatial W is projected from arbitrary T.
seval("setring cas01;")
c02_spatial = cert("c02_spatial_W", list(W * u) + (W.transpose() + W).list())
c02_algebra = cert("c02_Q_and_acceleration", list(Q * u) + (Q + Q.transpose() - 2 * B).list() + list(c * Q.transpose() * u - 2 * c * b))
h = g + uf.column() * uf.row()
D = P.transpose() * B * P
theta = sum(g[i, i] * B[i, i] for i in range(4))
sigma = D - (theta / 3) * h
c02_stf = cert("c02_theta_STF", list(D * u) + list(sigma * u) + [sum(g[i, i] * sigma[i, i] for i in range(4))] + (sigma - sigma.transpose()).list() + [sum(g[i, i] * D[i, i] for i in range(4)) - theta])
c02 = c02_spatial and c02_algebra and c02_stf

# C03: specialize the same generic form to the observer rest frame. The unit
# sphere is used for the quadrupole trace decomposition, not assumed by target.
rest_subs = {u[i]: (1 if i == 0 else 0) for i in range(4)}
nrest = vector(R, [-1, q["x1"], q["x2"], q["x3"]])
Br = B.apply_map(lambda entry: entry.subs(rest_subs))
thetar = sum(Br[i, i] for i in range(1, 4))
sigmar = matrix(R, 3, 3, lambda i, j: Br[i + 1, j + 1] - (thetar / 3 if i == j else 0))
dipole = vector(R, [2 * Br[i, 0] for i in range(1, 4)])
nn = vector(R, [q[f"x{i}"] for i in range(1, 4)])
rest_sphere = sum(ni ** 2 for ni in nn) - 1
rest_ideal = R.ideal([rest_sphere, c * z - 1])
rest_target = nrest.dot_product(Br * nrest) - (thetar / 3 + nn.dot_product(sigmar * nn) - dipole.dot_product(nn))
# A/c is 2b; the explicit c inverse witness checks A_i=2c b_i and A_i/c=2b_i.
rest_units = [c * z - 1, *(c * z * dipole[i] - dipole[i] for i in range(3))]
sage_rest = all(R(p).reduce(rest_ideal.groebner_basis()) == 0 for p in [rest_target] + rest_units)
seval(f"ideal RI={rest_sphere},c*z-1;")
seval("ideal RG=std(RI);")
sing_rest = all(sing_zero(p, "RG") for p in [rest_target] + rest_units)
# General S with STF h2 has the specified harmonic signs exactly.
H = matrix(R, 3, 3, lambda i, j: q[f"s{min(i+1,j+1)}{max(i+1,j+1)}"] if not (i == j == 2) else -q["s11"] - q["s22"])
h1 = vector(R, [q["s01"], q["s02"], q["s03"]])
Sformal = matrix(R, 4, 4, lambda i, j: q["s00"] if i == j == 0 else -h1[max(i,j)-1] / 2 if min(i,j) == 0 else H[i-1,j-1])
harmonic_target = nrest.dot_product(Sformal * nrest) - (q["s00"] + h1.dot_product(nn) + nn.dot_product(H * nn))
harmonic_sage = harmonic_target == 0 and sum(H[i, i] for i in range(3)) == 0
harmonic_singular = sing_zero(harmonic_target, "RG")
certificate["c03_rest_harmonics"] = {"sage": sage_rest and harmonic_sage, "singular": sing_rest and harmonic_singular}
c03 = sage_rest and sing_rest and harmonic_sage and harmonic_singular

# C04: form the affine seed, differentiate its norm polynomial at x=0, then
# apply the positive square-root derivative. Checking the resulting jet is
# valid because -g(v,v)=1 at the vertex; no local-flow theorem is inferred.
x = vector(R, [q[f"x{i}"] for i in range(4)])
J = z * g * Q.transpose()
v = u + J * x
norm2 = -v.dot_product(g * v)
xzero = {x[i]: 0 for i in range(4)}
N0 = norm2.subs(xzero)
dN = vector(R, [norm2.derivative(x[i]).subs(xzero) for i in range(4)])
jet = matrix(R, 4, 4, lambda i, j: J[i, j] - u[i] * dN[j] / 2)
c04 = cert("c04_normalization_jet", [N0 - 1] + list(dN) + (c * (jet - J)).list())

checks = {"CAS-01-C01": c01, "CAS-01-C02": c02, "CAS-01-C03": c03, "CAS-01-C04": c04}
(HERE / "CERTIFICATE.json").write_text(json.dumps({"sage_version": version(), "singular_version_code": seval('system("version");'), "certificates": certificate}, indent=2) + "\n")
(HERE / "SINGULAR_TRANSCRIPT.json").write_text(json.dumps(TRANSCRIPT, indent=2) + "\n")
print(json.dumps({"checks": checks, "domain_assumption_diff": [], "counterexample": None}, sort_keys=True))
