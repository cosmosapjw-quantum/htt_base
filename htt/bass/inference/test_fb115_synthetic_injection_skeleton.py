from __future__ import annotations

import numpy as np
import pytest

from bass.background.bianchi_types import ALL_BIANCHI_TYPES
from bass.inference import bayes_factor, run_posterior
from bass.inference.synthetic import make_problem, posterior_quantiles


def _fit_problem(label: str, *, truth_type: str, seed: int) -> object:
    problem = make_problem(label, truth_type=truth_type, seed=seed)
    return run_posterior(
        problem.log_likelihood,
        problem.priors,
        seed=seed,
        n_walkers=12,
        n_steps=24,
        burnin=12,
    )


def _coverage_parameter(label: str) -> str:
    return "structure_scale" if label not in {"FLRW", "I"} else "Sigma_mnu"


@pytest.mark.slow
@pytest.mark.parametrize("truth_type", ["FLRW", *ALL_BIANCHI_TYPES])
def test_fb115_synthetic_injection_coverage_reaches_nominal_band(truth_type: str) -> None:
    problem = make_problem(truth_type if truth_type != "FLRW" else "FLRW", truth_type=truth_type, seed=0)
    parameter = _coverage_parameter(truth_type)
    truth_value = float(problem.truth_params.get(parameter, 0.0))
    covered = 0
    for draw in range(100):
        posterior = _fit_problem(truth_type if truth_type != "FLRW" else "FLRW", truth_type=truth_type, seed=1000 + draw)
        quantiles = posterior_quantiles(
            posterior.samples,
            tuple(posterior.config["parameter_names"]),
        )[parameter]
        covered += int(float(quantiles[0]) <= truth_value <= float(quantiles[2]))
    assert covered >= 63


@pytest.mark.parametrize("label", ALL_BIANCHI_TYPES)
def test_fb115_flrw_truth_keeps_ln_b_near_zero_for_bianchi_i_family(label: str) -> None:
    baseline_problem = make_problem("FLRW", truth_type="FLRW", seed=42)
    observation = baseline_problem.observation
    flrw = run_posterior(baseline_problem.log_likelihood, baseline_problem.priors, seed=42, n_walkers=16, n_steps=48, burnin=24)
    model_problem = make_problem(label, truth_type="FLRW", seed=42, observation=observation, truth_params=baseline_problem.truth_params)
    model = run_posterior(model_problem.log_likelihood, model_problem.priors, seed=43, n_walkers=16, n_steps=48, burnin=24)
    result = bayes_factor(model, flrw)
    if label == "I":
        assert abs(result.ln_B) <= 2.0 * result.ln_B_err

