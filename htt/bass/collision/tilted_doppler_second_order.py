"""FB-4.3 skeleton — explicit ``v_e^2`` Doppler correction surface.

This module deliberately ships no physics during the FB-META-4
rotation. The public surface below is a contract placeholder only and
must raise ``NotImplementedError`` until the explicit second-order
Doppler correction surface is either implemented or retired by a fresh
scope decision.
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from bass.hierarchy.pstf_tensor import PSTFHierarchyState, PSTFTensor
from bass.species.tilted import TiltedSpeciesBackground


def evaluate_tilted_second_order_doppler_correction(
    ell: int,
    temperature_state: PSTFHierarchyState,
    eta: float,
    *,
    v_b_real_sph: np.ndarray,
    Gamma_T: float,
    tilted_electron: Optional[TiltedSpeciesBackground] = None,
) -> PSTFTensor:
    """Future FB-4.3 additive ``O(v_e^2)`` correction to ``K_{A_ell}``.

    Contract only: this surface is reserved for any explicit
    second-order Doppler remainder that sits on top of the FB-4.1
    linear tilted Thomson kernel. The eventual implementation must
    keep the correction additive and reduce to an identically zero
    contribution when ``tilted_electron is None`` or ``β = 0`` so the
    orthogonal LB-4 collision source remains byte-identical.

    References
    ----------
    - ``docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-4``.
    - ``docs/lowell_bianchi/04_thomson_collision_spec.md §1`` and
      ``§8.2``.
    - ``bass/species/tilted.py`` (exact ``gamma_sq`` / ``v_vector`` /
      ``β^2`` SSOT).
    - ``bass/hierarchy/tilt_kinematics.py`` (additive helper pattern
      with a ``β = 0`` short-circuit).
    - ``docs/lowell_bianchi/extended_coverage/SCOPE_DECISIONS.md §4``
      (current production-scope discard; this skeleton is contract
      only).
    """
    raise NotImplementedError(
        "FB-4.3 skeleton only: explicit v_e^2 Doppler correction "
        "surface not implemented."
    )
