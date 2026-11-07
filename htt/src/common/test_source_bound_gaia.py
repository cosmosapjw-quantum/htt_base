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
