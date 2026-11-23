"""Group-blocked CF4 holdout, selection uncertainty propagation, and component covariance tangents.

Implements:
- Numerically stable probit MLE with exact analytical gradient, observed negative
  Hessian, and Laplace parameter covariance.
- Union-find galaxy/group clustering respecting catalog sentinels (6dFGSv ``-1``
  and SDSS ``0`` ungrouped singletons) and balanced group-blocked K-fold splits
  with strict zero-leakage assertions.
- Analytical delta-method gradient & variance plus Laplace-Gaussian MC
  marginalization over selection parameter uncertainty in
  ``selected_probit_field_response``.
- 6dFGSv -> CF4 Table-2 multi-match ambiguity policies and Euler-homogeneous
  component-wise predictive covariance tangents.

Scientific boundary: all outputs remain source-conditional diagnostics on already
released catalogs (`source_qualification="BLOCKED_INPUT"`).
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence

import numpy as np
from scipy.spatial import cKDTree
from scipy.special import log_ndtr, logsumexp
from scipy.stats import norm

from htt.infer.cf4_predictive_response import (
    PredictiveContrasts,
    predictive_covariance_response,
    selected_probit_field_response,
)

__all__ = [
    "ProbitFitResult",
    "build_group_clusters",
    "cluster_bootstrap_probit",
    "component_covariance_tangents",
    "fit_probit_with_hessian",
    "group_kfold_indices",
    "selected_probit_uncertainty_propagation",
    "sixdf_match_ambiguity_policies",
]

_LOG_SQRT_2PI = 0.5 * math.log(2.0 * math.pi)


def _inverse_mills_stable(z: np.ndarray) -> np.ndarray:
    """Compute phi(z) / Phi(z) stably across all real inputs."""
    t = np.asarray(z, dtype=np.float64)
    out = np.empty_like(t, dtype=np.float64)
    mid = t > -20.0
    if np.any(mid):
        tm = t[mid]
        log_phi = -0.5 * tm * tm - _LOG_SQRT_2PI
        out[mid] = np.exp(log_phi - log_ndtr(tm))
    tail = ~mid
    if np.any(tail):
        x = -t[tail]
        # Continued fraction tail for phi(z)/Phi(z) = x + 1/(x + 2/(x + 3/(x + 4/...)))
        cf = x + 6.0 / x
        for k in (5.0, 4.0, 3.0, 2.0, 1.0):
            cf = x + k / cf
        out[tail] = cf
    return out


def _probit_mills_and_weight(z: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return (lambda(z), w(z)) where w(z) = -d^2/dz^2 log Phi(z) = lambda*(z+lambda) in (0,1)."""
    t = np.asarray(z, dtype=np.float64)
    lam = _inverse_mills_stable(t)
    w = np.empty_like(t, dtype=np.float64)
    mid = t > -20.0
    if np.any(mid):
        wm = lam[mid] * (t[mid] + lam[mid])
        w[mid] = np.clip(wm, 1e-300, 1.0)
    tail = ~mid
    if np.any(tail):
        # Since lam = -t + r with r = 1/(x + 2/(x + 3/...)), z + lam = r strictly > 0.
        x = -t[tail]
        cf_tail = 6.0 / x
        for k in (5.0, 4.0, 3.0, 2.0):
            cf_tail = k / (x + cf_tail)
        r = 1.0 / (x + cf_tail)
        w[tail] = np.clip(lam[tail] * r, 0.0, 1.0)
    return lam, w


@dataclass(frozen=True)
class ProbitFitResult:
    """Maximum-likelihood probit parameter estimate and observed Fisher Hessian."""

    beta_hat: np.ndarray
    cov_laplace: np.ndarray
    hessian: np.ndarray
    loglik: float
    grad_norm: float
    n_obs: int
    n_pos: int
    n_iter: int
    converged: bool


