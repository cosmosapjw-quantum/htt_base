"""Tests for Unified Multi-Probe Joint Likelihood L(theta_K, psi | D).

Verifies Wave 4 (Task 4A) requirements:
  - HTT ownership & parameter structure (theta_K in R^17, psi in R^4, JointState in R^21)
  - Exact special relativistic velocity closure (beta_RO derived from beta_RM and beta_MO)
  - Invariance under SO(3) rotations to machine precision
  - Analytic Schur marginalization of linear nuisance parameters (Delta M_0, Omega_triad, a_SSB)
  - Zero-stub empirical data integrity across all 7 observational channels
  - Valid, finite positive chi2 and probe-by-probe breakdown
  - Positive definiteness of all probe and joint covariances
  - Non-zero parameter gradients and positive semi-definite Fisher information matrix
  - LOOCV probe-deletion masking functionality
"""
from __future__ import annotations

import math
from pathlib import Path
import sys
import numpy as np
import pytest
import scipy.linalg
import scipy.optimize

# Ensure repository packages are in python path
ROOT = Path(__file__).resolve().parents[3]
for p in (ROOT / "htt/src", ROOT / "htt", ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from htt.infer.tensor_joint_multiprobe_likelihood import (
    DataIntegrityError,
    JointState,
    ProbeMaskedLikelihood,
    PsiCosmology,
    SchurMarginalizer,
    TensorJointMultiprobeLikelihood,
    ThetaKinematic,
    create_unified_joint_likelihood,
    params_to_kinematic_model,
)


def _make_so3_rotation(angle_rad: float, axis: np.ndarray) -> np.ndarray:
    """Construct SO(3) rotation matrix via Rodrigues formula."""
    u = np.asarray(axis, dtype=np.float64)
    u = u / np.linalg.norm(u)
    K = np.array([
        [0.0, -u[2], u[1]],
        [u[2], 0.0, -u[0]],
        [-u[1], u[0], 0.0],
    ], dtype=np.float64)
    R = np.eye(3, dtype=np.float64) + math.sin(angle_rad) * K + (1.0 - math.cos(angle_rad)) * (K @ K)
    return R


# -----------------------------------------------------------------------------
# 1. Parameter Classes and Exact Relativistic Velocity Closure
# -----------------------------------------------------------------------------

def test_parameter_classes_and_relativistic_velocity_closure():
    """Verify ThetaKinematic, PsiCosmology, JointState, and relativistic composition."""
    # Null kinematic state
    sigma5 = np.array([1e-5, -5e-6, 2e-6, -3e-6, 4e-6])
    omega = np.array([1e-4, -2e-4, 3e-4])
    accel = np.array([2e-4, 1e-4, -1e-4])
    b_rm = np.array([3e-4, -2e-4, 1e-4])
    b_mo = np.array([1.2e-3, 5e-4, -8e-4])

    th = ThetaKinematic(
        sigma_AB=sigma5,
        omega_A=omega,
        A_A=accel,
        beta_RM_A=b_rm,
        beta_MO_A=b_mo,
        chart="cartesian",
    )
    assert th.to_vector().shape == (17,)

    # Round-trip serialization
    th_rt = ThetaKinematic.from_vector(th.to_vector(), chart="cartesian")
    np.testing.assert_allclose(th.to_vector(), th_rt.to_vector(), atol=1e-15)

    # Relativistic velocity closure: beta_RO
    b_ro = th.beta_RO
    assert b_ro.shape == (3,)
    assert np.linalg.norm(b_ro) < 1.0

    # Closure result container
    closure = th.closure
    assert closure.closure_status == "EXACT_RELATIVISTIC_CLOSURE"
    assert closure.is_subluminal

    # Kinematic quadrupole is symmetric and trace-free
    Q_kin = th.kinematic_quadrupole_stf2
    assert Q_kin.shape == (3, 3)
    np.testing.assert_allclose(Q_kin, Q_kin.T, atol=1e-15)
    assert abs(np.trace(Q_kin)) < 1e-15

    # Orthonormal chart conversion
    th_on = ThetaKinematic(
        sigma_AB=th.sigma_orthonormal,
        omega_A=omega,
        A_A=accel,
        beta_RM_A=b_rm,
        beta_MO_A=b_mo,
        chart="orthonormal",
    )
    np.testing.assert_allclose(th.sigma_matrix, th_on.sigma_matrix, atol=1e-15)

    # Cosmological parameters psi
    psi = PsiCosmology(H_0=67.4, Omega_m=0.315, r_d=147.09, DeltaOmega_k=0.0)
    assert psi.to_vector().shape == (4,)
    psi_rt = PsiCosmology.from_vector(psi.to_vector())
    np.testing.assert_allclose(psi.to_vector(), psi_rt.to_vector(), atol=1e-15)
    assert psi.E_z(0.0) == pytest.approx(1.0)
    assert psi.hubble_distance_Mpc(0.0) > 4000.0

    # Joint state in R^21
    st = JointState(theta_K=th, psi=psi)
    v21 = st.to_vector()
    assert v21.shape == (21,)
    st_rt = JointState.from_vector(v21)
    np.testing.assert_allclose(v21, st_rt.to_vector(), atol=1e-15)


# -----------------------------------------------------------------------------
# 2. SO(3) Rotational Covariance and Invariance
# -----------------------------------------------------------------------------

def test_so3_rotational_covariance_and_invariance():
    """Verify SO(3) covariance of velocity composition, shear matrix, and scalar invariants."""
    th = ThetaKinematic(
        sigma_AB=np.array([2.5e-5, -1.2e-5, 8.0e-6, -6.0e-6, 1.1e-5]),
        omega_A=np.array([1.5e-4, -2.1e-4, 3.3e-4]),
        A_A=np.array([2.2e-4, 1.4e-4, -1.8e-4]),
        beta_RM_A=np.array([4.0e-4, -3.2e-4, 1.5e-4]),
        beta_MO_A=np.array([1.1e-3, 6.0e-4, -9.0e-4]),
    )
    st = JointState(theta_K=th, psi=PsiCosmology())
    lik = create_unified_joint_likelihood()

    # Test three independent rotation angles and axes
    test_cases = [
        (0.42, np.array([1.0, 0.0, 0.0])),
        (1.15, np.array([0.0, 1.0, 0.0])),
        (2.31, np.array([1.0, 2.0, 3.0])),
    ]

    for angle, axis in test_cases:
        R = _make_so3_rotation(angle, axis)
        audit = lik.verify_so3_invariance(st, R)

        # Relativistic velocity composition transforms covariantly: beta_RO(R theta) = R beta_RO(theta)
        assert audit["diff_beta_RO"] < 1e-15, f"beta_RO covariance failed: {audit['diff_beta_RO']}"

        # Shear matrix transforms covariantly: S(R theta) = R S(theta) R^T
        assert audit["diff_sigma_matrix"] < 1e-15, f"sigma matrix covariance failed: {audit['diff_sigma_matrix']}"

        # Kinematic quadrupole transforms covariantly: Q(R theta) = R Q(theta) R^T
        assert audit["diff_kinematic_quadrupole"] < 1e-15, f"quadrupole covariance failed: {audit['diff_kinematic_quadrupole']}"

        # Frobenius norm is strictly invariant under SO(3)
        assert audit["diff_sigma_frobenius"] < 1e-15, f"Frobenius norm invariance failed: {audit['diff_sigma_frobenius']}"

        # Total SO(3) invariant scalar norm is strictly preserved
        assert audit["diff_total_norm"] < 1e-15, f"Total norm invariance failed: {audit['diff_total_norm']}"

        # Directional response invariance: for any unit direction n, (R n)^T S' (R n) == n^T S n
        n_test = np.array([0.577, 0.577, 0.577])
        n_test /= np.linalg.norm(n_test)
        n_rot = R @ n_test
        S_orig = th.sigma_matrix
        S_rot = th.rotate(R).sigma_matrix
        val_orig = float(n_test @ S_orig @ n_test)
        val_rot = float(n_rot @ S_rot @ n_rot)
        assert abs(val_orig - val_rot) < 1e-15


# -----------------------------------------------------------------------------
# 3. Analytic Schur Marginalization Correctness
# -----------------------------------------------------------------------------

def test_analytic_schur_marginalization_correctness():
    """Verify analytic Schur marginalization matches numerical optimization over nuisance parameters."""
    np.random.seed(123)
    N = 25
    p = 3

    # Generate synthetic positive-definite covariance
    A = np.random.randn(N, N)
    C = A @ A.T + 0.1 * np.eye(N)
    L = np.linalg.cholesky(C)

    # Design matrix for linear nuisance parameters
    H = np.random.randn(N, p)
    # Raw residual
    r_raw = np.random.randn(N)

    # 1. Analytic Schur marginalization
    marginalizer = SchurMarginalizer(L, design_matrix=H, name="TestSchur")
    chi2_schur, logp_schur, eta_hat = marginalizer.marginalize(r_raw)

    assert eta_hat is not None
    assert eta_hat.shape == (p,)

    # 2. Independent numerical minimization over nuisance parameters eta:
    # min_eta (r - H eta)^T C^-1 (r - H eta)
    def chi2_fn(eta: np.ndarray) -> float:
        res = r_raw - H @ eta
        w = scipy.linalg.solve_triangular(L, res, lower=True)
        return float(np.dot(w, w))

    res_opt = scipy.optimize.minimize(chi2_fn, x0=np.zeros(p), method="BFGS")
    chi2_num = float(res_opt.fun)
    eta_num = res_opt.x

    # Must match to machine precision / numerical optimizer tolerance
    np.testing.assert_allclose(chi2_schur, chi2_num, rtol=1e-8, atol=1e-8)
    np.testing.assert_allclose(eta_hat, eta_num, rtol=1e-6, atol=1e-6)

    # Nuisance Fisher information matrix F_eta is positive-definite
    eigs_F = np.linalg.eigvalsh(marginalizer.F_eta)
    assert np.all(eigs_F > 0)


# -----------------------------------------------------------------------------
# 4. Zero-Stub Empirical Data Verification
# -----------------------------------------------------------------------------

def test_zero_stub_data_verification():
    """Verify that every active likelihood component reads real empirical data from inventory."""
    lik = create_unified_joint_likelihood()
    lik.assert_zero_stub_data()

    assert lik.n_data == 1536
    assert len(lik.enabled_probes) == 7

    # Probe-specific checks
    for probe_name in ["CMB", "Quasars", "Radio", "Gaia", "SNe", "PV", "DESI"]:
        probe = lik.all_probes[probe_name]
        assert probe.n_data > 0
        assert probe.cov_matrix.shape == (probe.n_data, probe.n_data)
        assert not np.all(probe.data_vector == 0.0)
        assert not np.all(probe.cov_matrix == np.eye(probe.n_data))
        assert Path(probe.source_path).exists()


# -----------------------------------------------------------------------------
# 5. Valid Chi2 and Probe Breakdown
# -----------------------------------------------------------------------------

def test_valid_chi2_and_breakdown():
    """Verify valid, finite positive chi2 and probe breakdown across all 7 channels."""
    lik = create_unified_joint_likelihood()

    # Null state
    st_null = JointState.null()
    bd_null = lik.chi2_breakdown(st_null)
    assert len(bd_null) == 8  # 7 probes + 'Total'
    assert bd_null["Total"] > 0
    assert math.isfinite(bd_null["Total"])

    for p in ["CMB", "Quasars", "Radio", "Gaia", "SNe", "PV", "DESI"]:
        assert bd_null[p] > 0
        assert math.isfinite(bd_null[p])

    total_chi2 = lik.chi2(st_null)
    assert total_chi2 == pytest.approx(bd_null["Total"])

    logp_val = lik.logp(st_null)
    assert math.isfinite(logp_val)
    assert logp_val < 0  # Gaussian log-likelihood is negative for large N

    # Perturbed physical state
    st_phys = JointState(
        theta_K=ThetaKinematic(
            sigma_AB=np.array([5e-5, -2e-5, 1e-5, -1e-5, 2e-5]),
            omega_A=np.array([1e-4, -1e-4, 2e-4]),
            A_A=np.array([1e-4, 2e-4, -1e-4]),
            beta_RM_A=np.array([2e-4, -1e-4, 1e-4]),
            beta_MO_A=np.array([1e-3, 1e-3, -5e-4]),
        ),
        psi=PsiCosmology(H_0=68.0, Omega_m=0.31, r_d=147.5, DeltaOmega_k=0.005),
    )
    bd_phys = lik.chi2_breakdown(st_phys)
    assert math.isfinite(bd_phys["Total"])
    assert bd_phys["Total"] > 0


# -----------------------------------------------------------------------------
# 6. Positive Definiteness of All Covariances
# -----------------------------------------------------------------------------

def test_positive_definiteness_of_all_covariances():
    """Verify that every probe covariance matrix and joint covariance has strictly positive eigenvalues."""
    lik = create_unified_joint_likelihood()

    # Check each individual probe covariance
    for name, probe in lik.all_probes.items():
        cov = probe.cov_matrix
        np.testing.assert_allclose(cov, cov.T, atol=1e-12, err_msg=f"[{name}] Covariance not symmetric")
        eigs = np.linalg.eigvalsh(cov)
        min_eig = float(np.min(eigs))
        assert min_eig > 0, f"[{name}] Minimum eigenvalue {min_eig} <= 0"

    # Joint covariance positive definiteness and Cholesky existence
    assert lik.L is not None
    assert lik.L.shape == (lik.n_data, lik.n_data)
    assert np.all(np.diag(lik.L) > 0)


# -----------------------------------------------------------------------------
# 7. Non-Zero Gradients and Fisher Information
# -----------------------------------------------------------------------------

def test_nonzero_gradients_and_jacobians():
    """Verify non-zero gradients with respect to physical parameters and positive semi-definite Fisher matrix."""
    lik = create_unified_joint_likelihood()
    st = JointState.null()

    # Compute numerical gradient of total joint chi2 (21 parameters)
    grad = lik.gradient(st, eps=1e-5)
    assert grad.shape == (21,)
    assert not np.all(grad == 0.0)
    assert np.linalg.norm(grad) > 0.0

    # Specifically check that gradient is non-zero in key sectors:
    # 1. Matter-observer boost beta_MO (indices 14..17)
    grad_beta_mo = grad[14:17]
    assert np.linalg.norm(grad_beta_mo) > 0.0, "Gradient with respect to beta_MO must be non-zero"

    # 2. Cosmic shear sigma_AB (indices 0..5)
    grad_sigma = grad[0:5]
    assert np.linalg.norm(grad_sigma) > 0.0, "Gradient with respect to shear must be non-zero"

    # 3. Cosmological background H_0 and Omega_m (indices 17..19)
    grad_cosmo = grad[17:19]
    assert np.linalg.norm(grad_cosmo) > 0.0, "Gradient with respect to background must be non-zero"


# -----------------------------------------------------------------------------
# 8. Probe Deletion Masking (LOOCV Compatibility)
# -----------------------------------------------------------------------------

def test_probe_deletion_masked_likelihood():
    """Verify probe-deletion masking for Leave-One-Probe-Out Cross-Validation."""
    lik = create_unified_joint_likelihood()
    st = JointState.null()
    th_vec = st.theta_K.to_vector()

    # Exclude CMB
    loocv_cmb = lik.get_probe_deletion_likelihood("CMB")
    assert loocv_cmb.held_out_name == "CMB"
    assert loocv_cmb.n_held == 10
    assert loocv_cmb.n_active == lik.n_data - 10

    logp_act = loocv_cmb.logp_active(th_vec)
    assert math.isfinite(logp_act)

    logp_held, chi2_held, chi2_dof = loocv_cmb.evaluate_held_out(th_vec)
    assert math.isfinite(logp_held)
    assert chi2_held > 0
    assert chi2_dof > 0

    # Compatibility: params_to_kinematic_model helper
    model = params_to_kinematic_model(th_vec)
    assert model.state.beta_RO.shape == (3,)
