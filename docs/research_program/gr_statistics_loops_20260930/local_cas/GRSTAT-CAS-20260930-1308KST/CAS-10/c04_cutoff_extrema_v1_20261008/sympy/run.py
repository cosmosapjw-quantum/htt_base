#!/usr/bin/env python3
"""Exact SymPy axis for the frozen CAS-10-C04 finite polynomial component.

Run with /usr/bin/python3 -B run.py. Standard output is exactly the runner
payload; standard error is a detailed proof trace. No sibling axis is read.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import sympy as sp


HERE = Path(__file__).resolve().parent
UNIT = HERE.parent
REPO = HERE.parents[7]
CONTRACT = UNIT / "EXECUTION_CONTRACT.json"
INPUT = UNIT / "ADMITTED_INPUTS.json"
COMMON = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
EXPECTED_HASHES = {
    CONTRACT: "8f2f5e387e8130f605073c650c9c0174253dd70e34ae4d4fbb23c697b53ead3a",
    INPUT: "1df59b533e32a7f21d3a7a1ee90c39cf6451b42bcd10d4ec580bdb031a47e992",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}


def require(condition: bool, description: str) -> None:
    if not condition:
        raise AssertionError(description)
    print(f"PASS {description}", file=sys.stderr)


def exact_zero(expr: sp.Expr) -> bool:
    return sp.cancel(sp.radsimp(sp.simplify(expr))) == 0


def main() -> None:
    require(sp.__version__ == "1.14.0", "SymPy version 1.14.0")
    for path, expected in EXPECTED_HASHES.items():
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        require(actual == expected, f"input SHA256 {path.name}={actual}")

    contract = json.loads(CONTRACT.read_text())
    admitted = json.loads(INPUT.read_text())
    require(contract["identity"]["contract_id"] == "GRSTAT-20260930-CAS-10-C04-CUTOFF-EXTREMA-V1", "frozen contract ID")
    require(admitted["definition"] == "F(t)=1-10t^3+15t^4-6t^5", "admitted definition")
    require(admitted["domain"] == "t in [0,1] for extrema", "admitted compact real domain")

    t = sp.symbols("t", real=True)
    F = 1 - 10*t**3 + 15*t**4 - 6*t**5
    d1 = sp.diff(F, t)
    d2 = sp.diff(d1, t)
    d3 = sp.diff(d2, t)
    half = sp.Rational(1, 2)
    rlo = (3 - sp.sqrt(3))/6
    rhi = (3 + sp.sqrt(3))/6

    require(F.subs(t, 0) == 1 and F.subs(t, 1) == 0, "endpoint values")
    require(all(p.subs(t, e) == 0 for p in (d1, d2) for e in (0, 1)), "first and second endpoint jets")
    require(exact_zero(d1 + 30*t**2*(1-t)**2), "factorization F'=-30[t(1-t)]^2")
    require(exact_zero(sp.Rational(1, 4)-t*(1-t)-(t-half)**2), "global square identity 1/4-t(1-t)=(t-1/2)^2")
    # On 0<=t<=1, t(1-t)>=0. The square identity gives <=1/4,
    # with equality iff t=1/2. Thus |F'|<=30/16=15/8 uniquely.
    require(exact_zero(abs(d1.subs(t, half))-sp.Rational(15, 8)), "unique |F'| maximum 15/8 at t=1/2")
    require(sp.solve(sp.Eq((t-half)**2, 0), t) == [half], "first derivative equality point")

    require(exact_zero(d2 + 60*t*(1-t)*(1-2*t)), "factorization F''=-60t(1-t)(1-2t)")
    require(exact_zero(d3 + 60*(1-6*t+6*t**2)), "factorization F'''=-60(1-6t+6t^2)")
    roots = set(sp.solve(sp.Eq(d3, 0), t))
    require(roots == {rlo, rhi}, "all F'' stationary points are (3±sqrt(3))/6")
    require(bool(0 < rlo < rhi < 1), "both stationary points lie strictly inside [0,1]")
    candidates = [sp.Integer(0), sp.Integer(1), rlo, rhi]
    candidate_values = [sp.simplify(d2.subs(t, x)) for x in candidates]
    require(candidate_values == [0, 0, -10/sp.sqrt(3), 10/sp.sqrt(3)], "F'' at endpoints and both stationary points")
    require(all(exact_zero(abs(v)-10/sp.sqrt(3)) for v in candidate_values[2:]), "both stationary points have equal absolute value")
    require(bool(10/sp.sqrt(3) > 0), "positive claimed maximum")
    # |F''| is continuous on [0,1]. A positive interior absolute maximum has
    # F''!=0 and is a stationary point of F''; endpoints are also candidates.
    # The complete candidate list above therefore proves the global maximum
    # and the exact equality set {rlo,rhi}.

    margin = sp.Rational(25, 24)*(sp.Rational(14, 15)+sp.Rational(9, 400))
    require(margin == sp.Rational(1147, 1152), "exact rational margin 1147/1152")
    require(margin < 1 and 1-margin == sp.Rational(5, 1152), "strict margin below one by 5/1152")

    print("F'=", d1, file=sys.stderr)
    print("F''=", d2, file=sys.stderr)
    print("F'''=", d3, file=sys.stderr)
    print("F'' candidate values=", [str(v) for v in candidate_values], file=sys.stderr)
    print("Scope: exact real polynomial component only; exp/sqrt auxiliary bounds are assumed inputs; no mollifier, probability, or science conclusion.", file=sys.stderr)
    print(json.dumps({"checks": {"CAS-10-C04": True}, "domain_assumption_diff": [], "counterexample": None}, separators=(",", ":")))


if __name__ == "__main__":
    main()
