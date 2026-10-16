"""Finite ell6..32 masked response envelopes for declared synthetic power only.

The matrix is a source-processing geometry operator. These routines do not
estimate an observed C_l, sky covariance, cosmological epsilon, or Bianchi
response. Shell ordering is the PR536/537 real-harmonic ordering.
"""
from __future__ import annotations

from collections.abc import Mapping
import numpy as np

ELLS = tuple(range(6, 33))
OLD_COUNT = 253
NEW_COUNT = 800


class EnvelopeInputError(ValueError):
    pass


def shell_slice(ell: int) -> slice:
    if type(ell) is not int or ell not in ELLS:
        raise EnvelopeInputError("integer ell 6..32 required")
    return slice(ell * ell - 36, (ell + 1) ** 2 - 36)


def joined_operator(old: np.ndarray, new: np.ndarray) -> np.ndarray:
    """Join retained ell2..5 responses after strict source column checks."""
    a = np.asarray(old)
    b = np.asarray(new)
    if (a.shape != (32, OLD_COUNT) or b.shape != (32, NEW_COUNT) or
            not np.issubdtype(a.dtype, np.number) or
            not np.issubdtype(b.dtype, np.number) or
            not np.isrealobj(a) or not np.isrealobj(b) or
            not np.isfinite(a).all() or not np.isfinite(b).all()):
        raise EnvelopeInputError("real finite 32x253 and 32x800 source matrices required")
    out = np.concatenate((a.astype(float), b.astype(float)), axis=1)
    if out.shape != (32, 1053):
        raise EnvelopeInputError("ell6..32 column count mismatch")
    assert shell_slice(16).stop == OLD_COUNT
    assert shell_slice(17).start == OLD_COUNT
    assert shell_slice(32).stop == 1053
    return out


def _values(values: Mapping[int, float], name: str) -> np.ndarray:
    if not isinstance(values, Mapping) or set(values) != set(ELLS):
        raise EnvelopeInputError(f"{name}: every ell6..32 must be explicit")
    out = []
    for ell in ELLS:
        value = values[ell]
        if isinstance(value, (bool, np.bool_)) or np.iscomplexobj(value):
            raise EnvelopeInputError(f"{name}[{ell}]: invalid scalar")
        try:
            scalar = float(value)
        except (ValueError, TypeError, OverflowError) as exc:
            raise EnvelopeInputError(f"{name}[{ell}]: invalid scalar") from exc
        if not np.isfinite(scalar) or scalar < 0:
            raise EnvelopeInputError(f"{name}[{ell}]: finite nonnegative required")
        out.append(scalar)
    return np.asarray(out)


def _operator(operator: np.ndarray) -> np.ndarray:
    k = np.asarray(operator)
    if (k.shape != (32, 1053) or not np.isrealobj(k) or
            not np.issubdtype(k.dtype, np.number) or not np.isfinite(k).all()):
        raise EnvelopeInputError("finite real 32x1053 ell6..32 operator required")
    return k.astype(float, copy=False)


def shell_grams(operator: np.ndarray) -> dict[int, np.ndarray]:
    k = _operator(operator)
    return {ell: k[:, shell_slice(ell)] @ k[:, shell_slice(ell)].T for ell in ELLS}


def independent_shell_covariance(operator: np.ndarray,
                                 power: Mapping[int, float]) -> np.ndarray:
    """Conditional K diag(C_l I) K^T; cross-shell covariance assumed zero."""
    vals = _values(power, "scenario C_l")
    k = _operator(operator)
    out = np.zeros((32, 32), float)
    for value, gram in zip(vals, shell_grams(k).values()):
        out += value * gram
    out = (out + out.T) / 2
    if not np.isfinite(out).all() or np.linalg.eigvalsh(out)[0] < -1e-10 * max(1., np.linalg.norm(out, 2)):
        raise EnvelopeInputError("calculated covariance is not PSD")
    return out


