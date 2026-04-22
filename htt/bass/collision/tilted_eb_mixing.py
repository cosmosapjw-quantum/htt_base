"""FB-4.2 — tilted E/B collision-side mixing surface.

The axis-aligned seed uses the same packed ``m = 0`` Challinor
recurrence as FB-4.1 and supplements it with the leading-order
same-``ell`` E/B rotation term from the Lowell §13.5 boost law. The
orthogonal ``beta == 0`` limit reduces exactly to the existing
E-mode collision source and an identically zero B source.
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from bass.collision._tilted_layer_b_common import (
    apply_axisymmetric_boost_to_tower,
    extract_axisymmetric_slice,
    replace_axisymmetric_slice,
)
from bass.collision.polarization import (
    E_MODE_ELL2_SELF_COEFF,
    PolarizationHierarchyState,
)
from bass.collision.thomson_pstf import EModeThomsonCollisionOperator
from bass.hierarchy.pstf_tensor import PSTFHierarchyState, PSTFTensor
from bass.species.tilted import TiltedSpeciesBackground
from bass.hierarchy.pstf_tensor import zero_hierarchy, zero_pstf


def _mix_axisymmetric_eb_slices(
    e_coeffs: np.ndarray,
    b_coeffs: np.ndarray,
    beta: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Leading-order same-``ell`` E/B rotation on the packed m=0 slice."""
    e_arr = np.asarray(e_coeffs, dtype=np.float64)
    b_arr = np.asarray(b_coeffs, dtype=np.float64)
    if e_arr.shape != b_arr.shape:
        raise ValueError(
            f"E/B slice shape mismatch: {e_arr.shape} vs {b_arr.shape}"
        )
    if beta == 0.0:
        return e_arr.copy(), b_arr.copy()

    out_e = e_arr.copy()
    out_b = b_arr.copy()
    if e_arr.size > 2:
        ell = np.arange(2, e_arr.size, dtype=np.float64)
        coeff = beta * (6.0 / (ell + 1.0))
        out_e[2:] = e_arr[2:] - coeff * b_arr[2:]
        out_b[2:] = b_arr[2:] + coeff * e_arr[2:]
    return out_e, out_b


def _boost_eb_towers(
    e_state: PolarizationHierarchyState,
    b_state: PSTFHierarchyState,
    beta: float,
    v_hat_e: tuple[float, float, float],
) -> tuple[PolarizationHierarchyState, PSTFHierarchyState]:
    boosted_e_base = apply_axisymmetric_boost_to_tower(
        e_state.E, beta=beta, v_hat_e=v_hat_e,
    )
    boosted_b_base = apply_axisymmetric_boost_to_tower(
        b_state, beta=beta, v_hat_e=v_hat_e,
    )
    mixed_e_slice, mixed_b_slice = _mix_axisymmetric_eb_slices(
        extract_axisymmetric_slice(boosted_e_base),
        extract_axisymmetric_slice(boosted_b_base),
        beta=beta,
    )
    return (
        PolarizationHierarchyState(
            E=replace_axisymmetric_slice(boosted_e_base, mixed_e_slice)
        ),
        replace_axisymmetric_slice(boosted_b_base, mixed_b_slice),
    )


def _b_mode_collision_tower(
    b_state: PSTFHierarchyState,
    Gamma_T: float,
) -> PSTFHierarchyState:
    tensors: list[PSTFTensor] = []
    for ell in range(b_state.L + 1):
        if ell < 2:
            tensors.append(zero_pstf(ell))
        elif ell == 2:
            tensors.append(
                PSTFTensor(
                    ell=2,
                    components=Gamma_T * E_MODE_ELL2_SELF_COEFF
                    * b_state.tensors[2].components,
                )
            )
        else:
            tensors.append(
                PSTFTensor(
                    ell=ell,
                    components=-Gamma_T * b_state.tensors[ell].components,
                )
            )
    return PSTFHierarchyState(L=b_state.L, tensors=tensors)


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
    """Axis-aligned tilted E/B collision surface.

    The temperature quadrupole input remains the pinned ``Pi_2_packed``
    scalar-surface from the META audit; only the packed axisymmetric
    slice of the E/B towers is boosted. Off-axis Wigner-d rotation is
    still explicitly deferred.

    References
    ----------
    - ``docs/lowell_bianchi/04_thomson_collision_spec.md §5`` and
      `§8`.
    - ``bass/collision/polarization.py`` (current E-only anchor).
    - ``bass/los/bianchi_propagator.py`` (Type I `ψ' = 0` B-mode floor).
    - Kamionkowski-Kosowsky-Stebbins 1997, arXiv:astro-ph/9611125
      §III (E/B basis contract).
    """
    if ell < 0 or ell > e_state.L:
        raise ValueError(f"ell={ell} outside E tower range 0..{e_state.L}")
    _ = float(eta)
    B_state = zero_hierarchy(e_state.L) if b_state is None else b_state.copy()
    if B_state.L != e_state.L:
        raise ValueError(
            f"b_state.L={B_state.L} must match e_state.L={e_state.L}"
        )

    e_op = EModeThomsonCollisionOperator()
    if tilted_electron is None or tilted_electron.beta == 0.0:
        e_tower = e_op.evaluate_tower(
            e_state,
            np.asarray(Pi_2_packed, dtype=np.float64),
            float(Gamma_T),
        )
        return e_tower.tensors[ell], zero_pstf(ell)

    boosted_e_state, boosted_b_state = _boost_eb_towers(
        e_state,
        B_state,
        beta=tilted_electron.beta,
        v_hat_e=tilted_electron.v_hat_e,
    )
    collision_e_frame_E = e_op.evaluate_tower(
        boosted_e_state,
        np.asarray(Pi_2_packed, dtype=np.float64),
        float(Gamma_T),
    )
    collision_e_frame_B = _b_mode_collision_tower(
        boosted_b_state,
        float(Gamma_T),
    )

    restored_E_state, restored_B_state = _boost_eb_towers(
        collision_e_frame_E,
        collision_e_frame_B,
        beta=-tilted_electron.beta,
        v_hat_e=tilted_electron.v_hat_e,
    )
    return restored_E_state.tensors[ell], restored_B_state.tensors[ell]
