from __future__ import annotations

import math

import numpy as np

from obsstat.cf4_forward_simulator import SimMeta
from obsstat.cf4_velocity_estimators import Cf4Sample
from obsstat.cf4_affine_divergence import (
    AffineDivergenceConfig,
    COEFFICIENT_NAMES,
    PreparedBall,
    build_affine_design,
    fit_affine_divergence,
    formula_response_coefficients,
)


def _directions(count: int = 240) -> np.ndarray:
    rng = np.random.Generator(np.random.PCG64(176))
    value = rng.normal(size=(count, 3))
    return value / np.linalg.norm(value, axis=1)[:, None]


def _ball(distance: np.ndarray, coefficients: np.ndarray) -> PreparedBall:
    n = _directions(len(distance))
    design = build_affine_design(n, distance)
    response = design @ coefficients
    sample = Cf4Sample(
        n=n,
        v=response,
        w=np.ones(len(distance)),
        sig_v=np.ones(len(distance)),
        pos_hmpc=n * distance[:, None] * 0.7,
        sg=None,
    )
    meta = SimMeta(dist=distance, e_dmzp=np.full(len(distance), 0.1), h0=74.6)
    return PreparedBall(
        radius_mpc=float(np.max(distance)),
        sample=sample,
        meta=meta,
        design=design,
        covariance=np.eye(len(distance)),
        selected_row_sha256="synthetic",
    )


def test_full_affine_design_recovers_each_structural_channel() -> None:
    distance = np.linspace(10.0, 125.0, 240)
    truth = np.asarray((120.0, -80.0, 45.0, 30.0, 2.5, 1.5, -0.5, 0.2, -0.3, 0.4))
    fit = fit_affine_divergence(_ball(distance, truth), AffineDivergenceConfig())
    assert fit.diagnostics["response_gate_pass"] is True
    assert tuple(COEFFICIENT_NAMES) == (
        "Bx", "By", "Bz", "M", "theta", "Sxx_minus_Szz",
        "Syy_minus_Szz", "Sxy", "Sxz", "Syz",
    )
    np.testing.assert_allclose(fit.coefficients, truth, rtol=0.0, atol=2e-12)


def test_rigid_translation_and_antisymmetric_rotation_have_zero_trace() -> None:
    distance = np.linspace(5.0, 125.0, 240)
    translation = np.zeros(10)
    translation[:3] = (300.0, -200.0, 100.0)
    ball = _ball(distance, translation)
    fit = fit_affine_divergence(ball, AffineDivergenceConfig())
    assert abs(float(fit.coefficients[4])) < 1e-12
    omega = np.asarray((8.0, -5.0, 3.0))
    position = distance[:, None] * ball.sample.n
    radial = np.einsum(
        "ij,ij->i",
        ball.sample.n,
        np.cross(np.broadcast_to(omega, position.shape), position),
    )
    assert np.max(np.abs(radial)) < 1e-12


def test_diagonal_shear_columns_match_literal_stf_component_differences() -> None:
    distance = np.linspace(5.0, 125.0, 240)
    n = _directions(len(distance))
    d1, d2 = 3.0, 0.0
    shear = np.diag(((2.0 * d1 - d2) / 3.0,
                     (-d1 + 2.0 * d2) / 3.0,
                     -(d1 + d2) / 3.0))
    assert math.isclose(shear[0, 0] - shear[2, 2], d1)
    assert math.isclose(shear[1, 1] - shear[2, 2], d2)
    direct = distance * np.einsum("ni,ij,nj->n", n, shear, n)
    design = build_affine_design(n, distance)
    projected = design[:, 5:7] @ np.asarray((d1, d2))
    np.testing.assert_allclose(projected, direct, rtol=0.0, atol=2e-13)


def test_constant_distance_makes_monopole_and_trace_nonidentifiable() -> None:
    truth = np.zeros(10)
    ball = _ball(np.full(240, 100.0), truth)
    fit = fit_affine_divergence(ball, AffineDivergenceConfig())
    assert fit.diagnostics["response_gate_pass"] is False
    assert fit.coefficients is None
    assert fit.coefficient_covariance is None


def test_exact_h0_trace_alias_is_minus_three_delta_h() -> None:
    distance = np.linspace(5.0, 125.0, 240)
    truth = np.asarray((100.0, 20.0, -60.0, 35.0, 4.0, 1.0, -0.5, 0.2, 0.3, -0.1))
    base = _ball(distance, truth)
    base_fit = fit_affine_divergence(base, AffineDivergenceConfig())
    delta_h = 1.25
    shifted_sample = Cf4Sample(
        n=base.sample.n,
        v=base.sample.v - delta_h * distance,
        w=base.sample.w,
        sig_v=base.sample.sig_v,
        pos_hmpc=base.sample.pos_hmpc,
        sg=None,
    )
    shifted = PreparedBall(
        radius_mpc=base.radius_mpc,
        sample=shifted_sample,
        meta=base.meta,
        design=base.design,
        covariance=base.covariance,
        selected_row_sha256="synthetic-shifted",
    )
    shifted_fit = fit_affine_divergence(shifted, AffineDivergenceConfig())
    difference = shifted_fit.coefficients - base_fit.coefficients
    expected = np.zeros(10)
    expected[4] = -3.0 * delta_h
    np.testing.assert_allclose(difference, expected, rtol=0.0, atol=3e-12)


def test_source_formula_coefficients_keep_two_bridges_distinct() -> None:
    response = formula_response_coefficients(
        h0_km_s_mpc=74.6,
        c_km_s=299792.458,
        lambda_mpc=200.0,
    )
    assert response["R_lh_qs1_delta_q_per_theta"] > 0.0
    assert response["R_lh_qs2_delta_q_per_theta"] > 0.0
    assert response["R_lh_qs1_delta_q_per_theta"] != response["R_lh_qs2_delta_q_per_theta"]
    assert response["units"] == "Mpc_s_per_km"
