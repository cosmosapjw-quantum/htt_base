"""Independent SymPy checks for the frozen CAS-07 M02 scalar obligation.

The quantified absolute-integral argument is in PROOF.md. SymPy checks its
algebraic/FTC ingredients; finite examples are ancillary and do not restrict Z.
"""

from __future__ import annotations

import sympy as sp


def check() -> dict:
    t = sp.symbols("t", real=True)
    s = sp.symbols("s", real=True, nonnegative=True)
    L = sp.symbols("L", real=True, positive=True)
    c = sp.symbols("c", real=True, positive=True)
    M2 = sp.symbols("M2", real=True, nonnegative=True)
    Z = sp.Function("Z")  # Arbitrary differentiable real function, not a polynomial ansatz.

    z1 = sp.diff(Z(t), t)
    z2 = sp.diff(Z(t), t, 2)
    product = (s - t) * z1
    product_rule = sp.simplify(sp.diff(product, t) - ((s - t) * z2 - z1)) == 0
    endpoint = sp.simplify(product.subs(t, s) - product.subs(t, 0))
    endpoint_expected = -s * sp.Subs(z1, t, 0)
    endpoint_ok = sp.simplify(endpoint - endpoint_expected) == 0

    # SymPy performs the FTC and integration by parts on an arbitrary Function.
    ftc_z1 = sp.integrate(z1, (t, 0, s))
    ftc_ok = sp.simplify(ftc_z1 - (Z(s) - Z(0))) == 0
    weighted_z2 = sp.integrate((s - t) * z2, (t, 0, s))
    target = Z(s) - Z(0) - s * sp.Subs(z1, t, 0)
    ibp_ok = sp.simplify(weighted_z2 - target) == 0
    schema_ok = sp.simplify(endpoint + ftc_z1 - target) == 0

    H0 = c * sp.Subs(z1, t, 0)
    physical_notation_ok = sp.simplify(target - (Z(s) - Z(0) - H0 * s / c)) == 0

    weight = sp.integrate(s - t, (t, 0, s))
    weight_ok = sp.simplify(weight - s**2 / 2) == 0
    bound_expression_ok = sp.simplify(M2 * weight - M2 * s**2 / 2) == 0

    # Ancillary endpoint and saturation checks; neither is used as a universal proof.
    a, b = sp.symbols("a b", real=True)
    affine = a + b * t
    affine_remainder = sp.simplify(
        affine.subs(t, s) - affine.subs(t, 0) - s * sp.diff(affine, t).subs(t, 0)
    )
    quadratic = a + b * t + M2 * t**2 / 2
    quadratic_remainder = sp.simplify(
        quadratic.subs(t, s) - quadratic.subs(t, 0)
        - s * sp.diff(quadratic, t).subs(t, 0)
    )
    examples_ok = bool(
        affine_remainder == 0
        and sp.simplify(quadratic_remainder - M2 * s**2 / 2) == 0
        and sp.simplify(target.subs(s, 0)) == 0
    )

    identity_ok = bool(
        product_rule and endpoint_ok and ftc_ok and ibp_ok
        and schema_ok and physical_notation_ok
    )
    bound_ok = bool(identity_ok and weight_ok and bound_expression_ok)

    return {
        "checks": {
            "CAS-07-M02-REMAINDER-IDENTITY": identity_ok,
            "CAS-07-M02-REMAINDER-BOUND": bound_ok,
        },
        "domain_assumption_diff": [],
        "counterexample": None,
        "sympy_version": sp.__version__,
        "symbolic_evidence": {
            "product_rule": bool(product_rule),
            "endpoint": bool(endpoint_ok),
            "ftc_Z1": bool(ftc_ok),
            "weighted_Z2_ibp": bool(ibp_ok),
            "ibp_schema": bool(schema_ok),
            "H0_definition": bool(physical_notation_ok),
            "weight_integral": bool(weight_ok),
            "bound_algebra": bool(bound_expression_ok),
            "ancillary_examples": bool(examples_ok),
            "weighted_Z2_result": str(weighted_z2),
            "weight_result": str(weight),
            "L_symbol_positive": bool(L.is_positive),
        },
        "universal_inequality_argument": "PROOF.md",
        "scope": "integral_Taylor_prerequisite_only_no_scientific_admission",
    }
