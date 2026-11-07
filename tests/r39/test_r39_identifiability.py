"""Unit tests for R39 identifiability, SVD, and nuisance projection."""
from __future__ import annotations

import numpy as np
import pytest

from common.r39_identifiability import (
    PARAM_NAMES_17,
    IdentifiabilitySpectrum,
    compute_numerical_jacobian,
    analyze_r39_identifiability,
)


def test_compute_numerical_jacobian():
    # Linear function: f(theta) = A @ theta
    A = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    theta_0 = np.array([0.5, -0.2, 0.8])
    J = compute_numerical_jacobian(lambda th: A @ th, theta_0)
    np.testing.assert_allclose(J, A, rtol=1e-5, atol=1e-8)


def test_analyze_r39_identifiability_synthetic():
    np.random.seed(42)
    n_data = 30
    n_params = 17

    # Create a rank-14 Jacobian (3 null directions)
    U, _ = np.linalg.qr(np.random.randn(n_data, n_data))
    V, _ = np.linalg.qr(np.random.randn(n_params, n_params))
    # 14 non-zero singular values, 3 zero
    s = np.zeros(n_params)
    s[:14] = np.logspace(0, -3, 14)
    # J = U @ diag(s) @ V.T
    J = U[:, :n_params] @ np.diag(s) @ V.T

    cov = np.eye(n_data) * 0.01

    spectrum = analyze_r39_identifiability(J, cov, rank_tol=1e-4)

    assert spectrum.effective_rank == 14
    assert spectrum.null_space_dimension == 3
    assert len(spectrum.singular_values) == n_params
    assert spectrum.null_vectors.shape == (17, 3)
    assert spectrum.identifiable_basis.shape == (17, 14)
    assert np.isfinite(spectrum.condition_number)
    assert spectrum.fisher_matrix.shape == (17, 17)


def test_nuisance_projection():
    np.random.seed(42)
    n_data = 25
    n_params = 17

    J = np.random.randn(n_data, n_params)
    cov = np.eye(n_data)

    # Nuisance vector that overlaps with column 0 of J
    nuisance = np.zeros((n_data, 1))
    nuisance[:, 0] = J[:, 0]

    spectrum = analyze_r39_identifiability(J, cov, nuisance_matrix=nuisance, rank_tol=1e-4)
    # Since column 0 is projected out, effective rank is reduced by 1
    # Check that column 0 of J has zero projection on the effective Jacobian
    assert spectrum.null_space_dimension >= 1
