"""Shared helpers for the FB-4 tilted Thomson Layer-B seed surfaces.

The current repo-level boost SSOT for collision-side moment mixing is
the axisymmetric linearised Challinor 2000 recurrence already shipped
in ``bass.hierarchy.boost_kernel``. The helpers below reuse that law
for the ``m = 0`` packed slot of each PSTF multipole while leaving the
remaining packed components untouched. This keeps the FB-4 seed aligned
with the existing FB-3 boost surface and preserves the exact
``beta == 0`` byte-identity anchor.
"""
from __future__ import annotations

from typing import Iterable, Tuple

import numpy as np

from bass.hierarchy.boost_kernel import is_axis_aligned
from bass.hierarchy.pstf_tensor import PSTFHierarchyState


__all__ = [
    "apply_axisymmetric_boost_to_tower",
    "extract_axisymmetric_slice",
    "replace_axisymmetric_slice",
    "signed_axisymmetric_boost",
]


def _axis_sign(v_hat_e: Tuple[float, float, float]) -> float:
    arr = np.asarray(v_hat_e, dtype=np.float64)
    if arr.shape != (3,):
        raise ValueError(
            f"v_hat_e must have shape (3,), got {arr.shape}"
        )
    idx = int(np.argmax(np.abs(arr)))
    sign = float(np.sign(arr[idx]))
    return 1.0 if sign == 0.0 else sign


def signed_axisymmetric_boost(
    coeffs: Iterable[float],
    beta: float,
    v_hat_e: Tuple[float, float, float],
) -> np.ndarray:
    """Linear Challinor recurrence on the axisymmetric packed slice.

    Unlike ``boost_project_axisymmetric`` this helper accepts a signed
    ``beta`` so callers can apply the inverse boost with ``-beta``.
    The sign of an axis-flipped ``v_hat_e`` is also respected.
    """
    arr = np.asarray(list(coeffs), dtype=np.float64)
    if arr.ndim != 1:
        raise ValueError(
            f"coeffs must be 1-D, got shape {arr.shape}"
        )
    beta_val = float(beta)
    if not np.isfinite(beta_val):
        raise ValueError(f"beta must be finite, got {beta!r}")
    if abs(beta_val) >= 1.0:
        raise ValueError(
            f"beta must satisfy |β| < 1; got beta={beta_val!r}"
        )
    if beta_val == 0.0:
        return arr.copy()
    if not is_axis_aligned(v_hat_e):
        raise NotImplementedError(
            f"off-axis v_hat_e={tuple(v_hat_e)!r} requires the FB-5.2 "
            f"Wigner-d lift; FB-4 seeds only the axis-aligned subset."
        )

    signed_beta = beta_val * _axis_sign(v_hat_e)
    out = arr.copy()
    for ell in range(arr.size):
        delta = 0.0
        if ell - 1 >= 0:
            delta += (ell / (2.0 * ell - 1.0)) * arr[ell - 1]
        if ell + 1 < arr.size:
            delta -= ((ell + 1.0) / (2.0 * ell + 3.0)) * arr[ell + 1]
        out[ell] = arr[ell] + signed_beta * delta
    return out


def extract_axisymmetric_slice(state: PSTFHierarchyState) -> np.ndarray:
    """Return the packed ``m = 0`` slot from every multipole."""
    return np.array(
        [tensor.components[ell] for ell, tensor in enumerate(state.tensors)],
        dtype=np.float64,
    )


def replace_axisymmetric_slice(
    state: PSTFHierarchyState,
    coeffs: Iterable[float],
) -> PSTFHierarchyState:
    """Return a copy of ``state`` with the ``m = 0`` slots replaced."""
    coeff_arr = np.asarray(list(coeffs), dtype=np.float64)
    if coeff_arr.shape != (state.L + 1,):
        raise ValueError(
            f"coeffs shape {coeff_arr.shape} != ({state.L + 1},)"
        )
    out = state.copy()
    for ell, value in enumerate(coeff_arr):
        out.tensors[ell].components[ell] = float(value)
    return out


def apply_axisymmetric_boost_to_tower(
    state: PSTFHierarchyState,
    beta: float,
    v_hat_e: Tuple[float, float, float],
) -> PSTFHierarchyState:
    """Apply the signed axisymmetric recurrence to a full tower."""
    coeffs = extract_axisymmetric_slice(state)
    boosted = signed_axisymmetric_boost(coeffs, beta=beta, v_hat_e=v_hat_e)
    return replace_axisymmetric_slice(state, boosted)
