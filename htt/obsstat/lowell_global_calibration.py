"""PR08-001 mechanics: finite-mock global max-scan calibration for low-ell scans.

One row per end-to-end simulation, one column per registered statistic/analysis
choice. The complete registered scan is repeated in every simulation, each
result is converted to a tail score, a single maximum is taken, and the global
rank Monte-Carlo p-value carries the +1 correction. A parity ratio and a
monotonic transform of the same ratio count as ONE test, not two.

This module does NOT generate Planck simulations: real use requires PR4/NPIPE
E2E summaries processed with the identical map/mask/statistic pipeline
(BLOCKED_MISSING_PR4_E2E_ACCESS). Nothing here is a globally significant low-ell
anomaly claim.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class GlobalCalibrationResult:
    local_p: np.ndarray
    observed_max_score: float
    simulation_max_scores: np.ndarray
    global_p: float

    def as_dict(self) -> dict:
        return {
            "local_p": self.local_p.tolist(),
            "observed_max_score": self.observed_max_score,
            "global_p": self.global_p,
            "simulation_count": int(self.simulation_max_scores.size),
        }


def _oriented_scores(observed: np.ndarray, simulations: np.ndarray, directions: list[str]):
    obs = np.asarray(observed, dtype=float).reshape(-1)
    sims = np.asarray(simulations, dtype=float)
    if sims.ndim != 2 or sims.shape[1] != obs.size:
        raise ValueError("simulations must have shape (S,P) matching observed")
    if len(directions) != obs.size:
        raise ValueError("one direction is required per statistic")
    obs_score = np.empty_like(obs)
    sim_score = np.empty_like(sims)
    for j, direction in enumerate(directions):
        d = direction.lower()
        if d == "high":
            obs_score[j] = obs[j]; sim_score[:, j] = sims[:, j]
        elif d == "low":
            obs_score[j] = -obs[j]; sim_score[:, j] = -sims[:, j]
        elif d == "two-sided":
            center = float(np.median(sims[:, j]))
            obs_score[j] = abs(obs[j] - center); sim_score[:, j] = np.abs(sims[:, j] - center)
        else:
            raise ValueError(f"unsupported tail direction: {direction}")
    return obs_score, sim_score


def calibrate_max_scan(observed: np.ndarray, simulations: np.ndarray,
                       directions: list[str]) -> GlobalCalibrationResult:
    """Rank-calibrate local and global p-values over the full scan family.

    Dependence among statistics is preserved because each simulation carries
    the complete scan and the global null uses its maximum transformed score.
    """
    obs_score, sim_score = _oriented_scores(observed, simulations, directions)
    S, P = sim_score.shape
    local_p = np.array([(1.0 + np.sum(sim_score[:, j] >= obs_score[j])) / (S + 1.0) for j in range(P)])
    sim_local_p = np.empty_like(sim_score)
    for j in range(P):
        order = sim_score[:, j]
        sim_local_p[:, j] = np.array([(1.0 + np.sum(order >= value)) / (S + 1.0) for value in order])
    obs_T = float(np.max(-np.log(local_p)))
    sim_T = np.max(-np.log(sim_local_p), axis=1)
    global_p = float((1.0 + np.sum(sim_T >= obs_T)) / (S + 1.0))
    return GlobalCalibrationResult(local_p, obs_T, sim_T, global_p)


def synthetic_correlated_scan(seed: int = 7, simulations: int = 2000, statistics: int = 8) -> dict:
    rng = np.random.default_rng(seed)
    rho = 0.55
    cov = rho * np.ones((statistics, statistics)) + (1.0 - rho) * np.eye(statistics)
    sims = rng.multivariate_normal(np.zeros(statistics), cov, size=simulations)
    obs = rng.multivariate_normal(np.zeros(statistics), cov)
    obs[0] -= 2.3  # a locally interesting lower-tail feature
    directions = ["low"] + ["two-sided"] * (statistics - 1)
    result = calibrate_max_scan(obs, sims, directions)
    return {
        "schema": "htt.pr08_001.k1_global.synthetic.v1",
        "observed": obs.tolist(),
        "directions": directions,
        **result.as_dict(),
        "note": "synthetic demonstration only; real use requires PR4/NPIPE E2E summaries",
    }
