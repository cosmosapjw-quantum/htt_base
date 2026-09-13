#!/usr/bin/env sage -python
"""Repaired bounded Sage/Singular finite-identity evidence runner.

The runner checks finite symbolic residuals in two independent algebra engines.
Those checks are deliberately kept separate from the D1--D4 general theorem
obligations, which remain false/unverified in the emitted payload.
"""
import json
import subprocess
import sys

from sage.all import QQ, PolynomialRing, matrix


OBLIGATIONS = {
    "D1": ["D1_MEAN_COVARIANCE_LINEAR_MAP", "D1_ALL_CROSS_STEP_BLOCKS", "D1_PSD_PULLBACK_GENERAL_DIMENSION"],
    "D2": ["D2_GAUSSIAN_PUSHFORWARD_SUPPORT", "D2_SUPPORTED_PSEUDOINVERSE_CHISQUARE", "D2_RANK_ZERO_AND_OFF_SUPPORT"],
    "D3": ["D3_RECURSION_BOTH_INVERSES_ARBITRARY_BLOCKS", "D3_KERNEL_SURJECTIVITY_DETERMINANT", "D3_FULL_LAW_SUPPORT_PRESERVED"],
    "D4": ["D4_PSD_RANGE_SCHUR_SUPPORT", "D4_FULL_PAST_CONDITIONAL_GAUSSIAN", "D4_INNOVATION_INDEPENDENCE_AND_FIXED_LAW_LIMIT"],
}


def singular_normal_form(expression):
    """Return Singular's normal form over ideal(0), with a real residual."""
    variables = "a,b,c,k,k0,k1,y0,y1,y2,c00,c01,c10,c11,lam,z1,z2"
    code = (
        "ring r=0,(" + variables + "),dp;\n"
        "ideal I=0;\npoly p=" + expression + ";\nreduce(p,I);\nquit;\n"
    )
    run = subprocess.run(
        ["/usr/bin/Singular", "-q"], input=code, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=30,
    )
    if run.returncode != 0:
        raise RuntimeError("Singular failed: " + run.stderr.strip())
    return run.stdout.strip()


def enforce_finite_checks(name, checks):
    """Reject a runtime if any advertised finite check or negative control fails."""
    if not all(checks.values()):
        failed = sorted(key for key, value in checks.items() if not value)
        raise RuntimeError(name + " finite check failed: " + ", ".join(failed))
    return checks


def d1_finite():
    R = PolynomialRing(QQ, "k,c00,c01,c10,c11")
    k, c00, c01, c10, c11 = R.gens()
    H = matrix(R, [[-k, 1]])
    C = matrix(R, [[c00, c01], [c10, c11]])
    expected = c11 - c10*k - k*c01 + k*k*c00
    sage_residual = (H * C * H.transpose())[0, 0] - expected
    singular_residual = singular_normal_form("-k*(-k*c00+c01)+(-k*c10+c11)-(c11-c10*k-k*c01+k^2*c00)")
    negative = singular_normal_form("1")
    return enforce_finite_checks("D1", {
        "sage_scalar_cross_block_residual_zero": sage_residual == 0,
        "singular_scalar_cross_block_normal_form_zero": singular_residual == "0",
        "singular_negative_control_nonzero": negative == "1",
    })


def d3_finite():
    R = PolynomialRing(QQ, "k0,k1,y0,y1,y2")
    k0, k1, y0, y1, y2 = R.gens()
    r0 = y1 - k0*y0
    r1 = y2 - k1*y1
    inverse_one = r0 + k0*y0 - y1
    inverse_two = r1 + k1*(r0 + k0*y0) - y2
    triangular = matrix(R, [[1, 0, 0], [-k0, 1, 0], [0, -k1, 1]])
    singular_one = singular_normal_form("(y1-k0*y0)+k0*y0-y1")
    singular_two = singular_normal_form("(y2-k1*y1)+k1*((y1-k0*y0)+k0*y0)-y2")
    negative = singular_normal_form("1")
    return enforce_finite_checks("D3", {
        "sage_two_step_both_inverse_residuals_zero": inverse_one == 0 and inverse_two == 0,
        "sage_triangular_determinant_one": triangular.det() == 1,
        "singular_two_step_inverse_normal_forms_zero": singular_one == "0" and singular_two == "0",
        "singular_negative_control_nonzero": negative == "1",
    })


def d2_finite():
    R = PolynomialRing(QQ, "lam,z1,z2")
    lam, z1, z2 = R.gens()
    F = R.fraction_field()
    score = F(z1)**2 / F(lam)
    cleared = F(lam)*score - F(z1)**2
    singular_residual = singular_normal_form("lam*(z1^2)-z1^2*lam")
    negative = singular_normal_form("1")
    return enforce_finite_checks("D2", {
        "sage_rank_one_supported_score_cleared_residual_zero": cleared == 0,
        "singular_rank_one_score_cleared_normal_form_zero": singular_residual == "0",
        "singular_negative_control_nonzero": negative == "1",
    })


def d4_finite():
    R = PolynomialRing(QQ, "a,b,c")
    a, b, c = R.gens()
    F = R.fraction_field()
    schur = F(c) - F(b)**2 / F(a)
    cleared = F(a)*schur - (F(a)*F(c) - F(b)**2)
    singular_residual = singular_normal_form("a*c-b^2-(a*c-b^2)")
    negative = singular_normal_form("1")
    return enforce_finite_checks("D4", {
        "sage_scalar_schur_cleared_residual_zero": cleared == 0,
        "singular_scalar_schur_cleared_normal_form_zero": singular_residual == "0",
        "singular_negative_control_nonzero": negative == "1",
    })


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in OBLIGATIONS:
        raise SystemExit("usage: depth_sage_singular_runner_repaired.py D1|D2|D3|D4")
    proposition = sys.argv[1]
    finite_checks = {"D1": d1_finite, "D2": d2_finite, "D3": d3_finite, "D4": d4_finite}[proposition]()
    print(json.dumps({
        "checks": {name: False for name in OBLIGATIONS[proposition]},
        "domain_assumption_diff": [],
        "counterexample": None,
        "computed": {
            "finite_identity_checks": finite_checks,
            "finite_scope_only": True,
            "general_contract_obligations_unverified": True,
        },
    }, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
