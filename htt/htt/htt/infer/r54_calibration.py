"""R54 local calibration helpers (nodes R54-L01, R54-L02).

Leave-one-out (LOO) calibration of a GLS estimator built with a simulation covariance, the
covariance identity check of a cached simulation set, and an empirical null object that refuses
to be built from too few realisations (a single split difference is never a null law).

Conventions: LOCAL_AGENT_CONTRACT.json (precision form, named laws). Every function fails closed.
"""
from __future__ import annotations

import math
from typing import Sequence

import numpy as np
from scipy import stats

from htt.htt.infer import r54_tensor_five_view as fv

#: minimum number of independent realisations for an empirical null law (MG-L03)
MIN_NULL_REALISATIONS = 30


def covariance_identity_rel(sims: np.ndarray, s_ref: np.ndarray) -> float:
    """max|cov(sims, ddof=1) - S_ref| / max|S_ref| (R54-L01 step 1).

    Invariant under a permutation of the simulation rows; a permutation of the columns changes it."""
    sims = np.asarray(sims, float)
    s_ref = np.asarray(s_ref, float)
    if sims.ndim != 2 or s_ref.shape != (sims.shape[1], sims.shape[1]):
        raise ValueError(f"shape mismatch: sims {sims.shape}, S_ref {s_ref.shape}")
    s = np.cov(sims.T, ddof=1)
    return float(np.max(np.abs(s - s_ref)) / np.max(np.abs(s_ref)))


def _gls(j: np.ndarray, s: np.ndarray, d: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """theta = F^-1 J^T S^-1 d, F = J^T S^-1 J; raises if S or F is not positive definite."""
    ls = np.linalg.cholesky(s)
    a = np.linalg.solve(ls, j)
    f = a.T @ a
    np.linalg.cholesky(f)
    t = a.T @ np.linalg.solve(ls, d)
    return np.linalg.solve(f, t), f


def sub_wald(theta: np.ndarray, cov: np.ndarray, idx: Sequence[int]) -> float:
    i = np.asarray(idx, int)
    return float(theta[i] @ np.linalg.solve(cov[np.ix_(i, i)], theta[i]))


def loo_replicates(sims: np.ndarray, j: np.ndarray, blocks: dict[str, Sequence[int]] | None = None,
                   leave_one_out: bool = True) -> dict:
    """GLS replicates of the null (theta = 0) with S_i from the other N - 1 simulations.

    sims: (N, p) realisations on the carrier rows; j: (p, k) response. Returns theta_i (N, k),
    plug-in sd_i (N, k) and Wald statistics W_i = theta_i^T F_i theta_i plus block Walds
    theta_b^T (F_i^-1)_bb^-1 theta_b for each named parameter block.

    leave_one_out=False is the defective variant (sims[i] inside its own covariance); it exists
    only so that mutation gate MG-L02 can show that the coverage test detects it."""
    sims = np.asarray(sims, float)
    j = np.asarray(j, float)
    n, p = sims.shape
    if j.shape[0] != p:
        raise ValueError(f"response rows {j.shape[0]} != carrier rows {p}")
    k = j.shape[1]
    if n - 1 <= p:
        raise ValueError("need N - 1 > p for a positive-definite sample covariance")
    blocks = blocks or {}
    theta, sd, wald = np.zeros((n, k)), np.zeros((n, k)), np.zeros(n)
    bw = {b: np.zeros(n) for b in blocks}
    full = np.cov(sims.T, ddof=1)
    for i in range(n):
        s_i = np.cov(np.delete(sims, i, axis=0).T, ddof=1) if leave_one_out else full
        th, f = _gls(j, s_i, sims[i])
        cov = np.linalg.inv(f)
        theta[i], sd[i], wald[i] = th, np.sqrt(np.diag(cov)), float(th @ f @ th)
        for b, idx in blocks.items():
            bw[b][i] = sub_wald(th, cov, idx)
    return {"theta": theta, "sd_plugin": sd, "wald": wald, "block_wald": bw, "n": n, "p": p, "k": k,
            "leave_one_out": bool(leave_one_out)}


def coverage(theta: np.ndarray, sd: np.ndarray, inflation: float, level: float) -> np.ndarray:
    """Per-parameter fraction of |theta_i| <= z_level * inflation * sd_i (true value 0)."""
    if not 0.0 < level < 1.0 or inflation <= 0.0:
        raise ValueError("level in (0,1) and positive inflation required")
    z = float(stats.norm.ppf(0.5 + level / 2.0))
    return np.mean(np.abs(theta) <= z * inflation * sd, axis=0)


def hotelling_quantile(level: float, p_dim: int, n_dof: int) -> float:
    """level-quantile of Hotelling T^2(p, n): n p/(n - p + 1) F_level(p, n - p + 1)."""
    if n_dof - p_dim + 1 <= 0:
        raise ValueError("need n > p - 1")
    return float(n_dof * p_dim / (n_dof - p_dim + 1.0) * stats.f.ppf(level, p_dim, n_dof - p_dim + 1))


def wald_coverage(rep: dict, level: float) -> float:
    """Fraction of replicates with W_i <= the Hotelling T^2(k, N - 2) level-quantile (square carrier, S_i from N - 1 realisations).

    With leave-one-out the replicate and its covariance are independent and the law is exact; with sims[i] inside its
    own covariance W_i is bounded by (N - 1)^2/N and the coverage is pushed towards 1 (gate MG-L02)."""
    if rep["p"] != rep["k"]:
        raise ValueError("the Hotelling law of W_i is exact only for a square response")
    return float(np.mean(rep["wald"] <= hotelling_quantile(level, rep["k"], rep["n"] - 2)))


def binomial_band(level: float, n: int, n_sd: float = 3.0) -> tuple[float, float]:
    """level +- n_sd * sqrt(level (1 - level) / n): the acceptance band of a coverage fraction."""
    h = n_sd * math.sqrt(level * (1.0 - level) / n)
    return level - h, level + h


def empirical_quantile_inflation(theta: np.ndarray, sd: np.ndarray, level: float) -> np.ndarray:
    """Per-parameter factor c such that the fraction of |theta_i| <= c z sd_i equals level (empirical LOO law)."""
    z = float(stats.norm.ppf(0.5 + level / 2.0))
    return np.quantile(np.abs(theta) / sd, level, axis=0) / z


class EmpiricalNull:
    """Empirical null law built from independent realisations of the same statistic.

    Refuses fewer than MIN_NULL_REALISATIONS values: one split-difference vector is one realisation
    and can only enter a difference test (R54-L02 kill criterion, MG-L03)."""

    def __init__(self, values: np.ndarray, law: str):
        v = np.asarray(values, float).reshape(-1)
        if not law.strip():
            raise ValueError("a law name is mandatory")
        if v.size < MIN_NULL_REALISATIONS:
            raise ValueError(f"an empirical null needs >= {MIN_NULL_REALISATIONS} independent realisations, got {v.size}")
        if not np.all(np.isfinite(v)):
            raise ValueError("non-finite null value")
        self.values, self.law = v, law

    def upper_tail(self, obs: float) -> dict:
        """(k + 1)/(n + 1) with a Clopper-Pearson interval (r54_tensor_five_view.empirical_upper_tail)."""
        return fv.empirical_upper_tail(obs, self.values, self.law)
