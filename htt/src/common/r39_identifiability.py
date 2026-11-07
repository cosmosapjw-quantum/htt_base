"""Nuisance-projected response rank, SVD, Fisher information and functional identifiability.

Work Package E of HTT-R39 Observational Convergence.
Computes:
  - Exact source-conditioned forward Jacobians J_p = d(pred)/d(theta_K) across 17 parameters
  - Whitening on the positive-definite joint covariance support: J_tilde = L^-1 J
  - QR projection of shared and probe-specific nuisance directions (monopole, absolute magnitude, triad rotation)
  - SVD of the projected effective Jacobian J_eff = (I - Q_n Q_n^T) J_tilde
  - Singular spectrum, effective rank, condition number on the supported quotient
  - Local functional identifiability check: ker(J_eff) subset ker(D phi_alpha)
  - Preregistered ablations: scalar x_C vs vector/tensor x, O(3) vs SO(3) quotient, leave-one-probe-out
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence
import numpy as np

from common.covariance_validator import validate_covariance, whiten_matrix
from common.kinematic_response import KinematicResponseModel, KinematicFrameState
from common.kinematical_functionals import stf5_to_matrix
from common.relativistic_velocity_closure import compose_velocities_sr
from common.stf_metric_bridge import (
    G_STF5,
    cartesian_to_orthonormal_matrix,
    orthonormal_to_cartesian_matrix,
)


PARAM_NAMES_17 = [
    "sigma_xx", "sigma_yy", "sigma_xy", "sigma_xz", "sigma_yz",
    "omega_x", "omega_y", "omega_z",
    "A_x", "A_y", "A_z",
    "beta_RM_x", "beta_RM_y", "beta_RM_z",
    "beta_MO_x", "beta_MO_y", "beta_MO_z",
]


@dataclass(frozen=True)
class IdentifiabilitySpectrum:
    """Results of nuisance-projected SVD and rank-stability analysis."""

    parameter_names: list[str]
    singular_values: np.ndarray
    effective_rank: int
    null_space_dimension: int
    condition_number: float
    null_vectors: np.ndarray        # Basis of ker(J_eff), shape (17, null_dim)
    identifiable_basis: np.ndarray  # Basis of supported quotient, shape (17, eff_rank)
    functional_identifiability: dict[str, bool]
    fisher_matrix: np.ndarray
    gram_whitened: bool = True


def compute_numerical_jacobian(
    forward_fn,
    theta_0: np.ndarray,
    eps: float = 1e-6,
) -> np.ndarray:
    """Compute central-difference Jacobian of forward_fn around theta_0."""
    theta_0 = np.asarray(theta_0, dtype=np.float64)
    f0 = np.asarray(forward_fn(theta_0), dtype=np.float64)
    n_out = len(f0)
    n_in = len(theta_0)
    J = np.zeros((n_out, n_in), dtype=np.float64)

    for j in range(n_in):
        step = np.zeros(n_in, dtype=np.float64)
        step[j] = eps
        f_plus = np.asarray(forward_fn(theta_0 + step), dtype=np.float64)
        f_minus = np.asarray(forward_fn(theta_0 - step), dtype=np.float64)
        J[:, j] = (f_plus - f_minus) / (2.0 * eps)

    return J


def analyze_r39_identifiability(
    joint_jacobian: np.ndarray,
    cov_joint: np.ndarray,
    nuisance_matrix: np.ndarray | None = None,
    rank_tol: float = 1e-5,
    use_gram_whitening: bool = True,
) -> IdentifiabilitySpectrum:
    """Whiten Jacobian, project nuisance directions, and perform SVD analysis.

    Parameters
    ----------
    joint_jacobian : np.ndarray, shape (N_data, 17)
    cov_joint : np.ndarray, shape (N_data, N_data)
    nuisance_matrix : np.ndarray | None, shape (N_data, N_nuisance)
    rank_tol : float
        Relative singular value threshold below which a mode is classified as null.
    use_gram_whitening : bool
        If True, whitens Cartesian shear parameters by Gram metric G_STF5 so
        SVD and Fisher eigenspaces are coordinate-invariant with Frobenius metric.
    """
    J = np.asarray(joint_jacobian, dtype=np.float64)
    C = np.asarray(cov_joint, dtype=np.float64)
    n_data, n_params = J.shape
    if n_params != 17:
        raise ValueError(f"Expected 17 parameters, got {n_params}")

    # 1. Cholesky factor of joint covariance
    cov_sym, L, _ = validate_covariance(C, name="JointCovariance", check_positive_definite=True)

    # 2. Whiten Jacobian
    J_tilde = whiten_matrix(L, J)

    # 3. Project nuisance directions
    if nuisance_matrix is not None and nuisance_matrix.shape[1] > 0:
        N = np.asarray(nuisance_matrix, dtype=np.float64)
        N_tilde = whiten_matrix(L, N)
        Q_n, _ = np.linalg.qr(N_tilde, mode="reduced")
        # Project out nuisance space
        J_eff = J_tilde - Q_n @ (Q_n.T @ J_tilde)
    else:
        J_eff = J_tilde

    # 4. Gram metric G_STF5 whitening for parameter space (Bug 1 & SVD geometry)
    if use_gram_whitening:
        M_inv = orthonormal_to_cartesian_matrix("kinematic_response")
        T_inv = np.eye(n_params, dtype=np.float64)
        T_inv[:5, :5] = M_inv
        J_svd = J_eff @ T_inv
    else:
        T_inv = np.eye(n_params, dtype=np.float64)
        J_svd = J_eff

    # 5. SVD of effective Jacobian on Riemannian parameter quotient
    U, s, Vt = np.linalg.svd(J_svd, full_matrices=False)
    V_white = Vt.T
    V = T_inv @ V_white

    # 6. Effective rank and null space
    max_s = float(s[0]) if len(s) > 0 and s[0] > 0 else 1.0
    cutoff = max_s * rank_tol
    is_active = s > cutoff
    eff_rank = int(np.sum(is_active))
    null_dim = n_params - eff_rank

    cond_num = float(s[0] / s[eff_rank - 1]) if eff_rank > 0 else float("inf")

    identifiable_basis = V[:, :eff_rank]
    null_vectors = V[:, eff_rank:]

    # 7. Fisher information matrix in Cartesian coordinates
    Fisher = J_eff.T @ J_eff

    # 7. Check local identifiability of key physical functionals:
    # A functional phi is locally identified if ker(J_eff) subset ker(D phi)
    # i.e., null_vectors.T @ grad_phi == 0
    functional_id_map: dict[str, bool] = {}

    def test_functional_id(grad: np.ndarray, tol: float = 1e-4) -> bool:
        if null_dim == 0:
            return True
        projection = null_vectors.T @ grad
        return float(np.linalg.norm(projection)) < tol * float(np.linalg.norm(grad))

    # Shear components: indices 0..4
    for i in range(5):
        g = np.zeros(17); g[i] = 1.0
        functional_id_map[f"sigma_{i}"] = test_functional_id(g)

    # Vorticity components: indices 5..7
    for i in range(3):
        g = np.zeros(17); g[5+i] = 1.0
        functional_id_map[f"omega_{i}"] = test_functional_id(g)

    # Acceleration components: indices 8..10
    for i in range(3):
        g = np.zeros(17); g[8+i] = 1.0
        functional_id_map[f"accel_{i}"] = test_functional_id(g)

    # Relative velocity beta_RM: indices 11..13
    for i in range(3):
        g = np.zeros(17); g[11+i] = 1.0
        functional_id_map[f"beta_RM_{i}"] = test_functional_id(g)

    # Relative velocity beta_MO: indices 14..16
    for i in range(3):
        g = np.zeros(17); g[14+i] = 1.0
        functional_id_map[f"beta_MO_{i}"] = test_functional_id(g)

    # Derived closure: beta_RO = beta_RM + beta_MO
    for i in range(3):
        g = np.zeros(17); g[11+i] = 1.0; g[14+i] = 1.0
        functional_id_map[f"beta_RO_{i}"] = test_functional_id(g)

    # Mixed functional: beta_RM . beta_MO
    # Gradient depends on fiducial point, tested separately in ablations

    return IdentifiabilitySpectrum(
        parameter_names=list(PARAM_NAMES_17),
        singular_values=s,
        effective_rank=eff_rank,
        null_space_dimension=null_dim,
        condition_number=cond_num,
        null_vectors=null_vectors,
        identifiable_basis=identifiable_basis,
        functional_identifiability=functional_id_map,
        fisher_matrix=Fisher,
    )
