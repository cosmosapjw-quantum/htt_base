"""PR-124 CAS axis: SymPy — independent exact verification of the MES
geodesic reduction statement (contract CAS-PR124-MES-GEODESIC-001).

This script implements the C1/C2 reduction and every exact evaluation
directly from the contract-registered raw data. It deliberately does NOT
import ``htt.obsstat.egs3_mes_rederivation`` or any other MES module: the
axis obligation is an independent engine computation, and the in-repo
lineage modules are a separate (derivation-lineage) metric.

Output: one JSON object on stdout with per-check booleans and the computed
exact values as strings. The PR-124 runner wraps this into the axis result
envelope and binds it to the contract hash.
"""
from __future__ import annotations

import json

import sympy as sp

# Contract-registered raw data (the statement under test).
RAW_SIGMA = [(sp.Rational(8, 3), 2, 0), (sp.Integer(1), 2, 1),
             (sp.Integer(5), 1, 1), (sp.Rational(9, 7), 3, 1)]
RAW_OMEGA = [(sp.Integer(9), 1, 1), (sp.Integer(3), 1, 2),
             (sp.Rational(6, 5), 2, 2)]
EXPECT_SIGMA = (sp.Rational(5, 3), sp.Integer(3), sp.Rational(3, 7))
EXPECT_OMEGA = (sp.Rational(10, 3), sp.Rational(2, 15), sp.Integer(0))
E2 = sp.Rational(3559629, 10**12)
E3 = sp.Rational(6065291, 10**12)
E1_OBS = sp.Rational(771, 625000)
EXPECT_E1_CRIT_C2 = sp.Rational(43, 25)
EXPECT_E1_CRIT_C3 = sp.Rational(9, 35)
EXPECT_W2 = sp.Rational(4223652872547, 12500000000000000000000000)
EXPECT_SIG2 = sp.Rational(6479509460609043, 24500000000000000000000000)


def reduce_raw(terms):
    acc = {1: sp.Integer(0), 2: sp.Integer(0), 3: sp.Integer(0)}
    for coeff, ell, order in terms:
        acc[ell] += coeff * sp.Rational(1, 3) ** order
    return (acc[1], acc[2], acc[3])


def main() -> None:
    e1, e2, e3 = sp.symbols("e1 e2 e3", positive=True)

    sig = reduce_raw(RAW_SIGMA)
    om = reduce_raw(RAW_OMEGA)

    b_sigma = sig[0] * e1 + sig[1] * e2 + sig[2] * e3
    b_omega = om[0] * e1 + om[1] * e2 + om[2] * e3
    diff = sp.expand(b_sigma - b_omega)
    e1_crit = sp.solve(sp.Eq(diff, 0), e1)[0]
    e1_crit_c2 = sp.simplify(e1_crit.coeff(e2))
    e1_crit_c3 = sp.simplify(e1_crit.coeff(e3))

    def at(expr, e1v):
        return sp.nsimplify(expr.subs({e1: e1v, e2: E2, e3: E3}), rational=True)

    bs0, bo0 = at(b_sigma, sp.Integer(0)), at(b_omega, sp.Integer(0))
    w2 = sp.Rational(3, 2) * bo0 ** 2
    sig2 = sp.Rational(3, 2) * bs0 ** 2
    e1_crit_num = e1_crit.subs({e2: E2, e3: E3})
    bs_crit = at(b_sigma, e1_crit_num)
    bo_crit = at(b_omega, e1_crit_num)
    bs_obs, bo_obs = at(b_sigma, E1_OBS), at(b_omega, E1_OBS)

    checks = {
        "sigma_reduction": sig == EXPECT_SIGMA,
        "omega_reduction": om == EXPECT_OMEGA,
        "e1_crit_coefficients": (e1_crit_c2 == EXPECT_E1_CRIT_C2
                                 and e1_crit_c3 == EXPECT_E1_CRIT_C3),
        "w2_ceiling_exact": w2 == EXPECT_W2,
        "sigma2_ceiling_exact": sig2 == EXPECT_SIG2,
        "hierarchy_e1_zero_strict": bool(bs0 > bo0 > 0),
        "hierarchy_observed_fails": bool(bs_obs <= bo_obs),
        "boundary_e1_crit_equality": bool(sp.simplify(bs_crit - bo_crit) == 0),
    }
    payload = {
        "engine": "sympy",
        "engine_version": sp.__version__,
        "checks": {k: bool(v) for k, v in checks.items()},
        "computed": {
            "sigma_triple": [str(c) for c in sig],
            "omega_triple": [str(c) for c in om],
            "e1_crit_coefficients": [str(e1_crit_c2), str(e1_crit_c3)],
            "B_sigma_exact": str(bs0),
            "B_omega_exact": str(bo0),
            "W2_max_exact": str(w2),
            "Sigma2_max_exact": str(sig2),
        },
        "all_pass": all(checks.values()),
    }
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
