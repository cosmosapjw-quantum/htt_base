"""FB-5.2 — full off-axis ``nabla_tilde`` via explicit Euler rotation."""
from __future__ import annotations

from typing import Callable

import numpy as np

from bass.background.bianchi_types import StructureConstants
from bass.hierarchy.nabla_dispatch import HarmonicMode, make_nabla_tilde


__all__ = ["make_full_mode_nabla_tilde_operator"]


def _rotation_matrix_zyz(
    alpha: float,
    beta: float,
    gamma: float,
) -> np.ndarray:
    """Active ZYZ Euler rotation matrix."""
    ca, sa = np.cos(alpha), np.sin(alpha)
    cb, sb = np.cos(beta), np.sin(beta)
    cg, sg = np.cos(gamma), np.sin(gamma)

    Rz_a = np.array(
        [[ca, -sa, 0.0], [sa, ca, 0.0], [0.0, 0.0, 1.0]],
        dtype=np.float64,
    )
    Ry_b = np.array(
        [[cb, 0.0, sb], [0.0, 1.0, 0.0], [-sb, 0.0, cb]],
        dtype=np.float64,
    )
    Rz_g = np.array(
        [[cg, -sg, 0.0], [sg, cg, 0.0], [0.0, 0.0, 1.0]],
        dtype=np.float64,
    )
    return Rz_a @ Ry_b @ Rz_g


def _rotate_spatial_tensor(tensor: np.ndarray, rotation: np.ndarray) -> np.ndarray:
    """Apply the same SO(3) rotation to every spatial index."""
    arr = np.asarray(tensor)
    if arr.ndim == 0:
        return arr.copy()
    out = arr
    for axis in range(arr.ndim):
        out = np.tensordot(rotation, out, axes=([1], [axis]))
        out = np.moveaxis(out, 0, axis)
    return out


def make_full_mode_nabla_tilde_operator(
    structure: StructureConstants,
    mode: HarmonicMode,
    *,
    euler_angles: tuple[float, float, float],
) -> Callable[..., object]:
    """Lift the axis-aligned FB-2 dispatch to an explicitly rotated frame.

    The Euler angles define the active rotation that maps the canonical
    axis-aligned basis used by :func:`make_nabla_tilde` into the physical
    frame of ``mode.k_vec``. Internally we:

    1. Rotate the requested physical ``k`` back into the canonical frame.
    2. Build the already-audited FB-2 operator on that canonical mode.
    3. Rotate input tensors into the canonical frame before applying the
       operator, then rotate the result back to the physical frame.
    """
    if structure.label != mode.type_label:
        raise ValueError(
            f"structure.label={structure.label!r} does not match "
            f"mode.type_label={mode.type_label!r}"
        )
    angles = np.asarray(euler_angles, dtype=np.float64)
    if angles.shape != (3,) or not np.all(np.isfinite(angles)):
        raise ValueError(
            f"euler_angles must be a finite 3-tuple, got {euler_angles!r}"
        )

    rotation = _rotation_matrix_zyz(*map(float, angles))
    rotation_inv = rotation.T
    canonical_k = rotation_inv @ mode.k_vec
    canonical_mode = HarmonicMode(
        type_label=mode.type_label,
        k_vec=canonical_k,
        ell=mode.ell,
    )
    canonical_operator = make_nabla_tilde(structure, canonical_mode)

    def op(tensor: np.ndarray, kind: str = "gradient") -> np.ndarray:
        tensor_canonical = _rotate_spatial_tensor(tensor, rotation_inv)
        out_canonical = canonical_operator(tensor_canonical, kind=kind)
        return _rotate_spatial_tensor(out_canonical, rotation)

    return op