def fit_probit_with_hessian(
    X: np.ndarray,
    y: np.ndarray,
    *,
    ridge: float = 1e-10,
    max_iter: int = 100,
    tol: float = 1e-10,
) -> ProbitFitResult:
    """Fit binary probit model P(y_i=1|X_i)=Phi(X_i @ beta) via damped Newton-Raphson.

    Returns exact MLE, observed negative Hessian H = X^T diag(w) X, and cov_laplace = inv(H).
    """
    X_arr = np.asarray(X, dtype=np.float64)
    y_raw = np.asarray(y)
    if X_arr.ndim != 2 or not np.all(np.isfinite(X_arr)):
        raise ValueError("X must be a finite 2D array")
    n, p = X_arr.shape
    if y_raw.shape != (n,):
        raise ValueError(f"y shape {y_raw.shape} does not match X rows {n}")
    y_bool = y_raw.astype(np.bool_)
    if not np.all((y_raw == 0) | (y_raw == 1)):
        raise ValueError("y must contain only binary {0, 1} / boolean indicators")
    if n < p:
        raise ValueError(f"underdetermined probit fit: n={n} < p={p}")
    if np.linalg.matrix_rank(X_arr) < p:
        raise ValueError("probit design matrix X is rank-deficient")

    sign = np.where(y_bool, 1.0, -1.0)
    beta = np.zeros(p, dtype=np.float64)

    def _eval(b: np.ndarray) -> tuple[float, np.ndarray, np.ndarray, np.ndarray]:
        z = sign * (X_arr @ b)
        ll = float(np.sum(log_ndtr(z)))
        lam, w = _probit_mills_and_weight(z)
        grad = (sign * lam) @ X_arr
        H = (X_arr.T * w) @ X_arr
        H = 0.5 * (H + H.T)
        return ll, grad, H, w

    ll, grad, H, _ = _eval(beta)
    converged = False
    n_iter = 0
    for it in range(1, max_iter + 1):
        n_iter = it
        gnorm = float(np.linalg.norm(grad, ord=np.inf))
        if gnorm <= tol:
            converged = True
            break
        # Damped Newton solve with diagonal safeguard only if needed for step conditioning
        H_step = H + ridge * np.eye(p, dtype=np.float64)
        step = np.linalg.solve(H_step, grad)
        slope = float(grad @ step)
        if slope <= 0.0:
            step = grad / max(float(np.trace(H_step)) / p, 1.0)
            slope = float(grad @ step)
        alpha = 1.0
        accepted = False
        for _ in range(40):
            cand = beta + alpha * step
            ll_c, grad_c, H_c, _ = _eval(cand)
            if np.isfinite(ll_c) and ll_c >= ll + 1e-4 * alpha * slope - 1e-14 * max(1.0, abs(ll)):
                beta, ll, grad, H = cand, ll_c, grad_c, H_c
                accepted = True
                break
            alpha *= 0.5
        if not accepted:
            break
        if float(np.linalg.norm(grad, ord=np.inf)) <= tol or float(np.linalg.norm(alpha * step)) <= tol * 1e-2:
            converged = float(np.linalg.norm(grad, ord=np.inf)) <= max(tol * 1e2, 1e-7)
            if converged:
                break

    # Final exact inverse Fisher covariance (add ridge only if near-singular)
    eig_min = float(np.linalg.eigvalsh(H)[0])
    if eig_min <= 1e-14:
        H_inv_mat = H + max(ridge, 1e-10) * np.eye(p, dtype=np.float64)
    else:
        H_inv_mat = H
    cov_laplace = np.linalg.inv(H_inv_mat)
    cov_laplace = 0.5 * (cov_laplace + cov_laplace.T)

    return ProbitFitResult(
        beta_hat=beta,
        cov_laplace=cov_laplace,
        hessian=H,
        loglik=float(ll),
        grad_norm=float(np.linalg.norm(grad, ord=np.inf)),
        n_obs=int(n),
        n_pos=int(np.count_nonzero(y_bool)),
        n_iter=int(n_iter),
        converged=bool(converged),
    )


