from __future__ import annotations

import math

import numpy as np
import pytest
from scipy.special import sph_harm_y

from obsstat.boost_response import (
    first_order_quadrupole_boost,
    quadrupole_boost_dipole,
    quadrupole_boost_octupole,
    quadrupole_temperature,
)
from obsstat.lorentz_sky_pullback import (
    deaberrate_sky_direction,
    thermodynamic_temperature_pullback,
)
from obsstat.planck_lowell_irrep_projection import stf3_to_real_harmonic

pytestmark = pytest.mark.fast


def _quadrupole() -> np.ndarray:
    return np.array(
        [[0.8, -0.3, 0.2], [-0.3, -0.5, 0.4], [0.2, 0.4, -0.3]],
        dtype=float,
    )


def _sphere_rule() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    z, z_weights = np.polynomial.legendre.leggauss(32)
    phi = 2.0 * np.pi * np.arange(64) / 64
    zz = np.repeat(z, phi.size)
    pp = np.tile(phi, z.size)
    sin_theta = np.sqrt(np.maximum(0.0, 1.0 - zz * zz))
    directions = np.column_stack(
        (sin_theta * np.cos(pp), sin_theta * np.sin(pp), zz)
    )
    weights = np.repeat(z_weights, phi.size) * (2.0 * np.pi / phi.size)
    return directions, weights, np.arccos(zz), pp


def _stored_real_coefficients(
    field: np.ndarray,
    *,
    ell: int,
    weights: np.ndarray,
    theta: np.ndarray,
    phi: np.ndarray,
) -> np.ndarray:
    coefficients: list[float] = []
    for m in range(ell + 1):
        harmonic = sph_harm_y(ell, m, theta, phi)
        value = np.sum(weights * field * np.conjugate(harmonic))
        if m == 0:
            coefficients.append(float(value.real))
        else:
            coefficients.extend((float(value.real), float(value.imag)))
    return np.asarray(coefficients)


def _multipole_power(
    field: np.ndarray,
    *,
    ell: int,
    weights: np.ndarray,
    theta: np.ndarray,
    phi: np.ndarray,
) -> float:
    return float(
        sum(
            abs(
                np.sum(
                    weights
                    * field
                    * np.conjugate(sph_harm_y(ell, m, theta, phi))
                )
            )
            ** 2
            for m in range(-ell, ell + 1)
        )
    )


def test_wu010_exact_pullback_preserves_full_sky_l2_for_doppler_weight_one() -> None:
    q = _quadrupole()
    directions, weights, _, _ = _sphere_rule()
    beta_hat = np.array([0.4, -0.2, 0.3], dtype=float)
    beta = 0.31 * beta_hat / np.linalg.norm(beta_hat)

    source_directions = deaberrate_sky_direction(directions, beta)
    exact = thermodynamic_temperature_pullback(
        directions,
        beta,
        quadrupole_temperature(q, source_directions),
    )
    source = quadrupole_temperature(q, directions)

    np.testing.assert_allclose(
        np.sum(weights * exact * exact),
        np.sum(weights * source * source),
        atol=2.0e-13,
        rtol=0.0,
    )


def test_wu010_first_order_response_has_only_l1_l3_and_matches_stf_maps() -> None:
    q = _quadrupole()
    directions, weights, theta, phi = _sphere_rule()
    beta_hat = np.array([0.4, -0.2, 0.3], dtype=float)
    beta = 0.013 * beta_hat / np.linalg.norm(beta_hat)
    field = first_order_quadrupole_boost(q, beta, directions)

    powers = {
        ell: _multipole_power(
            field,
            ell=ell,
            weights=weights,
            theta=theta,
            phi=phi,
        )
        for ell in range(6)
    }
    support = powers[1] + powers[3]
    off_support = sum(
        value for ell, value in powers.items() if ell not in (1, 3)
    )
    assert off_support < 1.0e-24 * support

    observed_l3 = _stored_real_coefficients(
        field,
        ell=3,
        weights=weights,
        theta=theta,
        phi=phi,
    )
    expected_l3 = stf3_to_real_harmonic(
        quadrupole_boost_octupole(q, beta)
    )
    np.testing.assert_allclose(
        observed_l3,
        expected_l3,
        atol=3.0e-14,
        rtol=0.0,
    )

    dipole = quadrupole_boost_dipole(q, beta)
    root = math.sqrt(3.0 / (8.0 * math.pi))
    expected_l1 = np.asarray(
        [
            dipole[2] / math.sqrt(3.0 / (4.0 * math.pi)),
            -dipole[0] / (2.0 * root),
            dipole[1] / (2.0 * root),
        ]
    )
    observed_l1 = _stored_real_coefficients(
        field,
        ell=1,
        weights=weights,
        theta=theta,
        phi=phi,
    )
    np.testing.assert_allclose(
        observed_l1,
        expected_l1,
        atol=3.0e-14,
        rtol=0.0,
    )
