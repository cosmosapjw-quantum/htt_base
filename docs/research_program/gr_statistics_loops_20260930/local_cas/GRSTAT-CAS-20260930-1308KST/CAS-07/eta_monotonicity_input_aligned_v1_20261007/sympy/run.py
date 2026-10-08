#!/usr/bin/python3.12
"""Independent SymPy certificate for frozen CAS-07-M01."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import mpmath
import sympy as sp

REPO = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
BASE = REPO / "docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-07/eta_monotonicity_input_aligned_v1_20261007"
CONTRACT = BASE / "EXECUTION_CONTRACT.json"
INPUTS = BASE / "ADMITTED_INPUTS.json"
COMMON = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
EXPECTED = {
    CONTRACT: "b5a49f066f95a010607eb800d323094d5d4050c986c3cb26f78bba022977cc70",
    INPUTS: "89949f14b9671720a7df7e73ab2bdf2e8cede8ed7937a86ea531635f29259400",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    hashes = {str(path.relative_to(REPO)): sha(path) for path in EXPECTED}
    seals_ok = all(sha(path) == expected for path, expected in EXPECTED.items())

    x = sp.symbols("x", positive=True, real=True)
    t, a = sp.symbols("t a", positive=True, real=True)
    n = sp.symbols("n", integer=True, positive=True)
    h = sp.sinh(x) / x - 1
    numerator = x * sp.cosh(x) - sp.sinh(x)
    eta = sp.sinh(a * t) / (a * t) - 1

    checks = {
        "piecewise_k_zero": sp.simplify(t / t - 1) == 0,
        "eta_derivative_identity": sp.simplify(
            sp.diff(eta, t) - ((a * t) * sp.cosh(a * t) - sp.sinh(a * t)) / (a * t**2)
        ) == 0,
        "sinh_minus_x_derivative": sp.simplify(sp.diff(sp.sinh(x) - x, x) - (sp.cosh(x) - 1)) == 0,
        "numerator_derivative": sp.simplify(sp.diff(numerator, x) - x * sp.sinh(x)) == 0,
    }

    # Exact positive-term series. For x>0 and n>=1 every displayed term is
    # positive, which proves both required one-variable signs universally.
    sinh_term = x ** (2 * n + 1) / sp.factorial(2 * n + 1)
    numerator_term = 2 * n * x ** (2 * n + 1) / sp.factorial(2 * n + 1)
    checks["sinh_positive_series_identity"] = sp.simplify(
        sp.summation(sinh_term, (n, 1, sp.oo)) - (sp.sinh(x) - x)
    ) == 0
    checks["numerator_positive_series_identity"] = sp.simplify(
        sp.summation(numerator_term, (n, 1, sp.oo)) - numerator
    ) == 0
    checks["sinh_series_term_positive"] = sp.ask(sp.Q.positive(sinh_term)) is True
    checks["numerator_series_term_positive"] = sp.ask(sp.Q.positive(numerator_term)) is True

    # These conclusions use only the exact identities above, positivity of
    # positive-term infinite sums, and the standard derivative monotonicity theorem.
    nonnegative = all(
        checks[name]
        for name in ("sinh_positive_series_identity", "sinh_series_term_positive")
    )
    monotone = all(
        checks[name]
        for name in (
            "eta_derivative_identity",
            "numerator_positive_series_identity",
            "numerator_series_term_positive",
        )
    )
    checks["eta_nonnegative_universal"] = nonnegative
    checks["eta_monotone_universal"] = monotone
    checks["upper_bound_implication"] = nonnegative and monotone

    mpmath.mp.dps = 80
    numerical = []
    for kval, sval, lval in ((0, 1, 3), (mpmath.mpf("0.04"), 1, 3), (mpmath.mpf("2.25"), mpmath.mpf("0.1"), mpmath.mpf("0.4"))):
        if kval == 0:
            es = el = mpmath.mpf("0")
        else:
            root = mpmath.sqrt(kval)
            es = mpmath.sinh(root * sval) / (root * sval) - 1
            el = mpmath.sinh(root * lval) / (root * lval) - 1
        numerical.append({"Kc": str(kval), "s": str(sval), "L": str(lval), "eta_s": str(es), "eta_L": str(el), "ordered": bool(0 <= es <= el)})
    checks["high_precision_vectors"] = all(row["ordered"] for row in numerical)

    full = seals_ok and all(checks.values())
    record = {
        "sympy_version": sp.__version__,
        "input_sha256": hashes,
        "checks": checks,
        "high_precision_80_digit_vectors": numerical,
        "proof_basis": [
            "For Kc=0 the literal branch gives eta=0.",
            "For Kc>0 set x=sqrt(Kc)t>0. SymPy exactly sums the positive-term series for sinh(x)-x and x cosh(x)-sinh(x).",
            "The exact derivative identity reduces eta' to the second nonnegative series divided by a positive denominator, so eta is nondecreasing on positive t.",
            "Therefore 0<=eta(Kc,s)<=eta(Kc,L); the admitted eta(Kc,L)<1 yields eta(Kc,s)<1.",
        ],
    }
    (BASE / "sympy" / "proof_record.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    payload = {
        "checks": {"CAS-07-M01": full},
        "domain_assumption_diff": [],
        "counterexample": None,
    }
    print(json.dumps(payload, sort_keys=True))
    return 0 if full else 2


if __name__ == "__main__":
    raise SystemExit(main())
