"""Tests for conditional Schur information, not physical cosmological validation."""
import numpy as np
import pytest

from obsstat.cf4_schur_information import (
    SchurInformationError, profile_stf_information,
    projected_precision_with_general_covariance,
)
from obsstat.cf4_apparent_kinematic_distribution import weighted_lsq, model_matrix


def _synthetic(seed=19, n=360):
    rng = np.random.default_rng(seed)
    Z = rng.normal(size=(n, 3))
    B = rng.normal(size=(n, 5))
    X = np.column_stack((Z, B))
    s = rng.uniform(.6, 1.7, size=n)
    truth = rng.normal(size=8)
    y = X @ truth + rng.normal(size=n) * s
    return X, y, s


def test_schur_gls_and_joint_qr_agree():
    X, y, s = _synthetic()
    got = profile_stf_information(X, y, s, slice(3, 8))
    reference = weighted_lsq(X, y, s)
    np.testing.assert_allclose(got["beta_full"], reference["beta"], atol=3e-12)
    np.testing.assert_allclose(got["signal_cov"], reference["cov"][3:, 3:], atol=3e-12)
    np.testing.assert_allclose(got["chi2_profiled"], reference["chisq"], atol=5e-10)
    np.testing.assert_allclose(
        got["fisher_profiled"],
        np.linalg.inv(reference["cov"][3:, 3:]), atol=1e-9,
    )
    assert got["signal_rank"] == 5 and got["nuisance_rank"] == 3
    assert np.min(got["relative_information_eigenvalues"]) > 0
    assert np.max(got["relative_information_eigenvalues"]) <= 1 + 1e-12


def test_nuisance_basis_and_data_shift_invariance():
    X, y, s = _synthetic(seed=24)
    rng = np.random.default_rng(111)
    T = np.array([[1.1, .4, -.3], [.0, 1.2, .5], [.2, -.1, .9]])
    rotated = X.copy()
    rotated[:, :3] = X[:, :3] @ T
    base = profile_stf_information(X, y, s, slice(3, 8))
    changed = profile_stf_information(rotated, y + X[:, :3] @ np.array([2., -.7, .9]), s, slice(3, 8))
    for k in ("beta_signal", "signal_cov", "relative_information_eigenvalues", "fisher_profiled"):
        np.testing.assert_allclose(base[k], changed[k], rtol=2e-12, atol=3e-12)


def test_orthogonal_stf_coordinate_change():
    X, y, s = _synthetic(seed=103)
    Q, _ = np.linalg.qr(np.random.default_rng(55).normal(size=(5, 5)))
    new = X.copy()
    new[:, 3:] = X[:, 3:] @ Q
    base = profile_stf_information(X, y, s, slice(3, 8))
    rotated = profile_stf_information(new, y, s, slice(3, 8))
    np.testing.assert_allclose(Q @ rotated["beta_signal"], base["beta_signal"], atol=3e-12)
    np.testing.assert_allclose(
        rotated["relative_information_eigenvalues"],
        base["relative_information_eigenvalues"], atol=2e-12,
    )


def test_rank_loss_rejected_explicitly():
    X, y, s = _synthetic(n=70)
    X[:, -1] = X[:, 0] + 2 * X[:, -2]
    with pytest.raises(SchurInformationError, match="loses rank"):
        profile_stf_information(X, y, s, slice(3, 8))
    with pytest.raises(SchurInformationError, match="zero.*nuisance"):
        profile_stf_information(np.column_stack((X[:, :2], np.zeros(len(y)), X[:, 3:])), y, s, slice(3, 8))


def test_calibration_covariance_in_free_nuisance_span_cancels():
    rng = np.random.default_rng(307)
    n, p = 38, 4
    N = rng.normal(size=(n, p))
    sig = rng.uniform(.7, 2.1, n)
    D = np.diag(sig**2)
    V = rng.normal(size=(p, p))
    K = V @ V.T * .5
    P0 = projected_precision_with_general_covariance(D, N)
    P1 = projected_precision_with_general_covariance(D + N @ K @ N.T, N)
    np.testing.assert_allclose(P0, P1, atol=8e-14, rtol=2e-13)
    # A covariance perturbation outside span(N) is NOT protected.
    u = rng.normal(size=(n, 1))
    P2 = projected_precision_with_general_covariance(D + .3 * u @ u.T, N)
    assert np.linalg.norm(P2 - P0) > 1e-3


def test_actual_cf4_basis_model_synthetic_injection():
    rng = np.random.default_rng(27)
    n = 1000
    unit = rng.normal(size=(n, 3))
    unit /= np.linalg.norm(unit, axis=1)[:, None]
    z = rng.uniform(.012, .095, n)
    method = rng.choice(["FP", "TF", "SN", "OTHER"], n)
    design = model_matrix(z, unit, method, include_method_slope=True)
    X, sl = design["design"], design["slices"]["shear"]
    error = rng.uniform(.2, .4, n)
    target = rng.normal(size=X.shape[1])
    signal = X @ target
    got = profile_stf_information(X, signal, error, sl)
    np.testing.assert_allclose(got["beta_full"], target, atol=1e-8, rtol=2e-8)
    assert got["projected_signal_condition"] < 12
