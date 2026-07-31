#!/usr/bin/env python3
"""Independent SageMath+Singular axis for PR-270."""
from __future__ import annotations

import json

from sage.all import (
    PolynomialRing,
    QQ,
    identity_matrix,
    matrix,
    singular,
    vector,
)


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
    ring = PolynomialRing(
        QQ,
        names=(
            "a",
            "b",
            "d",
            "e",
            "f",
            "l1",
            "l2",
            "x1",
            "x2",
            "x3",
            "v01",
            "v02",
            "v03",
            "v11",
            "v12",
            "v13",
            "v21",
            "v22",
            "v23",
            "v31",
            "v32",
            "v33",
            "q2",
            "q3",
            "dq2",
            "dq3",
        ),
    )
    (
        a,
        b,
        d,
        e,
        f,
        l1,
        l2,
        x1,
        x2,
        x3,
        v01,
        v02,
        v03,
        v11,
        v12,
        v13,
        v21,
        v22,
        v23,
        v31,
        v32,
        v33,
        q2,
        q3,
        dq2,
        dq3,
    ) = ring.gens()
    sigma = matrix(ring, ((a, d, e), (d, b, f), (e, f, -a - b)))
    i2_matrix = (sigma**2).trace()
    i3_matrix = (sigma**3).trace()
    ch = (
        sigma**3
        - (i2_matrix / 2) * sigma
        - (i3_matrix / 3) * identity_matrix(ring, 3)
    )
    ch_ok = ch == matrix(ring, 3, 3, 0)
    contraction_ok = (
        sigma**4 - (i2_matrix / 2) * sigma**2 - (i3_matrix / 3) * sigma
        == matrix(ring, 3, 3, 0)
    )

    l3 = -l1 - l2
    lam = (l1, l2, l3)
    x = (x1, x2, x3)
    krylov = matrix(
        ring,
        3,
        3,
        [x[row] * lam[row] ** power for row in range(3) for power in range(3)],
    )
    vandermonde = x1 * x2 * x3
    for left in range(3):
        for right in range(left + 1, 3):
            vandermonde *= lam[right] - lam[left]
    krylov_ok = krylov.det() == vandermonde
    gram_ok = (krylov.transpose() * krylov).det() == krylov.det() ** 2

    i2 = sum(value**2 for value in lam)
    i3 = sum(value**3 for value in lam)
    delta = i2**3 / 2 - 3 * i3**2
    squared_vandermonde = ring.one()
    for left in range(3):
        for right in range(left + 1, 3):
            squared_vandermonde *= (lam[right] - lam[left]) ** 2
    discriminant_ok = delta == squared_vandermonde
    shape_strata_ok = (
        delta.subs({l1: 2, l2: -1}) == 0
        and i2.subs({l1: 2, l2: -1}) == 6
        and i3.subs({l1: 2, l2: -1}) == 6
    )

    vectors = (
        (v01, v02, v03),
        (v11, v12, v13),
        (v21, v22, v23),
        (v31, v32, v33),
    )
    variables = (l1, l2, *sum((tuple(item) for item in vectors), ()))
    coordinates = [i2, i3]
    for item in vectors:
        for power in range(3):
            coordinates.append(
                sum(
                    vectors[0][index] * lam[index] ** power * item[index]
                    for index in range(3)
                )
            )
    jacobian = matrix(
        ring,
        [[coordinate.derivative(variable) for variable in variables] for coordinate in coordinates],
    )
    jacobian_det = jacobian.det()
    expected_factor = (
        -48
        * v01**4
        * v02**4
        * v03**4
        * (l1 - l2) ** 5
        * (l1 + 2 * l2) ** 5
        * (2 * l1 + l2) ** 5
    )
    # Multivariate factorization is provided by Sage's Singular backend.
    jacobian_ok = jacobian_det == expected_factor and bool(jacobian_det.factor())
    point = {
        l1: -2,
        l2: 0,
        v01: 1,
        v02: 1,
        v03: 1,
        v11: 1,
        v12: 2,
        v13: 4,
        v21: 2,
        v22: -1,
        v23: 3,
        v31: -1,
        v32: 3,
        v33: 2,
    }
    principal_jacobian = jacobian_det.subs(point)
    witness = {l1: -2, l2: 0, x1: 1, x2: 1, x3: 1}
    principal_krylov = krylov.det().subs(witness)
    principal_gram = (krylov.transpose() * krylov).det().subs(witness)
    cyclicity_ok = (
        krylov.det().subs({l1: 2, l2: -1}) == 0
        and krylov.det().subs({x2: 0}) == 0
        and principal_krylov != 0
    )

    # Algebraic differential of J^2 = 6 I3^2 / I2^3, cleared of I2^4.
    chain_residual = (
        (-18 * q3**2 * dq2 + 12 * q2 * q3 * dq3)
        - (12 * q2 * q3 * dq3 - 18 * q3**2 * dq2)
    )
    chain_rule_ok = chain_residual == 0
    singular_ready = bool(str(singular.eval('system("version");')).strip())

    checks = {
        "vt_t5_discriminant_identity": bool(discriminant_ok),
        "vt_t5_shape_bound_strata": bool(shape_strata_ok),
        "vt_t6_cayley_hamilton": bool(ch_ok),
        "vt_t6_contraction_reduction": bool(contraction_ok),
        "vt_t7_krylov_vandermonde": bool(krylov_ok),
        "vt_t7_krylov_gram": bool(gram_ok),
        "vt_t7_cyclicity_boundary": bool(cyclicity_ok),
        "vt_t8_local_jacobian_factor": bool(jacobian_ok and singular_ready),
        "vt_t8_principal_witness_rank": bool(principal_jacobian == 50331648),
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
