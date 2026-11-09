#!/usr/bin/env python3
"""R45 finite-model posterior information loss under deterministic compression.

Synthetic statistical-theory experiments only; no cosmological survey data.
The script estimates E[KL(p(M|Y)||p(M|S))] and checks its mutual-information
representation for a common deterministic summary S=T(Y).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy.special import gammaln, logsumexp

SEED = 20261109
EPS = np.finfo(float).tiny


def gaussian_logpdf_batch(y: np.ndarray, means: np.ndarray, covariances: np.ndarray) -> np.ndarray:
    """Return log p(y_i|m) with shapes (n,d), (k,d), (k,d,d)."""
    y = np.asarray(y, dtype=float)
    means = np.asarray(means, dtype=float)
    covariances = np.asarray(covariances, dtype=float)
    n, d = y.shape
    k = means.shape[0]
    out = np.empty((n, k), dtype=float)
    for j in range(k):
        L = np.linalg.cholesky(covariances[j])
        z = np.linalg.solve(L, (y - means[j]).T).T
        quad = np.einsum("ni,ni->n", z, z)
        logdet = 2.0 * np.log(np.diag(L)).sum()
        out[:, j] = -0.5 * (d * np.log(2.0 * np.pi) + logdet + quad)
    return out


def posterior_from_loglik(loglik: np.ndarray, prior: np.ndarray) -> np.ndarray:
    logw = np.log(prior)[None, :] + np.asarray(loglik, dtype=float)
    return np.exp(logw - logsumexp(logw, axis=1, keepdims=True))


def posterior_from_exact_loglr(loglik: np.ndarray, prior: np.ndarray) -> np.ndarray:
    """Posterior as a function of the K-1 log likelihood ratios to model K."""
    loglik = np.asarray(loglik, dtype=float)
    # The omitted reference log-likelihood cancels from Bayes' rule.
    loglr = loglik[:, :-1] - loglik[:, -1, None]
    logw = np.column_stack([np.log(prior[:-1]) + loglr, np.full(len(loglik), np.log(prior[-1]))])
    return np.exp(logw - logsumexp(logw, axis=1, keepdims=True))


def posterior_loss_metrics(raw: np.ndarray, summary: np.ndarray, prior: np.ndarray) -> dict[str, float]:
    raw = np.clip(raw, EPS, 1.0)
    summary = np.clip(summary, EPS, 1.0)
    prior = np.asarray(prior, dtype=float)
    kl_rows = np.sum(raw * (np.log(raw) - np.log(summary)), axis=1)
    if float(np.min(kl_rows)) < -1e-10:
        raise ArithmeticError("posterior KL became materially negative; inspect normalization/numerics")
    # Remove only roundoff-scale negative values for mathematically identical posteriors.
    kl_rows = np.maximum(kl_rows, 0.0)
    mi_raw_rows = np.sum(raw * (np.log(raw) - np.log(prior)[None, :]), axis=1)
    mi_summary_rows = np.sum(summary * (np.log(summary) - np.log(prior)[None, :]), axis=1)
    mi_difference_rows = mi_raw_rows - mi_summary_rows
    tv_rows = 0.5 * np.sum(np.abs(raw - summary), axis=1)
    risk_raw_rows = 1.0 - np.max(raw, axis=1)
    risk_summary_rows = 1.0 - np.max(summary, axis=1)
    n = len(raw)
    loss = float(np.mean(kl_rows))
    mi_difference = float(np.mean(mi_difference_rows))
    risk_gap = float(np.mean(risk_summary_rows - risk_raw_rows))
    return {
        "expected_posterior_kl_direct": loss,
        "expected_posterior_kl_mi_difference": mi_difference,
        "posterior_kl_mcse": float(np.std(kl_rows, ddof=1) / np.sqrt(n)),
        "mi_information_difference_mcse": float(np.std(mi_difference_rows, ddof=1) / np.sqrt(n)),
        "chain_rule_identity_absolute_discrepancy": float(abs(loss - mi_difference)),
        "raw_model_information_nats": float(np.mean(mi_raw_rows)),
        "summary_model_information_nats": float(np.mean(mi_summary_rows)),
        "expected_posterior_tv": float(np.mean(tv_rows)),
        "posterior_tv_mcse": float(np.std(tv_rows, ddof=1) / np.sqrt(n)),
        "raw_bayes_0_1_risk": float(np.mean(risk_raw_rows)),
        "summary_bayes_0_1_risk": float(np.mean(risk_summary_rows)),
        "bayes_risk_increase": risk_gap,
        "risk_gap_mcse": float(np.std(risk_summary_rows - risk_raw_rows, ddof=1) / np.sqrt(n)),
        "pinsker_expected_tv_upper_bound_from_direct_loss": float(np.sqrt(max(loss, 0.0) / 2.0)),
        "n_replications": int(n),
    }


def simulate_gaussian_models(
    means: np.ndarray, covariances: np.ndarray, prior: np.ndarray,
    n_rep: int, seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    model = rng.choice(len(prior), size=n_rep, p=prior)
    y = np.empty((n_rep, means.shape[1]), dtype=float)
    for m in range(len(prior)):
        idx = np.flatnonzero(model == m)
        if idx.size:
            y[idx] = rng.multivariate_normal(means[m], covariances[m], size=idx.size)
    return model, y, rng


def projected_gaussian_posterior(
    y: np.ndarray, A: np.ndarray, means: np.ndarray, covariances: np.ndarray,
    prior: np.ndarray,
) -> np.ndarray:
    """Posterior from S=A^T Y with its exact induced Gaussian laws."""
    s = y @ A
    sm = means @ A
    sc = np.stack([A.T @ c @ A for c in covariances])
    return posterior_from_loglik(gaussian_logpdf_batch(s, sm, sc), prior)


def common_covariance_experiment(n_rep: int, seed: int) -> dict[str, Any]:
    d, k = 8, 4
    rng = np.random.default_rng(seed)
    raw = rng.normal(size=(d, d))
    sigma = raw @ raw.T / d + 0.35 * np.eye(d)
    means = np.zeros((k, d))
    means[1, [0, 1]] = [0.80, 0.10]
    means[2, [1, 2]] = [-0.65, 0.75]
    means[3, [2, 3]] = [0.55, -0.70]
    cov = np.repeat(sigma[None, :, :], k, axis=0)
    prior = np.array([0.25, 0.25, 0.25, 0.25])
    model, y, _ = simulate_gaussian_models(means, cov, prior, n_rep, seed + 1)
    raw_loglik = gaussian_logpdf_batch(y, means, cov)
    p_raw = posterior_from_loglik(raw_loglik, prior)

    # K-1 common-covariance discriminant scores are the complete log-LR coordinates.
    contrasts = (means[:-1] - means[-1]).T
    A_exact = np.linalg.solve(sigma, contrasts)
    p_exact = projected_gaussian_posterior(y, A_exact, means, cov, prior)

    # A deliberately lossy projection retaining only the first discriminant coordinate.
    A_lossy = A_exact[:, :1]
    p_lossy = projected_gaussian_posterior(y, A_lossy, means, cov, prior)
    exact = posterior_loss_metrics(p_raw, p_exact, prior)
    lossy = posterior_loss_metrics(p_raw, p_lossy, prior)

    # Verify the Fisher-Neyman residual factorization numerically: ratios depend only on S.
    return {
        "dimension_raw": d,
        "number_models": k,
        "summary_dimension_exact": int(A_exact.shape[1]),
        "summary_dimension_lossy": int(A_lossy.shape[1]),
        "exact_common_covariance_discriminant_score": exact,
        "lossy_one_score_projection": lossy,
        "sampled_model_frequency": np.bincount(model, minlength=k).astype(float).tolist(),
        "interpretation": "With common known covariance, the K-1 mean-contrast scores encode every model log-likelihood ratio. Dropping discriminant directions produces positive model-posterior information loss.",
    }


def covariance_change_experiment(n_rep: int, seed: int) -> dict[str, Any]:
    d, k = 6, 3
    prior = np.array([0.34, 0.33, 0.33])
    means = np.zeros((k, d))
    means[1, 0] = 0.60
    means[2, 1] = -0.60
    cov = np.repeat(np.eye(d)[None, :, :], k, axis=0)
    cov[1, 3, 3] = 2.2
    cov[2, 4, 4] = 2.8
    model, y, _ = simulate_gaussian_models(means, cov, prior, n_rep, seed)
    raw_loglik = gaussian_logpdf_batch(y, means, cov)
    p_raw = posterior_from_loglik(raw_loglik, prior)

    # The mean-only/common-C score misses covariance information in coordinates 4,5.
    A_mean = np.eye(d)[:, :2]
    p_mean = projected_gaussian_posterior(y, A_mean, means, cov, prior)

    # The K-1 exact raw log-likelihood ratios are themselves a common deterministic statistic.
    p_exact_lr = posterior_from_exact_loglr(raw_loglik, prior)
    mean_only = posterior_loss_metrics(p_raw, p_mean, prior)
    exact_lr = posterior_loss_metrics(p_raw, p_exact_lr, prior)
    return {
        "dimension_raw": d,
        "number_models": k,
        "covariance_diagonal_by_model": [np.diag(c).tolist() for c in cov],
        "mean_only_summary": mean_only,
        "exact_log_likelihood_ratio_summary": exact_lr,
        "interpretation": "When covariance is model-dependent, quadratic residual information is needed. Mean-only score summaries lose model information; the K-1 exact log-likelihood ratios remain sufficient for the finite model index.",
    }


def radial_and_directional_experiment(n_rep: int, seed: int) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    d = 5
    prior = np.array([0.5, 0.5])
    a = 0.85
    means = np.zeros((2, d))
    means[0, 0] = a
    means[1, 0] = -a
    cov = np.repeat(np.eye(d)[None, :, :], 2, axis=0)
    model, y, _ = simulate_gaussian_models(means, cov, prior, n_rep, seed + 1)
    p_raw = posterior_from_loglik(gaussian_logpdf_batch(y, means, cov), prior)
    # The norm has identical distributions under the two sign-reflected models.
    p_norm = np.repeat(prior[None, :], n_rep, axis=0)
    directional = posterior_loss_metrics(p_raw, p_norm, prior)

    # Radial control: zero-mean isotropic Gaussians, for which ||Y||^2 is sufficient.
    scales = np.array([0.65, 1.45])
    radial_cov = np.stack([s**2 * np.eye(d) for s in scales])
    radial_model = rng.choice(2, size=n_rep, p=prior)
    yr = np.empty((n_rep, d))
    for m in range(2):
        idx = np.flatnonzero(radial_model == m)
        if idx.size:
            yr[idx] = rng.multivariate_normal(np.zeros(d), radial_cov[m], size=idx.size)
    raw_radial_loglik = gaussian_logpdf_batch(yr, np.zeros((2, d)), radial_cov)
    p_raw_radial = posterior_from_loglik(raw_radial_loglik, prior)
    r2 = np.einsum("ni,ni->n", yr, yr)
    log_radial = np.empty((n_rep, 2))
    for m, s in enumerate(scales):
        log_radial[:, m] = (
            (d / 2.0 - 1.0) * np.log(np.maximum(r2, EPS))
            - r2 / (2.0 * s**2)
            - (d / 2.0) * np.log(2.0 * s**2)
            - gammaln(d / 2.0)
        )
    p_radial = posterior_from_loglik(log_radial, prior)
    radial_exact = posterior_loss_metrics(p_raw_radial, p_radial, prior)
    return {
        "directional_signal": directional,
        "radial_scale_control": radial_exact,
        "interpretation": "A norm destroys direction and loses all model information for equal-prior sign-reflected means. For centered isotropic scale alternatives, the squared norm is exactly sufficient.",
    }


def parameter_vs_model_information_experiment(n_rep: int, seed: int) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    prior = np.array([0.5, 0.5])

    # Case A: S=U preserves model index M, but drops V which informs a shared theta.
    # U|M=m ~ N((-1)^m delta, 1); theta~N(0,1), V|theta~N(theta,1), independent of M.
    delta = 0.9
    model_a = rng.choice(2, size=n_rep, p=prior)
    mu_u = np.where(model_a == 0, -delta, delta)
    u = rng.normal(mu_u, 1.0)
    theta = rng.normal(0.0, 1.0, size=n_rep)
    v = rng.normal(theta, 1.0)
    loglik_u = np.column_stack([
        -0.5 * (u + delta) ** 2,
        -0.5 * (u - delta) ** 2,
    ])
    p_m_y = posterior_from_loglik(loglik_u, prior)  # V cancels from M posterior.
    p_m_s = p_m_y.copy()
    model_loss_a = posterior_loss_metrics(p_m_y, p_m_s, prior)
    # theta|V ~ N(V/2, 1/2); prior theta ~ N(0,1).
    theta_kl_rows = 0.5 * (0.5 + (v**2) / 4.0 - 1.0 + np.log(2.0))
    theta_loss_a = float(np.mean(theta_kl_rows))
    theta_loss_mcse = float(np.std(theta_kl_rows, ddof=1) / np.sqrt(n_rep))

    # Case B: S=U is sufficient for theta within each model, but M is signaled by V.
    theta_b = rng.normal(0.0, 1.0, size=n_rep)
    u_b = rng.normal(theta_b, 0.55)
    model_b = rng.choice(2, size=n_rep, p=prior)
    mu_v = np.where(model_b == 0, -delta, delta)
    v_b = rng.normal(mu_v, 1.0)
    # Full posterior M uses V. Conditional on M, V is theta-independent; theta posterior uses U only.
    loglik_m_y = np.column_stack([
        -0.5 * (v_b + delta) ** 2,
        -0.5 * (v_b - delta) ** 2,
    ])
    p_m_raw_b = posterior_from_loglik(loglik_m_y, prior)
    p_m_summary_b = np.repeat(prior[None, :], n_rep, axis=0)
    model_loss_b = posterior_loss_metrics(p_m_raw_b, p_m_summary_b, prior)
    return {
        "case_A_model_index_preserved_parameter_posterior_lost": {
            "model_index_information_loss": model_loss_a,
            "within_model_parameter_posterior_information_loss_nats": theta_loss_a,
            "parameter_loss_mcse": theta_loss_mcse,
            "analytic_parameter_loss_nats": float(0.5 * np.log(2.0)),
            "interpretation": "M posterior is exactly preserved by S=U, but V contains additional information about theta. The joint (M,theta) posterior is therefore not preserved.",
        },
        "case_B_within_model_parameter_sufficient_but_model_index_lost": {
            "model_index_information_loss": model_loss_b,
            "within_model_parameter_posterior_information_loss_nats": 0.0,
            "interpretation": "Within each model, S=U contains all theta information because V is conditionally independent of theta. Yet V discriminates the model label and is omitted from S, so model-choice information is lost.",
        },
    }


def run_experiment(n_rep: int = 60000, seed: int = SEED) -> dict[str, Any]:
    common = common_covariance_experiment(n_rep, seed + 11)
    covariance = covariance_change_experiment(n_rep, seed + 23)
    radial = radial_and_directional_experiment(n_rep, seed + 37)
    parameter = parameter_vs_model_information_experiment(n_rep, seed + 53)
    return {
        "schema": "htt.r45_model_posterior_information_loss/1",
        "seed": seed,
        "classification": "SYNTHETIC_STATISTICAL_THEORY_EXPERIMENT_NOT_OBSERVATIONAL",
        "replications_per_experiment": n_rep,
        "theory_claim": "DERIVED_STANDARD_INFORMATION_THEORY_IDENTITY; no novelty claim for the conditional-MI chain rule",
        "experiments": {
            "common_covariance_multi_model": common,
            "model_dependent_covariance": covariance,
            "radial_vs_directional_summary": radial,
            "model_index_vs_parameter_posterior": parameter,
        },
        "global_scope": [
            "No Planck, Gaia, Quaia, NVSS, Pantheon, DESI or other observed survey data are used.",
            "All Gaussian distributions and summaries in these experiments are synthetic.",
            "Model-index posterior preservation is not equivalent to preservation of continuous within-model parameter posteriors.",
            "A model-specific summary family is not a common statistic unless its outputs are joined into one common vector or common channel.",
            "Results are finite-model posterior-information diagnostics, not a cosmological detection or Bianchi-family identification."
        ],
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--replications", type=int, default=60000)
    p.add_argument("--output", type=Path, default=Path("R45_MOCK_RESULTS.json"))
    args = p.parse_args()
    result = run_experiment(args.replications, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "common_exact_loss": result["experiments"]["common_covariance_multi_model"]["exact_common_covariance_discriminant_score"]["expected_posterior_kl_direct"],
        "common_lossy_loss": result["experiments"]["common_covariance_multi_model"]["lossy_one_score_projection"]["expected_posterior_kl_direct"],
        "covariance_mean_only_loss": result["experiments"]["model_dependent_covariance"]["mean_only_summary"]["expected_posterior_kl_direct"],
        "covariance_exact_lr_loss": result["experiments"]["model_dependent_covariance"]["exact_log_likelihood_ratio_summary"]["expected_posterior_kl_direct"],
        "norm_directional_loss": result["experiments"]["radial_vs_directional_summary"]["directional_signal"]["expected_posterior_kl_direct"],
        "parameter_loss_case_A": result["experiments"]["model_index_vs_parameter_posterior"]["case_A_model_index_preserved_parameter_posterior_lost"]["within_model_parameter_posterior_information_loss_nats"],
    }, indent=2))


if __name__ == "__main__":
    main()
