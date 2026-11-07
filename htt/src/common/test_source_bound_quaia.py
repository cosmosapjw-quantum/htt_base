"""Tests for the source-bound Quaia Quasar Count Dipole operator."""

import pytest
import numpy as np

from common.source_bound_quaia_operator import (
    SourceBoundQuaiaDipoleOperator,
    QUAIA_CAT_PATH,
    QUAIA_RND_PATH,
    QUAIA_SEL_PATH,
    EXPECTED_CAT_SHA256,
    EXPECTED_RND_SHA256,
    EXPECTED_SEL_SHA256,
    verify_file_sha256,
)


def test_quaia_file_sha256_verification():
    """Verify that local Quaia G20.0 data files match authoritative SHA256 hashes."""
    assert verify_file_sha256(QUAIA_CAT_PATH, EXPECTED_CAT_SHA256), "Quaia catalog hash mismatch!"
    assert verify_file_sha256(QUAIA_RND_PATH, EXPECTED_RND_SHA256), "Quaia randoms hash mismatch!"
    assert verify_file_sha256(QUAIA_SEL_PATH, EXPECTED_SEL_SHA256), "Quaia selection map hash mismatch!"


def test_quaia_operator_initialization_and_measurement():
    """Verify Quaia operator loads full catalogue and measures empirical dipole."""
    op = SourceBoundQuaiaDipoleOperator(verify_sha=False)
    assert op.n_sources == 755850
    assert op.n_randoms > 7000000
    assert op.f_sky > 0.40  # Covers majority of extra-Galactic sky
    assert 2.5 < op.C_EB < 4.0
    
    # Measured dipole amplitude should be in empirical range ~ 0.015 to 0.045
    assert 0.010 < op.amp_obs < 0.060, f"Unexpected dipole amplitude: {op.amp_obs}"
    assert op.cov_D.shape == (3, 3)
    assert np.all(np.linalg.eigvalsh(op.cov_D) > 0.0)


def test_quaia_likelihood_evaluation():
    """Verify Quaia dipole chi2 and log-likelihood under zero and best-fit boost."""
    op = SourceBoundQuaiaDipoleOperator(verify_sha=False)
    
    # Under zero boost: pure isotropic null
    chi2_null, log_like_null = op.evaluate_model(np.zeros(3))
    assert np.isfinite(chi2_null)
    assert chi2_null > 0.0

    # Under best-fit boost: beta_MO = D_obs / C_EB
    beta_best = op.D_obs / op.C_EB
    chi2_best, log_like_best = op.evaluate_model(beta_best)
    
    assert chi2_best < 1e-10, f"Expected near-zero chi2 at best fit, got {chi2_best}"
    assert log_like_best > log_like_null

