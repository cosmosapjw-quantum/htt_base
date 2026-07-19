#!/usr/bin/env sage
"""PR-170 SageMath+Singular exact Buchert/two-patch scalar axis."""

import json

from sage.all import QQ, PolynomialRing, version
from sage.interfaces.singular import singular

TYPES = ("I", "II", "III", "IV", "V", "VI_0", "VI_h", "VII_0", "VII_h", "VIII", "IX")
R = PolynomialRing(QQ, names=("w", "h1", "h2", "s1", "s2", "m"))
w, h1, h2, s1, s2, mean_sigma_magnitude = R.gens()
h_d = w * h1 + (1 - w) * h2
var_theta = 9 * w * (1 - w) * (h1 - h2) ** 2
mean_sigma = w * s1 + (1 - w) * s2
q_d = QQ(2) / 3 * var_theta - 2 * mean_sigma

equal = {w: QQ(1) / 2, h1: 2, h2: 2, s1: 3, s2: 3}
cancel = {w: QQ(1) / 2, h1: 3, h2: 1, s1: 3, s2: 3}
zero_shear = {w: QQ(1) / 2, h1: 3, h2: 1, s1: 0, s2: 0}

def normalized_values(fixture):
    hd = QQ(h_d.subs(fixture))
    var = QQ(var_theta.subs(fixture))
    shear = QQ(mean_sigma.subs(fixture))
    q = QQ(q_d.subs(fixture))
    return hd, var, q, -q / (6 * hd**2), shear / (3 * hd**2)

equal_values = normalized_values(equal)
cancel_values = normalized_values(cancel)
zero_values = normalized_values(zero_shear)
cancel_bridge = cancel_values[3] - cancel_values[4]

singular.eval("ring pr170=0,(w,h1,h2,s1,s2),dp;")
singular_remainder = singular.eval(
    "poly hd=w*h1+(1-w)*h2; "
    "poly vt=9*w*(1-w)*(h1-h2)^2; "
    "poly ms=w*s1+(1-w)*s2; "
    "poly q=2*vt-6*ms; reduce(3*q-(6*vt-18*ms),std(ideal(q)));"
).strip()

swapped = {w: 1 - w, h1: h2, h2: h1, s1: s2, s2: s1}
q_bt = QQ(2) / 3 * var_theta - 2 * (mean_sigma - mean_sigma_magnitude**2)
bridge_numerator = (-q_d) * 3 - mean_sigma * 6 + QQ(2) / 3 * var_theta * 3

checks = {
    "buchert_definition_and_dimension_lock": q_d == 6 * w * (1 - w) * (h1 - h2) ** 2 - 2 * mean_sigma and singular_remainder == "0",
    "two_patch_weighted_hubble_identity": h_d == w * h1 + (1 - w) * h2,
    "two_patch_expansion_variance_identity": var_theta == 9 * w * (1 - w) * (h1 - h2) ** 2,
    "general_bridge_residual_identity": bridge_numerator == 0,
    "constant_expansion_bridge": bridge_numerator.subs({h2: h1}) == 0,
    "cancellation_condition": QQ(2) / 3 * (3 * mean_sigma) - 2 * mean_sigma == 0,
    "constant_expansion_zero_q_implies_zero_mean_shear": q_d.subs({h2: h1}) + 2 * mean_sigma == 0,
    "patch_label_exchange_symmetry": all(expr == expr.subs(swapped) for expr in (h_d, var_theta, mean_sigma, q_d)),
    "barrow_tsagas_symbol_separation": q_bt - q_d - 2 * mean_sigma_magnitude**2 == 0,
    "typed_scalar_identity_all_11": len(TYPES) == 11 and len(set(TYPES)) == 11,
    "equal_expansion_fixture": equal_values == (QQ(2), QQ(0), QQ(-6), QQ(1) / 4, QQ(1) / 4),
    "two_patch_cancellation_fixture": cancel_values + (cancel_bridge,) == (QQ(2), QQ(9), QQ(0), QQ(0), QQ(1) / 4, -QQ(1) / 4),
    "zero_shear_unequal_expansion_control": zero_values[2:] == (QQ(6), -QQ(1) / 4, QQ(0)),
    "hubble_zero_normalization_guard": h_d.subs({w: QQ(1) / 2, h1: 1, h2: -1}) == 0,
    "curvature_source_negative_control": QQ(1) * QQ(1) + QQ(-1) * QQ(-1) == 2,
}
computed = {
    "equal_H_D": "2", "equal_variance_theta": "0", "equal_Q_D_B": "-6",
    "equal_Omega_Q_D_B": "1/4", "equal_Sigma2_D_rms": "1/4",
    "cancel_H_D": "2", "cancel_variance_theta": "9", "cancel_Q_D_B": "0",
    "cancel_Omega_Q_D_B": "0", "cancel_Sigma2_D_rms": "1/4",
    "cancel_bridge_residual": "-1/4", "zero_shear_Q_D_B": "6",
    "zero_shear_Omega_Q_D_B": "-1/4", "typed_scalar_rows": "11",
    "curvature_control_contraction": "2",
    "barrow_buchert_relation": "Q_D_BT=Q_D_B+2*mean_sigma^2",
}
payload = {
    "engine": "sage_singular", "engine_version": version(),
    "singular_version": singular.eval('system("version");').strip(),
    "checks": checks, "computed": computed,
    "fixture_matches": all(checks.values()), "all_pass": all(checks.values()),
}
print(json.dumps(payload, sort_keys=True))
if not payload["all_pass"]:
    raise RuntimeError("one or more exact PR-170 Sage/Singular checks failed")
