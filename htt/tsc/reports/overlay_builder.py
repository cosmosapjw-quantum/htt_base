"""Single-entrypoint TSC overlay builder for the active-service phase."""
from __future__ import annotations

from collections.abc import Mapping, Sequence

from common.contracts import (
    ArtifactManifest,
    TscAdequacyOverlay,
    TscChannelAdequacyBudget,
    TscDomainReport,
    TscResidualReport,
    TscSourceBridgeReport,
    TscUpgradeRecommendation,
)
from tsc.audit.no_overclaim import build_no_overclaim_flags, quarantine_reasons_from_flags
from tsc.contracts import validate_tsc_service_labels


def _validate_overlay_components(
    *,
    source_report: TscSourceBridgeReport | None,
    channel_budgets: Sequence[TscChannelAdequacyBudget],
    upgrade_recommendation: TscUpgradeRecommendation,
) -> None:
    if source_report is not None:
        validate_tsc_service_labels(source_report.labels)
    for budget in channel_budgets:
        validate_tsc_service_labels(budget.labels)
    validate_tsc_service_labels(upgrade_recommendation.labels)


def build_public_caveat_snippet(
    domain_report: TscDomainReport,
    source_report: TscSourceBridgeReport | None,
    channel_budgets: Sequence[TscChannelAdequacyBudget],
) -> str:
    pending_channels = tuple(
        budget.channel for budget in channel_budgets if budget.propagation_status == "pending"
    )
    blocked_channels = tuple(
        budget.channel for budget in channel_budgets if budget.propagation_status == "blocked"
    )
    bb_trace_only = "BB" in blocked_channels
    if domain_report.status == "invalid_domain":
        return "TSC domain invalid: chart use must remain diagnostic-only until domain blockers are resolved."
    if source_report is None:
        return "TSC source bridge not attached; artifact must declare TSC-not-applicable or stay caveated."
    if source_report.source_status == "inadequate":
        return "TSC trace-source adequacy is insufficient; artifact must remain diagnostic-only until source-side blockers are reduced."
    if source_report.source_status == "pending":
        pending_text = ", ".join(pending_channels) if pending_channels else "TT, TE, EE"
        suffix = " BB remains outside trace-only validation." if bb_trace_only else ""
        return (
            "TSC trace-source bridge is provisional; propagation validation is still pending for "
            f"{pending_text}.{suffix}"
        )
    if pending_channels:
        pending_text = ", ".join(pending_channels)
        suffix = " BB remains outside trace-only validation." if bb_trace_only else ""
        return (
            "TSC source-side checks are available, but propagation validation is still pending for "
            f"{pending_text}.{suffix}"
        )
    if bb_trace_only:
        return "TSC trace semantics do not validate BB; spin-2/high propagation remains required."
    return "TSC overlay attached with source/domain coverage and no runtime-decision ownership."


def build_tsc_overlay(
    *,
    domain_report: TscDomainReport,
    residual_report: TscResidualReport,
    source_bridge_report: TscSourceBridgeReport | None,
    channel_budgets: Sequence[TscChannelAdequacyBudget],
    upgrade_recommendation: TscUpgradeRecommendation,
    artifact_manifest: ArtifactManifest,
    artifact_metadata: Mapping[str, object] | None = None,
    public_snippet: str | None = None,
) -> TscAdequacyOverlay:
    _validate_overlay_components(
        source_report=source_bridge_report,
        channel_budgets=channel_budgets,
        upgrade_recommendation=upgrade_recommendation,
    )
    snippet = public_snippet or build_public_caveat_snippet(
        domain_report, source_bridge_report, channel_budgets
    )
    texts = (snippet,)
    flags = build_no_overclaim_flags(texts=texts, metadata=artifact_metadata)
    quarantine = tuple(dict.fromkeys(quarantine_reasons_from_flags(flags)))
    return TscAdequacyOverlay(
        domain_report=domain_report,
        residual_report=residual_report,
        source_bridge_report=source_bridge_report,
        channel_budgets=tuple(channel_budgets),
        upgrade_recommendation=upgrade_recommendation,
        no_overclaim_flags=flags,
        quarantine_reasons=quarantine,
        public_caveat_snippet=snippet,
        manifest=artifact_manifest,
    )


__all__ = ["build_public_caveat_snippet", "build_tsc_overlay"]
