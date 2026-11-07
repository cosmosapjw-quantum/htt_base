"""Unit tests for R39 source-bound fail-closed likelihoods."""
from __future__ import annotations

import math
import numpy as np
import pytest

from common.source_bound_likelihoods import (
    DataIntegrityError,
    BaseSourceBoundLikelihood,
    SourceBoundPlanckLikelihood,
    SourceBoundCountsLikelihood,
    SourceBoundGaiaLikelihood,
    SourceBoundDistanceLikelihood,
    SourceBoundDESILikelihood,
    SourceBoundJointLikelihood,
)
from common.kinematic_response import KinematicResponseModel, KinematicFrameState


class DummyProvider:
    def __init__(self, model: KinematicResponseModel):
        self._model = model

    def get_result(self, name: str):
        if name == "kinematic_model":
            return self._model
        raise KeyError(name)


@pytest.fixture
def fiducial_model() -> KinematicResponseModel:
    state = KinematicFrameState(
        beta_RO=np.array([0.0012, -0.0005, 0.0008]),
        beta_RM=np.array([0.0002, -0.0001, 0.0001]),
        beta_MO=np.array([0.0010, -0.0004, 0.0007]),
        d_int=np.zeros(3),
        stf_shear_amplitudes=np.array([1e-5, -1e-5, 2e-6, -1e-6, 3e-6]),
        e1_polar_vector=np.array([1e-4, -2e-4, 5e-5]),
        b1_axial_vector=np.array([5e-5, 1e-4, -5e-5]),
    )
    return KinematicResponseModel(state)


def test_base_likelihood_validation():
    lik = BaseSourceBoundLikelihood()
    # Empty data
    with pytest.raises(DataIntegrityError, match="Data vector is empty"):
        lik.initialize_covariance(np.array([]), np.eye(0), "empty")

    # Shape mismatch
    with pytest.raises(DataIntegrityError, match="does not match data length"):
        lik.initialize_covariance(np.array([1.0, 2.0]), np.eye(3), "mismatch")

    # Non-finite data
    with pytest.raises(DataIntegrityError, match="non-finite"):
        lik.initialize_covariance(np.array([1.0, np.nan]), np.eye(2), "nan")

    # Valid initialization
    d = np.array([1.0, 2.0])
    c = np.eye(2) * 0.5
    lik.initialize_covariance(d, c, "valid")
    assert lik.n_data == 2
    assert lik.L is not None
    assert np.allclose(lik.cov_matrix, c)

    # Compute logp with zero residual -> equal to norm_const
    logp = lik.compute_logp(np.zeros(2))
    assert math.isclose(logp, lik.norm_const)


def test_planck_likelihood(fiducial_model):
    lik = SourceBoundPlanckLikelihood()
    lik.initialize()
    lik.provider = DummyProvider(fiducial_model)
    assert lik.n_data == 10
    assert lik.L is not None
    assert np.all(np.isfinite(lik.data_vector))
    val = lik.logp()
    assert np.isfinite(val)


def test_counts_likelihood(fiducial_model):
    lik = SourceBoundCountsLikelihood()
    lik.initialize()
    lik.provider = DummyProvider(fiducial_model)
    assert lik.n_data == 6
    assert lik.L is not None
    assert np.all(np.isfinite(lik.data_vector))
    val = lik.logp()
    assert np.isfinite(val)


def test_gaia_likelihood(fiducial_model):
    lik = SourceBoundGaiaLikelihood()
    lik.initialize()
    lik.provider = DummyProvider(fiducial_model)
    assert lik.n_data == 11
    assert lik.L is not None
    assert np.all(np.isfinite(lik.data_vector))
    val = lik.logp()
    assert np.isfinite(val)


def test_distance_likelihood(fiducial_model):
    lik = SourceBoundDistanceLikelihood()
    lik.initialize()
    lik.provider = DummyProvider(fiducial_model)
    assert lik.n_data == 490
    assert lik.L is not None
    assert np.all(np.isfinite(lik.data_vector))
    val = lik.logp()
    assert np.isfinite(val)


def test_desi_likelihood(fiducial_model):
    lik = SourceBoundDESILikelihood()
    lik.initialize()
    lik.provider = DummyProvider(fiducial_model)
    assert lik.n_data > 0
    assert lik.L is not None
    assert np.all(np.isfinite(lik.data_vector))
    val = lik.logp()
    assert np.isfinite(val)


def test_joint_likelihood(fiducial_model):
    lik = SourceBoundJointLikelihood()
    lik.initialize()
    lik.provider = DummyProvider(fiducial_model)
    # Total data length: 10 (Planck) + 6 (Counts) + 11 (Gaia) + 490 (Pantheon+) + len(DESI)
    expected_len = 10 + 6 + 11 + 490 + lik.desi.n_data
    assert lik.n_data == expected_len
    assert lik.L is not None
    assert np.all(np.isfinite(lik.data_vector))
    val = lik.logp()
    assert np.isfinite(val)
