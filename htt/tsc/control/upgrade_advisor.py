"""Skeleton chart-upgrade advisor for VER2 TSC service."""
from __future__ import annotations

from dataclasses import dataclass

from common.contracts import (
    TscDomainReport,
    TscResidualReport,
    TscSourceBridgeReport,
    TscUpgradeRecommendation,
)


@dataclass(frozen=True)
class UpgradeAdvisorConfig:
    eta_tangent_fraction_warn: float = 0.5
    residual_block_floor: float = 1.0
    full_resolved_threshold: float = 2.0
    dwell_steps: int = 2


def recommend_chart_transition(
    domain_report: TscDomainReport,
    residual_report: TscResidualReport,
    source_report: TscSourceBridgeReport | None,
    config: UpgradeAdvisorConfig | None = None,
) -> TscUpgradeRecommendation:
    config = config or UpgradeAdvisorConfig()
    if domain_report.status == "invalid_domain":
        return TscUpgradeRecommendation(
            current_chart=domain_report.chart,
            recommended_chart=domain_report.chart,
            reason="invalid_domain",
            severity="block",
            dwell_time_required=float(config.dwell_steps),
            hysteresis_state="hold",
            labels=("source_invalid_domain__blocked",),
            manifest=domain_report.manifest,
        )

    eta_fraction = residual_report.eta_tangent_fraction or 0.0
    if eta_fraction >= config.eta_tangent_fraction_warn and domain_report.chart == "one_field":
        return TscUpgradeRecommendation(
            current_chart=domain_report.chart,
            recommended_chart="two_field",
            reason="eta_tangent_false_trigger",
            severity="warn",
            dwell_time_required=float(config.dwell_steps),
            hysteresis_state="pending_upgrade",
            labels=("two_field_recommended__one_field_warn",),
            manifest=domain_report.manifest,
        )

    max_residual = max(
        float(residual_report.onefield_residual or 0.0),
        float(residual_report.twofield_residual or 0.0),
        float(residual_report.high_residual or 0.0),
    )
    if max_residual >= config.full_resolved_threshold or residual_report.residual_origin in {"spin2", "high"}:
        reason = "spin2_required" if residual_report.residual_origin == "spin2" else "high_residual_required"
        return TscUpgradeRecommendation(
            current_chart=domain_report.chart,
            recommended_chart="full_resolved_trace",
            reason=reason,  # type: ignore[arg-type]
            severity="block" if max_residual >= config.residual_block_floor else "warn",
            dwell_time_required=float(config.dwell_steps),
            hysteresis_state="upgrade_required",
            labels=("full_resolved_trace_required",),
            manifest=domain_report.manifest,
        )

    if source_report is not None and source_report.source_status == "pending":
        return TscUpgradeRecommendation(
            current_chart=domain_report.chart,
            recommended_chart=domain_report.chart,
            reason="source_error_bound_exceeded",
            severity="warn",
            dwell_time_required=float(config.dwell_steps),
            hysteresis_state="monitor",
            labels=("source_adequate__propagation_pending",),
            manifest=domain_report.manifest,
        )

    return TscUpgradeRecommendation(
        current_chart=domain_report.chart,
        recommended_chart=domain_report.chart,
        reason="stable_no_upgrade",
        severity="info",
        dwell_time_required=None,
        hysteresis_state="stable",
        labels=("stable_no_upgrade",),
        manifest=domain_report.manifest,
    )


def apply_hysteresis(previous_state: str | None, current_signal: str, config: UpgradeAdvisorConfig | None = None) -> str:
    del config
    if previous_state == current_signal:
        return current_signal
    if previous_state in {None, "stable"}:
        return current_signal
    return f"{previous_state}->{current_signal}"


__all__ = ["UpgradeAdvisorConfig", "apply_hysteresis", "recommend_chart_transition"]
