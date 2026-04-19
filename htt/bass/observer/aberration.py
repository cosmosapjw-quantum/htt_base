"""FB-8.2 skeleton — observer-frame aberration-kernel contract.

This module deliberately ships no aberration physics during the
FB-META-8 rotation. The public surface below is a contract placeholder
only and must raise ``NotImplementedError`` until the observer-frame
kernel is wired to the FB-8 adapters and discriminator stack.
"""
from __future__ import annotations

import numpy as np

from bass.observer.observer_boost import ObserverBoost


def aberration_kernel(L_max: int, boost: ObserverBoost) -> np.ndarray:
    """Future FB-8.2 observer-frame aberration kernel ``K_{ell ell'}``.

    Contract only: this surface is reserved for the aligned-boost
    kernel that acts on cosmological-frame multipoles before the FB-8.3
    observer adapters and the FB-8.5 discriminator.

    References
    ----------
    - ``docs/lowell_bianchi/extended_coverage/FB8_DISCRIMINATOR_SDD.md``
      §3 (canonical kernel signature and invariants).
    - ``bass/hierarchy/boost_kernel.py`` (existing axi-symmetric
      hierarchy-side seed; observer-side kernel remains separate).
    - Challinor & van Leeuwen 2002, Phys. Rev. D 65, 103001,
      arXiv:astro-ph/0112457 (corrected preprint locator; the
      prompt-supplied ``astro-ph/0205005`` is a different paper and is
      rejected in the FB-META-8 audit).
    - Planck Collaboration 2013 XXVII, arXiv:1303.5087 (Sun-dipole
      observer-speed scale ``v/c ≈ 1.23e-3``; Table 1 is an observer-
      velocity significance table rather than a direct kernel-coefficient
      fixture, which is recorded explicitly in the audit).
    """
    raise NotImplementedError(
        "FB-8.2 skeleton only: observer-frame aberration kernel is not "
        "implemented."
    )
