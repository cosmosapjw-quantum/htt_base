"""Canonical STF rank-2 algebra for an orthonormal spatial triad.

The coefficient convention is intentionally explicit.  No legacy coefficient
vector is silently reinterpreted.  Use :func:`basis_change_matrix` when a
legacy design uses a different STF basis.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import numpy as np

SQRT2 = np.sqrt(2.0)
SQRT6 = np.sqrt(6.0)
CANONICAL_STF_BASIS = np.asarray([
    [[1/SQRT2, 0, 0], [0, -1/SQRT2, 0], [0, 0, 0]],
    [[1/SQRT6, 0, 0], [0, 1/SQRT6, 0], [0, 0, -2/SQRT6]],
    [[0, 1/SQRT2, 0], [1/SQRT2, 0, 0], [0, 0, 0]],
    [[0, 0, 1/SQRT2], [0, 0, 0], [1/SQRT2, 0, 0]],
    [[0, 0, 0], [0, 0, 1/SQRT2], [0, 1/SQRT2, 0]],
], dtype=float)


def stf_project(tensor: np.ndarray) -> np.ndarray:
    """Return the Euclidean symmetric trace-free projection of a 3x3 tensor."""
    t = np.asarray(tensor, dtype=float)
    if t.shape != (3, 3):
        raise ValueError(f"expected (3,3), got {t.shape}")
    s = 0.5 * (t + t.T)
    return s - np.eye(3) * np.trace(s) / 3.0


def validate_basis(basis: np.ndarray = CANONICAL_STF_BASIS, atol: float = 1e-12) -> None:
    b = np.asarray(basis, dtype=float)
    if b.shape != (5, 3, 3):
        raise ValueError(f"expected basis shape (5,3,3), got {b.shape}")
    gram = np.einsum('aij,bij->ab', b, b)
    if not np.allclose(gram, np.eye(5), atol=atol, rtol=0):
        raise ValueError("STF basis is not Frobenius-orthonormal")
    if not np.allclose(b, np.swapaxes(b, 1, 2), atol=atol, rtol=0):
        raise ValueError("basis contains a non-symmetric tensor")
    if not np.allclose(np.trace(b, axis1=1, axis2=2), 0.0, atol=atol, rtol=0):
        raise ValueError("basis contains a non-trace-free tensor")


def coeffs_to_stf(coefficients: np.ndarray, basis: np.ndarray = CANONICAL_STF_BASIS) -> np.ndarray:
    c = np.asarray(coefficients, dtype=float)
    if c.shape[-1] != 5:
        raise ValueError("the final coefficient axis must have length 5")
    return np.einsum('...a,aij->...ij', c, np.asarray(basis, dtype=float))


def stf_to_coeffs(tensor: np.ndarray, basis: np.ndarray = CANONICAL_STF_BASIS) -> np.ndarray:
    t = np.asarray(tensor, dtype=float)
    if t.shape[-2:] != (3, 3):
        raise ValueError("the final tensor axes must be (3,3)")
    return np.einsum('...ij,aij->...a', stf_project(t), np.asarray(basis, dtype=float))


def basis_change_matrix(source_basis: np.ndarray,
                        target_basis: np.ndarray = CANONICAL_STF_BASIS) -> np.ndarray:
    """Map coefficients in ``source_basis`` to coefficients in ``target_basis``.

    Both bases may be non-orthonormal but must independently span the five-
    dimensional STF subspace.  The returned matrix ``M`` obeys
    ``c_target = M @ c_source``.
    """
    s = np.asarray(source_basis, dtype=float)
    t = np.asarray(target_basis, dtype=float)
    if s.shape != (5, 3, 3) or t.shape != (5, 3, 3):
        raise ValueError("both bases must have shape (5,3,3)")
    sf = s.reshape(5, 9).T
    tf = t.reshape(5, 9).T
    if np.linalg.matrix_rank(sf) != 5 or np.linalg.matrix_rank(tf) != 5:
        raise ValueError("basis does not span the STF subspace")
    return np.linalg.pinv(tf) @ sf


def directional_hubble_design(directions: np.ndarray) -> np.ndarray:
    """Design for ``H(n)=Theta/3-A_i n^i+sigma_ij n^i n^j``.

    Column order is ``Theta, A_x, A_y, A_z, sigma_1..sigma_5`` in the canonical
    STF basis.  Input directions are normalized and interpreted as
    observer-to-source directions in an orthonormal spatial triad.
    """
    n = np.asarray(directions, dtype=float)
    if n.ndim != 2 or n.shape[1] != 3:
        raise ValueError("directions must have shape (N,3)")
    norms = np.linalg.norm(n, axis=1)
    if np.any(norms <= 0):
        raise ValueError("zero direction is not allowed")
    n = n / norms[:, None]
    q = np.einsum('ni,aij,nj->na', n, CANONICAL_STF_BASIS, n)
    return np.column_stack([np.full(len(n), 1.0/3.0), -n, q])


validate_basis()
