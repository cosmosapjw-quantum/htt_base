"""Observer-frame likelihood adapter over the FB-7 cosmological stack."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol, TypeVar

import numpy as np

from bass.likelihood.cosmological_frame import CosmologicalFrameLikelihood
from bass.observer.adapters import apply_observer_boost, observed_alm_mixing
from bass.observer.observer_boost import ObserverBoost
from bass.species.tilted import V_HAT_E_DEFAULT, velocity_to_rapidity

T = TypeVar("T")
_SPECTRUM_KEYS = ("TT", "EE", "TE", "BB")


class Prior(Protocol[T]):
    """Prior carrier for observer boosts."""

    def log_prob(self, value: T) -> float: ...


def _logsumexp(values: list[float]) -> float:
    finite = [value for value in values if np.isfinite(value)]
    if not finite:
        return float("-inf")
    pivot = max(finite)
    return float(pivot + np.log(sum(np.exp(value - pivot) for value in finite)))


def _observer_boost_from_params(params: dict[str, object]) -> ObserverBoost:
    if "observer_boost" in params:
        boost = params["observer_boost"]
        if not isinstance(boost, ObserverBoost):
            raise TypeError(
                "observer_boost must be an ObserverBoost instance; "
                "silent coercion is forbidden."
            )
        return boost
    if "beta_obs" in params or "v_hat_obs" in params:
        beta_obs = float(params.get("beta_obs", 0.0))
        v_hat_obs = tuple(
            float(component)
            for component in params.get("v_hat_obs", V_HAT_E_DEFAULT)  # type: ignore[arg-type]
        )
        return ObserverBoost(
            rapidity=velocity_to_rapidity(beta_obs),
            v_hat=v_hat_obs,
        )
    if "rapidity_obs" in params:
        v_hat_obs = tuple(
            float(component)
            for component in params.get("v_hat_obs", V_HAT_E_DEFAULT)  # type: ignore[arg-type]
        )
        return ObserverBoost(rapidity=float(params["rapidity_obs"]), v_hat=v_hat_obs)
    return ObserverBoost(rapidity=0.0)


def _extract_frame_spectra(
    params: dict[str, object],
    fallback: dict[str, np.ndarray],
) -> dict[str, np.ndarray]:
    if "spectra_frame" in params:
        payload = params["spectra_frame"]
        if not isinstance(payload, dict):
            raise TypeError("spectra_frame must be a dict[str, ndarray]")
        return {
            key: np.asarray(value, dtype=float)
            for key, value in payload.items()
            if key in _SPECTRUM_KEYS
        }
    extracted: dict[str, np.ndarray] = {}
    for key in _SPECTRUM_KEYS:
        frame_key = f"spectra_{key}_frame"
        if frame_key in params:
            extracted[key] = np.asarray(params[frame_key], dtype=float)
        elif f"spectra_{key}" in params:
            extracted[key] = np.asarray(params[f"spectra_{key}"], dtype=float)
    if extracted:
        return extracted
    return {
        key: np.asarray(value, dtype=float)
        for key, value in fallback.items()
        if key in _SPECTRUM_KEYS
    }


def _extract_frame_alms(
    params: dict[str, object],
    fallback: dict[str, np.ndarray] | None,
) -> dict[str, np.ndarray]:
    if fallback is None:
        fallback = {}
    if "alm_frame" in params:
        payload = params["alm_frame"]
        if not isinstance(payload, dict):
            raise TypeError("alm_frame must be a dict[str, ndarray]")
        return {
            key: np.asarray(value, dtype=float)
            for key, value in payload.items()
            if key in {"alm_T", "alm_E", "alm_B"}
        }
    extracted: dict[str, np.ndarray] = {}
    for key in ("alm_T", "alm_E", "alm_B"):
        frame_key = f"{key}_frame"
        if frame_key in params:
            extracted[key] = np.asarray(params[frame_key], dtype=float)
        elif key in params:
            extracted[key] = np.asarray(params[key], dtype=float)
        elif key in fallback:
            extracted[key] = np.asarray(fallback[key], dtype=float)
    return extracted


def _restrict_to_support(
    values: np.ndarray,
    support: tuple[object, ...],
) -> np.ndarray:
    out = np.zeros(len(support), dtype=float)
    for idx, row in enumerate(support):
        if not isinstance(row, Mapping):
            raise TypeError("harmonic_support entries must be mappings")
        flat_index = int(row["flat_index"])
        out[idx] = float(values[flat_index])
    return out


@dataclass(frozen=True)
class FlatObserverBoostPrior:
    """Uninformative finite-support prior used by profiling surfaces."""

    support: tuple[ObserverBoost, ...] = ()

    def log_prob(self, value: ObserverBoost) -> float:
        return 0.0

    def support_points(self) -> tuple[ObserverBoost, ...]:
        if self.support:
            return self.support
        return (ObserverBoost(rapidity=0.0),)


@dataclass(frozen=True)
class DeltaObserverBoostPrior:
    """Delta prior at a single observer boost."""

    value: ObserverBoost

    def log_prob(self, value: ObserverBoost) -> float:
        return 0.0 if value == self.value else float("-inf")

    def support_points(self) -> tuple[ObserverBoost, ...]:
        return (self.value,)


@dataclass(frozen=True)
class GaussianObserverBoostPrior:
    """Gaussian rapidity prior anchored at a fixed observer direction."""

    mean: ObserverBoost
    sigma_rapidity: float
    num_points: int = 17
    support_sigma: float = 3.0

    def __post_init__(self) -> None:
        sigma = float(self.sigma_rapidity)
        if not np.isfinite(sigma) or sigma <= 0.0:
            raise ValueError(
                f"sigma_rapidity must be positive and finite; got {self.sigma_rapidity!r}"
            )
        if int(self.num_points) < 2:
            raise ValueError("num_points must be at least 2")
        if float(self.support_sigma) <= 0.0:
            raise ValueError("support_sigma must be positive")
        object.__setattr__(self, "sigma_rapidity", sigma)
        object.__setattr__(self, "num_points", int(self.num_points))
        object.__setattr__(self, "support_sigma", float(self.support_sigma))

    def log_prob(self, value: ObserverBoost) -> float:
        if tuple(value.v_hat) != tuple(self.mean.v_hat):
            return float("-inf")
        delta = (value.rapidity - self.mean.rapidity) / self.sigma_rapidity
        return float(
            -0.5 * delta * delta
            - np.log(self.sigma_rapidity)
            - 0.5 * np.log(2.0 * np.pi)
        )

    def support_points(self) -> tuple[ObserverBoost, ...]:
        grid = np.linspace(
            max(0.0, self.mean.rapidity - self.support_sigma * self.sigma_rapidity),
            self.mean.rapidity + self.support_sigma * self.sigma_rapidity,
            self.num_points,
        )
        return tuple(
            ObserverBoost(rapidity=float(rapidity), v_hat=self.mean.v_hat)
            for rapidity in grid
        )


class ObserverFrameLikelihood:
    """Observer-frame likelihood wrapper.

    This class wraps an FB-7 cosmological-frame likelihood so that
    observer-frame boost parameters can be layered on top as a separate
    axis. It must not fold observer boosts back into the cosmological-
    frame class itself.

    References
    ----------
    - ``docs/lowell_bianchi/extended_coverage/FB8_DISCRIMINATOR_SDD.md``
      §7 (canonical likelihood-stack ingest contract).
    - ``bass.likelihood.cosmological_frame`` (the FB-7 cosmological-only
      base surface this adapter composes over).
    - Kosowsky & Kahniashvili 2011, arXiv:1007.4539 (observer-motion
      signal scale and recoverability context for the boost prior).
    - ``# TODO: citation needed`` exact on-disk Lowell ``§14`` locator;
      the prompt-supplied historical Lowell reference is absent in this
      worktree and remains an explicit audit gap rather than an invented
      citation.
    """

    def __init__(
        self,
        *,
        cosmo_likelihood: CosmologicalFrameLikelihood,
        boost_prior: Prior[ObserverBoost],
    ) -> None:
        if not isinstance(cosmo_likelihood, CosmologicalFrameLikelihood):
            raise TypeError(
                "cosmo_likelihood must be a CosmologicalFrameLikelihood instance"
            )
        self.cosmo_likelihood = cosmo_likelihood
        self.boost_prior = boost_prior

    def _support_points(self, params: dict[str, object]) -> tuple[ObserverBoost, ...]:
        if "boost_grid" in params:
            grid = tuple(params["boost_grid"])  # type: ignore[arg-type]
            if not all(isinstance(item, ObserverBoost) for item in grid):
                raise TypeError("boost_grid entries must all be ObserverBoost values")
            return grid
        if hasattr(self.boost_prior, "support_points"):
            support = tuple(self.boost_prior.support_points())  # type: ignore[attr-defined]
            if support:
                return support
        return (_observer_boost_from_params(dict(params)),)

    def _adapt_params(
        self,
        params: dict[str, object],
        *,
        boost: ObserverBoost,
    ) -> dict[str, object]:
        skipped_keys = {
            "observer_boost",
            "beta_obs",
            "v_hat_obs",
            "rapidity_obs",
            "boost_grid",
            "spectra_frame",
        }
        skipped_keys.update({f"spectra_{key}_frame" for key in _SPECTRUM_KEYS})
        forwarded = {
            key: value for key, value in params.items()
            if key not in skipped_keys
        }
        frame_spectra = _extract_frame_spectra(params, self.cosmo_likelihood.spectra_reference)
        fallback_alms = None
        if self.cosmo_likelihood.alm_reference_packed is not None:
            fallback_alms = {
                "alm_T": np.asarray(self.cosmo_likelihood.alm_reference_packed["alm_T"], dtype=float),
                "alm_E": np.asarray(self.cosmo_likelihood.alm_reference_packed["alm_E"], dtype=float),
                "alm_B": np.asarray(self.cosmo_likelihood.alm_reference_packed["alm_B"], dtype=float),
            }
        frame_alms = _extract_frame_alms(params, fallback_alms)
        ell_max = len(self.cosmo_likelihood.ell) - 1
        adapted = (
            {key: np.array(value, copy=True) for key, value in frame_spectra.items()}
            if boost.rapidity == 0.0
            else apply_observer_boost(frame_spectra, boost, ell_max)
        )
        for key in _SPECTRUM_KEYS:
            if key in adapted:
                forwarded[f"spectra_{key}"] = adapted[key]
        if frame_alms:
            adapted_alms = (
                {key: np.array(value, copy=True) for key, value in frame_alms.items()}
                if boost.rapidity == 0.0
                else {
                    key: observed_alm_mixing(value, boost, ell_max)
                    for key, value in frame_alms.items()
                }
            )
            if self.cosmo_likelihood.harmonic_gaussian_ready:
                adapted_alms = {
                    key: _restrict_to_support(
                        np.asarray(value, dtype=float),
                        self.cosmo_likelihood.harmonic_support,
                    )
                    for key, value in adapted_alms.items()
                }
            forwarded.update(adapted_alms)
        if boost.velocity > 0.0 and "axis_vector" not in forwarded and "preferred_axis" not in forwarded:
            forwarded["axis_vector"] = np.asarray(boost.v_hat, dtype=float)
        if (
            boost.velocity > 0.0
            and "amplitude" not in forwarded
            and "anisotropy_amplitude" not in forwarded
        ):
            forwarded["amplitude"] = boost.velocity
        return forwarded

    def log_prob(self, params: dict[str, object]) -> float:
        """Evaluate the observer-frame log-likelihood."""
        local = dict(params)
        boost = _observer_boost_from_params(local)
        prior_logp = float(self.boost_prior.log_prob(boost))
        if not np.isfinite(prior_logp):
            return float("-inf")
        adapted = self._adapt_params(local, boost=boost)
        return float(self.cosmo_likelihood.log_prob(adapted) + prior_logp)

    def marginalise_boost(self, params: dict[str, object]) -> float:
        """Marginalise the observer-frame likelihood over support boosts."""
        local = dict(params)
        support = self._support_points(local)
        scores = []
        for boost in support:
            trial = dict(local)
            trial["observer_boost"] = boost
            scores.append(self.log_prob(trial))
        return float(_logsumexp(scores) - np.log(len(scores)))

    def profile_boost(
        self, params: dict[str, object]
    ) -> tuple[float, ObserverBoost]:
        """Profile the observer-frame likelihood over support boosts."""
        local = dict(params)
        support = self._support_points(local)
        best_logp = float("-inf")
        best_boost = support[0]
        for boost in support:
            trial = dict(local)
            trial["observer_boost"] = boost
            if "amplitude" not in trial and "anisotropy_amplitude" not in trial:
                trial["amplitude"] = boost.velocity
            if (
                boost.velocity > 0.0
                and "axis_vector" not in trial
                and "preferred_axis" not in trial
            ):
                trial["axis_vector"] = np.asarray(boost.v_hat, dtype=float)
            score = self.log_prob(trial)
            if score > best_logp:
                best_logp = score
                best_boost = boost
        return float(best_logp), best_boost
