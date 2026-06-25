"""Contract: the EGS3 graded-comparator view is an additive, bit-identical
upgrade of the signed comparator x (it never changes x or its downstream)."""
from __future__ import annotations

import numpy as np
import pytest

dp_mod = pytest.importorskip("htt.core.departure_posteriors")
DeparturePosterior = dp_mod.DeparturePosterior


def _posterior(seed=0, n=2000):
    rng = np.random.default_rng(seed)
    beta = rng.uniform(0.0, 2e-3, n)
    sigma2 = rng.uniform(0.0, 5e-6, n)
    w2 = rng.uniform(0.0, 5e-6, n)
    omega_k = rng.normal(0.0, 1e-6, n)
    samples = np.column_stack([beta, sigma2, w2, omega_k])
    return DeparturePosterior("FLRW_tilt", samples,
                              param_names=["beta", "Sigma2", "W2", "Omega_k"])


def test_graded_view_reconstructs_x_bit_identically():
    dp = _posterior()
    x = dp.compute_x()
    g = dp.compute_graded_comparator()
    x_from_g = g["Sigma2"] - g["W2"] + g["Omega_tilt"] + g["Omega_k_aniso"]
    assert np.array_equal(x_from_g, x)            # bit-identical, not just close
    assert set(g) == set(DeparturePosterior.GRADED_SECTORS)


def test_graded_view_keeps_sector_identity_under_cancellation():
    # construct a sample where Sigma2 == W2 so x cancels in those sectors;
    # the graded view must still expose both nonzero.
    samples = np.array([[1e-3, 3e-6, 3e-6, 0.0]])
    dp = DeparturePosterior("FLRW_tilt", samples,
                            param_names=["beta", "Sigma2", "W2", "Omega_k"])
    dp.compute_x()
    g = dp.compute_graded_comparator()
    assert g["Sigma2"][0] > 0.0 and g["W2"][0] > 0.0   # both visible
    # their contribution to x cancels, but the sectors are individually retained
    assert abs(g["Sigma2"][0] - g["W2"][0]) < 1e-18


def test_graded_view_does_not_mutate_x():
    dp = _posterior(seed=3)
    x_before = dp.compute_x().copy()
    dp.compute_graded_comparator()
    assert np.array_equal(dp.x, x_before)
