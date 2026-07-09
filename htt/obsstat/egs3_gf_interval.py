"""EGS3 Axis E: joint-feasible-set interval propagation for the depth gap G_F (P36).

Set-valued semantics must propagate PAST x_C and F into the depth-gap ratio. When
two depth bins b and b0 share unobserved (null) components -- the SAME sky, hence
the SAME unobserved W^2 / Omega_k values enter both bins -- the interval for a
ratio-type contrast

    G_F = N(s) / D(s),   N(s) = n_pt + c_N . s,   D(s) = d_pt + c_D . s,

with the shared null vector s constrained to its MES box, is the joint sup/inf over
the SHARED feasible set. The naive quotient of the two marginal intervals lets the
numerator and the denominator pick DIFFERENT values of s, which is impossible on
one sky: the naive interval is therefore a superset (conservative). It is STRICTLY
wider only when the numerator and denominator extrema conflict on at least one
nondegenerate shared box component; aligned regimes collapse to equality.

Implementation: the shared components are evaluated on the box corners, where the
linear-fractional extrema live for a positive denominator. For each fixed s the
numerator/denominator reachable parts vary independently over their own bin
intervals, and the ratio is monotone in each, so the per-s extrema sit at the
bin-interval endpoints. P33's delta method is the POINT-IDENTIFIED limit of this
object and is domain-restricted accordingly.

Claim discipline. Diagnostic-only interval algebra on declared inputs; no data
claim, no detection, no family/geometry/native-solver/posterior claim.
"""
from __future__ import annotations

from dataclasses import dataclass
import itertools
import math

import numpy as np

__all__ = [
    "gf_naive_quotient",
    "gf_joint_interval",
    "gf_strictness_criterion",
    "gf_strictness_witness",
    "GFIntervalComparison",
    "gf_joint_vs_naive",
]


def _validate_interval(iv, name: str) -> tuple[float, float]:
    lo, hi = float(iv[0]), float(iv[1])
    if not lo <= hi:
        raise ValueError(f"{name} interval endpoints out of order")
    return lo, hi


def gf_naive_quotient(num_iv, den_iv) -> tuple[float, float]:
    """Interval-arithmetic quotient [n_lo, n_hi] / [d_lo, d_hi] with d_lo > 0.

    This is the CONSERVATIVE object: it ignores that shared components tie the
    numerator and denominator together."""
    n_lo, n_hi = _validate_interval(num_iv, "numerator")
    d_lo, d_hi = _validate_interval(den_iv, "denominator")
    if d_lo <= 0.0:
        raise ValueError("naive quotient requires a strictly positive denominator "
                         "interval (d_lo > 0); otherwise the report is no-result")
    candidates = [n_lo / d_lo, n_lo / d_hi, n_hi / d_lo, n_hi / d_hi]
    return min(candidates), max(candidates)


def gf_joint_interval(num_reach_iv, den_reach_iv, shared_bounds,
                      c_shared_num, c_shared_den, *, n_grid: int = 201
                      ) -> tuple[float, float]:
    """Joint sup/inf of (N_r + c_N . s)/(D_r + c_D . s) over the SHARED box.

    num_reach_iv / den_reach_iv: the per-bin reachable intervals [lo, hi];
    shared_bounds: sequence of (lo_j, hi_j) boxes for the shared null components
    (one common value per component across both bins); c_shared_num / c_shared_den:
    the signed coefficients with which each shared component enters each bin."""
    n_lo, n_hi = _validate_interval(num_reach_iv, "numerator-reachable")
    d_lo, d_hi = _validate_interval(den_reach_iv, "denominator-reachable")
    shared_bounds = [(float(lo), float(hi)) for lo, hi in shared_bounds]
    c_num = np.asarray(c_shared_num, dtype=float).ravel()
    c_den = np.asarray(c_shared_den, dtype=float).ravel()
    if len(shared_bounds) != c_num.size or len(shared_bounds) != c_den.size:
        raise ValueError("shared_bounds / coefficient length mismatch")
    for lo, hi in shared_bounds:
        if not (math.isfinite(lo) and math.isfinite(hi) and lo <= hi):
            raise ValueError("shared components need finite ordered bounds "
                             "(no-result otherwise)")

    if len(shared_bounds) == 0:
        return gf_naive_quotient((n_lo, n_hi), (d_lo, d_hi))

    del n_grid  # retained for backward-compatible call sites; corners are exact.
    grids = [(lo, hi) if hi > lo else (lo,) for lo, hi in shared_bounds]
    best_lo = math.inf
    best_hi = -math.inf
    for point in itertools.product(*grids):
        s = np.asarray(point, dtype=float)
        dn = float(c_num @ s)
        dd = float(c_den @ s)
        den_min = d_lo + dd
        if den_min <= 0.0:
            raise ValueError("denominator loses positivity on the shared box; "
                             "the joint report is no-result")
        # ratio monotone in each reachable part for positive denominator:
        lo_val = (n_lo + dn) / (d_hi + dd)
        hi_val = (n_hi + dn) / (d_lo + dd)
        best_lo = min(best_lo, lo_val)
        best_hi = max(best_hi, hi_val)
    return best_lo, best_hi


