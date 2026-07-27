"""PR-225: estimated-covariance partial identification + anytime evidence.

A calibrated inference layer over finite covariance (Hartlap correction),
partial identification, and staged data via sequential e-values (Ville's
inequality). Extends PR-200 (partial-ID coverage) and PR-197 (cluster rank) and
adds the anytime/e-value axis: a merged e-value has mean <= 1, its tail obeys
Markov's 1/t bound, and a running product crosses 20 at most 5% of the time.
"""
from __future__ import annotations
import numpy as np


def hartlap_stress(seed=20260721, nrep=3000, m=12, nsim=90) -> dict:
    for name, value, minimum in (
        ("seed", seed, 0),
        ("nrep", nrep, 1),
        ("m", m, 1),
        ("nsim", nsim, 2),
    ):
        if isinstance(value, (bool, np.bool_)) or not isinstance(
            value, (int, np.integer)
        ) or int(value) < minimum:
            raise ValueError(f"{name} must be an integer >= {minimum}")
    if nsim <= m + 2:
        raise ValueError("Hartlap diagnostic requires nsim > m + 2")
    rng = np.random.default_rng(seed)
    alpha = (nsim - m - 2) / (nsim - 1)   # Hartlap factor
    raw, cor = [], []
    for _ in range(nrep):
        sims = rng.normal(size=(nsim, m))
        S = np.cov(sims, rowvar=False)
        P = np.linalg.inv(S)
        y = rng.normal(size=m)
        raw.append(y @ P @ y)
        cor.append(alpha * y @ P @ y)
    raw, cor = np.asarray(raw), np.asarray(cor)
    return {"m": m, "Nsim": nsim, "hartlap_factor": float(alpha),
            "inference_role": "DIAGNOSTIC_COMPARATOR_ONLY",
            "raw_mean_over_m": float(raw.mean() / m),
            "corrected_mean_over_m": float(cor.mean() / m),
            "raw_inflated": bool(raw.mean() / m > 1.08),
            "corrected_calibrated": bool(abs(cor.mean() / m - 1) < 0.04)}


def evalue_anytime(seed=20260721, n=50000, K=6, T=80, lam=0.25) -> dict:
    rng = np.random.default_rng(seed)
    z = rng.normal(size=(n, 1))
    idio = rng.normal(size=(n, K))
    x = 0.9 * z + np.sqrt(1 - 0.9 ** 2) * idio
    E = np.exp(lam * x - 0.5 * lam ** 2)
    merged = E.mean(axis=1)
    tails = {str(t): float(np.mean(merged >= t)) for t in [2, 5, 10]}
    inc = np.exp(lam * rng.normal(size=(n, T)) - 0.5 * lam ** 2)
    M = np.cumprod(inc, axis=1)
    cross = float(np.mean(M.max(axis=1) >= 20))
    return {"merged_mean": float(merged.mean()),
            "tail_probs": tails, "markov_bounds": {str(t): 1 / t for t in [2, 5, 10]},
            "ville_crossing_at_20": cross, "ville_bound": 0.05,
            "merged_mean_le_one": bool(abs(merged.mean() - 1) < 0.015),
            "tails_within_markov": bool(all(tails[str(t)] <= 1 / t + 0.005 for t in [2, 5, 10])),
            "ville_holds": bool(cross <= 0.055)}
