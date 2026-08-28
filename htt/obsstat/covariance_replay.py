"""Portable numerical validation for sample covariance replay.

Covariance matrices are scientific numeric outputs. Cross-environment BLAS or
NumPy reductions may differ at the last bits even when the stored matrix is a
valid replay of the same rows. This module compares against a deterministic
``math.fsum`` reference with a forward-error bound, while retaining exact
symmetry and positive-semidefinite requirements.
"""

from __future__ import annotations

import math
from typing import Mapping

import numpy as np


class CovarianceReplayError(RuntimeError):
    """Raised when a stored covariance is not numerically the same object."""


def fsum_sample_covariance(rows: object) -> tuple[np.ndarray, np.ndarray]:
    """Return deterministic sample covariance and absolute-product scale."""

    matrix = np.asarray(rows, dtype=np.float64)
    if matrix.ndim != 2:
        raise CovarianceReplayError("sample rows must be two-dimensional")
    n_rows, dimension = matrix.shape
    if n_rows < 2 or dimension < 1:
        raise CovarianceReplayError("sample rows have an invalid shape")
    if not np.all(np.isfinite(matrix)):
        raise CovarianceReplayError("sample rows must be finite")

    means = np.asarray(
        [
            math.fsum(float(value) for value in matrix[:, column]) / n_rows
            for column in range(dimension)
        ],
        dtype=np.float64,
    )
    covariance = np.empty((dimension, dimension), dtype=np.float64)
    scale = np.empty_like(covariance)
    denominator = n_rows - 1
    for left in range(dimension):
        for right in range(left, dimension):
            products = [
                (float(row[left]) - float(means[left]))
                * (float(row[right]) - float(means[right]))
                for row in matrix
            ]
            value = math.fsum(products) / denominator
            absolute = math.fsum(abs(product) for product in products) / denominator
            covariance[left, right] = covariance[right, left] = value
            scale[left, right] = scale[right, left] = absolute
    return covariance, scale


def validate_sample_covariance_replay(
    *,
    stored_covariance: object,
    rows: object,
    forward_error_multiplier: float = 32.0,
) -> dict[str, object]:
    """Validate a stored covariance against a deterministic numeric oracle."""

    stored = np.asarray(stored_covariance, dtype=np.float64)
    matrix = np.asarray(rows, dtype=np.float64)
    if matrix.ndim != 2:
        raise CovarianceReplayError("sample rows must be two-dimensional")
    dimension = matrix.shape[1]
    if stored.shape != (dimension, dimension):
        raise CovarianceReplayError("stored covariance shape drifted")
    if not np.all(np.isfinite(stored)):
        raise CovarianceReplayError("stored covariance must be finite")
    if not np.array_equal(stored, stored.T):
        raise CovarianceReplayError("stored covariance is not exactly symmetric")
    if not math.isfinite(forward_error_multiplier) or forward_error_multiplier <= 0:
        raise CovarianceReplayError("forward-error multiplier must be positive")

    reference, absolute_product_scale = fsum_sample_covariance(matrix)
    epsilon = np.finfo(np.float64).eps
    reduction_length = matrix.shape[0]
    gamma_n = (reduction_length * epsilon) / (
        1.0 - reduction_length * epsilon
    )
    lower_scale = np.maximum(
        absolute_product_scale,
        np.finfo(np.float64).tiny,
    )
    bound = forward_error_multiplier * gamma_n * lower_scale
    delta = np.abs(stored - reference)
    ratio = delta / bound
    if not np.all(delta <= bound):
        raise CovarianceReplayError(
            "stored covariance exceeds the deterministic forward-error bound"
        )

    eigenvalues = np.linalg.eigvalsh(stored)
    spectral_scale = max(1.0, float(np.max(np.abs(eigenvalues))))
    psd_tolerance = 64.0 * epsilon * spectral_scale
    minimum_eigenvalue = float(eigenvalues.min())
    if minimum_eigenvalue < -psd_tolerance:
        raise CovarianceReplayError("stored covariance is not positive semidefinite")

    rank_tolerance = max(stored.shape) * epsilon * max(
        1.0,
        float(np.max(np.abs(eigenvalues))),
    )
    rank = int(np.count_nonzero(eigenvalues > rank_tolerance))
    return {
        "state": "NUMERICALLY_EQUIVALENT",
        "comparison_basis": "DETERMINISTIC_MATH_FSUM_FORWARD_ERROR",
        "row_count": int(matrix.shape[0]),
        "dimension": int(dimension),
        "symmetric": True,
        "positive_semidefinite": True,
        "minimum_eigenvalue": minimum_eigenvalue,
        "psd_tolerance": float(psd_tolerance),
        "numerical_rank": rank,
        "rank_tolerance": float(rank_tolerance),
        "gamma_n": float(gamma_n),
        "forward_error_multiplier": float(forward_error_multiplier),
        "max_absolute_delta": float(delta.max()),
        "max_forward_error_bound": float(bound.max()),
        "max_forward_error_ratio": float(ratio.max()),
    }
