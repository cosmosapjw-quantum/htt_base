from __future__ import annotations

import numpy as np
import pytest

from htt.obsstat.lorentz_sky_pullback import (
    LorentzSkyPullbackError,
    aberrate_sky_direction,
    deaberrate_sky_direction,
    doppler_factor_boosted,
    doppler_factor_unboosted,
    lorentz_factor,
    solid_angle_jacobian,
    thermodynamic_temperature_pullback,
)


def _unit_rows(seed: int = 1729, count: int = 64) -> np.ndarray:
    rng = np.random.default_rng(seed)
    rows = rng.normal(size=(count, 3))
    return rows / np.linalg.norm(rows, axis=1, keepdims=True)


def test_aberration_round_trip_and_unit_norm() -> None:
    directions = _unit_rows()
    beta = np.array([0.012, -0.021, 0.015])
    boosted = aberrate_sky_direction(directions, beta)
    restored = deaberrate_sky_direction(boosted, beta)
    np.testing.assert_allclose(
        np.linalg.norm(boosted, axis=1), 1.0, atol=3e-14, rtol=0.0
    )
    np.testing.assert_allclose(restored, directions, atol=3e-14, rtol=0.0)


def test_doppler_pair_is_exact_in_both_direction_charts() -> None:
    directions = _unit_rows(count=32)
    beta = np.array([0.017, 0.009, -0.013])
    boosted = aberrate_sky_direction(directions, beta)
    np.testing.assert_allclose(
        doppler_factor_boosted(boosted, beta),
        doppler_factor_unboosted(directions, beta),
        atol=3e-14,
        rtol=0.0,
    )


def test_thermodynamic_temperature_pullback_uses_doppler_weight_one() -> None:
    boosted = _unit_rows(count=16)
    beta = np.array([0.011, -0.007, 0.004])
    source = np.linspace(2.70, 2.74, boosted.shape[0])
    pulled = thermodynamic_temperature_pullback(boosted, beta, source)
    expected = source * doppler_factor_boosted(boosted, beta)
    np.testing.assert_allclose(pulled, expected, atol=0.0, rtol=0.0)


def test_solid_angle_jacobian_is_inverse_doppler_square() -> None:
    directions = _unit_rows(count=24)
    beta = np.array([0.014, 0.005, -0.008])
    expected = doppler_factor_unboosted(directions, beta) ** -2
    np.testing.assert_allclose(
        solid_angle_jacobian(directions, beta), expected, atol=0.0, rtol=0.0
    )


def test_zero_beta_is_identity() -> None:
    directions = _unit_rows(count=8)
    beta = np.zeros(3)
    np.testing.assert_array_equal(aberrate_sky_direction(directions, beta), directions)
    np.testing.assert_array_equal(
        deaberrate_sky_direction(directions, beta), directions
    )
    assert lorentz_factor(beta) == 1.0


@pytest.mark.parametrize(
    "beta",
    [np.array([1.0, 0.0, 0.0]), np.array([np.nan, 0.0, 0.0]), np.ones(4)],
)
def test_invalid_beta_is_rejected(beta: np.ndarray) -> None:
    with pytest.raises(LorentzSkyPullbackError):
        lorentz_factor(beta)


def test_nonunit_sky_direction_is_rejected() -> None:
    with pytest.raises(LorentzSkyPullbackError):
        aberrate_sky_direction(np.array([1.0, 1.0, 0.0]), np.zeros(3))