def build_group_clusters(
    group_ids: Sequence[int] | np.ndarray,
    *,
    ungrouped_sentinel: tuple[int, ...] | Sequence[int] = (-1, 0),
    secondary_keys: Sequence[int] | np.ndarray | None = None,
) -> np.ndarray:
    """Build union-find cluster IDs keeping ungrouped sentinel rows as singletons.

    Positive group IDs not in ``ungrouped_sentinel`` cluster together. Optional valid
    ``secondary_keys`` (> 0 and not in ``ungrouped_sentinel``) also link shared rows
    transitively via path-compressed union-find.
    """
    gids = np.asarray(group_ids, dtype=np.int64)
    if gids.ndim != 1:
        raise ValueError("group_ids must be a 1D array")
    n = len(gids)
    sentinel_set = {int(v) for v in ungrouped_sentinel}
    parent = np.arange(n, dtype=np.int64)
    rank = np.zeros(n, dtype=np.int8)

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = int(parent[x])
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra == rb:
            return
        if rank[ra] < rank[rb]:
            parent[ra] = rb
        elif rank[ra] > rank[rb]:
            parent[rb] = ra
        else:
            parent[rb] = ra
            rank[ra] += 1

    seen_gid: dict[int, int] = {}
    for idx, raw in enumerate(gids):
        val = int(raw)
        if val <= 0 or val in sentinel_set:
            continue
        prev = seen_gid.get(val)
        if prev is None:
            seen_gid[val] = idx
        else:
            union(prev, idx)

    if secondary_keys is not None:
        sec = np.asarray(secondary_keys, dtype=np.int64)
        if sec.shape != (n,):
            raise ValueError(f"secondary_keys shape {sec.shape} != ({n},)")
        seen_sec: dict[int, int] = {}
        for idx, raw in enumerate(sec):
            val = int(raw)
            if val <= 0 or val in sentinel_set:
                continue
            prev = seen_sec.get(val)
            if prev is None:
                seen_sec[val] = idx
            else:
                union(prev, idx)

    roots = np.array([find(i) for i in range(n)], dtype=np.int64)
    _, inverse = np.unique(roots, return_inverse=True)
    # Deterministic first-appearance renumbering 0 .. K-1
    remap = np.full(int(inverse.max()) + 1 if n > 0 else 0, -1, dtype=np.int64)
    clusters = np.empty(n, dtype=np.int64)
    next_id = 0
    for i, inv_val in enumerate(inverse):
        cid = int(remap[inv_val])
        if cid < 0:
            cid = next_id
            remap[inv_val] = cid
            next_id += 1
        clusters[i] = cid
    return clusters


