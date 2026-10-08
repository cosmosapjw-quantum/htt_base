#!/usr/bin/env python3
"""Independent SymPy check of the frozen PORT-CAS-01 finite algebra contract."""

import json
import sys
import traceback

import sympy as sp


def boost(gamma, beta):
    h = gamma**2 / (gamma + 1)
    spatial = sp.eye(3) + h * (beta * beta.T)
    return sp.Matrix.vstack(
        sp.Matrix.hstack(sp.Matrix([[gamma]]), gamma * beta.T),
        sp.Matrix.hstack(gamma * beta, spatial),
    )


def exact_remainder_zero(expr, gamma, relation, coefficient_field):
    """Prove a rational expression vanishes in Q(beta)[gamma]/(relation)."""
    numerator, denominator = sp.fraction(sp.cancel(expr))
    poly = sp.Poly(numerator, gamma, domain=coefficient_field)
    modulus = sp.Poly(relation, gamma, domain=coefficient_field)
    remainder = poly.rem(modulus)
    return remainder.is_zero, sp.factor(denominator), str(remainder.as_expr())


def numeric_residuals(beta):
    s = (beta.T * beta)[0]
    gamma = 1 / sp.sqrt(1 - s)
    eta = sp.diag(-1, 1, 1, 1)
    b = boost(gamma, beta)
    bm = boost(gamma, -beta)
    u = b[:, 0]
    residuals = list(b.T * eta * b - eta)
    residuals += list(b * bm - sp.eye(4))
    residuals += list(u - sp.Matrix([gamma, *(gamma * beta)]))
    residuals += [(u.T * eta * u)[0] + 1]
    return max(abs(sp.N(x, 80)) for x in residuals)


def main():
    b1, b2, b3 = sp.symbols("b1 b2 b3", real=True)
    gamma = sp.symbols("gamma", positive=True)
    beta = sp.Matrix([b1, b2, b3])
    s = (beta.T * beta)[0]
    relation = gamma**2 * (1 - s) - 1
    field = sp.QQ.frac_field(b1, b2, b3)
    eta = sp.diag(-1, 1, 1, 1)
    b = boost(gamma, beta)
    bm = boost(gamma, -beta)
    u = b[:, 0]

    metric_residual = b.T * eta * b - eta
    inverse_residual = b * bm - sp.eye(4)
    velocity_residual = u - sp.Matrix([gamma, gamma * b1, gamma * b2, gamma * b3])
    shell_residual = (u.T * eta * u)[0] + 1
    expressions = list(metric_residual) + list(inverse_residual)
    expressions += list(velocity_residual) + [shell_residual]
    reductions = [exact_remainder_zero(x, gamma, relation, field) for x in expressions]
    matrix_exact = all(ok for ok, _, _ in reductions)

    # The only nonconstant denominator introduced by the boost is gamma+1.
    # gamma>0 in the admitted branch, so it never vanishes. The coefficient
    # field denominators used for reduction are algebraic bookkeeping only.
    denominator_forms = sorted(set(d for _, d, _ in reductions), key=str)
    # Validate each denominator has one admissible gamma+1 power.
    denominator_safe = all(
        any(
            sp.simplify(d / (gamma + 1) ** k).is_number
            and sp.simplify(d / (gamma + 1) ** k) != 0
            for k in range(0, 5)
        )
        for d in denominator_forms
    )

    z0 = sp.symbols("z0", positive=True)
    z1, z2, z3 = sp.symbols("z1 z2 z3", real=True)
    z = sp.Matrix([z1, z2, z3])
    zsum = (z.T * z)[0]
    shell_relation = z0**2 - zsum - 1
    beta_converse = z / z0
    bnorm = (beta_converse.T * beta_converse)[0]
    norm_identity = sp.cancel((1 - bnorm) - 1 / z0**2 - shell_relation / z0**2) == 0
    reciprocal_positive = sp.ask(sp.Q.positive(1 / z0**2), sp.Q.positive(z0)) is True
    # On the shell, 1-|beta|^2=1/z0^2>0. z0>=1 gives z0>0;
    # the nonnegative real sqrt yields gamma=1/sqrt(1/z0^2)=z0.
    gamma_on_shell = sp.simplify(1 / sp.sqrt(1 / z0**2))
    branch_exact = gamma_on_shell == z0
    reconstructed = sp.Matrix([gamma_on_shell, *(gamma_on_shell * beta_converse)])
    converse_exact = sp.simplify(reconstructed - sp.Matrix([z0, z1, z2, z3])) == sp.zeros(4, 1)
    future_exact = gamma.is_positive is True and z0.is_positive is True

    zero_beta = sp.zeros(3, 1)
    boundary_exact = boost(sp.Integer(1), zero_beta) == sp.eye(4)
    boundary_exact &= sp.Matrix(boost(sp.Integer(1), zero_beta)[:, 0]) == sp.Matrix([1, 0, 0, 0])

    examples = [
        sp.Matrix([0, 0, 0]),
        sp.Matrix([sp.Rational(1, 5), -sp.Rational(1, 10), sp.Rational(1, 20)]),
    ]
    numeric_max = max(numeric_residuals(v) for v in examples)
    zeta = sp.Matrix([sp.Rational(5, 4), sp.Rational(3, 4), 0, 0])
    zeta_beta = zeta[1:4, 0] / zeta[0]
    zeta_rebuilt = boost(1 / sp.sqrt(1 - (zeta_beta.T * zeta_beta)[0]), zeta_beta)[:, 0]
    zeta_numeric_max = max(abs(sp.N(x, 80)) for x in zeta_rebuilt - zeta)
    numeric_ok = numeric_max < sp.Float("1e-50", 80) and zeta_numeric_max < sp.Float("1e-50", 80)

    exact_ok = all((matrix_exact, denominator_safe, norm_identity, reciprocal_positive, branch_exact,
                    converse_exact, future_exact, boundary_exact))
    print(json.dumps({
        "checks": {"PORT-CAS-01": bool(exact_ok and numeric_ok)},
        "domain_assumption_diff": [],
        "counterexample": None,
    }, separators=(",", ":")))
    print(json.dumps({
        "sympy_version": sp.__version__,
        "exact_reductions": len(reductions),
        "nonzero_remainders": [r for ok, _, r in reductions if not ok],
        "denominators": [str(d) for d in denominator_forms],
        "matrix_exact": matrix_exact,
        "denominator_safe": denominator_safe,
        "norm_identity": norm_identity,
        "reciprocal_positive": reciprocal_positive,
        "branch_exact": branch_exact,
        "converse_exact": converse_exact,
        "future_exact": future_exact,
        "boundary_exact": boundary_exact,
        "numeric_max_80_digits": str(numeric_max),
        "zeta_numeric_max_80_digits": str(zeta_numeric_max),
        "numeric_ok": bool(numeric_ok),
    }, sort_keys=True), file=sys.stderr)
    return 0 if exact_ok and numeric_ok else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        print(json.dumps({
            "checks": {"PORT-CAS-01": False},
            "domain_assumption_diff": [],
            "counterexample": None,
        }, separators=(",", ":")))
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
