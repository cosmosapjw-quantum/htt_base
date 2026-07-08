"""EGS3 Axis E: e-value merging under dependence + anytime validity (P29).

Two facts close the finite-cover combination gap flagged by the external review:

(1) Arithmetic-mean merging is valid under ARBITRARY dependence. If each E_k is an
    e-value (E_0[E_k] <= 1 under the null), then for any convex weights w_k the
    merged statistic E = sum_k w_k E_k satisfies E_0[E] = sum_k w_k E_0[E_k] <= 1 by
    LINEARITY of expectation -- no independence, no dependence model, no copula
    assumption. Markov then gives the global bound P_0(E >= t) <= 1/t. (This is the
    standard e-merging fact: linearity does not see dependence; cf. the e-value
    merging literature -- external-context citation, Vovk & Wang.)

(2) Anytime validity via test (super)martingales. The product process
    M_t = prod_{i<=t} exp(lambda X_i - lambda^2/2) with X_i ~ N(0,1) i.i.d. under
    the null is a nonnegative martingale with M_0 = 1, so Ville's inequality gives
    P_0(sup_t M_t >= 1/beta) <= beta: the type-I error is controlled at ANY
    data-dependent stopping time, matching the staged K1/K5 data-arrival workflow
    without pre-specifying the analysis time.

Both are exercised as seeded Monte-Carlo witnesses (the dependence case uses a
COMMON factor across the E_k, i.e. maximal positive dependence).

Claim discipline. Diagnostic-only statistics machinery on synthetic nulls; no data
claim, no detection, no family/geometry/native-solver/posterior claim.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

__all__ = [
    "MergeResult", "arithmetic_merge_mc",
    "VilleResult", "test_martingale_ville_mc",
]


@dataclass(frozen=True)
class MergeResult:
    k: int
    n_sims: int
    seed: int
    dependence: str
    merged_mean: float
    se: float
    mean_le_one: bool


def arithmetic_merge_mc(*, k: int = 5, n_sims: int = 20000, seed: int = 20260708,
                        dependence: str = "common_factor",
                        lam_grid=None) -> MergeResult:
    """MC witness that the arithmetic-mean merge of k e-values stays an e-value
    under maximal dependence (all E_k driven by ONE shared null draw)."""
    if lam_grid is None:
        lam_grid = np.linspace(0.2, 1.0, int(k))
    lam = np.asarray(lam_grid, dtype=float).ravel()
    if lam.size != int(k):
        raise ValueError("lam_grid length must equal k")
    rng = np.random.default_rng(seed)
    if dependence == "common_factor":
        x = rng.normal(size=(int(n_sims), 1))          # ONE draw shared by all k
        x = np.broadcast_to(x, (int(n_sims), int(k)))
    elif dependence == "independent":
        x = rng.normal(size=(int(n_sims), int(k)))
    else:
        raise ValueError("dependence must be 'common_factor' or 'independent'")
    e_vals = np.exp(lam[None, :] * x - 0.5 * lam[None, :] ** 2)
    merged = e_vals.mean(axis=1)
    mean = float(merged.mean())
    se = float(merged.std(ddof=1) / math.sqrt(merged.size))
    return MergeResult(k=int(k), n_sims=int(n_sims), seed=int(seed),
                       dependence=str(dependence), merged_mean=mean, se=se,
                       mean_le_one=bool(mean <= 1.0 + 3.0 * se))


@dataclass(frozen=True)
class VilleResult:
    n_paths: int
    t_steps: int
    lam: float
    seed: int
    beta_grid: tuple
    crossing_rate: tuple
    ville_holds: bool


def test_martingale_ville_mc(*, n_paths: int = 4000, t_steps: int = 50,
                             lam: float = 0.3, seed: int = 20260708,
                             beta_grid=(0.5, 0.2, 0.1, 0.05)) -> VilleResult:
    """MC witness of Ville's inequality for the null product test martingale:
    P_0(sup_{t <= T} M_t >= 1/beta) <= beta at every beta in the grid (anytime
    validity; the crossing time is data-dependent, never pre-specified)."""
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(int(n_paths), int(t_steps)))
    log_m = np.cumsum(float(lam) * x - 0.5 * float(lam) ** 2, axis=1)
    running_max = np.max(log_m, axis=1)
    rates = []
    holds = True
    for beta in beta_grid:
        threshold = math.log(1.0 / float(beta))
        rate = float(np.mean(running_max >= threshold))
        rates.append(rate)
        margin = 3.0 / math.sqrt(float(n_paths))
        if rate > float(beta) + margin:
            holds = False
    return VilleResult(n_paths=int(n_paths), t_steps=int(t_steps), lam=float(lam),
                       seed=int(seed), beta_grid=tuple(float(b) for b in beta_grid),
                       crossing_rate=tuple(rates), ville_holds=bool(holds))
