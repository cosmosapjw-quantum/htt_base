"""Finite-sample Schur information of an *apparent* angular STF2 CF4 signal.

Within an explicitly fixed linear Gaussian working law y = B gamma + N eta + e
with diagonal positive covariance D, this module computes the exact profile
information of five STF2 coefficients, with unrestricted nuisance coefficients.
No cosmological Bianchi shear, real survey likelihood, or significance is inferred.
"""
from __future__ import annotations

import numpy as np
from scipy.linalg import cho_factor, cho_solve, eigh, solve_triangular


class SchurInformationError(ValueError):
    """Working-model rank, domain, or numerical identification failure."""


def profile_stf_information(
    design: np.ndarray,
    residual_mag: np.ndarray,
    error_mag: np.ndarray,
    signal_slice: slice,
    *,
    relative_rank_tolerance: float = 1e-10,
) -> dict:
    """Return nuisance-profiled five-STF coefficients and generalized information.

    Let A = diag(1/error_mag) B, Z = diag(1/error_mag) N.
    For Q an orthonormal basis for range(Z), F = (A-QQ^T A)^T (A-QQ^T A)
    and gamma_hat = F^{-1}(A-QQ^T A)^T (I-QQ^T)y_w.
    The eigenvalues of (F, A^T A) are relative information fractions in [0,1],
    *not* astronomical confidence/probability calibration. Operates in O(n p^2)
    memory O(n p), never forming an n-by-n projector or covariance.
    """
    X = np.asarray(design, dtype=np.float64)
    y = np.asarray(residual_mag, dtype=np.float64)
    std = np.asarray(error_mag, dtype=np.float64)
    if (
        X.ndim != 2 or y.shape != (X.shape[0],) or std.shape != y.shape
        or X.shape[0] <= X.shape[1]
        or not np.isfinite(X).all() or not np.isfinite(y).all()
        or not np.isfinite(std).all() or np.any(std <= 0)
    ):
        raise SchurInformationError("finite nondegenerate design, residual and positive errors expected")
    if (
        not isinstance(signal_slice, slice) or signal_slice.step not in (None, 1)
        or signal_slice.start is None or signal_slice.stop is None
        or signal_slice.stop - signal_slice.start != 5
        or signal_slice.start < 0 or signal_slice.stop > X.shape[1]
    ):
        raise SchurInformationError("exactly five contiguous signal columns required")
    if not 0 < relative_rank_tolerance < 1:
        raise SchurInformationError("relative_rank_tolerance must belong to (0,1)")

    signal_idx = np.arange(signal_slice.start, signal_slice.stop)
    nuisance_idx = np.concatenate((
        np.arange(signal_slice.start), np.arange(signal_slice.stop, X.shape[1])
    ))
    if not len(nuisance_idx):
        raise SchurInformationError("this method requires explicit nuisance columns")
    B = X[:, signal_idx] / std[:, None]
    N = X[:, nuisance_idx] / std[:, None]
    yw = y / std
    # Normalize columns prior to QR to handle mixed dimensionless and km/s units.
    scales = np.linalg.norm(N, axis=0)
    if np.any(scales <= 0) or not np.isfinite(scales).all():
        raise SchurInformationError("zero or nonfinite nuisance direction")
    Q, R = np.linalg.qr(N / scales, mode="reduced")
    nuisance_s = np.linalg.svd(R, compute_uv=False)
    nuisance_ratio = float(nuisance_s[-1] / nuisance_s[0])
    if nuisance_ratio <= relative_rank_tolerance:
        raise SchurInformationError("nuisance full-column rank lost")

    projected_B = B - Q @ (Q.T @ B)
    projected_y = yw - Q @ (Q.T @ yw)
    F = projected_B.T @ projected_B
    F0 = B.T @ B
    F = (F + F.T) / 2
    F0 = (F0 + F0.T) / 2

    signal_s = np.linalg.svd(projected_B, compute_uv=False)
    signal_ratio = float(signal_s[-1] / signal_s[0])
    if signal_ratio <= relative_rank_tolerance:
        raise SchurInformationError("nuisance-profiled five-STF response loses rank")
    try:
        fractions = eigh(F, F0, eigvals_only=True, check_finite=False)
        factor = cho_factor(F, lower=True, check_finite=False)
        gamma = cho_solve(factor, projected_B.T @ projected_y, check_finite=False)
        gamma_cov = cho_solve(factor, np.eye(5), check_finite=False)
    except (np.linalg.LinAlgError, ValueError) as exc:
        raise SchurInformationError("Schur Fisher not positive definite") from exc
    if np.min(fractions) < -1e-9 or np.max(fractions) > 1 + 1e-9:
        raise SchurInformationError("projected information exceeds unprofiled Fisher")
    if not np.isfinite(gamma).all() or not np.isfinite(gamma_cov).all():
        raise SchurInformationError("nonfinite conditional GLS solution")

    # Exact unrestricted-nuisance coefficients for comparison with full WLS.
    eta_scaled = solve_triangular(R, Q.T @ (yw - B @ gamma), lower=False)
    eta = eta_scaled / scales
    joint = np.empty(X.shape[1], dtype=np.float64)
    joint[signal_idx] = gamma
    joint[nuisance_idx] = eta
    cov = (gamma_cov + gamma_cov.T) / 2
    r = projected_y - projected_B @ gamma
    ldF = np.linalg.slogdet(F)
    ldF0 = np.linalg.slogdet(F0)
    if ldF[0] <= 0 or ldF0[0] <= 0:
        raise SchurInformationError("information ellipsoid lacks positive determinant")
    return {
        "beta_signal": gamma,
        "beta_nuisance": eta,
        "beta_full": joint,
        "signal_cov": cov,
        "fisher_profiled": F,
        "fisher_before_nuisance": F0,
        "relative_information_eigenvalues": fractions,
        "relative_information_trace": float(np.trace(F) / np.trace(F0)),
        "uncertainty_hypervolume_inflation_vs_fixed_nuisance": float(
            np.exp(0.5 * (ldF0[1] - ldF[1]))
        ),
        "projected_response_singular_values": signal_s,
        "projected_signal_condition": float(signal_s[0] / signal_s[-1]),
        "nuisance_condition_normalized": float(1 / nuisance_ratio),
        "signal_rank": 5,
        "nuisance_rank": int(len(nuisance_idx)),
        "n_data": len(y),
        "chi2_profiled": float(r @ r),
        "dof": int(len(y) - X.shape[1]),
        "normal_equation_residual": float(np.linalg.norm(projected_B.T @ r)),
        "assumption": "fixed diagonal Gaussian errors; unrestricted nuisance; no survey/cosmic covariance",
    }


def projected_precision_with_general_covariance(
    covariance: np.ndarray, nuisance: np.ndarray
) -> np.ndarray:
    """Dense reference, only for *small* tests of covariance-nuisance subspaces.

    C^{-1} - C^{-1}N(N^TC^{-1}N)^{-1}N^TC^{-1}; never on CF4-sized inputs.
    """
    C = np.asarray(covariance, float)
    N = np.asarray(nuisance, float)
    if C.ndim != 2 or C.shape[0] != C.shape[1] or N.ndim != 2 or N.shape[0] != len(C):
        raise SchurInformationError("square covariance and compatible nuisance expected")
    try:
        f = cho_factor(C, lower=True, check_finite=True)
        cinvn = cho_solve(f, N)
        cinv = cho_solve(f, np.eye(len(C)))
        m = cho_factor(N.T @ cinvn, lower=True)
        projected = cinv - cinvn @ cho_solve(m, cinvn.T)
    except (np.linalg.LinAlgError, ValueError) as exc:
        raise SchurInformationError("covariance or nuisance Fisher is not SPD") from exc
    return (projected + projected.T) / 2
