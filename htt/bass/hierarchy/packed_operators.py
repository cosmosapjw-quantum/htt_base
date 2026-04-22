"""Packed PSTF operator helpers for the VER3 hierarchy layout.

This module lowers the dominant linear hierarchy terms onto the packed
``(2ℓ+1,)`` PSTF storage used by Tier B. It preserves the exact
term-level algebra from ``bass.hierarchy.terms`` by constructing
cached operator bases from those reference implementations, then
reusing them as small dense matvecs during runtime.

This follows the VER3 PR-09 direction that hierarchy evolution should
be expressed through operator assembly rather than repeated
high-rank tensor contractions inside the solver loop.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np

from bass.hierarchy.contractions import pstf_pack, pstf_unpack
from bass.hierarchy.terms import (
    T1_expansion,
    T4_accel_divergence,
    T5_accel_gradient,
    T6_vorticity,
    T7_shear_up,
    T8_shear_same,
    T9_shear_down,
)

__all__ = [
    "apply_T1_expansion_packed",
    "apply_T4_accel_divergence_packed",
    "apply_T5_accel_gradient_packed",
    "apply_T6_vorticity_packed",
    "apply_T7_shear_up_packed",
    "apply_T8_shear_same_packed",
    "apply_T9_shear_down_packed",
]


def _rank2_parameter_coefficients(value: np.ndarray) -> np.ndarray:
    arr = np.asarray(value)
    if arr.shape == (5,):
        return arr.astype(np.float64, copy=False)
    if arr.shape != (3, 3):
        raise ValueError(f"rank-2 parameter must have shape (3, 3) or (5,), got {arr.shape}")
    return np.asarray(pstf_pack(arr.astype(np.float64, copy=False)), dtype=np.float64)


@lru_cache(maxsize=None)
def _source_basis(ell: int) -> tuple[np.ndarray, ...]:
    eye = np.eye(2 * ell + 1, dtype=np.float64)
    return tuple(np.asarray(pstf_unpack(eye[i], ell), dtype=np.float64) for i in range(2 * ell + 1))


@lru_cache(maxsize=1)
def _vector_parameter_basis() -> tuple[np.ndarray, ...]:
    eye = np.eye(3, dtype=np.float64)
    return tuple(eye[i].copy() for i in range(3))


@lru_cache(maxsize=1)
def _rank2_parameter_basis() -> tuple[np.ndarray, ...]:
    eye = np.eye(5, dtype=np.float64)
    return tuple(np.asarray(pstf_unpack(eye[i], 2), dtype=np.float64) for i in range(5))


def _build_rank1_basis_ops(
    *,
    source_ell: int,
    output_ell: int,
    term_builder,
) -> np.ndarray:
    ops = np.empty(
        (3, 2 * output_ell + 1, 2 * source_ell + 1),
        dtype=np.float64,
    )
    for p_index, param in enumerate(_vector_parameter_basis()):
        for s_index, source in enumerate(_source_basis(source_ell)):
            ops[p_index, :, s_index] = np.asarray(
                pstf_pack(np.asarray(term_builder(source, param))),
                dtype=np.float64,
            )
    return np.ascontiguousarray(ops)


def _build_rank2_basis_ops(
    *,
    source_ell: int,
    output_ell: int,
    term_builder,
) -> np.ndarray:
    ops = np.empty(
        (5, 2 * output_ell + 1, 2 * source_ell + 1),
        dtype=np.float64,
    )
    for p_index, param in enumerate(_rank2_parameter_basis()):
        for s_index, source in enumerate(_source_basis(source_ell)):
            ops[p_index, :, s_index] = np.asarray(
                pstf_pack(np.asarray(term_builder(source, param))),
                dtype=np.float64,
            )
    return np.ascontiguousarray(ops)


def _apply_parametric_operator(
    basis_ops: np.ndarray,
    source_components: np.ndarray,
    parameter_components: np.ndarray,
) -> np.ndarray:
    source = np.asarray(source_components)
    coeffs = np.asarray(parameter_components)
    if basis_ops.ndim != 3:
        raise ValueError(f"basis_ops must be rank-3, got shape {basis_ops.shape}")
    if source.shape != (basis_ops.shape[2],):
        raise ValueError(
            f"source_components shape {source.shape} does not match operator input size {(basis_ops.shape[2],)}"
        )
    if coeffs.shape != (basis_ops.shape[0],):
        raise ValueError(
            f"parameter_components shape {coeffs.shape} does not match parameter size {(basis_ops.shape[0],)}"
        )
    out_dtype = np.result_type(source.dtype, coeffs.dtype, basis_ops.dtype)
    if not np.any(coeffs):
        return np.zeros(basis_ops.shape[1], dtype=out_dtype)
    source_arr = source.astype(out_dtype, copy=False)
    coeff_arr = coeffs.astype(out_dtype, copy=False)
    projected = np.matmul(basis_ops.astype(out_dtype, copy=False), source_arr)
    return np.matmul(coeff_arr, projected)


@lru_cache(maxsize=None)
def _t1_ricci_basis_ops(ell: int) -> np.ndarray:
    return _build_rank2_basis_ops(
        source_ell=ell,
        output_ell=ell,
        term_builder=lambda source, param: T1_expansion(
            ell,
            source,
            0.0,
            aniso_ricci_tensor=param,
        ),
    )


@lru_cache(maxsize=None)
def _t4_basis_ops(ell: int) -> np.ndarray:
    return _build_rank1_basis_ops(
        source_ell=ell + 1,
        output_ell=ell,
        term_builder=lambda source, param: T4_accel_divergence(ell, source, param),
    )


@lru_cache(maxsize=None)
def _t5_basis_ops(ell: int) -> np.ndarray:
    return _build_rank1_basis_ops(
        source_ell=ell - 1,
        output_ell=ell,
        term_builder=lambda source, param: T5_accel_gradient(ell, source, param),
    )


@lru_cache(maxsize=None)
def _t6_basis_ops(ell: int) -> np.ndarray:
    return _build_rank1_basis_ops(
        source_ell=ell,
        output_ell=ell,
        term_builder=lambda source, param: T6_vorticity(ell, source, param),
    )


@lru_cache(maxsize=None)
def _t7_basis_ops(ell: int) -> np.ndarray:
    return _build_rank2_basis_ops(
        source_ell=ell + 2,
        output_ell=ell,
        term_builder=lambda source, param: T7_shear_up(ell, source, param),
    )


@lru_cache(maxsize=None)
def _t8_basis_ops(ell: int) -> np.ndarray:
    return _build_rank2_basis_ops(
        source_ell=ell,
        output_ell=ell,
        term_builder=lambda source, param: T8_shear_same(ell, source, param),
    )


@lru_cache(maxsize=None)
def _t9_basis_ops(ell: int) -> np.ndarray:
    return _build_rank2_basis_ops(
        source_ell=ell - 2,
        output_ell=ell,
        term_builder=lambda source, param: T9_shear_down(ell, source, param),
    )


def apply_T1_expansion_packed(
    ell: int,
    components: np.ndarray,
    Theta: float,
    *,
    aniso_ricci_tensor: np.ndarray | None = None,
) -> np.ndarray:
    source = np.asarray(components)
    if source.shape != (2 * ell + 1,):
        raise ValueError(f"components shape {source.shape} != {(2 * ell + 1,)}")
    out = np.asarray((4.0 / 3.0) * float(Theta) * source, dtype=np.result_type(source.dtype, np.float64))
    if aniso_ricci_tensor is None:
        return out
    ricci_coeffs = _rank2_parameter_coefficients(aniso_ricci_tensor)
    if not np.any(ricci_coeffs):
        return out
    return out + _apply_parametric_operator(_t1_ricci_basis_ops(ell), source, ricci_coeffs)


def apply_T4_accel_divergence_packed(
    ell: int,
    next_components: np.ndarray,
    accel_vector: np.ndarray,
) -> np.ndarray:
    return _apply_parametric_operator(
        _t4_basis_ops(ell),
        np.asarray(next_components),
        np.asarray(accel_vector, dtype=np.float64),
    )


def apply_T5_accel_gradient_packed(
    ell: int,
    prev_components: np.ndarray,
    accel_vector: np.ndarray,
) -> np.ndarray:
    return _apply_parametric_operator(
        _t5_basis_ops(ell),
        np.asarray(prev_components),
        np.asarray(accel_vector, dtype=np.float64),
    )


def apply_T6_vorticity_packed(
    ell: int,
    components: np.ndarray,
    omega_vector: np.ndarray,
) -> np.ndarray:
    return _apply_parametric_operator(
        _t6_basis_ops(ell),
        np.asarray(components),
        np.asarray(omega_vector, dtype=np.float64),
    )


def apply_T7_shear_up_packed(
    ell: int,
    next_next_components: np.ndarray,
    sigma_tensor: np.ndarray,
) -> np.ndarray:
    sigma_coeffs = _rank2_parameter_coefficients(sigma_tensor)
    return _apply_parametric_operator(_t7_basis_ops(ell), np.asarray(next_next_components), sigma_coeffs)


def apply_T8_shear_same_packed(
    ell: int,
    components: np.ndarray,
    sigma_tensor: np.ndarray,
) -> np.ndarray:
    sigma_coeffs = _rank2_parameter_coefficients(sigma_tensor)
    return _apply_parametric_operator(_t8_basis_ops(ell), np.asarray(components), sigma_coeffs)


def apply_T9_shear_down_packed(
    ell: int,
    prev_prev_components: np.ndarray,
    sigma_tensor: np.ndarray,
) -> np.ndarray:
    sigma_coeffs = _rank2_parameter_coefficients(sigma_tensor)
    return _apply_parametric_operator(_t9_basis_ops(ell), np.asarray(prev_prev_components), sigma_coeffs)
