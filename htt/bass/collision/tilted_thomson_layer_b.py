"""FB-4.1 — tilted Thomson Layer-B collision surface.

The current repo-level boost SSOT is the axisymmetric linearised
Challinor 2000 recurrence already shipped in ``bass.hierarchy.
boost_kernel``. This module uses that law to lift the orthogonal LB-4
collision kernel into the axis-aligned tilted-electron subset:

1. boost the temperature and E-mode towers into the electron frame,
2. evaluate the orthogonal LB-4 collision operator there,
3. boost the resulting collision tower back to the transport frame.

The ``beta == 0`` path returns the exact LB-4 anchor without any extra
floating-point work.
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from bass.collision.polarization import PolarizationHierarchyState
from bass.collision.thomson_pstf import ThomsonAux, ThomsonPSTFCollisionOperator
from bass.collision._tilted_layer_b_common import apply_axisymmetric_boost_to_tower
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
    """Axis-aligned Layer-B Thomson collision source ``K_{A_ℓ}``.

    The implementation reuses the shipped axisymmetric Challinor 2000
    recurrence on the packed ``m = 0`` slice of the temperature and
    E-mode towers. Off-axis Wigner-d rotation remains deferred to
    FB-5.2; that path raises ``NotImplementedError`` rather than
    silently falling back.

    References
    ----------
    - ``docs/lowell_bianchi/04_thomson_collision_spec.md §8.2``.
    - ``bass/collision/thomson_pstf.py`` (LB-4 orthogonal anchor).
    - ``bass/collision/tilted_visibility.py`` (lowell §11.3 Lorentz
      factor surface).
    - Challinor 2000, arXiv:astro-ph/9911481, eqs. (2.26)–(2.28)
      (linearised frame-change multipole mixing).
    """
    op = ThomsonPSTFCollisionOperator()
    aux = ThomsonAux(
        E_state=polarization_state,
        v_b_real_sph=np.asarray(v_b_real_sph, dtype=np.float64),
        Gamma_T=float(Gamma_T),
    )
    if ell < 0 or ell > temperature_state.L:
        raise ValueError(
            f"ell={ell} outside temperature tower range 0..{temperature_state.L}"
        )
    if ell > polarization_state.L:
        raise ValueError(
            f"ell={ell} exceeds polarization tower L={polarization_state.L}"
        )

    _ = float(eta)
    if tilted_electron is None or tilted_electron.beta == 0.0:
        return op.evaluate(ell, temperature_state, aux)

    boosted_temperature = apply_axisymmetric_boost_to_tower(
        temperature_state,
        beta=tilted_electron.beta,
        v_hat_e=tilted_electron.v_hat_e,
    )
    boosted_polarization = PolarizationHierarchyState(
        E=apply_axisymmetric_boost_to_tower(
            polarization_state.E,
            beta=tilted_electron.beta,
            v_hat_e=tilted_electron.v_hat_e,
        )
    )
    boosted_aux = ThomsonAux(
        E_state=boosted_polarization,
        v_b_real_sph=np.asarray(v_b_real_sph, dtype=np.float64),
        Gamma_T=float(Gamma_T),
    )
    collision_e_frame = op.evaluate_tower(
        boosted_temperature,
        boosted_polarization,
        boosted_aux.v_b_real_sph,
        boosted_aux.Gamma_T,
    )
    collision_transport_frame = apply_axisymmetric_boost_to_tower(
        collision_e_frame,
        beta=-tilted_electron.beta,
        v_hat_e=tilted_electron.v_hat_e,
    )
    return collision_transport_frame.tensors[ell]
