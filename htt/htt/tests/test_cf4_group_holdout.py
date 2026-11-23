"""Tests for SQ-CF4 group-blocked holdout, probit Fisher uncertainty, and component tangents."""
from __future__ import annotations

import numpy as np
from numpy.testing import assert_allclose
import pytest

from htt.infer.cf4_group_holdout import (
    build_group_clusters,
    cluster_bootstrap_probit,
    component_covariance_tangents,
    fit_probit_with_hessian,
    group_kfold_indices,
    selected_probit_uncertainty_propagation,
    sixdf_match_ambiguity_policies,
)
from htt.infer.cf4_predictive_response import predictive_contrasts, selected_probit_field_response


def test_fit_probit_hessian_matches_fd_and_laplace_cov() -> None:
    rng = np.random.default_rng(7)
    n, p = 400, 4
    X = np.column_stack((np.ones(n), rng.normal(size=(n, p - 1))))
    beta_true = np.array([0.7, -0.35, -0.8, 0.25])
    probs = 0.5 * (1.0 + np.tanh(0.0))  # placeholder unused
    del probs
    from scipy.special import ndtr

    y = (rng.uniform(size=n) < ndtr(X @ beta_true)).astype(np.int64)
    fit = fit_probit_with_hessian(X, y)
    assert fit.converged
    assert fit.grad_norm < 1e-8

    # Check analytical gradient=0 at MLE and numerical Hessian via analytical gradient FD
    sign = np.where(y > 0, 1.0, -1.0)

    def grad_neg_ll(b: np.ndarray) -> np.ndarray:
        z = sign * (X @ b)
        from htt.infer.cf4_group_holdout import _inverse_mills_stable

        return -((sign * _inverse_mills_stable(z)) @ X)

    eps = 1e-6
    H_fd = np.zeros((p, p), dtype=np.float64)
    for j in range(p):
        ej = np.zeros(p)
        ej[j] = eps
        H_fd[:, j] = (grad_neg_ll(fit.beta_hat + ej) - grad_neg_ll(fit.beta_hat - ej)) / (2.0 * eps)
    assert_allclose(fit.hessian, H_fd, rtol=1e-7, atol=1e-7)
    assert_allclose(fit.cov_laplace @ fit.hessian, np.eye(p), atol=1e-10)

    # Also test cluster_bootstrap_probit returns PD cov
    clusters = build_group_clusters(np.r_[np.full(200, -1), np.repeat(np.arange(1, 51), 4)])
    boot = cluster_bootstrap_probit(X, y, clusters, n_boot=15, seed=9)
    assert boot["cov_cluster_bootstrap"].shape == (p, p)
    assert np.all(np.linalg.eigvalsh(boot["cov_cluster_bootstrap"]) > 0.0)


def test_group_clusters_sentinels_and_zero_leakage_kfold() -> None:
    # 6dFGSv sentinel (-1) and SDSS sentinel (0) must NOT cluster together
    gids = np.array([-1, -1, 0, 0, 10, 10, 10, 20, 20, 30, 40, 50])
    # Add secondary linkage bridging index 1 (sentinel -1) with group 20 via shared table2 PGC
    sec = np.array([-1, 777, 0, 0, 0, 0, 0, 777, 888, 0, 0, 0])
    clusters = build_group_clusters(gids, secondary_keys=sec)
    # Index 0, 2, 3 remain distinct singletons; 1 is linked with indices 7 and 8!
    assert len({int(clusters[0]), int(clusters[2]), int(clusters[3])}) == 3
    assert clusters[1] == clusters[7] == clusters[8]
    assert clusters[4] == clusters[5] == clusters[6]

    splits = group_kfold_indices(clusters, n_splits=5, seed=123)
    seen_test = []
    for tr, te in splits:
        assert len(np.intersect1d(clusters[tr], clusters[te])) == 0
        seen_test.append(te)
    assert_allclose(np.sort(np.concatenate(seen_test)), np.arange(len(gids)))


