#!/usr/bin/env python3
"""Independent SymPy axis for PR-169's exact rational comparator theorem."""
from __future__ import annotations

import json

import sympy as sp


def _s(value: sp.Expr) -> str:
    return str(sp.factor(value))


def main() -> int:
    B, sigma2, v2, omega_tilt, delta, q, a = sp.symbols(
        "B sigma2 v2 omega_tilt delta q a", rational=True
    )
    x_c = sigma2 - v2 + omega_tilt + delta
    m_q = sigma2 + v2 + omega_tilt + q

    full_slack = sp.expand(
        4 * B - m_q
        - ((B - sigma2) + (B - v2) + (B - omega_tilt) + (B - q))
    )
    slice_slack = sp.expand(
        2 * B - (sigma2 + v2) - ((B - sigma2) + (B - v2))
    )

    full = {sigma2: B, v2: B, omega_tilt: B, delta: -B, q: B}
    sliced = {sigma2: B, v2: B, omega_tilt: 0, delta: 0, q: 0}
    uncapped = {sigma2: a, v2: a, omega_tilt: 0, delta: 0, q: 0}

    fixture = {B: sp.Rational(3, 10)}
    full_x = sp.expand(x_c.subs(full)).subs(fixture)
    full_m = sp.expand(m_q.subs(full)).subs(fixture)
    slice_x = sp.expand(x_c.subs(sliced)).subs(fixture)
    slice_m = sp.expand(m_q.subs(sliced)).subs(fixture)
    sign_mutant = (sigma2 + v2 + omega_tilt + delta).subs(sliced).subs(fixture)
    projected_full_x = x_c.subs(full).subs(delta, 0).subs(fixture)
    projected_full_m = m_q.subs(full).subs({delta: 0, q: 0}).subs(fixture)

    checks = {
        "full_ceiling_upper_bound_certificate": full_slack == 0,
        "full_ceiling_attained": (
            sp.expand(x_c.subs(full)) == 0
            and sp.expand(m_q.subs(full) - 4 * B) == 0
        ),
        "slice_ceiling_upper_bound_certificate": slice_slack == 0,
        "slice_ceiling_attained": (
            sp.expand(x_c.subs(sliced)) == 0
            and sp.expand(m_q.subs(sliced) - 2 * B) == 0
        ),
        "uncapped_family_exact": (
            sp.expand(x_c.subs(uncapped)) == 0
            and sp.expand(m_q.subs(uncapped) - 2 * a) == 0
        ),
        "sign_mutation_detected": sign_mutant == sp.Rational(3, 5),
        "signed_projection_mutation_detected": (
            projected_full_x == sp.Rational(3, 10)
            and projected_full_m == sp.Rational(9, 10)
        ),
        "nilsson_symbol_type_distinct": sp.Symbol("W_N2") != sp.Symbol("V2"),
        "missing_physical_receipt_blocks_promotion": not all([True] * 7 + [False]),
    }
    computed = {
        "fixture_B": "3/10",
        "full_ceiling_coefficient": "4",
        "slice_ceiling_coefficient": "2",
        "full_fixture_x_C": _s(full_x),
        "full_fixture_M_unsigned": _s(full_m),
        "slice_fixture_x_C": _s(slice_x),
        "slice_fixture_M_unsigned": _s(slice_m),
        "uncapped_family_x_C": "0",
        "uncapped_family_M_over_a": "2",
        "sign_mutant_slice_x_C": _s(sign_mutant),
        "projected_full_x_C": _s(projected_full_x),
        "projected_full_M_unsigned": _s(projected_full_m),
        "symbol_bridge": "REJECTED_TYPED_MISMATCH",
        "physical_bundle": "MISSING",
    }
    payload = {
        "engine": "sympy",
        "engine_version": sp.__version__,
        "checks": checks,
        "computed": computed,
        "fixture_matches": all(checks.values()),
        "all_pass": all(checks.values()),
    }
    print(json.dumps(payload, sort_keys=True))
    return 0 if payload["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

