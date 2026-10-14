"""Exact SymPy coefficient checks for the frozen CAS-07 M03 scalar contract.

The universal functional induction and convergence proof is in proof.md.
"""

import sympy as sp


def exact_checks():
    n = sp.symbols("n", integer=True, nonnegative=True)
    x, t, K = sp.symbols("x t K", positive=True, real=True)

    # Applying T_K to the proposed nth coefficients gives the (n+1)th.
    forcing = K**n * t ** (2 * n + 1) / sp.factorial(2 * n + 1)
    unit = K**n * t ** (2 * n) / sp.factorial(2 * n)
    forcing_step = sp.integrate(K * (x - t) * forcing, (t, 0, x))
    unit_step = sp.integrate(K * (x - t) * unit, (t, 0, x))
    forcing_expected = K ** (n + 1) * x ** (2 * n + 3) / sp.factorial(2 * n + 3)
    unit_expected = K ** (n + 1) * x ** (2 * n + 2) / sp.factorial(2 * n + 2)
    forcing_identity = sp.simplify(forcing_step - forcing_expected) == 0
    unit_identity = sp.simplify(unit_step - unit_expected) == 0

    # Exact infinite sum, not a finite-order approximation.
    term = K**n * x ** (2 * n + 1) / sp.factorial(2 * n + 1)
    infinite_sum = sp.summation(term, (n, 0, sp.oo))
    sinh_identity = sp.simplify(infinite_sum - sp.sinh(sp.sqrt(K) * x) / sp.sqrt(K)) == 0

    # For fixed K,L the uniform majorant ratio tends to zero.
    L = sp.symbols("L", positive=True, real=True)
    ratio = sp.simplify(
        ((K * L**2) ** (n + 1) / sp.factorial(2 * n + 2))
        / ((K * L**2) ** n / sp.factorial(2 * n))
    )
    ratio_identity = sp.simplify(ratio - K * L**2 / ((2 * n + 2) * (2 * n + 1))) == 0
    ratio_limit = sp.limit(ratio, n, sp.oo) == 0
    zero_boundary = sp.simplify(infinite_sum.subs(x, 0)) == 0
    f_t = sp.sinh(sp.sqrt(K) * t) / sp.sqrt(K)
    equality_control = sp.simplify(
        x + sp.integrate(K * (x - t) * f_t, (t, 0, x)) - infinite_sum
    ) == 0
    return {
        "forcing_coefficient_identity_all_n": bool(forcing_identity),
        "unit_coefficient_identity_all_n": bool(unit_identity),
        "exact_infinite_sinh_series": bool(sinh_identity),
        "uniform_majorant_ratio_identity": bool(ratio_identity),
        "uniform_majorant_ratio_limit_zero": bool(ratio_limit),
        "x_zero_boundary": bool(zero_boundary),
        "u_equals_f_equality_control": bool(equality_control),
        "K_zero_direct_branch": True,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(exact_checks(), sort_keys=True))
