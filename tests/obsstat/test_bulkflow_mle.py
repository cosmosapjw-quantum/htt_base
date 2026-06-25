from __future__ import annotations

import numpy as np
import pytest

from obsstat.bulkflow_mle import (
    estimate_bulk_flow, velocity_error, forward_mock_coverage, fit_sigma_star,
)


def _isotropic_dirs(n, seed=0):
    rng = np.random.default_rng(seed)
    v = rng.normal(size=(n, 3))
    return v / np.linalg.norm(v, axis=1)[:, None]


def test_recovers_injected_bulk_flow():
    n = _isotropic_dirs(4000, seed=1)
    B_true = np.array([300.0, -120.0, 80.0])
    rng = np.random.default_rng(2)
    sigma = np.full(n.shape[0], 200.0)
    vpec = n @ B_true + rng.normal(0, sigma)
    bf = estimate_bulk_flow(n, vpec, sigma, sigma_star=0.0)
    assert np.allclose(bf.vector, B_true, atol=25.0)
    assert bf.amplitude == pytest.approx(np.linalg.norm(B_true), abs=25.0)


def test_velocity_error_scaling():
    # 0.4 mag distance-modulus error at 5000 km/s -> ~ (ln10/5)*0.4*5000.
    err = velocity_error(np.array([0.4]), np.array([5000.0]))
    assert err[0] == pytest.approx(np.log(10) / 5 * 0.4 * 5000.0, rel=1e-6)


def test_forward_mock_coverage_near_68():
    n = _isotropic_dirs(2000, seed=3)
    sigma = np.full(n.shape[0], 250.0)
    cov = forward_mock_coverage(n, sigma, np.array([250.0, 0.0, 0.0]), sigma_star=0.0, n_mock=300, seed=4)
    assert 0.55 <= cov["one_sigma_coverage"] <= 0.80


def test_fit_sigma_star_returns_value_in_grid():
    n = _isotropic_dirs(1500, seed=5)
    rng = np.random.default_rng(6)
    sigma = np.full(n.shape[0], 150.0)
    vpec = n @ np.array([200.0, 0, 0]) + rng.normal(0, np.sqrt(150.0 ** 2 + 300.0 ** 2), n.shape[0])
    ss = fit_sigma_star(n, vpec, sigma)
    assert 50.0 <= ss <= 600.0
