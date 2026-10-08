#!/usr/bin/python3.12
"""Independent SymPy check for the admitted CAS-13-C01 power jet."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import sympy as sp


REPO = Path(__file__).resolve().parents[8]
SOURCES = {
    "docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-13/c01_power_jet_v1_20261008/EXECUTION_CONTRACT.json": "a603f1f31004a278095ea6ec4523aff77789bd3c5cf58fa74ee51033b566c638",
    "docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-13/c01_power_jet_v1_20261008/ADMITTED_INPUTS.json": "6e29ae54d7e065d784ddf673958b8c9b56a1ebe5532e5a4d8d05aca6f588fa3a",
    "docs/research_program/gr_statistics_loops_20260930/cas/TEFF_INTERVAL_SPEC.md": "bc055d391d3231c634a14e146f228d3b8179a043485c41ce08754cdeac4fd0fe",
    "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md": "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}


def main() -> int:
    if len(sys.argv) != 1:
        raise SystemExit("CAS-13-C01 takes no arguments")
    source_hashes = {
        path: hashlib.sha256((REPO / path).read_bytes()).hexdigest()
        for path in SOURCES
    }
    source_binding = source_hashes == SOURCES

    p = sp.Symbol("p", real=True)
    y = sp.Symbol("y", positive=True, real=True)
    t = sp.Symbol("t", positive=True, real=True)
    c0 = (p - 3) * (p - 4) / 12
    c3 = p * (4 - p) / 3
    c4 = p * (p - 3) / 4
    q = c0 + c3 * y**3 + c4 * y**4
    psi = y**p  # Positive y fixes the real branch exp(p log y).

    jets = []
    expected_jets = [sp.Integer(1), p, p * (p - 1)]
    for order, expected in enumerate(expected_jets):
        psi_jet = sp.diff(psi, y, order).subs(y, 1)
        q_jet = sp.diff(q, y, order).subs(y, 1)
        jets.append({
            "order": order,
            "psi": str(sp.factor(psi_jet)),
            "q": str(sp.factor(q_jet)),
            "expected": str(expected),
            "exact": bool(sp.simplify(psi_jet - expected) == 0 and sp.simplify(q_jet - expected) == 0),
        })

    q_third = sp.diff(q, y, 3)
    expected_q_third = 2 * p * (4 - p) + 6 * p * (p - 3) * y
    mismatch = sp.diff(psi, y, 3) - q_third
    expected_mismatch = (
        p * (p - 1) * (p - 2) * y ** (p - 3)
        - 2 * p * (4 - p) - 6 * p * (p - 3) * y
    )
    unit_mismatch = sp.factor(mismatch.subs(y, 1))
    expected_unit = p * (p - 3) * (p - 4)
    positive_shift = sp.factor(unit_mismatch.subs(p, t + 4))
    positivity = bool(sp.ask(sp.Q.positive(positive_shift)))

    vectors = []
    for pv, yv in [(sp.Integer(5), sp.Rational(4, 5)), (sp.Integer(6), sp.Rational(6, 5))]:
        direct = sp.diff(psi, y, 3).subs({p: pv, y: yv}) - sp.diff(q, y, 3).subs({p: pv, y: yv})
        formula = expected_mismatch.subs({p: pv, y: yv})
        decimal_direct = sp.N(direct, 80)
        decimal_formula = sp.N(formula, 80)
        residual = abs(decimal_direct - decimal_formula)
        threshold = sp.Float("1e-50", 80) + sp.Float("1e-40", 80) * abs(decimal_formula)
        vectors.append({
            "p": str(pv), "y": str(yv),
            "direct_exact": str(direct), "formula_exact": str(formula),
            "direct_80d": str(decimal_direct), "formula_80d": str(decimal_formula),
            "residual_80d": str(residual), "threshold_80d": str(threshold),
            "exact_equal": bool(sp.simplify(direct - formula) == 0),
            "within_tolerance": bool(residual <= threshold),
        })

    detailed_checks = {
        "source_binding": source_binding,
        "positive_real_branch": sp.simplify(psi - sp.exp(p * sp.log(y))) == 0,
        "three_jets": all(jet["exact"] for jet in jets),
        "q_third": sp.simplify(q_third - expected_q_third) == 0,
        "full_mismatch": sp.simplify(mismatch - expected_mismatch) == 0,
        "unit_factorization": sp.simplify(unit_mismatch - expected_unit) == 0,
        "unit_positive_p_gt_4": positivity,
        "numeric_controls": all(v["exact_equal"] and v["within_tolerance"] for v in vectors),
    }
    passed = all(bool(value) for value in detailed_checks.values())
    payload = {
        "axis": "sympy",
        "tool_version": sp.__version__,
        "checks": {"CAS-13-C01": passed},
        "domain_assumption_diff": [],
        "counterexample": None,
        "source_hashes": source_hashes,
        "domain": {"p": "real p>4", "y": "real y>0", "power_branch": "exp(p log y)", "units": "dimensionless"},
        "detailed_checks": detailed_checks,
        "jets_at_one": jets,
        "q_third": str(sp.expand(q_third)),
        "mismatch": str(sp.expand(mismatch)),
        "unit_mismatch": str(unit_mismatch),
        "positive_shift_p_eq_4_plus_t": str(positive_shift),
        "numeric_controls": vectors,
        "scope": "admitted CAS-13-C01 power-response jet only",
    }
    print(json.dumps(payload, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
