"""Independent SymPy certificate for the admitted CAS-03-C01 component.

The quantified steps in proof.md explain why these symbolic identities certify
arbitrary real symmetric S and every allowed spatial-kernel dimension. This
program checks polynomial identities and branch/control certificates exactly.
"""

import json
import platform
import sys

import sympy as sp


def zero_matrix(matrix):
    return all(sp.simplify(entry) == 0 for entry in matrix)


def main():
    g = sp.diag(-1, 1, 1, 1)
    s = sp.symbols("s00 s01 s02 s03 s11 s12 s13 s22 s23 s33", real=True)
    S = sp.Matrix([[s[0], s[1], s[2], s[3]],
                   [s[1], s[4], s[5], s[6]],
                   [s[2], s[5], s[7], s[8]],
                   [s[3], s[6], s[8], s[9]]])
    x, y, z = sp.symbols("x y z", real=True)
    t = sp.sqrt(1 + x*x + y*y + z*z)
    u = sp.Matrix([t, x, y, z])
    st = -(u.T*S*u)[0]
    B = S - st*g
    c = sp.symbols("c", real=True)
    shell = sp.simplify((u.T*g*u)[0]) == -1
    eigen_equivalence = zero_matrix(g.inv()*B*u - (g.inv()*S*u-st*u))
    # If (S-cg)u=0, left contraction vanishes. On the shell it is -st+c.
    coefficient_identity = sp.simplify((u.T*(S-c*g)*u)[0] - (c-st)) == 0

    e0 = sp.Matrix([1, 0, 0, 0])
    st0 = -(e0.T*S*e0)[0]
    B0 = S-st0*g
    rest_column = zero_matrix(B0*e0 - sp.Matrix([0, s[1], s[2], s[3]]))
    rest_row = zero_matrix(e0.T*B0 - sp.Matrix([[0, s[1], s[2], s[3]]]))
    rest_equivalence = (sp.simplify(B0[0, 0]) == 0 and rest_column and rest_row)

    a, b, d, e, f = sp.symbols("a b d e f", real=True)
    D = sp.Matrix([[a, b, d], [b, e, f], [d, f, -a-e]])
    Brest = sp.diag(0, 1, 1, 1)
    Brest[1:4, 1:4] = D
    w = sp.Matrix([x, y, z])
    phi = sp.Matrix([t, x, y, z])
    spatial_projection = sp.Matrix([phi[1], phi[2], phi[3]])
    chart_kernel = zero_matrix(Brest*phi-sp.Matrix([0, *(D*w)]))
    chart_shell = sp.simplify((phi.T*g*phi)[0]) == -1
    chart_inverse = zero_matrix(spatial_projection-w)
    chart_trace = sp.simplify(sp.trace(D)) == 0

    q, v1, v2, v3 = sp.symbols("q v1 v2 v3", real=True)
    v = sp.Matrix([q, v1, v2, v3])
    vw = sp.Matrix([v1, v2, v3])
    converse_kernel = zero_matrix(Brest*v-sp.Matrix([0, *(D*vw)]))
    # q^2=1+||vw||^2 follows from shell. Since q>0 and RHS>0,
    # uniqueness of the positive real square root gives q=sqrt(...).
    converse_shell = sp.simplify((v.T*g*v)[0] -
                                (-q*q+vw.dot(vw))) == 0
    q_squared_identity = sp.simplify((v.T*g*v)[0] + 1 -
                                     (1+vw.dot(vw)-q*q)) == 0

    controls = {}
    for name, diag, expected_rank, expected_kernel_dim in [
        ("zero_full_sheet", (0, 0, 0), 0, 3),
        ("one_kernel_direction", (0, 1, -1), 2, 1),
        ("singleton_rest", (1, 1, -2), 3, 0),
    ]:
        dc = sp.diag(*diag)
        controls[name] = {
            "trace_zero": sp.trace(dc) == 0,
            "rank": dc.rank(),
            "kernel_dimension": len(dc.nullspace()),
            "expected": dc.rank() == expected_rank and
                        len(dc.nullspace()) == expected_kernel_dim,
        }

    # A is Lorentz-self-adjoint because S=gA is symmetric. Its only real
    # eigenvalue is 0, whose kernel has temporal component zero.
    A = sp.Matrix([[0, 1, 0, 0], [-1, 0, 0, 0],
                   [0, 0, 0, 0], [0, 0, 0, 0]])
    Sexample = g*A
    counterexample = (Sexample == Sexample.T and
                      A.charpoly().all_coeffs() == [1, 0, 1, 0, 0] and
                      all(vec[0] == 0 for vec in A.nullspace()))

    checks = {
        "mass_shell": shell,
        "eigen_equation_equivalence": eigen_equivalence,
        "metric_coefficient_unique_on_shell": coefficient_identity,
        "rest_zero_time_row_column_from_Be0": rest_equivalence,
        "zero_expansion_spatial_trace": chart_trace,
        "chart_kernel_exact_identity": chart_kernel,
        "chart_future_mass_shell": chart_shell,
        "chart_spatial_inverse_and_injectivity": chart_inverse,
        "converse_kernel_identity": converse_kernel,
        "converse_shell_positive_root_identity": converse_shell and q_squared_identity,
        "zero_full_singleton_controls": all(item["expected"] and
                                            item["trace_zero"] for item in controls.values()),
        "no_universal_timelike_eigenline_counterexample": counterexample,
    }
    # Exact symbolic identities over the real domain, interpreted using
    # the branch and elementary linear-algebra arguments in proof.md.
    passed = all(value is True or value == sp.true for value in checks.values())
    print(json.dumps({
        "component": "CAS-03-C01",
        "checks": {key: bool(value) for key, value in checks.items()},
        "controls": controls,
        "sympy_version": sp.__version__,
        "python_version": platform.python_version(),
        "domain_assumption_diff": [],
        "counterexample": None if passed else "see failed exact check",
        "final_checks": {"CAS-03-C01": bool(passed)},
    }, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
