"""Exact local-observer Lorentz pullback for thermodynamic CMB temperature.

The outward sky direction is ``n = -e``, where ``e`` is the photon
propagation direction.  A boosted observer has four-velocity
``u_tilde = gamma (u + beta)`` with the dimensionless three-velocity
``beta = v/c``.  In these conventions

``D(n) = gamma (1 + beta.n) = 1/[gamma (1 - beta.n_tilde)]``

and a blackbody thermodynamic-temperature field has Doppler weight one,
``T_tilde(n_tilde) = D T(n(n_tilde))``.

This module is an output-side local boost adapter.  It is not a global
matter-frame tilt, a frequency-dependent intensity transform, a foreground
model, an empirical velocity estimator, or a Bianchi-family classifier.
"""

from __future__ import annotations

import math
from collections.abc import Callable

import numpy as np


_DIRECTION_ATOL = 5.0e-13


class LorentzSkyPullbackError(ValueError):
    """Raised when the exact local-boost contract is violated."""


def _beta_vector(beta: object) -> tuple[np.ndarray, float]:
    try:
        vector = np.asarray(beta, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise LorentzSkyPullbackError("beta must be a finite real three-vector") from exc
    if vector.shape != (3,) or not np.all(np.isfinite(vector)):
        raise LorentzSkyPullbackError("beta must be a finite real three-vector")
    beta2 = float(np.dot(vector, vector))
    if beta2 >= 1.0:
        raise LorentzSkyPullbackError("beta must satisfy beta^2 < 1")
    return vector, beta2


def _unit_directions(value: object, *, label: str) -> np.ndarray:
    try:
        directions = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise LorentzSkyPullbackError(
            f"{label} must be finite unit three-vectors"
        ) from exc
    if (
        directions.ndim < 1
        or directions.shape[-1] != 3
        or not np.all(np.isfinite(directions))
    ):
        raise LorentzSkyPullbackError(f"{label} must be finite unit three-vectors")
    norms = np.linalg.norm(directions, axis=-1)
    if not np.allclose(norms, 1.0, rtol=0.0, atol=_DIRECTION_ATOL):
        raise LorentzSkyPullbackError(
            f"{label} must be unit normalized; no silent projection is allowed"
        )
    return directions


def lorentz_factor(beta: object) -> float:
    """Return ``gamma = (1-beta^2)^(-1/2)`` after exact-domain validation."""

    _, beta2 = _beta_vector(beta)
    return 1.0 / math.sqrt(1.0 - beta2)


def doppler_factor_unboosted(direction: object, beta: object) -> np.ndarray:
    """Return ``D = gamma(1+beta.n)`` in the unboosted sky chart."""

    directions = _unit_directions(direction, label="unboosted sky direction")
    vector, beta2 = _beta_vector(beta)
    gamma = 1.0 / math.sqrt(1.0 - beta2)
    projection = np.einsum("...i,i->...", directions, vector)
    return gamma * (1.0 + projection)


def doppler_factor_boosted(direction: object, beta: object) -> np.ndarray:
    """Return ``D = 1/[gamma(1-beta.n_tilde)]`` in the boosted chart."""

    directions = _unit_directions(direction, label="boosted sky direction")
    vector, beta2 = _beta_vector(beta)
    gamma = 1.0 / math.sqrt(1.0 - beta2)
    projection = np.einsum("...i,i->...", directions, vector)
    denominator = gamma * (1.0 - projection)
    if np.any(denominator <= 0.0):  # defensive; beta^2 < 1 already implies this
        raise LorentzSkyPullbackError("boosted Doppler denominator is nonpositive")
    return 1.0 / denominator


def aberrate_sky_direction(direction: object, beta: object) -> np.ndarray:
    """Map an unboosted outward line of sight ``n`` to ``n_tilde``.

    The active observer boost is ``+beta``.  The formula is exact to all
    orders in ``|beta| < 1`` and is vectorized over every leading axis.
    """

    directions = _unit_directions(direction, label="unboosted sky direction")
    vector, beta2 = _beta_vector(beta)
    if beta2 == 0.0:
        return directions.copy()
    gamma = 1.0 / math.sqrt(1.0 - beta2)
    projection = np.einsum("...i,i->...", directions, vector)
    coefficient = gamma + (gamma - 1.0) * projection / beta2
    numerator = directions + np.expand_dims(coefficient, -1) * vector
    denominator = gamma * (1.0 + projection)
    output = numerator / np.expand_dims(denominator, -1)
    if not np.all(np.isfinite(output)):
        raise LorentzSkyPullbackError("aberrated direction became nonfinite")
    return output


def deaberrate_sky_direction(direction: object, beta: object) -> np.ndarray:
    """Map a boosted outward line of sight ``n_tilde`` back to ``n``."""

    directions = _unit_directions(direction, label="boosted sky direction")
    vector, beta2 = _beta_vector(beta)
    if beta2 == 0.0:
        return directions.copy()
    gamma = 1.0 / math.sqrt(1.0 - beta2)
    projection = np.einsum("...i,i->...", directions, vector)
    coefficient = (gamma - 1.0) * projection / beta2 - gamma
    numerator = directions + np.expand_dims(coefficient, -1) * vector
    denominator = gamma * (1.0 - projection)
    output = numerator / np.expand_dims(denominator, -1)
    if not np.all(np.isfinite(output)):
        raise LorentzSkyPullbackError("inverse-aberrated direction became nonfinite")
    return output


def solid_angle_jacobian(direction: object, beta: object) -> np.ndarray:
    """Return ``dOmega_tilde/dOmega = D(n)^(-2)`` on the full sky."""

    doppler = doppler_factor_unboosted(direction, beta)
    return doppler**-2


def thermodynamic_temperature_pullback(
    boosted_direction: object,
    beta: object,
    source_temperature: object,
) -> np.ndarray:
    """Apply the exact Doppler-weight-one absolute-temperature pullback.

    ``source_temperature`` must already be evaluated at the corresponding
    inverse-aberrated directions ``n(n_tilde)``.  It must be strictly
    positive because this API represents absolute blackbody thermodynamic
    temperature, not a signed anisotropy or frequency-dependent intensity.
    The function only applies the exact local-observer Doppler factor; it
    never interpolates a map or changes thermodynamic units.
    """

    directions = _unit_directions(
        boosted_direction, label="boosted sky direction"
    )
    try:
        source = np.asarray(source_temperature, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise LorentzSkyPullbackError("source temperature must be finite") from exc
    if not np.all(np.isfinite(source)):
        raise LorentzSkyPullbackError("source temperature must be finite")
    target_shape = directions.shape[:-1]
    try:
        values = np.broadcast_to(source, target_shape)
    except ValueError as exc:
        raise LorentzSkyPullbackError(
            "source temperature cannot be broadcast to the sky directions"
        ) from exc
    if np.any(values <= 0.0):
        raise LorentzSkyPullbackError(
            "absolute thermodynamic temperature must be strictly positive"
        )
    return doppler_factor_boosted(directions, beta) * values


def pullback_thermodynamic_temperature_field(
    boosted_direction: object,
    beta: object,
    source_field: Callable[[np.ndarray], object],
) -> np.ndarray:
    """Evaluate and boost an absolute temperature field at the correct sky points.

    The callback receives the inverse-aberrated unboosted directions.  This
    high-level API prevents callers from accidentally evaluating the source
    field at ``n_tilde`` and applying only a Doppler multiplier.
    """

    directions = _unit_directions(
        boosted_direction, label="boosted sky direction"
    )
    if not callable(source_field):
        raise LorentzSkyPullbackError("source field must be callable")
    source_directions = deaberrate_sky_direction(directions, beta)
    source_temperature = source_field(source_directions)
    return thermodynamic_temperature_pullback(
        directions,
        beta,
        source_temperature,
    )


__all__ = [
    "LorentzSkyPullbackError",
    "aberrate_sky_direction",
    "deaberrate_sky_direction",
    "doppler_factor_boosted",
    "doppler_factor_unboosted",
    "lorentz_factor",
    "pullback_thermodynamic_temperature_field",
    "solid_angle_jacobian",
    "thermodynamic_temperature_pullback",
]
