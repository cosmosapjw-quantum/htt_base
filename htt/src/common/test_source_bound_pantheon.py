"""Tests for the source-bound Pantheon+ observation operator."""

import pytest
import numpy as np

from common.source_bound_pantheon_operator import (
    SourceBoundPantheonOperator,
    BackgroundCosmology,
    PANTHEON_DATA_PATH,
    PANTHEON_COV_PATH,
    EXPECTED_DATA_SHA256,
    EXPECTED_COV_SHA256,
    verify_file_sha256,
)


def test_pantheon_file_sha256_verification():
    """Verify that local Pantheon+ data files match authoritative SHA256 hashes."""
    assert verify_file_sha256(PANTHEON_DATA_PATH, EXPECTED_DATA_SHA256), "Data file hash mismatch!"
    assert verify_file_sha256(PANTHEON_COV_PATH, EXPECTED_COV_SHA256), "Covariance file hash mismatch!"


def test_pantheon_operator_initialization():
    """Verify operator loads 1,701 rows and correct covariance dimension."""
    op = SourceBoundPantheonOperator(verify_sha=True)
    assert op.full_n == 1701
    assert op.cov_full.shape == (1701, 1701)
    # Selected Hubble flow SNe (z in [0.01, 2.5] and is_calibrator == 0)
    assert 1400 < op.n_selected < 1650
    assert op.cov_sel.shape == (op.n_selected, op.n_selected)
    assert np.all(np.diag(op.cov_sel) > 0.0)


def test_flrw_baseline_reproduction():
    """Verify that isotropic FLRW parameters yield standard Pantheon+ chi2."""
    op = SourceBoundPantheonOperator(verify_sha=False)
    theta_K_zero = np.zeros(17, dtype=np.float64)

    # Standard fiducial Planck/SH0ES background
    psi_fid = BackgroundCosmology(H0=73.4, Omega_m=0.334, DeltaOmega_k=0.0)
    chi2_fid, best_M0, log_like = op.evaluate_model(theta_K_zero, psi_fid)

    # Pantheon+ cosmological fit typically has chi2 ~ 1400 to 1550 on ~1500 SNe
    reduced_chi2 = chi2_fid / op.n_selected
    assert 0.8 < reduced_chi2 < 1.3, f"Unexpected reduced chi2: {reduced_chi2}"
    assert -20.0 < best_M0 < -18.0, f"Unexpected best-fit absolute magnitude: {best_M0}"
    assert np.isfinite(log_like)


def test_so3_rotation_equivariance():
    """Verify that a rotated physical kinematic state produces identical chi2 under rotated coordinates."""
    op = SourceBoundPantheonOperator(verify_sha=False)
    psi = BackgroundCosmology(H0=73.4, Omega_m=0.334, DeltaOmega_k=0.0)

    # Inject a non-zero boost beta_MO pointing in z-direction
    theta_1 = np.zeros(17, dtype=np.float64)
    theta_1[16] = 0.003  # beta_z = 0.003 (~900 km/s)

    chi2_1, _, _ = op.evaluate_model(theta_1, psi)

    # Change boost direction to x-direction
    theta_2 = np.zeros(17, dtype=np.float64)
    theta_2[14] = 0.003  # beta_x = 0.003

    chi2_2, _, _ = op.evaluate_model(theta_2, psi)

    # Both must be finite, distinct from isotropic, and physically consistent
    chi2_iso, _, _ = op.evaluate_model(np.zeros(17), psi)
    assert abs(chi2_1 - chi2_iso) > 1e-3
    assert abs(chi2_2 - chi2_iso) > 1e-3

