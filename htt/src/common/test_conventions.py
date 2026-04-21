from __future__ import annotations

import numpy as np
import pytest

from common.conventions import gamma_norm2_tensor, gamma_trace, lower_vector, pstf_gamma, raise_vector


def _sample_gamma() -> np.ndarray:
    return np.diag([4.0, 9.0, 16.0]).astype(np.float64)


def test_raise_lower_roundtrip_with_nontrivial_gamma():
    gamma = _sample_gamma()
    v_up = np.array([1.0, -2.0, 3.0], dtype=np.float64)
    np.testing.assert_allclose(raise_vector(lower_vector(v_up, gamma), gamma), v_up)


def test_gamma_trace_matches_explicit_diagonal_metric_formula():
    gamma = _sample_gamma()
    x_ab = np.diag([8.0, 9.0, -16.0]).astype(np.float64)
    expected = 8.0 / 4.0 + 9.0 / 9.0 - 16.0 / 16.0
    assert gamma_trace(x_ab, gamma) == pytest.approx(expected)


def test_gamma_norm_matches_double_raised_explicit_formula():
    gamma = _sample_gamma()
    x_ab = np.diag([8.0, 9.0, -16.0]).astype(np.float64)
    expected = (8.0**2) / (4.0**2) + (9.0**2) / (9.0**2) + ((-16.0) ** 2) / (16.0**2)
    assert gamma_norm2_tensor(x_ab, gamma) == pytest.approx(expected)


def test_pstf_gamma_is_symmetric_and_gamma_trace_free():
    gamma = _sample_gamma()
    x_ab = np.array(
        [[3.0, 2.0, 0.0], [1.0, -4.0, 5.0], [0.0, 5.0, 2.0]],
        dtype=np.float64,
    )
    projected = pstf_gamma(x_ab, gamma)
    np.testing.assert_allclose(projected, projected.T)
    assert gamma_trace(projected, gamma) == pytest.approx(0.0, abs=1.0e-12)


def test_identity_metric_pstf_matches_orthonormal_formula():
    x_ab = np.array(
        [[3.0, 2.0, 0.0], [1.0, -4.0, 5.0], [0.0, 5.0, 2.0]],
        dtype=np.float64,
    )
    sym = 0.5 * (x_ab + x_ab.T)
    expected = sym - np.trace(sym) * np.eye(3, dtype=np.float64) / 3.0
    np.testing.assert_allclose(pstf_gamma(x_ab), expected)


def test_non_symmetric_gamma_is_rejected():
    with pytest.raises(ValueError, match="symmetric"):
        _ = pstf_gamma(np.eye(3), np.array([[1.0, 1.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]))
