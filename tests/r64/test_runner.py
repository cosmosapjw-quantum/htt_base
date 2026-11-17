"""Meaningful checks for the newly introduced correlated-window prediction."""
import sys
from pathlib import Path

import numpy as np
from scipy import linalg

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/r64"))
from run_r64_directional_hubble import conditional_holdout, nested_angular_null
from htt.htt.infer import r58_mixed_tensor_likelihood as mt


def test_holdout_covariance_matches_full_observation_error_operator():
    rng = np.random.default_rng(3184)
    n, p = 14, 4
    a = rng.normal(size=(n, n))
    cov = a @ a.T + np.eye(n)
    x = rng.normal(size=(n, p))
    y = rng.normal(size=n)
    held = np.array([1, 4, 9])
    train = np.setdiff1d(np.arange(n), held)
    got = conditional_holdout(y, cov, x, held, np.ones(p), mt.fit_linear)
    ct = cov[np.ix_(train, train)]
    invcx = linalg.solve(ct, x[train], assume_a="pos")
    gain = linalg.solve(x[train].T @ invcx, invcx.T, assume_a="pos")
    aht = linalg.solve(ct, cov[np.ix_(train, held)], assume_a="pos").T
    error_op = np.eye(n)[held] - (aht + (x[held]-aht@x[train])@gain) @ np.eye(n)[train]
    np.testing.assert_allclose(got["predictive_covariance"], error_op@cov@error_op.T, rtol=2e-12, atol=2e-12)
    np.testing.assert_allclose(got["error"], error_op@y, rtol=2e-12, atol=2e-12)
    np.testing.assert_allclose(error_op@x, 0., atol=2e-12)


def test_holdout_rejects_an_unidentified_training_prediction():
    x = np.column_stack((np.ones(6), np.r_[np.zeros(5), 1.]))
    got = conditional_holdout(np.arange(6.), np.eye(6), x, [5], np.ones(2), mt.fit_linear)
    assert got["status"] == "UNIDENTIFIED_PREDICTION"


def test_nested_angular_null_preserves_monopole_and_constant_angular_nuisance():
    rng = np.random.default_rng(782)
    x = rng.normal(size=(36, 21))
    cov = np.eye(36)
    theta = np.zeros(21)
    theta[:13] = rng.normal(size=13)
    y = x @ theta
    fit = mt.fit_linear(y, cov, x)
    null = nested_angular_null(y, cov, x, 1, np.ones(21), fit, mt.fit_linear)
    assert null["df"] == 8
    assert null["delta_chi2"] < 1e-22
    assert null["nominal_p"] > .999999


def test_nested_radial_angular_test_matches_known_orthogonal_coordinates():
    x = np.eye(36)[:, :21]
    theta = np.zeros(21)
    theta[13:] = np.arange(1., 9.)
    y = x @ theta
    fit = mt.fit_linear(y, np.eye(36), x)
    got = nested_angular_null(y, np.eye(36), x, 1, np.ones(21), fit, mt.fit_linear)
    np.testing.assert_allclose(got["delta_chi2"], np.sum(np.arange(1., 9.)**2), rtol=1e-14)
