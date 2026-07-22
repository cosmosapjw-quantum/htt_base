from __future__ import annotations

from functools import lru_cache

import numpy as np
from scipy.linalg import expm


@lru_cache(maxsize=None)
def angular_momentum_matrices(ell: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if ell < 1:
        raise ValueError("ell must be >= 1")
    m = np.arange(-ell, ell + 1, dtype=float)
    n = 2 * ell + 1
    jp = np.zeros((n, n), dtype=np.complex128)
    for i, mi in enumerate(m[:-1]):
        jp[i + 1, i] = np.sqrt(ell * (ell + 1) - mi * (mi + 1))
    jm = jp.T.conj()
    jx = (jp + jm) / 2.0
    jy = (jp - jm) / (2.0j)
    jz = np.diag(m).astype(np.complex128)
    return jx, jy, jz


def random_real_alm(ell: int, rng: np.random.Generator, variance: float = 1.0) -> np.ndarray:
    """Draw a full m=-ell..ell coefficient vector satisfying map reality."""
    if variance < 0:
        raise ValueError("variance must be non-negative")
    a = np.zeros(2 * ell + 1, dtype=np.complex128)
    a[ell] = rng.normal(scale=np.sqrt(variance))
    for m in range(1, ell + 1):
        z = (rng.normal() + 1j * rng.normal()) * np.sqrt(variance / 2.0)
        a[ell + m] = z
        a[ell - m] = ((-1) ** m) * np.conj(z)
    return a


def check_reality(alm: np.ndarray, ell: int, atol: float = 1e-10) -> bool:
    a = np.asarray(alm)
    if a.shape != (2 * ell + 1,):
        return False
    if abs(a[ell].imag) > atol:
        return False
    for m in range(1, ell + 1):
        if not np.allclose(a[ell - m], ((-1) ** m) * np.conj(a[ell + m]), atol=atol):
            return False
    return True


def rotation_matrix_alm_zyz(ell: int, alpha: float, beta: float, gamma: float) -> np.ndarray:
    """Active ZYZ rotation in the spin-ell representation."""
    _, jy, jz = angular_momentum_matrices(ell)
    return expm(-1j * alpha * jz) @ expm(-1j * beta * jy) @ expm(-1j * gamma * jz)


def rotate_alm_zyz(
    alm: np.ndarray, ell: int, alpha: float, beta: float, gamma: float
) -> np.ndarray:
    a = np.asarray(alm, dtype=np.complex128)
    if a.shape != (2 * ell + 1,):
        raise ValueError("alm has incompatible shape")
    return rotation_matrix_alm_zyz(ell, alpha, beta, gamma) @ a


def axisymmetric_alm(ell: int, axis: np.ndarray, amplitude: float = 1.0) -> np.ndarray:
    """Return the rotated m=0 mode whose symmetry axis is ``axis``."""
    n = np.asarray(axis, dtype=float)
    if n.shape != (3,) or not np.isfinite(n).all() or np.linalg.norm(n) == 0:
        raise ValueError("axis must be a finite non-zero 3-vector")
    n = n / np.linalg.norm(n)
    theta = float(np.arccos(np.clip(n[2], -1.0, 1.0)))
    phi = float(np.arctan2(n[1], n[0]))
    a = np.zeros(2 * ell + 1, dtype=np.complex128)
    a[ell] = float(amplitude)
    return rotate_alm_zyz(a, ell, phi, theta, 0.0)


def correlated_real_alms(
    ell: int,
    covariance: np.ndarray,
    rng: np.random.Generator,
    jitter: float = 1e-12,
) -> np.ndarray:
    """Draw correlated real-sky alm vectors over a shell index.

    Returns an array of shape ``(n_shell, 2*ell+1)``.  Each shell individually
    satisfies the real-map coefficient condition, while the same m modes are
    correlated across shells according to ``covariance``.
    """
    cov = np.asarray(covariance, dtype=float)
    if cov.ndim != 2 or cov.shape[0] != cov.shape[1]:
        raise ValueError("covariance must be square")
    if not np.allclose(cov, cov.T, atol=1e-10):
        raise ValueError("covariance must be symmetric")
    eig = np.linalg.eigvalsh(cov)
    if eig.min() < -1e-10:
        raise ValueError("covariance must be positive semidefinite")
    cov = cov + max(jitter, -eig.min() + jitter) * np.eye(cov.shape[0])
    n_shell = cov.shape[0]
    out = np.zeros((n_shell, 2 * ell + 1), dtype=np.complex128)
    out[:, ell] = rng.multivariate_normal(np.zeros(n_shell), cov)
    for m in range(1, ell + 1):
        re = rng.multivariate_normal(np.zeros(n_shell), cov / 2.0)
        im = rng.multivariate_normal(np.zeros(n_shell), cov / 2.0)
        z = re + 1j * im
        out[:, ell + m] = z
        out[:, ell - m] = ((-1) ** m) * np.conj(z)
    return out
