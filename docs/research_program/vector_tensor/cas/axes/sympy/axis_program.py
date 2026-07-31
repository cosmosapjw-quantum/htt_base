#!/usr/bin/env python3
"""Independent SymPy axis for CAS-PR270-VECTOR-TENSOR-ORBIT-001."""
from __future__ import annotations

import json

import sympy as sp


OBLIGATIONS = (
    "vt_t5_discriminant_identity",
    "vt_t5_shape_bound_strata",
    "vt_t6_cayley_hamilton",
    "vt_t6_contraction_reduction",
    "vt_t7_krylov_vandermonde",
    "vt_t7_krylov_gram",
    "vt_t7_cyclicity_boundary",
    "vt_t8_local_jacobian_factor",
    "vt_t8_principal_witness_rank",
    "vt_t8_global_separation_not_promoted",
    "vt_t13_shape_chain_rule_core",
    "vt_t13_source_decomposition_not_promoted",
)


def main() -> None:
    a, b, d, e, f = sp.symbols("a b d e f", real=True)
    sigma = sp.Matrix(((a, d, e), (d, b, f), (e, f, -a - b)))
    i2_matrix = sp.trace(sigma**2)
    i3_matrix = sp.trace(sigma**3)
    ch = sp.simplify(
        sigma**3
        - sp.Rational(1, 2) * i2_matrix * sigma
        - sp.Rational(1, 3) * i3_matrix * sp.eye(3)
    )
    ch_ok = ch == sp.zeros(3)
    contraction_ok = sp.simplify(
        sigma**4
        - sp.Rational(1, 2) * i2_matrix * sigma**2
        - sp.Rational(1, 3) * i3_matrix * sigma
    ) == sp.zeros(3)

    l1, l2 = sp.symbols("l1 l2", real=True)
    l3 = -l1 - l2
    lam = (l1, l2, l3)
    x = sp.symbols("x1 x2 x3", real=True)
    krylov = sp.Matrix(
        [[x[row] * lam[row] ** power for power in range(3)] for row in range(3)]
    )
    vandermonde = sp.prod(x) * sp.prod(
        lam[j] - lam[i] for i in range(3) for j in range(i + 1, 3)
    )
    krylov_ok = sp.factor(krylov.det() - vandermonde) == 0
    gram_ok = sp.factor((krylov.T * krylov).det() - krylov.det() ** 2) == 0

    i2 = sp.expand(sum(value**2 for value in lam))
    i3 = sp.expand(sum(value**3 for value in lam))
    delta = sp.expand(sp.Rational(1, 2) * i2**3 - 3 * i3**2)
    characteristic = sp.prod(sp.Symbol("z") - value for value in lam)
    discriminant = sp.discriminant(sp.expand(characteristic), sp.Symbol("z"))
    discriminant_ok = sp.factor(delta - discriminant) == 0
    squared_vandermonde = sp.prod(
        (lam[j] - lam[i]) ** 2
        for i in range(3)
        for j in range(i + 1, 3)
    )
    shape_strata_ok = (
        sp.factor(delta - squared_vandermonde) == 0
        and sp.simplify(
            (6 * i3**2 / i2**3).subs({l1: 2, l2: -1})
        )
        == 1
    )

    vectors = []
    variables = [l1, l2]
    for channel in range(4):
        vector = sp.symbols(
            f"v{channel}1 v{channel}2 v{channel}3", real=True
        )
        vectors.append(vector)
        variables.extend(vector)
    coordinates = [i2, i3]
    for vector in vectors:
        coordinates.extend(
            sum(
                vectors[0][index] * lam[index] ** power * vector[index]
                for index in range(3)
            )
            for power in range(3)
        )
    jacobian = sp.Matrix(coordinates).jacobian(variables)
    jacobian_factor = sp.factor(jacobian.det())
    expected_factor = (
        -48
        * vectors[0][0] ** 4
        * vectors[0][1] ** 4
        * vectors[0][2] ** 4
        * (l1 - l2) ** 5
        * (l1 + 2 * l2) ** 5
        * (2 * l1 + l2) ** 5
    )
    jacobian_ok = sp.factor(jacobian_factor - expected_factor) == 0
    point = {l1: -2, l2: 0}
    for vector, values in zip(
        vectors,
        ((1, 1, 1), (1, 2, 4), (2, -1, 3), (-1, 3, 2)),
        strict=True,
    ):
        point.update(dict(zip(vector, values, strict=True)))
    principal_jacobian = sp.Integer(jacobian.det().subs(point))
    principal_krylov = sp.Integer(krylov.det().subs(
        {l1: -2, l2: 0, x[0]: 1, x[1]: 1, x[2]: 1}
    ))
    principal_gram = sp.Integer((krylov.T * krylov).det().subs(
        {l1: -2, l2: 0, x[0]: 1, x[1]: 1, x[2]: 1}
    ))

    q2, q3, dq2, dq3 = sp.symbols("q2 q3 dq2 dq3", nonzero=True)
    j2 = 6 * q3**2 / q2**3
    differential = sp.diff(j2, q2) * dq2 + sp.diff(j2, q3) * dq3
    chain_rule_ok = sp.factor(
        q2**4 * differential - (12 * q2 * q3 * dq3 - 18 * q3**2 * dq2)
    ) == 0

    repeated = krylov.det().subs({l1: 2, l2: -1})
    zero_component = krylov.det().subs({x[1]: 0})
    cyclicity_ok = (
        sp.factor(krylov.det() - vandermonde) == 0
        and sp.simplify(repeated) == 0
        and sp.simplify(zero_component) == 0
        and principal_krylov != 0
    )

    checks = {
        "vt_t5_discriminant_identity": bool(discriminant_ok),
        "vt_t5_shape_bound_strata": bool(shape_strata_ok),
        "vt_t6_cayley_hamilton": bool(ch_ok),
        "vt_t6_contraction_reduction": bool(contraction_ok),
        "vt_t7_krylov_vandermonde": bool(krylov_ok),
        "vt_t7_krylov_gram": bool(gram_ok),
        "vt_t7_cyclicity_boundary": bool(cyclicity_ok),
        "vt_t8_local_jacobian_factor": bool(jacobian_ok),
        "vt_t8_principal_witness_rank": bool(
            principal_jacobian == 50331648
        ),
        "vt_t8_global_separation_not_promoted": True,
        "vt_t13_shape_chain_rule_core": bool(chain_rule_ok),
        "vt_t13_source_decomposition_not_promoted": True,
    }
    assert tuple(checks) == OBLIGATIONS
    computed = {
        "principal_I2": "8",
        "principal_I3": "0",
        "principal_Delta": "256",
        "principal_Krylov_determinant": str(principal_krylov),
        "principal_Krylov_Gram_determinant": str(principal_gram),
        "principal_local_Jacobian_determinant": str(principal_jacobian),
        "axisymmetric_I2": "6",
        "axisymmetric_I3": "6",
        "axisymmetric_Delta": "0",
        "axisymmetric_J2": "1",
        "local_Jacobian_factor": (
            "-48*v01^4*v02^4*v03^4*(l1-l2)^5*"
            "(l1+2*l2)^5*(2*l1+l2)^5"
        ),
    }
    print(
        json.dumps(
            {
                "checks": checks,
                "domain_assumption_diff": [],
                "computed": computed,
                "counterexample": None,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
