"""R54 local calibration helpers (htt/htt/htt/infer/r54_calibration.py): gates MG-L01, MG-L02, MG-L03.

MG-L01  the covariance identity of R54-L01 step 1 passes for a row permutation and fails for a column permutation;
MG-L02  leave-one-out replicates obey the Hotelling law; sims[i] inside its own covariance leaves the coverage band;
MG-L03  an empirical null refuses fewer than 30 realisations (a single split difference is never a null law).
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from htt.htt.infer import r54_calibration as cal


def test_mg_l01_covariance_identity_detects_column_but_not_row_permutation():
    rng = np.random.default_rng(20261116)
    sims = rng.normal(size=(300, 12)) * np.linspace(1.0, 3.0, 12)
    s_ref = np.cov(sims.T, ddof=1)
    assert cal.covariance_identity_rel(sims, s_ref) <= 1e-10
    assert cal.covariance_identity_rel(sims[rng.permutation(300)], s_ref) <= 1e-10
    assert cal.covariance_identity_rel(sims[:, rng.permutation(12)], s_ref) > 1e-3
    with pytest.raises(ValueError):
        cal.covariance_identity_rel(sims, s_ref[:-1, :-1])


def test_mg_l02_leave_one_out_obeys_the_hotelling_law_and_self_inclusion_does_not():
    """50 synthetic Gaussian sets with N = 60, p = k = 10 (square response): pooled coverage of the Hotelling 95% region."""
    rng = np.random.default_rng([20261116, 21])
    j = np.eye(10)
    loo, self_incl = [], []
    for _ in range(50):
        sims = rng.normal(size=(60, 10))
        loo.append(cal.wald_coverage(cal.loo_replicates(sims, j), 0.95))
        self_incl.append(cal.wald_coverage(cal.loo_replicates(sims, j, leave_one_out=False), 0.95))
    lo, hi = cal.binomial_band(0.95, 50 * 60)
    assert lo <= float(np.mean(loo)) <= hi
    assert not lo <= float(np.mean(self_incl)) <= hi


def test_coverage_and_empirical_quantile_inflation():
    rng = np.random.default_rng(3)
    theta = rng.normal(size=(20000, 2)) * np.array([1.0, 2.0])
    sd = np.ones_like(theta)
    cov = cal.coverage(theta, sd, 1.0, 0.95)
    assert abs(cov[0] - 0.95) < 0.006 and cov[1] < 0.75
    q = cal.empirical_quantile_inflation(theta, sd, 0.95)
    assert np.allclose(q, [1.0, 2.0], rtol=0.03)
    assert np.allclose(cal.coverage(theta, sd * q, 1.0, 0.95), 0.95, atol=1e-3)
    lo, hi = cal.binomial_band(0.95, 300)
    assert math.isclose(lo, 0.95 - 3.0 * math.sqrt(0.95 * 0.05 / 300)) and hi > 0.95


def test_mg_l03_empirical_null_refuses_a_single_split_difference():
    with pytest.raises(ValueError):
        cal.EmpiricalNull(np.array([3.2]), "one half-mission difference")
    with pytest.raises(ValueError):
        cal.EmpiricalNull(np.arange(29.0), "29 realisations")
    with pytest.raises(ValueError):
        cal.EmpiricalNull(np.arange(40.0), " ")
    tail = cal.EmpiricalNull(np.arange(40.0), "toy law").upper_tail(35.0)
    assert tail["n_exceed"] == 5 and math.isclose(tail["p_value"], 6.0 / 41.0) and tail["law"] == "toy law"


def test_loo_replicates_fail_closed():
    with pytest.raises(ValueError):
        cal.loo_replicates(np.zeros((10, 10)), np.eye(10))
    with pytest.raises(ValueError):
        cal.loo_replicates(np.zeros((50, 4)), np.eye(3))
