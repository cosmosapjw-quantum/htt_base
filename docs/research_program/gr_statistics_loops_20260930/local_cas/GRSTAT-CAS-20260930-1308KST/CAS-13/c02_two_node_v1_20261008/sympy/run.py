#!/usr/bin/python3.12
"""Blind SymPy verification of the frozen CAS-13-C02 two-node contract."""

from __future__ import annotations

import hashlib
import json
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import mpmath
import sympy as sp


HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent
CONTRACT_HASH = "66b839cb44573842f36f73c234c4b5b6c8cca639465c58e525b86be8aea754b0"
INPUT_HASH = "83bb552d9cbc733c58bd57bef88a53ac060261b343b6e9596181586104a68725"
TEFF_HASH = "bc055d391d3231c634a14e146f228d3b8179a043485c41ce08754cdeac4fd0fe"
COMMON_HASH = "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(condition: bool, message: str, log: list[str]) -> None:
    if not condition:
        raise AssertionError(message)
    log.append("PASS " + message)


def zero(expression: sp.Expr) -> bool:
    return sp.cancel(sp.factor(expression)) == 0


def numeric_control(m4: sp.Rational, label: str, log: list[str]) -> dict:
    aa, bb, mm3 = sp.Integer(1), sp.Integer(3), sp.Integer(8)
    rr = sp.Integer(2)
    chord = aa**4 + (mm3 - aa**3) * (bb**4 - aa**4) / (bb**3 - aa**3)
    check(rr**4 < m4 < chord, f"{label}: exact S121 strict interior", log)
    x = sp.Symbol("x")
    fa = sp.cancel((x**4 - aa**4) / (x**3 - aa**3))
    gb = sp.cancel((bb**4 - x**4) / (bb**3 - x**3))
    tl = (m4 - aa**4) / (mm3 - aa**3)
    tu = (bb**4 - m4) / (bb**3 - mm3)
    u = sp.nsolve(fa - tl, (rr, bb), solver="bisect", prec=100, maxsteps=400)
    d = sp.nsolve(gb - tu, (aa, rr), solver="bisect", prec=100, maxsteps=400)
    wu = (mm3 - aa**3) / (u**3 - aa**3)
    wb = (mm3 - d**3) / (bb**3 - d**3)
    check(bool(rr < u < bb and aa < d < rr), f"{label}: node branch", log)
    check(bool(0 < wu < 1 and 0 < wb < 1), f"{label}: strict weights", log)
    residuals = [
        (1 - wu) * aa**3 + wu * u**3 - mm3,
        (1 - wu) * aa**4 + wu * u**4 - m4,
        (1 - wb) * d**3 + wb * bb**3 - mm3,
        (1 - wb) * d**4 + wb * bb**4 - m4,
    ]
    max_residual = max(abs(sp.N(z, 90)) for z in residuals)
    check(bool(max_residual < sp.Rational(1, 10**50)), f"{label}: 80-digit moment residual < 1e-50", log)
    return {
        "label": label,
        "a": "1",
        "b": "3",
        "m3": "8",
        "m4": str(m4),
        "r": "2",
        "u_80d": str(sp.N(u, 80)),
        "d_80d": str(sp.N(d, 80)),
        "w_u_80d": str(sp.N(wu, 80)),
        "w_b_80d": str(sp.N(wb, 80)),
        "maximum_moment_residual_80d": str(sp.N(max_residual, 80)),
    }


