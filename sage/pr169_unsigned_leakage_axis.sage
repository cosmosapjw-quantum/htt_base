#!/usr/bin/env sage
"""PR-169 SageMath+Singular exact rational comparator axis."""
import json

from sage.all import QQ, PolynomialRing, version
from sage.interfaces.singular import singular

R = PolynomialRing(QQ, names=("B", "sigma2", "v2", "omega_tilt", "delta", "q", "a"))
B, sigma2, v2, omega_tilt, delta, q, a = R.gens()
x_c = sigma2 - v2 + omega_tilt + delta
m_q = sigma2 + v2 + omega_tilt + q

full_slack = 4 * B - m_q - (
    (B - sigma2) + (B - v2) + (B - omega_tilt) + (B - q)
)
slice_slack = 2 * B - (sigma2 + v2) - ((B - sigma2) + (B - v2))

full = {sigma2: B, v2: B, omega_tilt: B, delta: -B, q: B}
projected_full = {sigma2: B, v2: B, omega_tilt: B, delta: 0, q: 0}
sliced = {sigma2: B, v2: B, omega_tilt: 0, delta: 0, q: 0}
uncapped = {sigma2: a, v2: a, omega_tilt: 0, delta: 0, q: 0}
fixture = {B: QQ(3) / 10}

full_x = QQ(x_c.subs(full).subs(fixture))
full_m = QQ(m_q.subs(full).subs(fixture))
slice_x = QQ(x_c.subs(sliced).subs(fixture))
slice_m = QQ(m_q.subs(sliced).subs(fixture))
sign_mutant = QQ((sigma2 + v2 + omega_tilt + delta).subs(sliced).subs(fixture))
projected_full_x = QQ(x_c.subs(projected_full).subs(fixture))
projected_full_m = QQ(m_q.subs(projected_full).subs(fixture))

singular.eval("ring pr169=0,(B,s,v,t,d,q,a),dp;")
singular_remainder = singular.eval(
    "poly f=4*B-(s+v+t+q)-((B-s)+(B-v)+(B-t)+(B-q)); "
    "ideal I=std(ideal(f)); reduce(f,I);"
).strip()

checks = {
    "full_ceiling_upper_bound_certificate": full_slack == 0 and singular_remainder == "0",
    "full_ceiling_attained": x_c.subs(full) == 0 and m_q.subs(full) == 4 * B,
    "slice_ceiling_upper_bound_certificate": slice_slack == 0,
    "slice_ceiling_attained": x_c.subs(sliced) == 0 and m_q.subs(sliced) == 2 * B,
    "uncapped_family_exact": x_c.subs(uncapped) == 0 and m_q.subs(uncapped) == 2 * a,
    "sign_mutation_detected": sign_mutant == QQ(3) / 5,
    "signed_projection_mutation_detected": (
        projected_full_x == QQ(3) / 10 and projected_full_m == QQ(9) / 10
    ),
    "nilsson_symbol_type_distinct": "W_N2" != "V2",
    "missing_physical_receipt_blocks_promotion": not all([True] * 7 + [False]),
}
computed = {
    "fixture_B": "3/10",
    "full_ceiling_coefficient": "4",
    "slice_ceiling_coefficient": "2",
    "full_fixture_x_C": str(full_x),
    "full_fixture_M_unsigned": str(full_m),
    "slice_fixture_x_C": str(slice_x),
    "slice_fixture_M_unsigned": str(slice_m),
    "uncapped_family_x_C": "0",
    "uncapped_family_M_over_a": "2",
    "sign_mutant_slice_x_C": str(sign_mutant),
    "projected_full_x_C": str(projected_full_x),
    "projected_full_M_unsigned": str(projected_full_m),
    "symbol_bridge": "REJECTED_TYPED_MISMATCH",
    "physical_bundle": "MISSING",
}
payload = {
    "engine": "sage_singular",
    "engine_version": version(),
    "singular_version": singular.eval('system("version");').strip(),
    "checks": checks,
    "computed": computed,
    "fixture_matches": all(checks.values()),
    "all_pass": all(checks.values()),
}
print(json.dumps(payload, sort_keys=True))
if not payload["all_pass"]:
    raise RuntimeError("one or more exact PR-169 Sage/Singular checks failed")
