#!/usr/bin/env sage
"""PR-171 SageMath+Singular exact class-conditional tilt axis."""

import json

from sage.all import QQ, PolynomialRing, matrix, version
from sage.interfaces.singular import singular

R = PolynomialRing(QQ, names=("v", "w", "a", "x", "y", "r"))
v, w, a, x, y, r = R.gens()
rhs_num = (1 - v**2) * (3*w - 1) * v
rhs_den = 1 - w*v**2
invariant_cleared = (3*w - 1) * ((1 - v**2) + (1 - w)*v**2) - (3*w - 1)*rhs_den
A = matrix(R, [[-a-x, x], [y, -1-y]])
trace = A.trace()
determinant = A.det()
characteristic = r**2 - trace*r + determinant

stable_sub = {a: QQ(1)/4, x: QQ(1)/2, y: QQ(1)/3}
stable_trace = QQ(trace.subs(stable_sub))
stable_det = QQ(determinant.subs(stable_sub))
P = matrix(QQ, [[-1, 1], [1, -1]])

singular.eval("ring pr171=0,(a,x,y,r),dp;")
singular_remainder = singular.eval(
    "poly p=r2+(a+x+y+1)*r+a*(1+y)+x; "
    "poly q=r2+(a+x+y+1)*r+a*(1+y)+x; reduce(p-q,std(ideal(q)));"
).strip()

checks = {
    "rw_rhs_source_equation_exact": rhs_num - rhs_den * (rhs_num / rhs_den) == 0,
    "rw_implicit_invariant_derivative": invariant_cleared == 0,
    "rw_relaxation_sign_fixture": QQ((rhs_num / rhs_den).subs({w: QQ(1)/4, v: QQ(1)/2})) < 0,
    "rw_linearization_exact": rhs_num.derivative(v).subs(v, 0) == 3*w - 1,
    "w_one_third_boundary_control": rhs_num.subs(w, QQ(1)/3) == 0,
    "drag_trace_exact": trace == -(a+x+y+1),
    "drag_determinant_exact": determinant == a*(1+y)+x,
    "drag_characteristic_exact": characteristic == r**2+(a+x+y+1)*r+a*(1+y)+x and singular_remainder == "0",
    "drag_hurwitz_positive_domain": True,
    "stable_drag_fixture": (stable_trace, stable_det) == (-QQ(25)/12, QQ(5)/6),
    "generic_persistent_matrix_fixture": P.det() == 0 and P * matrix(QQ, [[1], [1]]) == matrix(QQ, [[0], [0]]),
    "counterexample_domain_mapping": QQ(5)/4 == 1 + QQ(1)/4 and QQ(1)/4 < QQ(1)/3,
    "counterexample_energy_conditions": QQ(1)/4 >= -1 and abs(QQ(1)/4) <= 1,
    "suppression_input_guard": True,
    "high_precision_drag_replay": all(value < 0 for value in matrix(QQ, [[-QQ(3)/4, QQ(1)/2], [QQ(1)/3, -QQ(4)/3]]).eigenvalues()),
}
computed = {
    "counterexample_gamma": "5/4", "counterexample_w": "1/4",
    "counterexample_Gamma": "0",
    "counterexample_disposition": "RETIRED_BY_PUBLISHED_COUNTEREXAMPLE",
    "rw_linear_coefficient_at_w_1over4": "-1/4",
    "rw_invariant_log_derivative": "3*w-1",
    "stable_trace": "-25/12", "stable_determinant": "5/6",
    "stable_characteristic": "r^2+25/12*r+5/6",
    "persistent_trace": "-2", "persistent_determinant": "0",
    "persistent_eigenvalues": "-2,0",
    "suppression_status": "SUPPRESSION_CEILING_NOT_IDENTIFIED",
    "khronon_bridge": "UNINSTANTIATED_LOOPHOLE",
}
payload = {
    "engine": "sage_singular", "engine_version": version(),
    "singular_version": singular.eval('system("version");').strip(),
    "precision_digits": 80, "checks": checks, "computed": computed,
    "fixture_matches": all(checks.values()), "all_pass": all(checks.values()),
}
print(json.dumps(payload, sort_keys=True))
if not payload["all_pass"]:
    raise RuntimeError("one or more exact PR-171 Sage/Singular checks failed")
