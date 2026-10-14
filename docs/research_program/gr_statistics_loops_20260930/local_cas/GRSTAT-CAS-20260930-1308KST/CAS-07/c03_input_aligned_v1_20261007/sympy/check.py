"""Exact, conditional CAS-07 C03 finite-distance algebra (SymPy axis).

Only the two frozen local JSON inputs and neutral COMMON_SPEC are read.  The
Taylor/screen inequalities are *premises*, never derived here.  The comments
below give the ordered-real proof accompanying the checked exact identities.
Numerical vectors are ancillary and do not establish universal implications.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import sympy as sp


ROOT = Path(__file__).resolve().parents[8]
CASE = Path(__file__).resolve().parent.parent
CONTRACT = CASE / "EXECUTION_CONTRACT.json"
INPUTS = CASE / "ADMITTED_INPUTS.json"
COMMON = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
EXPECTED_HASHES = {
    CONTRACT: "a65d1f9c9c64a149f554855be39400755cb2aee394440d813877a6fcd6e25b6d",
    INPUTS: "8e87c30466c362dc85071c64fd722933fa5e170d8128f81de29d859a045aa827",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}


def exact_zero(expression: sp.Expr) -> bool:
    return sp.simplify(sp.cancel(sp.together(expression))) == 0


def binding() -> tuple[dict, dict]:
    for path, expected in EXPECTED_HASHES.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, str(path)
    contract = json.loads(CONTRACT.read_text())
    inputs = json.loads(INPUTS.read_text())
    assert contract["identity"]["contract_id"] == "GRSTAT-20260930-CAS-07-C03-FD-ALGEBRA-V1"
    assert contract["independence"]["mode"] == "blind-results-and-derivations"
    assert sp.__version__ == "1.14.0"
    assert inputs["admitted_premises"] == [
        "abs(Z-Z0-H0*s/c) <= M2*s^2/2",
        "s*(1-eta) <= dA",
        "dA <= s*(1+eta)",
        "0 <= eta",
        "eta <= etaL",
        "etaL < 1",
    ]
    assert inputs["targets"] == {
        "CAS-07-C03-FD1": "abs(Z-Z0-H0*dA/c) <= M2*s^2/2 + abs(H0)*s*eta/c",
        "CAS-07-C03-FD2": "abs(Z-Z0-H0*dA/c) <= M2*dA^2/(2*(1-etaL)^2) + abs(H0)*dA*etaL/(c*(1-etaL))",
        "CAS-07-C03-FD3": "abs(c*(Z-Z0)/dA-H0) <= c*M2*s/(2*(1-eta)) + abs(H0)*eta/(1-eta)",
    }
    return contract, inputs


# Real variables and declared positivity. etaL is real, with etaL >= eta >= 0
# and etaL < 1 supplied as relational premises below, not assumed by SymPy.
s, L, c, dA = sp.symbols("s L c dA", positive=True)
M2 = sp.Symbol("M2", nonnegative=True)
H0, Z, Z0, eta, etaL = sp.symbols("H0 Z Z0 eta etaL", real=True)
r = Z - Z0 - H0 * s / c
delta = dA - s
e = Z - Z0 - H0 * dA / c
A = M2 * s**2 / 2
B = sp.Abs(H0) * s * eta / c
rhs1 = A + B
rhs2 = M2 * dA**2 / (2 * (1 - etaL) ** 2) + sp.Abs(H0) * dA * etaL / (c * (1 - etaL))
rhs3 = c * M2 * s / (2 * (1 - eta)) + sp.Abs(H0) * eta / (1 - eta)


def triangle_certificate() -> bool:
    """Prove |a+b| <= |a|+|b| in the four sign branches.

    Write a=sign_a*X, b=sign_b*Y with X,Y>=0.  The exact squared
    difference (X+Y)^2-(a+b)^2 is either 0 or 4XY, hence nonnegative.
    X+Y>=0 then gives the unsquared triangle inequality.
    """
    X, Y = sp.symbols("X Y", nonnegative=True)
    for sa in (-1, 1):
        for sb in (-1, 1):
            difference = sp.factor((X + Y) ** 2 - (sa * X + sb * Y) ** 2)
            expected = sp.Integer(0) if sa == sb else 4 * X * Y
            if not exact_zero(difference - expected):
                return False
    return True


def fd1() -> bool:
    """Screen interval plus Taylor premise imply FD1, for arbitrary Z0.

    Set t=dA-s(1-eta)>=0 and u=s(1+eta)-dA>=0.  Then
    delta+s*eta=t and s*eta-delta=u.  Since eta>=0 and s>0,
    -s*eta <= delta <= s*eta.  In the delta>=0 and delta<=0 branches,
    respectively, this gives |delta|<=s*eta.  With |r|<=A supplied,
    e=r-H0*delta/c, triangle and c>0 yield
    |e|<=|r|+|H0||delta|/c<=A+|H0|s*eta/c.
    """
    t = dA - s * (1 - eta)
    u = s * (1 + eta) - dA
    return all((
        triangle_certificate(),
        exact_zero(e - (r - H0 * delta / c)),
        exact_zero(delta + s * eta - t),
        exact_zero(s * eta - delta - u),
        exact_zero(sp.Abs(H0 * delta / c) - sp.Abs(H0) * sp.Abs(delta) / c),
        exact_zero(rhs1 - (A + B)),
    ))


def fd2() -> bool:
    """FD1 bound is bounded by FD2's bound by nonnegative factors.

    Put p=1-etaL>0, q=etaL-eta>=0, t=dA-s(1-eta)>=0.
    etaL>=eta>=0, so etaL>=0.  The exact identity
      dA/p-s=(t+s*q)/p >= 0
    gives dA/p+s>0.  Thus the M2 part of rhs2-rhs1 is
      (M2/2)*(dA/p-s)*(dA/p+s) >= 0.
    Its |H0| part is
      (|H0|/c)*(etaL*(dA/p-s)+s*q) >= 0.
    The two terms sum exactly to rhs2-rhs1.  The strict p>0 premise
    licenses all divisions.  This proof uses no FD2 target as a premise.
    """
    p = 1 - etaL
    q = etaL - eta
    t = dA - s * (1 - eta)
    gap = dA / p - s
    m_part = M2 * gap * (dA / p + s) / 2
    h_part = sp.Abs(H0) * (etaL * gap + s * q) / c
    return all((
        fd1(),
        exact_zero(p - (1 - etaL)),
        exact_zero(q - (etaL - eta)),
        exact_zero(gap - (t + s * q) / p),
        exact_zero(rhs2 - rhs1 - m_part - h_part),
    ))


def fd3() -> bool:
    """Scale FD1 by c/dA>0 and bound the remaining nonnegative gap.

    eta<=etaL<1 gives u=1-eta>0, and t=dA-s*u>=0.
    The left side of FD3 equals (c/dA)*|e|.  FD1 therefore bounds it
    by (c/dA)*rhs1.  The exact difference is
      rhs3-(c/dA)*rhs1 = (c*M2*s/2+|H0|*eta)*t/(dA*u) >= 0.
    The numerator's factors are nonnegative and both denominator
    factors are strictly positive.  H0=0, M2=0, eta=0 are included.
    """
    u = 1 - eta
    t = dA - s * u
    gap = (c * M2 * s / 2 + sp.Abs(H0) * eta) * t / (dA * u)
    return all((
        fd1(),
        exact_zero(c * (Z - Z0) / dA - H0 - c * e / dA),
        exact_zero(sp.Abs(c * (Z - Z0) / dA - H0) - c * sp.Abs(e) / dA),
        exact_zero(rhs3 - c * rhs1 / dA - gap),
    ))


def exact_vectors() -> bool:
    """Ancillary exact boundary/interior substitutions, never a proof step."""
    Q = sp.Rational
    vectors = [
        # eta=etaL=0 and dA=s; s=L.
        (2, 2, 3, 2, 5, 0, 0, 2, Q(7, 3)),
        # H0=0 and lower screen endpoint.
        (2, 3, 3, 2, 0, Q(1, 4), Q(1, 2), Q(3, 2), Q(7, 3)),
        # M2=0 and upper screen endpoint.
        (2, 3, 3, 0, -5, Q(1, 4), Q(1, 2), Q(5, 2), Q(7, 3)),
        # eta<etaL<1 and interior dA.
        (2, 3, 3, 2, -5, Q(1, 4), Q(1, 2), Q(9, 4), Q(7, 3)),
    ]
    for sv, Lv, cv, mv, hv, nv, nLv, dv, z0v in vectors:
        zv = z0v + hv * Q(sv, cv) + mv * Q(sv * sv, 4)
        sub = {s: sv, L: Lv, c: cv, M2: mv, H0: hv,
               eta: nv, etaL: nLv, dA: dv, Z0: z0v, Z: zv}
        premises = [sp.Abs(r) <= A, s * (1 - eta) <= dA,
                    dA <= s * (1 + eta), 0 <= eta, eta <= etaL,
                    etaL < 1, s <= L]
        targets = [sp.Abs(e) <= rhs1, sp.Abs(e) <= rhs2,
                   sp.Abs(c * (Z - Z0) / dA - H0) <= rhs3]
        if not all(bool(statement.subs(sub)) for statement in premises + targets):
            return False
    return True


def run_checks() -> dict[str, object]:
    binding()
    results = {
        "CAS-07-C03-FD1": fd1(),
        "CAS-07-C03-FD2": fd2(),
        "CAS-07-C03-FD3": fd3(),
    }
    assert exact_vectors(), "ancillary exact vectors failed"
    return {**results, "domain_assumption_diff": [], "counterexample": None}
