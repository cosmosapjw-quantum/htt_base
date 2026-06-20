"""Synthetic dynamic-budget barrier diagnostics for REV-R084."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any


DEFAULT_DYNAMIC_BUDGET_CAVEAT = (
    "Synthetic MIO dynamic-budget diagnostic only; not HTT evidence, not a "
    "posterior, not native solver validation, and not geometry/family support."
)


def _finite(value: object, name: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _nonnegative(value: object, name: str) -> float:
    number = _finite(value, name)
    if number < 0.0:
        raise ValueError(f"{name} must be non-negative finite")
    return number


@dataclass(frozen=True)
class DynamicBudgetBarrierResult:
    theorem_id: str
    barrier_status: str
    candidate_bound: float | None
    comparison_budget: float
    barrier_margin: float | None
    collision_gap: float
    kill_switches: tuple[str, ...]
    numerator_channel: str
    budget_channel: str
    numerator_operator: str
    budget_operator: str
    owner: str = "MIO"
    implementation_scope: str = "mio"
    claim_tier: str = "diagnostic_only"
    transfer_source: str = "none"
    production_claim_allowed: bool = False
    native_solver_result: bool = False
    family_identification: bool = False
    caveats: tuple[str, ...] = field(
        default_factory=lambda: (
            DEFAULT_DYNAMIC_BUDGET_CAVEAT,
            "not HTT evidence",
            "not native solver validation",
            "not geometry/family support",
        )
    )

    def as_payload(self) -> dict[str, Any]:
        return {
            "theorem_id": self.theorem_id,
            "barrier_status": self.barrier_status,
            "candidate_bound": self.candidate_bound,
            "comparison_budget": self.comparison_budget,
            "barrier_margin": self.barrier_margin,
            "collision_gap": self.collision_gap,
            "kill_switches": list(self.kill_switches),
            "numerator_channel": self.numerator_channel,
            "budget_channel": self.budget_channel,
            "numerator_operator": self.numerator_operator,
            "budget_operator": self.budget_operator,
            "owner": self.owner,
            "implementation_scope": self.implementation_scope,
            "claim_tier": self.claim_tier,
            "transfer_source": self.transfer_source,
            "production_claim_allowed": self.production_claim_allowed,
            "native_solver_result": self.native_solver_result,
            "family_identification": self.family_identification,
            "caveats": list(self.caveats),
        }


def dynamic_comparison_budget_barrier(
    *,
    initial_budget: float,
    forcing_envelope: float,
    damping_integral: float,
    comparison_budget: float,
    collision_gap: float,
    theorem_id: str,
    numerator_channel: str = "synthetic_channel",
    budget_channel: str = "synthetic_channel",
    numerator_operator: str = "x_C",
    budget_operator: str = "x_C",
) -> DynamicBudgetBarrierResult:
    initial = _nonnegative(initial_budget, "initial_budget")
    forcing = _nonnegative(forcing_envelope, "forcing_envelope")
    damping = _nonnegative(damping_integral, "damping_integral")
    comparison = _finite(comparison_budget, "comparison_budget")
    gap = _finite(collision_gap, "collision_gap")
    if comparison <= 0.0:
        raise ValueError("comparison_budget must be positive finite")
    if gap <= 0.0:
        return DynamicBudgetBarrierResult(
            theorem_id=theorem_id,
            barrier_status="blocked_collision_gap_nonpositive",
            candidate_bound=None,
            comparison_budget=comparison,
            barrier_margin=None,
            collision_gap=gap,
            kill_switches=("collision_gap_nonpositive_blocks_exponential_forgetting_language",),
            numerator_channel=numerator_channel,
            budget_channel=budget_channel,
            numerator_operator=numerator_operator,
            budget_operator=budget_operator,
        )
    if numerator_channel != budget_channel or numerator_operator != budget_operator:
        return DynamicBudgetBarrierResult(
            theorem_id=theorem_id,
            barrier_status="blocked_channel_or_operator_mismatch",
            candidate_bound=None,
            comparison_budget=comparison,
            barrier_margin=None,
            collision_gap=gap,
            kill_switches=("channel_operator_mismatch_blocks_dynamic_budget_certification",),
            numerator_channel=numerator_channel,
            budget_channel=budget_channel,
            numerator_operator=numerator_operator,
            budget_operator=budget_operator,
        )
    decay = math.exp(-gap * damping)
    candidate = initial * decay + (forcing / gap) * (1.0 - decay)
    margin = comparison - candidate
    status = "synthetic_barrier_certified" if margin >= 0.0 else "blocked_comparison_budget_exceeded"
    return DynamicBudgetBarrierResult(
        theorem_id=theorem_id,
        barrier_status=status,
        candidate_bound=candidate,
        comparison_budget=comparison,
        barrier_margin=margin,
        collision_gap=gap,
        kill_switches=(),
        numerator_channel=numerator_channel,
        budget_channel=budget_channel,
        numerator_operator=numerator_operator,
        budget_operator=budget_operator,
    )
