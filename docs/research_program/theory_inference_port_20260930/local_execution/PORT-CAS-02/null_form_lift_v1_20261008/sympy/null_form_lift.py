#!/usr/bin/env python3
"""Independent exact SymPy axis for frozen PORT-CAS-02 finite algebra."""

from __future__ import annotations

import json
import sys

import sympy as sp


def zero_matrix(value: sp.MatrixBase) -> bool:
    return all(sp.cancel(entry) == 0 for entry in value)


def main() -> int:
    h0, st, gauge = sp.symbols("h0 st gauge", real=True)
    h1 = sp.Matrix(sp.symbols("h1x h1y h1z", real=True))
    nx, ny, nz = sp.symbols("nx ny nz", real=True)
    n = sp.Matrix([nx, ny, nz])
    qxx, qyy, qzz, qxy, qxz, qyz = sp.symbols(
        "qxx qyy qzz qxy qxz qyz", real=True
    )
    q = sp.Matrix(
        [[qxx, qxy, qxz], [qxy, qyy, qyz], [qxz, qyz, qzz]]
    )
    g = sp.diag(-1, 1, 1, 1)
    K = sp.Matrix([-1, nx, ny, nz])
    S = sp.zeros(4)
    S[0, 0] = h0
    for i in range(3):
        S[0, i + 1] = S[i + 1, 0] = -h1[i] / 2
        for j in range(3):
            S[i + 1, j + 1] = q[i, j]
    B = S - st * g
    u = sp.Matrix(sp.symbols("u0 u1 u2 u3", real=True))
    mixed_S = g * S  # g^{-1}=g in this signature
    eigen_residual = mixed_S * u - st * u
    kernel_residual = B * u
    null_constraint = (n.dot(n) - 1).expand()
    null_form = h0 + h1.dot(n) + (n.T * q * n)[0]
    trace = sp.trace(q)
    q_tf = q - trace * sp.eye(3) / 3
    shifted_S = S + gauge * g
    shifted_st = st + gauge

    checks = {
        "metric_inverse_and_signature": zero_matrix(g * g - sp.eye(4)),
        "S_covariant_symmetric": zero_matrix(S - S.T),
        "B_covariant_symmetric": zero_matrix(B - B.T),
        "gKK_equals_n_squared_minus_one": sp.expand((K.T * g * K)[0] - null_constraint) == 0,
        "S_null_polynomial_full_signs": sp.expand((K.T * S * K)[0] - null_form) == 0,
        "B_null_equals_S_null_on_unit_sphere": sp.expand(
            (K.T * B * K)[0] - (K.T * S * K)[0] + st * null_constraint
        ) == 0,
        "kernel_is_metric_lowered_eigen_residual": zero_matrix(kernel_residual - g * eigen_residual),
        "eigen_residual_is_metric_raised_kernel": zero_matrix(eigen_residual - g * kernel_residual),
        "trace_decomposition": zero_matrix(q - q_tf - trace * sp.eye(3) / 3),
        "q_tf_is_tracefree": sp.expand(sp.trace(q_tf)) == 0,
        "spatial_monopole_is_trace_over_three": sp.expand(
            (n.T * (q - q_tf) * n)[0] - trace * n.dot(n) / 3
        ) == 0,
        "kernel_equivalence_independent_of_tracefree": zero_matrix(
            (kernel_residual - g * eigen_residual).subs(qzz, -qxx - qyy)
        ),
        "gauge_B_invariance": zero_matrix(shifted_S - shifted_st * g - B),
        "gauge_mixed_eigen_residual_invariance": zero_matrix(
            g * shifted_S * u - shifted_st * u - eigen_residual
        ),
        "gauge_null_shift_is_metric_null": sp.expand(
            (K.T * shifted_S * K)[0] - (K.T * S * K)[0] - gauge * null_constraint
        ) == 0,
    }

    numeric = {h0: 2, h1[0]: 1, h1[1]: -2, h1[2]: 3,
               qxx: 1, qyy: -1, qzz: 0, qxy: 0, qxz: 0, qyz: 0,
               nx: 1, ny: 0, nz: 0, st: 7}
    checks["contract_vector_gKK_zero"] = (K.T * g * K)[0].subs(numeric) == 0
    checks["contract_vector_SKK_equals_four"] = (K.T * S * K)[0].subs(numeric) == 4
    checks["contract_vector_BKK_equals_four"] = (K.T * B * K)[0].subs(numeric) == 4

    # An exact future unit timelike eigenpair with tracefree spatial q.
    eigen_case = {h0: -2, h1[0]: 0, h1[1]: 0, h1[2]: 0,
                  qxx: 1, qyy: -1, qzz: 0, qxy: 0, qxz: 0, qyz: 0, st: 2,
                  u[0]: 1, u[1]: 0, u[2]: 0, u[3]: 0}
    checks["future_unit_eigenpair_u_squared_minus_one"] = (
        (u.T * g * u)[0].subs(eigen_case) == -1
    )
    checks["future_unit_eigenpair_kernel_zero"] = zero_matrix(kernel_residual.subs(eigen_case))
    checks["future_unit_eigenpair_mixed_residual_zero"] = zero_matrix(eigen_residual.subs(eigen_case))
    isotropic_S = st * g
    checks["contract_degenerate_vector_S_equals_st_g_gives_B_zero"] = zero_matrix(isotropic_S - st * g)
    checks["contract_degenerate_vector_null_contraction_zero"] = sp.expand(
        (K.T * isotropic_S * K)[0] - st * null_constraint
    ) == 0

    output = {
        "schema": "port-cas02.sympy.exact-check.v1",
        "axis": "sympy",
        "status": "PASS" if all(bool(value) for value in checks.values()) else "FAIL",
        "sympy_version": sp.__version__,
        "python_version": sys.version.split()[0],
        "checks": {key: bool(value) for key, value in checks.items()},
        "canonical": {
            "g_K_K": "nx**2 + ny**2 + nz**2 - 1",
            "S_K_K": str(sp.expand((K.T * S * K)[0])),
            "B_K_K_minus_S_K_K": str(sp.expand((K.T * B * K)[0] - (K.T * S * K)[0])),
            "iff_witness": "B*u = g*(g*S*u-st*u), and g*(B*u)=g*S*u-st*u because g*g=I",
            "tracefree_relation": "q=q_tf+(tr(q)/3)I; on n.n=1 monopole=tr(q)/3",
            "gauge_relation": "(S+a*g)-(st+a)*g=B; S'KK-SKK=a*(n.n-1)",
        },
        "domain_alignment": [
            "real symbols; symmetric q; tracefree restriction qzz=-qxx-qyy",
            "g=diag(-1,1,1,1), K=(-1,n), n.n=1",
            "u future unit timelike only for physical interpretation; iff algebra holds for every u",
            "no eigenline existence, uniqueness, geodesicity, vorticity, or inference conclusion",
        ],
    }
    print(json.dumps(output, sort_keys=True))
    return 0 if output["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
