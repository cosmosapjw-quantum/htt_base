"""Unit tests for SourceBoundPlanckLowEllOperator."""

import os
import pytest
import numpy as np

from common.source_bound_planck_lowell_operator import (
    SourceBoundPlanckLowEllOperator,
    PLANCK_OBS_PATH,
    EXPECTED_PLANCK_OBS_SHA256,
)
from common.source_bound_pantheon_operator import verify_file_sha256


@pytest.mark.skipif(not os.path.exists(PLANCK_OBS_PATH), reason="Planck observed carrier not found")
def test_planck_file_hash():
    """Verify authoritative SHA-256 hash of Planck observed carrier file."""
    assert verify_file_sha256(PLANCK_OBS_PATH, EXPECTED_PLANCK_OBS_SHA256)


@pytest.mark.skipif(not os.path.exists(PLANCK_OBS_PATH), reason="Planck observed carrier not found")
def test_planck_operator_initialization():
    """Verify initialization, MC count, and positive-definiteness of empirical covariance."""
    op = SourceBoundPlanckLowEllOperator(verify_sha=False)
    assert op.n_modes == 10
    assert op.n_mc >= 10
    assert op.cov.shape == (10, 10)

    # Check positive definiteness
    evals = np.linalg.eigvalsh(op.cov)
    assert np.all(evals > 0), "Planck empirical covariance must be positive definite"
    assert np.linalg.cond(op.cov) < 100.0, "Covariance conditioning must be well-behaved"

    # Reduced chi2 under null hypothesis (H0) should be physically plausible (~ 1.0)
    assert 0.5 < op.chi2_null / 10.0 < 2.5, f"Unexpected chi2_null: {op.chi2_null}"


@pytest.mark.skipif(not os.path.exists(PLANCK_OBS_PATH), reason="Planck observed carrier not found")
def test_planck_operator_evaluation():
    """Verify model evaluation under zero state vs predicted modes."""
    op = SourceBoundPlanckLowEllOperator(verify_sha=False)

    # Null hypothesis
    theta_zero = np.zeros(17, dtype=np.float64)
    chi2_zero, logl_zero = op.evaluate_model(theta_zero)
    assert np.isclose(chi2_zero, op.chi2_null)

    # Exact match evaluation
    chi2_exact, logl_exact = op.evaluate_modes(op.d_obs)
    assert np.isclose(chi2_exact, 0.0)
    assert logl_exact > logl_zero
