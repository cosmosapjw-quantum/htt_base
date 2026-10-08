#!/usr/bin/python3
"""Independent exact SymPy calculation for the frozen CAS-10-C01 component.

Inputs are transcribed from ADMITTED_INPUTS.json. No target expression is used
to construct either matrix or tuple; targets occur only in residual checks.
"""

import json
import sys
from pathlib import Path

import sympy as sp


H = sp.symbols("H", real=True)
q = sp.Rational
g = sp.diag(-1, 1, 1, 1)
u = sp.Matrix([q(5, 4), q(3, 4), 0, 0])
B1 = H * sp.Matrix(
    [[q(9, 16), q(-15, 16), 0, 0],
     [q(-15, 16), q(25, 16), 0, 0],
     [0, 0, 1, 0],
     [0, 0, 0, 1]]
)
B2 = H / 128 * sp.Matrix(
    [[-153, 0, -120, 0],
     [0, 425, 0, 0],
     [-120, 0, 353, 0],
     [0, 0, 0, 353]]
)

target_b2 = H / 512 * sp.Matrix([-765, 1275, -600, 0])
target_norm = q(87525, 16384) * H**2
target_powers = (
    q(25, 16), q(9, 16), q(49, 16) * H**2,
    q(225, 64) * H**2, q(27, 128) * H**2,
)


def scalar(x):
    return sp.factor(sp.simplify(x))


def vector(x):
    return [scalar(v) for v in x]


def strings(values):
    return [str(v) for v in values]


def zero(values):
    return all(v == 0 for v in values)


b1u = vector(B1 * u)
b2 = vector(B2 * u)
orthogonality = scalar((u.T * sp.Matrix(b2))[0])
norm = scalar((sp.Matrix(b2).T * g.inv() * sp.Matrix(b2))[0])
unit_residual = scalar((u.T * g * u)[0] + 1)

# Z=5/4+(3/4)n_x. The two declared component powers are calculated
# separately from its scalar and dipole coefficient, with no sky averaging.
z_monopole = q(5, 4)
z_dipole = sp.Matrix([q(3, 4), 0, 0])
m = q(7, 4) * H
T = sp.diag(q(3, 8) * H, q(-3, 16) * H, q(-3, 16) * H)


def powers(p):
    return (
        scalar(z_monopole**2),
        scalar(z_dipole.dot(z_dipole)),
        scalar(m**2),
        scalar(p.dot(p)),
        scalar(sum(T[i, j]**2 for i in range(3) for j in range(3))),
    )


p1 = sp.Matrix([q(15, 8) * H, 0, 0])
p2 = sp.Matrix([0, q(15, 8) * H, 0])
tuple1 = powers(p1)
tuple2 = powers(p2)

residuals = {
    "unit_timelike": [unit_residual],
    "B1_u": b1u,
    "B2_u_target": vector(sp.Matrix(b2) - target_b2),
    "uT_b2": [orthogonality],
    "b2_Lorentz_norm_target": [scalar(norm - target_norm)],
    "tuple1_powers_target": [scalar(a - b) for a, b in zip(tuple1, target_powers)],
    "tuple2_powers_target": [scalar(a - b) for a, b in zip(tuple2, target_powers)],
}
all_exact = all(zero(group) for group in residuals.values())
boundary_zero = all(scalar(v.subs(H, 0)) == 0 for v in b2) and scalar(norm.subs(H, 0)) == 0
control_one = scalar(norm.subs(H, 1)) == q(87525, 16384)
strict_control = sp.Rational(87525, 16384) > 0 and norm == target_norm
pass_component = all_exact and boundary_zero and control_one and strict_control

payload = {
    "checks": {
        "CAS-10-C01": {
            "status": "PASS" if pass_component else "FAIL",
            "exact": all_exact,
            "sympy_version": sp.__version__,
            "u_g_u": str(scalar((u.T * g * u)[0])),
            "B1_u": strings(b1u),
            "b2": strings(b2),
            "uT_b2": str(orthogonality),
            "b2_g_inverse_b2": str(norm),
            "tuple1_powers": strings(tuple1),
            "tuple2_powers": strings(tuple2),
            "residuals": {name: strings(group) for name, group in residuals.items()},
            "H_zero": {"b2_zero": boundary_zero, "norm_squared": str(scalar(norm.subs(H, 0))), "strict_nonzero": False},
            "H_one": {"norm_squared": str(scalar(norm.subs(H, 1))), "positive": control_one},
            "H_nonzero_strictness": "87525/16384 > 0 and H**2 > 0 for real H != 0",
        }
    },
    "domain_assumption_diff": [],
    "counterexample": None,
}

Path(__file__).with_name("result.json").write_text(
    json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
    encoding="utf-8",
)
print(json.dumps({
    "checks": {"CAS-10-C01": bool(pass_component)},
    "domain_assumption_diff": [],
    "counterexample": None,
}, sort_keys=True, separators=(",", ":")))
sys.exit(0 if pass_component else 1)
