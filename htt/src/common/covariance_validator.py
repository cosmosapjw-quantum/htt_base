"""Strict covariance validation, factorization, and whitening utilities.

Phase C of HTT-R38 Observational Convergence.
Implements fail-closed checks for symmetry, finiteness, positive-definiteness,
condition numbers, Cholesky decomposition, and triangular solve whitening.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
import numpy as np
from scipy.linalg import solve_triangular

class CovarianceValidationError(ValueError):
    """Base exception for covariance validation errors."""
    pass

class CovarianceShapeError(CovarianceValidationError):
    """Raised when covariance is not a 2D square matrix."""
    pass

class CovarianceNonFiniteError(CovarianceValidationError):
    """Raised when covariance contains NaN or Inf."""
    pass

class CovarianceNotSymmetricError(CovarianceValidationError):
    """Raised when covariance violates symmetry beyond tolerance."""
    pass

class CovarianceNotPositiveDefiniteError(CovarianceValidationError):
    """Raised when covariance is singular or not positive-definite."""
    pass


@dataclass(frozen=True)
class CovarianceAudit:
    """Report on covariance integrity and spectral conditioning."""
    dimension: int
    is_symmetric: bool
    max_symmetry_residual: float
    symmetry_tolerance: float
    is_positive_definite: bool
    min_eigenvalue: float
    max_eigenvalue: float
    condition_number: float
    log_determinant: float
    cholesky_success: bool


def validate_covariance(
    cov: np.ndarray,
    name: str = "covariance",
    rtol: float = 1e-12,
    atol: float = 1e-12,
    check_positive_definite: bool = True,
) -> tuple[np.ndarray, np.ndarray, CovarianceAudit]:
    """Validate covariance array and return (validated_cov, cholesky_L, audit).
    
    Parameters
    ----------
    cov : np.ndarray
        Candidate covariance matrix.
    name : str
        Descriptive label for error messages.
    rtol, atol : float
        Relative and absolute tolerances for symmetry check:
        |C - C^T| <= atol + rtol * max(|C|).
    check_positive_definite : bool
        If True, enforces strict positive definiteness via Cholesky decomposition.
        
    Returns
    -------
    C : np.ndarray
        Cleaned, verified float64 covariance matrix.
    L : np.ndarray
        Lower-triangular Cholesky factor (C = L @ L.T).
    audit : CovarianceAudit
        Numerical diagnostic report.
    """
    C = np.asarray(cov, dtype=np.float64)
    if C.ndim != 2 or C.shape[0] != C.shape[1]:
        raise CovarianceShapeError(
            f"{name} must be a 2D square matrix, got shape {C.shape}"
        )
    n = C.shape[0]
    if n == 0:
        raise CovarianceShapeError(f"{name} cannot be empty (0x0)")
        
    if not np.all(np.isfinite(C)):
        num_nan = int(np.sum(np.isnan(C)))
        num_inf = int(np.sum(np.isinf(C)))
        raise CovarianceNonFiniteError(
            f"{name} contains non-finite entries (NaN={num_nan}, Inf={num_inf})"
        )
        
    max_abs = float(np.max(np.abs(C)))
    if max_abs == 0.0:
        raise CovarianceNotPositiveDefiniteError(f"{name} is identically zero")
        
    sym_diff = np.abs(C - C.T)
    max_sym_res = float(np.max(sym_diff))
    # Threshold based on matrix norm and machine precision
    sym_tol = atol + rtol * max_abs * n
    is_symmetric = bool(max_sym_res <= sym_tol)
    if not is_symmetric:
        raise CovarianceNotSymmetricError(
            f"{name} is not symmetric: max |C - C.T| = {max_sym_res:.3e} exceeds tolerance {sym_tol:.3e}"
        )
        
    # Enforce exact floating symmetry
    C_sym = (C + C.T) / 2.0
    
    # Compute eigenvalues for spectral diagnostics
    evals = np.linalg.eigvalsh(C_sym)
    min_eig = float(evals[0])
    max_eig = float(evals[-1])
    cond = float(max_eig / min_eig) if min_eig > 0 else float("inf")
    
    if check_positive_definite:
        if min_eig <= 0.0:
            raise CovarianceNotPositiveDefiniteError(
                f"{name} is not positive-definite: min eigenvalue = {min_eig:.3e} <= 0"
            )
        try:
            L = np.linalg.cholesky(C_sym)
            log_det = float(2.0 * np.sum(np.log(np.diag(L))))
            cholesky_ok = True
        except np.linalg.LinAlgError as e:
            raise CovarianceNotPositiveDefiniteError(
                f"{name} failed Cholesky factorization: {e}"
            ) from e
    else:
        L = np.zeros_like(C_sym)
        log_det = float(np.sum(np.log(evals))) if min_eig > 0 else float("-inf")
        cholesky_ok = False
        
    audit = CovarianceAudit(
        dimension=n,
        is_symmetric=is_symmetric,
        max_symmetry_residual=max_sym_res,
        symmetry_tolerance=sym_tol,
        is_positive_definite=bool(min_eig > 0),
        min_eigenvalue=min_eig,
        max_eigenvalue=max_eig,
        condition_number=cond,
        log_determinant=log_det,
        cholesky_success=cholesky_ok,
    )
    return C_sym, L, audit


def whiten_vector(L: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Compute whitened vector y_w = L^{-1} y via forward substitution.
    
    Parameters
    ----------
    L : np.ndarray
        Lower triangular Cholesky factor of covariance C.
    y : np.ndarray
        1D or 2D data vector.
        
    Returns
    -------
    y_w : np.ndarray
        Whitened vector such that Cov(y_w) = I.
    """
    y_arr = np.asarray(y, dtype=np.float64)
    if not np.all(np.isfinite(y_arr)):
        raise ValueError("Data vector contains non-finite values (NaN or Inf)")
    if y_arr.shape[0] != L.shape[0]:
        raise ValueError(f"Dimension mismatch: L has {L.shape[0]} rows, y has {y_arr.shape[0]}")
    return solve_triangular(L, y_arr, lower=True, check_finite=False)


def whiten_matrix(L: np.ndarray, X: np.ndarray) -> np.ndarray:
    """Compute whitened design matrix X_w = L^{-1} X via forward substitution."""
    X_arr = np.asarray(X, dtype=np.float64)
    if not np.all(np.isfinite(X_arr)):
        raise ValueError("Design matrix contains non-finite values (NaN or Inf)")
    if X_arr.shape[0] != L.shape[0]:
        raise ValueError(f"Dimension mismatch: L has {L.shape[0]} rows, X has {X_arr.shape[0]}")
    return solve_triangular(L, X_arr, lower=True, check_finite=False)


def quadratic_form(L: np.ndarray, residual: np.ndarray) -> float:
    """Compute exact quadratic form r^T C^{-1} r = ||L^{-1} r||^2."""
    r_w = whiten_vector(L, residual)
    return float(np.sum(r_w ** 2))

