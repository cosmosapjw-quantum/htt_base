"""Independent SymPy check of the frozen CAS-10-C03 v2 finite component.

The five ordered blocks are (Z0, Z1, m, p, T), of sizes (1, 3, 1, 3, 5).
Only the fourth block changes.  This program asserts exact symbolic identities;
the high precision values are controls, not substitutes for those identities.
"""

import json

import sympy as sp


def zero_matrix(matrix):
    return all(sp.cancel(entry) == 0 for entry in matrix)


def main():
    H = sp.symbols("H", real=True)
    sigma_0, sigma_1, sigma_m, sigma_p, sigma_T = sp.symbols(
        "sigma_0 sigma_1 sigma_m sigma_p sigma_T", positive=True, real=True
    )
    scales = (sigma_0, sigma_1, sigma_m, sigma_p, sigma_T)
    dimensions = (1, 3, 1, 3, 5)
    assert sum(dimensions) == 13
    assert all(sp.ask(sp.Q.positive(scale)) for scale in scales)

    R = sp.Matrix([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
    p = sp.Matrix([15 * H / 8, 0, 0])
    p_prime = sp.Matrix([0, 15 * H / 8, 0])
    B = sp.diag(sp.eye(1), sp.eye(3), sp.eye(1), R, sp.eye(5))

    Z0 = sp.Matrix(sp.symbols("z0:1"))
    Z1 = sp.Matrix(sp.symbols("z1:4"))
    m = sp.Matrix(sp.symbols("m0:1"))
    T = sp.Matrix(sp.symbols("t0:5"))
    blocks_1 = (Z0, Z1, m, p, T)
    blocks_2 = (Z0, Z1, m, p_prime, T)
    mu_1 = sp.Matrix.vstack(*blocks_1)
    mu_2 = sp.Matrix.vstack(*blocks_2)
    Sigma = sp.diag(*(
        sp.eye(dim) * scale**2 for dim, scale in zip(dimensions, scales)
    ))

    checks = {
        "slope_rotation_orthogonal": zero_matrix(R.T * R - sp.eye(3)),
        "slope_rotation_proper": R.det() == 1,
        "slope_rotation_maps_p": zero_matrix(R * p - p_prime),
        "block_order_and_dimensions": B.shape == (13, 13) and Sigma.shape == (13, 13),
        "direct_sum_orthogonal": zero_matrix(B.T * B - sp.eye(13)),
        "direct_sum_proper": B.det() == 1,
        "direct_sum_maps_means": zero_matrix(B * mu_1 - mu_2),
        "direct_sum_preserves_covariance": zero_matrix(B * Sigma * B.T - Sigma),
        "all_five_block_norms_equal": all(
            sp.cancel((a.T * a)[0] - (b.T * b)[0]) == 0
            for a, b in zip(blocks_1, blocks_2)
        ),
        "positive_block_covariance": all(
            sp.ask(sp.Q.positive(scale**2)) for scale in scales
        ),
    }
    delta = mu_1 - mu_2
    inverse = sp.diag(*(
        sp.eye(dim) / scale**2 for dim, scale in zip(dimensions, scales)
    ))
    checks["inverse_covariance"] = zero_matrix(Sigma * inverse - sp.eye(13))
    quadratic = sp.factor((delta.T * inverse * delta)[0] / 2)
    target = 225 * H**2 / (64 * sigma_p**2)
    checks["kl_exact"] = sp.cancel(quadratic - target) == 0
    checks["control_H_zero"] = sp.cancel(quadratic.subs(H, 0)) == 0
    checks["control_H_one_sigma_p_one"] = (
        sp.cancel(quadratic.subs({H: 1, sigma_p: 1}) - sp.Rational(225, 64)) == 0
    )
    probe = {H: sp.Rational(7, 3), sigma_p: sp.Rational(5, 4)}
    numerical_residual = sp.N((quadratic - target).subs(probe), 80)
    checks["precision_80_control"] = numerical_residual == 0

    result = {
        "axis": "sympy",
        "tool": {"sympy": sp.__version__},
        "assumptions": {
            "H": "real",
            "block_scales": "positive real",
            "block_order": ["Z0", "Z1", "m", "p", "T"],
            "block_dimensions": list(dimensions),
            "sigma_p_block_index_zero_based": 3,
        },
        "checks": checks,
        "derived": {
            "p": str(p.T),
            "p_prime": str(p_prime.T),
            "quadratic_KL": str(quadratic),
            "target": str(target),
            "control_H_zero": str(quadratic.subs(H, 0)),
            "control_H_one_sigma_p_one": str(quadratic.subs({H: 1, sigma_p: 1})),
            "precision_80_residual": str(numerical_residual),
        },
        "pass": all(checks.values()),
        "scope": "finite block rotation and equal-covariance KL quadratic algebra only",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
