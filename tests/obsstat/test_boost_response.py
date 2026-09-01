from __future__ import annotations

import numpy as np
import pytest

from htt.obsstat.boost_response import (
    BoostResponseError,
    boost_least_squares_inverse,
    boost_orthogonal_residual,
    boost_response_matrix,
    boost_response_metric,
    contract_octupole_with_quadrupole,
    first_order_quadrupole_boost,
    project_onto_boost_image,
    quadrupole_boost_dipole,
    quadrupole_boost_octupole,
    quadrupole_temperature,
    stf3_component_metric,
)
from htt.obsstat.lorentz_sky_pullback import (
    deaberrate_sky_direction,
    thermodynamic_temperature_pullback,
)


def _q() -> np.ndarray:
    return np.array(
        [[0.8, -0.3, 0.2], [-0.3, -0.5, 0.4], [0.2, 0.4, -0.3]],
        dtype=float,
    )


def _unit_rows(seed: int = 9182, count: int = 256) -> np.ndarray:
    rng = np.random.default_rng(seed)
    rows = rng.normal(size=(count, 3))
    return rows / np.linalg.norm(rows, axis=1, keepdims=True)


def _exact_boosted_quadrupole(
    q: np.ndarray,
    beta: np.ndarray,
    boosted_direction: np.ndarray,
) -> np.ndarray:
    """Boost a positive absolute sky and subtract its boosted monopole.

    The production pullback is an absolute thermodynamic-temperature API.
    A bare STF quadrupole is signed and is therefore not a valid direct input.
    Adding a sufficiently large positive monopole and subtracting the same
    boosted monopole isolates the exact quadrupole response without weakening
    the physical domain contract.
    """

    monopole = 3.0
    source_direction = deaberrate_sky_direction(boosted_direction, beta)
    source_quadrupole = quadrupole_temperature(q, source_direction)
    total = thermodynamic_temperature_pullback(
        boosted_direction,
        beta,
        monopole + source_quadrupole,
    )
    boosted_monopole = thermodynamic_temperature_pullback(
        boosted_direction,
        beta,
        monopole,
    )
    return total - boosted_monopole


def test_octupole_response_is_fully_symmetric_and_trace_free() -> None:
    q = _q()
    beta = np.array([0.02, -0.01, 0.03])
    o = quadrupole_boost_octupole(q, beta)
    np.testing.assert_allclose(o, np.transpose(o, (1, 0, 2)), atol=2e-15, rtol=0.0)
    np.testing.assert_allclose(o, np.transpose(o, (2, 1, 0)), atol=2e-15, rtol=0.0)
    np.testing.assert_allclose(
        np.einsum("iik->k", o), 0.0, atol=2e-15, rtol=0.0
    )


def test_contraction_identity_matches_positive_response_metric() -> None:
    q = _q()
    beta = np.array([0.02, -0.01, 0.03])
    o = quadrupole_boost_octupole(q, beta)
    lhs = contract_octupole_with_quadrupole(o, q)
    rhs = boost_response_metric(q) @ beta
    np.testing.assert_allclose(lhs, rhs, atol=3e-15, rtol=0.0)


def test_response_matrix_has_rank_three_for_nonzero_q() -> None:
    response = boost_response_matrix(_q())
    assert response.shape == (7, 3)
    assert np.linalg.matrix_rank(response, tol=1e-13) == 3


def test_exact_image_inverse_recovers_beta() -> None:
    q = _q()
    beta = np.array([0.04, -0.025, 0.017])
    o = quadrupole_boost_octupole(q, beta)
    np.testing.assert_allclose(
        boost_least_squares_inverse(q, o), beta, atol=3e-15, rtol=0.0
    )


def test_projector_is_orthogonal_and_reconstructs_input() -> None:
    q = _q()
    response = quadrupole_boost_octupole(q, np.array([0.04, -0.025, 0.017]))
    nuisance = quadrupole_boost_octupole(
        np.array([[0.0, 0.2, 0.0], [0.2, 0.0, 0.0], [0.0, 0.0, 0.0]]),
        np.array([0.0, 0.0, 0.4]),
    )
    observed = response + nuisance
    projected = project_onto_boost_image(q, observed)
    residual = boost_orthogonal_residual(q, observed)
    np.testing.assert_allclose(projected + residual, observed, atol=3e-14, rtol=0.0)
    np.testing.assert_allclose(
        contract_octupole_with_quadrupole(residual, q),
        0.0,
        atol=3e-14,
        rtol=0.0,
    )


def test_sharp_condition_number_is_five_thirds() -> None:
    q = np.diag([-5.0, 4.0, 1.0])
    condition = np.linalg.cond(boost_response_metric(q), 2)
    np.testing.assert_allclose(condition, 5.0 / 3.0, atol=3e-15, rtol=0.0)


def test_first_order_response_matches_finite_pullback_quadratically() -> None:
    q = _q()
    direction = _unit_rows(count=512)
    beta_hat = np.array([0.4, -0.2, 0.3])
    beta_hat /= np.linalg.norm(beta_hat)
    errors = []
    for epsilon in (2.0e-4, 1.0e-4):
        beta = epsilon * beta_hat
        exact = _exact_boosted_quadrupole(q, beta, direction)
        baseline = quadrupole_temperature(q, direction)
        linear = baseline + first_order_quadrupole_boost(q, beta, direction)
        errors.append(float(np.max(np.abs(exact - linear))))
    assert errors[1] < 0.27 * errors[0]


def test_direction_sign_mutation_is_detected() -> None:
    q = _q()
    direction = _unit_rows(count=256)
    beta = 1.0e-5 * np.array([0.4, -0.2, 0.3])
    exact = _exact_boosted_quadrupole(q, beta, direction)
    baseline = quadrupole_temperature(q, direction)
    correct = baseline + first_order_quadrupole_boost(q, beta, direction)
    wrong = baseline + first_order_quadrupole_boost(q, -beta, direction)
    assert np.linalg.norm(exact - correct) < 1.0e-4 * np.linalg.norm(exact - wrong)


def test_stf3_component_metric_matches_full_frobenius_norm() -> None:
    o = quadrupole_boost_octupole(_q(), np.array([0.3, -0.2, 0.1]))
    components = np.array(
        [
            o[0, 0, 0],
            o[0, 0, 1],
            o[0, 0, 2],
            o[0, 1, 1],
            o[0, 1, 2],
            o[1, 1, 1],
            o[1, 1, 2],
        ]
    )
    expected = np.einsum("abc,abc->", o, o)
    np.testing.assert_allclose(
        components @ stf3_component_metric() @ components,
        expected,
        atol=3e-15,
        rtol=0.0,
    )


def test_non_stf_quadrupole_is_rejected() -> None:
    with pytest.raises(BoostResponseError):
        quadrupole_boost_dipole(np.eye(3), np.zeros(3))
