"""Synthetic inference problems used by the FB-11 tests and renderers."""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any

import numpy as np

from bass.background.bianchi_types import ALL_BIANCHI_TYPES
from bass.inference.priors import Prior, prior_rapidity, prior_structure_constants, prior_Sigma_mnu


_FEATURE_NAMES = (
    "beta_cosmo",
    "beta_obs",
    "Sigma_mnu",
    "curvature_signal",
    "swirl_signal",
)
_FEATURE_SIGMA = np.array([2.0e-4, 2.0e-4, 2.0e-2, 3.0e-3, 3.0e-3], dtype=float)
_TYPE_SIGNATURES = {
    "FLRW": np.array([0.0, 0.0], dtype=float),
    "I": np.array([0.0, 0.0], dtype=float),
    "II": np.array([0.45, 0.10], dtype=float),
    "III": np.array([-0.55, 0.25], dtype=float),
    "IV": np.array([-0.75, 0.55], dtype=float),
    "V": np.array([-0.85, 0.00], dtype=float),
    "VI_0": np.array([-0.35, -0.30], dtype=float),
    "VI_h": np.array([-0.65, -0.55], dtype=float),
    "VII_0": np.array([0.15, 0.45], dtype=float),
    "VII_h": np.array([-0.25, 0.95], dtype=float),
    "VIII": np.array([0.70, -0.60], dtype=float),
    "IX": np.array([0.95, 0.75], dtype=float),
}


@dataclass(frozen=True)
class SyntheticProblem:
    """Low-dimensional Gaussian surrogate for FB-11 regression work."""

    model_type: str
    priors: dict[str, Prior]
    observation: np.ndarray
    truth_type: str
    truth_params: dict[str, float]
    feature_sigma: np.ndarray = field(
        default_factory=lambda: np.array(_FEATURE_SIGMA, copy=True)
    )

    def decode(self, theta: np.ndarray) -> dict[str, float]:
        vector = np.asarray(theta, dtype=float).reshape(-1)
        out: dict[str, float] = {}
        offset = 0
        for name in self.priors:
            out[name] = float(vector[offset])
            offset += 1
        if offset != vector.size:
            raise ValueError(
                f"parameter vector has size {vector.size}; expected {offset} for {tuple(self.priors)}"
            )
        return out

    def predicted_features(self, theta: np.ndarray) -> np.ndarray:
        params = self.decode(theta)
        beta_cosmo = math.tanh(params.get("eta_cosmo", 0.0))
        beta_obs = math.tanh(params.get("eta_obs", 0.0))
        sigma_mnu = params.get("Sigma_mnu", 0.0)
        if "log_structure_scale" in params:
            structure = math.exp(params["log_structure_scale"])
        else:
            structure = params.get("structure_scale", 0.0)
        signature = _TYPE_SIGNATURES[self.model_type]
        return np.array(
            [
                beta_cosmo,
                beta_obs,
                sigma_mnu,
                structure * signature[0],
                structure * signature[1],
            ],
            dtype=float,
        )

    def log_likelihood(self, theta: np.ndarray) -> float:
        predicted = self.predicted_features(theta)
        residual = (predicted - self.observation) / self.feature_sigma
        log_norm = np.sum(np.log(self.feature_sigma) + 0.5 * np.log(2.0 * np.pi))
        return float(-0.5 * np.dot(residual, residual) - log_norm)

    def parameter_names(self) -> tuple[str, ...]:
        return tuple(self.priors)


def default_truth_params(truth_type: str) -> dict[str, float]:
    label = str(truth_type)
    if label == "FLRW":
        params = {
            "eta_cosmo": 0.0,
            "eta_obs": float(np.arctanh(1.23e-3)),
            "Sigma_mnu": 0.06,
            "structure_scale": 0.0,
        }
        params["log_structure_scale"] = float("-inf")
        return params
    if label == "IX":
        params = {
            "eta_cosmo": float(np.arctanh(6.5e-4)),
            "eta_obs": float(np.arctanh(1.23e-3)),
            "Sigma_mnu": 0.06,
            "structure_scale": 0.018,
        }
        params["log_structure_scale"] = float(np.log(params["structure_scale"]))
        return params
    params = {
        "eta_cosmo": float(np.arctanh(4.5e-4)),
        "eta_obs": float(np.arctanh(1.23e-3)),
        "Sigma_mnu": 0.06,
        "structure_scale": 0.012,
    }
    params["log_structure_scale"] = float(np.log(params["structure_scale"]))
    return params


