"""Exact reference identities for root's one R65 verification pass.

Written by the bounded theory lane; not executed there. No catalogue, fit,
random draw, network, filesystem mutation or floating-point tolerance is used.
This verifies algebra, not the actual observational model.
"""
import json
import sympy as s


def zero(expr):
    if isinstance(expr, s.MatrixBase):
        return all(s.simplify(e) == 0 for e in expr)
    return s.simplify(expr) == 0


def main():
    checks = {}
    N, Z = s.symbols("N Z", positive=True)
    T, u = s.symbols("T u", real=True)
    eta = s.log(N / Z)
    profile = N * eta + u * T - s.exp(eta) * Z
    conditional = u * T - N * s.log(Z)
    checks["profile_conditional_constant"] = zero(
        profile - conditional - (N * s.log(N) - N)
    )

    # Three rational probability points on one declination circle.
    points = [s.Matrix([1, 0]), s.Matrix([0, 1]), s.Matrix([-1, 0])]
    probs = [s.Rational(1, 6), s.Rational(1, 3), s.Rational(1, 2)]
    mu = sum((p * t for p, t in zip(probs, points)), s.zeros(2, 1))
    second = sum((p * t * t.T for p, t in zip(probs, points)), s.zeros(2, 2))
    cov = second - mu * mu.T
    expected_full = (N * second).row_join(N * mu).col_join(
        (N * mu.T).row_join(s.Matrix([[N]]))
    )
    schur = expected_full[:2, :2] - (
        expected_full[:2, 2:] * expected_full[2:, 2:].inv()
        * expected_full[2:, :2]
    )
    checks["profile_fisher_covariance"] = zero(schur - N * cov)
    checks["positive_rank_example"] = cov.det() > 0 and cov[0, 0] > 0

    dx, dz, z = s.symbols("dx dz z", real=True)
    wx = dx / (1 + dz * z)
    checks["linear_dz_derivative"] = zero(
        s.diff(wx, dz) + z * dx / (1 + dz * z) ** 2
    )
    checks["linear_origin_dz_null"] = zero(s.diff(wx, dz).subs(dx, 0))

    # Correlated three-bin scalar experiment; Kronecker I2 gives the vector case.
    C = s.Matrix([[3, 1, 0], [1, 4, 1], [0, 1, 2]])
    H = s.ones(3, 1)
    R = s.Matrix([[-1, 1, 0], [-1, 0, 1]])
    precision_resid = C.inv() - C.inv() * H * (
        H.T * C.inv() * H
    ).inv() * H.T * C.inv()
    contrast_precision = R.T * (R * C * R.T).inv() * R
    checks["gls_contrast_precision"] = zero(precision_resid - contrast_precision)

    path = s.Matrix([[1, 0, 0], [-1, 1, 0], [-1, 0, 1]])
    checks["path_determinant"] = path.det() == 1
    checks["path_precision_pullback"] = zero(
        path.T * (path * C * path.T).inv() * path - C.inv()
    )
    checks["common_lss_cancellation"] = zero(R * H * H.T * R.T)

    k1, k2 = s.symbols("k1 k2", real=True)
    checks["shared_beta_residual_rank_condition"] = zero(
        s.Matrix([[k1, 1], [k2, 1]]).det() - (k1 - k2)
    )

    # A finite flux bin of a power-law source count has the same EB slope.
    low, high, exponent, amp = s.symbols("low high exponent amp", positive=True)
    nbin = amp * (low ** (-exponent) - high ** (-exponent)) / exponent
    boundary = amp * (low ** (-exponent) - high ** (-exponent))
    checks["finite_bin_powerlaw_response"] = zero(boundary / nbin - exponent)

    out = {name: bool(value) for name, value in checks.items()}
    print(json.dumps({"kind": "symbolic_reference", "checks": out,
                      "all_pass": all(out.values())}, indent=2, sort_keys=True))
    assert all(out.values()), out


if __name__ == "__main__":
    main()
