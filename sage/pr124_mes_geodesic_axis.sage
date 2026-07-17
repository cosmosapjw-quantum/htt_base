# PR-124 CAS axis: SageMath — independent exact verification of the MES
# geodesic reduction statement (contract CAS-PR124-MES-GEODESIC-001).
# Exact QQ arithmetic and polynomial-ring coefficient extraction only.
# Emits one JSON object on stdout; the PR-124 runner wraps it into the
# axis result envelope.

import json
from sage.all import QQ, PolynomialRing, version

raw_sigma = [(QQ(8) / 3, 2, 0), (QQ(1), 2, 1), (QQ(5), 1, 1), (QQ(9) / 7, 3, 1)]
raw_omega = [(QQ(9), 1, 1), (QQ(3), 1, 2), (QQ(6) / 5, 2, 2)]
expect_sigma = (QQ(5) / 3, QQ(3), QQ(3) / 7)
expect_omega = (QQ(10) / 3, QQ(2) / 15, QQ(0))
e2v = QQ(3559629) / QQ(10) ** 12
e3v = QQ(6065291) / QQ(10) ** 12
e1_obs = QQ(771) / 625000
expect_w2 = QQ(4223652872547) / QQ(12500000000000000000000000)
expect_sig2 = QQ(6479509460609043) / QQ(24500000000000000000000000)


def reduce_raw(terms):
    acc = {1: QQ(0), 2: QQ(0), 3: QQ(0)}
    for coeff, ell, order in terms:
        acc[ell] += coeff * (QQ(1) / 3) ** order
    return (acc[1], acc[2], acc[3])


sig = reduce_raw(raw_sigma)
om = reduce_raw(raw_omega)

R = PolynomialRing(QQ, names=("e1", "e2", "e3"))
e1, e2, e3 = R.gens()
b_sigma = sig[0] * e1 + sig[1] * e2 + sig[2] * e3
b_omega = om[0] * e1 + om[1] * e2 + om[2] * e3
diff = b_sigma - b_omega
# diff = -(coef) e1 + c2 e2 + c3 e3; e1_crit = (c2 e2 + c3 e3) / coef
coef_e1 = -diff.coefficient({e1: 1, e2: 0, e3: 0})
c2coef = diff.coefficient({e1: 0, e2: 1, e3: 0}) / coef_e1
c3coef = diff.coefficient({e1: 0, e2: 0, e3: 1}) / coef_e1


def at(poly, e1v):
    return poly(e1=e1v, e2=e2v, e3=e3v)


bs0 = at(b_sigma, QQ(0))
bo0 = at(b_omega, QQ(0))
w2 = QQ(3) / 2 * bo0 ** 2
sig2 = QQ(3) / 2 * bs0 ** 2
e1_crit_num = c2coef * e2v + c3coef * e3v
checks = {
    "sigma_reduction": tuple(sig) == expect_sigma,
    "omega_reduction": tuple(om) == expect_omega,
    "e1_crit_coefficients": (c2coef == QQ(43) / 25 and c3coef == QQ(9) / 35),
    "w2_ceiling_exact": w2 == expect_w2,
    "sigma2_ceiling_exact": sig2 == expect_sig2,
    "hierarchy_e1_zero_strict": bool(bs0 > bo0 > 0),
    "hierarchy_observed_fails": bool(at(b_sigma, e1_obs) <= at(b_omega, e1_obs)),
    "boundary_e1_crit_equality": bool(
        at(b_sigma, e1_crit_num) == at(b_omega, e1_crit_num)
    ),
}
payload = {
    "engine": "sage",
    "engine_version": str(version()),
    "checks": {k: bool(v) for k, v in checks.items()},
    "computed": {
        "sigma_triple": [str(c) for c in sig],
        "omega_triple": [str(c) for c in om],
        "e1_crit_coefficients": [str(c2coef), str(c3coef)],
        "B_sigma_exact": str(bs0),
        "B_omega_exact": str(bo0),
        "W2_max_exact": str(w2),
        "Sigma2_max_exact": str(sig2),
    },
    "all_pass": all(checks.values()),
}
print(json.dumps(payload, sort_keys=True))
