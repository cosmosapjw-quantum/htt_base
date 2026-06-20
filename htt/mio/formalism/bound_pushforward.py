"""Synthetic bound-to-Pi and finite-cover diagnostics for REV-R084."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
import math
from typing import Any


DEFAULT_BOUND_PUSHFORWARD_CAVEAT = (
    "Synthetic MIO bound-pushforward diagnostic only; Pi remains threshold "
    "exceedance, not truth probability, posterior odds, HTT evidence, native "
    "solver validation, or geometry/family support."
)


def _values(values: Sequence[object], name: str) -> tuple[float, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be a numeric sequence")
    result = tuple(float(value) for value in values)
    if not result or any(not math.isfinite(value) or value < 0.0 for value in result):
        raise ValueError(f"{name} must contain finite nonnegative values")
    return result


def _unit_values(values: Sequence[object], name: str) -> tuple[float, ...]:
    result = _values(values, name)
    if any(value > 1.0 for value in result):
        raise ValueError(f"{name} values must lie in the unit interval")
    return result


def _curve(samples: tuple[float, ...], thresholds: tuple[float, ...]) -> list[float]:
    count = float(len(samples))
    return [sum(value > threshold for value in samples) / count for threshold in thresholds]


@dataclass(frozen=True)
class BoundToPiDominationResult:
    theorem_id: str
    thresholds: tuple[float, ...]
    sample_pi_curve: tuple[float, ...]
    bound_pi_curve: tuple[float, ...]
    domination_status: str = "samplewise_bound_dominates_pi"
    owner: str = "MIO"
    implementation_scope: str = "mio"
    claim_tier: str = "diagnostic_only"
    transfer_source: str = "none"
    production_claim_allowed: bool = False
    native_solver_result: bool = False
    family_identification: bool = False
    caveats: tuple[str, ...] = field(default_factory=lambda: (DEFAULT_BOUND_PUSHFORWARD_CAVEAT,))

    def as_payload(self) -> dict[str, Any]:
        return {
            "theorem_id": self.theorem_id,
            "domination_status": self.domination_status,
            "thresholds": list(self.thresholds),
            "sample_pi_curve": list(self.sample_pi_curve),
            "bound_pi_curve": list(self.bound_pi_curve),
            "owner": self.owner,
            "implementation_scope": self.implementation_scope,
            "claim_tier": self.claim_tier,
            "transfer_source": self.transfer_source,
            "production_claim_allowed": self.production_claim_allowed,
            "native_solver_result": self.native_solver_result,
            "family_identification": self.family_identification,
            "caveats": list(self.caveats),
        }


@dataclass(frozen=True)
class FiniteCoverUnionBoundResult:
    theorem_id: str
    local_bounds: tuple[float, ...]
    union_bound: float
    cover_status: str
    physical_cover_use_allowed: bool
    physical_metric_status: str
    mask_selection_status: str
    lipschitz_provenance: str
    owner: str = "MIO"
    implementation_scope: str = "mio"
    claim_tier: str = "diagnostic_only"
    transfer_source: str = "none"
    production_claim_allowed: bool = False
    native_solver_result: bool = False
    family_identification: bool = False
    caveats: tuple[str, ...] = field(default_factory=lambda: (DEFAULT_BOUND_PUSHFORWARD_CAVEAT,))

    def as_payload(self) -> dict[str, Any]:
        return {
            "theorem_id": self.theorem_id,
            "cover_status": self.cover_status,
            "local_bounds": list(self.local_bounds),
            "union_bound": self.union_bound,
            "physical_cover_use_allowed": self.physical_cover_use_allowed,
            "physical_metric_status": self.physical_metric_status,
            "mask_selection_status": self.mask_selection_status,
            "lipschitz_provenance": self.lipschitz_provenance,
            "owner": self.owner,
            "implementation_scope": self.implementation_scope,
            "claim_tier": self.claim_tier,
            "transfer_source": self.transfer_source,
            "production_claim_allowed": self.production_claim_allowed,
            "native_solver_result": self.native_solver_result,
            "family_identification": self.family_identification,
            "caveats": list(self.caveats),
        }


def bound_to_pi_domination(
    *,
    sample_values: Sequence[object],
    bound_values: Sequence[object],
    thresholds: Sequence[object],
    theorem_id: str,
) -> BoundToPiDominationResult:
    samples = _values(sample_values, "sample_values")
    bounds = _values(bound_values, "bound_values")
    threshold_values = tuple(sorted(set(_values(thresholds, "thresholds"))))
    if len(samples) != len(bounds):
        raise ValueError("sample_values and bound_values must have matching samplewise length")
    if any(bound < sample for sample, bound in zip(samples, bounds, strict=True)):
        raise ValueError("bound_values must dominate sample_values samplewise")
    return BoundToPiDominationResult(
        theorem_id=theorem_id,
        thresholds=threshold_values,
        sample_pi_curve=tuple(_curve(samples, threshold_values)),
        bound_pi_curve=tuple(_curve(bounds, threshold_values)),
    )


def finite_cover_union_bound(
    local_bounds: Sequence[object],
    *,
    theorem_id: str,
    physical_metric_status: str = "not_bound",
    mask_selection_status: str = "not_bound",
    lipschitz_provenance: str = "not_bound",
) -> FiniteCoverUnionBoundResult:
    bounds = _unit_values(local_bounds, "local_bounds")
    physical_ready = (
        physical_metric_status == "bound"
        and mask_selection_status == "bound"
        and lipschitz_provenance == "bound"
    )
    return FiniteCoverUnionBoundResult(
        theorem_id=theorem_id,
        local_bounds=bounds,
        union_bound=min(1.0, sum(bounds)),
        cover_status="finite_cover_union_bound" if physical_ready else "descriptive_cover_only",
        physical_cover_use_allowed=physical_ready,
        physical_metric_status=physical_metric_status,
        mask_selection_status=mask_selection_status,
        lipschitz_provenance=lipschitz_provenance,
    )
