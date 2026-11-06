"""Unit tests for nuisance-projected SVD and rank stability analysis.

Phase C of HTT-R38 Observational Convergence.
Tests QR projection, multi-threshold singular spectrum, null space extraction,
and exact orthogonal likelihood decomposition identities.
"""
from __future__ import annotations

import math
import numpy as np
import pytest

from common.nuisance_projection import (
    analyze_nuisance_projected_rank,
    IdentifiabilityError,
    ProjectedSVDResult,
)

def test_full_rank_projection_and_orthogonal_identity():
    np.random.seed(123)
    n = 100
    p = 4   # 4 signal channels
    k = 2   # 2 nuisance modes (e.g. constant + slope)
    
    # Generate design matrices
    S = np.random.randn(n, p)
    N = np.random.randn(n, k)
    
    # True parameters
    true_beta = np.array([2.5, -1.2, 0.8, 3.1])
    true_alpha = np.array([10.0, -5.0])
    
    # Non-trivial covariance
    X = np.random.randn(n, n) * 0.1
    C = X @ X.T + np.eye(n) * 0.5
    
    # Generate clean + noise data
    L = np.linalg.cholesky(C)
    noise = L @ np.random.randn(n)
    y = S @ true_beta + N @ true_alpha + noise
    
    res = analyze_nuisance_projected_rank(
        y=y,
        signal_matrix=S,
        nuisance_matrix=N,
        covariance=C,
        rank_tol=1e-10,
        check_orthogonal_identity=True,
        name="test_full_rank",
    )
    
    assert res.is_full_rank
    assert res.effective_rank == p
    assert res.null_space.shape == (0, p)
    assert res.is_orthogonal_identity_verified
    assert res.orthogonal_identity_residual < 1e-7 * max(1.0, res.chi2_null)
    
    # Recovered beta should be within 3-sigma of true beta
    stderr = np.sqrt(np.diag(res.parameter_covariance))
    diff = np.abs(res.coefficients - true_beta)
    assert np.all(diff < 3.5 * stderr)


def test_deficient_rank_and_null_space_extraction():
    np.random.seed(456)
    n = 50
    # Create collinear signal columns: column 2 = 2 * column 0 + column 1
    s0 = np.random.randn(n)
    s1 = np.random.randn(n)
    s2 = 2.0 * s0 + s1  # Collinear!
    S = np.column_stack((s0, s1, s2))
    
    N = np.ones((n, 1)) # Nuisance monopole
    y = s0 + 0.5 * np.random.randn(n)
    C = np.eye(n)
    
    res = analyze_nuisance_projected_rank(
        y=y,
        signal_matrix=S,
        nuisance_matrix=N,
        covariance=C,
        rank_tol=1e-8,
        check_orthogonal_identity=False,
        name="test_collinear",
    )
    
    assert not res.is_full_rank
    assert res.effective_rank == 2 # 2 independent columns out of 3
    assert res.status == "RANK_HOLD_DEFICIENT"
    assert res.null_space.shape[0] == 1 # 1 null direction
    
    # Verify that S_projected @ null_vector == 0
    # Compute projected S:
    Nw = N
    Qn, _ = np.linalg.qr(Nw, mode="reduced")
    Sp = S - Qn @ (Qn.T @ S)
    null_v = res.null_space[0]
    proj_null = Sp @ null_v
    assert np.allclose(proj_null, np.zeros(n), atol=1e-10)


def test_reject_singular_nuisance():
    n = 30
    S = np.random.randn(n, 2)
    # Singular nuisance (duplicate column)
    n0 = np.random.randn(n)
    N = np.column_stack((n0, n0))
    y = np.random.randn(n)
    C = np.eye(n)
    
    with pytest.raises(IdentifiabilityError, match="nuisance matrix is rank-deficient"):
        analyze_nuisance_projected_rank(y, S, N, C)


def test_prior_cannot_inflate_rank():
    # The rank audit relies purely on data and covariance singular values,
    # ensuring no artificial Bayesian prior can inflate the data rank!
    n = 40
    s0 = np.random.randn(n)
    S = np.column_stack((s0, s0)) # Identical columns
    y = np.random.randn(n)
    C = np.eye(n)
    
    res = analyze_nuisance_projected_rank(y, S, None, C)
    assert res.effective_rank == 1 # Strictly 1, not 2
    assert not res.is_full_rank
