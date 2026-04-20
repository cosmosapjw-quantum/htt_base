"""Convergence diagnostics and frozen FB-11 thresholds."""
from __future__ import annotations

from typing import Any

import numpy as np
from scipy.stats import norm, rankdata


R_HAT_THRESHOLD = 1.01
ESS_THRESHOLD = 400.0
GEWEKE_ABS_Z_THRESHOLD = 2.0
_SMALL = 1.0e-30


def _coerce_samples(samples: np.ndarray) -> np.ndarray:
    array = np.asarray(samples, dtype=float)
    if array.ndim != 3:
        raise ValueError(
            "samples must have shape (n_chains, n_draws, n_dim); "
            f"got {array.shape}"
        )
    if array.shape[0] < 2:
        raise ValueError("at least two chains are required")
    if array.shape[1] < 8:
        raise ValueError("at least eight draws per chain are required")
    if not np.all(np.isfinite(array)):
        raise ValueError("samples must be finite")
    return array


def _split_chains(samples: np.ndarray) -> np.ndarray:
    array = _coerce_samples(samples)
    n_chains, n_draws, n_dim = array.shape
    if n_draws % 2 != 0:
        array = array[:, :-1, :]
        n_draws -= 1
    half = n_draws // 2
    return array.reshape(n_chains, 2, half, n_dim).reshape(2 * n_chains, half, n_dim)


def _rank_normalize(values: np.ndarray) -> np.ndarray:
    flat = np.asarray(values, dtype=float).reshape(-1)
    ranks = rankdata(flat, method="average")
    scaled = (ranks - 0.375) / (flat.size + 0.25)
    return norm.ppf(np.clip(scaled, 1.0e-12, 1.0 - 1.0e-12)).reshape(values.shape)


def _basic_r_hat(samples: np.ndarray) -> np.ndarray:
    n_chains, n_draws, _ = samples.shape
    chain_means = np.mean(samples, axis=1)
    grand_mean = np.mean(chain_means, axis=0)
    between = (
        float(n_draws)
        / max(float(n_chains - 1), 1.0)
        * np.sum((chain_means - grand_mean) ** 2, axis=0)
    )
    within = np.mean(np.var(samples, axis=1, ddof=1), axis=0)
    within = np.maximum(within, _SMALL)
    var_hat = ((n_draws - 1.0) / n_draws) * within + between / n_draws
    return np.sqrt(np.maximum(var_hat / within, 1.0))


def _autocorrelation(sequence: np.ndarray) -> np.ndarray:
    centered = np.asarray(sequence, dtype=float) - float(np.mean(sequence))
    n = centered.size
    if n < 2:
        return np.ones(1, dtype=float)
    variance = float(np.var(centered))
    if variance <= _SMALL:
        return np.ones(n, dtype=float)
    fft_size = 1 << int(np.ceil(np.log2(2 * n)))
    spectrum = np.fft.rfft(centered, fft_size)
    acf = np.fft.irfft(spectrum * np.conjugate(spectrum), fft_size)[:n]
    acf /= variance * np.arange(n, 0, -1, dtype=float)
    return np.clip(acf, -1.0, 1.0)


def _integrated_time_from_acf(acf: np.ndarray) -> float:
    tau = 1.0
    for lag in range(1, acf.size - 1, 2):
        pair_sum = acf[lag] + acf[lag + 1]
        if pair_sum <= 0.0:
            break
        tau += 2.0 * pair_sum
    return max(float(tau), 1.0)


def r_hat(samples: np.ndarray) -> np.ndarray:
    """Return the per-dimension split rank-normalized `R-hat` statistic."""
    split = _split_chains(samples)
    normalized = np.stack(
        [_rank_normalize(split[:, :, dim]) for dim in range(split.shape[2])],
        axis=2,
    )
    folded = np.abs(normalized - np.median(normalized, axis=(0, 1), keepdims=True))
    return np.maximum(_basic_r_hat(normalized), _basic_r_hat(folded))


