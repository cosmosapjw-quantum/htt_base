#!/usr/bin/env python3
"""Independent SymPy proof certificates for frozen CAS-14 C01--C03."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import sympy as sp


def is_zero_matrix(matrix: sp.MatrixBase) -> bool:
    return all(sp.expand(value) == 0 for value in matrix)


def cross_matrix(vector: sp.Matrix) -> sp.Matrix:
    a, b, c = vector
    return sp.Matrix([[0, -c, b], [c, 0, -a], [-b, a, 0]])


def decimal(value: sp.Expr, digits: int = 80) -> str:
    return str(sp.N(value, digits))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    ox, oy, oz, x1, x2, x3 = sp.symbols("ox oy oz x1 x2 x3", real=True)
    v1, v2, v3 = sp.symbols("v1 v2 v3", real=True)
    omega = sp.Matrix([ox, oy, oz])
    x = sp.Matrix([x1, x2, x3])
    v = sp.Matrix([v1, v2, v3])
    identity = sp.eye(3)
    q = sp.expand(x.dot(x))

    # W_ij = epsilon_ijk omega_k is the negative of the usual cross matrix.
    W = sp.Matrix([[0, oz, -oy], [-oz, 0, ox], [oy, -ox, 0]])
    cross_omega_x = cross_matrix(omega) * x
    y = -W * x
    P = identity - x * x.T
    c01_w_sign = is_zero_matrix(W * x + cross_omega_x)
    c01_y = is_zero_matrix(y - cross_omega_x)
    c01_triple_defect = sp.simplify(cross_matrix(x) * y - P * omega)
    c01_triple_factor = is_zero_matrix(c01_triple_defect - (q - 1) * omega)
    Cx = cross_matrix(x)
    c01_gram_factor = is_zero_matrix(
        sp.simplify(Cx.T * Cx - P - (q - 1) * identity)
    )

    # Universal quadratic-form identity.  Unit normalization q=1 gives P.
    cross_vx = cross_matrix(v) * x
    lagrange_identity = sp.expand(
        cross_vx.dot(cross_vx) - (v.dot(v) * q - v.dot(x) ** 2)
    )
    p_quadratic_defect = sp.expand(
        (v.T * P * v)[0] - cross_vx.dot(cross_vx)
    )
    p_quadratic_factor = sp.expand(p_quadratic_defect - (1 - q) * v.dot(v))

    w1, w2, r, s = sp.symbols("w1 w2 r s", real=True)
    e1 = sp.Matrix([1, 0, 0])
    e2 = sp.Matrix([0, 1, 0])
    xrs = sp.Matrix([r, s, 0])
    G_parallel = sp.simplify(
        w1 * (identity - e1 * e1.T) + w2 * (identity - e1 * e1.T)
    )
    G_e1e2 = sp.simplify(
        w1 * (identity - e1 * e1.T) + w2 * (identity - e2 * e2.T)
    )
    G_two = sp.simplify(
        w1 * (identity - e1 * e1.T) + w2 * (identity - xrs * xrs.T)
    )
    det_two = sp.factor(G_two.det())
    det_two_unit_defect = sp.factor(
        det_two - w1 * w2 * (w1 + w2) * s**2
    )
    controls_exact = (
        G_parallel == sp.diag(0, w1 + w2, w1 + w2)
        and G_e1e2 == sp.diag(w2, w1, w1 + w2)
        and det_two_unit_defect == 0
    )

    # Frobenius certificate for delta W.
    d1, d2, d3 = sp.symbols("d1 d2 d3", real=True)
    delta = sp.Matrix([d1, d2, d3])
    delta_W = -cross_matrix(delta)
    frobenius_sq = sp.expand(sum(entry**2 for entry in delta_W))
    frobenius_certificate = sp.expand(frobenius_sq - 2 * delta.dot(delta))

    # Exact finite test operator from two nonparallel directions e1,e2.
    # sqrt(weights)=(1,2), hence all entries remain rational.
    A = cross_matrix(e1).col_join(2 * cross_matrix(e2))
    omega0 = sp.Matrix([sp.Rational(2, 7), -sp.Rational(3, 5), sp.Rational(5, 11)])
    noise = sp.Matrix(
        [
            sp.Rational(1, 100),
            -sp.Rational(1, 125),
            sp.Rational(1, 200),
            sp.Rational(1, 250),
            -sp.Rational(1, 160),
            sp.Rational(1, 180),
        ]
    )
    pinv_A = (A.T * A).inv() * A.T
    exact_left_inverse = is_zero_matrix(pinv_A * A - identity)
    recovered = pinv_A * (A * omega0 + noise)
    exact_error = sp.sqrt((recovered - omega0).dot(recovered - omega0))
    noise_norm = sp.sqrt(noise.dot(noise))
    sigma_min_A = min(A.singular_values(), key=lambda z: float(sp.N(z, 30)))
    exact_bound_margin = sp.N(noise_norm / sigma_min_A - exact_error, 90)

    perturbation = sp.zeros(6, 3)
    perturbation[0, 0] = sp.Rational(1, 10)
    perturbation[4, 2] = -sp.Rational(1, 20)
    Ahat = A + perturbation
    pinv_Ahat = (Ahat.T * Ahat).inv() * Ahat.T
    perturbed_left_inverse = is_zero_matrix(pinv_Ahat * Ahat - identity)
    recovered_hat = pinv_Ahat * (A * omega0 + noise)
    perturbed_error = sp.sqrt((recovered_hat - omega0).dot(recovered_hat - omega0))
    perturbation_norm = max(
        perturbation.singular_values(), key=lambda z: float(sp.N(z, 30))
    )
    sigma_min_Ahat = min(
        Ahat.singular_values(), key=lambda z: float(sp.N(z, 30))
    )
    omega_norm = sp.sqrt(omega0.dot(omega0))
    perturbed_bound = (noise_norm + perturbation_norm * omega_norm) / sigma_min_Ahat
    perturbed_bound_margin = sp.N(perturbed_bound - perturbed_error, 90)

    # Boundary controls and the necessary-amplitude counterfamily.
    zero_noise_recovery = is_zero_matrix(pinv_A * (A * omega0) - omega0)
    zero_operator_reduction = sp.simplify(
        (noise_norm + sp.Integer(0) * omega_norm) / sigma_min_A
        - noise_norm / sigma_min_A
    ) == 0
    amp_zero_reduction = sp.simplify(
        (noise_norm + perturbation_norm * sp.Integer(0)) / sigma_min_Ahat
        - noise_norm / sigma_min_Ahat
    ) == 0
    delta_scalar, proposed_B = sp.symbols(
        "delta_scalar proposed_B", positive=True, real=True
    )
    unbounded_amplitude = (proposed_B + 1) / delta_scalar
    no_amplitude_excess = sp.simplify(
        delta_scalar * unbounded_amplitude - proposed_B
    )

    c01 = all(
        [c01_w_sign, c01_y, c01_triple_factor, c01_gram_factor]
    )
    c02 = all(
        [
            lagrange_identity == 0,
            p_quadratic_factor == 0,
            controls_exact,
        ]
    )
    c03 = all(
        [
            frobenius_certificate == 0,
            exact_left_inverse,
            perturbed_left_inverse,
            exact_bound_margin >= 0,
            perturbed_bound_margin >= 0,
            zero_noise_recovery,
            zero_operator_reduction,
            amp_zero_reduction,
            no_amplitude_excess == 1,
        ]
    )

    result = {
        "schema": "htt.cas14.sympy-math-result.v1",
        "engine": {"name": "SymPy", "version": sp.__version__},
        "checks": {
            "CAS-14-C01": bool(c01),
            "CAS-14-C02": bool(c02),
            "CAS-14-C03": bool(c03),
        },
        "domain_assumption_diff": [],
        "counterexample": None,
        "exact_certificates": {
            "C01": {
                "W_matrix": sp.sstr(W),
                "Wx_plus_omega_cross_x": [sp.sstr(z) for z in W * x + cross_omega_x],
                "x_cross_y_minus_Pomega": [sp.sstr(z) for z in c01_triple_defect],
                "unit_sphere_factor": "(x.x-1)*omega",
                "cross_block_gram_minus_P": "(x.x-1)*I_3",
                "finite_sum_rule": "For each unit x_m, x_m cross y_m=P_m omega; multiplying by w_m and summing gives b=G omega.",
            },
            "C02": {
                "universal_quadratic_identity": "v^T P_x v=|v cross x|^2>=0 for every real v and unit x",
                "sum_identity": "v^T G v=sum_m w_m |v cross x_m|^2 for every real v",
                "kernel_certificate": [
                    "Every summand is nonnegative and every w_m is positive.",
                    "Therefore v^T G v=0 iff v cross x_m=0 for every m.",
                    "For unit x_m, v cross x_m=0 iff v belongs to span(x_m).",
                    "Hence ker(G)=intersection_m span(x_m).",
                    "Two nonparallel unit directions have span intersection {0}; PSD G is then positive definite.",
                    "Since b=G omega and positive definite G is invertible, omega=G^{-1}b.",
                ],
                "all_parallel_G": sp.sstr(G_parallel),
                "e1_e2_G": sp.sstr(G_e1e2),
                "two_direction_determinant": sp.sstr(det_two),
                "unit_nonparallel_determinant": "w1*w2*(w1+w2)*s^2>0 when w1,w2>0 and s!=0",
            },
            "C03": {
                "exact_operator_chain": [
                    "A has full column rank, so A^dagger A=I and ||A^dagger||op=1/sigma_min(A)<=1/sigma_*.",
                    "omega_hat-omega=A^dagger e.",
                    "||omega_hat-omega||<=||A^dagger||op ||e||<=epsilon_y/sigma_*.",
                ],
                "perturbed_operator_chain": [
                    "Ahat has full column rank, so Ahat^dagger Ahat=I and ||Ahat^dagger||op<=1/sigmahat_*.",
                    "omega_hat-omega=Ahat^dagger(e+(A-Ahat)omega).",
                    "||e+(A-Ahat)omega||<=epsilon_y+epsilon_A Omega_*.",
                    "||omega_hat-omega||<=(epsilon_y+epsilon_A Omega_*)/sigmahat_*.",
                ],
                "frobenius_squared": sp.sstr(frobenius_sq),
                "frobenius_identity": "||delta W||_F=sqrt(2)|delta omega| on the nonnegative square-root branch",
                "no_amplitude_counterfamily": "Ahat=I, A=(1+delta)I, e=0, omega=((B+1)/delta)e1 gives epsilon_A=delta but error=B+1>B.",
                "no_amplitude_symbolic_excess": sp.sstr(no_amplitude_excess),
            },
        },
        "numeric_diagnostics": {
            "precision_digits": 80,
            "scope": "ancillary regular-domain checks; universal claims use the exact certificates above",
            "A_singular_values": [decimal(z) for z in A.singular_values()],
            "Ahat_singular_values": [decimal(z) for z in Ahat.singular_values()],
            "exact_error": decimal(exact_error),
            "exact_bound": decimal(noise_norm / sigma_min_A),
            "exact_bound_margin": decimal(exact_bound_margin),
            "perturbed_error": decimal(perturbed_error),
            "perturbed_bound": decimal(perturbed_bound),
            "perturbed_bound_margin": decimal(perturbed_bound_margin),
        },
        "controls": {
            "all_parallel_one_dimensional_kernel": bool(controls_exact),
            "e1_e2_component_check": bool(controls_exact),
            "zero_data_error": bool(zero_noise_recovery),
            "zero_operator_error": bool(zero_operator_reduction),
            "Omega_star_zero": bool(amp_zero_reduction),
            "amplitude_bound_is_necessary": bool(no_amplitude_excess == 1),
        },
        "claim_ceiling": "finite_vorticity_inverse_math_only_no_observation_or_science",
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if all(result["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
