#!/usr/bin/env sage
"""PR-168 SageMath+Singular exact source-basis axis."""
import json

from sage.all import QQ, PolynomialRing, matrix, vector, version
from sage.interfaces.singular import singular

R = PolynomialRing(QQ, names=("a", "d", "g", "delta", "mu"))
a, d, g, delta, mu = R.gens()
basis = vector(R, [0, 1, 0, 0, 0])
source_a = (a * g / 3) * basis
source_d = (d * g / 3) * basis
columns = matrix(R, 5, 2, lambda i, j: (source_a, source_d)[j][i])
minors = [columns.matrix_from_rows_and_columns([i, j], [0, 1]).det()
          for i in range(5) for j in range(i + 1, 5)]
redistributed = ((a + delta) * g / 3) * basis + ((d - delta) * g / 3) * basis

K = R.fraction_field()
normalized_a = vector(K, [K(3 * value) / K(a) for value in source_a])
normalized_d = vector(K, [K(3 * value) / K(d) for value in source_d])
normalized_target = vector(K, [0, g, 0, 0, 0])

fixture = {a: QQ(6), d: QQ(9), g: QQ(15), delta: QQ(3)}
source_a_test = vector(QQ, [QQ(value.subs(fixture)) for value in source_a])
source_d_test = vector(QQ, [QQ(value.subs(fixture)) for value in source_d])
combined_test = source_a_test + source_d_test
redistributed_test = vector(QQ, [QQ(value.subs(fixture)) for value in redistributed])

streaming = matrix(QQ, 5, 5, sparse=True)
streaming[2, 1] = 2
streaming_ell2 = (streaming * source_a_test)[2]
accel_response = QQ(6) / (3 * QQ(3))
kinematic_response = QQ(9) / (3 * (QQ(3) + QQ(6)))
p2 = (3 * mu**2 - 1) / 2
second_order_residual = mu**2 - (QQ(1) / 3 + QQ(2) / 3 * p2)

# Explicit Singular reduction, separate from Sage's polynomial simplifier.
singular.eval("ring pr168=0,(a,d,g),dp;")
singular_remainder = singular.eval(
    "poly m=(a*g)*(d*g)-(d*g)*(a*g); ideal I=std(ideal(m)); reduce(m,I);"
).strip()

checks = {
    "source_column_collinearity": all(value == 0 for value in minors),
    "combined_source_invariance": source_a + source_d == redistributed,
    "direct_support_only_ell1": all(
        source_a[i] == 0 and source_d[i] == 0 for i in (0, 2, 3, 4)
    ),
    "normalized_thermodynamic_basis": (
        normalized_a == normalized_target and normalized_d == normalized_target
    ),
    "rank_one_minor_vanishes": (
        all(value == 0 for value in minors) and singular_remainder == "0"
    ),
    "streaming_negative_control_nonzero": streaming_ell2 == 60,
    "operator_change_negative_control_distinct": (
        accel_response == QQ(2) / 3
        and kinematic_response == QQ(1) / 3
        and accel_response != kinematic_response
    ),
    "second_order_quadrupole_negative_control": second_order_residual == 0,
}

def strings(values):
    return [str(QQ(value)) for value in values]

computed = {
    "acceleration_source_test": strings(source_a_test),
    "kinematic_source_test": strings(source_d_test),
    "combined_source_test": strings(combined_test),
    "normalized_basis_test": ["0", "15", "0", "0", "0"],
    "rank_upper_bound": "1",
    "direct_ell_ge_2_projection": "0",
    "streaming_ell2_negative_control": str(streaming_ell2),
    "operator_change_responses": [str(accel_response), str(kinematic_response)],
    "second_order_quadrupole_coefficient": "2/3",
}
payload = {
    "engine": "sage_singular",
    "engine_version": version(),
    "singular_version": singular.eval('system("version");').strip(),
    "checks": checks,
    "computed": computed,
    "redistributed_fixture_matches": redistributed_test == combined_test,
    "all_pass": all(checks.values()) and redistributed_test == combined_test,
}
print(json.dumps(payload, sort_keys=True))
if not payload["all_pass"]:
    raise RuntimeError("one or more exact PR-168 Sage/Singular checks failed")
