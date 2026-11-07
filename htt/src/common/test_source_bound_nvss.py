"""Tests for source-bound NVSS radio count dipole operator."""

import os
import pytest
import numpy as np

from common.source_bound_nvss_operator import SourceBoundNVSSOperator, NVSS_CAT_PATH


@pytest.mark.skipif(not os.path.exists(NVSS_CAT_PATH), reason="NVSS catalog not on disk")
def test_nvss_operator_initialization():
    op = SourceBoundNVSSOperator(s_min_mjy=20.0, b_cut_deg=10.0)
    assert op.n_sources > 300000
    assert op.n_selected > 250000
    assert op.D_obs.shape == (3,)
    # Measured dipole amplitude is around 0.015 - 0.020 (consistent with Blake & Wall 2002)
    assert 0.010 <= op.amp_obs <= 0.025


@pytest.mark.skipif(not os.path.exists(NVSS_CAT_PATH), reason="NVSS catalog not on disk")
def test_nvss_operator_evaluations():
    op = SourceBoundNVSSOperator(s_min_mjy=20.0, b_cut_deg=10.0)
    chi2_0, loglike_0 = op.evaluate_model(np.zeros(3))
    assert chi2_0 > 0.0
    assert np.isfinite(loglike_0)

    # Best-fit beta reduces chi2 to near 0
    beta_best = op.D_obs / op.C_EB
    chi2_best, loglike_best = op.evaluate_model(beta_best)
    assert chi2_best < 0.1
    assert loglike_best > loglike_0

