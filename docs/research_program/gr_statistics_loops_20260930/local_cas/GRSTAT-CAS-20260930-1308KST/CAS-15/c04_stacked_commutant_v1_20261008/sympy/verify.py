#!/usr/bin/env python3
"""Independent exact SymPy certificate for CAS-15-C04.

This source uses only the frozen contract and admitted neutral inputs.  The
orthonormal skew basis is E_i = hat(e_i)/sqrt(2), where hat(w)x = w cross x.
"""

from __future__ import annotations

import json
import platform
import sys

import sympy as sp


def hat(w: sp.Matrix) -> sp.Matrix:
    w1, w2, w3 = w
    return sp.Matrix(
        [
            [0, -w3, w2],
            [w3, 0, -w1],
            [-w2, w1, 0],
        ]
    )


def frobenius(a: sp.Matrix, b: sp.Matrix) -> sp.Expr:
    return sp.expand(sp.trace(a.T * b))


def commutator(m: sp.Matrix, w: sp.Matrix) -> sp.Matrix:
    return sp.expand(m * w - w * m)


def gram(channels: list[sp.Matrix], basis: list[sp.Matrix]) -> sp.Matrix:
    responses = [[commutator(m, e) for e in basis] for m in channels]
    return sp.Matrix(
        len(basis),
        len(basis),
        lambda i, j: sp.expand(
            sum(frobenius(r[i], r[j]) for r in responses)
        ),
    )


def zero_matrix(m: sp.Matrix) -> bool:
    return all(sp.simplify(x) == 0 for x in m)


