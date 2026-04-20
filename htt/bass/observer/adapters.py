"""Observer-frame ``C_ell`` and ``a_{ell m}`` adapters."""
from __future__ import annotations

import numpy as np

from bass.observer.aberration import aberration_kernel
from bass.observer.observer_boost import ObserverBoost

_SPECTRUM_KEYS = frozenset({"TT", "EE", "TE", "BB"})


def _copy_value(value: object) -> object:
    if isinstance(value, np.ndarray):
        return np.array(value, copy=True)
    return value


def apply_observer_boost(
    Cl_frame: dict[str, np.ndarray],
    boost: ObserverBoost,
    L_max: int,
) -> dict[str, np.ndarray]:
    """Apply the observer-frame linear boost to diagonal spectra.

    The adapter treats each diagonal spectrum as an ``ell``-space vector
    and propagates it with the squared-magnitude kernel
    ``sum_{ell'} |K_{ell ell'}|^2 C_{ell'}``, which is the diagonal
    piece implied by applying the same aligned linear mixing to every
    ``m`` block.

    The ``boost.rapidity == 0`` path returns a byte-identical copy of
    the input spectra.

    References
    ----------
    - ``docs/lowell_bianchi/extended_coverage/FB8_DISCRIMINATOR_SDD.md``
      §4 (canonical observer-frame adapter contract).
    - ``bass.observer.aberration_kernel`` (FB-8.2 observer-only kernel
      dependency).
    - Challinor & van Leeuwen 2002, arXiv:astro-ph/0112457 §II–III
      (temperature and polarization multipole transformations).
    - Planck Collaboration 2013 XXVII, arXiv:1303.5087 (observer-speed
      scale and de-boosting context around the Sun-dipole value
      ``v/c ≈ 1.23e-3``).
    """
    if not isinstance(boost, ObserverBoost):
        raise TypeError("boost must be an ObserverBoost instance")
    ell_max = int(L_max)
    out = {key: _copy_value(value) for key, value in Cl_frame.items()}
    if boost.rapidity == 0.0:
        return out

    kernel = aberration_kernel(ell_max, boost)
    power_kernel = kernel * kernel
    ells = np.arange(ell_max + 1, dtype=float)
    shared_m_weight = (
        2.0 * np.minimum.outer(ells, ells) + 1.0
    ) / (2.0 * ells[:, None] + 1.0)
    for key in _SPECTRUM_KEYS.intersection(Cl_frame):
        arr = np.asarray(Cl_frame[key])
        if arr.ndim != 1:
            raise ValueError(
                f"Cl_frame[{key!r}] must be 1-D; got shape {arr.shape}"
            )
        if arr.size < ell_max + 1:
            raise ValueError(
                f"Cl_frame[{key!r}] length {arr.size} is smaller than "
                f"L_max + 1 = {ell_max + 1}"
            )
        mixed = np.array(arr, copy=True)
        mixed[: ell_max + 1] = (power_kernel * shared_m_weight) @ arr[: ell_max + 1]
        out[key] = mixed
    return out


def observed_alm_mixing(
    alm: np.ndarray,
    boost: ObserverBoost,
    L_max: int,
) -> np.ndarray:
    """Apply the observer-frame linear boost to harmonic coefficients.

    The first axis is interpreted as the multipole index ``ell``. Any
    trailing dimensions are treated as independent ``m`` or field
    channels that all receive the same aligned ``ell``-space mixing.

    The ``boost.rapidity == 0`` path returns a byte-identical copy of
    the input harmonic array.

    References
    ----------
    - ``docs/lowell_bianchi/extended_coverage/FB8_DISCRIMINATOR_SDD.md``
      §4 (canonical harmonic-mixing contract).
    - ``bass.observer.aberration_kernel`` (shared FB-8.2 kernel
      dependency).
    - Challinor & van Leeuwen 2002, arXiv:astro-ph/0112457 §III
      (linear-polarization and multipole-mixing transformation laws).
    """
    if not isinstance(boost, ObserverBoost):
        raise TypeError("boost must be an ObserverBoost instance")
    arr = np.asarray(alm)
    ell_max = int(L_max)
    if arr.ndim == 0:
        raise ValueError("alm must carry an ell axis; scalar input is invalid")
    if arr.shape[0] < ell_max + 1:
        raise ValueError(
            f"alm first-axis length {arr.shape[0]} is smaller than "
            f"L_max + 1 = {ell_max + 1}"
        )
    out = np.array(arr, copy=True)
    if boost.rapidity == 0.0:
        return out

    kernel = aberration_kernel(ell_max, boost)
    out[: ell_max + 1] = np.tensordot(kernel, arr[: ell_max + 1], axes=(1, 0))
    return out
