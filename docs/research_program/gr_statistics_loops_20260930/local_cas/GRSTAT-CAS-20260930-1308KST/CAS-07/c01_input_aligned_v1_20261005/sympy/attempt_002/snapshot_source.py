"""Independent exact SymPy check of the frozen CAS-07-C01 scalar component."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import sympy as sp


ROOT = Path(__file__).resolve().parents[8]
BASE = Path(__file__).resolve().parent.parent
INPUTS = {
    "contract": (
        BASE / "EXECUTION_CONTRACT.json",
        "e5342381440cb6456ad27add75a9d23faa52a01b1a0f5998599e3026452a9f1a",
    ),
    "admitted_inputs": (
        BASE / "ADMITTED_INPUTS.json",
        "30bbb6fce513eedfd98a693c2acbf3308363a7098a7938f4b5abf7e9282b2e39",
    ),
    "common_spec": (
        ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md",
        "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    ),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    observed = {name: digest(path) for name, (path, _) in INPUTS.items()}
    expected = {name: value for name, (_, value) in INPUTS.items()}
    if observed != expected:
        print(json.dumps({"error": "frozen_input_mismatch", "expected": expected,
                          "observed": observed}, sort_keys=True))
        return 2

    K = sp.symbols("Kc", positive=True, real=True)
    s, t = sp.symbols("s t", nonnegative=True, real=True)
    f = sp.sinh(sp.sqrt(K) * s) / sp.sqrt(K)
    ft = sp.sinh(sp.sqrt(K) * t) / sp.sqrt(K)

    at_origin = sp.simplify(f.subs(s, 0))
    first = sp.diff(f, s)
    first_origin = sp.simplify(first.subs(s, 0))
    second = sp.diff(f, s, 2)
    ode_residual = sp.simplify(second - K * f)

    actual_integral = sp.integrate((s - t) * ft, (t, 0, s))
    integral_residual = sp.simplify(K * actual_integral - (f - s))
    integral_closed_form_residual = sp.simplify(
        actual_integral - (f - s) / K
    )

    flat_f = s
    flat_origin = flat_f.subs(s, 0)
    flat_first_origin = sp.diff(flat_f, s).subs(s, 0)
    flat_second = sp.diff(flat_f, s, 2)
    right_limit = sp.limit(f, K, 0, dir="+")
    flat_ft = flat_f.subs(s, t)
    flat_integrand = (s - t) * flat_ft
    flat_actual_integral = sp.integrate(flat_integrand, (t, 0, s))
    flat_integral_residual = sp.simplify(
        sp.Integer(0) * flat_actual_integral - (flat_f - s)
    )

    subchecks = {
        "positive_branch_at_origin": at_origin == 0,
        "positive_branch_first_derivative_at_origin": first_origin == 1,
        "positive_branch_ode": ode_residual == 0,
        "actual_interval_integral": integral_residual == 0,
        "integral_closed_form": integral_closed_form_residual == 0,
        "flat_origin": flat_origin == 0,
        "flat_first_derivative_at_origin": flat_first_origin == 1,
        "flat_second_derivative": flat_second == 0,
        "flat_unscaled_integral": sp.simplify(flat_actual_integral - s**3 / 6) == 0,
        "flat_integral_identity": flat_integral_residual == 0,
        "fixed_s_positive_Kc_right_limit": sp.simplify(right_limit - flat_f) == 0,
    }
    output = {
        "axis": "sympy",
        "component": "CAS-07-C01",
        "checks": {"CAS-07-C01": bool(all(subchecks.values()))},
        "subchecks": {key: bool(value) for key, value in subchecks.items()},
        "domain_assumption_diff": [],
        "counterexample": None,
        "witness": None,
        "assumptions": "Kc real > 0; s,t real with s >= 0 and 0 <= t <= s on interval; principal positive sqrt(Kc); Kc=0 handled separately; fixed-s right limit",
        "units": "s,t,f length; Kc inverse length squared; sqrt(Kc)*s dimensionless; f' dimensionless; f'' inverse length",
        "expressions": {
            "f": str(f),
            "first_derivative": str(first),
            "second_derivative": str(second),
            "integral_evaluated": str(actual_integral),
            "right_limit": str(right_limit),
            "flat_f": str(flat_f),
            "flat_ft": str(flat_ft),
            "flat_integrand": str(flat_integrand),
            "flat_integral_evaluated": str(flat_actual_integral),
            "residuals": {
                "ode": str(ode_residual),
                "integral": str(integral_residual),
                "integral_closed_form": str(integral_closed_form_residual),
                "flat_integral": str(flat_integral_residual),
            },
        },
        "engine": {"python": sys.version, "sympy": sp.__version__,
                   "sympy_file": sp.__file__},
        "input_sha256": observed,
        "evidence_class": "exact",
        "scope": "Only full explicit CAS-07-C01 scalar identities; no C02/C03, Jacobi majorization/existence, physical distance inference, or scientific admission",
    }
    print(json.dumps(output, sort_keys=True))
    return 0 if output["checks"]["CAS-07-C01"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