def main() -> int:
    alpha, beta, beta1, beta2 = sp.symbols(
        "alpha beta beta1 beta2", real=True
    )
    w1, w2, w3 = sp.symbols("w1 w2 w3", real=True)
    s, c = sp.symbols("s c", real=True)
    w = sp.Matrix([w1, w2, w3])
    eye = sp.eye(3)
    std = [sp.eye(3).col(i) for i in range(3)]
    basis = [hat(e) / sp.sqrt(2) for e in std]

    # The basis is exactly Frobenius orthonormal.
    basis_gram = sp.Matrix(
        3, 3, lambda i, j: sp.simplify(frobenius(basis[i], basis[j]))
    )
    basis_orthonormal = basis_gram == sp.eye(3)

    # Generic symmetric channel: establish the response Gram definition and
    # the real sum-of-squares identity ker(A^T A)=ker(A).
    m11, m22, m33, m12, m13, m23 = sp.symbols(
        "m11 m22 m33 m12 m13 m23", real=True
    )
    mg = sp.Matrix(
        [[m11, m12, m13], [m12, m22, m23], [m13, m23, m33]]
    )
    cols = []
    for e in basis:
        r = commutator(mg, e)
        cols.append(sp.Matrix(list(r)))
    response_matrix = sp.Matrix.hstack(*cols)
    generic_gram = gram([mg], basis)
    gram_is_ata = zero_matrix(generic_gram - response_matrix.T * response_matrix)
    quadratic_sos = sp.simplify(
        (w.T * generic_gram * w)[0]
        - sum(x**2 for x in response_matrix * w)
    ) == 0

    # Axisymmetric formula.  Canonical axes below lose no information because
    # simultaneous orthogonal conjugation preserves Frobenius products, rank,
    # kernels and commutators.
    n = sp.Matrix(sp.symbols("n1 n2 n3", real=True))
    mn = alpha * eye + beta * n * n.T
    gn = gram([mn], basis)
    n_sq = sp.expand(n.dot(n))
    expected_gn = sp.expand(beta**2 * n_sq * (n_sq * eye - n * n.T))
    axis_formula = zero_matrix(gn - expected_gn)

    # The matrix commutator vanishes exactly with W n: both squared norms are
    # related by an exact factor on the unit-axis locus.
    wn = (hat(w) / sp.sqrt(2)) * n
    comm_n = commutator(mn, hat(w) / sp.sqrt(2))
    comm_norm_relation = sp.simplify(
        frobenius(comm_n, comm_n) - 2 * beta**2 * n_sq * (wn.dot(wn))
    ) == 0

    # One nonisotropic unit axis, fixed to e3 by an orthogonal frame change.
    n1_axis = sp.Matrix([0, 0, 1])
    m1 = alpha * eye + beta1 * n1_axis * n1_axis.T
    g1 = sp.simplify(gram([m1], basis))
    g1_expected = sp.diag(beta1**2, beta1**2, 0)
    one_axis_formula = zero_matrix(g1 - g1_expected)
    one_axis_rank2 = g1.rank(iszerofunc=lambda x: sp.simplify(x) == 0) == 2
    one_axis_kernel = g1.nullspace() == [sp.Matrix([0, 0, 1])]
    one_axis_comm_solution = sp.linsolve(
        list(commutator(m1, hat(w) / sp.sqrt(2))), (w1, w2, w3)
    ) == sp.FiniteSet((0, 0, w3))

    # A second unit axis can be placed in the x-z plane as (s,0,c), with
    # s^2+c^2=1.  Nonparallelity is s != 0.
    n2_axis = sp.Matrix([s, 0, c])
    m2 = alpha * eye + beta2 * n2_axis * n2_axis.T
    g12_raw = sp.simplify(gram([m1, m2], basis))
    response12_columns = []
    for e in basis:
        response12_columns.append(
            sp.Matrix(list(commutator(m1, e)) + list(commutator(m2, e)))
        )
    response12 = sp.Matrix.hstack(*response12_columns)
    two_axis_gram_is_ata = zero_matrix(g12_raw - response12.T * response12)
    two_axis_quadratic_sos = sp.simplify(
        (w.T * g12_raw * w)[0] - sum(x**2 for x in response12 * w)
    ) == 0
    g12_expected_raw = sp.expand(
        beta1**2 * (eye - n1_axis * n1_axis.T)
        + beta2**2
        * (s**2 + c**2)
        * ((s**2 + c**2) * eye - n2_axis * n2_axis.T)
    )
    two_axis_formula = zero_matrix(g12_raw - g12_expected_raw)

    unit_reduce = {s**2: 1 - c**2}
    det_raw = sp.factor(g12_raw.det())
    det_unit = sp.factor(det_raw.subs(unit_reduce))
    det_expected = beta1**2 * beta2**2 * (beta1**2 + beta2**2) * s**2
    det_expected_unit = sp.factor(det_expected.subs(unit_reduce))
    two_axis_det = sp.simplify(det_unit - det_expected_unit) == 0

    # Exact common-commutant solve: W e3=0 forces w1=w2=0, and then
    # W(s,0,c)=0 with s!=0 forces w3=0.
    eq_common = list((hat(w) / sp.sqrt(2)) * n1_axis) + list(
        (hat(w) / sp.sqrt(2)) * n2_axis
    )
    common_solution_generic = sp.linsolve(eq_common, (w1, w2, w3))
    # SymPy works over the rational function field in s,c, hence s is generic
    # nonzero here, exactly the contracted nonparallel chart.
    common_kernel_zero = common_solution_generic == sp.FiniteSet((0, 0, 0))

    # G=A^T A is positive semidefinite over R.  On beta1 beta2 s != 0 its
    # exact positive determinant proves nonsingularity, so the Gram is PD and
    # rank three.  Record the algebraic rank as a separate exact check.
    two_axis_rank3 = g12_raw.rank(iszerofunc=lambda x: sp.simplify(x) == 0) == 3
    determinant_positive_conditions = ["beta1!=0", "beta2!=0", "s!=0"]
    positive_definite_certificate = (
        two_axis_gram_is_ata
        and two_axis_quadratic_sos
        and two_axis_det
        and common_kernel_zero
        and determinant_positive_conditions
        == ["beta1!=0", "beta2!=0", "s!=0"]
    )

    # Required singular controls.
    g_isotropic = sp.simplify(g1.subs(beta1, 0))
    isotropic_zero = zero_matrix(g_isotropic) and g_isotropic.rank() == 0
    g_parallel = sp.simplify(
        gram(
            [
                alpha * eye + beta1 * n1_axis * n1_axis.T,
                alpha * eye + beta2 * n1_axis * n1_axis.T,
            ],
            basis,
        )
    )
    parallel_expected = sp.diag(beta1**2 + beta2**2, beta1**2 + beta2**2, 0)
    parallel_control = (
        zero_matrix(g_parallel - parallel_expected)
        and g_parallel.rank(iszerofunc=lambda x: sp.simplify(x) == 0) == 2
        and g_parallel.nullspace() == [sp.Matrix([0, 0, 1])]
    )

    subchecks = {
        "orthonormal_skew_basis": basis_orthonormal,
        "generic_gram_equals_response_transpose_response": gram_is_ata,
        "generic_kernel_sum_of_squares_identity": quadratic_sos,
        "axisymmetric_gram_formula": axis_formula,
        "axisymmetric_commutator_norm_relation": comm_norm_relation,
        "one_axis_formula": one_axis_formula,
        "one_axis_rank_two": one_axis_rank2,
        "one_axis_kernel_span_axis": one_axis_kernel,
        "one_axis_commutant_solution": one_axis_comm_solution,
        "two_axis_gram_formula": two_axis_formula,
        "two_axis_gram_equals_response_transpose_response": two_axis_gram_is_ata,
        "two_axis_real_sum_of_squares_identity": two_axis_quadratic_sos,
        "two_axis_unit_determinant": two_axis_det,
        "two_axis_common_commutant_zero": common_kernel_zero,
        "two_axis_rank_three": two_axis_rank3,
        "two_axis_positive_definite_gram_certificate": positive_definite_certificate,
        "isotropic_zero_control": isotropic_zero,
        "parallel_one_dimensional_kernel_control": parallel_control,
    }
    passed = all(subchecks.values())
    result = {
        "schema": "htt.cas.axis-result.v1",
        "axis": "sympy",
        "contract_id": "GRSTAT-20260930-CAS-15-C04-STACKED-COMMUTANT-V1",
        "contract_sha256": "67422619e47fda896d7516d48e980ec693d878f3c63e5d61e0c151ffaef65ed8",
        "admitted_inputs_sha256": "1b98962616a8a43aca614c18a7e69304653c84f0d1b54846a81811642d2491d8",
        "status": "PASS" if passed else "FAIL",
        "evidence_class": "exact",
        "checks": {"CAS-15-C04": passed},
        "subchecks": subchecks,
        "exact_certificates": {
            "axisymmetric_gram": str(expected_gn),
            "one_axis_gram": str(g1),
            "two_axis_determinant_on_unit_locus": str(det_unit),
            "two_axis_determinant_factored_target": str(det_expected),
            "two_axis_common_solution_generic_nonparallel_chart": str(
                common_solution_generic
            ),
            "parallel_gram": str(g_parallel),
        },
        "domain": {
            "field": "real",
            "unit_axes": True,
            "nonisotropic": ["beta1!=0", "beta2!=0"],
            "nonparallel_canonical_chart": "s!=0 with s^2+c^2=1",
            "orthogonal_frame_reduction": True,
        },
        "domain_assumption_diff": [],
        "counterexample": None,
        "statement_alignment": {
            "stacked_gram_and_kernel": "exact via G=A^T A and real sum of squares",
            "one_axis": "exact rank 2 and kernel span(n)",
            "two_nonparallel_axes": "exact zero common skew commutant, rank 3, positive definite Gram",
            "controls": "beta=0, one axis, and parallel-axis controls exact",
            "claim_ceiling": "C04 finite commutant only; no transport or science",
        },
        "runtime": {
            "python": sys.version,
            "python_executable": sys.executable,
            "platform": platform.platform(),
            "sympy": sp.__version__,
            "sympy_file": sp.__file__,
            "launch_id": None,
            "authority_status": "UNAVAILABLE_BY_OWNER_DIRECT_LOCAL_INSTRUCTION",
            "observed_model": "UNKNOWN",
            "observed_effort": "UNKNOWN",
        },
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
