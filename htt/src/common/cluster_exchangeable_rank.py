"""PR-197: cluster-exchangeable / split finite-null rank (H11).

The exact finite-sample rank test fixes the score on an INDEPENDENT training
ensemble (so the observation and calibration units share a byte-identical
scoring pipeline) and calibrates on ONE predeclared representative per
independent cluster. Under exchangeability of (observation, representatives)
the rank is uniform, so the size is controlled exactly. The naive all-rows
procedure that treats correlated rows as independent is only an empirical
rank and is refused an exact label.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass

import numpy as np
from scipy.stats import beta


def fit_mahalanobis(train: np.ndarray, ridge: float = 1e-8) -> tuple[np.ndarray, np.ndarray]:
    mean = train.mean(axis=0)
    cov = np.cov(train, rowvar=False) + ridge * np.eye(train.shape[1])
    return mean, np.linalg.inv(cov)


def score(x: np.ndarray, mean: np.ndarray, precision: np.ndarray) -> np.ndarray:
    d = np.atleast_2d(x) - mean
    return np.einsum("ij,jk,ik->i", d, precision, d)


def rank_p(observed: float, calibration: np.ndarray) -> float:
    return float((1 + np.sum(calibration >= observed)) / (len(calibration) + 1))


def cp_upper(rejections: int, n: int, confidence: float = 0.99) -> float:
    if rejections >= n:
        return 1.0
    return float(beta.ppf(confidence, rejections + 1, n - rejections))


# --- exact small-N enumeration (the load-bearing exactness) ---------------

def exact_rejection_probability(n_cal: int, alpha: float, ties: int = 0) -> float:
    """Exact P(reject) for the observation-inclusive rank with n_cal exchangeable
    calibration values, at level alpha, with ``ties`` calibration values equal
    to the observation.

    Under exchangeability the observation's position among the n_cal+1 values is
    uniform; p = (1 + #{cal >= obs})/(n_cal+1). Ties (cal == obs) count toward
    ``>=``, only raising p, so they can only lower the rejection probability.
    We enumerate the uniform positions exactly.
    """
    total = n_cal + 1
    reject = 0
    # place the observation at each of the total positions among distinct
    # exchangeable draws; #{cal >= obs} = number of calibration values ranked
    # at or above the observation, plus the tie count.
    for pos in range(total):  # pos = number of calibration strictly above obs
        exceed = pos + ties
        p = (1 + exceed) / total
        if p <= alpha:
            reject += 1
    return reject / total


def max_exact_rejection(n_cal: int, alpha: float) -> float:
    """Worst-case (over tie patterns 0..n_cal) exact rejection probability."""
    return max(exact_rejection_probability(n_cal, alpha, t) for t in range(n_cal + 1))


# --- split scorer (byte-equivalent pipeline, no leakage) ------------------

@dataclass(frozen=True)
class FixedScorer:
    mean: np.ndarray
    precision: np.ndarray

    def score(self, x: np.ndarray) -> np.ndarray:
        return score(x, self.mean, self.precision)


def train_scorer(train: np.ndarray) -> FixedScorer:
    mean, precision = fit_mahalanobis(train)
    return FixedScorer(mean, precision)


# --- Monte-Carlo size (corroboration) -------------------------------------

def run_size_mc(
    *, repetitions: int, n_train: int, n_clusters: int, cluster_size: int,
    dim: int, rho: float, alpha: float, seed: int,
) -> dict:
    rng = np.random.default_rng(seed)
    reject_naive = reject_safe = 0
    for _ in range(repetitions):
        scorer = train_scorer(rng.normal(size=(n_train, dim)))
        shared = rng.normal(scale=np.sqrt(rho), size=(n_clusters, dim))
        indiv = rng.normal(scale=np.sqrt(1 - rho), size=(n_clusters, cluster_size, dim))
        rows = (shared[:, None, :] + indiv)
        all_rows = rows.reshape(n_clusters * cluster_size, dim)
        obs = rng.normal(size=(1, dim))
        obs_s = float(scorer.score(obs)[0])
        reps = rows[:, 0, :]
        reject_naive += rank_p(obs_s, scorer.score(all_rows)) <= alpha
        reject_safe += rank_p(obs_s, scorer.score(reps)) <= alpha
    return {
        "repetitions": repetitions,
        "naive_empirical_size": float(reject_naive / repetitions),
        "safe_empirical_size": float(reject_safe / repetitions),
        "safe_cp_upper_99": float(cp_upper(reject_safe, repetitions, 0.99)),
        "naive_exact_label": False,  # refused -- empirical rank only
    }


def scoring_pipeline_identical(train: np.ndarray, obs: np.ndarray, cal: np.ndarray) -> bool:
    """After fixing the training object, obs and cal go through the same scorer."""
    scorer = train_scorer(train)
    a = scorer.score(obs)
    b = scorer.score(np.vstack([obs, cal]))[:1]
    return bool(np.allclose(a, b, rtol=0, atol=0))


def cluster_variant_agreement(
    *, n_train: int, n_clusters: int, cluster_size: int, dim: int, rho: float,
    seed: int,
) -> dict:
    """Representative / permuted-representative / randomized-representative
    calibration ranks agree within MC noise (all are valid cluster units)."""
    rng = np.random.default_rng(seed)
    scorer = train_scorer(rng.normal(size=(n_train, dim)))
    shared = rng.normal(scale=np.sqrt(rho), size=(n_clusters, dim))
    indiv = rng.normal(scale=np.sqrt(1 - rho), size=(n_clusters, cluster_size, dim))
    rows = shared[:, None, :] + indiv
    obs = rng.normal(size=(1, dim))
    obs_s = float(scorer.score(obs)[0])
    p_first = rank_p(obs_s, scorer.score(rows[:, 0, :]))
    p_last = rank_p(obs_s, scorer.score(rows[:, -1, :]))
    rand_idx = rng.integers(0, cluster_size, size=n_clusters)
    p_rand = rank_p(obs_s, scorer.score(rows[np.arange(n_clusters), rand_idx, :]))
    two_se = float(2.0 / np.sqrt(n_clusters + 1))
    spread = float(max(p_first, p_last, p_rand) - min(p_first, p_last, p_rand))
    return {
        "p_first": float(p_first), "p_last": float(p_last),
        "p_random": float(p_rand),
        "max_spread": spread,
        "two_se": two_se,
        "agree_within_2se": bool(spread <= two_se),
    }
