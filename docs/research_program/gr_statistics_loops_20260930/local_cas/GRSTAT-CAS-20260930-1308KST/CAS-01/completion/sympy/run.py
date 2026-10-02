#!/usr/bin/env python3
"""Independent SymPy checks of the four frozen CAS-01 finite components.

All matrix entries are covariant unless explicitly raised by eta.  The
polynomial reductions use u.eta.u=-1; the rational future-hyperboloid chart
used for the normalized seed covers every future unit timelike u.
"""

import json
import sys

import sympy as sp


eta = sp.diag(-1, 1, 1, 1)
u0, u1, u2, u3 = sp.symbols("u0 u1 u2 u3", real=True)
u = sp.Matrix([u0, u1, u2, u3])
shell = u0**2 - u1**2 - u2**2 - u3**2 - 1
c = sp.Symbol("c", positive=True)


def on_shell_zero(expr):
    """Exact polynomial quotient reduction by the unit mass shell."""
    numerator, denominator = sp.fraction(sp.cancel(expr))
    if denominator == 0:
        return False
    return sp.rem(sp.Poly(numerator, u0), sp.Poly(shell, u0)).is_zero


def matrix_on_shell_zero(matrix):
    return all(on_shell_zero(entry) for entry in matrix)


def symmetric_matrix(prefix):
    names = sp.symbols(" ".join(f"{prefix}{i}{j}" for i in range(4) for j in range(i, 4)), real=True)
    result = sp.zeros(4)
    k = 0
    for i in range(4):
        for j in range(i, 4):
            result[i, j] = result[j, i] = names[k]
            k += 1
    return result


S = symmetric_matrix("s")
alpha = (u.T * S * u)[0]
B = S + alpha * eta
u_flat = eta * u
H = sp.eye(4) + u * u_flat.T  # H^a_b; H*u=0 on the shell.
h = eta + u_flat * u_flat.T


def component_01():
    gauge = sp.Symbol("a", real=True)
    shifted = S + gauge * eta
    shifted_B = shifted + (u.T * shifted * u)[0] * eta
    normalization = on_shell_zero((u.T * B * u)[0])
    invariance = matrix_on_shell_zero(shifted_B - B)

    # Nine independent null directions impose nine linear equations on a
    # symmetric 4x4 form.  The kernel is exactly the metric line.
    axes = [sp.eye(3)[:, i] for i in range(3)]
    directions = axes + [-n for n in axes]
    directions += [(axes[i] + axes[j]) / sp.sqrt(2) for i in range(3) for j in range(i + 1, 3)]
    T = symmetric_matrix("t")
    unknowns = [T[i, j] for i in range(4) for j in range(i, 4)]
    evaluations = []
    for n in directions:
        K = sp.Matrix([-1, *n])
        evaluations.append(sp.expand((K.T * T * K)[0]))
    coefficient_matrix, rhs = sp.linear_eq_to_matrix(evaluations, unknowns)
    metric_vector = sp.Matrix([eta[i, j] for i in range(4) for j in range(i, 4)])
    kernel = coefficient_matrix.rank() == 9 and coefficient_matrix * metric_vector == sp.zeros(9, 1)
    # The converse uses K.eta.K=0 on the whole sphere, not merely at samples.
    n1, n2, n3 = sp.symbols("n1 n2 n3", real=True)
    K = sp.Matrix([-1, n1, n2, n3])
    converse = sp.expand((K.T * eta * K)[0] - (n1**2 + n2**2 + n3**2 - 1)) == 0
    print(f"C01 normalization={normalization} gauge={invariance} null_rank={coefficient_matrix.rank()} converse={converse}", file=sys.stderr)
    return bool(normalization and invariance and kernel and converse and rhs == sp.zeros(9, 1))


def component_02():
    b = B * u
    L = sp.zeros(4)
    ls = sp.symbols("l01 l02 l03 l12 l13 l23", real=True)
    k = 0
    for i in range(4):
        for j in range(i + 1, 4):
            L[i, j], L[j, i] = ls[k], -ls[k]
            k += 1
    W = H.T * L * H
    Q = B + b * u_flat.T - u_flat * b.T + W
    skew = matrix_on_shell_zero(W + W.T)
    spatial_skew = matrix_on_shell_zero(W * u)
    annihilation = matrix_on_shell_zero(Q * u)
    symmetric = matrix_on_shell_zero((Q + Q.T) / 2 - B)
    acceleration = matrix_on_shell_zero(c * Q.T * u - 2 * c * b)

    D = H.T * B * H
    theta = sp.trace(eta * B)
    sigma = D - theta * h / 3
    spatial = matrix_on_shell_zero(D * u) and matrix_on_shell_zero(sigma * u)
    trace = on_shell_zero(sp.trace(eta * D) - theta)
    stf = matrix_on_shell_zero(sigma - sigma.T) and on_shell_zero(sp.trace(eta * sigma))
    print(f"C02 Wskew={skew} Wspatial={spatial_skew} Qu={annihilation} sym={symmetric} A={acceleration} Dspatial={spatial} trace={trace} STF={stf}", file=sys.stderr)
    return bool(all((skew, spatial_skew, annihilation, symmetric, acceleration, spatial, trace, stf)))


