from __future__ import annotations

import numpy as np
import pytest

from obsstat.affine_flow import (
    decompose_gradient, fit_affine_flow, curl_injection_recovery,
)


def test_decompose_pure_expansion():
    M = np.eye(3) * 2.0
    theta, shear, w = decompose_gradient(M)
    assert theta == pytest.approx(6.0)
    assert np.allclose(shear, 0.0)
    assert np.allclose(w, 0.0)


def test_decompose_pure_rotation():
    # antisymmetric M -> zero expansion, zero shear, axial vector = curl/2.
    M = np.array([[0.0, -3.0, 0.0], [3.0, 0.0, 0.0], [0.0, 0.0, 0.0]])
    theta, shear, w = decompose_gradient(M)
    assert theta == pytest.approx(0.0)
    assert np.allclose(shear, 0.0)
    assert np.allclose(w, [0.0, 0.0, 3.0])


def test_affine_fit_recovers_known_flow():
    rng = np.random.default_rng(0)
    pos = rng.normal(size=(2000, 3)) * 50.0
    B = np.array([100.0, -50.0, 25.0])
    M = np.array([[1.0, 0.5, 0.0], [-0.5, 2.0, 0.3], [0.0, 0.3, -1.0]])
    vel = B + pos @ M.T
    fit = fit_affine_flow(pos, vel)
    assert np.allclose(fit.bulk, B, atol=1e-6)
    assert np.allclose(fit.gradient, M, atol=1e-6)
    assert fit.expansion == pytest.approx(np.trace(M), abs=1e-6)


def test_curl_injection_recovery_exact():
    rng = np.random.default_rng(1)
    pos = rng.normal(size=(3000, 3)) * 80.0
    vel = rng.normal(size=(3000, 3)) * 100.0
    out = curl_injection_recovery(pos, vel, radius=200.0, omega_inject=np.array([0.2, -0.4, 1.1]))
    assert out["rel_error"] < 1e-10


def test_fit_requires_enough_cells():
    with pytest.raises(ValueError):
        fit_affine_flow(np.zeros((3, 3)), np.zeros((3, 3)))
