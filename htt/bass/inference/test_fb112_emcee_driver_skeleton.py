from __future__ import annotations

import inspect
from dataclasses import is_dataclass
from pathlib import Path

import numpy as np
import pytest
import yaml

from bass.inference import PosteriorSample, Prior, run_posterior
from bass.inference.__main__ import build_parser, main


def _gaussian_prior(name: str, sigma: float = 1.0) -> Prior:
    sigma = float(sigma)

    def log_pdf(value: np.ndarray) -> np.ndarray:
        x = np.asarray(value, dtype=float).reshape(-1)
        return -0.5 * (x / sigma) ** 2 - np.log(sigma) - 0.5 * np.log(2.0 * np.pi)

    def sample(rng: np.random.Generator, n: int) -> np.ndarray:
        return rng.normal(0.0, sigma, size=int(n))

    return Prior(name=name, domain=None, log_pdf=log_pdf, sample=sample)


def _toy_likelihood(theta: np.ndarray) -> float:
    target = np.array([0.25, -0.35], dtype=float)
    sigma = 0.15
    delta = np.asarray(theta, dtype=float) - target
    return float(
        -0.5 * np.dot(delta, delta) / (sigma * sigma)
        - theta.size * np.log(sigma)
        - 0.5 * theta.size * np.log(2.0 * np.pi)
    )


def _toy_priors() -> dict[str, Prior]:
    return {"x": _gaussian_prior("x"), "y": _gaussian_prior("y")}


def test_fb112_posterior_sample_is_a_dataclass() -> None:
    assert is_dataclass(PosteriorSample)


def test_fb112_run_posterior_signature_keeps_public_contract() -> None:
    signature = inspect.signature(run_posterior)
    assert signature.parameters["seed"].default is inspect._empty
    assert signature.parameters["n_walkers"].default == 64
    assert signature.parameters["n_steps"].default == 5000
    assert signature.parameters["burnin"].default == 1000
    assert signature.parameters["parallel"].default is False


def test_fb112_single_thread_seed_roundtrip_is_byte_identical() -> None:
    lhs = run_posterior(_toy_likelihood, _toy_priors(), seed=42, n_walkers=16, n_steps=96, burnin=48)
    rhs = run_posterior(_toy_likelihood, _toy_priors(), seed=42, n_walkers=16, n_steps=96, burnin=48)
    assert np.array_equal(lhs.samples, rhs.samples)
    assert np.array_equal(lhs.log_prob, rhs.log_prob)
    for key in lhs.diagnostics:
        left = lhs.diagnostics[key]
        right = rhs.diagnostics[key]
        if isinstance(left, np.ndarray):
            assert np.array_equal(left, right)
        elif isinstance(left, dict):
            assert left.keys() == right.keys()
            for inner_key in left:
                assert left[inner_key] == right[inner_key]
        else:
            assert left == right


@pytest.mark.parametrize("seed", [1, 7, 42, 99])
def test_fb112_repeated_seed_is_deterministic(seed: int) -> None:
    lhs = run_posterior(_toy_likelihood, _toy_priors(), seed=seed, n_walkers=12, n_steps=64, burnin=32)
    rhs = run_posterior(_toy_likelihood, _toy_priors(), seed=seed, n_walkers=12, n_steps=64, burnin=32)
    assert np.array_equal(lhs.samples, rhs.samples)


@pytest.mark.parametrize("seed_a,seed_b", [(1, 2), (7, 8), (41, 42)])
def test_fb112_different_seeds_change_the_chain(seed_a: int, seed_b: int) -> None:
    lhs = run_posterior(_toy_likelihood, _toy_priors(), seed=seed_a, n_walkers=12, n_steps=64, burnin=32)
    rhs = run_posterior(_toy_likelihood, _toy_priors(), seed=seed_b, n_walkers=12, n_steps=64, burnin=32)
    assert not np.array_equal(lhs.samples, rhs.samples)


def test_fb112_parallel_path_is_documentedly_nondeterministic() -> None:
    lhs = run_posterior(_toy_likelihood, _toy_priors(), seed=42, n_walkers=12, n_steps=48, burnin=24, parallel=True)
    rhs = run_posterior(_toy_likelihood, _toy_priors(), seed=42, n_walkers=12, n_steps=48, burnin=24, parallel=True)
    assert not np.array_equal(lhs.log_prob, rhs.log_prob)


@pytest.mark.parametrize("walkers", [4, 8, 16, 24])
def test_fb112_output_shapes_match_public_contract(walkers: int) -> None:
    posterior = run_posterior(_toy_likelihood, _toy_priors(), seed=5, n_walkers=walkers, n_steps=40, burnin=20)
    assert posterior.samples.shape == (walkers, 40, 2)
    assert posterior.log_prob.shape == (walkers, 40)


def test_fb112_sampler_string_mentions_emcee() -> None:
    posterior = run_posterior(_toy_likelihood, _toy_priors(), seed=6, n_walkers=12, n_steps=32, burnin=16)
    assert "emcee" in posterior.sampler


def test_fb112_thermodynamic_integration_metadata_is_recorded() -> None:
    posterior = run_posterior(_toy_likelihood, _toy_priors(), seed=7, n_walkers=12, n_steps=40, burnin=20)
    ti = dict(posterior.config["thermodynamic_integration"])
    assert {"beta_grid", "mean_log_likelihood", "stderr_log_likelihood", "ln_Z", "ln_Z_err"} <= set(ti)


def test_fb112_parser_exposes_config_and_seed() -> None:
    parser = build_parser()
    option_strings = {option for action in parser._actions for option in action.option_strings}
    assert "--config" in option_strings
    assert "--seed" in option_strings


def test_fb112_cli_returns_nonzero_when_summary_row_is_not_converged(tmp_path: Path) -> None:
    config = {
        "dataset": {"kind": "synthetic_planck2018", "truth_type": "IX"},
        "models": {"baseline": "FLRW", "type_labels": list(("I", "II", "III", "IV", "V", "VI_0", "VI_h", "VII_0", "VII_h", "VIII", "IX"))},
        "outputs": {
            "summary_json": str(tmp_path / "summary.json"),
            "summary_markdown": str(tmp_path / "summary.md"),
            "posterior_dir": str(tmp_path / "posteriors"),
        },
        "sampler": {"n_walkers": 12, "n_steps": 12, "burnin": 6, "parallel": False},
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    assert main(["--config", str(config_path), "--seed", "42"]) == 1
