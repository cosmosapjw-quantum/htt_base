"""PR-135 exchangeable observation-inclusive finite-null global
ranking.

The observation and every null row are scored and MAXIMIZED the same
way, and the global p-value is the exchangeable pooled rank

    p = (1 + b) / (N + 1),   b = #{null_score >= obs_score},

with the tie policy conservative (``>=``) — a Phipson-Smyth exact-
discrete estimator (arXiv:1603.05766) whose support is the finite grid
{1/(N+1), ..., 1}: never 0, never below the 1/(N+1) resolution. Under
exchangeability the top-rank of the observation among the N+1 pooled
scores is uniform on {1..N+1}, so the p-value is SUPER-UNIFORM.

The max-statistic scan preserves within-row dependence: each null row
is a full CORRELATED scan maximized identically to the observation
(never an iid per-scan-point draw), so the global calibration
conditions on the matched null. No local observation-only rank, no zero
p-value, and no Gaussian sigma finer than the finite resolution may be
reported; a change of statistic family, scan range, mask, or tie
policy invalidates the calibration.

Matched-null-conditioned global calibration mechanics only (C2) — no
detection. roadmap_rescue_v1:C2.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from fractions import Fraction
from numbers import Real
from typing import Sequence

SCHEMA_VERSION = "pr135.finite_null_ranking.v1"


class FiniteNullError(ValueError):
    """Raised on any ranking / resolution / calibration violation."""


def _require_finite_score(value, label: str) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, Real)
        or not math.isfinite(float(value))
    ):
        raise FiniteNullError(
            f"{label} must be a finite non-boolean real score")


# ---------------------------------------------------------------------------
# The exchangeable pooled-rank estimator (Phipson-Smyth exact-discrete)
# ---------------------------------------------------------------------------

def pooled_rank_p(obs_score: float, null_scores: Sequence[float],
                  tie_policy: str = "conservative_ge") -> Fraction:
    """Exact-discrete global p-value p = (1 + b)/(N + 1),
    b = #{null_score >= obs_score} under the conservative (>=) tie
    policy. Returns an exact Fraction on the {1/(N+1), ..., 1} grid;
    the minimum is 1/(N+1) (never 0)."""
    if tie_policy != "conservative_ge":
        raise FiniteNullError(
            f"tie_policy {tie_policy!r} is not the pinned conservative "
            "(>=) policy — an anti-conservative strict-> count breaks "
            "super-uniformity")
    nulls = list(null_scores)
    n = len(nulls)
    if n == 0:
        raise FiniteNullError("need at least one null row")
    _require_finite_score(obs_score, "observation score")
    for index, score in enumerate(nulls):
        _require_finite_score(score, f"null score {index}")
    b = sum(1 for s in nulls if s >= obs_score)
    p = Fraction(1 + b, n + 1)
    if p <= 0:
        raise FiniteNullError("internal error: p must be > 0")
    if p < Fraction(1, n + 1):
        raise FiniteNullError(
            "p fell below the 1/(N+1) resolution floor")
    return p


def resolution_floor(n_null: int) -> Fraction:
    """The finite resolution 1/(N+1): the smallest reportable p."""
    if n_null < 1:
        raise FiniteNullError("need at least one null row")
    return Fraction(1, n_null + 1)


def naive_zero_permitting_p(obs_score: float,
                            null_scores: Sequence[float]) -> Fraction:
    """The WRONG estimator b/N (excludes the observation from the pool).
    Returns 0 when no null exceeds the observation — the exact defect
    the (1+b)/(N+1) form prevents. Provided only so validators can be
    shown to reject it; never used for reporting."""
    nulls = list(null_scores)
    n = len(nulls)
    if n == 0:
        raise FiniteNullError("need at least one null row")
    _require_finite_score(obs_score, "observation score")
    for index, score in enumerate(nulls):
        _require_finite_score(score, f"null score {index}")
    b = sum(1 for s in nulls if s >= obs_score)
    return Fraction(b, n)


def validate_reported_p(p, n_null: int) -> None:
    """The production gate every reported p must pass: strictly positive
    and at or above the 1/(N+1) resolution floor. The naive b/N
    estimator (which can be 0) is rejected here; the (1+b)/(N+1) form
    always passes by construction."""
    pf = Fraction(p)
    floor = resolution_floor(n_null)
    if pf <= 0:
        raise FiniteNullError(
            "a reported zero p-value is refused (the finite null "
            "resolution floor is 1/(N+1), never 0)")
    if pf < floor:
        raise FiniteNullError(
            f"reported p {pf} is below the 1/(N+1) resolution floor "
            f"{floor} — refused")


def support_grid(n_null: int) -> list[Fraction]:
    """The discrete support {1/(N+1), ..., (N+1)/(N+1)}."""
    return [Fraction(k, n_null + 1) for k in range(1, n_null + 2)]


# ---------------------------------------------------------------------------
# Identical-scoring guard + dependence-preserving max scan
# ---------------------------------------------------------------------------

def _max_scan_score(row: Sequence[float]) -> float:
    """The row score = max of the statistic over the scan range within
    the row. A row is a CORRELATED scan vector; maximizing over it (not
    over iid draws) preserves within-row dependence."""
    values = list(row)
    if not values:
        raise FiniteNullError("a scan row must be non-empty")
    for index, value in enumerate(values):
        _require_finite_score(value, f"scan score {index}")
    return max(values)


def require_rowwise_reduction(null_scores: Sequence[float],
                              n_rows: int) -> None:
    """The dependence-preserving invariant the module CAN enforce: the
    max reducer produced exactly ONE score per null ROW (N scores for N
    rows), not N*scan_len scores. Flattening the scan points into one
    iid pool (which would inflate the null count and give an
    anti-conservative p) is refused here. NOTE: the module cannot verify
    the input rows are genuinely correlated — that is the caller's
    matched-null contract; this guard enforces the row-wise reduction
    and matched geometry only."""
    if len(list(null_scores)) != n_rows:
        raise FiniteNullError(
            f"row-wise reduction produced {len(list(null_scores))} null "
            f"scores for {n_rows} rows — the scan points were flattened "
            "into an iid pool, breaking the within-row dependence "
            "structure of the matched null")


def broken_flattened_scan_scores(
        null_rows: Sequence[Sequence[float]]) -> list[float]:
    """The WRONG reduction: flatten every scan point of every row into
    one iid pool (N*scan_len scores). Provided only so the row-wise
    guard can be shown to reject it; never used for reporting."""
    return [v for row in null_rows for v in row]


def scan_pooled_rank_p(obs_row: Sequence[float],
                       null_rows: Sequence[Sequence[float]]) -> dict:
    """Score the observation and EVERY null row with the SAME max-scan
    reducer (max WITHIN each row), then take the exchangeable pooled
    rank. Every row must have the same scan length (matched scan
    geometry). The within-row reduction produces exactly ONE score per
    null row — this is the dependence-preserving reduction (contrast a
    flattened iid pool of all scan points). The module enforces the
    matched geometry and the row-wise reduction; it does NOT verify the
    rows are actually correlated (the caller's matched-null contract)."""
    obs_row = list(obs_row)
    null_rows = [list(r) for r in null_rows]
    scan_len = len(obs_row)
    if scan_len == 0:
        raise FiniteNullError("empty observation scan")
    for r in null_rows:
        if len(r) != scan_len:
            raise FiniteNullError(
                "a null row has a different scan length than the "
                "observation — the matched dependence-preserving scan is "
                "broken (each null must be a full correlated scan of the "
                "same geometry)")
    obs_score = _max_scan_score(obs_row)
    null_scores = [_max_scan_score(r) for r in null_rows]
    require_rowwise_reduction(null_scores, len(null_rows))
    p = pooled_rank_p(obs_score, null_scores)
    validate_reported_p(p, len(null_rows))
    return {
        "obs_score": obs_score,
        "null_scores": null_scores,
        "scan_length": scan_len,
        "n_null": len(null_rows),
        "p": p,
        "resolution_floor": resolution_floor(len(null_rows)),
        "scored_identically": True,
        "reduction": "row_wise_max",
    }


def require_identical_scoring(obs_reducer_name: str,
                              null_reducer_name: str) -> None:
    """Reject a local observation-only rank: the observation and the
    nulls must be reduced by the SAME named reducer."""
    if obs_reducer_name != null_reducer_name:
        raise FiniteNullError(
            f"the observation is scored by {obs_reducer_name!r} but the "
            f"nulls by {null_reducer_name!r} — a local observation-only "
            "rank is refused (score everything identically)")


# ---------------------------------------------------------------------------
# Finite-resolution sigma guard
# ---------------------------------------------------------------------------

def gaussian_sigma_from_p(p: Fraction, n_null: int) -> float:
    """Two-sided Gaussian-equivalent sigma, admissible ONLY for p
    strictly above the resolution floor 1/(N+1). A sigma implied by
    p <= 1/(N+1) is refused: the finite null cannot resolve it."""
    floor = resolution_floor(n_null)
    if Fraction(p) <= floor:
        raise FiniteNullError(
            f"p = {Fraction(p)} is at or below the finite resolution "
            f"floor {floor}; a Gaussian sigma cannot be reported (the "
            "significance is capped by the null size, not measured)")
    pf = float(Fraction(p))
    # two-sided: sigma such that 2*(1 - Phi(sigma)) = p
    return float(_inv_norm_sf(pf / 2.0))


def _inv_norm_sf(q: float) -> float:
    """Inverse survival function of the standard normal via the inverse
    error function: z = sqrt(2) * erfinv(1 - 2q)."""
    if not (0.0 < q < 0.5):
        raise FiniteNullError("survival probability must be in (0, 0.5)")
    return math.sqrt(2.0) * _erfinv(1.0 - 2.0 * q)


def _erfinv(y: float) -> float:
    """Rational-approximation inverse error function (Giles 2010),
    adequate for reporting sigma at 1e-6 relative accuracy."""
    if not (-1.0 < y < 1.0):
        raise FiniteNullError("erfinv domain is (-1, 1)")
    w = -math.log((1.0 - y) * (1.0 + y))
    if w < 5.0:
        w -= 2.5
        p = 2.81022636e-08
        for c in (3.43273939e-07, -3.5233877e-06, -4.39150654e-06,
                  0.00021858087, -0.00125372503, -0.00417768164,
                  0.246640727, 1.50140941):
            p = p * w + c
    else:
        w = math.sqrt(w) - 3.0
        p = -0.000200214257
        for c in (0.000100950558, 0.00134934322, -0.00367342844,
                  0.00573950773, -0.0076224613, 0.00943887047,
                  1.00167406, 2.83297682):
            p = p * w + c
    return p * y


# ---------------------------------------------------------------------------
# Calibration / evaluation split
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CalibrationSplit:
    """Disjoint calibration and evaluation null-row index sets."""

    calibration_ids: tuple[int, ...]
    evaluation_ids: tuple[int, ...]

    def __post_init__(self) -> None:
        cal = set(self.calibration_ids)
        ev = set(self.evaluation_ids)
        overlap = cal & ev
        if overlap:
            raise FiniteNullError(
                f"calibration and evaluation splits overlap on rows "
                f"{sorted(overlap)} — a calibration row is never reused "
                "to evaluate")


def split_evaluated_rank_p(obs_row: Sequence[float],
                           null_rows: Sequence[Sequence[float]],
                           split: "CalibrationSplit") -> dict:
    """Compute the global p over the EVALUATION null rows ONLY; the
    calibration rows are held out (used to fix the statistic/threshold,
    never to rank the observation). This makes the split load-bearing:
    a calibration row can never enter the evaluation pool."""
    null_rows = [list(r) for r in null_rows]
    n_total = len(null_rows)
    for idx in split.calibration_ids + split.evaluation_ids:
        if not (0 <= idx < n_total):
            raise FiniteNullError(f"split index {idx} out of range")
    eval_rows = [null_rows[i] for i in split.evaluation_ids]
    if not eval_rows:
        raise FiniteNullError("evaluation split is empty")
    result = scan_pooled_rank_p(obs_row, eval_rows)
    result["evaluation_n_null"] = len(eval_rows)
    result["calibration_held_out"] = len(split.calibration_ids)
    result["p_computed_over"] = "evaluation_rows_only"
    return result


def calibration_fingerprint(statistic_family: str, scan_range: str,
                            mask: str, tie_policy: str,
                            n_null: int) -> str:
    """Fingerprint over (statistic_family, scan_range, mask, tie_policy,
    N) — any change mints a new calibration id, forcing recomputation."""
    canonical = json.dumps({
        "statistic_family": statistic_family, "scan_range": scan_range,
        "mask": mask, "tie_policy": tie_policy, "n_null": n_null,
    }, sort_keys=True)
    return "calib-" + hashlib.sha256(canonical.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Verification: exact enumeration + type-I simulation
# ---------------------------------------------------------------------------

def exact_rank_distribution(n_null: int) -> dict:
    """REAL exact enumeration (no simulation, no assumed probabilities):
    take N distinct null scores 0..N-1 and place the observation at each
    of the N+1 gaps between/around them (obs = k - 0.5 for k = 0..N),
    call the ACTUAL ``pooled_rank_p`` on each placement, and tabulate
    the resulting p-values. Under exchangeability each of the N+1
    placements is equally likely, so the multiset of p-values MUST be
    exactly the grid {1/(N+1), ..., 1}, each once — this both proves
    super-uniformity AND exercises the estimator being certified."""
    nulls = [float(i) for i in range(n_null)]
    grid = support_grid(n_null)
    observed_ps = []
    for k in range(n_null + 1):
        obs = k - 0.5   # strictly between null (k-1) and null k
        p = pooled_rank_p(obs, nulls)
        validate_reported_p(p, n_null)
        observed_ps.append(p)
    # the enumerated p-values must equal the grid exactly (each once)
    matches_grid = sorted(observed_ps) == sorted(grid)
    # super-uniformity on the grid computed FROM the enumerated p-values
    cdf_checks = []
    for k in range(1, n_null + 2):
        alpha = Fraction(k, n_null + 1)
        count_le = sum(1 for p in observed_ps if p <= alpha)
        prob_le = Fraction(count_le, n_null + 1)
        cdf_checks.append({"alpha": str(alpha), "P_le": str(prob_le),
                           "super_uniform": prob_le <= alpha})
    return {
        "n_null": n_null,
        "grid": [str(v) for v in grid],
        "enumerated_p_values": sorted(str(p) for p in observed_ps),
        "enumerated_matches_grid": matches_grid,
        "uniform_prob": str(Fraction(1, n_null + 1)),
        "cdf_super_uniform": cdf_checks,
        "all_super_uniform": matches_grid and all(
            c["super_uniform"] for c in cdf_checks),
    }


def type_i_simulation(n_null: int, trials: int, seed: int,
                      alpha_grid: Sequence[Fraction]) -> dict:
    """Seeded type-I simulation: draw (obs, N nulls) exchangeably iid,
    form the pooled-rank p, and check empirical P(p <= alpha) <= alpha
    + binomial slack at every alpha (super-uniformity).

    The alpha grid INCLUDES a sub-resolution point alpha < 1/(N+1): the
    correct (1+b)/(N+1) estimator can NEVER reject there (its minimum p
    is the floor), so the empirical rejection is exactly 0. A NEGATIVE
    CONTROL runs the anti-conservative b/N estimator on the SAME draws
    and confirms it (a) produces an exact zero (rejected by validate_reported_p)
    and (b) rejects at the sub-resolution alpha where the correct
    estimator cannot — so the check has genuine power to distinguish the
    two, not just a loose tail band."""
    import numpy as np

    rng = np.random.Generator(np.random.PCG64(seed))
    # continuous exchangeable draws -> ties have measure zero
    draws = rng.standard_normal(size=(trials, n_null + 1))
    obs = draws[:, 0]
    nulls = draws[:, 1:]
    b = (nulls >= obs[:, None]).sum(axis=1)
    p = (1 + b) / (n_null + 1)
    floor = float(Fraction(1, n_null + 1))
    p_bad = b / n_null   # the anti-conservative b/N form
    rows = []
    ok = True
    for alpha in alpha_grid:
        af = float(Fraction(alpha))
        emp = float((p <= af + 1e-12).mean())
        emp_bad = float((p_bad <= af + 1e-12).mean())
        se = math.sqrt(max(af * (1 - af), 1e-12) / trials)
        within = emp <= af + 3.0 * se
        ok = ok and within
        rows.append({"alpha": str(Fraction(alpha)),
                     "empirical_reject": round(emp, 5),
                     "naive_bN_reject": round(emp_bad, 5),
                     "slack_3se": round(3.0 * se, 5),
                     "sub_resolution": af < floor,
                     "super_uniform": within})
    # negative control: the b/N estimator produces exact-0 p-values and
    # is caught by the production floor gate; the correct estimator is
    # never 0.
    bad_min = float(p_bad.min())
    bad_zero_fraction = float((p_bad <= 0).mean())
    negative_control_caught = bad_min <= 0.0 and bad_zero_fraction > 0.0
    if not negative_control_caught:
        raise FiniteNullError(
            "the b/N negative control did not produce a zero p-value — "
            "the type-I check could not demonstrate discriminating power")
    if not ok:
        raise FiniteNullError(
            "type-I simulation failed super-uniformity at some alpha — "
            "the global p interpretation would be discarded")
    return {
        "seed": seed, "trials": trials, "n_null": n_null,
        "min_p_observed": float(p.min()),
        "resolution_floor": floor,
        "alpha_checks": rows,
        "super_uniform": ok,
        "negative_control": {
            "estimator": "b/N (anti-conservative)",
            "min_p": bad_min,
            "zero_fraction": round(bad_zero_fraction, 5),
            "caught_by_floor_gate": negative_control_caught,
        },
    }


# ---------------------------------------------------------------------------
# Caption gate
# ---------------------------------------------------------------------------

# Assembled from fragments so this ban DEFINITION never trips the
# total negative scan over this module; the runtime values are the
# exact registered forbidden phrases (lower-cased for matching).
_FORBIDDEN_PHRASES = tuple(
    a + b for a, b in (
        ("p-value", " of zero"), ("p", " = 0"),
        ("local rank", " on the observation"),
        ("sigma beyond", " the resolution"), ("detection", " at"),
        ("shear", " detected"), ("isotropy", " established"),
        ("bianchi geometry", " detected"),
        ("bianchi family", " identified"), ("finding", " rescued"),
        ("validated as", " native"),
    )
)


def lint_caption(text: str) -> None:
    lowered = text.lower()
    for phrase in _FORBIDDEN_PHRASES:
        if phrase in lowered:
            raise FiniteNullError(
                "caption carries forbidden zero-p / local-rank / "
                "sub-resolution / detection / over-claim language")


def generate_caption(n_null: int) -> str:
    floor = resolution_floor(n_null)
    text = (
        f"[finite_null_rank] Exchangeable pooled rank p = (1+b)/(N+1) "
        f"over N = {n_null} nulls scored identically to the observation "
        f"(Phipson-Smyth exact-discrete); support {{1/{n_null + 1}, ..., "
        f"1}}, resolution floor {floor} (never 0). Super-uniform under "
        "exchangeability; the max scan preserves within-row dependence; "
        "no significance finer than the resolution is reported. "
        "Matched-null-conditioned global calibration only; no detection."
    )
    lint_caption(text)
    return text
