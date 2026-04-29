from __future__ import annotations

import math

import numpy as np
import pytest
from scipy.stats import norm

from bass.inference import BayesFactorResult, Prior, bayes_factor, run_posterior
from bass.inference.drivers.dynesty_driver import run_nested_evidence

pytestmark = pytest.mark.slow


def _gaussian_prior(name: str, sigma: float = 1.0) -> Prior:
    sigma = float(sigma)

    def log_pdf(value: np.ndarray) -> np.ndarray:
        x = np.asarray(value, dtype=float).reshape(-1)
        return -0.5 * (x / sigma) ** 2 - np.log(sigma) - 0.5 * np.log(2.0 * np.pi)

    def sample(rng: np.random.Generator, n: int) -> np.ndarray:
        return rng.normal(0.0, sigma, size=int(n))

    return Prior(name=name, domain=None, log_pdf=log_pdf, sample=sample)


def _toy_priors(sigma_prior: float = 1.0) -> dict[str, Prior]:
    return {"x": _gaussian_prior("x", sigma=sigma_prior), "y": _gaussian_prior("y", sigma=sigma_prior)}


def _likelihood_factory(data: np.ndarray, mean_shift: np.ndarray, sigma_like: float):
    sigma_like = float(sigma_like)

    def _likelihood(theta: np.ndarray) -> float:
        residual = np.asarray(data, dtype=float) - (np.asarray(theta, dtype=float) + mean_shift)
        return float(
            -0.5 * np.dot(residual, residual) / (sigma_like * sigma_like)
            - theta.size * np.log(sigma_like)
            - 0.5 * theta.size * np.log(2.0 * np.pi)
        )

    return _likelihood


def _analytic_log_evidence(data: np.ndarray, mean_shift: np.ndarray, sigma_prior: float, sigma_like: float) -> float:
    cov = (sigma_prior * sigma_prior + sigma_like * sigma_like)
    residual = np.asarray(data, dtype=float) - np.asarray(mean_shift, dtype=float)
    ndim = residual.size
    return float(
        -0.5 * np.dot(residual, residual) / cov
        - 0.5 * ndim * np.log(2.0 * np.pi * cov)
    )


def _run_posterior_for_shift(mean_shift: np.ndarray, *, seed: int) -> tuple[object, float]:
    sigma_prior = 1.0
    sigma_like = 0.35
    data = np.array([0.1, -0.2], dtype=float)
    posterior = run_posterior(
        _likelihood_factory(data, mean_shift, sigma_like),
        _toy_priors(sigma_prior),
        seed=seed,
        n_walkers=24,
        n_steps=160,
        burnin=80,
    )
    analytic = _analytic_log_evidence(data, mean_shift, sigma_prior, sigma_like)
    return posterior, analytic


def test_fb113_result_is_a_dataclass() -> None:
    assert hasattr(BayesFactorResult, "__dataclass_fields__")


def test_fb113_bayes_factor_self_consistency_is_zero_within_error() -> None:
    posterior, _ = _run_posterior_for_shift(np.array([0.0, 0.0]), seed=42)
    result = bayes_factor(posterior, posterior)
    assert abs(result.ln_B) <= 3.0 * result.ln_B_err


def test_fb113_bayes_factor_is_antisymmetric() -> None:
    posterior_a, _ = _run_posterior_for_shift(np.array([0.0, 0.0]), seed=1)
    posterior_b, _ = _run_posterior_for_shift(np.array([0.45, -0.3]), seed=2)
    ab = bayes_factor(posterior_a, posterior_b)
    ba = bayes_factor(posterior_b, posterior_a)
    assert ab.ln_B == pytest.approx(-ba.ln_B, abs=max(ab.ln_B_err, ba.ln_B_err))


def test_fb113_analytic_vs_thermodynamic_agree_within_point_one_log_units() -> None:
    posterior_a, analytic_a = _run_posterior_for_shift(np.array([0.0, 0.0]), seed=7)
    posterior_b, analytic_b = _run_posterior_for_shift(np.array([0.45, -0.3]), seed=8)
    result = bayes_factor(posterior_a, posterior_b)
    analytic_ln_b = analytic_a - analytic_b
    assert abs(result.ln_B - analytic_ln_b) < 0.1


def test_fb113_analytic_vs_dynesty_agree_within_two_sigma() -> None:
    sigma_prior = 1.0
    sigma_like = 0.35
    data = np.array([0.1, -0.2], dtype=float)
    mean_a = np.array([0.0, 0.0], dtype=float)
    mean_b = np.array([0.45, -0.3], dtype=float)
    posterior_a, _ = _run_posterior_for_shift(mean_a, seed=11)
    posterior_b, _ = _run_posterior_for_shift(mean_b, seed=12)
    ti_result = bayes_factor(posterior_a, posterior_b)

    def transform(u: np.ndarray) -> np.ndarray:
        return norm.ppf(u, loc=0.0, scale=sigma_prior)

    dynesty_a = run_nested_evidence(_likelihood_factory(data, mean_a, sigma_like), transform, 2, seed=101, nlive=200)
    dynesty_b = run_nested_evidence(_likelihood_factory(data, mean_b, sigma_like), transform, 2, seed=102, nlive=200)
    nested_ln_b = dynesty_a.ln_Z - dynesty_b.ln_Z
    nested_err = math.hypot(dynesty_a.ln_Z_err, dynesty_b.ln_Z_err)
    assert abs(ti_result.ln_B - nested_ln_b) <= 2.0 * max(ti_result.ln_B_err, nested_err)


@pytest.mark.parametrize("shift", [np.array([0.0, 0.0]), np.array([0.25, -0.15]), np.array([0.45, -0.3])])
def test_fb113_ti_provenance_records_sampler_and_seed(shift: np.ndarray) -> None:
    posterior, _ = _run_posterior_for_shift(shift, seed=31)
    result = bayes_factor(posterior, posterior)
    assert result.method == "thermodynamic"
    assert result.provenance["model_A_seed"] == 31
    assert "emcee" in result.provenance["model_A_sampler"]