def gf_strictness_criterion(shared_bounds, c_shared_num, c_shared_den) -> dict:
    """Classify the naive-vs-joint strictness criterion for shared box components.

    A nondegenerate component with c_N * c_D > 0 makes the numerator optimum and
    denominator optimum require opposite endpoints for both lower and upper ratio
    bounds. If no such conflict exists, the naive quotient can be attained jointly
    and the joint interval equals the naive interval.
    """
    shared_bounds = [(float(lo), float(hi)) for lo, hi in shared_bounds]
    c_num = np.asarray(c_shared_num, dtype=float).ravel()
    c_den = np.asarray(c_shared_den, dtype=float).ravel()
    if len(shared_bounds) != c_num.size or len(shared_bounds) != c_den.size:
        raise ValueError("shared_bounds / coefficient length mismatch")
    conflict = []
    aligned = []
    for j, ((lo, hi), cn, cd) in enumerate(zip(shared_bounds, c_num, c_den)):
        if hi <= lo or cn == 0.0 or cd == 0.0:
            aligned.append(j)
            continue
        if cn * cd > 0.0:
            conflict.append(j)
        else:
            aligned.append(j)
    strict = bool(conflict)
    return {
        "strict_lower_predicted": strict,
        "strict_upper_predicted": strict,
        "conflict_components": tuple(conflict),
        "aligned_or_degenerate_components": tuple(aligned),
        "criterion": "exists nondegenerate shared component with c_N*c_D > 0",
    }


@dataclass(frozen=True)
class GFIntervalComparison:
    joint: tuple
    naive: tuple
    width_ratio: float
    joint_within_naive: bool
    n_shared_grid: int
    strict_lower: bool = False
    strict_upper: bool = False
    equality_reason: str = ""
    witness_id: str = "unspecified"
    strictness_criterion: dict | None = None


