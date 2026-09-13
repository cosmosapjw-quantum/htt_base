#!/usr/bin/env python3
"""Bounded SymPy probe for the R9 depth contracts.

This runner intentionally returns false for an obligation unless the engine
has established its declared all-finite-dimensional/probabilistic statement.
The computations retained below are exact partial algebraic evidence only;
they are not finite-example substitutes for the contracts.
"""
from __future__ import annotations

import argparse
import json
import sys

import sympy as sp


OBLIGATIONS = {
    "D1": [
        "D1_MEAN_COVARIANCE_LINEAR_MAP",
        "D1_ALL_CROSS_STEP_BLOCKS",
        "D1_PSD_PULLBACK_GENERAL_DIMENSION",
    ],
    "D3": [
        "D3_RECURSION_BOTH_INVERSES_ARBITRARY_BLOCKS",
        "D3_KERNEL_SURJECTIVITY_DETERMINANT",
        "D3_FULL_LAW_SUPPORT_PRESERVED",
    ],
    "D2": [
        "D2_GAUSSIAN_PUSHFORWARD_SUPPORT",
        "D2_SUPPORTED_PSEUDOINVERSE_CHISQUARE",
        "D2_RANK_ZERO_AND_OFF_SUPPORT",
    ],
    "D4": [
        "D4_PSD_RANGE_SCHUR_SUPPORT",
        "D4_FULL_PAST_CONDITIONAL_GAUSSIAN",
        "D4_INNOVATION_INDEPENDENCE_AND_FIXED_LAW_LIMIT",
    ],
}


def d1_partial() -> None:
    """Exact one-step block expansion with symbolic compatible dimensions."""
    n, m = sp.symbols("n m", integer=True, positive=True)
    k = sp.MatrixSymbol("K", m, n)
    c00 = sp.MatrixSymbol("C00", n, n)
    c01 = sp.MatrixSymbol("C01", n, m)
    c10 = sp.MatrixSymbol("C10", m, n)
    c11 = sp.MatrixSymbol("C11", m, m)
    h = sp.BlockMatrix([[-k, sp.Identity(m)]])
    c = sp.BlockMatrix([[c00, c01], [c10, c11]])
    got = sp.block_collapse(h * c * h.T)
    expected = c11 - c10 * k.T - k * c01 + k * c00 * k.T
    assert sp.expand(got) == expected


def d3_partial() -> None:
    """Exact two-step triangular identity; deliberately not an induction proof."""
    n0, n1, n2 = sp.symbols("n0 n1 n2", integer=True, positive=True)
    k0 = sp.MatrixSymbol("K0", n1, n0)
    k1 = sp.MatrixSymbol("K1", n2, n1)
    t = sp.BlockMatrix(
        [
            [sp.Identity(n0), sp.ZeroMatrix(n0, n1), sp.ZeroMatrix(n0, n2)],
            [-k0, sp.Identity(n1), sp.ZeroMatrix(n1, n2)],
            [sp.ZeroMatrix(n2, n0), -k1, sp.Identity(n2)],
        ]
    )
    tinv = sp.BlockMatrix(
        [
            [sp.Identity(n0), sp.ZeroMatrix(n0, n1), sp.ZeroMatrix(n0, n2)],
            [k0, sp.Identity(n1), sp.ZeroMatrix(n1, n2)],
            [k1 * k0, k1, sp.Identity(n2)],
        ]
    )
    product = sp.block_collapse(t * tinv)
    # MatrixExpr equality does not canonicalize BlockMatrix against
    # BlockDiagMatrix, although the corresponding compatible blocks agree.
    assert product.blocks == sp.BlockDiagMatrix(
        sp.Identity(n0), sp.Identity(n1), sp.Identity(n2)
    ).blocks


def d2_partial() -> None:
    """Exact diagonal whitening identity, with no distributional conclusion."""
    a, b, u, v = sp.symbols("a b u v", nonzero=True, real=True)
    vv = sp.diag(a**2, b**2)
    z = sp.Matrix([a * u, b * v])
    q = (z.T * vv.inv() * z)[0]
    assert sp.simplify(q - (u**2 + v**2)) == 0


def d4_partial() -> None:
    """Exact nonsingular covariance residual identity, not the PSD support proof."""
    n, m = sp.symbols("n m", integer=True, positive=True)
    a = sp.MatrixSymbol("A", n, n)
    b = sp.MatrixSymbol("B", m, n)
    residual_cross = b - b * a**-1 * a
    assert sp.simplify(residual_cross) == sp.ZeroMatrix(m, n)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("proposition", choices=sorted(OBLIGATIONS))
    args = parser.parse_args()
    if sp.__version__ != "1.14.0":
        raise RuntimeError(f"expected SymPy 1.14.0, got {sp.__version__}")

    {"D1": d1_partial, "D3": d3_partial, "D2": d2_partial, "D4": d4_partial}[args.proposition]()

    # SymPy supplies the partial exact manipulations above, but it neither
    # quantifies over arbitrary finite depth/dimension nor proves the needed
    # probability/support assertions. Each false means UNVERIFIED, not a
    # counterexample to the underlying mathematical proposition.
    payload = {
        "checks": {name: False for name in OBLIGATIONS[args.proposition]},
        "domain_assumption_diff": [],
        "counterexample": None,
    }
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 1


if __name__ == "__main__":
    sys.exit(main())
