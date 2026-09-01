from __future__ import annotations

import numpy as np
import pytest

from obsstat.boost_response import (
    BoostResponseError,
    boost_least_squares_inverse,
    boost_orthogonal_residual,
    boost_response_metric,
    contract_octupole_with_quadrupole,
    first_order_quadrupole_boost,
    project_onto_boost_image,
    quadrupole_boost_dipole,
    quadrupole_boost_octupole,
    quadrupole_temperature,
    stf3_component_metric,
)
from obsstat.lorentz_sky_pullback import (
    aberrate_sky_direction,
    deaberrate_sky_direction,
    doppler_factor_boosted,
    doppler_factor_unboosted,
    solid_angle_jacobian,
    thermodynamic_temperature_pullback,
)

pytestmark = pytest.mark.fast


def _q() -> np.ndarray:
    return np.array(
        [[0.8, -0.3, 0.2], [-0.3, -0.5, 0.4], [0.2, 0.4, -0.3]],
        dtype=float,
    )


def _unit_rows(seed: int = 9182, count: int = 256) -> np.ndarray:
    rng = np.random.default_rng(seed)
    rows = rng.normal(size=(count, 3))
    return rows / np.linalg.norm(rows, axis=1, keepdims=True)


def test_wu010_aberration_round_trip_and_doppler_pair() -> None:
    directions = _unit_rows(count=64)
    beta = np.array([0.012, -0.021, 0.015])
    boosted = aberrate_sky_direction(directions, beta)
    restored = deaberrate_sky_direction(boosted, beta)
    np.testing.assert_allclose(restored, directions, atol=3e-14, rtol=0.0)
    np.testing.assert_allclose(
        doppler_factor_boosted(boosted, beta),
        doppler_factor_unboosted(directions, beta),
        atol=3e-14,
        rtol=0.0,
    )
    np.testing.assert_allclose(
        solid_angle_jacobian(directions, beta),
        doppler_factor_unboosted(directions, beta) ** -2,
        atol=0.0,
        rtol=0.0,
    )


def test_wu010_quadrupole_response_contraction_and_inverse() -> None:
    q = _q()
    beta = np.array([0.02, -0.01, 0.03])
    octupole = quadrupole_boost_octupole(q, beta)
    np.testing.assert_allclose(
        np.einsum("iik->k", octupole),
        0.0,
        atol=3e-15,
        rtol=0.0,
    )
    np.testing.assert_allclose(
        contract_octupole_with_quadrupole(octupole, q),
        boost_response_metric(q) @ beta,
        atol=3e-15,
        rtol=0.0,
    )
    np.testing.assert_allclose(
        boost_least_squares_inverse(q, octupole),
        beta,
        atol=3e-15,
        rtol=0.0,
    )


def test_wu010_projector_and_four_dimensional_residual_contract() -> None:
    q = _q()
    signal = quadrupole_boost_octupole(q, np.array([0.04, -0.025, 0.017]))
    nuisance_q = np.array(
        [[0.0, 0.2, 0.0], [0.2, 0.0, 0.0], [0.0, 0.0, 0.0]],
        dtype=float,
    )
    nuisance = quadrupole_boost_octupole(nuisance_q, np.array([0.0, 0.0, 0.4]))
    observed = signal + nuisance
    projected = project_onto_boost_image(q, observed)
    residual = boost_orthogonal_residual(q, observed)
    np.testing.assert_allclose(projected + residual, observed, atol=3e-14, rtol=0.0)
    np.testing.assert_allclose(
        contract_octupole_with_quadrupole(residual, q),
        0.0,
        atol=3e-14,
        rtol=0.0,
    )


def test_wu010_stf3_component_metric_matches_frobenius_norm() -> None:
    octupole = quadrupole_boost_octupole(_q(), np.array([0.3, -0.2, 0.1]))
    components = np.array(
        [
            octupole[0, 0, 0],
            octupole[0, 0, 1],
            octupole[0, 0, 2],
            octupole[0, 1, 1],
            octupole[0, 1, 2],
            octupole[1, 1, 1],
            octupole[1, 1, 2],
        ]
    )
    np.testing.assert_allclose(
        components @ stf3_component_metric() @ components,
        np.einsum("abc,abc->", octupole, octupole),
        atol=3e-15,
        rtol=0.0,
    )


def test_wu010_sharp_condition_bound_saturates() -> None:
    q = np.diag([-5.0, 4.0, 1.0])
    np.testing.assert_allclose(
        np.linalg.cond(boost_response_metric(q), 2),
        5.0 / 3.0,
        atol=3e-15,
        rtol=0.0,
    )


def test_wu010_finite_pullback_matches_linear_generator() -> None:
    q = _q()
    directions = _unit_rows(count=512)
    beta_hat = np.array([0.4, -0.2, 0.3])
    beta_hat /= np.linalg.norm(beta_hat)
    errors = []
    for epsilon in (2.0e-4, 1.0e-4):
        beta = epsilon * beta_hat
        source_directions = deaberrate_sky_direction(directions, beta)
        exact = thermodynamic_temperature_pullback(
            directions,
            beta,
            quadrupole_temperature(q, source_directions),
        )
        linear = quadrupole_temperature(q, directions) + first_order_quadrupole_boost(
            q, beta, directions
        )
        errors.append(float(np.max(np.abs(exact - linear))))
    assert errors[1] < 0.27 * errors[0]


def test_wu010_line_of_sight_sign_mutation_is_killed() -> None:
    q = _q()
    directions = _unit_rows(count=256)
    beta = 1.0e-5 * np.array([0.4, -0.2, 0.3])
    source_directions = deaberrate_sky_direction(directions, beta)
    exact = thermodynamic_temperature_pullback(
        directions,
        beta,
        quadrupole_temperature(q, source_directions),
    )
    baseline = quadrupole_temperature(q, directions)
    correct = baseline + first_order_quadrupole_boost(q, beta, directions)
    wrong = baseline + first_order_quadrupole_boost(q, -beta, directions)
    assert np.linalg.norm(exact - correct) < 1.0e-4 * np.linalg.norm(exact - wrong)


def test_wu010_rejects_non_stf_or_zero_inverse_domains() -> None:
    with pytest.raises(BoostResponseError):
        quadrupole_boost_dipole(np.eye(3), np.zeros(3))
    with pytest.raises(BoostResponseError):
        boost_least_squares_inverse(np.zeros((3, 3)), np.zeros((3, 3, 3)))
