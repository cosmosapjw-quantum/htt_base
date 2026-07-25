"""PR-137 weak-identification boundary + grid-conditional simultaneous
coverage.

A pre-registered DGP grid crosses the point-identified, partially-
identified, and unidentified regimes continuously via the identified-set
half-width ``w`` (w = 0 point; 0 < w < inf partial; w -> inf
unidentified). The COMPLETE frozen algorithm — the Imbens-Manski
partial-identification confidence interval

    CI(w) = [L_hat - c(w) s,  U_hat + c(w) s],
    c(w) solves  Phi(c + w/s) - Phi(-c) = 0.95

over ``L_hat ~ N(theta0 - w/2, s^2)``, ``U_hat ~ N(theta0 + w/2, s^2)``
(theta0 = 0, s = 1) — is measured for simultaneous empirical coverage
at every grid point. The family-wise 99% Clopper-Pearson LOWER bound is
reported; a grid point is retained iff its lower bound >= 0.93, and a
below-threshold point is preserved in the FAILURE MAP (never removed).
Coverage change and optimizer endpoint error are reported at two mesh
refinements. The result is GRID-CONDITIONAL simultaneous empirical
coverage; the word "uniform" (class-wide) is refused without a
registered continuity/mesh certificate.

Grid-conditional coverage-calibrated partial-identification mechanics
only (C2) — no detection. roadmap_rescue_v1:C2.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from numbers import Integral, Real
from typing import Sequence

SCHEMA_VERSION = "pr137.weak_id_coverage.v1"

# Registered continuity/mesh-error certificate registry. EMPTY: the word
# "uniform" (class-wide coverage) is refused while this is empty.
CONTINUITY_MESH_CERTIFICATES: dict[str, dict] = {}


class WeakIdError(ValueError):
    """Raised on any coverage / grid / language violation."""


# ---------------------------------------------------------------------------
# Normal CDF / inverse and the Imbens-Manski critical value
# ---------------------------------------------------------------------------

def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def imbens_manski_c(w: float, s: float = 1.0, level: float = 0.95,
                    tol: float = 1e-12) -> dict:
    """Solve Phi(c + w/s) - Phi(-c) = level for c by bisection. Returns
    c and the OPTIMIZER ENDPOINT ERROR (the residual at the returned c),
    which the mesh report checks against the tolerance fraction."""
    if (
        isinstance(w, bool)
        or not isinstance(w, Real)
        or not math.isfinite(float(w))
        or w < 0
    ):
        raise WeakIdError("w must be a finite non-negative real value")
    if (
        isinstance(s, bool)
        or not isinstance(s, Real)
        or not math.isfinite(float(s))
        or s <= 0
    ):
        raise WeakIdError("s must be a finite positive real value")
    if (
        isinstance(level, bool)
        or not isinstance(level, Real)
        or not math.isfinite(float(level))
        or not 0 < level < 1
    ):
        raise WeakIdError("level must be a finite real value in (0, 1)")
    if (
        isinstance(tol, bool)
        or not isinstance(tol, Real)
        or not math.isfinite(float(tol))
        or tol <= 0
    ):
        raise WeakIdError("tol must be a finite positive real value")
    w = float(w)
    s = float(s)
    level = float(level)
    tol = float(tol)

    def f(c):
        return _norm_cdf(c + w / s) - _norm_cdf(-c) - level

    lo, hi = 0.0, 40.0
    if f(lo) > 0:
        # even c=0 over-covers (only at w huge); c=0 is the solution edge
        return {"c": 0.0, "endpoint_error": abs(f(0.0))}
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if f(mid) < 0:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    c = 0.5 * (lo + hi)
    return {"c": c, "endpoint_error": abs(f(c))}


# ---------------------------------------------------------------------------
# Clopper-Pearson lower bound (family-wise binomial)
# ---------------------------------------------------------------------------

def _validated_binomial_inputs(
    k: int, n: int, conf: float
) -> tuple[int, int, float]:
    if (
        isinstance(k, bool)
        or not isinstance(k, Integral)
        or isinstance(n, bool)
        or not isinstance(n, Integral)
        or n <= 0
        or not 0 <= k <= n
    ):
        raise WeakIdError("invalid integer (k, n) for Clopper-Pearson")
    if (
        isinstance(conf, bool)
        or not isinstance(conf, Real)
        or not math.isfinite(float(conf))
        or not 0.0 < float(conf) < 1.0
    ):
        raise WeakIdError(
            "Clopper-Pearson confidence must be finite and in (0, 1)")
    return int(k), int(n), float(conf)


def clopper_pearson_lower(k: int, n: int, conf: float = 0.99) -> float:
    """Exact one-sided Clopper-Pearson LOWER confidence bound on a
    binomial proportion: the p such that P(Bin(n, p) >= k) = 1 - conf,
    via the Beta quantile lower = BetaInv(1-conf; k, n-k+1). Returns 0
    for k = 0. Conservative (never anti-conservative)."""
    k, n, conf = _validated_binomial_inputs(k, n, conf)
    if k == 0:
        return 0.0
    alpha = 1.0 - conf
    return _beta_ppf(alpha, k, n - k + 1)


def clopper_pearson_upper(k: int, n: int, conf: float = 0.99) -> float:
    """Exact one-sided Clopper-Pearson UPPER bound — provided ONLY so the
    lower-bound guard can be shown to reject it (an upper bound is
    anti-conservative when reported as the coverage guarantee)."""
    k, n, conf = _validated_binomial_inputs(k, n, conf)
    if k == n:
        return 1.0
    return _beta_ppf(conf, k + 1, n - k)


def bonferroni_conf(family_conf: float, n_points: int) -> float:
    """Per-point confidence so the JOINT (family-wise, simultaneous over
    all grid points) confidence is at least ``family_conf`` by the
    Bonferroni bound: 1 - (1 - family_conf)/n_points."""
    if (
        isinstance(n_points, bool)
        or not isinstance(n_points, Integral)
        or n_points < 1
    ):
        raise WeakIdError("n_points must be a positive integer")
    if (
        isinstance(family_conf, bool)
        or not isinstance(family_conf, Real)
        or not math.isfinite(float(family_conf))
        or not 0.0 < float(family_conf) < 1.0
    ):
        raise WeakIdError(
            "family confidence must be finite and in (0, 1)")
    return 1.0 - (1.0 - float(family_conf)) / int(n_points)


def validate_lower_bound(claimed: float, k: int, n: int,
                         conf: float) -> None:
    """The production guard: a reported family-wise LOWER bound must (a)
    not exceed the point estimate k/n and (b) equal the Clopper-Pearson
    lower bound at ``conf``. An upper bound (or a point estimate)
    masquerading as the guarantee is rejected."""
    k, n, conf = _validated_binomial_inputs(k, n, conf)
    if (
        isinstance(claimed, bool)
        or not isinstance(claimed, Real)
        or not math.isfinite(float(claimed))
        or not 0.0 <= float(claimed) <= 1.0
    ):
        raise WeakIdError(
            "claimed lower bound must be finite and in [0, 1]")
    claimed = float(claimed)
    point = k / n
    if claimed > point + 1e-12:
        raise WeakIdError(
            f"claimed lower bound {claimed} exceeds the point coverage "
            f"{point}; that is an upper bound, not the conservative "
            "Clopper-Pearson lower bound")
    true_lower = clopper_pearson_lower(k, n, conf)
    if abs(claimed - true_lower) > 1e-9:
        raise WeakIdError(
            f"claimed lower bound {claimed} != the Clopper-Pearson lower "
            f"bound {true_lower} at conf {conf}")


def _beta_ppf(p: float, a: float, b: float) -> float:
    """Inverse regularized incomplete Beta by bisection on the
    regularized incomplete beta (continued-fraction). Adequate to ~1e-10
    for the coverage bounds here."""
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if _betainc_reg(mid, a, b) < p:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-14:
            break
    return 0.5 * (lo + hi)


def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the incomplete beta (Lentz, Numerical
    Recipes). Does NOT re-enter _betainc_reg."""
    tiny = 1e-30
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-14:
            break
    return h


