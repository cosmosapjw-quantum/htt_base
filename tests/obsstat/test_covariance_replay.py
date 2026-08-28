from __future__ import annotations

import numpy as np
import pytest

from obsstat.covariance_replay import (
    CovarianceReplayError,
    fsum_sample_covariance,
    validate_sample_covariance_replay,
)


def _rows() -> np.ndarray:
    rng = np.random.default_rng(315)
    matrix = rng.normal(size=(300, 12))
    matrix[:, 1] += 0.15 * matrix[:, 0]
    matrix[:, 5] -= 0.07 * matrix[:, 3]
    return matrix


def test_numpy_covariance_is_numerically_equivalent_to_fsum_reference() -> None:
    rows = _rows()
    stored = np.cov(rows, rowvar=False, ddof=1)
    report = validate_sample_covariance_replay(
        stored_covariance=stored,
        rows=rows,
    )
    assert report["state"] == "NUMERICALLY_EQUIVALENT"
    assert report["symmetric"] is True
    assert report["positive_semidefinite"] is True
    assert report["max_forward_error_ratio"] <= 1.0


def test_one_ulp_symmetric_variation_remains_equivalent() -> None:
    rows = _rows()
    stored = np.cov(rows, rowvar=False, ddof=1)
    varied = stored.copy()
    varied[2, 7] = np.nextafter(varied[2, 7], np.inf)
    varied[7, 2] = varied[2, 7]
    report = validate_sample_covariance_replay(
        stored_covariance=varied,
        rows=rows,
    )
    assert report["state"] == "NUMERICALLY_EQUIVALENT"


def test_material_covariance_change_fails_closed() -> None:
    rows = _rows()
    stored = np.cov(rows, rowvar=False, ddof=1)
    stored[4, 4] += 1.0e-6
    with pytest.raises(CovarianceReplayError, match="forward-error"):
        validate_sample_covariance_replay(
            stored_covariance=stored,
            rows=rows,
        )


def test_asymmetry_and_indefiniteness_fail_closed() -> None:
    rows = _rows()
    stored = np.cov(rows, rowvar=False, ddof=1)
    asymmetric = stored.copy()
    asymmetric[0, 1] += 1.0e-8
    with pytest.raises(CovarianceReplayError, match="symmetric"):
        validate_sample_covariance_replay(
            stored_covariance=asymmetric,
            rows=rows,
        )
    indefinite = stored.copy()
    indefinite[0, 0] = -10.0
    with pytest.raises(CovarianceReplayError, match="positive semidefinite"):
        validate_sample_covariance_replay(
            stored_covariance=indefinite,
            rows=rows,
        )


def test_fsum_reference_is_exactly_symmetric_and_dimension_checked() -> None:
    reference, scale = fsum_sample_covariance(_rows())
    assert np.array_equal(reference, reference.T)
    assert np.array_equal(scale, scale.T)
    with pytest.raises(CovarianceReplayError, match="two-dimensional"):
        fsum_sample_covariance(np.zeros(12))
