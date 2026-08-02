#!/usr/bin/env python3
"""Independent SymPy axis for the PR-190 normal-vorticity obstruction."""

from __future__ import annotations

import json

import sympy as sp


OBLIGATIONS = (
    "normal_spatial_vorticity_zero",
    "normal_frame_w2_zero",
    "registered_lower_w2_positive",
    "lower_endpoint_same_frame_contradiction",
    "registered_interior_w2_positive",
    "interior_endpoint_same_frame_contradiction",
    "refuted_constraint_cannot_promote",
)


def main() -> None:
    t = sp.symbols("t", real=True)
    lapse = sp.Function("N")(t)
    # In the adapted homogeneous chart n_mu=(-N(t),0,0,0).  Every projected
    # spatial component n_i and every spatial derivative d_i N is zero.
    n_spatial = sp.zeros(3, 1)
    spatial_derivative = sp.zeros(3, 3)
    vorticity = sp.simplify(
        (spatial_derivative - spatial_derivative.T) / 2
    )
    omega_squared = sp.simplify(sum(value**2 for value in vorticity))
    theta = sp.symbols("Theta", nonzero=True, real=True)
    normal_w2 = sp.simplify(3 * omega_squared / theta**2)
    registered_lower_w2 = sp.Rational(1, 25)
    registered_interior_w2 = sp.Rational(3, 100)
    lower_contradiction_residual = sp.simplify(
        registered_lower_w2 - normal_w2
    )
    interior_contradiction_residual = sp.simplify(
        registered_interior_w2 - normal_w2
    )
    algebraic_attained = sp.true
    constraint_attained = sp.false
    local_attained = sp.symbols("local_attained", boolean=True)
    global_attained = sp.symbols("global_attained", boolean=True)
    full_programme = sp.And(
        algebraic_attained,
        constraint_attained,
        local_attained,
        global_attained,
    )
    checks = {
        "normal_spatial_vorticity_zero": bool(
            n_spatial == sp.zeros(3, 1) and vorticity == sp.zeros(3)
        ),
        "normal_frame_w2_zero": bool(normal_w2 == 0),
        "registered_lower_w2_positive": bool(registered_lower_w2 > 0),
        "lower_endpoint_same_frame_contradiction": bool(
            lower_contradiction_residual == registered_lower_w2
            and normal_w2 != registered_lower_w2
        ),
        "registered_interior_w2_positive": bool(registered_interior_w2 > 0),
        "interior_endpoint_same_frame_contradiction": bool(
            interior_contradiction_residual == registered_interior_w2
            and normal_w2 != registered_interior_w2
        ),
        "refuted_constraint_cannot_promote": bool(
            sp.simplify(full_programme) is sp.false
        ),
    }
    assert tuple(checks) == OBLIGATIONS
    del lapse
    print(
        json.dumps(
            {
                "checks": checks,
                "computed": {
                    "normal_omega_squared": str(omega_squared),
                    "normal_W2": str(normal_w2),
                    "registered_lower_W2": "1/25",
                    "registered_interior_W2": "3/100",
                    "lower_contradiction_residual": "1/25",
                    "interior_contradiction_residual": "3/100",
                },
                "counterexample": None,
                "domain_assumption_diff": [],
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
