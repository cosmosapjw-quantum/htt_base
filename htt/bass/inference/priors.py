"""Inference priors for the FB-11 posterior driver."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable

import numpy as np

from bass.background.bianchi_types import TYPE_REGISTRY, get_type


_LogPdf = Callable[[np.ndarray], np.ndarray]
_SampleFn = Callable[[np.random.Generator, int], np.ndarray]
_LOG_2PI = math.log(2.0 * math.pi)
_LOG_4PI = math.log(4.0 * math.pi)
_PLANCK_SIGMA_MNU_SIGMA_EV = 0.15
_OBSERVER_BOOST_BETA_MEAN = 1.23e-3
_OBSERVER_BOOST_BETA_SIGMA = 1.23e-3
_SUN_CMB_DIPOLE_L_DEG = 264.02
_SUN_CMB_DIPOLE_B_DEG = 48.25


@dataclass(frozen=True)
class Prior:
    """Named inference prior with log-density and seeded sampling."""

    name: str
    domain: tuple[float, float] | None
    log_pdf: _LogPdf
    sample: _SampleFn


def _as_row_vector(values: np.ndarray, *, width: int) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim == 0:
        if width != 1:
            raise ValueError(f"expected width={width}; got scalar input")
        return array.reshape(1, 1)
    if array.ndim == 1:
        if width == 0 and array.size == 0:
            return array.reshape(1, 0)
        if width == 1:
            return array.reshape(-1, 1)
        if array.size != width:
            raise ValueError(f"expected width={width}; got shape {array.shape}")
        return array.reshape(1, width)
    if array.ndim == 2:
        if array.shape[1] != width:
            raise ValueError(f"expected width={width}; got shape {array.shape}")
        return array
    raise ValueError(f"expected at most 2 dimensions; got shape {array.shape}")


def _scalarise(result: np.ndarray, original: np.ndarray) -> np.ndarray:
    if np.asarray(original).ndim <= 1:
        return np.asarray(result, dtype=float).reshape(-1)
    return np.asarray(result, dtype=float)


def _half_normal_log_pdf(values: np.ndarray, *, sigma: float) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    row = _as_row_vector(array, width=1).reshape(-1)
    out = np.full(row.shape, float("-inf"), dtype=float)
    finite = np.isfinite(row) & (row >= 0.0)
    if np.any(finite):
        out[finite] = (
            math.log(2.0)
            - math.log(sigma)
            - 0.5 * _LOG_2PI
            - 0.5 * (row[finite] / sigma) ** 2
        )
    return _scalarise(out, array)


def _sample_half_normal(
    rng: np.random.Generator,
    n: int,
    *,
    sigma: float,
) -> np.ndarray:
    return np.abs(rng.normal(loc=0.0, scale=sigma, size=int(n)))


def _direction_from_galactic(l_deg: float, b_deg: float) -> np.ndarray:
    lon = math.radians(float(l_deg))
    lat = math.radians(float(b_deg))
    return np.array(
        [
            math.cos(lat) * math.cos(lon),
            math.cos(lat) * math.sin(lon),
            math.sin(lat),
        ],
        dtype=float,
    )


SUN_CMB_DIPOLE_DIRECTION = _direction_from_galactic(
    _SUN_CMB_DIPOLE_L_DEG,
    _SUN_CMB_DIPOLE_B_DEG,
)


def prior_rapidity(label: str, *, sigma: float) -> Prior:
    """Half-Gaussian prior on boost rapidity.

    References
    ----------
    - `docs/lowell_bianchi/extended_coverage/FB11_INFERENCE_DRIVER_SDD.md`
      §2.1.
    - Planck Collaboration 2018 VI, `arXiv:1807.06209`.
    """
    sigma = float(sigma)
    if not np.isfinite(sigma) or sigma <= 0.0:
        raise ValueError(f"sigma must be positive and finite; got {sigma!r}")

    def _log_pdf(values: np.ndarray) -> np.ndarray:
        return _half_normal_log_pdf(values, sigma=sigma)

    def _sample(rng: np.random.Generator, n: int) -> np.ndarray:
        return _sample_half_normal(rng, n, sigma=sigma)

    return Prior(
        name=str(label),
        domain=(0.0, float("inf")),
        log_pdf=_log_pdf,
        sample=_sample,
    )


def prior_direction() -> Prior:
    """Isotropic prior on the unit sphere `S^2`.

    References
    ----------
    - `docs/lowell_bianchi/extended_coverage/FB11_INFERENCE_DRIVER_SDD.md`
      §2.1.
    - `docs/lowell_bianchi/00_conventions.md` §13.
    """

    def _log_pdf(values: np.ndarray) -> np.ndarray:
        array = np.asarray(values, dtype=float)
        row = _as_row_vector(array, width=3)
        norms = np.linalg.norm(row, axis=1)
        out = np.full(norms.shape, float("-inf"), dtype=float)
        valid = np.isfinite(norms) & np.isclose(norms, 1.0, atol=1.0e-10, rtol=0.0)
        out[valid] = -_LOG_4PI
        return _scalarise(out, array)

    def _sample(rng: np.random.Generator, n: int) -> np.ndarray:
        draws = rng.normal(size=(int(n), 3))
        norms = np.linalg.norm(draws, axis=1, keepdims=True)
        zero = norms[:, 0] == 0.0
        while np.any(zero):
            draws[zero] = rng.normal(size=(int(np.sum(zero)), 3))
            norms = np.linalg.norm(draws, axis=1, keepdims=True)
            zero = norms[:, 0] == 0.0
        return draws / norms

    return Prior(
        name="direction",
        domain=None,
        log_pdf=_log_pdf,
        sample=_sample,
    )


def prior_Sigma_mnu() -> Prior:
    """Half-Gaussian prior on `Sigma_mnu` with the Planck 2018 VI scale.

    References
    ----------
    - `docs/lowell_bianchi/extended_coverage/FB11_INFERENCE_DRIVER_SDD.md`
      §2.1.
    - Planck Collaboration 2018 VI, `arXiv:1807.06209`, Table 2.
    - `docs/audits/AUDIT_PHASE_FB_META11_2026-04-20.md` §FB-11.1.
    """
    return prior_rapidity("Sigma_mnu", sigma=_PLANCK_SIGMA_MNU_SIGMA_EV)


def prior_observer_boost() -> Prior:
    """Gaussian prior centred on the measured CMB dipole vector.

    The sampled quantity is the observer-velocity vector `beta * v_hat`
    in Cartesian components. The prior mode therefore sits at the
    Planck-era Sun-CMB dipole direction with magnitude `1.23e-3`.

    References
    ----------
    - `docs/lowell_bianchi/extended_coverage/FB11_INFERENCE_DRIVER_SDD.md`
      §2.1.
    - Kosowsky & Kahniashvili 2011, `arXiv:1007.4539`, §IV.
    """
    sigma = float(_OBSERVER_BOOST_BETA_SIGMA)
    mean = float(_OBSERVER_BOOST_BETA_MEAN) * SUN_CMB_DIPOLE_DIRECTION

    def _log_pdf(values: np.ndarray) -> np.ndarray:
        array = np.asarray(values, dtype=float)
        row = _as_row_vector(array, width=3)
        diff = row - mean.reshape(1, 3)
        norm_sq = np.sum(diff * diff, axis=1)
        out = (
            -1.5 * _LOG_2PI
            - 3.0 * math.log(sigma)
            - 0.5 * norm_sq / (sigma * sigma)
        )
        return _scalarise(out, array)

    def _sample(rng: np.random.Generator, n: int) -> np.ndarray:
        return rng.normal(loc=mean, scale=sigma, size=(int(n), 3))

    return Prior(
        name="observer_boost",
        domain=None,
        log_pdf=_log_pdf,
        sample=_sample,
    )


def _structure_scale_bounds(bianchi_type: str) -> tuple[float, float]:
    structure = get_type(str(bianchi_type))
    base_scale = max(
        abs(structure.n1),
        abs(structure.n2),
        abs(structure.n3),
        abs(structure.a_twist),
        1.0e-3,
    )
    return (base_scale * 1.0e-4, base_scale * 5.0e-2)


def prior_structure_constants(bianchi_type: str) -> Prior:
    """Prior on the free structure-constant scale for one Bianchi type.

    The prior is log-flat on a single positive scale parameter anchored
    to the canonical default amplitudes in
    `bass.background.bianchi_types`. Types with no free structure
    parameters (`FLRW` and `I`) expose a zero-dimensional delta prior.

    References
    ----------
    - `docs/lowell_bianchi/extended_coverage/FB11_INFERENCE_DRIVER_SDD.md`
      §2.1.
    - `docs/lowell_bianchi/extended_coverage/EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md`
      §5.
    """
    label = str(bianchi_type)
    if label not in TYPE_REGISTRY:
        raise KeyError(
            f"Unknown Bianchi type {label!r}; valid labels: {sorted(TYPE_REGISTRY)}"
        )
    if label in {"FLRW", "I"}:
        def _log_pdf(values: np.ndarray) -> np.ndarray:
            array = np.asarray(values, dtype=float)
            row = _as_row_vector(array, width=0)
            out = np.zeros(row.shape[0], dtype=float)
            return _scalarise(out, array)

        def _sample(rng: np.random.Generator, n: int) -> np.ndarray:
            _ = rng
            return np.empty((int(n), 0), dtype=float)

        return Prior(
            name=f"{label}_structure_constants",
            domain=None,
            log_pdf=_log_pdf,
            sample=_sample,
        )

    lower, upper = _structure_scale_bounds(label)
    log_width = math.log(upper / lower)

    def _log_pdf(values: np.ndarray) -> np.ndarray:
        array = np.asarray(values, dtype=float)
        row = _as_row_vector(array, width=1).reshape(-1)
        out = np.full(row.shape, float("-inf"), dtype=float)
        valid = np.isfinite(row) & (row >= lower) & (row <= upper)
        if np.any(valid):
            out[valid] = -np.log(row[valid]) - log_width
        return _scalarise(out, array)

    def _sample(rng: np.random.Generator, n: int) -> np.ndarray:
        return np.exp(rng.uniform(math.log(lower), math.log(upper), size=int(n)))

    return Prior(
        name=f"{label}_structure_constants",
        domain=(lower, upper),
        log_pdf=_log_pdf,
        sample=_sample,
    )
