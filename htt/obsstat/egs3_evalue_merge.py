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
from fractions import Fraction
import math
from numbers import Integral, Rational
from typing import Sequence

import numpy as np

__all__ = [
    "ArbitraryDependenceMergeReport", "merge_evalues_arbitrary_dependence",
    "MergeResult", "arithmetic_merge_mc",
    "VilleResult", "test_martingale_ville_mc",
]


def _exact_rational(value: object, name: str) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, Rational):
        raise ValueError(f"{name} must be an exact rational")
    if isinstance(value, Integral):
        return Fraction(int(value), 1)
    return Fraction(value)


@dataclass(frozen=True)
class ArbitraryDependenceMergeReport:
    """Exact convex arithmetic merge; no independence premise is consumed."""

    labels: tuple[str, ...]
    e_values: tuple[Fraction, ...]
    weights: tuple[Fraction, ...]
    merged_numerator: int
    merged_denominator: int
    combination_rule: str = "CONVEX_ARITHMETIC_MEAN"
    dependence_class: str = "ARBITRARY_OR_DEPENDENT"
    independence_assumed: bool = False
    common_null_required: bool = True
    prespecified_weights_required: bool = True
    validity_scope: str = "ARITHMETIC_ONLY_CONDITIONAL_ON_VALID_INPUT_EVALUES"

    @property
    def merged_e_value(self) -> Fraction:
        return Fraction(self.merged_numerator, self.merged_denominator)


def merge_evalues_arbitrary_dependence(
    *,
    labels: Sequence[str],
    e_values: Sequence[Rational],
    weights: Sequence[Rational],
) -> ArbitraryDependenceMergeReport:
    """Merge individually valid e-values by an exact convex arithmetic mean.

    Linearity of expectation makes this merge valid under arbitrary dependence.
    The function deliberately exposes neither a product rule nor a pooled sign
    count, because those require additional independence or martingale premises.
    """

    labels_i = tuple(labels)
    e_values_i = tuple(e_values)
    weights_i = tuple(weights)
    if not labels_i:
        raise ValueError("labels must not be empty")
    if not (len(labels_i) == len(e_values_i) == len(weights_i)):
        raise ValueError("labels, e_values, and weights must align")
    if any(
        not isinstance(label, str)
        or not label.strip()
        or label != label.strip()
        for label in labels_i
    ):
        raise ValueError("labels must be non-empty trimmed strings")
    if len(labels_i) != len(set(labels_i)):
        raise ValueError("labels must not contain duplicates")

    exact_e_values = tuple(
        _exact_rational(value, "e_values") for value in e_values_i
    )
    exact_weights = tuple(
        _exact_rational(value, "weights") for value in weights_i
    )
    if any(value < 0 for value in exact_e_values):
        raise ValueError("e_values must be nonnegative")
    if any(weight < 0 for weight in exact_weights):
        raise ValueError("weights must be nonnegative")
    if sum(exact_weights, start=Fraction(0, 1)) != 1:
        raise ValueError("weights must sum exactly to one")

    merged = sum(
        (weight * value for weight, value in zip(exact_weights, exact_e_values, strict=True)),
        start=Fraction(0, 1),
    )
    return ArbitraryDependenceMergeReport(
        labels=labels_i,
        e_values=exact_e_values,
        weights=exact_weights,
        merged_numerator=merged.numerator,
        merged_denominator=merged.denominator,
    )


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
