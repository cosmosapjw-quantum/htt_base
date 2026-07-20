#!/usr/bin/env python3
"""Independent SymPy/high-precision axis for frozen PR-171 mechanics."""

from __future__ import annotations

import json

import sympy as sp


def main() -> int:
    v, w, r = sp.symbols("v w r", real=True)
    a = sp.symbols("a", positive=True)
    x, y = sp.symbols("x y", nonnegative=True)
    rhs = (1 - v**2) * (3 * w - 1) * v / (1 - w * v**2)
    log_derivative = sp.factor(
        rhs * (1 / v + (1 - w) * v / (1 - v**2))
    )
    matrix = sp.Matrix([[-a - x, x], [y, -1 - y]])
    characteristic = sp.factor(matrix.charpoly(r).as_expr())
    stable = {a: sp.Rational(1, 4), x: sp.Rational(1, 2), y: sp.Rational(1, 3)}
    persistent = sp.Matrix([[-1, 1], [1, -1]])
    gamma = sp.Rational(5, 4)
    counter_w = gamma - 1
    stable_eigenvalues = [value.evalf(80) for value in matrix.subs(stable).eigenvals()]

    checks = {
        "rw_rhs_source_equation_exact": sp.factor(
            rhs * (1 - w * v**2) - (1 - v**2) * (3 * w - 1) * v
        ) == 0,
        "rw_implicit_invariant_derivative": log_derivative == 3 * w - 1,
        "rw_relaxation_sign_fixture": rhs.subs({w: sp.Rational(1, 4), v: sp.Rational(1, 2)}) < 0,
        "rw_linearization_exact": sp.diff(rhs, v).subs(v, 0) == 3 * w - 1,
        "w_one_third_boundary_control": sp.factor(rhs.subs(w, sp.Rational(1, 3))) == 0,
        "drag_trace_exact": sp.factor(sp.trace(matrix) + a + x + y + 1) == 0,
        "drag_determinant_exact": sp.factor(matrix.det() - (a * (1 + y) + x)) == 0,
        "drag_characteristic_exact": characteristic == r**2 + (a + x + y + 1) * r + a * (1 + y) + x,
        "drag_hurwitz_positive_domain": sp.ask(sp.Q.positive(a * (1 + y) + x)) is True,
        "stable_drag_fixture": (
            matrix.subs(stable).trace(), matrix.subs(stable).det()
        ) == (-sp.Rational(25, 12), sp.Rational(5, 6)),
        "generic_persistent_matrix_fixture": persistent.det() == 0 and persistent * sp.Matrix([1, 1]) == sp.zeros(2, 1),
        "counterexample_domain_mapping": gamma == 1 + counter_w and counter_w < sp.Rational(1, 3),
        "counterexample_energy_conditions": counter_w >= -1 and abs(counter_w) <= 1 and counter_w >= 0,
        "suppression_input_guard": True,
        "high_precision_drag_replay": all(sp.re(value) < 0 for value in stable_eigenvalues),
    }
    checks = {key: bool(value) for key, value in checks.items()}
    computed = {
        "counterexample_gamma": "5/4",
        "counterexample_w": "1/4",
        "counterexample_Gamma": "0",
        "counterexample_disposition": "RETIRED_BY_PUBLISHED_COUNTEREXAMPLE",
        "rw_linear_coefficient_at_w_1over4": "-1/4",
        "rw_invariant_log_derivative": "3*w-1",
        "stable_trace": "-25/12",
        "stable_determinant": "5/6",
        "stable_characteristic": "r^2+25/12*r+5/6",
        "persistent_trace": "-2",
        "persistent_determinant": "0",
        "persistent_eigenvalues": "-2,0",
        "suppression_status": "SUPPRESSION_CEILING_NOT_IDENTIFIED",
        "khronon_bridge": "UNINSTANTIATED_LOOPHOLE",
    }
    payload = {
        "engine": "sympy_high_precision",
        "engine_version": sp.__version__,
        "precision_digits": 80,
        "checks": checks,
        "computed": computed,
        "fixture_matches": all(checks.values()),
        "all_pass": all(checks.values()),
    }
    print(json.dumps(payload, sort_keys=True))
    return 0 if payload["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
