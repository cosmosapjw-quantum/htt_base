"""Correlated real-sky alm draws for a transparent shell reference DGP.

The caller supplies the complete shell covariance directly.  The returned array
has shape (n_shell, 2 * ell + 1), with column m + ell storing a_lm for
m = -ell, ..., +ell.  This is a numerical reference generator; it is not a
CAMB/CLASS calculation or a physical transfer model.
"""
from __future__ import annotations

import math
import operator

import numpy as np

__all__ = ["draw_correlated_real_shell_alms"]


def draw_correlated_real_shell_alms(
    *,
    ell: int,
    shell_covariance: np.ndarray,
    seed: int,
) -> np.ndarray:
    """Draw seeded shell-correlated coefficients satisfying map reality.

    If C is shell_covariance, every m mode obeys
    E[a_lm(i) conjugate(a_lm(j))] = C[i, j] up to floating-point roundoff
    and removal of eigenmodes at numerical zero.  For m > 0 the real and
    imaginary parts each have covariance C / 2; the negative-m coefficients
    are then fixed by a_l,-m = (-1)^m conjugate(a_lm).

    Positive-semidefinite square roots are formed without adding diagonal
    jitter, so exact rank deficiencies and cross-shell constraints are not
    silently changed.
    """

    ell_i = _validate_ell(ell)
    covariance, factor = _validated_psd_factor(shell_covariance)

    try:
        seed_i = operator.index(seed)
    except TypeError as exc:
        raise ValueError("seed must be a non-negative integer") from exc
    if seed_i < 0:
        raise ValueError("seed must be a non-negative integer")
    rng = np.random.default_rng(seed_i)

    n_shell = covariance.shape[0]
    coefficients = np.zeros(
        (n_shell, 2 * ell_i + 1),
        dtype=np.complex128,
    )
    coefficients[:, ell_i] = factor @ rng.standard_normal(n_shell)

    inverse_sqrt_two = 1.0 / math.sqrt(2.0)
    for m in range(1, ell_i + 1):
        real_part = factor @ rng.standard_normal(n_shell)
        imaginary_part = factor @ rng.standard_normal(n_shell)
        positive_m = (real_part + 1j * imaginary_part) * inverse_sqrt_two
        coefficients[:, ell_i + m] = positive_m
        coefficients[:, ell_i - m] = ((-1) ** m) * np.conj(positive_m)

    return coefficients


def _validate_ell(ell: int) -> int:
    try:
        ell_i = operator.index(ell)
    except TypeError as exc:
        raise ValueError("ell must be an integer >= 1") from exc
    if ell_i < 1:
        raise ValueError("ell must be an integer >= 1")
    return int(ell_i)


def _validated_psd_factor(
    shell_covariance: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    raw_covariance = np.asarray(shell_covariance)
    if np.iscomplexobj(raw_covariance):
        if np.any(raw_covariance.imag != 0.0):
            raise ValueError("shell_covariance must be real")
        raw_covariance = raw_covariance.real
    try:
        covariance = np.asarray(raw_covariance, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("shell_covariance must be a real numeric matrix") from exc
    if (
        covariance.ndim != 2
        or covariance.shape[0] == 0
        or covariance.shape[0] != covariance.shape[1]
    ):
        raise ValueError("shell_covariance must be a non-empty square matrix")
    if not np.isfinite(covariance).all():
        raise ValueError("shell_covariance must contain only finite values")

    n_shell = covariance.shape[0]
    scale = float(np.max(np.abs(covariance)))
    reference_scale = max(scale, float(np.finfo(float).tiny))
    symmetry_tolerance = (
        64.0 * np.finfo(float).eps * n_shell * reference_scale
    )
    asymmetry = float(np.max(np.abs(covariance - covariance.T)))
    if asymmetry > symmetry_tolerance:
        raise ValueError("shell_covariance must be symmetric")

    symmetric_covariance = (covariance + covariance.T) / 2.0
    eigenvalues, eigenvectors = np.linalg.eigh(symmetric_covariance)
    psd_tolerance = (
        128.0 * np.finfo(float).eps * n_shell * reference_scale
    )
    if float(eigenvalues[0]) < -psd_tolerance:
        raise ValueError("shell_covariance must be positive semidefinite")

    # Numerical zero modes remain exact zero modes rather than receiving
    # artificial independent power through a jitter term.
    retained_eigenvalues = np.where(
        eigenvalues > psd_tolerance,
        eigenvalues,
        0.0,
    )
    factor = eigenvectors * np.sqrt(retained_eigenvalues)[np.newaxis, :]
    return symmetric_covariance, factor
