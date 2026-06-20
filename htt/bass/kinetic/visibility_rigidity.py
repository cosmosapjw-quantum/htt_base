"""Synthetic visibility-cancellation no-go diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any


DEFAULT_VISIBILITY_CAVEAT = (
    "Synthetic BASS visibility diagnostic only; observed line-of-sight source "
    "bounds require sign/phase, rank, mask, and kernel-floor provenance."
)


@dataclass(frozen=True)
class VisibilityCancellationNoGo:
    theorem_id: str
    no_go_status: str
    source_upper_bound_allowed: bool
    source_rank: int
    line_of_sight_phase_coherent: bool
    visibility_width: float
    collision_gap_status: str
    kernel_floor_status: str
    mask_support_status: str
    kill_switches: tuple[str, ...]
    owner: str = "BASS"
    implementation_scope: str = "bass_py"
    claim_tier: str = "diagnostic_only"
    transfer_source: str = "none"
    production_claim_allowed: bool = False
    native_solver_result: bool = False
    family_identification: bool = False
    caveats: tuple[str, ...] = field(default_factory=lambda: (DEFAULT_VISIBILITY_CAVEAT,))

    def as_payload(self) -> dict[str, Any]:
        return {
            "theorem_id": self.theorem_id,
            "no_go_status": self.no_go_status,
            "source_upper_bound_allowed": self.source_upper_bound_allowed,
            "source_rank": self.source_rank,
            "line_of_sight_phase_coherent": self.line_of_sight_phase_coherent,
            "visibility_width": self.visibility_width,
            "collision_gap_status": self.collision_gap_status,
            "kernel_floor_status": self.kernel_floor_status,
            "mask_support_status": self.mask_support_status,
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


def visibility_cancellation_no_go(
    *,
    source_rank: int,
    line_of_sight_phase_coherent: bool,
    visibility_width: float,
    theorem_id: str,
    collision_gap_status: str = "not_bound",
    kernel_floor_status: str = "not_bound",
    mask_support_status: str = "not_bound",
) -> VisibilityCancellationNoGo:
    if not isinstance(source_rank, int):
        raise ValueError("source_rank must be an integer")
    width = float(visibility_width)
    if not math.isfinite(width) or width <= 0.0:
        raise ValueError("visibility_width must be positive finite")
    if source_rank <= 0:
        return VisibilityCancellationNoGo(
            theorem_id=theorem_id,
            no_go_status="blocked_source_rank_near_zero",
            source_upper_bound_allowed=False,
            source_rank=source_rank,
            line_of_sight_phase_coherent=bool(line_of_sight_phase_coherent),
            visibility_width=width,
            collision_gap_status=collision_gap_status,
            kernel_floor_status=kernel_floor_status,
            mask_support_status=mask_support_status,
            kill_switches=("source_rank_near_zero_blocks_inverse_source_claim",),
        )
    if not line_of_sight_phase_coherent:
        return VisibilityCancellationNoGo(
            theorem_id=theorem_id,
            no_go_status="blocked_line_of_sight_sign_phase_incoherence",
            source_upper_bound_allowed=False,
            source_rank=source_rank,
            line_of_sight_phase_coherent=False,
            visibility_width=width,
            collision_gap_status=collision_gap_status,
            kernel_floor_status=kernel_floor_status,
            mask_support_status=mask_support_status,
            kill_switches=("line_of_sight_sign_phase_incoherence_blocks_source_upper_bound",),
        )
    provenance_ready = (
        collision_gap_status == "positive_bound"
        and kernel_floor_status == "positive_bound"
        and mask_support_status == "bound"
    )
    if not provenance_ready:
        return VisibilityCancellationNoGo(
            theorem_id=theorem_id,
            no_go_status="blocked_visibility_provenance_not_bound",
            source_upper_bound_allowed=False,
            source_rank=source_rank,
            line_of_sight_phase_coherent=True,
            visibility_width=width,
            collision_gap_status=collision_gap_status,
            kernel_floor_status=kernel_floor_status,
            mask_support_status=mask_support_status,
            kill_switches=("visibility_gap_kernel_mask_not_bound_blocks_source_upper_bound",),
        )
    return VisibilityCancellationNoGo(
        theorem_id=theorem_id,
        no_go_status="synthetic_visibility_cancellation_no_go",
        source_upper_bound_allowed=True,
        source_rank=source_rank,
        line_of_sight_phase_coherent=True,
        visibility_width=width,
        collision_gap_status=collision_gap_status,
        kernel_floor_status=kernel_floor_status,
        mask_support_status=mask_support_status,
        kill_switches=(),
    )