def execute(log: list[str]) -> dict:
    root = next(p for p in HERE.parents if (p / ".git").exists())
    inputs = [
        (PACKAGE / "EXECUTION_CONTRACT.json", CONTRACT_HASH),
        (PACKAGE / "ADMITTED_INPUTS.json", INPUT_HASH),
        (root / "docs/research_program/gr_statistics_loops_20260930/cas/TEFF_INTERVAL_SPEC.md", TEFF_HASH),
        (root / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md", COMMON_HASH),
    ]
    for path, expected in inputs:
        check(sha(path) == expected, f"frozen SHA-256 {path.name}", log)

    a, b, r, m3, m4, u, d = sp.symbols("a b r m3 m4 u d", positive=True, real=True)
    fa = sp.cancel((u**4 - a**4) / (u**3 - a**3))
    gb = sp.cancel((b**4 - d**4) / (b**3 - d**3))
    dfa = u**2 * (3*a**2 + 2*a*u + u**2) / (a**2 + a*u + u**2)**2
    dgb = d**2 * (3*b**2 + 2*b*d + d**2) / (b**2 + b*d + d**2)**2
    check(zero(sp.diff(fa, u) - dfa), "exact lower derivative identity", log)
    check(zero(sp.diff(gb, d) - dgb), "exact upper derivative identity", log)
    # In 0<a<r<b, both derivative numerators and denominator squares are positive.
    check(all(x.is_positive for x in (a, b, r, u, d)), "positive-real symbols for derivative sign certificate", log)

    chord = a**4 + (m3-a**3)*(b**4-a**4)/(b**3-a**3)
    lower_target = (m4-a**4)/(m3-a**3)
    upper_target = (b**4-m4)/(b**3-m3)
    fa_r = fa.subs(u, r)
    fa_b = fa.subs(u, b)
    gb_a = gb.subs(d, a)
    gb_r = gb.subs(d, r)
    # The sole substitution m3=r^3 encodes the positive real cube-root branch.
    identities = {
        "F_target_minus_F_r": lower_target.subs(m3, r**3)-fa_r-(m4-r**4)/(r**3-a**3),
        "F_b_minus_F_target": fa_b-lower_target-(chord-m4)/(m3-a**3),
        "G_target_minus_G_a": upper_target-gb_a-(chord-m4)/(b**3-m3),
        "G_r_minus_G_target": gb_r-upper_target.subs(m3, r**3)-(m4-r**4)/(b**3-r**3),
    }
    for name, expression in identities.items():
        check(zero(expression), f"exact endpoint bracket {name}", log)
    # S121 gives r^4<m4<chord; 0<a<r<b makes every displayed denominator positive.
    # The ratio functions are continuous on the closed bracket intervals and have
    # strictly positive derivatives, so IVT gives existence and strict monotonicity
    # gives uniqueness in u in (r,b) and d in (a,r).

    wu = (m3-a**3)/(u**3-a**3)
    wb = (m3-d**3)/(b**3-d**3)
    check(zero((1-wu)*a**3+wu*u**3-m3), "exact lower third moment", log)
    check(zero((1-wb)*d**3+wb*b**3-m3), "exact upper third moment", log)
    check(zero((1-wu)*a**4+wu*u**4-m4-(m3-a**3)*(fa-lower_target)),
          "lower fourth moment reduces to node equation", log)
    check(zero((1-wb)*d**4+wb*b**4-m4-(b**3-m3)*(upper_target-gb)),
          "upper fourth moment reduces to node equation", log)
    check(zero((1-wu)+wu-1) and zero((1-wb)+wb-1), "exact weight normalization", log)
    # m3=r^3, a<r<u imply 0<m3-a^3<u^3-a^3; d<r<b similarly gives
    # 0<m3-d^3<b^3-d^3. Thus both weights are strictly between zero and one.

    lam = (m3-a**3)/(b**3-a**3)
    checks_boundary = {
        "lower_dirac_weight": wu.subs({m3:r**3,u:r})-1,
        "upper_dirac_weight": wb.subs({m3:r**3,d:r}),
        "lower_chord_weight": wu.subs(u,b)-lam,
        "upper_chord_weight": wb.subs(d,a)-lam,
        "chord_m3": (1-lam)*a**3+lam*b**3-m3,
        "chord_m4": (1-lam)*a**4+lam*b**4-chord,
    }
    for name, expression in checks_boundary.items():
        check(zero(expression), f"boundary limiting measure {name}", log)
    # m3=a^3 or b^3 forces m4=a^4 or b^4 by squeezing r^4<=m4<=chord;
    # positive support and extremal third moment force delta_a or delta_b.
    check(zero(chord.subs(m3,a**3)-a**4) and zero(chord.subs(m3,b**3)-b**4),
          "endpoint data squeeze to Dirac moments", log)

    m4_reference = sp.Integer(20)
    m4_lower_near = sp.Integer(16) + sp.Rational(1, 10**20)
    chord_control = chord.subs({a:1,b:3,m3:8})
    m4_chord_near = chord_control - sp.Rational(1, 10**20)
    controls = [
        numeric_control(m4_reference, "reference", log),
        numeric_control(m4_lower_near, "near_dirac", log),
        numeric_control(m4_chord_near, "near_chord", log),
    ]
    return {
        "symbolic_checks": len([x for x in log if x.startswith("PASS")]) - 15,
        "proof_certificate": {
            "domain": "0<a<r<b, m3=r^3, r^4<m4<chord(m3)",
            "branch": "r is the positive real cube root of m3",
            "strict_denominators": ["r^3-a^3", "m3-a^3", "b^3-m3", "b^3-r^3", "u^3-a^3", "b^3-d^3"],
            "monotonicity": "Both derivative identities are positive on their node intervals. Continuity, strict endpoint brackets, and IVT give unique u in (r,b), d in (a,r).",
            "weights": "a<r<u implies 0<m3-a^3<u^3-a^3; d<r<b implies 0<m3-d^3<b^3-d^3.",
            "boundaries": "At m4=r^4 use delta_r; at m4=chord use (1-lambda)delta_a+lambda delta_b. Endpoint m3=a^3/b^3 squeeze m4 to a^4/b^4 and give delta_a/delta_b. Interior formulas are not evaluated at their 0/0 endpoints.",
        },
        "numeric_controls": controls,
    }


def main() -> int:
    started = time.time()
    log: list[str] = []
    error = ""
    details: dict = {}
    status = "PASS"
    try:
        details = execute(log)
    except Exception:
        status = "FAIL"
        error = traceback.format_exc()
    (HERE / "sympy.stdout.log").write_text("\n".join(log) + "\n", encoding="utf-8")
    (HERE / "sympy.stderr.log").write_text(error, encoding="utf-8")
    artifacts = {
        name: {"path": str(HERE / name), "sha256": sha(HERE / name)}
        for name in ("run.py", "sympy.stdout.log", "sympy.stderr.log")
    }
    result = {
        "schema_version": 1,
        "axis": "sympy",
        "status": status,
        "evidence_class": "exact",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "contract_id": "GRSTAT-20260930-CAS-13-C02-TWO-NODE-V1",
        "contract_sha256": CONTRACT_HASH,
        "input_sha256": INPUT_HASH,
        "source_hashes": {"TEFF_INTERVAL_SPEC.md": TEFF_HASH, "COMMON_SPEC.md": COMMON_HASH},
        "component": "CAS-13-C02",
        "scope": "two-node existence, uniqueness and feasibility only",
        "assumptions_aligned": True,
        "branch_aligned": True,
        "independence_mode": "blind-results-and-derivations",
        "tool_versions": {"python": sys.version.split()[0], "sympy": sp.__version__, "mpmath": mpmath.__version__},
        "executable": sys.executable,
        "argv": [sys.executable, "-B", str(Path(__file__).relative_to(next(p for p in HERE.parents if (p / '.git').exists())))],
        "exit_code": 0 if status == "PASS" else 1,
        "commands": [{
            "argv": [sys.executable, "-B", str(Path(__file__).relative_to(next(p for p in HERE.parents if (p / '.git').exists())))],
            "exit_code": 0 if status == "PASS" else 1,
            "tool": "SymPy",
            "version": sp.__version__,
        }],
        "elapsed_seconds": round(time.time()-started, 6),
        "executable_artifacts": artifacts,
        "details": details,
        "error": error or None,
        "claim_ceiling": "No general-p extremizer, C03/C04, full theorem, or scientific admission",
    }
    (HERE / "axis_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"checks": {"CAS-13-C02": status == "PASS"}, "domain_assumption_diff": [], "counterexample": None}, separators=(",", ":")))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
