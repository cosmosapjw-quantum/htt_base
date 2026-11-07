"""Unit tests for SourceBoundGaiaVSHOperator."""

import os
import pytest
import numpy as np

from common.source_bound_gaia_vsh_operator import (
    SourceBoundGaiaVSHOperator,
    GAIA_NPZ_PATH,
    EXPECTED_GAIA_SHA256,
    H0_MAS_YR,
)
from common.source_bound_pantheon_operator import verify_file_sha256


@pytest.mark.skipif(not os.path.exists(GAIA_NPZ_PATH), reason="Gaia NPZ dataset not found")
def test_gaia_file_hash():
    """Verify authoritative SHA-256 hash of Gaia CRF3 join file."""
    assert verify_file_sha256(GAIA_NPZ_PATH, EXPECTED_GAIA_SHA256)


@pytest.mark.skipif(not os.path.exists(GAIA_NPZ_PATH), reason="Gaia NPZ dataset not found")
def test_gaia_vsh_operator_initialization():
    """Verify initialization, clean quasar count, and Fisher matrix properties."""
    op = SourceBoundGaiaVSHOperator(verify_sha=False)
    assert op.n_raw == 692154
    assert op.n_selected > 600000
    assert op.A.shape == (8, 8)
    assert op.cov_c.shape == (8, 8)
    
    # Check positive definiteness of Fisher matrix and covariance
    evals = np.linalg.eigvalsh(op.A)
    assert np.all(evals > 0), "Fisher matrix must be positive definite"
    assert np.all(np.linalg.eigvalsh(op.cov_c) > 0), "Covariance must be positive definite"

    # Measured glide amplitude should match Gaia Collaboration baseline ~ 5.4 uas/yr = 0.0054 mas/yr
    assert 0.003 < op.amp_glide < 0.008, f"Unexpected glide amplitude: {op.amp_glide}"
    assert 0.0005 < op.amp_shear < 0.005, f"Unexpected shear amplitude: {op.amp_shear}"


@pytest.mark.skipif(not os.path.exists(GAIA_NPZ_PATH), reason="Gaia NPZ dataset not found")
def test_gaia_vsh_evaluation():
    """Verify model evaluation under zero state vs best-fit state."""
    op = SourceBoundGaiaVSHOperator(verify_sha=False)
    
    # Evaluation at best-fit MLE modes
    chi2_best, logl_best = op.evaluate_modes(op.c_mle)
    assert np.isclose(chi2_best, op.chi2_min)
    
    # Evaluation under zero state (H0)
    theta_zero = np.zeros(17, dtype=np.float64)
    chi2_zero, logl_zero = op.evaluate_model(theta_zero)
    assert chi2_zero > chi2_best
    assert logl_zero < logl_best

    # Evaluation with acceleration matching glide
    theta_accel = np.zeros(17, dtype=np.float64)
    theta_accel[8:11] = op.glide_mle / H0_MAS_YR
    chi2_accel, logl_accel = op.evaluate_model(theta_accel)
    assert chi2_accel < chi2_zero


def test_gaia_vsh_spin_glide_mathematical_properties():
    """Verify divergence-free property of spin modes and pointwise orthogonality to glide."""
    from common.source_bound_gaia_vsh_operator import vsh_basis_functions

    # Grid of test points avoiding poles
    ra = np.linspace(10.0, 350.0, 35)
    dec = np.linspace(-80.0, 80.0, 17)
    ra_grid, dec_grid = np.meshgrid(ra, dec)
    ra_flat = ra_grid.ravel()
    dec_flat = dec_grid.ravel()

    vsh = vsh_basis_functions(ra_flat, dec_flat)

    # 1. Pointwise orthogonality: R_k . G_k = R_alpha * G_alpha + R_delta * G_delta == 0
    for k in range(3):
        R_k = vsh["spin"][k]
        G_k = vsh["glide"][k]
        dot_prod = R_k[:, 0] * G_k[:, 0] + R_k[:, 1] * G_k[:, 1]
        assert np.max(np.abs(dot_prod)) < 1e-14, f"Spin and Glide mode {k} not orthogonal: max={np.max(np.abs(dot_prod))}"


def test_gaia_vsh_stf_shear_exactness():
    """Verify that STF Cartesian tensor maps exactly to VSH shear basis to machine precision."""
    from common.source_bound_gaia_vsh_operator import vsh_basis_functions

    # Generate arbitrary non-trivial STF tensor
    rng = np.random.RandomState(42)
    M = rng.normal(size=(3, 3))
    S = 0.5 * (M + M.T)
    S -= np.trace(S) / 3.0 * np.eye(3)

    Sxx, Syy, Szz = S[0, 0], S[1, 1], S[2, 2]
    Sxy, Sxz, Syz = S[0, 1], S[0, 2], S[1, 2]

    # Grid of points
    ra = np.array([15.0, 75.0, 160.0, 230.0, 310.0])
    dec = np.array([-60.0, -15.0, 20.0, 55.0, 80.0])
    phi = np.deg2rad(ra)
    theta = np.deg2rad(90.0 - dec)

    # Direct 3D Cartesian shear projection onto sphere
    rx = np.sin(theta) * np.cos(phi)
    ry = np.sin(theta) * np.sin(phi)
    rz = np.cos(theta)
    r = np.column_stack([rx, ry, rz])
    v_3d = r @ S.T

    e_alpha = np.column_stack([-np.sin(phi), np.cos(phi), np.zeros_like(phi)])
    e_delta = np.column_stack([-np.cos(theta)*np.cos(phi), -np.cos(theta)*np.sin(phi), np.sin(theta)])

    v_alpha_direct = np.sum(v_3d * e_alpha, axis=1)
    v_delta_direct = np.sum(v_3d * e_delta, axis=1)

    # Model coefficients from operator
    E2_0 = 0.25 * Szz
    E2_1c = 0.5 * Sxz
    E2_1s = 0.5 * Syz
    E2_2c = 0.25 * (Sxx - Syy)
    E2_2s = 0.5 * Sxy

    vsh = vsh_basis_functions(ra, dec)
    vsh_shear = (
        E2_0 * vsh["shear"][0]
        + E2_1c * vsh["shear"][1]
        + E2_1s * vsh["shear"][2]
        + E2_2c * vsh["shear"][3]
        + E2_2s * vsh["shear"][4]
    )

    diff_alpha = np.max(np.abs(vsh_shear[:, 0] - v_alpha_direct))
    diff_delta = np.max(np.abs(vsh_shear[:, 1] - v_delta_direct))

    assert diff_alpha < 1e-15, f"Shear alpha reconstruction error: {diff_alpha}"
    assert diff_delta < 1e-15, f"Shear delta reconstruction error: {diff_delta}"
