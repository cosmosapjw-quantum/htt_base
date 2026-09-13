#!/usr/bin/env sage -python
"""Bounded Sage/Singular evidence runner for the R9 depth contracts.

This runner deliberately reports every full general proposition as false.  Its
calculations are exact, but are finite-dimensional algebraic instances and do
not prove the contracts' arbitrary-dimensional/probabilistic assertions.
"""
import json
import subprocess
import sys

from sage.all import QQ, PolynomialRing, matrix, vector


OBLIGATIONS = {
    "D1": [
        "D1_MEAN_COVARIANCE_LINEAR_MAP",
        "D1_ALL_CROSS_STEP_BLOCKS",
        "D1_PSD_PULLBACK_GENERAL_DIMENSION",
    ],
    "D2": [
        "D2_GAUSSIAN_PUSHFORWARD_SUPPORT",
        "D2_SUPPORTED_PSEUDOINVERSE_CHISQUARE",
        "D2_RANK_ZERO_AND_OFF_SUPPORT",
    ],
    "D3": [
        "D3_RECURSION_BOTH_INVERSES_ARBITRARY_BLOCKS",
        "D3_KERNEL_SURJECTIVITY_DETERMINANT",
        "D3_FULL_LAW_SUPPORT_PRESERVED",
    ],
    "D4": [
        "D4_PSD_RANGE_SCHUR_SUPPORT",
        "D4_FULL_PAST_CONDITIONAL_GAUSSIAN",
        "D4_INNOVATION_INDEPENDENCE_AND_FIXED_LAW_LIMIT",
    ],
}


def singular_zero(polynomial):
    """Ask the required case-sensitive Singular binary to reduce 0 exactly."""
    code = "ring r=0,(a,b,c,k,y0,y1,y2),dp;\npoly p=" + polynomial + ";\nreduce(p,ideal(1));\nquit;\n"
    run = subprocess.run(
        ["/usr/bin/Singular", "-q"], input=code, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=30,
    )
    # The Sage identity below is the substantive exact check.  Singular is
    # independently invoked on its zero polynomial representation as an engine
    # availability/exact-normal-form witness; no output is emitted to stdout.
    return run.returncode == 0 and "0" in run.stdout


def d1_partial():
    R = PolynomialRing(QQ, "k,c00,c01,c10,c11")
    k, c00, c01, c10, c11 = R.gens()
    H = matrix(R, [[-k, 1]])
    C = matrix(R, [[c00, c01], [c10, c11]])
    expected = c11 - c10*k - k*c01 + k*k*c00
    return (H * C * H.transpose())[0, 0] == expected and singular_zero("0")


def d3_partial():
    R = PolynomialRing(QQ, "k0,k1,y0,y1,y2")
    k0, k1, y0, y1, y2 = R.gens()
    r0 = y1 - k0*y0
    r1 = y2 - k1*y1
    yi1 = r0 + k0*y0
    yi2 = r1 + k1*yi1
    T = matrix(R, [[1, 0, 0], [-k0, 1, 0], [0, -k1, 1]])
    return yi1 == y1 and yi2 == y2 and T.det() == 1 and singular_zero("0")


def d2_partial():
    # One rank-one diagonal covariance illustrates support and the score, but
    # it is not a proof of Gaussian pushforward or chi-square law in general.
    R = PolynomialRing(QQ, "lam,z1,z2")
    lam, z1, z2 = R.gens()
    supported_score = z1*z1/lam
    return supported_score * lam == z1*z1 and singular_zero("0")


def d4_partial():
    # Nonsingular scalar-past Schur-complement algebra only; it intentionally
    # omits pseudoinverse range consistency and Gaussian conditional laws.
    R = PolynomialRing(QQ, "a,b,c")
    a, b, c = R.gens()
    schur = c - b*b/a
    return a*schur == a*c - b*b and singular_zero("0")


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in OBLIGATIONS:
        raise SystemExit("usage: depth_sage_singular_runner.py D1|D2|D3|D4")
    proposition = sys.argv[1]
    partial = {"D1": d1_partial, "D2": d2_partial, "D3": d3_partial, "D4": d4_partial}[proposition]()
    # `partial` is intentionally not elevated into a contract check.
    payload = {
        "checks": {name: False for name in OBLIGATIONS[proposition]},
        "domain_assumption_diff": [],
        "counterexample": None,
    }
    if not partial:
        # A failed finite calculation is still not offered as a counterexample
        # to the general theorem because this runner does not test its domain.
        payload["counterexample"] = None
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
