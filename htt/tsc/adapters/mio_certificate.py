"""MIO-facing adequacy fields derived from TSC overlays."""
from __future__ import annotations

from dataclasses import dataclass

from common.contracts import TscAdequacyOverlay


@dataclass(frozen=True)
class MioTscAdequacyFields:
    source_caveats: tuple[str, ...]
    channel_responsibility: dict[str, str]
    channel_claim_ceiling: dict[str, str]
    tsc_domain_status: str
    tsc_upgrade_hint: str | None
    trace_source_adequacy: str
    propagation_status_required: tuple[str, ...]
    diagnostic_only: bool


def overlay_to_mio_fields(overlay: TscAdequacyOverlay) -> MioTscAdequacyFields:
    channel_claim_ceiling = {
        budget.channel: budget.claim_ceiling for budget in overlay.channel_budgets
    }
    required = tuple(
        sorted(
            {
                budget.channel
                for budget in overlay.channel_budgets
                if budget.propagation_status != "validated"
            }
        )
    )
    limited_claim_channels = tuple(
        sorted(
            budget.channel
            for budget in overlay.channel_budgets
            if budget.channel in {"TT", "EE", "TE", "scalar_summary"}
            and budget.claim_ceiling not in {"conditional", "validated"}
        )
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
        propagation_status_required=required,
        diagnostic_only=bool(
            required or overlay.quarantine_reasons or limited_claim_channels
        ),
    )


__all__ = ["MioTscAdequacyFields", "overlay_to_mio_fields"]
