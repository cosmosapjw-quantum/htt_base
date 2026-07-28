"""PR-189: general joint feasible-set support theorem (H05/H06).

For a compact feasible set F(physics, data, nuisance), the comparator identified
set is the exact interval I_C = [inf_F c^T g, sup_F c^T g]. The product-box
formula (independent per-axis marginals) is the CORROLLARY that holds only when
F factorizes; on a coupled F the joint interval can be strictly narrower than
the product box. This module computes I_C two ways -- exact rational vertex
enumeration (the certified authority) and a floating HiGHS LP (cross-check) --
and classifies the feasible-set topology.
"""

from __future__ import annotations

import itertools
import math
from fractions import Fraction

import numpy as np
from scipy.optimize import linprog


class InfeasibleError(ValueError):
    pass


def _solve_vertex(rows: list[list[Fraction]], rhs: list[Fraction]) -> list[Fraction] | None:
    """Exact rational solve of a square system (Gaussian elimination)."""
    n = len(rows)
    a = [list(r) + [b] for r, b in zip(rows, rhs)]
    for col in range(n):
        piv = next((r for r in range(col, n) if a[r][col] != 0), None)
        if piv is None:
            return None
        a[col], a[piv] = a[piv], a[col]
        inv = a[col][col]
        a[col] = [x / inv for x in a[col]]
        for r in range(n):
            if r != col and a[r][col] != 0:
                f = a[r][col]
                a[r] = [x - f * y for x, y in zip(a[r], a[col])]
    return [a[r][n] for r in range(n)]


def exact_support(
    c: list[Fraction],
    A: list[list[Fraction]],
    b: list[Fraction],
) -> dict:
    """I_C over ``{A g <= b}``, preserving objective recession explicitly.

    Finite endpoints remain exact rational vertex values. HiGHS is used only
    to classify feasibility/recession before the exact endpoint calculation;
    an unbounded objective is returned as ``+/- inf`` rather than clipped by a
    synthetic big-M box.
    """
    n = len(c)
    m = len(A)
    if n == 0 or m == 0 or len(b) != m or any(len(row) != n for row in A):
        raise ValueError("c, A and b must define a non-empty rectangular system")
    float_A = [[float(value) for value in row] for row in A]
    float_b = [float(value) for value in b]
    float_c = np.asarray([float(value) for value in c], dtype=float)
    feasibility = linprog(
        np.zeros(n),
        A_ub=float_A,
        b_ub=float_b,
        bounds=[(None, None)] * n,
        method="highs",
    )
    if feasibility.status == 2:
        raise InfeasibleError("polyhedron is infeasible")
    if not feasibility.success:
        raise RuntimeError(f"HiGHS feasibility classification failed: {feasibility.message}")
    lower_lp = linprog(
        float_c,
        A_ub=float_A,
        b_ub=float_b,
        bounds=[(None, None)] * n,
        method="highs",
    )
    upper_lp = linprog(
        -float_c,
        A_ub=float_A,
        b_ub=float_b,
        bounds=[(None, None)] * n,
        method="highs",
    )
    lower_unbounded = lower_lp.status == 3
    upper_unbounded = upper_lp.status == 3
    if not lower_unbounded and not lower_lp.success:
        raise RuntimeError(f"HiGHS lower support failed: {lower_lp.message}")
    if not upper_unbounded and not upper_lp.success:
        raise RuntimeError(f"HiGHS upper support failed: {upper_lp.message}")
    vertices = []
    for combo in itertools.combinations(range(m), n):
        rows = [A[i] for i in combo]
        rhs = [b[i] for i in combo]
        v = _solve_vertex(rows, rhs)
        if v is None:
            continue
        # feasible against all constraints?
        if all(sum(A[i][j] * v[j] for j in range(n)) <= b[i] for i in range(m)):
            vertices.append(v)
    if not vertices and not all(value == 0 for value in c):
        raise RuntimeError(
            "feasible support has no exact vertex representation; use the "
            "recession-aware IdentifiedDepartureSet contract"
        )
    values = [sum(c[j] * v[j] for j in range(n)) for v in vertices]
    if values:
        lo = -math.inf if lower_unbounded else min(values)
        hi = math.inf if upper_unbounded else max(values)
    else:
        lo = hi = Fraction(0)
    return {
        "exact_interval": [str(lo), str(hi)],
        "exact_lo": lo,
        "exact_hi": hi,
        "n_vertices": len(vertices),
        "lower_unbounded": lower_unbounded,
        "upper_unbounded": upper_unbounded,
        "topology": (
            "UNBOUNDED"
            if lower_unbounded or upper_unbounded
            else "BOUNDED"
        ),
    }


def marginal_ranges_exact(
    n: int, A: list[list[Fraction]], b: list[Fraction]
) -> list[tuple[Fraction, Fraction]]:
    ranges = []
    for j in range(n):
        e = [Fraction(0)] * n
        e[j] = Fraction(1)
        s = exact_support(e, A, b)
        ranges.append((s["exact_lo"], s["exact_hi"]))
    return ranges


def product_interval_exact(
    c: list[Fraction], ranges: list[tuple[Fraction, Fraction]]
) -> tuple[Fraction, Fraction]:
    lo = hi = Fraction(0)
    for coef, (a, bb) in zip(c, ranges):
        if coef >= 0:
            lo += coef * a
            hi += coef * bb
        else:
            lo += coef * bb
            hi += coef * a
    return lo, hi


def highs_support(
    c: list[float], A: list[list[float]], b: list[float]
) -> tuple[float, float]:
    """Floating cross-check via HiGHS."""
    cc = np.asarray(c, dtype=float)
    lo = linprog(cc, A_ub=A, b_ub=b, bounds=[(None, None)] * len(c), method="highs")
    hi = linprog(-cc, A_ub=A, b_ub=b, bounds=[(None, None)] * len(c), method="highs")
    if not (lo.success and hi.success):
        raise RuntimeError("HiGHS LP failed")
    return float(cc @ lo.x), float(cc @ hi.x)


def analyze(c, A, b) -> dict:
    """Full analysis: exact joint interval, product box, strictness, cross-check."""
    cF = [Fraction(x) for x in c]
    AF = [[Fraction(x) for x in row] for row in A]
    bF = [Fraction(x) for x in b]
    joint = exact_support(cF, AF, bF)
    ranges = marginal_ranges_exact(len(cF), AF, bF)
    prod_lo, prod_hi = product_interval_exact(cF, ranges)
    hs = highs_support([float(x) for x in c], [[float(x) for x in row] for row in A],
                       [float(x) for x in b])
    joint_lo, joint_hi = joint["exact_lo"], joint["exact_hi"]
    return {
        "joint_interval": joint["exact_interval"],
        "product_interval": [str(prod_lo), str(prod_hi)],
        "joint_subset_of_product": prod_lo <= joint_lo and joint_hi <= prod_hi,
        "strict_narrower": prod_lo < joint_lo or joint_hi < prod_hi,
        "joint_equals_product": joint_lo == prod_lo and joint_hi == prod_hi,
        "n_vertices": joint["n_vertices"],
        "highs_cross_check_agrees": (
            abs(hs[0] - float(joint_lo)) < 1e-9 and abs(hs[1] - float(joint_hi)) < 1e-9
        ),
        "highs_interval": list(hs),
    }
