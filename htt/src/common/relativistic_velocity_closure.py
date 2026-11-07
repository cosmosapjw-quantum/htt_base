"""Relativistic Velocity Closure, Wigner Rotation, and Kinematic Quadrupole.

Implements exact special relativistic velocity composition for multi-congruence
observational kinematics:
  beta_RO = (beta_RM + beta_MO_par + gamma_RM^-1 * beta_MO_perp) / (1 + beta_RM . beta_MO)

where:
  - beta_RM: Radiation-to-matter relative drift velocity (3-vector, c=1)
  - beta_MO: Matter-to-observer boost velocity (3-vector, c=1)
  - beta_RO: Exact radiation-to-observer boost velocity (3-vector, c=1)

Also computes:
  - First-order residual: Delta_beta = beta_RO - (beta_RM + beta_MO)
  - Strict subluminal bounds checking (|beta| < 1)
  - Exact Wigner rotation matrix R_W in SO(3) resulting from successive non-collinear boosts
  - Second-order kinematic quadrupole tensor: [beta_RO (x) beta_RO]_STF2
  - Chart projections into Cartesian and Frobenius-orthonormal 5-vector representations.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np

from common.kinematic_response import BetaTruncationError, KinematicsError
from common.relativistic_kinematics import lorentz_boost
from common.stf_metric_bridge import (
    Convention,
    cartesian_to_stf_matrix,
    stf_matrix_to_cartesian,
    stf_matrix_to_orthonormal,
)


@dataclass(frozen=True)
class VelocityClosureResult:
    """Immutable result of exact special relativistic velocity composition."""

    beta_RM: np.ndarray
    """Radiation-matter relative drift velocity (3-vector)."""

    beta_MO: np.ndarray
    """Matter-observer relative boost velocity (3-vector)."""

    beta_RO: np.ndarray
    """Exact composed radiation-observer boost velocity (3-vector)."""

    delta_beta: np.ndarray
    """First-order residual: beta_RO - (beta_RM + beta_MO)."""

    delta_beta_norm: float
    """Euclidean norm of first-order residual |delta_beta|."""

    beta_RO_norm: float
    """Magnitude |beta_RO| of composed velocity."""

    gamma_RO: float
    """Lorentz factor gamma_RO = (1 - |beta_RO|^2)^(-1/2)."""

    is_subluminal: bool
    """True if |beta_RO| < 1.0."""

    closure_status: str
    """Status description (e.g. 'EXACT_RELATIVISTIC_CLOSURE')."""

    wigner_rotation_matrix: np.ndarray
    """3x3 SO(3) Wigner rotation matrix: B(-beta_RO) @ B(beta_RM) @ B(beta_MO)."""

    wigner_angle_rad: float
    """Rotation angle of Wigner rotation in radians."""

    wigner_axis: np.ndarray
    """Unit 3-vector rotation axis (or zeros if angle == 0)."""

    quadrupole_stf2: np.ndarray
    """3x3 symmetric trace-free tensor: [beta_RO (x) beta_RO]_STF2."""

    quadrupole_stf5_cart: np.ndarray
    """Cartesian 5-vector chart of quadrupole: (S_xx, S_yy, S_xy, S_xz, S_yz)."""

    quadrupole_stf5_on: np.ndarray
    """Frobenius-orthonormal 5-vector chart of quadrupole."""

    def __post_init__(self) -> None:
        """Validate shapes and finite values."""
        for name, arr, expected_shape in [
            ("beta_RM", self.beta_RM, (3,)),
            ("beta_MO", self.beta_MO, (3,)),
            ("beta_RO", self.beta_RO, (3,)),
            ("delta_beta", self.delta_beta, (3,)),
            ("wigner_rotation_matrix", self.wigner_rotation_matrix, (3, 3)),
            ("wigner_axis", self.wigner_axis, (3,)),
            ("quadrupole_stf2", self.quadrupole_stf2, (3, 3)),
            ("quadrupole_stf5_cart", self.quadrupole_stf5_cart, (5,)),
            ("quadrupole_stf5_on", self.quadrupole_stf5_on, (5,)),
        ]:
            if not isinstance(arr, np.ndarray) or arr.shape != expected_shape:
                raise KinematicsError(f"{name} must be ndarray of shape {expected_shape}")
            if not np.all(np.isfinite(arr)):
                raise KinematicsError(f"{name} contains non-finite values")


def kinematic_quadrupole_stf2(beta: np.ndarray | Sequence[float]) -> np.ndarray:
    """Compute the second-order kinematic quadrupole STF-2 tensor: [beta (x) beta]_STF2.

    [beta (x) beta]_STF2 = beta (x) beta - (1/3) * |beta|^2 * I_3.

    Parameters
    ----------
    beta : 3-vector
        Dimensionless velocity vector (c=1).

    Returns
    -------
    np.ndarray
        (3, 3) symmetric trace-free tensor.
    """
    b = np.asarray(beta, dtype=np.float64)
    if b.shape != (3,):
        raise KinematicsError(f"beta must have shape (3,), got {b.shape}")
    if not np.all(np.isfinite(b)):
        raise KinematicsError("beta must contain finite values")
    b2 = float(np.dot(b, b))
    return np.outer(b, b) - (1.0 / 3.0) * b2 * np.eye(3, dtype=np.float64)


def wigner_rotation(
    beta_1: np.ndarray | Sequence[float],
    beta_2: np.ndarray | Sequence[float],
    beta_composed: np.ndarray | Sequence[float] | None = None,
) -> tuple[np.ndarray, float, np.ndarray]:
    """Compute the exact Wigner rotation matrix R_W in SO(3) for two successive boosts.

    Given Lorentz boosts B(beta_1) and B(beta_2) sending:
      L = B(beta_1) @ B(beta_2) = B(beta_composed) @ R_4
    where R_4 = diag(1, R_W) is a pure spatial rotation.

    Hence:
      R_4 = B(-beta_composed) @ B(beta_1) @ B(beta_2)
      R_W = R_4[1:, 1:]

    Parameters
    ----------
    beta_1 : 3-vector
        First boost velocity.
    beta_2 : 3-vector
        Second boost velocity.
    beta_composed : 3-vector, optional
        Composed velocity. If None, computed from relativistic velocity addition.

    Returns
    -------
    R_W : np.ndarray
        (3, 3) rotation matrix in SO(3).
    angle_rad : float
        Rotation angle in radians in [0, pi].
    axis : np.ndarray
        Unit 3-vector rotation axis (zeros if angle == 0).
    """
    b1 = np.asarray(beta_1, dtype=np.float64)
    b2 = np.asarray(beta_2, dtype=np.float64)
    if b1.shape != (3,) or b2.shape != (3,):
        raise KinematicsError("Input velocities must be 3-vectors")
    
    b1_sq = float(np.dot(b1, b1))
    b2_sq = float(np.dot(b2, b2))
    if b1_sq >= 1.0 or b2_sq >= 1.0:
        raise BetaTruncationError("Velocities must be strictly subluminal (|beta| < 1)")

    # Trivial cases: either velocity is zero, or collinear boosts
    if b1_sq == 0.0 or b2_sq == 0.0:
        return np.eye(3, dtype=np.float64), 0.0, np.zeros(3, dtype=np.float64)

    if beta_composed is None:
        b12 = compose_velocities_sr(b1, b2)
    else:
        b12 = np.asarray(beta_composed, dtype=np.float64)

    # 4-dimensional Lorentz matrices
    L1 = lorentz_boost(b1)
    L2 = lorentz_boost(b2)
    L_comp = lorentz_boost(-b12)

    R_4 = L_comp @ (L1 @ L2)
    R_W = np.array(R_4[1:, 1:], dtype=np.float64)

    # Project to pure SO(3) by Polar Decomposition / SVD to remove machine roundoff
    u, _, vt = np.linalg.svd(R_W)
    R_W = u @ vt
    if np.linalg.det(R_W) < 0.0:
        u[:, -1] *= -1.0
        R_W = u @ vt

    # Compute angle and axis
    tr = float(np.trace(R_W))
    cos_theta = np.clip((tr - 1.0) * 0.5, -1.0, 1.0)
    angle_rad = math.acos(cos_theta)

    if angle_rad < 1e-12:
        return R_W, 0.0, np.zeros(3, dtype=np.float64)

    # Antisymmetric part gives axis: R_ij - R_ji = 2 sin(theta) eps_ijk n_k
    unnorm_axis = np.array([
        R_W[2, 1] - R_W[1, 2],
        R_W[0, 2] - R_W[2, 0],
        R_W[1, 0] - R_W[0, 1],
    ], dtype=np.float64)
    axis_norm = float(np.linalg.norm(unnorm_axis))

    if axis_norm > 1e-12:
        axis = unnorm_axis / axis_norm
    else:
        # Near pi rotation: R_W = -I + 2 n n^T => (R_W + I) / 2 = n n^T
        M = (R_W + np.eye(3, dtype=np.float64)) * 0.5
        diag_idx = int(np.argmax(np.diag(M)))
        axis = M[:, diag_idx] / math.sqrt(max(float(M[diag_idx, diag_idx]), 1e-15))
        axis = axis / float(np.linalg.norm(axis))

    return R_W, angle_rad, axis


def compose_velocities_sr(
    beta_RM: np.ndarray | Sequence[float],
    beta_MO: np.ndarray | Sequence[float],
) -> np.ndarray:
    """Special relativistic velocity composition of beta_RM and beta_MO.

    Formula:
      beta_RO = (beta_RM + beta_MO_par + gamma_RM^-1 * beta_MO_perp) / (1 + beta_RM . beta_MO)

    Numerically regularized to evaluate smoothly for all subluminal speeds,
    including beta_RM -> 0 and beta_MO -> 0.

    Parameters
    ----------
    beta_RM : 3-vector
        Drift velocity of matter relative to radiation.
    beta_MO : 3-vector
        Boost velocity of observer relative to matter.

    Returns
    -------
    beta_RO : np.ndarray
        Composed velocity (3-vector).
    """
    b_rm = np.asarray(beta_RM, dtype=np.float64)
    b_mo = np.asarray(beta_MO, dtype=np.float64)
    if b_rm.shape != (3,) or b_mo.shape != (3,):
        raise KinematicsError("Velocities must be 3-vectors")
    if not np.all(np.isfinite(b_rm)) or not np.all(np.isfinite(b_mo)):
        raise KinematicsError("Velocities must contain only finite values")

    b_rm_sq = float(np.dot(b_rm, b_rm))
    b_mo_sq = float(np.dot(b_mo, b_mo))
    if b_rm_sq >= 1.0 or b_mo_sq >= 1.0:
        raise BetaTruncationError(
            f"Velocities must be strictly subluminal (|beta| < 1): got |b_RM|^2={b_rm_sq}, |b_MO|^2={b_mo_sq}"
        )

    dot = float(np.dot(b_rm, b_mo))
    denominator = 1.0 + dot
    if denominator <= 0.0:
        raise KinematicsError("Relativistic velocity composition denominator <= 0")

    gamma_rm_inv = math.sqrt(1.0 - b_rm_sq)

    # Parallel and perpendicular decomposition:
    # beta_MO_par = (b_mo . b_rm / b_rm^2) * b_rm
    # beta_MO_perp = b_mo - beta_MO_par
    #
    # Numerically stable formulation:
    # beta_MO_par + gamma_rm_inv * beta_MO_perp
    # = gamma_rm_inv * beta_MO + (1 - gamma_rm_inv) * (dot / b_rm^2) * beta_RM
    # Using (1 - gamma_inv) / b^2 = gamma / (gamma + 1):
    if b_rm_sq < 1e-15:
        # Zero drift limit: beta_RO = beta_MO
        numerator = b_rm + b_mo
    else:
        gamma_rm = 1.0 / gamma_rm_inv
        par_coeff = (gamma_rm / (gamma_rm + 1.0)) * dot
        numerator = b_rm + gamma_rm_inv * b_mo + par_coeff * b_rm

    beta_RO = numerator / denominator
    return beta_RO


def compose_and_close_velocities(
    beta_RM: np.ndarray | Sequence[float],
    beta_MO: np.ndarray | Sequence[float],
    convention: Convention = "kinematic_response",
) -> VelocityClosureResult:
    """Perform full special relativistic velocity composition and closure.

    Calculates:
      - beta_RO = (beta_RM + beta_MO_par + gamma_RM^-1 * beta_MO_perp) / (1 + beta_RM . beta_MO)
      - First-order residual Delta_beta = beta_RO - (beta_RM + beta_MO)
      - Subluminal check: |beta_RO| < 1.0
      - Exact Wigner rotation matrix R_W, angle, and axis
      - Second-order kinematic quadrupole tensor: [beta_RO (x) beta_RO]_STF2
      - Quadrupole representations in Cartesian and Frobenius-orthonormal 5-vector charts.

    Parameters
    ----------
    beta_RM : 3-vector
        Radiation-matter drift velocity.
    beta_MO : 3-vector
        Matter-observer boost velocity.
    convention : Convention
        STF basis convention ('kinematic_response' or 'explicit_szz').

    Returns
    -------
    VelocityClosureResult
        Complete closure result container.
    """
    b_rm = np.asarray(beta_RM, dtype=np.float64)
    b_mo = np.asarray(beta_MO, dtype=np.float64)

    # Relativistic composition
    b_ro = compose_velocities_sr(b_rm, b_mo)

    # Residual relative to first-order Galilean addition
    delta_beta = b_ro - (b_rm + b_mo)
    delta_beta_norm = float(np.linalg.norm(delta_beta))

    b_ro_sq = float(np.dot(b_ro, b_ro))
    b_ro_norm = math.sqrt(b_ro_sq)
    is_subluminal = b_ro_norm < 1.0
    if not is_subluminal:
        raise BetaTruncationError(f"Composed velocity exceeds speed of light: |beta_RO| = {b_ro_norm}")

    gamma_ro = 1.0 / math.sqrt(max(1.0 - b_ro_sq, 1e-15))

    # Wigner rotation
    R_W, wigner_angle, wigner_axis = wigner_rotation(b_rm, b_mo, beta_composed=b_ro)

    # Kinematic quadrupole STF2
    quad_stf2 = kinematic_quadrupole_stf2(b_ro)
    quad_cart = stf_matrix_to_cartesian(quad_stf2)
    quad_on = stf_matrix_to_orthonormal(quad_stf2, convention=convention)

    return VelocityClosureResult(
        beta_RM=b_rm,
        beta_MO=b_mo,
        beta_RO=b_ro,
        delta_beta=delta_beta,
        delta_beta_norm=delta_beta_norm,
        beta_RO_norm=b_ro_norm,
        gamma_RO=gamma_ro,
        is_subluminal=is_subluminal,
        closure_status="EXACT_RELATIVISTIC_CLOSURE",
        wigner_rotation_matrix=R_W,
        wigner_angle_rad=wigner_angle,
        wigner_axis=wigner_axis,
        quadrupole_stf2=quad_stf2,
        quadrupole_stf5_cart=quad_cart,
        quadrupole_stf5_on=quad_on,
    )
