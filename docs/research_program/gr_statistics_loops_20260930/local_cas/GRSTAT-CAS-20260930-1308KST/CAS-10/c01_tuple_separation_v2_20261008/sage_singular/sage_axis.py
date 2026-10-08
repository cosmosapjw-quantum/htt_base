"""Exact SageMath verification of the admitted CAS-10-C01 finite component."""

import json

from sage.all import QQ, PolynomialRing, diagonal_matrix, matrix, vector


R = PolynomialRing(QQ, "H")
H = R.gen()
u = vector(R, [QQ(5) / 4, QQ(3) / 4, 0, 0])
g = diagonal_matrix(R, [-1, 1, 1, 1])
B1 = H * matrix(R, [
    [QQ(9) / 16, -QQ(15) / 16, 0, 0],
    [-QQ(15) / 16, QQ(25) / 16, 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, 1],
])
B2 = H / 128 * matrix(R, [
    [-153, 0, -120, 0],
    [0, 425, 0, 0],
    [-120, 0, 353, 0],
    [0, 0, 0, 353],
])
b1 = B1 * u
b2 = B2 * u
expected_b2 = H / 512 * vector(R, [-765, 1275, -600, 0])
lorentz_norm = b2.dot_product(g.inverse() * b2)

T = diagonal_matrix(R, [3 * H / 8, -3 * H / 16, -3 * H / 16])
m = 7 * H / 4
p1 = vector(R, [15 * H / 8, 0, 0])
p2 = vector(R, [0, 15 * H / 8, 0])
z_monopole = QQ(5) / 4
z_dipole = vector(R, [QQ(3) / 4, 0, 0])


def powers(p):
    return [
        z_monopole**2,
        z_dipole.dot_product(z_dipole),
        m**2,
        p.dot_product(p),
        sum(entry**2 for entry in T.list()),
    ]


target_powers = [QQ(25) / 16, QQ(9) / 16,
                 49 * H**2 / 16, 225 * H**2 / 64, 27 * H**2 / 128]


def at(x, h):
    return R(x)(h)


checks = {
    "u_timelike_unit": u.dot_product(g * u) == -1,
    "B1u_zero": b1 == vector(R, [0, 0, 0, 0]),
    "B2u_exact": b2 == expected_b2,
    "uT_b2_zero": u.dot_product(b2) == 0,
    "b2_lorentz_norm_exact": lorentz_norm == 87525 * H**2 / 16384,
    "tuple1_separate_powers": powers(p1) == target_powers,
    "tuple2_separate_powers": powers(p2) == target_powers,
    "H0_B1u_zero": all(x(0) == 0 for x in b1),
    "H0_b2_zero": all(x(0) == 0 for x in b2),
    "H0_norm_zero": lorentz_norm(0) == 0,
    "H0_powers": all(at(a, 0) == at(b, 0) for a, b in zip(powers(p1), target_powers))
                 and all(at(a, 0) == at(b, 0) for a, b in zip(powers(p2), target_powers)),
    "H1_b2": vector(QQ, [x(1) for x in b2]) == vector(QQ, [-QQ(765) / 512, QQ(1275) / 512, -QQ(600) / 512, 0]),
    "H1_norm_positive": lorentz_norm(1) == QQ(87525) / 16384 and lorentz_norm(1) > 0,
    "H1_powers": all(at(a, 1) == at(b, 1) for a, b in zip(powers(p1), target_powers))
                 and all(at(a, 1) == at(b, 1) for a, b in zip(powers(p2), target_powers)),
}
record = {
    "checks": {key: bool(value) for key, value in checks.items()},
    "computed": {
        "u_g_u": str(u.dot_product(g * u)),
        "B1u": [str(x) for x in b1],
        "B2u": [str(x) for x in b2],
        "uT_b2": str(u.dot_product(b2)),
        "b2_ginv_b2": str(lorentz_norm),
        "tuple1_powers": [str(x) for x in powers(p1)],
        "tuple2_powers": [str(x) for x in powers(p2)],
    },
    "strictness": "87525*H^2/16384 > 0 exactly when real H != 0; zero at H=0",
}
print(json.dumps(record, sort_keys=True, separators=(",", ":")))
if not all(checks.values()):
    raise SystemExit(1)
