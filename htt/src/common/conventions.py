"""Invariant-basis tensor helpers frozen by ver3 PR-01.

This module provides the single helper layer required by
``docs/ver3/01_SSOT_FORMALISM_AND_PHYSICS.md`` §2.3 for
gamma-raising/lowering, gamma-trace contractions, and gamma-PSTF projection.

The helpers operate on 3D invariant-basis arrays. Callers must pass the
invariant-basis metric ``gamma_AB`` when it differs from the orthonormal
identity metric.
"""
from __future__ import annotations

import numpy as np

__all__ = [
    "gamma_trace",
    "gamma_norm2_tensor",
    "pstf_gamma",
    "raise_vector",
    "lower_vector",
    "gamma_from_vsq",
]


def _coerce_metric(gamma_ab: np.ndarray | None) -> tuple[np.ndarray, np.ndarray]:
    gamma = np.eye(3, dtype=np.float64) if gamma_ab is None else np.asarray(gamma_ab, dtype=np.float64)
    if gamma.shape != (3, 3):
        raise ValueError(f"gamma_AB must have shape (3,3), got {gamma.shape}")
    if not np.allclose(gamma, gamma.T, atol=1.0e-12):
        raise ValueError("gamma_AB must be symmetric")
    gamma_inv = np.linalg.inv(gamma)
    return gamma, gamma_inv


def raise_vector(v_a: np.ndarray, gamma_ab: np.ndarray | None = None) -> np.ndarray:
    """Raise one invariant-basis index with ``gamma^{AB}``."""

    covector = np.asarray(v_a, dtype=np.float64)
    if covector.shape != (3,):
        raise ValueError(f"v_A must have shape (3,), got {covector.shape}")
    _, gamma_inv = _coerce_metric(gamma_ab)
    return gamma_inv @ covector


def lower_vector(v_a: np.ndarray, gamma_ab: np.ndarray | None = None) -> np.ndarray:
    """Lower one invariant-basis index with ``gamma_AB``."""

    vector = np.asarray(v_a, dtype=np.float64)
    if vector.shape != (3,):
        raise ValueError(f"v^A must have shape (3,), got {vector.shape}")
    gamma, _ = _coerce_metric(gamma_ab)
    return gamma @ vector


def gamma_from_vsq(v_sq: float) -> float:
    """Return the Lorentz factor ``gamma = 1/sqrt(1-v^2)``.

    The ver3 helper layer freezes this as the single SSOT conversion from
    homogeneous global-tilt speed squared to the corresponding boost factor.
    """

    value = float(v_sq)
    if value < 0.0:
        raise ValueError(f"v^2 must be non-negative, got {v_sq!r}")
    if value >= 1.0:
        raise ValueError(f"v^2 must stay below 1, got {v_sq!r}")
    return 1.0 / np.sqrt(1.0 - value)


def gamma_trace(tensor_ab: np.ndarray, gamma_ab: np.ndarray | None = None) -> float:
    """Return ``gamma^{AB} X_AB`` for a covariant rank-2 tensor."""

    tensor = np.asarray(tensor_ab, dtype=np.float64)
    if tensor.shape != (3, 3):
        raise ValueError(f"X_AB must have shape (3,3), got {tensor.shape}")
    _, gamma_inv = _coerce_metric(gamma_ab)
    return float(np.einsum("ab,ab->", gamma_inv, tensor))


def gamma_norm2_tensor(tensor_ab: np.ndarray, gamma_ab: np.ndarray | None = None) -> float:
    """Return ``X_AB X^AB`` for a covariant rank-2 tensor."""

    tensor = np.asarray(tensor_ab, dtype=np.float64)
    if tensor.shape != (3, 3):
        raise ValueError(f"X_AB must have shape (3,3), got {tensor.shape}")
    _, gamma_inv = _coerce_metric(gamma_ab)
    return float(np.einsum("ac,bd,ab,cd->", gamma_inv, gamma_inv, tensor, tensor))


def pstf_gamma(tensor_ab: np.ndarray, gamma_ab: np.ndarray | None = None) -> np.ndarray:
    """Return the symmetric gamma-trace-free projector of ``X_AB``."""

    tensor = np.asarray(tensor_ab, dtype=np.float64)
    if tensor.shape != (3, 3):
        raise ValueError(f"X_AB must have shape (3,3), got {tensor.shape}")
    gamma, _ = _coerce_metric(gamma_ab)
    sym = 0.5 * (tensor + tensor.T)
    return sym - gamma_trace(sym, gamma) * gamma / 3.0
