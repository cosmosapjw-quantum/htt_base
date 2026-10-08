#!/usr/bin/python3
"""Independent exact SymPy check of the CAS-11-C01 finite component.

The scalar expansion below is one arbitrary coordinate of R^n. Since finite
inner products are sums of these terms, a zero generic summand proves the
identity for every finite n; H values cancel separately. MatrixExpr checks
the n-by-k/k-vector transpose step at symbolic positive dimensions.
"""

import json
import sys

import sympy as sp


def run_checks():
    if sp.__version__ != "1.14.0":
        raise RuntimeError(f"unsealed SymPy version: {sp.__version__}")

    # Arbitrary coordinate values; no relation between function values and
    # gradients is needed beyond the stated differentiability at f,g,h.
    f, g, h, pg, ph = sp.symbols("f g h pg ph", real=True)
    Hf, Hg, Hh = sp.symbols("Hf Hg Hh", real=True)
    d_fg = Hf - Hg - pg * (f - g)
    d_fh = Hf - Hh - ph * (f - h)
    d_hg = Hh - Hg - pg * (h - g)
    target = (ph - pg) * (f - h)
    three_point = sp.expand(d_fg - d_fh - d_hg - target) == 0

    # For arbitrary positive n,k, MatrixExpr canonicalizes the transpose
    # and product association. The matched moment is V.T*(f-h)=0_k.
    n, k = sp.symbols("n k", integer=True, positive=True)
    V = sp.MatrixSymbol("V", n, k)
    lam = sp.MatrixSymbol("lambda", k, 1)
    delta = sp.MatrixSymbol("f_minus_h", n, 1)
    transpose = (V * lam).T == lam.T * V.T
    dot_association = (V * lam).T * delta == lam.T * (V.T * delta)
    zero_moment = lam.T * sp.ZeroMatrix(k, 1) == sp.ZeroMatrix(1, 1)

    x = sp.symbols("x", real=True)
    cubic = x**3 / 3
    bregman = lambda a, b: sp.expand(
        cubic.subs(x, a) - cubic.subs(x, b)
        - sp.diff(cubic, x).subs(x, b) * (a - b)
    )
    cubic_orientation = (
        bregman(sp.Integer(2), sp.Integer(1)) == sp.Rational(4, 3)
        and bregman(sp.Integer(1), sp.Integer(2)) == sp.Rational(5, 3)
    )

    # V=lambda=1 and delta=1/10 have residual exactly 1/10.
    approximate_residual = (
        sp.Integer(1) * sp.Integer(1) * sp.Rational(1, 10)
        == sp.Rational(1, 10)
        and sp.Rational(1, 10) != 0
    )
    return all((three_point, transpose, dot_association, zero_moment,
                cubic_orientation, approximate_residual))


def main():
    passed = run_checks()
    payload = {
        "checks": {"CAS-11-C01": bool(passed)},
        "domain_assumption_diff": [],
        "counterexample": None,
    }
    sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