@pytest.mark.parametrize("with_rejected", [False, True])
def test_selected_probit_uncertainty_grad_matches_fd(with_rejected: bool) -> None:
    rng = np.random.default_rng(19)
    n = 35
    X = np.column_stack((np.ones(n), rng.normal(scale=0.3, size=n), rng.normal(size=n), rng.integers(0, 2, size=n)))
    beta_hat = np.array([0.85, -0.18, -0.95, 0.21])
    beta_cov = 1e-3 * (np.eye(4) + 0.1 * np.ones((4, 4)))
    sig = rng.uniform(0.05, 0.12, size=n)
    mark = rng.normal(0.0, 0.09, size=n)
    means = rng.normal(0.0, 0.04, size=(5, n))
    probs = np.full(5, 0.2)
    inc = None if not with_rejected else (rng.uniform(size=n) > 0.25)
    if inc is not None:
        mark = np.where(inc, mark, np.nan)

    prop = selected_probit_uncertainty_propagation(
        mark, means, sig, X, beta_hat, beta_cov, probs, included=inc, mark_col=2, n_mc=64, seed=55
    )

    def eval_mix_and_contrast(b: np.ndarray) -> tuple[float, float]:
        a = b[0] + b[1] * X[:, 1] + b[3] * X[:, 3]
        sl = float(b[2])
        m = selected_probit_field_response(mark, means, sig, a, sl, probs, included=inc)["log_density"]
        z = selected_probit_field_response(mark, np.zeros((1, n)), sig, a, sl, [1.0], included=inc)["log_density"]
        return float(m), float(m - z)

    eps = 1e-6
    fd_mix = np.zeros(4)
    fd_con = np.zeros(4)
    for j in range(4):
        ej = np.zeros(4)
        ej[j] = eps
        mp, cp = eval_mix_and_contrast(beta_hat + ej)
        mm, cm = eval_mix_and_contrast(beta_hat - ej)
        fd_mix[j] = (mp - mm) / (2.0 * eps)
        fd_con[j] = (cp - cm) / (2.0 * eps)

    assert_allclose(prop["grad_beta_mix"], fd_mix, rtol=1e-7, atol=1e-8)
    assert_allclose(prop["grad_beta_mix_minus_zero"], fd_con, rtol=1e-7, atol=1e-8)
    assert prop["delta_method_var_mix_minus_zero"] >= 0.0
    assert np.isfinite(prop["marginalized_log_density_mix_minus_zero"])


def test_component_covariance_tangents_euler_homogeneity() -> None:
    rng = np.random.default_rng(101)
    n, m, p = 18, 18, 9
    x = rng.normal(size=(n, p))
    h = rng.normal(size=(m, p))
    y = rng.normal(size=n + m)
    contrasts = predictive_contrasts(x, h)

    comps = {}
    for name in ("diag", "cal", "spv_low", "spv_high"):
        a = rng.normal(size=(n + m, n + m))
        comps[name] = (a @ a.T) / (n + m) + 0.05 * np.eye(n + m)

    out = component_covariance_tangents(y, comps, contrasts)
    assert out["euler_homogeneity_errors"]["max"] < 1e-11


def test_sixdf_ambiguity_policy_logic() -> None:
    table2 = {
        "ra": np.array([10.0, 20.0, 20.001]),
        "dec": np.array([-10.0, -20.0, -20.001]),
        "vcmb": np.array([5000.0, 6000.0, 6050.0]),
        "pgc": np.array([101, 202, 203]),
    }
    sixdf = {
        "ra": np.array([10.0, 20.0001, 50.0]),
        "dec": np.array([-10.0, -20.0001, -30.0]),
        "cz_gal": np.array([5010.0, 6002.0, 7000.0]),
    }
    res = sixdf_match_ambiguity_policies(table2, sixdf, arcsec=15.0, dv_kms=500.0)
    assert res["multiplicity_histogram"] == {0: 1, 1: 1, 2: 1}
    assert len(res["ambiguous_rows"]) == 1
    assert res["policies"]["unique_only_r101"]["included"].tolist() == [True, False, False]
    assert res["policies"]["resolve_closest"]["included"].tolist() == [True, True, False]
    assert res["policies"]["exclude_ambiguous"]["keep"].tolist() == [True, False, True]