def ess(samples: np.ndarray) -> np.ndarray:
    """Return the per-dimension effective sample size."""
    split = _split_chains(samples)
    normalized = np.stack(
        [_rank_normalize(split[:, :, dim]) for dim in range(split.shape[2])],
        axis=2,
    )
    n_chains, n_draws, n_dim = normalized.shape
    total = float(n_chains * n_draws)
    out = np.zeros(n_dim, dtype=float)
    for dim in range(n_dim):
        acf = np.mean(
            np.stack(
                [_autocorrelation(normalized[chain, :, dim]) for chain in range(n_chains)],
                axis=0,
            ),
            axis=0,
        )
        tau = _integrated_time_from_acf(acf)
        out[dim] = max(total / max(tau, 1.0), 1.0)
    return out


def geweke(
    samples: np.ndarray,
    *,
    first: float = 0.1,
    last: float = 0.5,
) -> np.ndarray:
    """Return the per-dimension Geweke split-window `z` diagnostic."""
    if not (0.0 < first < 1.0) or not (0.0 < last < 1.0):
        raise ValueError("first and last must lie in (0, 1)")
    if first + last >= 1.0:
        raise ValueError("first + last must be smaller than 1")
    array = _coerce_samples(samples)
    n_draws = array.shape[1]
    first_count = max(int(np.floor(first * n_draws)), 2)
    last_count = max(int(np.floor(last * n_draws)), 2)
    start = array[:, :first_count, :]
    end = array[:, n_draws - last_count :, :]
    mean_start = np.mean(start, axis=(0, 1))
    mean_end = np.mean(end, axis=(0, 1))
    var_start = np.zeros(array.shape[2], dtype=float)
    var_end = np.zeros(array.shape[2], dtype=float)
    for dim in range(array.shape[2]):
        spectral_start = []
        spectral_end = []
        for chain in range(array.shape[0]):
            start_series = start[chain, :, dim]
            end_series = end[chain, :, dim]
            acf_start = _autocorrelation(start_series)
            acf_end = _autocorrelation(end_series)
            spectral_start.append(np.var(start_series, ddof=1) * _integrated_time_from_acf(acf_start))
            spectral_end.append(np.var(end_series, ddof=1) * _integrated_time_from_acf(acf_end))
        var_start[dim] = np.mean(spectral_start) / (array.shape[0] * start.shape[1])
        var_end[dim] = np.mean(spectral_end) / (array.shape[0] * end.shape[1])
    denom = np.sqrt(np.maximum(var_start + var_end, _SMALL))
    return (mean_start - mean_end) / np.maximum(denom, _SMALL)


def trace_plot_data(samples: np.ndarray) -> dict[str, Any]:
    """Return trace-plot payloads and frozen convergence thresholds."""
    array = _coerce_samples(samples)
    rhat = r_hat(array)
    ess_value = ess(array)
    geweke_value = geweke(array)
    return {
        "mean_by_step": np.mean(array, axis=0),
        "std_by_step": np.std(array, axis=0, ddof=1),
        "chain_means": np.mean(array, axis=1),
        "r_hat": rhat,
        "ess": ess_value,
        "geweke_z": geweke_value,
        "thresholds": {
            "r_hat_max": R_HAT_THRESHOLD,
            "ess_min": ESS_THRESHOLD,
            "geweke_abs_z_max": GEWEKE_ABS_Z_THRESHOLD,
        },
    }


def convergence_report(samples: np.ndarray) -> dict[str, Any]:
    """Return the frozen FB-11 convergence decision payload."""
    payload = trace_plot_data(samples)
    rhat = np.asarray(payload["r_hat"], dtype=float)
    ess_value = np.asarray(payload["ess"], dtype=float)
    geweke_value = np.asarray(payload["geweke_z"], dtype=float)
    payload["converged"] = bool(
        np.all(rhat < R_HAT_THRESHOLD)
        and np.all(ess_value > ESS_THRESHOLD)
        and np.all(np.abs(geweke_value) < GEWEKE_ABS_Z_THRESHOLD)
    )
    return payload
