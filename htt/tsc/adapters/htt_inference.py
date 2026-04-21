"""HTT-facing caveat adapter for TSC overlays."""
from __future__ import annotations

from dataclasses import dataclass

from common.contracts import TscAdequacyOverlay


@dataclass(frozen=True)
class HttTscCaveatBundle:
    caveats: tuple[str, ...]
    channel_validity: dict[str, str]
    channel_claim_ceiling: dict[str, str]
    channel_labels: dict[str, tuple[str, ...]]
    scalar_only_discrimination_insufficient: bool
    tsc_overlay_ref: str | None = None


def overlay_to_htt_caveats(
    overlay: TscAdequacyOverlay,
    *,
    uses_scalar_only_geometry: bool = False,
    overlay_ref: str | None = None,
) -> HttTscCaveatBundle:
    caveats = list(overlay.quarantine_reasons)
    if overlay.domain_report.status == "invalid_domain":
        caveats.append("tsc_invalid_domain")
    if uses_scalar_only_geometry:
        caveats.append("scalar_only_discrimination_insufficient")
    channel_validity = {
        budget.channel: budget.propagation_status for budget in overlay.channel_budgets
    }
    channel_claim_ceiling = {
        budget.channel: budget.claim_ceiling for budget in overlay.channel_budgets
    }
    channel_labels = {
        budget.channel: tuple(budget.labels) for budget in overlay.channel_budgets
    }
    return HttTscCaveatBundle(
        caveats=tuple(caveats),
        channel_validity=channel_validity,
        channel_claim_ceiling=channel_claim_ceiling,
        channel_labels=channel_labels,
        scalar_only_discrimination_insufficient=uses_scalar_only_geometry,
        tsc_overlay_ref=overlay_ref,
    )


__all__ = ["HttTscCaveatBundle", "overlay_to_htt_caveats"]
