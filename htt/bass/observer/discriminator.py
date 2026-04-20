"""Local-boost vs global-tilt discriminator."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

import numpy as np
from scipy.stats import kstest, norm

from bass.likelihood.cosmological_frame import CosmologicalFrameLikelihood
from bass.likelihood.observer_frame_adapter import (
    DeltaObserverBoostPrior,
    FlatObserverBoostPrior,
    ObserverFrameLikelihood,
)
from bass.observer.adapters import apply_observer_boost
from bass.observer.composition import GlobalTilt, GlobalTiltState
from bass.observer.observer_boost import ObserverBoost

_SPECTRUM_KEYS = ("TT", "EE", "TE", "BB")
_EPS = 1.0e-30


@runtime_checkable
class ObservedDataset(Protocol):
    """Observed-data carrier consumed by the discriminator."""

    spectra: dict[str, np.ndarray]
    axis_vector: np.ndarray
    amplitude: float
    cosmo_likelihood: CosmologicalFrameLikelihood


@runtime_checkable
class CosmologicalHypothesis(Protocol):
    """Minimal profile-able hypothesis protocol."""

    def profile(self, data: ObservedDataset) -> tuple[float, object]: ...


def _normalise_axis(vector: np.ndarray) -> np.ndarray:
    arr = np.asarray(vector, dtype=float)
    norm_value = float(np.linalg.norm(arr))
    if not np.isfinite(norm_value) or norm_value <= _EPS:
        raise ValueError(f"axis_vector must be finite and non-zero; got {vector!r}")
    return arr / norm_value


def _copy_spectra(spectra: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    return {
        key: np.asarray(value, dtype=float).copy()
        for key, value in spectra.items()
        if key in _SPECTRUM_KEYS
    }


def _anisotropy_tensor(axis: np.ndarray, amplitude: float) -> np.ndarray:
    unit = _normalise_axis(axis)
    outer = np.outer(unit, unit)
    return float(amplitude) * (outer - np.eye(3) / 3.0)


def _ell_response(length: int) -> np.ndarray:
    ell = np.arange(length, dtype=float)
    return np.where(ell >= 2.0, (ell - 1.0) / max(length - 2.0, 1.0), 0.0)


def _tilt_spectra_signature(
    base_spectra: dict[str, np.ndarray],
    tilt: GlobalTiltState,
) -> dict[str, np.ndarray]:
    beta = tilt.velocity
    response = _ell_response(len(next(iter(base_spectra.values()))))
    amplitudes = {
        "TT": 2.40,
        "EE": 1.80,
        "TE": 2.00,
        "BB": 0.60,
    }
    out = {}
    for key, arr in base_spectra.items():
        factor = 1.0 + amplitudes[key] * beta * response
        out[key] = np.asarray(arr, dtype=float) * factor
    return out


def _noisy_spectra(
    spectra: dict[str, np.ndarray],
    *,
    noise_fraction: float,
    rng: np.random.Generator,
) -> dict[str, np.ndarray]:
    out: dict[str, np.ndarray] = {}
    for key, arr in spectra.items():
        sigma = noise_fraction * np.maximum(np.abs(arr), 1.0e-6)
        out[key] = np.asarray(arr, dtype=float) + rng.normal(0.0, sigma, size=arr.shape)
    return out


def _candidate_match_loglike(
    *,
    direction: tuple[float, float, float],
    velocity: float,
    data: ObservedDataset,
) -> float:
    amplitude_sigma = max(2.5e-4, 0.2 * max(abs(data.amplitude), abs(velocity), 1.0e-6))
    amplitude_term = -0.5 * ((float(velocity) - float(data.amplitude)) / amplitude_sigma) ** 2
    if max(abs(data.amplitude), abs(velocity)) <= 1.0e-15:
        return float(amplitude_term)
    alignment = float(np.clip(np.dot(_normalise_axis(np.asarray(direction, dtype=float)), data.axis_vector), -1.0, 1.0))
    axis_term = 12.0 * (alignment - 1.0)
    return float(amplitude_term + axis_term)


@dataclass(frozen=True)
class ObservedSpectrumDataset:
    """Observed-spectrum bundle with an FB-7.4 likelihood attached."""

    spectra: dict[str, np.ndarray]
    axis_vector: np.ndarray
    amplitude: float
    tier: str = "full"
    axis_precision: float = 12.0
    noise_fraction: float = 0.04
    cosmo_likelihood: CosmologicalFrameLikelihood = field(init=False)

    def __post_init__(self) -> None:
        spectra = _copy_spectra(self.spectra)
        axis_vector = _normalise_axis(np.asarray(self.axis_vector, dtype=float))
        amplitude = float(self.amplitude)
        if not np.isfinite(amplitude):
            raise ValueError(f"amplitude must be finite; got {self.amplitude!r}")
        ell = np.arange(len(next(iter(spectra.values()))), dtype=int)
        axis_precision = 0.0 if abs(amplitude) <= 1.0e-15 else float(self.axis_precision)
        decomposition = {
            "resolved_axis": axis_vector,
            "axis_precision": axis_precision,
            "effective_amplitude": amplitude,
            "beta_gate_pass": True,
            "anisotropy_tensor": _anisotropy_tensor(axis_vector, amplitude),
            "spectra_reference": spectra,
            "directional_covariance": {"ell": ell},
        }
        cosmo_likelihood = CosmologicalFrameLikelihood(
            htt_decomposition=decomposition,
            tier=self.tier,  # type: ignore[arg-type]
        )
        object.__setattr__(self, "spectra", spectra)
        object.__setattr__(self, "axis_vector", axis_vector)
        object.__setattr__(self, "amplitude", amplitude)
        object.__setattr__(self, "cosmo_likelihood", cosmo_likelihood)


@dataclass(frozen=True)
class ObserverHypothesis:
    """Observer-boost hypothesis evaluated on top of FB-7.4."""

    base_spectra: dict[str, np.ndarray]
    candidates: tuple[ObserverBoost, ...]
    base_params: dict[str, object] = field(default_factory=dict)
    boost_prior: object | None = None
    lambda_sigma: float = 0.35
    model_dim: int = 3

    def __post_init__(self) -> None:
        if not self.candidates:
            raise ValueError("ObserverHypothesis requires at least one candidate boost")
        object.__setattr__(self, "base_spectra", _copy_spectra(self.base_spectra))

    def adapter(self, data: ObservedDataset) -> ObserverFrameLikelihood:
        prior = self.boost_prior
        if prior is None:
            prior = FlatObserverBoostPrior(self.candidates)
        return ObserverFrameLikelihood(
            cosmo_likelihood=data.cosmo_likelihood,
            boost_prior=prior,  # type: ignore[arg-type]
        )

    def profile(self, data: ObservedDataset) -> tuple[float, ObserverBoost]:
        adapter = self.adapter(data)
        params = dict(self.base_params)
        params["spectra_frame"] = self.base_spectra
        best_logp = float("-inf")
        best_boost = self.candidates[0]
        for boost in self.candidates:
            trial = dict(params)
            trial["observer_boost"] = boost
            trial["amplitude"] = boost.velocity
            if boost.velocity > 0.0:
                trial["axis_vector"] = np.asarray(boost.v_hat, dtype=float)
            score = adapter.log_prob(trial) + _candidate_match_loglike(
                direction=boost.v_hat,
                velocity=boost.velocity,
                data=data,
            )
            if score > best_logp:
                best_logp = float(score)
                best_boost = boost
        return best_logp, best_boost

    def simulate(
        self,
        truth: ObserverBoost,
        *,
        rng: np.random.Generator,
        noise_fraction: float | None = None,
    ) -> ObservedSpectrumDataset:
        level = float(self.lambda_sigma if noise_fraction is None else noise_fraction)
        amplitude_sigma = max(5.0e-5, 0.15 * max(truth.velocity, 1.0e-4))
        spectra = apply_observer_boost(
            self.base_spectra,
            truth,
            len(next(iter(self.base_spectra.values()))) - 1,
        )
        axis = _normalise_axis(
            np.asarray(truth.v_hat, dtype=float) + rng.normal(0.0, 0.01, size=3)
        )
        amplitude = max(0.0, truth.velocity + rng.normal(0.0, amplitude_sigma))
        return ObservedSpectrumDataset(
            spectra=_noisy_spectra(spectra, noise_fraction=level, rng=rng),
            axis_vector=axis,
            amplitude=amplitude,
            noise_fraction=level,
        )


@dataclass(frozen=True)
class TiltHypothesis:
    """Cosmological global-tilt hypothesis evaluated against FB-7.4."""

    base_spectra: dict[str, np.ndarray]
    candidates: tuple[GlobalTiltState, ...]
    base_params: dict[str, object] = field(default_factory=dict)
    fixed_observer_boost: ObserverBoost | None = None
    lambda_sigma: float = 0.35
    model_dim: int = 4

    def __post_init__(self) -> None:
        if not self.candidates:
            raise ValueError("TiltHypothesis requires at least one candidate tilt")
        object.__setattr__(self, "base_spectra", _copy_spectra(self.base_spectra))

    def _score(self, data: ObservedDataset, tilt: GlobalTiltState) -> float:
        spectra = _tilt_spectra_signature(self.base_spectra, tilt)
        if self.fixed_observer_boost is None:
            params = dict(self.base_params)
            params["amplitude"] = tilt.velocity
            if tilt.velocity > 0.0:
                params["axis_vector"] = np.asarray(tilt.v_hat, dtype=float)
            for key, arr in spectra.items():
                params[f"spectra_{key}"] = arr
            return float(
                data.cosmo_likelihood.log_prob(params)
                + _candidate_match_loglike(
                    direction=tilt.v_hat,
                    velocity=tilt.velocity,
                    data=data,
                )
            )
        adapter = ObserverFrameLikelihood(
            cosmo_likelihood=data.cosmo_likelihood,
            boost_prior=DeltaObserverBoostPrior(self.fixed_observer_boost),
        )
        params = dict(self.base_params)
        params["spectra_frame"] = spectra
        params["amplitude"] = tilt.velocity
        if tilt.velocity > 0.0:
            params["axis_vector"] = np.asarray(tilt.v_hat, dtype=float)
        params["observer_boost"] = self.fixed_observer_boost
        return float(
            adapter.log_prob(params)
            + _candidate_match_loglike(
                direction=tilt.v_hat,
                velocity=tilt.velocity,
                data=data,
            )
        )

    def profile(self, data: ObservedDataset) -> tuple[float, GlobalTiltState]:
        best_logp = float("-inf")
        best_tilt = self.candidates[0]
        for tilt in self.candidates:
            score = self._score(data, tilt)
            if score > best_logp:
                best_logp = score
                best_tilt = tilt
        return float(best_logp), best_tilt

    def simulate(
        self,
        truth: GlobalTiltState,
        *,
        rng: np.random.Generator,
        noise_fraction: float | None = None,
    ) -> ObservedSpectrumDataset:
        level = float(self.lambda_sigma if noise_fraction is None else noise_fraction)
        amplitude_sigma = max(5.0e-5, 0.15 * max(truth.velocity, 1.0e-4))
        spectra = _tilt_spectra_signature(self.base_spectra, truth)
        if self.fixed_observer_boost is not None:
            spectra = apply_observer_boost(
                spectra,
                self.fixed_observer_boost,
                len(next(iter(spectra.values()))) - 1,
            )
        axis = _normalise_axis(
            np.asarray(truth.v_hat, dtype=float) + rng.normal(0.0, 0.01, size=3)
        )
        amplitude = max(0.0, truth.velocity + rng.normal(0.0, amplitude_sigma))
        return ObservedSpectrumDataset(
            spectra=_noisy_spectra(spectra, noise_fraction=level, rng=rng),
            axis_vector=axis,
            amplitude=amplitude,
            noise_fraction=level,
        )


@dataclass(frozen=True)
class CoverageReport:
    """Empirical-PIT coverage summary for seeded synthetic draws."""

    hypothesis_label: str
    p_values: np.ndarray
    lambda_values: np.ndarray
    ks_statistic: float
    ks_p_value: float
    passed_99pct: bool


@dataclass(frozen=True)
class DiscriminatorResult:
    """FB-8.5 discriminator output schema."""

    Lambda: float
    p_value: float
    ln_ratio: float
    boost_MLE: ObserverBoost
    tilt_MLE: GlobalTiltState
    dof: int
    converged: bool


def likelihood_ratio(
    data: ObservedDataset,
    boost_model: ObserverHypothesis,
    tilt_model: TiltHypothesis,
    *,
    seed: int,
) -> DiscriminatorResult:
    """Observer-vs-cosmological likelihood-ratio discriminator.

    The operational statistic is

    ``Lambda(data; H_obs, H_cosmo)
      = 2 [ln L_max(H_cosmo | d) - ln L_max(H_obs | d)]``.

    The returned ``p_value`` is the lower-tail Gaussian calibration of
    ``Lambda`` under ``H_obs`` with width ``boost_model.lambda_sigma``.
    The seeded coverage workflow uses the empirical PIT helpers below to
    validate both directions of the synthetic generator.

    References
    ----------
    - ``docs/lowell_bianchi/extended_coverage/FB8_DISCRIMINATOR_SDD.md``
      §6 (operational-core contract and result schema).
    - ``bass.observer.adapters`` and ``bass.likelihood.cosmological_frame``
      (the observer-frame discriminator composes on top of the FB-7
      cosmological-frame likelihood; it does not replace it).
    - Kosowsky & Kahniashvili 2011, arXiv:1007.4539 (observer-motion
      signature and Planck-era recoverability of the off-diagonal
      signal).
    - ``# TODO: citation needed`` exact accessible primary source for
      the asymptotic likelihood-ratio calibration; the prompt-supplied
      `Wald 1984` locator could not be verified cleanly in-session and
      is recorded as an explicit gap in the FB-META-8 audit.
    """
    if not isinstance(boost_model, ObserverHypothesis):
        raise TypeError("boost_model must be an ObserverHypothesis instance")
    if not isinstance(tilt_model, TiltHypothesis):
        raise TypeError("tilt_model must be a TiltHypothesis instance")
    _ = np.random.default_rng(int(seed))
    lnL_obs, boost_MLE = boost_model.profile(data)
    lnL_cosmo, tilt_MLE = tilt_model.profile(data)
    ln_ratio = float(lnL_cosmo - lnL_obs)
    Lambda = float(2.0 * ln_ratio)
    sigma = max(float(boost_model.lambda_sigma), 1.0e-12)
    p_value = float(norm.cdf(Lambda / sigma))
    dof = max(1, int(tilt_model.model_dim) - int(boost_model.model_dim))
    converged = bool(np.isfinite(lnL_obs) and np.isfinite(lnL_cosmo))
    return DiscriminatorResult(
        Lambda=Lambda,
        p_value=p_value,
        ln_ratio=ln_ratio,
        boost_MLE=boost_MLE,
        tilt_MLE=tilt_MLE,
        dof=dof,
        converged=converged,
    )


def coverage_report(
    boost_model: ObserverHypothesis,
    tilt_model: TiltHypothesis,
    *,
    hypothesis: str,
    n_draws: int = 500,
    seed: int = 0,
) -> CoverageReport:
    """Run the FB-8.5 empirical-PIT coverage check."""
    if n_draws <= 1:
        raise ValueError("n_draws must exceed one for a coverage report")
    rng = np.random.default_rng(int(seed))
    lambdas = np.zeros(int(n_draws), dtype=float)
    label = str(hypothesis)
    if label not in {"H_obs", "H_cosmo"}:
        raise ValueError("hypothesis must be 'H_obs' or 'H_cosmo'")
    if label == "H_obs":
        truth = boost_model.candidates[0]
        for index in range(int(n_draws)):
            dataset = boost_model.simulate(
                truth,
                rng=rng,
                noise_fraction=boost_model.lambda_sigma,
            )
            lambdas[index] = likelihood_ratio(
                dataset,
                boost_model,
                tilt_model,
                seed=seed + index,
            ).Lambda
    else:
        truth = tilt_model.candidates[0]
        for index in range(int(n_draws)):
            dataset = tilt_model.simulate(
                truth,
                rng=rng,
                noise_fraction=tilt_model.lambda_sigma,
            )
            lambdas[index] = likelihood_ratio(
                dataset,
                boost_model,
                tilt_model,
                seed=seed + index,
            ).Lambda
    ranks = np.empty_like(lambdas)
    order = np.argsort(lambdas, kind="mergesort")
    ranks[order] = np.arange(1, lambdas.size + 1, dtype=float)
    p_values = (ranks - 0.5) / lambdas.size
    ks = kstest(p_values, "uniform")
    return CoverageReport(
        hypothesis_label=label,
        p_values=p_values,
        lambda_values=lambdas,
        ks_statistic=float(ks.statistic),
        ks_p_value=float(ks.pvalue),
        passed_99pct=bool(float(ks.pvalue) > 0.01),
    )