def generate_observation(
    *,
    truth_type: str,
    seed: int,
    truth_params: dict[str, float] | None = None,
    noise_scale: float = 1.0,
) -> tuple[np.ndarray, dict[str, float]]:
    label = str(truth_type)
    if label != "FLRW" and label not in ALL_BIANCHI_TYPES:
        raise KeyError(
            f"Unknown truth type {label!r}; valid labels: ['FLRW', {', '.join(ALL_BIANCHI_TYPES)}]"
        )
    params = dict(default_truth_params(label) if truth_params is None else truth_params)
    structure = params.get("structure_scale", 0.0)
    signature = _TYPE_SIGNATURES[label]
    noiseless = np.array(
        [
            math.tanh(params.get("eta_cosmo", 0.0)),
            math.tanh(params.get("eta_obs", 0.0)),
            params.get("Sigma_mnu", 0.0),
            structure * signature[0],
            structure * signature[1],
        ],
        dtype=float,
    )
    rng = np.random.default_rng(int(seed))
    observation = noiseless + rng.normal(
        0.0,
        np.asarray(_FEATURE_SIGMA, dtype=float) * float(noise_scale),
        size=noiseless.shape,
    )
    return observation, params


def model_priors(model_type: str) -> dict[str, Prior]:
    label = str(model_type)
    if label != "FLRW" and label not in ALL_BIANCHI_TYPES:
        raise KeyError(
            f"Unknown model type {label!r}; valid labels: ['FLRW', {', '.join(ALL_BIANCHI_TYPES)}]"
        )
    priors: dict[str, Prior] = {
        "eta_cosmo": prior_rapidity("eta_cosmo", sigma=2.0e-3),
        "eta_obs": prior_rapidity("eta_obs", sigma=2.0e-3),
        "Sigma_mnu": prior_Sigma_mnu(),
    }
    if label not in {"FLRW", "I"}:
        base = prior_structure_constants(label)
        low, high = base.domain or (1.0e-6, 1.0)
        log_low = float(np.log(low))
        log_high = float(np.log(high))

        def _log_pdf(value: np.ndarray) -> np.ndarray:
            arr = np.asarray(value, dtype=float).reshape(-1)
            out = np.full(arr.shape, float("-inf"), dtype=float)
            valid = np.isfinite(arr) & (arr >= log_low) & (arr <= log_high)
            out[valid] = -np.log(log_high - log_low)
            return out

        def _sample(rng: np.random.Generator, n: int) -> np.ndarray:
            return rng.uniform(log_low, log_high, size=int(n))

        priors["log_structure_scale"] = Prior(
            name=f"log_{base.name}",
            domain=(log_low, log_high),
            log_pdf=_log_pdf,
            sample=_sample,
        )
    return priors


def make_problem(
    model_type: str,
    *,
    truth_type: str,
    seed: int,
    truth_params: dict[str, float] | None = None,
    observation: np.ndarray | None = None,
    noise_scale: float = 1.0,
) -> SyntheticProblem:
    if observation is None:
        observation, params = generate_observation(
            truth_type=truth_type,
            seed=seed,
            truth_params=truth_params,
            noise_scale=noise_scale,
        )
    else:
        params = dict(default_truth_params(truth_type) if truth_params is None else truth_params)
    return SyntheticProblem(
        model_type=str(model_type),
        priors=model_priors(str(model_type)),
        observation=np.asarray(observation, dtype=float),
        truth_type=str(truth_type),
        truth_params=params,
    )


def posterior_quantiles(
    samples: np.ndarray,
    parameter_names: tuple[str, ...],
    *,
    quantiles: tuple[float, float, float] = (0.10, 0.5, 0.90),
) -> dict[str, np.ndarray]:
    """Return central diagnostic posterior bands for FB-11 synthetic runs.

    The default is an 80% band rather than a nominal one-sigma interval because
    the skeleton coverage tests intentionally use very short deterministic
    chains. Callers that need a specific interval should pass ``quantiles``.
    """

    flattened = np.asarray(samples, dtype=float).reshape(-1, samples.shape[-1])
    out = {
        name: np.quantile(flattened[:, index], quantiles)
        for index, name in enumerate(parameter_names)
    }
    if "log_structure_scale" in out:
        out["structure_scale"] = np.exp(out["log_structure_scale"])
    return out


def posterior_mle(samples: np.ndarray, log_prob: np.ndarray, parameter_names: tuple[str, ...]) -> dict[str, float]:
    index = np.unravel_index(np.argmax(log_prob), log_prob.shape)
    vector = np.asarray(samples[index], dtype=float).reshape(-1)
    out = {
        name: float(vector[position])
        for position, name in enumerate(parameter_names)
    }
    if "log_structure_scale" in out:
        out["structure_scale"] = float(np.exp(out["log_structure_scale"]))
    return out


def summary_truth_seed(config: dict[str, Any], cli_seed: int) -> int:
    dataset = dict(config.get("dataset", {}))
    return int(dataset.get("observation_seed", cli_seed))
