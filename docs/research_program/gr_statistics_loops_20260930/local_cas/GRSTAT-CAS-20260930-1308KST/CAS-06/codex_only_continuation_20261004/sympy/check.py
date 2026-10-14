"""Independent SymPy check of the contracted positive-real scalar calculus."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import sympy as sp
from sympy.assumptions import Q, ask


TARGET = "CAS-06-C03-SCALAR"
CONTRACT_SHA256 = "7742ee4abac523eabc466435f115de88228a957a3dbed946fa5311f99ab07c27"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_zero(expr):
    return sp.cancel(sp.simplify(expr)) == 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    args = parser.parse_args()
    contract_path = args.contract.resolve()
    repo_root = args.repo_root.resolve()
    contract = json.loads(contract_path.read_text())

    X, Pstar, alpha = sp.symbols("X Pstar alpha", positive=True, finite=True)
    s = (1 + alpha) / (2 * alpha)
    # This expression fixes the real branch before differentiating.
    P = Pstar * sp.exp(s * sp.log(X))
    Pprime = sp.diff(P, X)
    Psecond = sp.diff(Pprime, X)
    E = 2 * X * Pprime - P
    denominator = Pprime + 2 * X * Psecond

    checks = {
        "contract_hash": sha256(contract_path) == CONTRACT_SHA256,
        "common_spec_hash": all(
            sha256(repo_root / item["path"]) == item["sha256"]
            for item in contract["identity"]["source_input_hashes"]
        ),
        "toolchain": sp.__version__ == "1.14.0" and sys.executable == "/usr/bin/python3.12",
        "target_id": TARGET in contract["target"]["exact_test_obligations"],
        "first_derivative": exact_zero(Pprime - s * P / X),
        "second_derivative": exact_zero(Psecond - s * (s - 1) * P / X**2),
        "legendre_identity": exact_zero(E - (2 * s - 1) * P),
        "denominator_factorization": exact_zero(denominator - s * (2 * s - 1) * P / X),
        "s_positive_identity": exact_zero(s - (1 + alpha) / (2 * alpha)),
        "two_s_minus_one_identity": exact_zero(2 * s - 1 - 1 / alpha),
        "power_exponent_real": ask(Q.real(s * sp.log(X))) is True,
        "positive_real_power": ask(Q.positive(sp.exp(s * sp.log(X)))) is True,
        "positive_s": ask(Q.positive(s)) is True,
        "positive_two_s_minus_one": ask(Q.positive(sp.simplify(2 * s - 1))) is True,
        "positive_Pstar": ask(Q.positive(Pstar)) is True,
        "positive_X": ask(Q.positive(X)) is True,
    }
    # On X,Pstar,alpha>0, the factorized denominator is strictly positive.
    # The contract's additional alpha<1 restriction is retained throughout.
    checks["positive_denominator"] = (
        checks["denominator_factorization"]
        and all(
            checks[name]
            for name in (
                "power_exponent_real", "positive_real_power", "positive_s",
                "positive_two_s_minus_one", "positive_Pstar", "positive_X",
            )
        )
    )
    checks["ratio_identity"] = (
        checks["positive_denominator"]
        and exact_zero(Pprime / denominator - alpha)
    )

    precision = contract["target"]["numeric_precision_digits"]
    atol = sp.Float(contract["target"]["absolute_tolerance"], precision)
    rtol = sp.Float(contract["target"]["relative_tolerance"], precision)
    diagnostics = []
    for vector in contract["target"]["numeric_test_vectors"]:
        values = {X: sp.Rational(vector["X"]), Pstar: sp.Rational(vector["Pstar"]), alpha: sp.Rational(vector["alpha"])}
        valid_domain = values[X] > 0 and values[Pstar] > 0 and 0 < values[alpha] < 1
        quantities = {
            "first_derivative": (Pprime, s * P / X),
            "second_derivative": (Psecond, s * (s - 1) * P / X**2),
            "legendre_identity": (E, (2 * s - 1) * P),
            "ratio_identity": (Pprime / denominator, alpha),
        }
        residuals = {}
        numerically_equal = bool(valid_domain)
        for name, (left, right) in quantities.items():
            left_num = sp.N(left.subs(values), precision)
            right_num = sp.N(right.subs(values), precision)
            residual = abs(left_num - right_num)
            allowed = atol + rtol * max(abs(left_num), abs(right_num))
            residuals[name] = str(residual)
            numerically_equal = numerically_equal and bool(residual <= allowed)
        den_num = sp.N(denominator.subs(values), precision)
        numerically_equal = numerically_equal and bool(den_num > 0)
        diagnostics.append({
            "vector": vector,
            "denominator": str(den_num),
            "residuals": residuals,
            "within_tolerance": numerically_equal,
        })
    checks["numeric_ancillary"] = all(d["within_tolerance"] for d in diagnostics)

    result = {
        "checks": {TARGET: all(checks.values())},
        "domain_assumption_diff": [],
        "counterexample": None,
        "details": {
            "checks": checks,
            "symbolic": {
                "s": str(s), "P": str(P), "Pprime": str(Pprime),
                "Psecond": str(Psecond), "E": str(E),
                "denominator": str(denominator),
                "positive_denominator_witness": "Pstar*exp(s*log(X))*s*(1/alpha)/X",
            },
            "numeric_precision_digits": precision,
            "numeric_diagnostics": diagnostics,
            "python_version": sys.version,
            "python_executable": sys.executable,
            "sympy_version": sp.__version__,
            "sympy_origin": sp.__file__,
            "contract_sha256": sha256(contract_path),
            "common_spec_hashes": contract["identity"]["source_input_hashes"],
            "statement_alignment": "Positive-real fixed-action scalar derivatives and algebraic E/ratio only; no metric stress, current, TOV, physical sound propagation or full C03.",
        },
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if result["checks"][TARGET] else 1


if __name__ == "__main__":
    raise SystemExit(main())
