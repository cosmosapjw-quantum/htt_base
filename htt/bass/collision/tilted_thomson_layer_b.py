"""FB-4.1 skeleton — tilted Thomson Layer-B collision surface.

This module deliberately ships no physics during the FB-META-4
rotation. The public surface below is a contract placeholder only and
must raise ``NotImplementedError`` until the full-Lorentz PSTF
collision kernel is implemented.
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from bass.collision.polarization import PolarizationHierarchyState
from bass.hierarchy.pstf_tensor import PSTFHierarchyState, PSTFTensor
from bass.species.tilted import TiltedSpeciesBackground


def evaluate_tilted_thomson_pstf_collision(
    ell: int,
    temperature_state: PSTFHierarchyState,
    polarization_state: PolarizationHierarchyState,
    eta: float,
    *,
    v_b_real_sph: np.ndarray,
    Gamma_T: float,
    tilted_electron: Optional[TiltedSpeciesBackground] = None,
) -> PSTFTensor:
    """Future FB-4.1 full-Lorentz Thomson collision source ``K_{A_ℓ}``.

    Contract only: this surface is reserved for the tilted-electron
    boost of the LB-4 orthogonal Thomson kernel. The eventual
    implementation must preserve the ``tilted_electron is None`` / ``β
    = 0`` byte-identity reduction to
    ``bass.collision.thomson_pstf.ThomsonPSTFCollisionOperator`` while
    consuming the same non-perturbative tilt SSOT used by
    ``bass.collision.tilted_visibility.TiltedVisibility``.

    References
    ----------
    - ``docs/lowell_bianchi/04_thomson_collision_spec.md §8.2``.
    - ``bass/collision/thomson_pstf.py`` (LB-4 orthogonal anchor).
    - ``bass/collision/tilted_visibility.py`` (lowell §11.3 Lorentz
      factor surface).
    - Challinor 2000, arXiv:astro-ph/9911481, eqs. (2.26)–(2.28)
      (frame-change multipole mixing; corrected from the broken
      prompt-supplied arXiv ID ``astro-ph/0006237``).
    """
    raise NotImplementedError(
        "FB-4.1 skeleton only: full-Lorentz Thomson PSTF collision "
        "surface not implemented."
    )
