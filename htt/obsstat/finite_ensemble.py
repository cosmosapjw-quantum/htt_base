"""Fail-closed finite-ensemble numerical-resolution primitives for PR-173.

The module certifies only whether a reported Monte Carlo quantity is resolved
under a registered finite-ensemble contract.  It does not classify a physical
signal, validate a null model, or authorize any model/family interpretation.
"""
from __future__ import annotations

import hashlib
import json
import math
from fractions import Fraction
from typing import Mapping, Sequence

import numpy as np


RESOLVED = "RESOLVED_WITHIN_REGISTERED_MC_CONTRACT"
UNRESOLVED = "NUMERICALLY_UNRESOLVED_AT_CURRENT_MC_BUDGET"
ALLOWED_STATUSES = (RESOLVED, UNRESOLVED)
INPUT_AVAILABLE = "AVAILABLE_AUTHENTICATED_COMPLETE"
INPUT_UNAVAILABLE = "NOT_EVALUATED_INPUT_UNAVAILABLE"
INPUT_PARTIAL_FORBIDDEN = "NOT_EVALUATED_PARTIAL_INPUT_FORBIDDEN"
LINEAGE_CERTIFIED = "CERTIFIED"
LINEAGE_MISSING = "NOT_CERTIFIABLE_MISSING_REPLICATE_LINEAGE"
LINEAGE_INVALID = "NOT_CERTIFIABLE_INVALID_DEPENDENCE_METHOD"
ALLOWED_INPUT_STATUSES = (INPUT_AVAILABLE, INPUT_UNAVAILABLE, INPUT_PARTIAL_FORBIDDEN)
ALLOWED_LINEAGE_STATUSES = (LINEAGE_CERTIFIED, LINEAGE_MISSING, LINEAGE_INVALID)


class FiniteEnsembleError(ValueError):
    """Raised when a finite-ensemble contract is incomplete or inconsistent."""


def _finite(value: float, name: str) -> float:
    if isinstance(value, bool):
        raise FiniteEnsembleError(f"{name} must be numeric, not boolean")
    result = float(value)
    if not math.isfinite(result):
        raise FiniteEnsembleError(f"{name} must be finite")
    return result