def _betainc_reg(x: float, a: float, b: float) -> float:
    """Regularized incomplete beta I_x(a, b); the symmetry transform is
    applied ONCE (no recursion into this function)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    bt = math.exp(a * math.log(x) + b * math.log(1.0 - x) - lbeta)
    if x < (a + 1.0) / (a + b + 2.0):
        val = bt * _betacf(a, b, x) / a
    else:
        val = 1.0 - bt * _betacf(b, a, 1.0 - x) / b
    return min(max(val, 0.0), 1.0)


# ---------------------------------------------------------------------------
# Coverage simulation
# ---------------------------------------------------------------------------

def _seed_stream(base_seed: int, w_key: str, procedure: str, seed_idx: int):
    """Deterministic per-(grid point, procedure, seed) PCG64 stream —
    the whole MC is reproducible byte-for-byte (hashlib, NOT the
    run-randomized builtin hash)."""
    import hashlib

    import numpy as np

    key = f"{base_seed}|{w_key}|{procedure}|{seed_idx}".encode()
    mix = int.from_bytes(hashlib.sha256(key).digest()[:8], "big") % (2 ** 63)
    return np.random.Generator(np.random.PCG64(mix))


def coverage_at_point(w: float, procedure: str, *, n_replicates: int,
                      seeds: int, base_seed: int, w_key: str,
                      s: float = 1.0,
                      theta0_position: str = "midpoint") -> dict:
    """Pooled empirical coverage of the true parameter theta0 for one
    grid point over ``seeds`` independent PCG64 streams. The identified
    set is [-w/2, +w/2] around the center; ``theta0_position`` places
    the true parameter at the set MIDPOINT (theta0 = 0, coverage-easiest)
    or at the least-favorable BOUNDARY (theta0 = +w/2). procedure =
    'imbens_manski' (the frozen algorithm) or 'naive_no_expansion' (the
    adversarial c = 0 procedure). The DELIVERED replicate count is
    returned so a caller can validate it (not merely the requested n)."""
    import numpy as np

    if (
        isinstance(w, bool)
        or not isinstance(w, Real)
        or not math.isfinite(float(w))
        or w < 0
    ):
        raise WeakIdError("w must be a finite non-negative real value")
    if (
        isinstance(s, bool)
        or not isinstance(s, Real)
        or not math.isfinite(float(s))
        or s <= 0
    ):
        raise WeakIdError("s must be a finite positive real value")
    if procedure not in ("imbens_manski", "naive_no_expansion"):
        raise WeakIdError(
            "procedure must be imbens_manski or naive_no_expansion")
    for name, value in (
        ("n_replicates", n_replicates),
        ("seeds", seeds),
        ("base_seed", base_seed),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, Integral)
            or value <= 0
        ):
            raise WeakIdError(f"{name} must be a positive integer")
    if n_replicates < seeds:
        raise WeakIdError(
            "n_replicates must be at least the number of seeds")
    if not isinstance(w_key, str) or not w_key:
        raise WeakIdError("w_key must be a non-empty string")
    w = float(w)
    s = float(s)
    n_replicates = int(n_replicates)
    seeds = int(seeds)
    base_seed = int(base_seed)
    if theta0_position not in ("midpoint", "boundary"):
        raise WeakIdError("theta0_position must be midpoint or boundary")
    theta0 = 0.0 if theta0_position == "midpoint" else w / 2.0
    per_seed = max(1, n_replicates // seeds)
    imc = imbens_manski_c(w, s)
    c = imc["c"] if procedure == "imbens_manski" else 0.0
    covered_total = 0
    n_total = 0
    per_seed_cov = []
    for seed_idx in range(seeds):
        rng = _seed_stream(base_seed, w_key + "|" + theta0_position,
                           procedure, seed_idx)
        L = rng.normal(-w / 2.0, s, per_seed)
        U = rng.normal(w / 2.0, s, per_seed)
        lo = L - c * s
        hi = U + c * s
        cov = (lo <= theta0) & (theta0 <= hi)
        k = int(cov.sum())
        covered_total += k
        n_total += per_seed
        per_seed_cov.append(k / per_seed)
    return {
        "w": w_key,
        "procedure": procedure,
        "theta0_position": theta0_position,
        "c": c,
        "endpoint_error": imc["endpoint_error"],
        "requested_replicates": n_replicates,
        "delivered_replicates": n_total,
        "seeds": seeds,
        "covered": covered_total,
        "coverage": covered_total / n_total,
        "marginal_lower_99": clopper_pearson_lower(covered_total,
                                                   n_total, 0.99),
        "per_seed_coverage": per_seed_cov,
    }


# ---------------------------------------------------------------------------
# Grid guards + failure map
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Preregistration:
    nominal_coverage: float
    retain_lower_bound: float
    min_replicates: int
    min_seeds: int
    base_seed: int
    endpoint_tol_fraction: float
    frozen_id: str = "prereg_v1"

    def __post_init__(self) -> None:
        for name, value in (
            ("nominal_coverage", self.nominal_coverage),
            ("retain_lower_bound", self.retain_lower_bound),
        ):
            if (
                isinstance(value, bool)
                or not isinstance(value, Real)
                or not math.isfinite(float(value))
                or not 0 <= value <= 1
            ):
                raise WeakIdError(
                    f"{name} must be a finite probability in [0, 1]")
        if self.nominal_coverage in (0, 1):
            raise WeakIdError(
                "nominal_coverage must be strictly inside (0, 1)")
        for name, value in (
            ("min_replicates", self.min_replicates),
            ("min_seeds", self.min_seeds),
            ("base_seed", self.base_seed),
        ):
            if (
                isinstance(value, bool)
                or not isinstance(value, Integral)
                or value <= 0
            ):
                raise WeakIdError(f"{name} must be a positive integer")
        if self.min_replicates < self.min_seeds:
            raise WeakIdError(
                "min_replicates must be at least min_seeds")
        if (
            isinstance(self.endpoint_tol_fraction, bool)
            or not isinstance(self.endpoint_tol_fraction, Real)
            or not math.isfinite(float(self.endpoint_tol_fraction))
            or not 0 < self.endpoint_tol_fraction <= 1
        ):
            raise WeakIdError(
                "endpoint_tol_fraction must be in the finite interval "
                "(0, 1]")
        if not isinstance(self.frozen_id, str) or not self.frozen_id:
            raise WeakIdError("frozen_id must be a non-empty string")

    def require_replicates(self, delivered_replicates: int,
                           seeds: int) -> None:
        """Validate the DELIVERED replicate count (not merely the
        requested n): integer per-seed division can short the total."""
        for name, value in (
            ("delivered_replicates", delivered_replicates),
            ("seeds", seeds),
        ):
            if (
                isinstance(value, bool)
                or not isinstance(value, Integral)
                or value <= 0
            ):
                raise WeakIdError(f"{name} must be a positive integer")
        if delivered_replicates < self.min_replicates or \
                seeds < self.min_seeds:
            raise WeakIdError(
                f"grid point delivered {delivered_replicates} replicates "
                f"over {seeds} seeds; the pre-registration requires at "
                f"least {self.min_replicates} over {self.min_seeds}")

    def require_pinned_threshold(self, threshold: float) -> None:
        if (
            isinstance(threshold, bool)
            or not isinstance(threshold, Real)
            or not math.isfinite(float(threshold))
            or not 0 <= threshold <= 1
        ):
            raise WeakIdError(
                "retain threshold must be a finite probability in [0, 1]")
        if abs(threshold - self.retain_lower_bound) > 1e-12:
            raise WeakIdError(
                f"retain threshold {threshold} differs from the pinned "
                f"{self.retain_lower_bound}; tuning the threshold to the "
                "coverage requires a NEW calibration/evaluation split")


def _validated_grid_values(values: Sequence[str], label: str) -> list[str]:
    if isinstance(values, (str, bytes)) or not values:
        raise WeakIdError(f"{label} must be a non-empty sequence")
    normalized = list(values)
    if any(not isinstance(value, str) or not value for value in normalized):
        raise WeakIdError(
            f"{label} must contain only non-empty string grid keys")
    if len(set(normalized)) != len(normalized):
        raise WeakIdError(f"{label} must not contain duplicate grid keys")
    return normalized


def require_full_grid(evaluated_w: Sequence[str],
                      registered_w: Sequence[str]) -> None:
    """Coverage must be computed over the FULL registered grid, never a
    central/high-signal subset."""
    evaluated = _validated_grid_values(evaluated_w, "evaluated grid")
    registered = _validated_grid_values(registered_w, "registered grid")
    evaluated_set = set(evaluated)
    registered_set = set(registered)
    missing = [w for w in registered if w not in evaluated_set]
    if missing:
        raise WeakIdError(
            f"coverage evaluated over a subset only; the grid points "
            f"{missing} are missing — computing coverage over central "
            "cases only is refused")
    unexpected = [w for w in evaluated if w not in registered_set]
    if unexpected:
        raise WeakIdError(
            f"coverage includes unregistered grid points {unexpected}; "
            "the frozen evaluation grid must be matched exactly")


def build_failure_map(point_results: Sequence[dict],
                      threshold: float,
                      bound_key: str = "family_wise_lower") -> dict:
    """A below-threshold grid point is PRESERVED here (never removed
    from the reported grid). The retain decision uses the family-wise
    (simultaneous) lower bound recorded under ``bound_key``."""
    failures = [{"w": r["w"], "procedure": r["procedure"],
                 "theta0_position": r.get("theta0_position"),
                 "coverage": r["coverage"],
                 bound_key: r[bound_key]}
                for r in point_results
                if r[bound_key] < threshold]
    return {
        "threshold": threshold,
        "failing_points": failures,
        "failing_count": len(failures),
        "all_points_reported": len(point_results),
    }


def require_failure_map_complete(reported_w: Sequence[str],
                                 all_w: Sequence[str]) -> None:
    """A failing grid point must remain in the reported grid, not be
    silently dropped."""
    reported = _validated_grid_values(reported_w, "reported grid")
    registered = _validated_grid_values(all_w, "registered grid")
    reported_set = set(reported)
    registered_set = set(registered)
    dropped = [w for w in registered if w not in reported_set]
    if dropped:
        raise WeakIdError(
            f"grid points {dropped} were dropped from the reported grid; "
            "a below-threshold corner must be PRESERVED in the failure "
            "map, never removed")
    unexpected = [w for w in reported if w not in registered_set]
    if unexpected:
        raise WeakIdError(
            f"reported grid contains unregistered points {unexpected}; "
            "the frozen grid must be preserved exactly")


# ---------------------------------------------------------------------------
# Uniform-language lint
# ---------------------------------------------------------------------------

_UNIFORM_TOKENS = ("uniform", "uniformly", "class-wide")


def require_uniform_certificate(certificate_id: str | None) -> None:
    """The word 'uniform' (class-wide coverage) is admissible only with a
    registered continuity/mesh certificate; the registry is empty."""
    if not certificate_id or certificate_id not in \
            CONTINUITY_MESH_CERTIFICATES:
        raise WeakIdError(
            "uniform (class-wide) coverage language requires a registered "
            "continuity/mesh-error certificate; none is registered, so "
            "only GRID-CONDITIONAL empirical coverage may be claimed")


def _normalize_lint(text: str) -> str:
    """Strip zero-width characters and intra-word hyphens so
    obfuscations like 'uni-form' or a zero-width-split 'unif<zwsp>orm'
    cannot slip the token check. A bounded normalization, not a proof of
    completeness."""
    import re

    lowered = text.lower()
    for zw in ("​", "‌", "‍", "﻿", "⁠"):
        lowered = lowered.replace(zw, "")
    # remove hyphens/underscores/spaces BETWEEN letters (join split words)
    lowered = re.sub(r"(?<=[a-z])[-_ ]+(?=[a-z])", "", lowered)
    return lowered


def lint_uniform(text: str, certificate_id: str | None = None) -> None:
    normalized = _normalize_lint(text)
    # "classwide" after normalization covers "class-wide"/"class wide"
    tokens = ("uniform", "uniformly", "classwide")
    # exclude the explicit negation "nonuniform" (a legitimate word)
    scrubbed = normalized.replace("nonuniform", "")
    if any(tok in scrubbed for tok in tokens):
        require_uniform_certificate(certificate_id)


_FORBIDDEN_PHRASES = tuple(
    a + b for a, b in (
        ("uniform coverage", " over the class"),
        ("coverage from", " the central cases"),
        ("dropped the", " failing corner"),
        ("tuned the threshold", " to the coverage"),
        ("detected", " the signal"),
        ("shear", " detected"), ("isotropy", " established"),
        ("bianchi geometry", " detected"),
        ("bianchi family", " identified"), ("finding", " rescued"),
        ("validated as", " native"),
    )
)


def lint_caption(text: str) -> None:
    lowered = text.lower()
    for phrase in _FORBIDDEN_PHRASES:
        if phrase.lower() in lowered:
            raise WeakIdError(
                "caption carries forbidden uniform/central/dropped/"
                "tuned/detection language")
    lint_uniform(text)


def generate_caption(min_lower: float, n_points: int,
                     failing: int) -> str:
    text = (
        "[weak_id_coverage] Grid-conditional simultaneous empirical "
        f"coverage of the Imbens-Manski CI over {n_points} pre-registered "
        f"DGP grid points (point -> partial -> unidentified) at the "
        f"least-favorable boundary theta0. Minimum family-wise 99% "
        f"(Bonferroni over all grid points) lower bound {min_lower:.4f} "
        f">= 0.93; {failing} adversarial-procedure points below the "
        "threshold preserved in the failure map. Not extended to the "
        "whole nuisance class (no continuity/mesh certificate); no "
        "detection."
    )
    lint_caption(text)
    return text
