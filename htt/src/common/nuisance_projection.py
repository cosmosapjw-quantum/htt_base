"""Nuisance-projected SVD, rank stability, and identifiability analyzer.

Phase C/F of HTT-R38 Observational Convergence.
Implements QR-based nuisance projection on Cholesky-whitened arrays,
column-scaled SVD, multi-threshold rank stability testing, nullspace extraction,
and verification of orthogonal likelihood decomposition identities.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence
import numpy as np
from scipy.linalg import solve_triangular, qr, svd

from common.covariance_validator import (
    validate_covariance,
    whiten_vector,
    whiten_matrix,
    CovarianceAudit,
)

class IdentifiabilityError(ValueError):
    """Raised when identifiability or rank stability fails."""
    pass


@dataclass(frozen=True)
class ProjectedSVDResult:
    """Diagnostic report on nuisance projection and signal rank."""
    dimension_data: int
    dimension_signal: int
    dimension_nuisance: int
    effective_rank: int
    is_full_rank: bool
    singular_values: tuple[float, ...]
    rank_tolerances: dict[str, int]
    null_space: np.ndarray
    coefficients: np.ndarray
    parameter_covariance: np.ndarray
    nuisance_coefficients: np.ndarray
    chi2_null: float
    chi2_full: float
    delta_chi2: float
    orthogonal_identity_residual: float
    is_orthogonal_identity_verified: bool
    status: str


def analyze_nuisance_projected_rank(
    y: np.ndarray,
    signal_matrix: np.ndarray,
    nuisance_matrix: np.ndarray | None,
    covariance: np.ndarray,
    rank_tol: float = 1e-10,
    check_orthogonal_identity: bool = True,
    name: str = "projected_svd",
) -> ProjectedSVDResult:
    """Perform exact Cholesky-whitened nuisance projection and signal SVD.
    
    Parameters
    ----------
    y : np.ndarray
        Data vector of length N.
    signal_matrix : np.ndarray
        N x P signal design matrix.
    nuisance_matrix : np.ndarray or None
        N x K nuisance design matrix (e.g. monopoles, calibration offsets, frame spin).
    covariance : np.ndarray
        N x N covariance matrix.
    rank_tol : float
        Singular value cutoff relative to maximum singular value.
    check_orthogonal_identity : bool
        If True, verifies |(T_null - T_full) - delta_T| < tolerance.
    name : str
        Diagnostic name.
        
    Returns
    -------
    ProjectedSVDResult
        Structured results including rank, singular values, coefficients, and null space.
    """
    y_arr = np.asarray(y, dtype=np.float64)
    S_arr = np.asarray(signal_matrix, dtype=np.float64)
    if S_arr.ndim == 1:
        S_arr = S_arr[:, None]
        
    N_arr = np.empty((len(y_arr), 0), dtype=np.float64) if nuisance_matrix is None else np.asarray(nuisance_matrix, dtype=np.float64)
    if N_arr.ndim == 1:
        N_arr = N_arr[:, None]
        
    n, p = S_arr.shape
    k = N_arr.shape[1]
    
    if y_arr.shape[0] != n or N_arr.shape[0] != n:
        raise ValueError(f"{name}: dimension mismatch between y ({y_arr.shape[0]}), S ({n}), N ({N_arr.shape[0]})")
        
    # 1. Validate covariance and compute Cholesky factor L
    _, L, cov_audit = validate_covariance(covariance, name=f"{name}_cov", check_positive_definite=True)
    
    # 2. Whiten arrays: y_w = L^{-1} y, S_w = L^{-1} S, N_w = L^{-1} N
    yw = whiten_vector(L, y_arr)
    Sw = whiten_matrix(L, S_arr)
    
    if k > 0:
        Nw = whiten_matrix(L, N_arr)
        # 3. QR factorization of whitened nuisance matrix
        Qn, Rn = np.linalg.qr(Nw, mode="reduced")
        nuisance_rank = int(np.linalg.matrix_rank(Rn))
        if nuisance_rank != k:
            raise IdentifiabilityError(f"{name}: nuisance matrix is rank-deficient ({nuisance_rank} < {k})")
            
        # 4. Project out nuisance: P_N^perp = I - Q_N Q_N^T
        yp = yw - Qn @ (Qn.T @ yw)
        Sp = Sw - Qn @ (Qn.T @ Sw)
    else:
        Qn = np.empty((n, 0), dtype=np.float64)
        Rn = np.empty((0, 0), dtype=np.float64)
        yp = yw.copy()
        Sp = Sw.copy()
        
    # 5. Column-scale signal to prevent artificial ill-conditioning
    scales = np.linalg.norm(Sp, axis=0)
    if np.any(scales <= 0.0) or not np.all(np.isfinite(scales)):
        raise IdentifiabilityError(f"{name}: zero or non-finite signal column after nuisance projection")
        
    Sp_scaled = Sp / scales
    
    # 6. SVD of projected signal
    u, s, vh = svd(Sp_scaled, full_matrices=False)
    s_max = float(s[0]) if len(s) > 0 else 1.0
    
    # Evaluate rank across multiple thresholds
    rank_dict = {
        "tol_1e_12": int(np.sum(s > 1e-12 * s_max)),
        "tol_1e_10": int(np.sum(s > 1e-10 * s_max)),
        "tol_1e_8": int(np.sum(s > 1e-8 * s_max)),
    }
    rank = int(np.sum(s > rank_tol * s_max))
    is_full = bool(rank == p)
    
    # Null-space extraction
    if not is_full:
        null_space = vh[rank:] / scales[None, :]
        null_space = null_space / np.linalg.norm(null_space, axis=1, keepdims=True)
    else:
        null_space = np.empty((0, p), dtype=np.float64)
        
    # 7. Solve for GLS coefficients if full rank, or pseudo-inverse if deficient
    if is_full:
        coeff = (vh.T @ ((u.T @ yp) / s)) / scales
        param_cov = (vh.T @ np.diag(1.0 / (s ** 2)) @ vh) / (scales[:, None] * scales[None, :])
    else:
        # Truncated pseudo-inverse solution on identifiable subspace
        s_inv = np.zeros_like(s)
        s_inv[:rank] = 1.0 / s[:rank]
        coeff = (vh.T @ (s_inv * (u.T @ yp))) / scales
        param_cov = (vh[:rank].T @ np.diag(1.0 / (s[:rank] ** 2)) @ vh[:rank]) / (scales[:, None] * scales[None, :])
        
    # Solve nuisance coefficients
    if k > 0:
        nuisance_coeff = np.linalg.solve(Rn, Qn.T @ (yw - Sw @ coeff))
        residual = yw - Nw @ nuisance_coeff - Sw @ coeff
    else:
        nuisance_coeff = np.empty(0, dtype=np.float64)
        residual = yw - Sw @ coeff
        
    chi2_full = float(np.sum(residual ** 2))
    chi2_null = float(np.sum(yp ** 2))
    delta_chi2 = chi2_null - chi2_full
    
    # Orthogonal projection identity: (yp^T yp) - (r^T r) = (Sp coeff)^T (Sp coeff)
    proj = Sp @ coeff
    delta_proj = float(np.sum(proj ** 2))
    ortho_res = abs(delta_chi2 - delta_proj)
    max_scale = max(1.0, chi2_null)
    ortho_ok = bool(ortho_res < 1e-7 * max_scale)
    
    if check_orthogonal_identity and not ortho_ok and is_full:
        raise IdentifiabilityError(
            f"{name}: orthogonal likelihood decomposition violated: "
            f"|delta_chi2 ({delta_chi2}) - delta_proj ({delta_proj})| = {ortho_res:.3e}"
        )
        
    return ProjectedSVDResult(
        dimension_data=n,
        dimension_signal=p,
        dimension_nuisance=k,
        effective_rank=rank,
        is_full_rank=is_full,
        singular_values=tuple(float(v) for v in s),
        rank_tolerances=rank_dict,
        null_space=null_space,
        coefficients=coeff,
        parameter_covariance=param_cov,
        nuisance_coefficients=nuisance_coeff,
        chi2_null=chi2_null,
        chi2_full=chi2_full,
        delta_chi2=delta_chi2,
        orthogonal_identity_residual=ortho_res,
        is_orthogonal_identity_verified=ortho_ok,
        status="FULL_RANK" if is_full else "RANK_HOLD_DEFICIENT",
    )
