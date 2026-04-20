"""Observer-frame aligned aberration kernel."""
from __future__ import annotations

import numpy as np

from bass.observer.observer_boost import ObserverBoost


def aberration_kernel(L_max: int, boost: ObserverBoost) -> np.ndarray:
    """Return the linear aligned aberration kernel ``K_{ell ell'}``.

    The implementation follows the linear m-preserving aligned-boost
    recurrence

    ``a'_{ell} = a_{ell}
                 + beta * [ell/(2ell-1) a_{ell-1}
                          - (ell+1)/(2ell+3) a_{ell+1}]``,

    evaluated on a finite tower ``0 .. L_max``. In matrix form this is
    the tridiagonal kernel returned here.

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
      observer-speed scale ``v/c ≈ 1.23e-3``; its accessible Table 1 is
      an observer-velocity significance table rather than a direct
      kernel-coefficient fixture, which is recorded explicitly in the
      audit).
    """
    if not isinstance(boost, ObserverBoost):
        raise TypeError("boost must be an ObserverBoost instance")
    ell_max = int(L_max)
    if ell_max < 0:
        raise ValueError(f"L_max must be non-negative; got {L_max!r}")
    size = ell_max + 1
    kernel = np.eye(size, dtype=np.float64)
    beta = boost.velocity
    if beta == 0.0:
        return kernel

    for ell in range(size):
        if ell - 1 >= 0:
            kernel[ell, ell - 1] = beta * (ell / (2.0 * ell - 1.0))
        if ell + 1 < size:
            kernel[ell, ell + 1] = -beta * ((ell + 1.0) / (2.0 * ell + 3.0))
    return kernel
