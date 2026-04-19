"""FB-8.3 skeleton — observer-frame ``C_ell`` / ``a_{ell m}`` adapters.

This module deliberately ships no observer-frame adapter physics during
the FB-META-8 rotation. The public surfaces below are contract
placeholders only and must raise ``NotImplementedError`` until the
aberration kernel is wired to cosmological-frame spectra and harmonic
maps.
"""
from __future__ import annotations

import numpy as np

from bass.observer.aberration import aberration_kernel
from bass.observer.observer_boost import ObserverBoost


def apply_observer_boost(
    Cl_frame: dict[str, np.ndarray],
    boost: ObserverBoost,
    L_max: int,
) -> dict[str, np.ndarray]:
    """Future FB-8.3 observer-frame spectrum adapter.

    Contract only: this surface will apply the observer-frame
    aberration/modulation map to cosmological-frame diagonal spectra.
    The `boost.rapidity == 0` path is reserved to remain byte-identical
    to the input cosmological-frame spectra.

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
    raise NotImplementedError(
        "FB-8.3 skeleton only: observer-frame spectrum adaptation is "
        "not implemented."
    )


def observed_alm_mixing(
    alm: np.ndarray,
    boost: ObserverBoost,
    L_max: int,
) -> np.ndarray:
    """Future FB-8.3 observer-frame harmonic-mixing adapter.

    Contract only: this surface will apply observer-frame aberration to
    cosmological-frame harmonic coefficients. The `boost.rapidity == 0`
    path is reserved to remain byte-identical to the input harmonic
    array.

    References
    ----------
    - ``docs/lowell_bianchi/extended_coverage/FB8_DISCRIMINATOR_SDD.md``
      §4 (canonical harmonic-mixing contract).
    - ``bass.observer.aberration_kernel`` (shared FB-8.2 kernel
      dependency).
    - Challinor & van Leeuwen 2002, arXiv:astro-ph/0112457 §III
      (linear-polarization and multipole-mixing transformation laws).
    """
    raise NotImplementedError(
        "FB-8.3 skeleton only: observer-frame harmonic mixing is not "
        "implemented."
    )