def _positive_count(value: int, name: str, *, minimum: int = 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise FiniteEnsembleError(f"{name} must be an integer >= {minimum}")
    return value


def finite_rank_resolution(n_null: int) -> Fraction:
    """Return the exact discrete resolution ``1/(N+1)``."""

    n_null = _positive_count(n_null, "n_null")
    return Fraction(1, n_null + 1)


def plus_one_rank(n_null: int, exceedance_count: int) -> Fraction:
    """Return ``(1+b)/(N+1)`` under the conservative greater-equal policy."""

    n_null = _positive_count(n_null, "n_null")
    if (
        isinstance(exceedance_count, bool)
        or not isinstance(exceedance_count, int)
        or not 0 <= exceedance_count <= n_null
    ):
        raise FiniteEnsembleError("exceedance_count must be an integer in [0, N]")
    return Fraction(1 + exceedance_count, n_null + 1)


def iid_rank_delete_one_jackknife_se(n_null: int, exceedance_count: int) -> float:
    """Delete-one jackknife SE of the plus-one rank over iid null units.

    The exact closed form is derived by deleting each binary exceedance unit
    in turn.  It is zero at the two boundaries; the finite-rank resolution is
    therefore retained as a separately reported support-grid limitation.
    """

    plus_one_rank(n_null, exceedance_count)
    n = float(n_null)
    b = float(exceedance_count)
    return math.sqrt(b * (n - b) * (n - 1.0)) / (n * n)


def _confidence_interval(values: Sequence[float], *, estimate: float) -> tuple[float, float]:
    if len(values) != 2:
        raise FiniteEnsembleError("uncertainty_interval must contain two endpoints")
    lower = _finite(values[0], "uncertainty_interval lower")
    upper = _finite(values[1], "uncertainty_interval upper")
    if lower > upper:
        raise FiniteEnsembleError("uncertainty_interval endpoints are reversed")
    if not lower <= estimate <= upper:
        raise FiniteEnsembleError("uncertainty_interval must contain the estimate")
    return lower, upper


def _confidence_level(value: float) -> float:
    confidence = _finite(value, "confidence_level")
    if not 0.0 < confidence < 1.0:
        raise FiniteEnsembleError("confidence_level must lie strictly between zero and one")
    return confidence


def _boundary_status(*, lower: float, upper: float, boundary: float, direction: str) -> str:
    if direction == "below":
        resolved = upper < boundary
    elif direction == "above":
        resolved = lower > boundary
    elif direction == "away_from":
        resolved = upper < boundary or lower > boundary
    else:
        raise FiniteEnsembleError("direction must be below, above, or away_from")
    return RESOLVED if resolved else UNRESOLVED


def rank_certificate(
    *,
    n_null: int,
    exceedance_count: int,
    uncertainty_interval: Sequence[float],
    boundary: float,
    direction: str,
    confidence_level: float,
    uncertainty_method: str,
    mc_se: float | None = None,
) -> dict[str, object]:
    """Build a boundary-aware finite-rank numerical-resolution certificate.

    The registered dependence-aware confidence interval is expanded by one
    exact finite-rank grid spacing.  A decision is resolved only when that
    complete guard interval lies strictly on the preregistered side of the
    probability boundary.  This avoids combining a rank floor with a
    dimensional uncertainty or treating distance from the minimum attainable
    rank as the scientific decision boundary.
    """

    p = plus_one_rank(n_null, exceedance_count)
    floor = finite_rank_resolution(n_null)
    estimate = float(p)
    lower, upper = _confidence_interval(uncertainty_interval, estimate=estimate)
    if lower < 0.0 or upper > 1.0:
        raise FiniteEnsembleError("rank uncertainty_interval must lie in [0, 1]")
    registered_boundary = _finite(boundary, "boundary")
    if not 0.0 <= registered_boundary <= 1.0:
        raise FiniteEnsembleError("rank boundary must lie in [0, 1]")
    confidence = _confidence_level(confidence_level)
    if not isinstance(uncertainty_method, str) or not uncertainty_method:
        raise FiniteEnsembleError("uncertainty_method must be non-empty")
    standard_error = None
    if mc_se is not None:
        standard_error = _finite(mc_se, "mc_se")
        if standard_error < 0.0:
            raise FiniteEnsembleError("mc_se must be non-negative")
    grid = float(floor)
    guard_lower = max(0.0, lower - grid)
    guard_upper = min(1.0, upper + grid)
    status = _boundary_status(
        lower=guard_lower,
        upper=guard_upper,
        boundary=registered_boundary,
        direction=direction,
    )
    return {
        "certificate_kind": "finite_rank_boundary",
        "input_availability_status": INPUT_AVAILABLE,
        "replicate_lineage_status": LINEAGE_CERTIFIED,
        "numerical_resolution_status": status,
        "n_null": n_null,
        "exceedance_count": exceedance_count,
        "tie_policy": "conservative_ge",
        "rank_fraction": f"{p.numerator}/{p.denominator}",
        "estimate": estimate,
        "estimand_unit": "probability",
        "finite_resolution_fraction": f"{floor.numerator}/{floor.denominator}",
        "finite_resolution": grid,
        "uncertainty_interval": [lower, upper],
        "guard_interval": [guard_lower, guard_upper],
        "mc_se": standard_error,
        "confidence_level": confidence,
        "uncertainty_method": uncertainty_method,
        "boundary": registered_boundary,
        "boundary_unit": "probability",
        "direction": direction,
        "decision_rule": "guard_interval_strictly_on_registered_boundary_side",
        "physical_interpretation": "not_evaluated",
        "gaussian_sigma_emitted": False,
    }


def scalar_certificate(
    *,
    estimate: float,
    uncertainty_interval: Sequence[float],
    boundary: float,
    direction: str,
    confidence_level: float,
    uncertainty_method: str,
    estimand_unit: str,
    mc_se: float | None = None,
) -> dict[str, object]:
    """Build a same-unit, boundary-aware scalar resolution certificate."""

    estimate = _finite(estimate, "estimate")
    lower, upper = _confidence_interval(uncertainty_interval, estimate=estimate)
    registered_boundary = _finite(boundary, "boundary")
    confidence = _confidence_level(confidence_level)
    if not isinstance(uncertainty_method, str) or not uncertainty_method:
        raise FiniteEnsembleError("uncertainty_method must be non-empty")
    if not isinstance(estimand_unit, str) or not estimand_unit:
        raise FiniteEnsembleError("estimand_unit must be non-empty")
    standard_error = None
    if mc_se is not None:
        standard_error = _finite(mc_se, "mc_se")
        if standard_error < 0.0:
            raise FiniteEnsembleError("mc_se must be non-negative")
    status = _boundary_status(
        lower=lower,
        upper=upper,
        boundary=registered_boundary,
        direction=direction,
    )
    return {
        "certificate_kind": "scalar_boundary",
        "input_availability_status": INPUT_AVAILABLE,
        "replicate_lineage_status": LINEAGE_CERTIFIED,
        "numerical_resolution_status": status,
        "estimate": estimate,
        "estimand_unit": estimand_unit,
        "uncertainty_interval": [lower, upper],
        "mc_se": standard_error,
        "confidence_level": confidence,
        "uncertainty_method": uncertainty_method,
        "boundary": registered_boundary,
        "boundary_unit": estimand_unit,
        "direction": direction,
        "decision_rule": "confidence_interval_strictly_on_registered_boundary_side",
        "physical_interpretation": "not_evaluated",
    }


def not_certifiable_certificate(
    *,
    reason: str,
    required_method: str,
    lineage_status: str,
) -> dict[str, object]:
    """Represent an available input whose numerical lineage cannot certify a decision."""

    if not isinstance(reason, str) or not reason:
        raise FiniteEnsembleError("reason must be non-empty")
    if not isinstance(required_method, str) or not required_method:
        raise FiniteEnsembleError("required_method must be non-empty")
    if lineage_status not in (LINEAGE_MISSING, LINEAGE_INVALID):
        raise FiniteEnsembleError("lineage_status must be a not-certifiable status")
    return {
        "certificate_kind": "not_certifiable",
        "input_availability_status": INPUT_AVAILABLE,
        "replicate_lineage_status": lineage_status,
        "numerical_resolution_status": None,
        "reason": reason,
        "required_method": required_method,
        "estimate": None,
        "mc_se": None,
        "physical_interpretation": "not_evaluated",
    }


def not_evaluated_certificate(
    *,
    reason: str,
    required_method: str,
    availability_status: str,
) -> dict[str, object]:
    """Represent unavailable or forbidden-partial input without a numerical verdict."""

    if not isinstance(reason, str) or not reason:
        raise FiniteEnsembleError("reason must be non-empty")
    if not isinstance(required_method, str) or not required_method:
        raise FiniteEnsembleError("required_method must be non-empty")
    if availability_status not in (INPUT_UNAVAILABLE, INPUT_PARTIAL_FORBIDDEN):
        raise FiniteEnsembleError("availability_status must be a not-evaluated status")
    return {
        "certificate_kind": "not_evaluated",
        "input_availability_status": availability_status,
        "replicate_lineage_status": None,
        "numerical_resolution_status": None,
        "reason": reason,
        "required_method": required_method,
        "estimate": None,
        "mc_se": None,
        "physical_interpretation": "not_evaluated",
    }


def seed_sem(seed_estimates: Sequence[float]) -> float:
    """Sample standard deviation across independent seeds divided by sqrt(K)."""

    values = np.asarray([_finite(value, "seed estimate") for value in seed_estimates])
    if values.ndim != 1 or values.size < 2:
        raise FiniteEnsembleError("seed_sem requires at least two scalar seed estimates")
    return float(np.std(values, ddof=1) / math.sqrt(values.size))


def batch_means_se(samples: Sequence[float], *, batch_size: int) -> float:
    """Standard error from equal-size non-overlapping batch means."""

    batch_size = _positive_count(batch_size, "batch_size")
    values = np.asarray([_finite(value, "sample") for value in samples])
    if values.ndim != 1 or values.size < 2 * batch_size:
        raise FiniteEnsembleError("batch_means_se requires at least two full batches")
    if values.size % batch_size:
        raise FiniteEnsembleError("batch_means_se requires equal complete batch sizes")
    means = values.reshape((-1, batch_size)).mean(axis=1)
    return float(np.std(means, ddof=1) / math.sqrt(means.size))


def delete_one_jackknife_se(leave_one_estimates: Sequence[float]) -> float:
    """Standard delete-one jackknife SE from already computed replicates."""

    values = np.asarray(
        [_finite(value, "leave-one estimate") for value in leave_one_estimates]
    )
    if values.ndim != 1 or values.size < 2:
        raise FiniteEnsembleError("jackknife requires at least two leave-one estimates")
    mean = float(values.mean())
    return float(math.sqrt((values.size - 1.0) / values.size * np.sum((values - mean) ** 2)))


def clustered_rank_bootstrap(
    clusters: Mapping[int | str, Sequence[bool | int]],
    *,
    seed: int = 20260719,
    replicates: int = 20000,
) -> dict[str, object]:
    """Whole-cluster bootstrap uncertainty for a plus-one finite rank.

    Each bootstrap draw selects the original number of clusters with
    replacement.  All rows in a selected cluster move together, preserving
    the registered within-cluster dependence.
    """

    replicates = _positive_count(replicates, "replicates", minimum=2)
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise FiniteEnsembleError("seed must be an integer")
    if not isinstance(clusters, Mapping) or len(clusters) < 2:
        raise FiniteEnsembleError("cluster bootstrap requires at least two clusters")
    try:
        labels = sorted(clusters)
    except TypeError as exc:
        raise FiniteEnsembleError("cluster labels must have one sortable type") from exc
    counts: list[int] = []
    sizes: list[int] = []
    for label in labels:
        rows = list(clusters[label])
        if not rows:
            raise FiniteEnsembleError(f"cluster {label!r} is empty")
        normalized: list[int] = []
        for value in rows:
            if isinstance(value, bool):
                normalized.append(int(value))
                continue
            if not isinstance(value, int) or value not in (0, 1):
                raise FiniteEnsembleError("cluster rows must be binary exceedances")
            normalized.append(int(value))
        counts.append(sum(normalized))
        sizes.append(len(normalized))
    counts_array = np.asarray(counts, dtype=np.int64)
    sizes_array = np.asarray(sizes, dtype=np.int64)
    rng = np.random.default_rng(seed)
    samples = np.empty(replicates, dtype=float)
    cluster_count = len(labels)
    chunk = 1000
    for start in range(0, replicates, chunk):
        stop = min(start + chunk, replicates)
        selected = rng.integers(0, cluster_count, size=(stop - start, cluster_count))
        b = counts_array[selected].sum(axis=1)
        n = sizes_array[selected].sum(axis=1)
        samples[start:stop] = (1.0 + b) / (1.0 + n)
    return {
        "method": "whole_cluster_bootstrap_plus_one_rank",
        "seed": seed,
        "replicates": replicates,
        "cluster_count": cluster_count,
        "row_count": int(sizes_array.sum()),
        "exceedance_count": int(counts_array.sum()),
        "cluster_size_set": sorted({int(value) for value in sizes_array}),
        "mc_se": float(np.std(samples, ddof=1)),
        "median": float(np.median(samples)),
        "percentile_95_interval": [
            float(np.quantile(samples, 0.025)),
            float(np.quantile(samples, 0.975)),
        ],
    }


def infer_exceedance_count(reported_p: float, n_null: int, *, tolerance: float) -> int:
    """Recover and validate the integer rank count from a rounded reported p."""

    reported = _finite(reported_p, "reported_p")
    tolerance = _finite(tolerance, "tolerance")
    if tolerance < 0.0:
        raise FiniteEnsembleError("tolerance must be non-negative")
    n_null = _positive_count(n_null, "n_null")
    candidate = round(reported * (n_null + 1) - 1.0)
    exact = plus_one_rank(n_null, int(candidate))
    if abs(float(exact) - reported) > tolerance:
        raise FiniteEnsembleError("reported p is not on the registered finite-rank grid")
    return int(candidate)


def certificate_errors(certificate: Mapping[str, object]) -> list[str]:
    """Recompute a certificate from primitives and report any false-green drift."""

    if not isinstance(certificate, Mapping):
        return ["certificate is not a mapping"]
    kind = certificate.get("certificate_kind")
    try:
        if kind == "finite_rank_boundary":
            expected = rank_certificate(
                n_null=certificate.get("n_null"),  # type: ignore[arg-type]
                exceedance_count=certificate.get("exceedance_count"),  # type: ignore[arg-type]
                uncertainty_interval=certificate.get("uncertainty_interval"),  # type: ignore[arg-type]
                boundary=certificate.get("boundary"),  # type: ignore[arg-type]
                direction=certificate.get("direction"),  # type: ignore[arg-type]
                confidence_level=certificate.get("confidence_level"),  # type: ignore[arg-type]
                mc_se=certificate.get("mc_se"),  # type: ignore[arg-type]
                uncertainty_method=certificate.get("uncertainty_method"),  # type: ignore[arg-type]
            )
        elif kind == "scalar_boundary":
            expected = scalar_certificate(
                estimate=certificate.get("estimate"),  # type: ignore[arg-type]
                uncertainty_interval=certificate.get("uncertainty_interval"),  # type: ignore[arg-type]
                boundary=certificate.get("boundary"),  # type: ignore[arg-type]
                direction=certificate.get("direction"),  # type: ignore[arg-type]
                confidence_level=certificate.get("confidence_level"),  # type: ignore[arg-type]
                mc_se=certificate.get("mc_se"),  # type: ignore[arg-type]
                uncertainty_method=certificate.get("uncertainty_method"),  # type: ignore[arg-type]
                estimand_unit=certificate.get("estimand_unit"),  # type: ignore[arg-type]
            )
        elif kind == "not_certifiable":
            expected = not_certifiable_certificate(
                reason=certificate.get("reason"),  # type: ignore[arg-type]
                required_method=certificate.get("required_method"),  # type: ignore[arg-type]
                lineage_status=certificate.get("replicate_lineage_status"),  # type: ignore[arg-type]
            )
        elif kind == "not_evaluated":
            expected = not_evaluated_certificate(
                reason=certificate.get("reason"),  # type: ignore[arg-type]
                required_method=certificate.get("required_method"),  # type: ignore[arg-type]
                availability_status=certificate.get("input_availability_status"),  # type: ignore[arg-type]
            )
        else:
            return [f"unknown certificate_kind: {kind!r}"]
    except (FiniteEnsembleError, TypeError, ValueError) as exc:
        return [f"invalid certificate primitives: {exc}"]
    if dict(certificate) != expected:
        return ["certificate derived fields do not match its primitives"]
    numerical_status = expected["numerical_resolution_status"]
    if numerical_status is not None and numerical_status not in ALLOWED_STATUSES:
        return ["certificate numerical status is outside the typed status set"]
    return []


def require_valid_certificate(certificate: Mapping[str, object]) -> None:
    """Raise if a certificate cannot be reproduced from its own primitives."""

    errors = certificate_errors(certificate)
    if errors:
        raise FiniteEnsembleError("; ".join(errors))


def semantic_digest(payload: Mapping[str, object]) -> str:
    """Stable digest excluding a payload's own ``semantic_digest`` field."""

    value = dict(payload)
    value.pop("semantic_digest", None)
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
