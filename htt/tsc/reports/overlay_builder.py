"""Single-entrypoint TSC overlay builder for the skeleton phase."""
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


def build_public_caveat_snippet(
    domain_report: TscDomainReport,
    source_report: TscSourceBridgeReport | None,
    channel_budgets: Sequence[TscChannelAdequacyBudget],
) -> str:
    if domain_report.status == "invalid_domain":
        return "TSC domain invalid: chart use must remain diagnostic-only until domain blockers are resolved."
    if source_report is None:
        return "TSC source bridge not attached; artifact must declare TSC-not-applicable or stay caveated."
    if any(budget.propagation_status == "pending" for budget in channel_budgets):
        return "TSC source-side checks are available, but propagation validation is still pending."
    if any(budget.channel == "BB" and budget.propagation_status != "validated" for budget in channel_budgets):
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
    texts = [public_snippet] if public_snippet else []
    flags = build_no_overclaim_flags(texts=texts, metadata=artifact_metadata)
    quarantine = quarantine_reasons_from_flags(flags)
    snippet = public_snippet or build_public_caveat_snippet(
        domain_report, source_bridge_report, channel_budgets
    )
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
