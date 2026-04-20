"""BASS-facing TSC adapter that preserves BASS decision ownership."""
from __future__ import annotations

from dataclasses import dataclass

from common.contracts import TscAdequacyOverlay


@dataclass(frozen=True)
class SourceAdequacySuggestion:
    """Advisory handoff from TSC to BASS.

    Intentionally excludes any final `allow_reduction` field.
    """

    source_status: str
    domain_status: str
    recommended_label: str
    quarantine_reasons: tuple[str, ...]
    tsc_overlay_ref: str | None = None


def overlay_to_bass_suggestion(
    overlay: TscAdequacyOverlay,
    *,
    overlay_ref: str | None = None,
) -> SourceAdequacySuggestion:
    if overlay.domain_report.status == "invalid_domain":
        label = "source_invalid_domain__blocked"
    elif any(b.propagation_status == "pending" for b in overlay.channel_budgets):
        label = "source_adequate__propagation_pending"
    else:
        label = "source_adequate__propagation_validated"
    source_status = (
        "adequate"
        if overlay.source_bridge_report is not None and overlay.source_bridge_report.source_status == "adequate"
        else "pending"
    )
    return SourceAdequacySuggestion(
        source_status=source_status,
        domain_status=overlay.domain_report.status,
        recommended_label=label,
        quarantine_reasons=overlay.quarantine_reasons,
        tsc_overlay_ref=overlay_ref,
    )


__all__ = ["SourceAdequacySuggestion", "overlay_to_bass_suggestion"]
