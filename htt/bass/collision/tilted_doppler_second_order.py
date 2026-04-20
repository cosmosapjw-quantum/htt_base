"""FB-4.3 — explicit ``v_e^2`` Doppler correction surface.

The quadratic Layer-B remainder is kept additive by construction:
the orthogonal LB-4 kernel is multiplied by the exact Doppler factor
``gamma_sq - 1``, which is identically zero at ``beta == 0`` and
expands as ``beta^2 + O(beta^4)`` for small tilt.
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from bass.collision.thomson_pstf import ThomsonAux, ThomsonPSTFCollisionOperator
from bass.collision.polarization import zero_polarization_hierarchy
from bass.hierarchy.pstf_tensor import PSTFHierarchyState, PSTFTensor
from bass.species.tilted import TiltedSpeciesBackground
from bass.hierarchy.pstf_tensor import zero_pstf


def evaluate_tilted_second_order_doppler_correction(
    ell: int,
    temperature_state: PSTFHierarchyState,
    eta: float,
    *,
    v_b_real_sph: np.ndarray,
    Gamma_T: float,
    tilted_electron: Optional[TiltedSpeciesBackground] = None,
) -> PSTFTensor:
    """Additive ``O(v_e^2)`` correction to ``K_{A_ell}``.

    The correction is evaluated on the orthogonal LB-4 kernel so the
    quadratic remainder does not silently alter the exact ``beta == 0``
    byte anchor. ``gamma_sq - 1`` is used instead of a truncated
    ``beta**2`` so the multiplicative factor remains deterministic for
    moderate tilt while still vanishing exactly at zero tilt.

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
      (production-scope discard; this helper stays additive).
    """
    if ell < 0 or ell > temperature_state.L:
        raise ValueError(
            f"ell={ell} outside temperature tower range 0..{temperature_state.L}"
        )
    _ = float(eta)
    if tilted_electron is None or tilted_electron.beta == 0.0:
        return zero_pstf(ell)

    aux = ThomsonAux(
        E_state=zero_polarization_hierarchy(temperature_state.L),
        v_b_real_sph=np.asarray(v_b_real_sph, dtype=np.float64),
        Gamma_T=float(Gamma_T),
    )
    anchor = ThomsonPSTFCollisionOperator().evaluate(
        ell,
        temperature_state,
        aux,
    )
    prefactor = tilted_electron.gamma_sq - 1.0
    return prefactor * anchor
