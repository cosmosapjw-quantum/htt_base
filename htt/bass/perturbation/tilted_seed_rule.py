"""FB-5.6 — tilted boost and re-regularisation of the FB-5.3 seed."""
from __future__ import annotations

import numpy as np

from bass.hierarchy.boost_kernel import boost_project_axisymmetric
from bass.hierarchy.pack_unpack import combined_total_size, pack_combined_state
from bass.perturbation.regular_adiabatic_ic import (
    CAMB_REGULAR_ADIABATIC_EXTRA_SIZE,
    infer_regular_adiabatic_seed_L_max,
    slice_regular_adiabatic_extras,
    unpack_camb_regular_adiabatic_seed,
)


__all__ = ["apply_tilted_boost_seed_rule"]


def _m0_slice_from_tower(tower) -> np.ndarray:
    return np.array(
        [tower.tensors[ell].components[ell] for ell in range(tower.L + 1)],
        dtype=np.float64,
    )


def _write_m0_slice_to_tower(tower, coeffs: np.ndarray) -> None:
    for ell in range(tower.L + 1):
        tower.tensors[ell].components[ell] = float(coeffs[ell])


def apply_tilted_boost_seed_rule(
    seed_state: np.ndarray,
    *,
    beta: float,
    v_hat_e: tuple[float, float, float],
) -> np.ndarray:
    """Boost the orthogonal FB-5.3 seed and re-project onto the m=0 slice.

    The seed stores only the axisymmetric ``m = 0`` components at
    startup, so the FB-3.3 on-axis boost kernel is the correct current
    transport primitive. Off-axis directions remain explicitly deferred
    to the FB-5.2 Wigner-d lift via :func:`boost_project_axisymmetric`.
    """
    arr = np.asarray(seed_state, dtype=np.float64)
    if arr.ndim != 1:
        raise ValueError(f"seed_state must be 1-D, got shape {arr.shape}")
    beta_val = float(beta)
    if not np.isfinite(beta_val) or beta_val < 0.0 or beta_val >= 1.0:
        raise ValueError(f"beta must satisfy 0 <= beta < 1, got {beta!r}")
    if beta_val == 0.0:
        return arr.copy()

    L_max = infer_regular_adiabatic_seed_L_max(arr.size)
    unpacked = unpack_camb_regular_adiabatic_seed(arr, L_max=L_max)
    combined = unpacked["combined"]
    extras = np.asarray(unpacked["extras"], dtype=np.float64).copy()

    photon_T = combined.photon_T.copy()
    photon_E = combined.photon_E.copy()

    boosted_T = boost_project_axisymmetric(
        _m0_slice_from_tower(photon_T),
        beta_val,
        v_hat_e,
    )
    boosted_E = boost_project_axisymmetric(
        _m0_slice_from_tower(photon_E.E),
        beta_val,
        v_hat_e,
    )
    _write_m0_slice_to_tower(photon_T, boosted_T)
    _write_m0_slice_to_tower(photon_E.E, boosted_E)

    neutrino = boost_project_axisymmetric(
        np.asarray(combined.neutrino_reduced, dtype=np.float64),
        beta_val,
        v_hat_e,
    )
    extras[0:2] = boost_project_axisymmetric(extras[0:2], beta_val, v_hat_e)
    extras[2:4] = boost_project_axisymmetric(extras[2:4], beta_val, v_hat_e)
    extras[4:6] = boost_project_axisymmetric(extras[4:6], beta_val, v_hat_e)

    prefix = pack_combined_state(
        a=combined.a,
        Sigma_plus=combined.Sigma_plus,
        Sigma_minus=combined.Sigma_minus,
        photon_T=photon_T,
        photon_E=photon_E,
        neutrino_reduced=neutrino,
        L_max=L_max,
    )
    out = np.empty(combined_total_size(L_max) + CAMB_REGULAR_ADIABATIC_EXTRA_SIZE, dtype=np.float64)
    out[: prefix.size] = prefix
    out[slice_regular_adiabatic_extras(L_max)] = extras
    return out
