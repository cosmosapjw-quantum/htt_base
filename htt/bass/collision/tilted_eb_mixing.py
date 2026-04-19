"""FB-4.2 skeleton — tilted E/B collision-side mixing surface.

This module deliberately ships no physics during the FB-META-4
rotation. The public surface below is a contract placeholder only and
must raise ``NotImplementedError`` until the tilted LOS E↔B mixing
surface is implemented.
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from bass.collision.polarization import PolarizationHierarchyState
from bass.hierarchy.pstf_tensor import PSTFHierarchyState, PSTFTensor
from bass.species.tilted import TiltedSpeciesBackground


def evaluate_tilted_polarization_eb_collision(
    ell: int,
    e_state: PolarizationHierarchyState,
    eta: float,
    *,
    Pi_2_packed: Optional[np.ndarray],
    Gamma_T: float,
    b_state: Optional[PSTFHierarchyState] = None,
    tilted_electron: Optional[TiltedSpeciesBackground] = None,
) -> tuple[PSTFTensor, PSTFTensor]:
    """Future FB-4.2 tilted E↔B collision surface.

    Contract only: this surface is reserved for the LOS-tilt-driven
    mixing between E- and B-mode polarization multipoles. The eventual
    implementation must preserve the ``tilted_electron is None`` /
    ``β = 0`` reduction to the existing E-mode collision source in
    ``bass.collision.polarization`` while returning an identically zero
    B-mode source in the same limit.

    References
    ----------
    - ``docs/lowell_bianchi/04_thomson_collision_spec.md §5`` and
      `§8`.
    - ``bass/collision/polarization.py`` (current E-only anchor).
    - ``bass/los/bianchi_propagator.py`` (Type I `ψ' = 0` B-mode floor).
    - Kamionkowski-Kosowsky-Stebbins 1997, arXiv:astro-ph/9611125
      §III (E/B basis contract).
    """
    raise NotImplementedError(
        "FB-4.2 skeleton only: tilted E/B collision surface not "
        "implemented."
    )