def group_kfold_indices(
    cluster_ids: Sequence[int] | np.ndarray,
    *,
    n_splits: int = 5,
    seed: int = 42,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Deterministic balanced K-fold split on group clusters asserting zero leakage."""
    cids = np.asarray(cluster_ids, dtype=np.int64)
    if cids.ndim != 1:
        raise ValueError("cluster_ids must be 1D")
    n = len(cids)
    if n_splits < 2:
        raise ValueError("n_splits must be >= 2")

    order = np.argsort(cids, kind="mergesort")
    sorted_cids = cids[order]
    uniq_cids, start_idx, counts = np.unique(sorted_cids, return_index=True, return_counts=True)
    if len(uniq_cids) < n_splits:
        raise ValueError(f"cannot split {len(uniq_cids)} clusters into {n_splits} folds")

    members: list[np.ndarray] = []
    for pos, (st, cnt) in enumerate(zip(start_idx, counts)):
        members.append(order[st : st + cnt])

    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(uniq_cids))
    # Sort descending by cluster size while preserving randomized tie-breaking
    perm = perm[np.argsort(-counts[perm], kind="mergesort")]

    fold_lists: list[list[np.ndarray]] = [[] for _ in range(n_splits)]
    fold_sizes = np.zeros(n_splits, dtype=np.int64)
    for k_idx in perm:
        f_best = int(np.argmin(fold_sizes))
        fold_lists[f_best].append(members[k_idx])
        fold_sizes[f_best] += int(counts[k_idx])

    fold_tests = [
        np.sort(np.concatenate(chunk)) if chunk else np.empty(0, dtype=np.int64)
        for chunk in fold_lists
    ]
    all_mask = np.ones(n, dtype=bool)
    splits: list[tuple[np.ndarray, np.ndarray]] = []
    for f_idx in range(n_splits):
        test_idx = fold_tests[f_idx]
        train_mask = all_mask.copy()
        train_mask[test_idx] = False
        train_idx = np.flatnonzero(train_mask)
        # Strict invariant: zero shared cluster IDs across train and test
        if len(np.intersect1d(cids[train_idx], cids[test_idx])) != 0:
            raise AssertionError(f"group leakage detected in fold {f_idx}")
        splits.append((train_idx, test_idx))
    return splits


def cluster_bootstrap_probit(
    X: np.ndarray,
    y: np.ndarray,
    cluster_ids: Sequence[int] | np.ndarray,
    *,
    n_boot: int = 40,
    seed: int = 202611,
) -> dict[str, object]:
    """Pairs cluster bootstrap for probit coefficients accounting for intra-group correlation."""
    X_arr = np.asarray(X, dtype=np.float64)
    y_arr = np.asarray(y)
    cids = np.asarray(cluster_ids, dtype=np.int64)
    if X_arr.shape[0] != len(y_arr) or len(cids) != len(y_arr):
        raise ValueError("X, y, cluster_ids lengths must match")
    order = np.argsort(cids, kind="mergesort")
    sorted_c = cids[order]
    uniq_c, starts, counts = np.unique(sorted_c, return_index=True, return_counts=True)
    cluster_members = [order[st : st + cnt] for st, cnt in zip(starts, counts)]
    n_clusters = len(cluster_members)

    rng = np.random.default_rng(seed)
    betas = []
    for _ in range(int(n_boot)):
        draw = rng.integers(0, n_clusters, size=n_clusters)
        idx = np.concatenate([cluster_members[j] for j in draw])
        fit_b = fit_probit_with_hessian(X_arr[idx], y_arr[idx])
        betas.append(fit_b.beta_hat)
    beta_mat = np.vstack(betas)
    mean_b = np.mean(beta_mat, axis=0)
    cov_b = np.cov(beta_mat, rowvar=False, ddof=1)
    cov_b = 0.5 * (cov_b + cov_b.T)
    return {
        "n_boot": int(n_boot),
        "n_clusters": int(n_clusters),
        "mean_beta": mean_b,
        "std_beta": np.sqrt(np.diag(cov_b)),
        "cov_cluster_bootstrap": cov_b,
    }


def _split_probit_covariates(
    X_cov: np.ndarray,
    beta: np.ndarray,
    mark_col: int | None,
) -> tuple[np.ndarray, float, np.ndarray, int]:
    X_arr = np.asarray(X_cov, dtype=np.float64)
    b_arr = np.asarray(beta, dtype=np.float64)
    if b_arr.ndim != 1:
        raise ValueError("beta_hat must be a 1D vector")
    p = len(b_arr)
    if X_arr.ndim != 2:
        raise ValueError("X_cov must be 2D")
    if X_arr.shape[1] == p:
        mc = (p - 1) if mark_col is None else int(mark_col)
        if not (0 <= mc < p):
            raise ValueError(f"mark_col {mc} out of range [0, {p})")
        nonmark_idx = [j for j in range(p) if j != mc]
        X_nonmark = X_arr[:, nonmark_idx]
        intercept = X_nonmark @ b_arr[nonmark_idx]
        slope = float(b_arr[mc])
        return intercept, slope, X_nonmark, mc
    if X_arr.shape[1] == p - 1:
        mc = (p - 1) if mark_col is None else int(mark_col)
        if not (0 <= mc < p):
            raise ValueError(f"mark_col {mc} out of range [0, {p})")
        nonmark_idx = [j for j in range(p) if j != mc]
        intercept = X_arr @ b_arr[nonmark_idx]
        slope = float(b_arr[mc])
        return intercept, slope, X_arr, mc
    raise ValueError(f"X_cov columns {X_arr.shape[1]} incompatible with beta dimension {p}")


def _probit_field_response_with_beta_grad(
    mark: np.ndarray,
    field_means: np.ndarray,
    sigma: np.ndarray,
    X_nonmark: np.ndarray,
    beta: np.ndarray,
    mark_col: int,
    probabilities: np.ndarray,
    *,
    included: np.ndarray | None,
) -> tuple[dict[str, object], np.ndarray]:
    """Exact log_density and analytical d(log_density)/d(beta) for selected_probit_field_response."""
    p = len(beta)
    nonmark_idx = [j for j in range(p) if j != mark_col]
    a_vec = X_nonmark @ beta[nonmark_idx]
    b = float(beta[mark_col])

    y = np.asarray(mark, dtype=np.float64)
    mu = np.asarray(field_means, dtype=np.float64)
    sig = np.asarray(sigma, dtype=np.float64)
    probs = np.asarray(probabilities, dtype=np.float64)
    n_fields, n_obj = mu.shape
    inc = np.ones(n_obj, dtype=bool) if included is None else np.asarray(included, dtype=bool)
    rej = ~inc

    # Delegate value computation to R101 SSOT helper so numerics stay bit-exact
    resp = selected_probit_field_response(
        y, mu, sig, a_vec, b, probs, included=included, mean_tangent=None
    )

    denom = np.sqrt(1.0 + (b * b) * (sig * sig))
    denom_cb = denom * denom * denom
    u = (a_vec[None, :] + b * mu) / denom[None, :]
    du_da = 1.0 / denom[None, :]
    du_db = (mu - (b * (sig * sig))[None, :] * a_vec[None, :]) / denom_cb[None, :]

    # Derivatives of numerator log L_f and denominator log D_f wrt (a_i, b)
    dlogQ_du = _inverse_mills_stable(u)
    dlog1mQ_du = -_inverse_mills_stable(-u)

    # Numerator contributions per field
    w_obs = np.asarray(resp["observed_field_weights"], dtype=np.float64)
    w_inc = np.asarray(resp["included_field_weights"], dtype=np.float64)

    dlog_num_da = np.zeros(n_obj, dtype=np.float64)
    dlog_num_db = 0.0
    if np.any(inc):
        z_inc = a_vec[inc] + b * y[inc]
        mills_inc = _inverse_mills_stable(z_inc)
        dlog_num_da[inc] += mills_inc
        dlog_num_db += float(np.sum(y[inc] * mills_inc))
    if np.any(rej):
        # Rejected objects multiply both numerator and denominator by prod_{j in rej} (1 - Q_{f,j})
        dR_da_f = dlog1mQ_du[:, rej] * du_da[:, rej]
        dR_db_f = np.sum(dlog1mQ_du[:, rej] * du_db[:, rej], axis=1)
        dlog_num_da[rej] += w_obs @ dR_da_f
        dlog_num_db += float(w_obs @ dR_db_f)

    dlog_den_da = np.zeros(n_obj, dtype=np.float64)
    dlog_den_db = 0.0
    if np.any(inc):
        dQ_da_f = dlogQ_du[:, inc] * du_da[:, inc]
        dQ_db_f = np.sum(dlogQ_du[:, inc] * du_db[:, inc], axis=1)
        dlog_den_da[inc] += w_inc @ dQ_da_f
        dlog_den_db += float(w_inc @ dQ_db_f)
    if np.any(rej):
        dR_da_f = dlog1mQ_du[:, rej] * du_da[:, rej]
        dR_db_f = np.sum(dlog1mQ_du[:, rej] * du_db[:, rej], axis=1)
        dlog_den_da[rej] += w_inc @ dR_da_f
        dlog_den_db += float(w_inc @ dR_db_f)

    dlogdens_da = dlog_num_da - dlog_den_da
    dlogdens_db = dlog_num_db - dlog_den_db

    grad_beta = np.zeros(p, dtype=np.float64)
    grad_beta[nonmark_idx] = dlogdens_da @ X_nonmark
    grad_beta[mark_col] = dlogdens_db
    return resp, grad_beta


def selected_probit_uncertainty_propagation(
    mark: np.ndarray,
    field_means: np.ndarray,
    sigma: np.ndarray,
    X_cov: np.ndarray,
    beta_hat: np.ndarray,
    beta_cov: np.ndarray,
    probabilities: Sequence[float] | np.ndarray,
    *,
    included: np.ndarray | None = None,
    mark_col: int | None = None,
    n_mc: int = 128,
    seed: int = 12345,
) -> dict[str, object]:
    """Propagate selection-parameter covariance into selected-probit field mixture density.

    Computes:
    - Plug-in 5-field mixture vs zero-field delta log-density (`log_density_mix_minus_zero`).
    - Exact analytical gradient ``grad_beta = d(log_density_mix)/d(beta)`` and
      ``grad_beta_contrast = d(log_density_mix - log_density_zero)/d(beta)``.
    - First-order delta-method variance and standard error on both quantities.
    - Laplace-Gaussian Monte Carlo marginalization ``log E_beta[exp(log_density(beta))]``
      across ``n_mc`` antithetic draws from ``N(beta_hat, beta_cov)``.
    """
    b_hat = np.asarray(beta_hat, dtype=np.float64)
    cov = np.asarray(beta_cov, dtype=np.float64)
    p = len(b_hat)
    if cov.shape != (p, p) or not np.all(np.isfinite(cov)):
        raise ValueError(f"beta_cov must be finite ({p}, {p})")
    cov = 0.5 * (cov + cov.T)

    _, _, X_nonmark, mc = _split_probit_covariates(X_cov, b_hat, mark_col)
    mu = np.asarray(field_means, dtype=np.float64)
    zero_mu = np.zeros((1, mu.shape[1]), dtype=np.float64)
    probs = np.asarray(probabilities, dtype=np.float64)

    mix_resp, grad_mix = _probit_field_response_with_beta_grad(
        mark, mu, sigma, X_nonmark, b_hat, mc, probs, included=included
    )
    zero_resp, grad_zero = _probit_field_response_with_beta_grad(
        mark, zero_mu, sigma, X_nonmark, b_hat, mc, np.array([1.0]), included=included
    )
    grad_contrast = grad_mix - grad_zero
    delta_log_plug = float(mix_resp["log_density"]) - float(zero_resp["log_density"])

    var_mix = float(grad_mix @ cov @ grad_mix)
    var_contrast = float(grad_contrast @ cov @ grad_contrast)

    # Antithetic Laplace MC marginalization with jitter if semi-definite
    eigvals, eigvecs = np.linalg.eigh(cov)
    eigvals = np.maximum(eigvals, 0.0)
    chol_factor = eigvecs @ np.diag(np.sqrt(eigvals))

    rng = np.random.default_rng(seed)
    half = max(1, int(n_mc) // 2)
    z_half = rng.normal(size=(half, p))
    z_draws = np.vstack((z_half, -z_half))
    if z_draws.shape[0] < int(n_mc):
        z_draws = np.vstack((z_draws, rng.normal(size=(1, p))))
    beta_draws = b_hat[None, :] + z_draws @ chol_factor.T

    nonmark_idx = [j for j in range(p) if j != mc]
    log_mix_samples = np.empty(beta_draws.shape[0], dtype=np.float64)
    log_zero_samples = np.empty(beta_draws.shape[0], dtype=np.float64)
    for m, bm in enumerate(beta_draws):
        am = X_nonmark @ bm[nonmark_idx]
        slm = float(bm[mc])
        log_mix_samples[m] = selected_probit_field_response(
            mark, mu, sigma, am, slm, probs, included=included
        )["log_density"]
        log_zero_samples[m] = selected_probit_field_response(
            mark, zero_mu, sigma, am, slm, np.array([1.0]), included=included
        )["log_density"]

    log_marg_mix = float(logsumexp(log_mix_samples) - math.log(len(log_mix_samples)))
    log_marg_zero = float(logsumexp(log_zero_samples) - math.log(len(log_zero_samples)))
    delta_samples = log_mix_samples - log_zero_samples

    p_joint = mix_resp.get("log_joint_inclusion")
    p_patt = mix_resp.get("log_inclusion_pattern")
    return {
        "plugin_log_density_mix": float(mix_resp["log_density"]),
        "plugin_log_density_zero": float(zero_resp["log_density"]),
        "plugin_log_density_mix_minus_zero": delta_log_plug,
        "plugin_log_joint_inclusion": None if p_joint is None else float(p_joint),
        "plugin_log_inclusion_pattern": None if p_patt is None else float(p_patt),
        "grad_beta_mix": grad_mix,
        "grad_beta_zero": grad_zero,
        "grad_beta_mix_minus_zero": grad_contrast,
        "delta_method_var_mix": var_mix,
        "delta_method_std_mix": math.sqrt(max(var_mix, 0.0)),
        "delta_method_var_mix_minus_zero": var_contrast,
        "delta_method_std_mix_minus_zero": math.sqrt(max(var_contrast, 0.0)),
        "mc_n": int(len(log_mix_samples)),
        "marginalized_log_density_mix": log_marg_mix,
        "marginalized_log_density_zero": log_marg_zero,
        "marginalized_log_density_mix_minus_zero": log_marg_mix - log_marg_zero,
        "mc_mean_log_density_mix_minus_zero": float(np.mean(delta_samples)),
        "mc_std_log_density_mix_minus_zero": float(np.std(delta_samples, ddof=1)),
    }


def _sph_unit_vectors(ra_deg: np.ndarray, dec_deg: np.ndarray) -> np.ndarray:
    ra = np.deg2rad(np.asarray(ra_deg, dtype=np.float64))
    dec = np.deg2rad(np.asarray(dec_deg, dtype=np.float64))
    cos_d = np.cos(dec)
    return np.column_stack((cos_d * np.cos(ra), cos_d * np.sin(ra), np.sin(dec)))


def sixdf_match_ambiguity_policies(
    table2: Mapping[str, np.ndarray],
    sixdf: Mapping[str, np.ndarray],
    *,
    arcsec: float = 15.0,
    dv_kms: float = 500.0,
) -> dict[str, object]:
    """Compare R101 unique-only rule vs closest-match and exclusion of multi-match rows."""
    u2 = _sph_unit_vectors(table2["ra"], table2["dec"])
    u6 = _sph_unit_vectors(sixdf["ra"], sixdf["dec"])
    v2 = np.asarray(table2["vcmb"], dtype=np.float64)
    cz6 = np.asarray(sixdf["cz_gal"], dtype=np.float64)

    radius = 2.0 * math.sin(math.radians(float(arcsec) / 3600.0) / 2.0)
    tree = cKDTree(u2)
    hits = tree.query_ball_point(u6, radius)

    counts = np.zeros(len(cz6), dtype=np.int64)
    closest_idx = np.full(len(cz6), -1, dtype=np.int64)
    ambiguous_details = []
    for i, (cand, v) in enumerate(zip(hits, cz6)):
        valid = [j for j in cand if abs(float(v2[j]) - float(v)) <= float(dv_kms)]
        counts[i] = len(valid)
        if valid:
            # Rank candidates by combined normalized angular + velocity metric
            c_arr = np.asarray(valid, dtype=np.int64)
            ang = 2.0 * np.arcsin(
                np.clip(0.5 * np.linalg.norm(u2[c_arr] - u6[i], axis=1), 0.0, 1.0)
            )
            ang_arcsec = np.rad2deg(ang) * 3600.0
            dv = np.abs(v2[c_arr] - v)
            score = (ang_arcsec / float(arcsec)) ** 2 + (dv / float(dv_kms)) ** 2
            best_pos = int(np.argmin(score))
            closest_idx[i] = int(c_arr[best_pos])
            if len(valid) > 1:
                ambiguous_details.append(
                    {
                        "sixdf_row": int(i),
                        "n_candidates": int(len(valid)),
                        "pgc_candidates": [int(table2["pgc"][j]) for j in c_arr],
                        "ang_arcsec": [float(x) for x in ang_arcsec],
                        "dv_kms": [float(x) for x in dv],
                        "chosen_pgc": int(table2["pgc"][closest_idx[i]]),
                    }
                )

    policies = {
        "unique_only_r101": {
            "keep": np.ones(len(cz6), dtype=bool),
            "included": counts == 1,
        },
        "resolve_closest": {
            "keep": np.ones(len(cz6), dtype=bool),
            "included": counts >= 1,
        },
        "exclude_ambiguous": {
            "keep": counts <= 1,
            "included": counts == 1,
        },
    }
    return {
        "multiplicity_histogram": {int(k): int(v) for k, v in zip(*np.unique(counts, return_counts=True))},
        "ambiguous_rows": ambiguous_details,
        "closest_table2_indices": closest_idx,
        "policies": policies,
    }


def component_covariance_tangents(
    y: np.ndarray,
    C_components: Mapping[str, np.ndarray],
    contrasts: PredictiveContrasts,
) -> dict[str, object]:
    """Decompose predictive chi2 & log_density tangents across additive covariance components.

    Verifies exact Euler homogeneity of the Gaussian predictive likelihood:
      sum_k d(chi2)/d(w_k) == -chi2
      sum_k d(logdet)/d(w_k) == m_test
      sum_k d(log_density)/d(w_k) == 0.5 * (chi2 - m_test)
    where C(w) = sum_k w_k C_k evaluated at w = 1.
    """
    if not C_components:
        raise ValueError("C_components must be non-empty")
    y_arr = np.asarray(y, dtype=np.float64)
    comp_names = list(C_components.keys())
    mats = [np.asarray(C_components[k], dtype=np.float64) for k in comp_names]
    C_tot = np.sum(mats, axis=0)
    # Baseline full-scaling check using C_tot as direction
    base = predictive_covariance_response(y_arr, C_tot, C_tot, contrasts)
    m_test = int(len(base["mean"]))
    chi2_val = float(base["chi2"])
    logdens_val = float(base["log_density"])

    per_component: dict[str, dict[str, object]] = {}
    sum_chi2_tan = 0.0
    sum_logdet_tan = 0.0
    sum_logdens_tan = 0.0
    sum_mean_tan = np.zeros(m_test, dtype=np.float64)
    sum_cov_tan = np.zeros((m_test, m_test), dtype=np.float64)

    for name, ck in zip(comp_names, mats):
        res_k = predictive_covariance_response(y_arr, C_tot, ck, contrasts)
        sum_chi2_tan += float(res_k["chi2_tangent"])
        sum_logdet_tan += float(res_k["logdet_tangent"])
        sum_logdens_tan += float(res_k["log_density_tangent"])
        sum_mean_tan += np.asarray(res_k["mean_tangent"], dtype=np.float64)
        sum_cov_tan += np.asarray(res_k["covariance_tangent"], dtype=np.float64)
        per_component[name] = {
            "trace": float(np.trace(ck)),
            "frobenius": float(np.linalg.norm(ck, ord="fro")),
            "chi2_tangent": float(res_k["chi2_tangent"]),
            "chi2_mean_term": float(res_k["chi2_mean_term"]),
            "chi2_covariance_term": float(res_k["chi2_covariance_term"]),
            "logdet_tangent": float(res_k["logdet_tangent"]),
            "log_density_tangent": float(res_k["log_density_tangent"]),
            "mean_tangent_norm": float(np.linalg.norm(res_k["mean_tangent"])),
        }

    # Exact Euler checks: mean is homogeneous of degree 0, S of degree 1, chi2 of degree -1, logdet of degree m_test
    euler_chi2_err = abs(sum_chi2_tan + chi2_val)
    euler_logdet_err = abs(sum_logdet_tan - float(m_test))
    euler_logdens_err = abs(sum_logdens_tan - 0.5 * (chi2_val - float(m_test)))
    euler_mean_err = float(np.max(np.abs(sum_mean_tan)))
    euler_cov_err = float(np.max(np.abs(sum_cov_tan - np.asarray(base["covariance"], dtype=np.float64))))
    max_euler_err = max(euler_chi2_err, euler_logdet_err, euler_logdens_err, euler_mean_err, euler_cov_err)

    return {
        "m_test": m_test,
        "baseline": {
            "chi2": chi2_val,
            "log_density": logdens_val,
            "trace_C_total": float(np.trace(C_tot)),
            "total_cov_min_eig": float(np.linalg.eigvalsh(0.5 * (C_tot + C_tot.T))[0]),
        },
        "components": per_component,
        "euler_homogeneity_errors": {
            "chi2": euler_chi2_err,
            "logdet": euler_logdet_err,
            "log_density": euler_logdens_err,
            "mean": euler_mean_err,
            "predictive_cov": euler_cov_err,
            "max": max_euler_err,
        },
    }
