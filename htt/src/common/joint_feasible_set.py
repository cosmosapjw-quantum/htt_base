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
    """Exact I_C over the rational polytope {A g <= b} by vertex enumeration.

    Assumes a bounded polytope (all vertices are intersections of n of the m
    inequality faces). Returns the exact interval and classification.
    """
    n = len(c)
    m = len(A)
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
    if not vertices:
        raise InfeasibleError("no feasible vertex; polytope empty or unbounded")
    values = [sum(c[j] * v[j] for j in range(n)) for v in vertices]
    lo, hi = min(values), max(values)
    return {
        "exact_interval": [str(lo), str(hi)],
        "exact_lo": lo,
        "exact_hi": hi,
        "n_vertices": len(vertices),
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
