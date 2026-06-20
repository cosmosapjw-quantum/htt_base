"""Small covariance helpers for rest-frame diagnostic tests."""

from __future__ import annotations

import numpy as np

__all__ = ["covariance_inverse_sqrt", "validate_positive_definite_covariance"]


def validate_positive_definite_covariance(value: object, *, rows: int) -> np.ndarray:
    covariance = np.asarray(value, dtype=float)
    if covariance.shape != (rows, rows):
        raise ValueError("covariance must be square with response row count")
    if not np.all(np.isfinite(covariance)):
        raise ValueError("covariance must contain finite values")
    covariance = (covariance + covariance.T) / 2.0
    evals = np.linalg.eigvalsh(covariance)
    scale = max(float(np.max(np.abs(evals))) if evals.size else 0.0, 1.0)
    if float(np.min(evals)) <= 1.0e-12 * scale:
        raise ValueError("covariance must be positive definite")
    return covariance


def covariance_inverse_sqrt(covariance: np.ndarray) -> np.ndarray:
    evals, evecs = np.linalg.eigh(covariance)
    return (evecs / np.sqrt(evals)) @ evecs.T