def gf_joint_vs_naive(*, num_reach_iv=(0.11, 0.17), den_reach_iv=(0.20, 0.26),
                      shared_bounds=((0.0, 0.04), (0.0, 0.02)),
                      c_shared_num=(-1.0, 1.0), c_shared_den=(-1.0, 1.0),
                      n_grid: int = 201,
                      witness_id: str = "registered_toy") -> GFIntervalComparison:
    """Compare the joint interval against the naive quotient on the registered toy
    (defaults reuse the section-10 numbers: two bins sharing the W^2 / Omega_k
    ceilings with the comparator signs). joint subseteq naive always."""
    joint = gf_joint_interval(num_reach_iv, den_reach_iv, shared_bounds,
                              c_shared_num, c_shared_den, n_grid=n_grid)
    # the naive quotient sees each bin's FULL marginal interval (reachable + nulls);
    # the marginal null span sums PER-COMPONENT extremes (each component free)
    def _span(coeffs):
        lo = sum(min(c * b_lo, c * b_hi)
                 for c, (b_lo, b_hi) in zip(coeffs, shared_bounds))
        hi = sum(max(c * b_lo, c * b_hi)
                 for c, (b_lo, b_hi) in zip(coeffs, shared_bounds))
        return lo, hi

    span_num = _span(c_shared_num)
    span_den = _span(c_shared_den)
    naive = gf_naive_quotient(
        (num_reach_iv[0] + span_num[0], num_reach_iv[1] + span_num[1]),
        (den_reach_iv[0] + span_den[0], den_reach_iv[1] + span_den[1]),
    )
    w_joint = joint[1] - joint[0]
    w_naive = naive[1] - naive[0]
    within = naive[0] <= joint[0] + 1e-12 and joint[1] <= naive[1] + 1e-12
    strict_lower = bool(joint[0] > naive[0] + 1e-12)
    strict_upper = bool(joint[1] < naive[1] - 1e-12)
    criterion = gf_strictness_criterion(shared_bounds, c_shared_num, c_shared_den)
    if strict_lower or strict_upper:
        equality_reason = "not_equal: shared extrema conflict on at least one component"
    elif len(shared_bounds) == 0:
        equality_reason = "equal: no shared components"
    elif not criterion["conflict_components"]:
        equality_reason = "equal: numerator/denominator extrema are aligned or degenerate"
    else:
        equality_reason = "equal: numeric degeneracy despite a sign-conflict predicate"
    return GFIntervalComparison(
        joint=(float(joint[0]), float(joint[1])),
        naive=(float(naive[0]), float(naive[1])),
        width_ratio=w_joint / w_naive if w_naive > 0 else 1.0,
        joint_within_naive=bool(within),
        n_shared_grid=int(n_grid),
        strict_lower=strict_lower,
        strict_upper=strict_upper,
        equality_reason=equality_reason,
        witness_id=str(witness_id),
        strictness_criterion=criterion,
    )


def gf_strictness_witness(*, n_trials: int = 371, seed: int = 20260709) -> dict:
    """Deterministic v7 witness: sign-conflict criterion agrees with intervals."""
    rng = np.random.default_rng(seed)
    agreement = 0
    strict_cases = 0
    equal_cases = 0
    for _ in range(int(n_trials)):
        n_dim = int(rng.integers(1, 5))
        width = rng.uniform(0.02, 0.45, size=n_dim)
        bounds = tuple((0.0, float(w)) for w in width)
        c_num = rng.choice((-1.0, 1.0), size=n_dim) * rng.uniform(0.02, 0.5, size=n_dim)
        # Force a mix of aligned and conflicting regimes without zero coefficients.
        signs = rng.choice((-1.0, 1.0), size=n_dim)
        c_den = signs * np.sign(c_num) * rng.uniform(0.02, 0.5, size=n_dim)
        den_shift_min = sum(min(cd * lo, cd * hi) for cd, (lo, hi) in zip(c_den, bounds))
        den_base = 1.0 + abs(float(den_shift_min))
        cmp_ = gf_joint_vs_naive(
            num_reach_iv=(1.0, 1.2),
            den_reach_iv=(den_base, den_base + 0.3),
            shared_bounds=bounds,
            c_shared_num=c_num,
            c_shared_den=c_den,
            witness_id="deterministic_sign_sweep",
        )
        predicted = bool(cmp_.strictness_criterion["conflict_components"])
        observed = bool(cmp_.strict_lower or cmp_.strict_upper)
        agreement += int(predicted == observed)
        strict_cases += int(observed)
        equal_cases += int(not observed)

    counter = gf_joint_vs_naive(
        num_reach_iv=(1.0, 1.0),
        den_reach_iv=(2.0, 2.0),
        shared_bounds=((0.0, 9.0 / 25.0), (0.0, 27.0 / 100.0), (0.0, 43.0 / 100.0)),
        c_shared_num=(-19.0 / 100.0, 39.0 / 100.0, 17.0 / 100.0),
        c_shared_den=(3.0 / 100.0, -23.0 / 100.0, -31.0 / 100.0),
        witness_id="external_counterexample_to_universal_strictness",
    )
    return {
        "trials_evaluated": int(n_trials),
        "criterion_agreement": f"{agreement}/{int(n_trials)}",
        "agreement_exact_1.0": agreement == int(n_trials),
        "strict_cases": strict_cases,
        "equal_cases": equal_cases,
        "explicit_counterexample_to_universal_strictness": {
            "joint": list(counter.joint),
            "naive": list(counter.naive),
            "strict_lower": counter.strict_lower,
            "strict_upper": counter.strict_upper,
            "equality_reason": counter.equality_reason,
        },
    }
