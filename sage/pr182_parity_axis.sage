# PR-182 Sage+Singular axis: solver-free parity identities over exact QQ.
# Independent implementation (no shared code with the SymPy axis).
import json

results = {}
computed = {}

# I1 parity involution + axisymmetric B annihilation over QQ
P = matrix(QQ, [[1, 0], [0, -1]])
results["parity_involution_exact"] = (P * P == identity_matrix(QQ, 2))
fixed = (P - identity_matrix(QQ, 2)).right_kernel()
basis = fixed.basis()
results["axisymmetric_source_forces_B_zero"] = (
    fixed.dimension() == 1 and basis[0][1] == 0 and basis[0][0] != 0
)
computed["fixed_space_dim"] = str(fixed.dimension())

# I2 reflection flips TB/EB, preserves TT/EE/BB/TE (symbolic ring + fixture)
Rng = PolynomialRing(QQ, ["tt", "ee", "bb", "te", "tb", "eb"])
tt, ee, bb, te, tb, eb = Rng.gens()
M = matrix(Rng, [[tt, te, tb], [te, ee, eb], [tb, eb, bb]])
R = matrix(Rng, [[1, 0, 0], [0, 1, 0], [0, 0, -1]])
Mp = R * M * R
symbolic_ok = (
    Mp[0, 2] == -tb and Mp[1, 2] == -eb and Mp[0, 0] == tt
    and Mp[1, 1] == ee and Mp[2, 2] == bb and Mp[0, 1] == te
)
F = matrix(QQ, [[1, QQ(1) / 4, QQ(3) / 7],
                [QQ(1) / 4, QQ(2) / 3, QQ(-2) / 5],
                [QQ(3) / 7, QQ(-2) / 5, QQ(1) / 9]])
RQ = matrix(QQ, [[1, 0, 0], [0, 1, 0], [0, 0, -1]])
Fp = RQ * F * RQ
fixture_ok = (
    Fp[0, 2] == QQ(-3) / 7 and Fp[1, 2] == QQ(2) / 5
    and Fp[0, 0] == 1 and Fp[1, 1] == QQ(2) / 3
    and Fp[2, 2] == QQ(1) / 9 and Fp[0, 1] == QQ(1) / 4
)
results["reflection_flips_TB_EB_fixture"] = bool(symbolic_ok and fixture_ok)
results["reflection_preserves_TT_EE_BB_TE_fixture"] = bool(fixture_ok)
computed["fixture_TB_flip"] = "3/7->" + str(Fp[0, 2])
computed["fixture_EB_flip"] = "-2/5->" + str(Fp[1, 2])

# I3 VII_h handedness pseudo-sign under improper transform
n = diagonal_matrix(QQ, [0, 1, 1])
a = matrix(QQ, [[QQ(1) / 2, 0, 0]])
Lam = diagonal_matrix(QQ, [-1, 1, 1])
n_prime = Lam.det() * Lam * n * Lam.transpose()
results["vii_h_improper_transform_flips_n_sign"] = (n_prime == -n)
results["vii_h_vector_constraint_holds_both_orientations"] = (
    (a * n).is_zero() and (a * n_prime).is_zero()
)
computed["n_prime_diagonal"] = str([n_prime[0, 0], n_prime[1, 1], n_prime[2, 2]])

# I4 boost kernel series: sqrt(1-b^2)/(1-b*mu) to O(b^3), mu-only coefficients
S = PowerSeriesRing(PolynomialRing(QQ, "mu"), "b", default_prec=4)
b = S.gen()
mu = S.base_ring().gen()
gamma_inv = (1 - b**2).sqrt(prec=4)
geometric = 1 + b * mu + b**2 * mu**2 + b**3 * mu**3  # 1/(1-b*mu) to O(b^3)
kernel = gamma_inv * geometric
expected = {
    0: [QQ(1)],
    1: [QQ(0), QQ(1)],
    2: [QQ(-1) / 2, QQ(0), QQ(1)],
    3: [QQ(0), QQ(-1) / 2, QQ(0), QQ(1)],
}
all_ok = True
for order, expect in expected.items():
    raw = kernel.padded_list(4)[order]
    poly = S.base_ring()(raw)  # exact conversion; raises if denominator != 1
    got = [poly[k] for k in range(len(expect))]
    if got != expect or poly.degree() >= len(expect):
        all_ok = False
    computed["boost_order_" + str(order)] = str([str(v) for v in got])
results["boost_kernel_mu_only_coefficients_exact"] = bool(all_ok)

# Singular presence receipt (axis is sage_singular)
singular_version = singular.eval('system("version");')

payload = {
    "all_pass": all(bool(v) for v in results.values()),
    "checks": {k: bool(v) for k, v in results.items()},
    "computed": computed,
    "sage_version": str(version()),
    "singular_version": str(singular_version).strip(),
}
print(json.dumps(payload, sort_keys=True))
