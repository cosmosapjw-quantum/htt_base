#!/usr/bin/env /usr/bin/python3
"""Independent finite SymPy checks for CAS-04; stdout is one JSON object."""

import json
import sys

import sympy as sp


def zero(value):
    return sp.cancel(sp.together(sp.expand(value))) == 0


def all_zero(items):
    return all(zero(item) for item in items)


def main():
    c = sp.symbols("c", positive=True)
    eps, p1, p2, p3 = sp.symbols("epsilon p1 p2 p3", real=True)
    pressures = (p1, p2, p3)
    gaps = tuple(eps + p for p in pressures)
    d = sp.Matrix(4, 3, lambda a, i: sp.Symbol(f"D{a}{i+1}", real=True))

    # At a rest point, T^a_b=diag(-epsilon,p1,p2,p3), u^a=(1,0,0,0).
    # The differentiated eigen-equation is checked before applying the
    # spectral inverse: h[(nabla T)u+(T+epsilon I)nabla u]=0.
    t = sp.diag(-eps, *pressures)
    h = sp.diag(0, 1, 1, 1)
    # Solve the projected differentiated equation for independent unknown
    # spatial derivatives.  Nonzero gaps give a unique spectral solution.
    v = sp.Matrix(4, 3, lambda a, i: sp.Symbol(f"v{a}{i+1}", real=True))
    equations = []
    for a in range(4):
        projected = h * (sp.Matrix([0, *(d[a, i] for i in range(3))])
                         + (t + eps * sp.eye(4))
                         * sp.Matrix([0, *(v[a, i] for i in range(3))]))
        equations.extend(projected[1:4, :])
    solved = sp.solve(equations, list(v), dict=True)
    c01 = len(solved) == 1 and len(solved[0]) == 12
    q = sp.Matrix(4, 3, lambda a, i: c * solved[0][v[a, i]])
    c01 = c01 and all_zero(q[a, i] + c * d[a, i] / gaps[i]
                             for a in range(4) for i in range(3))

    m = q[1:4, :]
    theta = sp.trace(m)
    sigma = (m + m.T) / 2 - theta * sp.eye(3) / 3
    w = (m - m.T) / 2
    omega = sp.Matrix([w[1, 2], w[2, 0], w[0, 1]])
    a_vec = sp.Matrix([c * q[0, i] for i in range(3)])
    frob = lambda mat: sum(entry**2 for entry in mat)
    lhs = theta**2 / 3 + frob(sigma) + 2 * frob(omega) + frob(a_vec) / c**2
    rhs = c**2 * sum(d[a, i]**2 / gaps[i]**2
                     for a in range(4) for i in range(3))
    c02 = all_zero([lhs - frob(q), frob(w) - 2 * frob(omega),
                    frob(q) - rhs,
                    *(m - (theta * sp.eye(3) / 3 + sigma + w))])
    # Test the sign/orientation W x = -omega cross x, not merely its norm.
    y = sp.Matrix(sp.symbols("y1 y2 y3", real=True))
    c02 = c02 and all_zero(w * y + omega.cross(y))

    delta = sp.symbols("delta", positive=True)
    norm_d = frob(d)
    bound = c**2 * norm_d / delta**2
    sos = c**2 * sum(d[a, i]**2 * (gaps[i]**2 - delta**2)
                       / (delta**2 * gaps[i]**2)
                       for a in range(4) for i in range(3))
    c03 = zero(bound - rhs - sos)
    # Independent exact signed-gap probe and strict/equality support probes.
    signed = {eps: sp.Integer(1), p1: sp.Integer(-3), p2: sp.Integer(2),
              p3: sp.Integer(-5), delta: sp.Integer(2), c: sp.Integer(3)}
    # Gaps (-2,3,-4), so the first eigenspace alone is minimal.
    minimal = {d[a, i]: (sp.Integer(a + 1) if i == 0 else sp.Integer(0))
               for a in range(4) for i in range(3)}
    off_support = {**minimal, d[0, 1]: sp.Integer(1)}
    c03 = c03 and zero(sos.subs({**signed, **minimal}))
    c03 = c03 and (sp.simplify(sos.subs({**signed, **off_support})) > 0) == sp.true
    c03 = c03 and all(gaps[i].subs(signed)**2 >= signed[delta]**2 for i in range(3))

    # Direct product-rule divergence of T^{ab}=(epsilon+p)u^a u^b+p g^{ab}.
    p = sp.symbols("p", real=True)
    grad_e = sp.symbols("e0:4", real=True)
    grad_p = sp.symbols("r0:4", real=True)
    jet_u = sp.Matrix(4, 4, lambda a, b: 0 if b == 0 else
                      sp.Symbol(f"v{a}{b}", real=True))
    u = sp.Matrix([1, 0, 0, 0])
    metric_inv = sp.diag(-1, 1, 1, 1)
    enthalpy = eps + p
    divergence = sp.Matrix(4, 1, lambda b, _:
        sum((grad_e[a] + grad_p[a]) * u[a] * u[b]
            + enthalpy * (jet_u[a, a] * u[b] + u[a] * jet_u[a, b])
            + grad_p[a] * metric_inv[a, b] for a in range(4)))
    spatial = h * divergence
    euler = sp.Matrix([enthalpy * jet_u[0, i] + grad_p[i]
                       for i in range(1, 4)])
    solution = [sp.solve(sp.Eq(euler[i], 0), jet_u[0, i + 1])[0]
                for i in range(3)]
    acceleration = sp.Matrix([c**2 * solution[i] for i in range(3)])
    cs2 = sp.symbols("cs2", real=True)
    eos = {grad_p[i]: cs2 * grad_e[i] / c**2 for i in range(1, 4)}
    c04 = all_zero(spatial[1:4, :] - euler)
    c04 = c04 and all_zero(acceleration[i] + c**2 * grad_p[i + 1] / enthalpy
                           for i in range(3))
    c04 = c04 and all_zero(acceleration[i].subs(eos)
                            + cs2 * grad_e[i + 1] / enthalpy
                            for i in range(3))
    c04 = c04 and all_zero(acceleration[i].subs({p: 0, grad_p[i + 1]: 0})
                            for i in range(3))

    result = {
        "checks": {"CAS-04-C01": bool(c01), "CAS-04-C02": bool(c02),
                   "CAS-04-C03": bool(c03), "CAS-04-C04": bool(c04)},
        "domain_assumption_diff": [],
        "counterexample": None,
        "engine": {"python": sys.version, "sympy": sp.__version__,
                   "sympy_origin": sp.__file__},
        "certificates": {
            "c02_residual": str(sp.cancel(sp.together(lhs-rhs))),
            "c03_sos_residual": str(sp.cancel(sp.together(bound-rhs-sos))),
            "c03_signed_equality": str(sos.subs({**signed, **minimal})),
            "c03_signed_strict": str(sos.subs({**signed, **off_support})),
            "c04_spatial_divergence": [str(v) for v in spatial[1:4, :]],
        },
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if all(result["checks"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
