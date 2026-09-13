import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest


MODULE = Path(__file__).parents[1] / "cf3_sdss_calibration_candidate.py"
spec = importlib.util.spec_from_file_location("candidate", MODULE)
candidate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = candidate
spec.loader.exec_module(candidate)


def test_shared_cross_terms_are_preserved():
    # Common SDSS/CF3 calibration noise makes the two pair differences exact.
    # A diagonal fallback would invent a positive error here.
    values = np.array([0.1, 0.2, 0.1, 0.2])
    shared = np.array([[0.04, 0.01], [0.01, 0.09]])
    covariance = np.block([[shared, shared], [shared, shared]])
    with pytest.raises(ValueError, match="singular"):
        candidate.calibrate_shared_offset(values[:2], values[2:], covariance)


def test_group_zero_is_not_a_common_group_and_cross_terms_transform():
    consensus = candidate.group_consensus_operator([7, 7, 0], [.1, .2, .1])
    assert consensus.shape == (2, 3)
    assert np.allclose(consensus[1], [0, 0, 1])
    # Full covariance has a nonzero SDSS--CF3 block.  The estimate must use it.
    joint = np.eye(6) * .04
    joint[:3, 3:] = joint[3:, :3] = np.eye(3) * .01
    result = candidate.calibrate_shared_offset([.01, .03, -.02], [.00, .02, -.01], joint,
                                                consensus_operator=consensus)
    assert result.difference_operator.shape == (2, 6)
    assert np.isfinite(result.offset_cf3_minus_sdss_dex)
    assert result.standard_error_dex > 0


def test_covariance_is_required_not_constructed_from_errors():
    with pytest.raises(ValueError, match="joint covariance"):
        candidate.calibrate_shared_offset([0.0], [0.0], np.eye(1))


def test_indefinite_joint_covariance_is_rejected_even_if_normalizer_is_positive():
    indefinite = np.diag([1., 1., 1., -0.01])
    with pytest.raises(ValueError, match="positive semidefinite"):
        candidate.calibrate_shared_offset([0., 0.], [0., 0.], indefinite)


def test_invalid_group_ids_and_zero_redshift_are_rejected():
    with pytest.raises(ValueError, match="non-negative integers"):
        candidate.group_consensus_operator([1, -1], [.1, .1])
    with pytest.raises(ValueError, match="redshifts"):
        candidate.cf3_eta_from_distance_modulus(np.array([31.]), np.array([0.]))
    with pytest.raises(ValueError, match="cosmology"):
        candidate.flat_comoving_distance_mpc(np.array([.01]), h0_km_s_mpc=np.nan)


def test_depth_operator_keeps_level_and_cancels_shared_shift_in_contrast():
    covariance = np.eye(4) * .04
    coefficients = candidate.shared_offset_coefficients(covariance, n_rows=2)
    projection = np.array([[1., 1.], [1., -1.]])
    operator = candidate.depth_calibration_operator(projection, coefficients, n_sdss_rows=2)
    # The first row is an anchored level and receives a shared offset.  The
    # contrast row sums to zero and therefore has no CF3 dependence.
    assert not np.allclose(operator[0, 2:], 0.)
    assert np.allclose(operator[1], [1., -1., 0., 0.])
