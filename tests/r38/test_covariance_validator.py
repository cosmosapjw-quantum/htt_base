"""Unit tests for strict covariance validation and whitening utilities.

Phase C of HTT-R38 Observational Convergence.
Tests malformed/non-finite arrays, non-symmetric and non-PD covariances,
and Cholesky whitening accuracy.
"""
from __future__ import annotations

import math
import numpy as np
import pytest

from common.covariance_validator import (
    validate_covariance,
    whiten_vector,
    whiten_matrix,
    quadratic_form,
    CovarianceShapeError,
    CovarianceNonFiniteError,
    CovarianceNotSymmetricError,
    CovarianceNotPositiveDefiniteError,
)

def test_valid_positive_definite_covariance():
    # Construct 4x4 strictly positive-definite matrix
    A = np.array([
        [2.0, 0.5, 0.1, 0.0],
        [0.5, 3.0, 0.2, 0.1],
        [0.1, 0.2, 2.5, 0.3],
        [0.0, 0.1, 0.3, 1.8],
    ])
    C, L, audit = validate_covariance(A, name="test_pd_cov")
    assert audit.is_symmetric
    assert audit.is_positive_definite
    assert audit.cholesky_success
    assert audit.min_eigenvalue > 0
    assert np.allclose(L @ L.T, C, atol=1e-14)


def test_reject_malformed_shape():
    # 1D array
    with pytest.raises(CovarianceShapeError, match="must be a 2D square matrix"):
        validate_covariance(np.array([1.0, 2.0, 3.0]))
    # Non-square 2D array
    with pytest.raises(CovarianceShapeError, match="must be a 2D square matrix"):
        validate_covariance(np.ones((3, 4)))
    # Empty 0x0
    with pytest.raises(CovarianceShapeError, match="cannot be empty"):
        validate_covariance(np.zeros((0, 0)))


def test_reject_non_finite():
    # Matrix with NaN
    A = np.eye(3)
    A[0, 1] = np.nan
    with pytest.raises(CovarianceNonFiniteError, match="contains non-finite entries"):
        validate_covariance(A)

    # Matrix with Inf
    B = np.eye(3)
    B[1, 1] = np.inf
    with pytest.raises(CovarianceNonFiniteError, match="contains non-finite entries"):
        validate_covariance(B)


def test_reject_asymmetric():
    # Asymmetric matrix beyond tolerance
    A = np.eye(3)
    A[0, 1] = 0.5
    A[1, 0] = 0.2
    with pytest.raises(CovarianceNotSymmetricError, match="is not symmetric"):
        validate_covariance(A)


def test_reject_non_positive_definite():
    # Matrix with negative eigenvalue
    A = np.array([
        [1.0, 2.0],
        [2.0, 1.0],
    ])
    with pytest.raises(CovarianceNotPositiveDefiniteError, match="not positive-definite"):
        validate_covariance(A)

    # Singular matrix (determinant zero)
    B = np.array([
        [1.0, 1.0],
        [1.0, 1.0],
    ])
    with pytest.raises(CovarianceNotPositiveDefiniteError, match="not positive-definite"):
        validate_covariance(B)

    # All-zero matrix
    with pytest.raises(CovarianceNotPositiveDefiniteError, match="identically zero"):
        validate_covariance(np.zeros((3, 3)))


def test_whitening_and_quadratic_form():
    np.random.seed(42)
    X = np.random.randn(5, 5)
    C_raw = X @ X.T + 0.1 * np.eye(5)
    C, L, _ = validate_covariance(C_raw)
    
    y = np.array([1.2, -0.5, 2.3, 0.8, -1.1])
    yw = whiten_vector(L, y)
    
    # Check y^T C^{-1} y matches ||yw||^2
    qf = quadratic_form(L, y)
    direct_qf = float(y @ np.linalg.solve(C, y))
    assert math.isclose(qf, direct_qf, rel_tol=1e-12, abs_tol=1e-12)
    assert math.isclose(qf, float(np.sum(yw ** 2)), rel_tol=1e-12)

    # Whiten design matrix
    M = np.random.randn(5, 3)
    Mw = whiten_matrix(L, M)
    direct_inv = np.linalg.solve(L, M)
    assert np.allclose(Mw, direct_inv, atol=1e-14)

