"""MIO-facing adequacy fields derived from TSC overlays."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from common.contracts import TscAdequacyOverlay
from tsc.reports.json_export import overlay_publication_blockers


_DEFAULT_REQUIRED_CHANNELS = ("TT", "TE", "EE")


@dataclass(frozen=True)
class MioTscAdequacyFields:
    source_caveats: tuple[str, ...]
    channel_responsibility: dict[str, str]
    channel_claim_ceiling: dict[str, str]
    tsc_domain_status: str
    tsc_upgrade_hint: str | None
    trace_source_adequacy: str
    required_channels: tuple[str, ...]
    propagation_status_required: tuple[str, ...]
    publication_blockers: tuple[str, ...]
    diagnostic_only: bool


def overlay_to_mio_fields(
    overlay: TscAdequacyOverlay,
    *,
    required_channels: Sequence[str] = _DEFAULT_REQUIRED_CHANNELS,
) -> MioTscAdequacyFields:
    channel_claim_ceiling = {
        budget.channel: budget.claim_ceiling for budget in overlay.channel_budgets
    }
    required_set = set(required_channels)
    required = tuple(
        sorted(
            {
                budget.channel
                for budget in overlay.channel_budgets
                if budget.channel in required_set
                if budget.propagation_status != "validated"
            }
        )
    )
    publication_blockers = overlay_publication_blockers(
        overlay,
        required_channels=required_channels,
    )
    return MioTscAdequacyFields(
        source_caveats=overlay.quarantine_reasons,
        channel_responsibility={
            budget.channel: "/".join(budget.labels) if budget.labels else "unspecified"
            for budget in overlay.channel_budgets
        },
        channel_claim_ceiling=channel_claim_ceiling,
        tsc_domain_status=overlay.domain_report.status,
        tsc_upgrade_hint=overlay.upgrade_recommendation.reason,
        trace_source_adequacy=(
            overlay.source_bridge_report.source_status
            if overlay.source_bridge_report is not None
            else "pending"
        ),
        required_channels=tuple(required_channels),
        propagation_status_required=required,
        publication_blockers=publication_blockers,
        diagnostic_only=bool(publication_blockers),
    )


__all__ = ["MioTscAdequacyFields", "overlay_to_mio_fields"]
