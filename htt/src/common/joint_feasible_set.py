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


class UnboundedError(ValueError):
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


def _is_feasible_exact(
    A: list[list[Fraction]], b: list[Fraction], n: int
) -> bool:
    """Exact rational Fourier--Motzkin feasibility test."""
    inequalities = [(list(row), rhs) for row, rhs in zip(A, b)]
    for _ in range(n):
        positive = []
        negative = []
        zero = []
        for row, rhs in inequalities:
            coefficient = row[-1]
            if coefficient > 0:
                positive.append((row, rhs))
            elif coefficient < 0:
                negative.append((row, rhs))
            else:
                zero.append((row[:-1], rhs))

        projected = list(zero)
        for upper_row, upper_rhs in positive:
            upper_coefficient = upper_row[-1]
            for lower_row, lower_rhs in negative:
                lower_coefficient = lower_row[-1]
                projected.append(
                    (
                        [
                            (-lower_coefficient) * upper_row[j]
                            + upper_coefficient * lower_row[j]
                            for j in range(len(upper_row) - 1)
                        ],
                        (-lower_coefficient) * upper_rhs
                        + upper_coefficient * lower_rhs,
                    )
                )
        inequalities = projected
        if any(not row and rhs < 0 for row, rhs in inequalities):
            return False
    return all(rhs >= 0 for _row, rhs in inequalities)


def _enumerate_vertices(
    A: list[list[Fraction]], b: list[Fraction], n: int
) -> list[list[Fraction]]:
    vertices = []
    for combo in itertools.combinations(range(len(A)), n):
        rows = [A[i] for i in combo]
        rhs = [b[i] for i in combo]
        vertex = _solve_vertex(rows, rhs)
        if vertex is None:
            continue
        if all(
            sum(A[i][j] * vertex[j] for j in range(n)) <= b[i]
            for i in range(len(A))
        ):
            vertices.append(vertex)
    return vertices


def _has_nonzero_recession_direction(
    A: list[list[Fraction]], n: int
) -> bool:
    """Return whether ``{d: A d <= 0}`` contains a nonzero direction.

    Intersecting the recession cone with the unit box makes it a compact
    rational polytope. It contains a nonzero vertex exactly when the original
    feasible set is unbounded.
    """
    recession_A = [list(row) for row in A]
    recession_b = [Fraction(0)] * len(A)
    for j in range(n):
        positive = [Fraction(0)] * n
        negative = [Fraction(0)] * n
        positive[j] = Fraction(1)
        negative[j] = Fraction(-1)
        recession_A.extend((positive, negative))
        recession_b.extend((Fraction(1), Fraction(1)))
    vertices = _enumerate_vertices(recession_A, recession_b, n)
    return any(any(value != 0 for value in vertex) for vertex in vertices)


def exact_support(
    c: list[Fraction],
    A: list[list[Fraction]],
    b: list[Fraction],
) -> dict:
    """Exact I_C over the rational polytope {A g <= b} by vertex enumeration.

    Requires a nonempty bounded polytope (all vertices are intersections of n
    of the m inequality faces). Infeasible and unbounded inputs are classified
    separately before a finite interval is returned.
    """
    n = len(c)
    if n == 0:
        raise ValueError("objective must have at least one dimension")
    if len(A) != len(b) or any(len(row) != n for row in A):
        raise ValueError("constraint dimensions must match the objective")
    if not _is_feasible_exact(A, b, n):
        raise InfeasibleError("polyhedron is empty")
    if _has_nonzero_recession_direction(A, n):
        raise UnboundedError("polyhedron is unbounded; finite support refused")
    vertices = _enumerate_vertices(A, b, n)
    if not vertices:
        raise RuntimeError("bounded nonempty polytope produced no vertices")
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