def sharp_ellipsoid(operator: np.ndarray,
                    radii: Mapping[int, float]) -> dict[str, object]:
    """Sharp output norm for sum_l ||a_l||^2/R_l^2 <= 1."""
    values = _values(radii, "scenario radius")
    k = _operator(operator)
    scale = float(np.max(values))
    if scale == 0.:
        return {"bound": 0., "normalized_gram": np.zeros((32, 32)),
                "gram_scale": 0.,
                "witness": np.zeros(1053), "witness_constraint": 0.,
                "achieved": 0.}
    # Keep the spectral problem at unit scale. Squaring a valid 1e-200
    # radius in native units would otherwise underflow to a false zero.
    normalized = values / scale
    gram = np.zeros((32, 32), float)
    for radius, shell in zip(normalized, shell_grams(k).values()):
        gram += radius * radius * shell
    gram = (gram + gram.T) / 2
    eigen, vectors = np.linalg.eigh(gram)
    if eigen[0] < -1e-10 * max(1., eigen[-1]):
        raise EnvelopeInputError("ellipsoid image Gram is not PSD")
    largest = max(float(eigen[-1]), 0.)
    normalized_bound = float(np.sqrt(largest))
    bound = float(scale * normalized_bound)
    if not np.isfinite(bound) or (largest > 0 and bound == 0.):
        raise EnvelopeInputError("sharp bound outside representable float range")
    witness = np.zeros(1053, float)
    if largest > 0:
        left = vectors[:, -1]
        unit_witness = np.zeros(1053, float)
        for ell, radius in zip(ELLS, normalized):
            sl = shell_slice(ell)
            unit_witness[sl] = radius * radius * (k[:, sl].T @ left) / normalized_bound
        witness = scale * unit_witness
        if not np.isfinite(witness).all():
            raise EnvelopeInputError("ellipsoid witness outside representable float range")
        ellipsoid_norm_sq = sum(float(np.linalg.norm(unit_witness[shell_slice(ell)] / radius)**2)
                                for ell, radius in zip(ELLS, normalized) if radius > 0)
        normalized_achieved = float(np.linalg.norm(k @ unit_witness))
        achieved = float(scale * normalized_achieved)
        if not np.isclose(ellipsoid_norm_sq, 1., rtol=1e-10, atol=1e-10) or not np.isclose(normalized_achieved, normalized_bound, rtol=1e-10, atol=1e-10):
            raise EnvelopeInputError("ellipsoid witness fails saturation")
    else:
        ellipsoid_norm_sq = achieved = 0.
    return {"bound": bound, "normalized_gram": gram, "gram_scale": scale,
            "witness": witness,
            "witness_constraint": float(ellipsoid_norm_sq), "achieved": achieved}


def shared_coordinate_toy(operator: np.ndarray, power: Mapping[int, float],
                          rho: float) -> np.ndarray:
    """Manufactured cross-shell coordinate coupling with fixed C_l marginals."""
    if isinstance(rho, (bool, np.bool_)) or not isinstance(rho, (int, float, np.integer, np.floating)) or not np.isfinite(rho) or not 0 <= rho <= 1:
        raise EnvelopeInputError("synthetic rho in [0,1] required")
    vals = _values(power, "scenario C_l")
    k = _operator(operator)
    base = independent_shell_covariance(k, power)
    shared = np.zeros((32, 65), float)
    for ell, value in zip(ELLS, vals):
        shared[:, :2*ell+1] += np.sqrt(value) * k[:, shell_slice(ell)]
    result = (1-rho) * base + rho * (shared @ shared.T)
    return (result + result.T) / 2


def cross_shell_agnostic_std_bound(operator: np.ndarray,
                                   power: Mapping[int, float]) -> float:
    """Minkowski upper bound given only diagonal shell C_l I marginals."""
    vals = _values(power, "scenario C_l")
    k = _operator(operator)
    return float(sum(np.sqrt(value) * np.linalg.norm(k[:, shell_slice(ell)], 2)
                     for ell, value in zip(ELLS, vals)))


def scenario_templates() -> dict[str, dict[int, float]]:
    return {
        "WHITE_UNIT_VARIANCE_SCENARIO": {ell: 1. for ell in ELLS},
        "RED_ELL6_NORMALIZED_SCENARIO": {ell: 42. / (ell * (ell + 1)) for ell in ELLS},
        "BLUE_ELL6_NORMALIZED_SCENARIO": {ell: ell * (ell + 1) / 42. for ell in ELLS},
    }
