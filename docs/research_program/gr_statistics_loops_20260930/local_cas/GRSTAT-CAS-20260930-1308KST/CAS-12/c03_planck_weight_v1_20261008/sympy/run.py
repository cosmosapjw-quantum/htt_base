#!/usr/bin/env python3
"""Independent SymPy verification of the frozen CAS-12-C03 component."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import sympy as sp


ROOT = Path(__file__).resolve().parents[8]
COMPONENT = Path(__file__).resolve().parent.parent
CONTRACT = COMPONENT / "EXECUTION_CONTRACT.json"
INPUTS = COMPONENT / "ADMITTED_INPUTS.json"
COMMON = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
RESULT = Path(__file__).resolve().parent / "axis_result.json"
EXPECTED_HASHES = {
    CONTRACT: "1950de303557d1b805f17a45dc478011bd24e73f06f5444b2ebf9cc3ce06c4a4",
    INPUTS: "22967352d8773a6324fc413d0da748081af52b1a63907af1f3d80119438a2a63",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    contract_hashes = {str(path.relative_to(ROOT)): sha256(path) for path in EXPECTED_HASHES}
    hash_ok = all(sha256(path) == expected for path, expected in EXPECTED_HASHES.items())
    contract = json.loads(CONTRACT.read_text())
    admitted = json.loads(INPUTS.read_text())
    domain_diff: list[str] = []
    if not hash_ok:
        domain_diff.append("frozen input hash mismatch")
    if contract["semantics"]["symbol_type_domain_map"] != admitted["definitions"]:
        domain_diff.append("symbol/domain definition mismatch")
    if contract["semantics"]["frame_signature_units_conventions"]["limit_direction"] != "right":
        domain_diff.append("limit direction mismatch")
    if admitted["domain_branch_units"]["E_original_domain"] != "E>0":
        domain_diff.append("original-domain mismatch")
    if admitted["domain_branch_units"]["b_positive"] is not True:
        domain_diff.append("b positivity mismatch")

    x = sp.Symbol("x", real=True)
    E = sp.Symbol("E", real=True, positive=True)
    b = sp.Symbol("b", real=True, positive=True)
    numerator = sp.exp(x)
    denominator = (sp.exp(x) - 1) ** 2
    weight = numerator / denominator
    hyperbolic = 1 / (4 * sp.sinh(x / 2) ** 2)
    candidate = x ** -2 - sp.Rational(1, 12) + x**2 / 240 - x**4 / 6048

    # The exponential identity and nonzero denominator on b>0,E>0 establish
    # equality on the original domain. No quotient is evaluated at E=0.
    exp_sinh_factor = sp.simplify((sp.exp(x) - 1 - 2 * sp.exp(x / 2) * sp.sinh(x / 2)).rewrite(sp.exp))
    identity_zero = sp.simplify(sp.together((weight - hyperbolic).rewrite(sp.exp)))
    identity_ok = exp_sinh_factor == 0 and identity_zero == 0

    series = sp.series(weight, x, 0, 6)
    series_poly = sp.expand(series.removeO())
    powers = (-2, -1, 0, 1, 2, 3, 4, 5)
    coefficients = {str(power): sp.sstr(series_poly.coeff(x, power)) for power in powers}
    expected_coefficients = {
        "-2": "1", "-1": "0", "0": "-1/12", "1": "0",
        "2": "1/240", "3": "0", "4": "-1/6048", "5": "0",
    }
    coefficients_ok = coefficients == expected_coefficients and sp.simplify(series_poly - candidate) == 0

    # Clearing the double zero of the denominator raises O(x^6) to O(x^8).
    product_residual = sp.expand(candidate * denominator - numerator)
    cleared_series = sp.series(product_residual, x, 0, 8)
    residual_ok = cleared_series.removeO().expand() == 0 and cleared_series.getO() == sp.Order(x**8, x)
    residual_leading = sp.simplify(sp.limit(product_residual / x**8, x, 0))

    energy_weight = weight.subs(x, b * E)
    formal_scaled = sp.series(E**2 * energy_weight, E, 0, 1).removeO()
    formal_ok = sp.simplify(formal_scaled - b**-2) == 0
    right_limit = sp.limit(E**2 * energy_weight, E, 0, dir="+")
    limit_ok = sp.simplify(right_limit - b**-2) == 0

    diagnostics = []
    abs_tol = sp.Float("1e-50", 80)
    rel_tol = sp.Float("1e-40", 80)
    numeric_ok = True
    for b_value, e_value in [(sp.Integer(1), sp.Rational(1, 10)), (sp.Integer(2), sp.Rational(1, 100))]:
        x_value = b_value * e_value
        direct = weight.subs(x, x_value).evalf(80)
        via_sinh = hyperbolic.subs(x, x_value).evalf(80)
        difference = abs((direct - via_sinh).evalf(80))
        tolerance = max(abs_tol, rel_tol * max(abs(direct), abs(via_sinh)))
        vector_ok = bool(difference <= tolerance)
        numeric_ok = numeric_ok and vector_ok
        laurent = candidate.subs(x, x_value).evalf(80)
        diagnostics.append({
            "b": str(b_value),
            "E": sp.sstr(e_value),
            "x": sp.sstr(x_value),
            "weight_exp_80d": str(direct),
            "weight_sinh_80d": str(via_sinh),
            "identity_abs_difference_80d": str(difference),
            "identity_tolerance_80d": str(tolerance),
            "identity_within_tolerance": vector_ok,
            "laurent_truncation_abs_difference_80d": str(abs((direct - laurent).evalf(80))),
        })

    subchecks = {
        "frozen_hashes": hash_ok,
        "domain_alignment": not domain_diff,
        "exact_exp_sinh_identity": identity_ok,
        "exact_laurent_coefficients_through_E4": coefficients_ok,
        "cleared_product_residual_O_x8": residual_ok,
        "formal_scaled_leading_coefficient": formal_ok,
        "analytic_right_limit": limit_ok,
        "numeric_80_digit_diagnostics": numeric_ok,
    }
    passed = all(subchecks.values())
    exit_code = 0 if passed else 1
    source_path = Path(__file__).resolve()
    executable_path = Path(sys.executable).resolve()
    result = {
        "axis": "sympy",
        "status": "PASS" if passed else "FAIL",
        "contract_sha256": sha256(CONTRACT),
        "evidence_class": "exact",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "component": "CAS-12-C03",
        "claim_ceiling": contract["identity"]["claim_ceiling"],
        "checks": {"CAS-12-C03": passed},
        "subchecks": subchecks,
        "domain_assumption_diff": domain_diff,
        "counterexample": None if passed else "See failed subchecks and raw evidence",
        "commands": [{
            "argv": sys.orig_argv,
            "exit_code": exit_code,
            "cwd": str(Path.cwd()),
        }],
        "tool_versions": {
            "sympy": sp.__version__,
            "python": platform.python_version(),
            "python_implementation": platform.python_implementation(),
        },
        "executable_artifacts": {
            "python_executable": {"path": str(executable_path), "sha256": sha256(executable_path)},
            "source": {"path": str(source_path), "sha256": sha256(source_path)},
            "sympy_module": {"path": str(Path(sp.__file__).resolve()), "sha256": sha256(Path(sp.__file__).resolve())},
        },
        "source_input_hashes": contract_hashes,
        "mathematical_evidence": {
            "exp_sinh_factor_residual": sp.sstr(exp_sinh_factor),
            "exact_identity_residual": sp.sstr(identity_zero),
            "series_in_x": sp.sstr(series),
            "coefficients_in_x": coefficients,
            "candidate_in_E": sp.sstr(candidate.subs(x, b * E)),
            "cleared_product_residual_series": sp.sstr(cleared_series),
            "cleared_product_x8_coefficient": sp.sstr(residual_leading),
            "formal_E2W_constant": sp.sstr(formal_scaled),
            "analytic_right_limit": sp.sstr(right_limit),
        },
        "numeric_diagnostics": diagnostics,
        "raw_logs": {"stdout": "stdout.log", "stderr": "stderr.log", "exit_code": "exit_code.txt"},
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "checks": {"CAS-12-C03": passed},
        "domain_assumption_diff": domain_diff,
        "counterexample": None if passed else "See failed subchecks and raw evidence",
    }, separators=(",", ":")))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
