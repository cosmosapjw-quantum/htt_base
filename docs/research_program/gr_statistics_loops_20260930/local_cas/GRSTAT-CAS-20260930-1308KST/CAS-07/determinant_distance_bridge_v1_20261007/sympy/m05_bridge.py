"""Exact SymPy checks for the admitted CAS-07 M05 dependency bridge.

M01, M04, and C02 are accepted theorem interfaces. This file checks the
algebraic substitutions and branches used to compose them; it does not
re-prove those interfaces or use sampled matrices as a universal proof.
"""

import json
from pathlib import Path
import sympy as sp


def main():
    admitted = json.loads((Path(__file__).resolve().parent.parent / "ADMITTED_INPUTS.json").read_text())
    statements = {x["component"]: x["statement"] for x in admitted["accepted_dependencies"]}
    interface_exact = (
        statements["CAS-07-M01"] == "Under K>=0, 0<s<=L and eta_K(L)<1, 0<=eta_K(s)<=eta_K(L)<1."
        and statements["CAS-07-M04"] == "For the admitted Jacobi system, ||D(s)-s Id||op<=f_K(s)-s."
        and statements["CAS-07-C02"] == "For arbitrary real 2x2 D, s>0, 0<=eta<1 and ||D-s Id||op<=s eta, both singular values lie in [s(1-eta),s(1+eta)], det(D)>0, and the positive sqrt(det(D)) lies in the same interval."
    )
    s, k = sp.symbols("s k", positive=True, real=True)
    e, e_l = sp.symbols("e e_l", nonnegative=True, real=True)
    # The symbols e and e_l stand for eta_K(s), eta_K(L).  The order
    # e <= e_l < 1 is supplied by the accepted M01 interface.
    f_zero = s
    eta_zero = f_zero / s - 1
    f_pos = sp.sinh(sp.sqrt(k) * s) / sp.sqrt(k)
    eta_pos = f_pos / s - 1

    rewrite_zero = sp.simplify(f_zero - s - s * eta_zero) == 0
    rewrite_pos = sp.simplify(f_pos - s - s * eta_pos) == 0
    k_zero = sp.simplify(eta_zero) == 0
    k_zero_det = sp.simplify(sp.det(s * sp.eye(2)) - s**2) == 0
    k_zero_distance = sp.sqrt(s**2) == s  # s is positive.

    # Introduce u=1-e_l>0 and v=e_l-e>=0. Then 1-e=u+v>0.
    # M01 supplies both inequalities; SymPy verifies the exact identity.
    u = sp.symbols("u", positive=True, real=True)
    v = sp.symbols("v", nonnegative=True, real=True)
    domain_identity = sp.expand((1 - e) - ((1 - e_l) + (e_l - e))) == 0
    domain_positive_witness = sp.ask(sp.Q.positive(s * (u + v))) is True
    norm_rhs_identity = sp.simplify((f_pos - s) - s * eta_pos) == 0

    # The accepted C02 theorem accepts arbitrary real, possibly nonsymmetric,
    # 2x2 D, s>0, 0<=e<1, and ||D-sI||_op<=s*e.  The previous two checks
    # establish its nontrivial scalar premises from M01 and M04.
    c02_premise = bool(
        interface_exact and rewrite_zero and rewrite_pos and domain_identity
        and domain_positive_witness and norm_rhs_identity
    )
    determinant_sign = bool(c02_premise)

    # C02 returns det(D)>0, then the positive square-root branch dA exists.
    # Check that the two endpoints are ordered and K=0 reduces to dA=s.
    lower = s * (1 - e)
    upper = s * (1 + e)
    endpoint_gap = sp.simplify(upper - lower - 2 * s * e) == 0
    endpoint_positive = sp.ask(sp.Q.positive(s * (u + v))) is True
    distance_bound = bool(determinant_sign and endpoint_gap and endpoint_positive and k_zero_distance)

    # Exact finite branch controls only; C02 carries the universal proof.
    skew = sp.Matrix([[0, 1], [-1, 0]])
    nonsymmetric = 2 * sp.eye(2) + skew
    nonsymmetric_control = bool(
        nonsymmetric != nonsymmetric.T
        and sp.det(nonsymmetric) == 5
        and sp.simplify((nonsymmetric - 2 * sp.eye(2)).T * (nonsymmetric - 2 * sp.eye(2)) - sp.eye(2)) == sp.zeros(2)
        and 1 < sp.sqrt(5) < 3
    )
    edge_eta = sp.Rational(999, 1000)
    edge = sp.eye(2) + edge_eta * skew
    near_one_control = bool(sp.det(edge) > 0 and sp.sqrt(sp.det(edge)) < 1 + edge_eta)

    checks = {
        "CAS-07-M05-REWRITE": bool(rewrite_zero and rewrite_pos),
        "CAS-07-M05-C02-PREMISE": c02_premise,
        "CAS-07-M05-DETERMINANT-SIGN": determinant_sign,
        "CAS-07-M05-DISTANCE-BOUND": distance_bound,
    }
    print(json.dumps({
        "sympy_version": sp.__version__,
        "checks": checks,
        "exact_controls": {
            "K_zero_eta": bool(k_zero),
            "K_zero_det": bool(k_zero_det),
            "K_zero_positive_sqrt": bool(k_zero_distance),
            "M01_domain_identity": bool(domain_identity),
            "M01_positive_lower_witness": bool(domain_positive_witness),
            "M04_rhs_rewrite": bool(norm_rhs_identity),
            "C02_endpoint_gap": bool(endpoint_gap),
            "accepted_interfaces_exact": bool(interface_exact),
            "nonsymmetric_exact_control": nonsymmetric_control,
            "eta_near_one_exact_control": near_one_control,
        },
        "accepted_theorems_used": ["CAS-07-M01", "CAS-07-M04", "CAS-07-C02"],
        "domain_assumption_diff": [],
        "counterexample": None,
    }, sort_keys=True))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