def component_03():
    n1, n2, n3 = sp.symbols("n1 n2 n3", real=True)
    n = sp.Matrix([n1, n2, n3])
    K = sp.Matrix([-1, n1, n2, n3])
    Br = symmetric_matrix("br")
    Br[0, 0] = 0  # B(u,u)=0 in the observer-rest frame.
    theta = sum(Br[i, i] for i in range(1, 4))
    sigma = Br[1:4, 1:4] - theta * sp.eye(3) / 3
    A = sp.Matrix([2 * c * Br[0, i] for i in range(1, 4)])
    rest_difference = sp.expand((K.T * Br * K)[0] - theta / 3 - (n.T * sigma * n)[0] + (A.T * n)[0] / c)
    rest = sp.rem(sp.Poly(rest_difference, n3), sp.Poly(n1**2 + n2**2 + n3**2 - 1, n3)).is_zero

    h0 = sp.Symbol("h0", real=True)
    h1 = sp.symbols("h11 h12 h13", real=True)
    h2 = sp.zeros(3)
    free = sp.symbols("h211 h222 h212 h213 h223", real=True)
    h2[0, 0], h2[1, 1], h2[2, 2] = free[0], free[1], -free[0] - free[1]
    h2[0, 1] = h2[1, 0] = free[2]
    h2[0, 2] = h2[2, 0] = free[3]
    h2[1, 2] = h2[2, 1] = free[4]
    Src = sp.zeros(4)
    Src[0, 0] = h0
    for i in range(3):
        Src[0, i + 1] = Src[i + 1, 0] = -h1[i] / 2
    Src[1:4, 1:4] = h2
    general = sp.expand((K.T * Src * K)[0] - h0 - sum(h1[i] * n[i] for i in range(3)) - (n.T * h2 * n)[0]) == 0
    print(f"C03 rest_sphere={rest} general_S={general} STF_trace={sp.trace(h2)}", file=sys.stderr)
    return bool(rest and general and sp.trace(h2) == 0)


def component_04():
    # r=p/(u0+1), |r|<1, parameterizes the entire future unit hyperboloid.
    r1, r2, r3 = sp.symbols("r1 r2 r3", real=True)
    r2sum = r1**2 + r2**2 + r3**2
    ur = sp.Matrix([(1 + r2sum) / (1 - r2sum), 2*r1 / (1 - r2sum), 2*r2 / (1 - r2sum), 2*r3 / (1 - r2sum)])
    Hr = sp.eye(4) + ur * (eta * ur).T
    M = sp.Matrix(4, 4, lambda i, j: sp.Symbol(f"m{i}{j}", real=True))
    Qr = M * Hr  # Every Q with Q*u=0 equals Q*H on this shell.
    x = sp.Matrix(sp.symbols("x0 x1 x2 x3", real=True))
    v = ur + eta * Qr.T * x / c
    norm_squared = -(v.T * eta * v)[0]
    v0 = {entry: 0 for entry in x}
    norm_at_origin = sp.cancel(norm_squared.subs(v0))
    norm_ok = norm_at_origin == 1
    # Differentiate the actual normalization, retaining its positive root.
    N = sp.sqrt(norm_squared)
    unit = v / N
    value = unit.subs(v0)
    value_ok = all(sp.cancel(value[i] - ur[i]) == 0 for i in range(4))
    J = unit.jacobian(x).subs(v0)
    expected = eta * Qr.T / c  # J^b_a = g^{bd}Q_ad/c.
    derivative_ok = all(sp.cancel(J[i, a] - expected[i, a]) == 0 for i in range(4) for a in range(4))
    spatial_Q = all(sp.cancel(z) == 0 for z in Qr * ur)
    print(f"C04 chart_norm={norm_ok} value={value_ok} derivative={derivative_ok} Qu={spatial_Q}", file=sys.stderr)
    return bool(norm_ok and value_ok and derivative_ok and spatial_Q)


def main():
    checks = {}
    for cid, fn in (("CAS-01-C01", component_01), ("CAS-01-C02", component_02),
                    ("CAS-01-C03", component_03), ("CAS-01-C04", component_04)):
        checks[cid] = fn()
    print(json.dumps({"checks": checks, "domain_assumption_diff": [], "counterexample": None}, sort_keys=True))


if __name__ == "__main__":
    main()
