from __future__ import annotations

import math

import numpy as np
import pytest

from obsstat.boost_response import (
    quadrupole_boost_dipole,
    quadrupole_boost_harmonic_matrices,
    quadrupole_boost_octupole,
    quadrupole_boost_real_harmonics,
)
from obsstat.lorentz_sky_pullback import (
    LorentzSkyPullbackError,
    deaberrate_sky_direction,
    doppler_factor_boosted,
    pullback_thermodynamic_temperature_field,
    thermodynamic_temperature_pullback,
)
from obsstat.planck_lowell_irrep_projection import (
    real_harmonic_l2_to_stf,
    stf3_to_real_harmonic,
)

pytestmark = pytest.mark.fast


def _unit_rows(seed: int = 20260902, count: int = 64) -> np.ndarray:
    rng = np.random.default_rng(seed)
    rows = rng.normal(size=(count, 3))
    return rows / np.linalg.norm(rows, axis=1, keepdims=True)


def _dipole_vector_to_real_harmonic(vector: np.ndarray) -> np.ndarray:
    """Independent Condon--Shortley l=1 Cartesian-to-stored-real adapter."""

    k0 = math.sqrt(3.0 / (4.0 * math.pi))
    k1 = math.sqrt(3.0 / (8.0 * math.pi))
    return np.asarray(
        [vector[2] / k0, -vector[0] / (2.0 * k1), vector[1] / (2.0 * k1)],
        dtype=np.float64,
    )


def test_wu010_direct_harmonic_matrices_match_exact_registered_coefficients() -> None:
    q = np.array([0.7, -0.4, 0.2, 0.9, -0.3], dtype=float)
    b1, b3 = quadrupole_boost_harmonic_matrices(q)
    a20, a21r, a21i, a22r, a22i = q
    expected_b1 = np.array(
        [
            [2.0 * math.sqrt(2.0 / 5.0) * a21r,
             -2.0 * math.sqrt(2.0 / 5.0) * a21i,
             -4.0 * a20 / math.sqrt(15.0)],
            [-math.sqrt(2.0 / 15.0) * a20 + 2.0 * a22r / math.sqrt(5.0),
             -2.0 * a22i / math.sqrt(5.0),
             -2.0 * a21r / math.sqrt(5.0)],
            [2.0 * a22i / math.sqrt(5.0),
             math.sqrt(2.0 / 15.0) * a20 + 2.0 * a22r / math.sqrt(5.0),
             -2.0 * a21i / math.sqrt(5.0)],
        ],
        dtype=float,
    )
    expected_b3 = np.array(
        [
            [3.0 * math.sqrt(6.0 / 35.0) * a21r,
             -3.0 * math.sqrt(6.0 / 35.0) * a21i,
             9.0 * a20 / math.sqrt(35.0)],
            [-3.0 * math.sqrt(3.0 / 35.0) * a20 + 3.0 * a22r / math.sqrt(70.0),
             -3.0 * a22i / math.sqrt(70.0),
             6.0 * math.sqrt(2.0 / 35.0) * a21r],
            [3.0 * a22i / math.sqrt(70.0),
             3.0 * math.sqrt(3.0 / 35.0) * a20 + 3.0 * a22r / math.sqrt(70.0),
             6.0 * math.sqrt(2.0 / 35.0) * a21i],
            [-3.0 * a21r / math.sqrt(7.0),
             -3.0 * a21i / math.sqrt(7.0),
             3.0 * a22r / math.sqrt(7.0)],
            [-3.0 * a21i / math.sqrt(7.0),
             3.0 * a21r / math.sqrt(7.0),
             3.0 * a22i / math.sqrt(7.0)],
            [-3.0 * math.sqrt(3.0 / 14.0) * a22r,
             -3.0 * math.sqrt(3.0 / 14.0) * a22i,
             0.0],
            [-3.0 * math.sqrt(3.0 / 14.0) * a22i,
             3.0 * math.sqrt(3.0 / 14.0) * a22r,
             0.0],
        ],
        dtype=float,
    )
    np.testing.assert_allclose(b1, expected_b1, atol=0.0, rtol=0.0)
    np.testing.assert_allclose(b3, expected_b3, atol=0.0, rtol=0.0)


def test_wu010_harmonic_oracle_matches_stf_route_for_every_basis_pair() -> None:
    for q_index in range(5):
        q_block = np.zeros(5)
        q_block[q_index] = 1.0
        q_tensor = real_harmonic_l2_to_stf(q_block)
        for beta_index in range(3):
            beta = np.zeros(3)
            beta[beta_index] = 1.0
            dipole, octupole = quadrupole_boost_real_harmonics(q_block, beta)
            dipole_reference = _dipole_vector_to_real_harmonic(
                quadrupole_boost_dipole(q_tensor, beta)
            )
            octupole_reference = stf3_to_real_harmonic(
                quadrupole_boost_octupole(q_tensor, beta)
            )
            np.testing.assert_allclose(
                dipole, dipole_reference, atol=3.0e-15, rtol=0.0
            )
            np.testing.assert_allclose(
                octupole, octupole_reference, atol=3.0e-15, rtol=0.0
            )


def test_wu010_direction_safe_field_pullback_evaluates_inverse_aberrated_sky() -> None:
    boosted = _unit_rows(count=32)
    beta = np.array([0.011, -0.007, 0.004])

    def absolute_temperature(direction: np.ndarray) -> np.ndarray:
        return 2.7255 + 0.01 * direction[..., 0] - 0.02 * direction[..., 2]

    pulled = pullback_thermodynamic_temperature_field(
        boosted, beta, absolute_temperature
    )
    source_direction = deaberrate_sky_direction(boosted, beta)
    expected = (
        doppler_factor_boosted(boosted, beta)
        * absolute_temperature(source_direction)
    )
    np.testing.assert_allclose(pulled, expected, atol=2.0e-15, rtol=0.0)


def test_wu010_absolute_temperature_api_rejects_zero_or_negative_values() -> None:
    boosted = _unit_rows(count=4)
    beta = np.zeros(3)
    for invalid in (0.0, -1.0, np.array([2.7, 2.7, 0.0, 2.7])):
        with pytest.raises(LorentzSkyPullbackError, match="strictly positive"):
            thermodynamic_temperature_pullback(boosted, beta, invalid)

    with pytest.raises(LorentzSkyPullbackError, match="strictly positive"):
        pullback_thermodynamic_temperature_field(
            boosted,
            beta,
            lambda direction: np.zeros(direction.shape[:-1]),
        )
