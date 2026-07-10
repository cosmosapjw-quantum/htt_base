# EGS3 v9 T2G exact-QQ SageMath lane (REV-R171).
#
# Independent second engine for the general fractional-program interval
# theorem: solves the Charnes-Cooper linear program EXACTLY over QQ (PPL
# backend) for the joint and product-relaxation intervals and cross-checks
# corner enumeration, on three pinned instances including the 2026-07-10
# reviewer counterexample. Emits one JSON line {"status": ..., "checks": ...}.
#
# Diagnostic-only exact interval algebra; no data claim, no geometry claim.

import json
import itertools


def corner_interval(n_pt, d_pt, bounds, c_num, c_den):
    """Corner-enumeration joint interval, signed-safe four-candidate form."""
    n_lo, n_hi = n_pt
    d_lo, d_hi = d_pt
    vals = []
    for corner in itertools.product(*[(lo, hi) for lo, hi in bounds]):
        dn = sum(c * s for c, s in zip(c_num, corner))
        dd = sum(c * s for c, s in zip(c_den, corner))
        Ds = [d_lo + dd, d_hi + dd]
        if min(Ds) <= 0:
            return None
        Ns = [n_lo + dn, n_hi + dn]
        vals.extend([N / D for N in Ns for D in Ds])
    return min(vals), max(vals)


def cc_lp_extreme(n_pt, d_pt, bounds, c_num, c_den, sense):
    """Charnes-Cooper LP over QQ (PPL): extreme of (r_N + c_N.s)/(r_D + c_D.s)
    with r_N in n_pt, r_D in d_pt, s in the box, denominator normalized to 1.

    Variables: t >= 0 (scaling), y_j = t s_j, u = t r_N, v = t r_D.
    Constraint v + c_D.y = 1; box: lo_j t <= y_j <= hi_j t;
    n_lo t <= u <= n_hi t; d_lo t <= v <= d_hi t. Objective u + c_N.y.
    """
    maximization = (sense == "max")
    lp = MixedIntegerLinearProgram(maximization=maximization, solver="PPL")
    t = lp.new_variable(nonnegative=True)["t"]
    y = lp.new_variable()
    u = lp.new_variable()["u"]
    v = lp.new_variable()["v"]
    k = len(bounds)
    lp.add_constraint(v + sum(c_den[j] * y[j] for j in range(k)) == 1)
    for j, (lo, hi) in enumerate(bounds):
        lp.add_constraint(y[j] - lo * t >= 0)
        lp.add_constraint(y[j] - hi * t <= 0)
    n_lo, n_hi = n_pt
    d_lo, d_hi = d_pt
    lp.add_constraint(u - n_lo * t >= 0)
    lp.add_constraint(u - n_hi * t <= 0)
    lp.add_constraint(v - d_lo * t >= 0)
    lp.add_constraint(v - d_hi * t <= 0)
    lp.set_objective(u + sum(c_num[j] * y[j] for j in range(k)))
    return QQ(lp.solve())


def product_interval(n_pt, d_pt, bounds, c_num, c_den):
    """Product relaxation: independent numerator/denominator box copies."""
    n_lo, n_hi = n_pt
    d_lo, d_hi = d_pt
    span_n_lo = sum(min(c * lo, c * hi) for c, (lo, hi) in zip(c_num, bounds))
    span_n_hi = sum(max(c * lo, c * hi) for c, (lo, hi) in zip(c_num, bounds))
    span_d_lo = sum(min(c * lo, c * hi) for c, (lo, hi) in zip(c_den, bounds))
    span_d_hi = sum(max(c * lo, c * hi) for c, (lo, hi) in zip(c_den, bounds))
    N_lo, N_hi = n_lo + span_n_lo, n_hi + span_n_hi
    D_lo, D_hi = d_lo + span_d_lo, d_hi + span_d_hi
    if D_lo <= 0:
        return None
    cands = [N / D for N in (N_lo, N_hi) for D in (D_lo, D_hi)]
    return min(cands), max(cands)


def analyze(n_pt, d_pt, bounds, c_num, c_den):
    corner = corner_interval(n_pt, d_pt, bounds, c_num, c_den)
    lp_lo = cc_lp_extreme(n_pt, d_pt, bounds, c_num, c_den, "min")
    lp_hi = cc_lp_extreme(n_pt, d_pt, bounds, c_num, c_den, "max")
    prod = product_interval(n_pt, d_pt, bounds, c_num, c_den)
    return {
        "corner": corner, "lp": (lp_lo, lp_hi), "product": prod,
        "lp_matches_corner": corner is not None and
                             (lp_lo, lp_hi) == corner,
        "containment": prod is not None and corner is not None and
                       prod[0] <= corner[0] and corner[1] <= prod[1],
        "strict_lower": corner[0] > prod[0],
        "strict_upper": corner[1] < prod[1],
    }


checks = {}

# (a) reviewer counterexample: S=[0,1], N(s)=s, D(s)=1+s
ce = analyze((QQ(0), QQ(0)), (QQ(1), QQ(1)), [(QQ(0), QQ(1))],
             [QQ(1)], [QQ(1)])
checks["ce_lp_matches_corner"] = ce["lp_matches_corner"]
checks["ce_containment"] = ce["containment"]
checks["ce_joint_is_0_half"] = ce["corner"] == (QQ(0), QQ(1) / 2)
checks["ce_product_is_0_1"] = ce["product"] == (QQ(0), QQ(1))
checks["ce_lower_not_strict"] = not ce["strict_lower"]
checks["ce_upper_strict"] = ce["strict_upper"]

# (b) pinned positive instance: N=1+2s, D=1+s on [0,1] (both endpoints strict)
pos = analyze((QQ(1), QQ(1)), (QQ(1), QQ(1)), [(QQ(0), QQ(1))],
              [QQ(2)], [QQ(1)])
checks["pos_lp_matches_corner"] = pos["lp_matches_corner"]
checks["pos_containment"] = pos["containment"]
checks["pos_joint_is_1_threehalves"] = pos["corner"] == (QQ(1), QQ(3) / 2)
checks["pos_product_is_half_3"] = pos["product"] == (QQ(1) / 2, QQ(3))
checks["pos_both_endpoints_strict"] = pos["strict_lower"] and pos["strict_upper"]

# (c) pinned signed instance: N=-2+s, D=2+s on [0,1] (both endpoints equal)
sgn = analyze((QQ(-2), QQ(-2)), (QQ(2), QQ(2)), [(QQ(0), QQ(1))],
              [QQ(1)], [QQ(1)])
checks["sgn_lp_matches_corner"] = sgn["lp_matches_corner"]
checks["sgn_containment"] = sgn["containment"]
checks["sgn_joint_is_m1_mthird"] = sgn["corner"] == (QQ(-1), QQ(-1) / 3)
checks["sgn_both_endpoints_equal"] = (not sgn["strict_lower"]
                                      and not sgn["strict_upper"])

status = "PASS" if all(bool(v) for v in checks.values()) else "FAIL"
print(json.dumps({
    "seal": "egs3.fractional_program.sage",
    "theorem_id": "T2G",
    "engine": "SageMath QQ + PPL exact LP (Charnes-Cooper)",
    "status": status,
    "checks": {k: bool(v) for k, v in checks.items()},
}))
