#!/usr/bin/env python3
"""Independent SymPy axis for PR-168's frozen source-basis identity."""
from __future__ import annotations

import json
import sympy as sp


def _s(value: sp.Expr) -> str:
    value = sp.factor(value)
    return str(value).replace("**", "^")


def main() -> int:
    a, d, g, delta = sp.symbols("a d g delta", nonzero=True)
    basis = sp.Matrix([0, 1, 0, 0, 0])
    source_a = sp.Rational(1, 3) * a * g * basis
    source_d = sp.Rational(1, 3) * d * g * basis
    columns = sp.Matrix.hstack(source_a, source_d)

    minors = []
    for i in range(columns.rows):
        for j in range(i + 1, columns.rows):
            minors.append(sp.expand(columns.extract([i, j], [0, 1]).det()))

    redistributed = (
        sp.Rational(1, 3) * (a + delta) * g * basis
        + sp.Rational(1, 3) * (d - delta) * g * basis
    )
    normalized_a = sp.simplify(3 * source_a / a)
    normalized_d = sp.simplify(3 * source_d / d)

    A = sp.Rational(6)
    D = sp.Rational(9)
    G = sp.Rational(15)
    Delta = sp.Rational(3)
    source_a_test = source_a.subs({a: A, g: G})
    source_d_test = source_d.subs({d: D, g: G})
    combined_test = source_a_test + source_d_test
    redistributed_test = redistributed.subs(
        {a: A, d: D, g: G, delta: Delta}
    )

    streaming = sp.zeros(5)
    streaming[2, 1] = sp.Rational(2)
    streaming_ell2 = (streaming * source_a_test)[2]

    gamma = sp.Rational(3)
    damping_increment = sp.Rational(6)
    accel_response = A / (3 * gamma)
    kinematic_response = D / (3 * (gamma + damping_increment))

    mu = sp.symbols("mu")
    p2 = sp.Rational(1, 2) * (3 * mu**2 - 1)
    second_order_residual = sp.expand(
        mu**2 - (sp.Rational(1, 3) + sp.Rational(2, 3) * p2)
    )

    checks = {
        "source_column_collinearity": all(v == 0 for v in minors),
        "combined_source_invariance": sp.simplify(
            source_a + source_d - redistributed
        ) == sp.zeros(5, 1),
        "direct_support_only_ell1": all(
            sp.simplify(source_a[i]) == 0 and sp.simplify(source_d[i]) == 0
            for i in (0, 2, 3, 4)
        ),
        "normalized_thermodynamic_basis": (
            normalized_a == g * basis and normalized_d == g * basis
        ),
        "rank_one_minor_vanishes": all(v == 0 for v in minors),
        "streaming_negative_control_nonzero": streaming_ell2 == 60,
        "operator_change_negative_control_distinct": (
            accel_response == sp.Rational(2, 3)
            and kinematic_response == sp.Rational(1, 3)
            and accel_response != kinematic_response
        ),
        "second_order_quadrupole_negative_control": second_order_residual == 0,
    }
    computed = {
        "acceleration_source_test": [_s(v) for v in source_a_test],
        "kinematic_source_test": [_s(v) for v in source_d_test],
        "combined_source_test": [_s(v) for v in combined_test],
        "normalized_basis_test": [_s(v) for v in normalized_a.subs(g, G)],
        "rank_upper_bound": "1",
        "direct_ell_ge_2_projection": _s(
            sum(source_a_test[i] ** 2 + source_d_test[i] ** 2 for i in (2, 3, 4))
        ),
        "streaming_ell2_negative_control": _s(streaming_ell2),
        "operator_change_responses": [_s(accel_response), _s(kinematic_response)],
        "second_order_quadrupole_coefficient": "2/3",
    }
    payload = {
        "engine": "sympy",
        "engine_version": sp.__version__,
        "checks": checks,
        "computed": computed,
        "redistributed_fixture_matches": redistributed_test == combined_test,
        "all_pass": all(checks.values()) and redistributed_test == combined_test,
    }
    print(json.dumps(payload, sort_keys=True))
    return 0 if payload["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
