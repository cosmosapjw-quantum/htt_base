"""Deterministic emcee-backed posterior driver for FB-11."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable
import math

import numpy as np

from bass.inference.diagnostics import (
    ESS_THRESHOLD,
    GEWEKE_ABS_Z_THRESHOLD,
    R_HAT_THRESHOLD,
    ess,
    geweke,
    r_hat,
)
from bass.inference.priors import Prior


LikelihoodFn = Callable[[np.ndarray], float]
_DEFAULT_BETA_LADDER = np.array([0.0, 0.05, 0.15, 0.35, 0.60, 1.0], dtype=float)
_PILOT_SCALE_FLOOR = 1.0e-6
_INITIAL_RETRY_LIMIT = 256


@dataclass(frozen=True)
class PosteriorSample:
    """Posterior samples and reproducibility metadata."""

    samples: np.ndarray
    log_prob: np.ndarray
    seed: int
    sampler: str
    config: dict[str, Any]
    diagnostics: dict[str, Any]


@dataclass(frozen=True)
class _PriorSpec:
    name: str
    prior: Prior
    width: int
    offset: int

    @property
    def slc(self) -> slice:
        return slice(self.offset, self.offset + self.width)


@dataclass(frozen=True)
class _EnsembleRun:
    samples: np.ndarray
    log_prob: np.ndarray
    log_like: np.ndarray
    acceptance_fraction: np.ndarray


class _ExecutorMapPool:
    """Small adapter exposing the `map` interface emcee expects."""

    def __init__(self, max_workers: int) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    def map(self, func: Callable[[np.ndarray], Any], items: list[np.ndarray]) -> list[Any]:
        return list(self._executor.map(func, items))

    def close(self) -> None:
        self._executor.shutdown(wait=True)


def _emcee_version() -> str:
    import emcee  # type: ignore

    return str(getattr(emcee, "__version__", "unknown"))


def _emcee_sampler_name() -> str:
    return f"emcee-{_emcee_version()}"


def _prior_width(prior: Prior) -> int:
    probe = prior.sample(np.random.default_rng(0), 1)
    array = np.asarray(probe, dtype=float)
    if array.ndim == 0:
        return 1
    if array.ndim == 1:
        return 1 if array.size == 1 else array.size
    if array.ndim == 2:
        return int(array.shape[1])
    raise ValueError(f"unsupported prior sample shape {array.shape}")


def _build_prior_specs(priors: dict[str, Prior]) -> tuple[list[_PriorSpec], int]:
    offset = 0
    specs: list[_PriorSpec] = []
    for name, prior in priors.items():
        width = _prior_width(prior)
        specs.append(_PriorSpec(name=name, prior=prior, width=width, offset=offset))
        offset += width
    return specs, offset


def _extract_value(theta: np.ndarray, spec: _PriorSpec) -> np.ndarray:
    if spec.width == 0:
        return np.empty((0,), dtype=float)
    value = theta[spec.slc]
    if spec.width == 1:
        return np.asarray([float(value[0])], dtype=float)
    return np.asarray(value, dtype=float)


def _sample_from_priors(
    specs: list[_PriorSpec],
    *,
    rng: np.random.Generator,
    n: int,
) -> np.ndarray:
    if not specs:
        return np.empty((int(n), 0), dtype=float)
    positions = np.zeros((int(n), specs[-1].offset + specs[-1].width), dtype=float)
    for spec in specs:
        draws = np.asarray(spec.prior.sample(rng, int(n)), dtype=float)
        if spec.width == 0:
            continue
        if spec.width == 1:
            positions[:, spec.slc] = draws.reshape(int(n), 1)
        else:
            positions[:, spec.slc] = draws.reshape(int(n), spec.width)
    return positions


def _prior_log_prob(theta: np.ndarray, specs: list[_PriorSpec]) -> float:
    total = 0.0
    for spec in specs:
        value = _extract_value(theta, spec)
        log_pdf = np.asarray(spec.prior.log_pdf(value), dtype=float).reshape(-1)
        contribution = float(log_pdf[0]) if log_pdf.size else 0.0
        if not np.isfinite(contribution):
            return float("-inf")
        total += contribution
    return float(total)


def _tempered_log_prob(
    theta: np.ndarray,
    *,
    likelihood: LikelihoodFn,
    specs: list[_PriorSpec],
    beta: float,
) -> tuple[float, float, float]:
    log_prior = _prior_log_prob(theta, specs)
    if not np.isfinite(log_prior):
        return float("-inf"), float("-inf"), float("-inf")
    log_like = float(likelihood(np.asarray(theta, dtype=float)))
    if not np.isfinite(log_like):
        return float("-inf"), log_prior, float("-inf")
    return float(log_prior + float(beta) * log_like), log_prior, log_like


def _make_base_rng(seed: int, *, deterministic: bool) -> np.random.Generator:
    if deterministic:
        return np.random.default_rng(int(seed))
    return np.random.default_rng()


def _random_state_from_rng(rng: np.random.Generator) -> tuple[Any, ...]:
    return np.random.RandomState(int(rng.integers(0, 2**31 - 1))).get_state()


def _spawn_rngs(rng: np.random.Generator, count: int) -> list[np.random.Generator]:
    return [
        np.random.default_rng(int(rng.integers(0, 2**32 - 1)))
        for _ in range(int(count))
    ]


def _choose_n_ensembles(n_walkers: int, ndim: int) -> int:
    preferred_minimum = max(int(ndim) + 2, 4)
    for n_ensembles in (4, 3, 2):
        if int(n_walkers) % n_ensembles != 0:
            continue
        walkers_per_ensemble = int(n_walkers) // n_ensembles
        if walkers_per_ensemble >= preferred_minimum and walkers_per_ensemble % 2 == 0:
            return n_ensembles
    for n_ensembles in (4, 3, 2):
        if int(n_walkers) % n_ensembles != 0:
            continue
        walkers_per_ensemble = int(n_walkers) // n_ensembles
        if walkers_per_ensemble >= 2 and walkers_per_ensemble % 2 == 0:
            return n_ensembles
    if int(n_walkers) % 2 != 0:
        raise ValueError("n_walkers must be even")
    return 1


def _pilot_positions(
    *,
    likelihood: LikelihoodFn,
    specs: list[_PriorSpec],
    beta: float,
    rng: np.random.Generator,
    n_points: int,
) -> tuple[np.ndarray, np.ndarray]:
    positions = _sample_from_priors(specs, rng=rng, n=int(n_points))
    rows = [
        _tempered_log_prob(theta, likelihood=likelihood, specs=specs, beta=beta)
        for theta in positions
    ]
    log_prob = np.array([row[0] for row in rows], dtype=float)
    finite = np.isfinite(log_prob)
    if not np.any(finite):
        raise RuntimeError("failed to draw any finite pilot points from the priors")
    filtered_positions = positions[finite]
    filtered_log_prob = log_prob[finite]
    order = np.argsort(filtered_log_prob)[::-1]
    return filtered_positions[order], filtered_log_prob[order]


def _jittered_initial_positions(
    *,
    likelihood: LikelihoodFn,
    specs: list[_PriorSpec],
    beta: float,
    base_rng: np.random.Generator,
    n_walkers: int,
) -> np.ndarray:
    ndim = specs[-1].offset + specs[-1].width if specs else 0
    n_pilot = max(32 * int(n_walkers), 128)
    pilot_positions, pilot_log_prob = _pilot_positions(
        likelihood=likelihood,
        specs=specs,
        beta=beta,
        rng=base_rng,
        n_points=n_pilot,
    )
    elite_count = min(max(4 * int(n_walkers), int(n_walkers)), pilot_positions.shape[0])
    elite = np.asarray(pilot_positions[:elite_count], dtype=float)
    scale = np.std(elite, axis=0, ddof=1) if elite.shape[0] > 1 else np.ones(ndim, dtype=float)
    scale = np.where(np.isfinite(scale) & (scale > _PILOT_SCALE_FLOOR), scale, 0.25)
    jitter_scale = np.maximum(0.15 * scale, _PILOT_SCALE_FLOOR)
    walker_rngs = _spawn_rngs(base_rng, int(n_walkers))
    positions = np.zeros((int(n_walkers), int(ndim)), dtype=float)
    for index, rng in enumerate(walker_rngs):
        anchor = elite[index % elite.shape[0]]
        accepted = False
        for _ in range(_INITIAL_RETRY_LIMIT):
            proposal = np.asarray(anchor, dtype=float) + rng.normal(0.0, jitter_scale, size=ndim)
            log_prob, _, log_like = _tempered_log_prob(
                proposal,
                likelihood=likelihood,
                specs=specs,
                beta=beta,
            )
            if np.isfinite(log_prob) and np.isfinite(log_like):
                positions[index] = proposal
                accepted = True
                break
        if accepted:
            continue
        positions[index] = elite[int(np.argmax(pilot_log_prob[:elite.shape[0]]))]
    return positions


def _build_moves(
    ndim: int,
    proposal_scale: np.ndarray,
    *,
    live_dangerously: bool,
) -> list[tuple[Any, float]]:
    import emcee  # type: ignore

    diag_cov = np.square(np.maximum(np.asarray(proposal_scale, dtype=float), _PILOT_SCALE_FLOOR))
    if live_dangerously:
        return [(emcee.moves.GaussianMove(cov=diag_cov, mode="vector"), 1.0)]
    return [
        (emcee.moves.StretchMove(a=2.0), 0.60),
        (emcee.moves.DEMove(), 0.30),
        (emcee.moves.GaussianMove(cov=diag_cov, mode="vector"), 0.10),
    ]


def _run_single_ensemble(
    *,
    likelihood: LikelihoodFn,
    specs: list[_PriorSpec],
    initial_positions: np.ndarray,
    seed_rng: np.random.Generator,
    n_steps: int,
    burnin: int,
    beta: float,
    parallel: bool,
) -> _EnsembleRun:
    import emcee  # type: ignore

    proposal_scale = (
        np.std(initial_positions, axis=0, ddof=1)
        if initial_positions.shape[0] > 1
        else np.ones(initial_positions.shape[1], dtype=float)
    )
    proposal_scale = np.where(
        np.isfinite(proposal_scale) & (proposal_scale > _PILOT_SCALE_FLOOR),
        proposal_scale,
        0.25,
    )

    def _log_prob(theta: np.ndarray) -> tuple[float, float]:
        log_post, _, log_like = _tempered_log_prob(
            np.asarray(theta, dtype=float),
            likelihood=likelihood,
            specs=specs,
            beta=beta,
        )
        return log_post, log_like

    pool: _ExecutorMapPool | None = None
    if parallel:
        pool = _ExecutorMapPool(max_workers=min(initial_positions.shape[0], 8))
    try:
        live_dangerously = bool(initial_positions.shape[0] < 2 * initial_positions.shape[1])
        sampler = emcee.EnsembleSampler(
            initial_positions.shape[0],
            initial_positions.shape[1],
            _log_prob,
            moves=_build_moves(
                initial_positions.shape[1],
                proposal_scale,
                live_dangerously=live_dangerously,
            ),
            pool=pool,
        )
        sampler.random_state = _random_state_from_rng(seed_rng)
        state = sampler.run_mcmc(
            initial_positions,
            int(burnin),
            progress=False,
            skip_initial_state_check=True,
        )
        sampler.reset()
        sampler.run_mcmc(
            state,
            int(n_steps),
            progress=False,
            skip_initial_state_check=True,
        )
        chain = np.asarray(sampler.get_chain(flat=False), dtype=float).transpose(1, 0, 2)
        log_prob = np.asarray(sampler.get_log_prob(flat=False), dtype=float).transpose(1, 0)
        blobs = np.asarray(sampler.get_blobs(flat=False), dtype=float).transpose(1, 0)
        acceptance = np.asarray(sampler.acceptance_fraction, dtype=float)
    finally:
        if pool is not None:
            pool.close()
    return _EnsembleRun(
        samples=chain,
        log_prob=log_prob,
        log_like=blobs,
        acceptance_fraction=acceptance,
    )


def _run_partitioned_ensembles(
    *,
    likelihood: LikelihoodFn,
    priors: dict[str, Prior],
    seed: int,
    n_walkers: int,
    n_steps: int,
    burnin: int,
    beta: float,
    parallel: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    specs, ndim = _build_prior_specs(priors)
    n_ensembles = _choose_n_ensembles(int(n_walkers), int(ndim))
    walkers_per_ensemble = int(n_walkers) // n_ensembles
    base_rng = _make_base_rng(int(seed), deterministic=not parallel)
    initial_positions = _jittered_initial_positions(
        likelihood=likelihood,
        specs=specs,
        beta=beta,
        base_rng=base_rng,
        n_walkers=int(n_walkers),
    ).reshape(n_ensembles, walkers_per_ensemble, ndim)
    ensemble_rngs = _spawn_rngs(base_rng, n_ensembles)
    runs = [
        _run_single_ensemble(
            likelihood=likelihood,
            specs=specs,
            initial_positions=initial_positions[index],
            seed_rng=ensemble_rngs[index],
            n_steps=int(n_steps),
            burnin=int(burnin),
            beta=beta,
            parallel=bool(parallel),
        )
        for index in range(n_ensembles)
    ]
    samples = np.stack([run.samples for run in runs], axis=0)
    log_prob = np.stack([run.log_prob for run in runs], axis=0)
    log_like = np.stack([run.log_like for run in runs], axis=0)
    acceptance = np.stack([run.acceptance_fraction for run in runs], axis=0)
    return samples, log_prob, log_like, acceptance


def _diagnostic_chains(samples: np.ndarray) -> np.ndarray:
    if samples.ndim != 4:
        raise ValueError(
            f"expected (n_ensembles, n_walkers, n_steps, n_dim); got {samples.shape}"
        )
    return np.mean(np.asarray(samples, dtype=float), axis=1)


def _diagnostic_draws(samples: np.ndarray) -> np.ndarray:
    if samples.ndim != 4:
        raise ValueError(
            f"expected (n_ensembles, n_walkers, n_steps, n_dim); got {samples.shape}"
        )
    array = np.asarray(samples, dtype=float)
    return array.transpose(0, 2, 1, 3).reshape(
        array.shape[0],
        array.shape[2] * array.shape[1],
        array.shape[3],
    )


def _hybrid_convergence_report(samples: np.ndarray) -> dict[str, Any]:
    mean_view = _diagnostic_chains(samples)
    draw_view = _diagnostic_draws(samples)
    rhat = r_hat(draw_view)
    ess_value = ess(draw_view)
    geweke_value = geweke(mean_view)
    return {
        "mean_by_step": np.mean(mean_view, axis=0),
        "std_by_step": np.std(mean_view, axis=0, ddof=1),
        "chain_means": np.mean(mean_view, axis=1),
        "r_hat": rhat,
        "ess": ess_value,
        "geweke_z": geweke_value,
        "thresholds": {
            "r_hat_max": R_HAT_THRESHOLD,
            "ess_min": ESS_THRESHOLD,
            "geweke_abs_z_max": GEWEKE_ABS_Z_THRESHOLD,
        },
        "converged": bool(
            np.all(rhat < R_HAT_THRESHOLD)
            and np.all(ess_value > ESS_THRESHOLD)
            and np.all(np.abs(geweke_value) < GEWEKE_ABS_Z_THRESHOLD)
        ),
    }


def _thermodynamic_integration(
    *,
    likelihood: LikelihoodFn,
    priors: dict[str, Prior],
    seed: int,
    n_walkers: int,
    n_steps: int,
    burnin: int,
    parallel: bool,
) -> dict[str, Any]:
    mean_log_like: list[float] = []
    stderr_log_like: list[float] = []
    acceptance: list[float] = []
    for index, beta in enumerate(_DEFAULT_BETA_LADDER):
        _, _, tempered_log_like, frac = _run_partitioned_ensembles(
            likelihood=likelihood,
            priors=priors,
            seed=int(seed) + 1009 * (index + 1),
            n_walkers=n_walkers,
            n_steps=max(int(n_steps) // 2, 32),
            burnin=max(int(burnin) // 2, 16),
            beta=float(beta),
            parallel=parallel,
        )
        flat = tempered_log_like.reshape(-1)
        mean_log_like.append(float(np.mean(flat)))
        stderr_log_like.append(float(np.std(flat, ddof=1) / math.sqrt(max(flat.size, 1))))
        acceptance.append(float(np.mean(frac)))
    beta_grid = np.array(_DEFAULT_BETA_LADDER, dtype=float)
    mean_arr = np.array(mean_log_like, dtype=float)
    err_arr = np.array(stderr_log_like, dtype=float)
    ln_z = float(np.trapezoid(mean_arr, beta_grid))
    delta_beta = np.diff(beta_grid)
    trap_weights = np.zeros(beta_grid.size, dtype=float)
    trap_weights[0] = 0.5 * delta_beta[0]
    trap_weights[-1] = 0.5 * delta_beta[-1]
    if beta_grid.size > 2:
        trap_weights[1:-1] = 0.5 * (delta_beta[:-1] + delta_beta[1:])
    ln_z_err = float(np.sqrt(np.sum((trap_weights * err_arr) ** 2)))
    return {
        "beta_grid": beta_grid.tolist(),
        "mean_log_likelihood": mean_arr.tolist(),
        "stderr_log_likelihood": err_arr.tolist(),
        "ln_Z": ln_z,
        "ln_Z_err": ln_z_err,
        "acceptance_fraction": acceptance,
    }


def run_posterior(
    likelihood: LikelihoodFn,
    priors: dict[str, Prior],
    *,
    seed: int,
    n_walkers: int = 64,
    n_steps: int = 5000,
    burnin: int = 1000,
    parallel: bool = False,
) -> PosteriorSample:
    """Run the deterministic FB-11 ensemble sampler.

    Two calls to `run_posterior(..., seed=42, parallel=False)` on the
    same machine return byte-identical `samples`, `log_prob`, and
    `diagnostics`. The `parallel=True` path remains explicitly
    non-deterministic.
    """
    if int(n_walkers) < 4 or int(n_walkers) % 2 != 0:
        raise ValueError("n_walkers must be an even integer >= 4")
    if int(n_steps) < 8 or int(burnin) < 0:
        raise ValueError("n_steps must be >= 8 and burnin must be >= 0")
    samples_4d, log_prob_4d, _, acceptance = _run_partitioned_ensembles(
        likelihood=likelihood,
        priors=priors,
        seed=int(seed),
        n_walkers=int(n_walkers),
        n_steps=int(n_steps),
        burnin=int(burnin),
        beta=1.0,
        parallel=bool(parallel),
    )
    diagnostics = _hybrid_convergence_report(samples_4d)
    diagnostics["acceptance_fraction"] = acceptance.reshape(-1)
    diagnostics["parallel_nondeterministic"] = bool(parallel)
    diagnostics["diagnostic_kind"] = "rhat_ess_flattened_walkers__geweke_ensemble_mean"
    diagnostics["diagnostic_chain_count"] = int(samples_4d.shape[0])
    diagnostics["diagnostic_draws"] = int(samples_4d.shape[1] * samples_4d.shape[2])
    config: dict[str, Any] = {
        "n_walkers": int(n_walkers),
        "n_steps": int(n_steps),
        "burnin": int(burnin),
        "parallel": bool(parallel),
        "parameter_names": tuple(priors),
        "n_ensembles": int(samples_4d.shape[0]),
        "walkers_per_ensemble": int(samples_4d.shape[1]),
    }
    config["thermodynamic_integration"] = _thermodynamic_integration(
        likelihood=likelihood,
        priors=priors,
        seed=int(seed),
        n_walkers=int(n_walkers),
        n_steps=int(n_steps),
        burnin=int(burnin),
        parallel=bool(parallel),
    )
    return PosteriorSample(
        samples=samples_4d.reshape(int(n_walkers), int(n_steps), samples_4d.shape[-1]),
        log_prob=log_prob_4d.reshape(int(n_walkers), int(n_steps)),
        seed=int(seed),
        sampler=_emcee_sampler_name(),
        config=config,
        diagnostics=diagnostics,
    )
