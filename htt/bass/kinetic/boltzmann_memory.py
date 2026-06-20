"""Synthetic Boltzmann-memory decay diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any


DEFAULT_KINETIC_CAVEAT = (
    "Synthetic BASS kinetic diagnostic only; not transfer validation, not native "
    "solver validation, not HTT evidence, and not geometry/family support."
)


def _nonnegative(value: object, name: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number < 0.0:
        raise ValueError(f"{name} must be non-negative finite")
    return number


@dataclass(frozen=True)
class ExponentialMemoryBound:
    theorem_id: str
    memory_status: str
    memory_bound: float | None
    collision_gap: float
    kill_switches: tuple[str, ...]
    owner: str = "BASS"
    implementation_scope: str = "bass_py"
    claim_tier: str = "diagnostic_only"
    transfer_source: str = "none"
    production_claim_allowed: bool = False
    native_solver_result: bool = False
    family_identification: bool = False
    caveats: tuple[str, ...] = field(default_factory=lambda: (DEFAULT_KINETIC_CAVEAT,))

    def as_payload(self) -> dict[str, Any]:
        return {
            "theorem_id": self.theorem_id,
            "memory_status": self.memory_status,
            "memory_bound": self.memory_bound,
            "collision_gap": self.collision_gap,
            "kill_switches": list(self.kill_switches),
            "owner": self.owner,
            "implementation_scope": self.implementation_scope,
            "claim_tier": self.claim_tier,
            "transfer_source": self.transfer_source,
            "production_claim_allowed": self.production_claim_allowed,
            "native_solver_result": self.native_solver_result,
            "family_identification": self.family_identification,
            "caveats": list(self.caveats),
        }


def exponential_memory_bound(
    *,
    initial_norm: float,
    source_envelope: float,
    collision_gap: float,
    time_span: float,
    theorem_id: str,
) -> ExponentialMemoryBound:
    initial = _nonnegative(initial_norm, "initial_norm")
    source = _nonnegative(source_envelope, "source_envelope")
    gap = float(collision_gap)
    span = _nonnegative(time_span, "time_span")
    if not math.isfinite(gap):
        raise ValueError("collision_gap must be finite")
    if gap <= 0.0:
        return ExponentialMemoryBound(
            theorem_id=theorem_id,
            memory_status="blocked_collision_gap_nonpositive",
            memory_bound=None,
            collision_gap=gap,
            kill_switches=("collision_gap_nonpositive_blocks_exponential_forgetting_language",),
        )
    decay = math.exp(-gap * span)
    bound = initial * decay + (source / gap) * (1.0 - decay)
    return ExponentialMemoryBound(
        theorem_id=theorem_id,
        memory_status="synthetic_exponential_forgetting_bound",
        memory_bound=bound,
        collision_gap=gap,
        kill_switches=(),
    )
