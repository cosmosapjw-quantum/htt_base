"""R54-L02 PR4-bypass helpers (htt/htt/htt/infer/r54_pr4_bypass.py).

The analytic T covariance (step 1), the Wishart LRT (step 2), the low-resolution E/B estimator used for WMAP9 and the
posterior zero tail used for BeyondPlanck (step 5) are checked against exact synthetic cases.
"""
from __future__ import annotations

import math

import healpy as hp
import numpy as np
import pytest

from htt.htt.infer import r54_pr4_bypass as pb


def test_full_sky_t_response_is_identity_inside_the_band_and_zero_outside():
    r, ells = pb.t_response_matrix(np.ones(hp.nside2npix(32)), 32, 10, np.eye(45), pb.mode_tuples(6, 2))
    assert r.shape == (45, 117) and ells.min() == 2 and ells.max() == 10
    assert np.abs(r[:, :45] - np.eye(45)).max() < 2e-3 and np.abs(r[:, 45:]).max() < 2e-3


def test_analytic_covariance_and_wishart_lrt():
    r = np.eye(3)
    c = pb.analytic_covariance(r, np.array([2, 3, 4]), lambda e: 1.0 / e, noise=0.1 * np.eye(3))
    assert np.allclose(np.diag(c), [0.6, 1.0 / 3.0 + 0.1, 0.35])
    with pytest.raises(ValueError):
        pb.analytic_covariance(r, np.array([2, 3, 4]), lambda e: -np.ones(3))
    rng = np.random.default_rng(20261116)
    s = np.cov((rng.normal(size=(300, 4)) * [1.0, 2.0, 1.0, 1.0]).T)
    good = pb.wishart_lrt(np.diag([1.0, 4.0, 1.0, 1.0]), s, 299)
    bad = pb.wishart_lrt(np.eye(4), s, 299)
    assert good["dof"] == 10 and good["p_value"] > 1e-3 and bad["p_value"] < 1e-10
    assert math.isclose(pb.wishart_lrt(s, s, 299)["statistic"], 0.0, abs_tol=1e-9)


def test_masked_eb_estimator_recovers_band_limited_e_and_b():
    modes = pb.mode_tuples(6, 2)
    rng = np.random.default_rng(1)
    x = rng.normal(size=90)
    ae = sum(x[j] * pb.unit_alm(6, *mode) for j, mode in enumerate(modes))
    ab = sum(x[45 + j] * pb.unit_alm(6, *mode) for j, mode in enumerate(modes))
    _, q, u = hp.alm2map([0 * ae, ae, ab], 16, lmax=6, pol=True)
    theta = hp.pix2ang(16, np.arange(hp.nside2npix(16)))[0]
    mask = (np.abs(theta - np.pi / 2) > 0.3).astype(float)
    k = pb.eb_operator(mask, 16)
    assert np.abs(pb.extract_eb(q, u, mask, k) - x).max() < 1e-10
    with pytest.raises(ValueError):
        pb.eb_operator(np.zeros(hp.nside2npix(16)), 16)


def test_posterior_zero_tail_is_basis_invariant():
    rng = np.random.default_rng(2)
    s = rng.normal(size=(2000, 5)) + np.array([0.3, 0.0, 0.0, 0.0, 0.0])
    a = rng.normal(size=(5, 5))
    t1, t2 = pb.posterior_zero_tail(s), pb.posterior_zero_tail(s @ a.T)
    assert t1["n_exceed"] == t2["n_exceed"] and math.isclose(t1["statistic"], t2["statistic"], rel_tol=1e-8)
    assert pb.posterior_zero_tail(s + 5.0)["p_value"] < 1e-3
    with pytest.raises(ValueError):
        pb.posterior_zero_tail(s[:10])
