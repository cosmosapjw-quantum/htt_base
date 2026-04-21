"""Skeleton chart-upgrade advisor for VER2 TSC service."""
from __future__ import annotations

from dataclasses import dataclass

from common.contracts import (
    TscDomainReport,
    TscResidualReport,
    TscSourceBridgeReport,
    TscUpgradeRecommendation,
)
from tsc.contracts import validate_tsc_service_labels


@dataclass(frozen=True)
class UpgradeAdvisorConfig:
    eta_tangent_fraction_warn: float = 0.5
    residual_block_floor: float = 1.0
    full_resolved_threshold: float = 2.0
    dwell_steps: int = 2


def _recommendation(
    *,
    domain_report: TscDomainReport,
    recommended_chart: str,
    reason: str,
    severity: str,
    dwell_time_required: float | None,
    hysteresis_state: str | None,
    labels: tuple[str, ...],
) -> TscUpgradeRecommendation:
    return TscUpgradeRecommendation(
        current_chart=domain_report.chart,
        recommended_chart=recommended_chart,  # type: ignore[arg-type]
        reason=reason,  # type: ignore[arg-type]
        severity=severity,  # type: ignore[arg-type]
        dwell_time_required=dwell_time_required,
        hysteresis_state=hysteresis_state,
        labels=validate_tsc_service_labels(labels),
        manifest=domain_report.manifest,
    )


def recommend_chart_transition(
    domain_report: TscDomainReport,
    residual_report: TscResidualReport,
    source_report: TscSourceBridgeReport | None,
    config: UpgradeAdvisorConfig | None = None,
) -> TscUpgradeRecommendation:
    config = config or UpgradeAdvisorConfig()
    if domain_report.status == "invalid_domain":
        return _recommendation(
            domain_report=domain_report,
            recommended_chart=domain_report.chart,
            reason="invalid_domain",
            severity="block",
            dwell_time_required=float(config.dwell_steps),
            hysteresis_state="hold",
            labels=("source_invalid_domain__blocked",),
        )

    eta_fraction = residual_report.eta_tangent_fraction or 0.0
    if eta_fraction >= config.eta_tangent_fraction_warn and domain_report.chart == "one_field":
        return _recommendation(
            domain_report=domain_report,
            recommended_chart="two_field",
            reason="eta_tangent_false_trigger",
            severity="warn",
            dwell_time_required=float(config.dwell_steps),
            hysteresis_state="pending_upgrade",
            labels=("two_field_recommended__one_field_warn",),
        )

    max_residual = max(
        float(residual_report.onefield_residual or 0.0),
        float(residual_report.twofield_residual or 0.0),
        float(residual_report.high_residual or 0.0),
    )
    if max_residual >= config.full_resolved_threshold or residual_report.residual_origin in {"spin2", "high"}:
        reason = "spin2_required" if residual_report.residual_origin == "spin2" else "high_residual_required"
        return _recommendation(
            domain_report=domain_report,
            recommended_chart="full_resolved_trace",
            reason=reason,  # type: ignore[arg-type]
            severity="block" if max_residual >= config.residual_block_floor else "warn",
            dwell_time_required=float(config.dwell_steps),
            hysteresis_state="upgrade_required",
            labels=("full_resolved_trace_required",),
        )

    if source_report is not None and source_report.source_status == "inadequate":
        return _recommendation(
            domain_report=domain_report,
            recommended_chart=domain_report.chart,
            reason="source_error_bound_exceeded",
            severity="warn",
            dwell_time_required=float(config.dwell_steps),
            hysteresis_state="monitor",
            labels=("source_inadequate__propagation_not_evaluated",),
        )

    if source_report is not None and source_report.source_status == "pending":
        return _recommendation(
            domain_report=domain_report,
            recommended_chart=domain_report.chart,
            reason="source_error_bound_exceeded",
            severity="warn",
            dwell_time_required=float(config.dwell_steps),
            hysteresis_state="monitor",
            labels=("source_bridge_bound_pending",),
        )

    return _recommendation(
        domain_report=domain_report,
        recommended_chart=domain_report.chart,
        reason="stable_no_upgrade",
        severity="info",
        dwell_time_required=None,
        hysteresis_state="stable",
        labels=("stable_no_upgrade",),
    )


def apply_hysteresis(previous_state: str | None, current_signal: str, config: UpgradeAdvisorConfig | None = None) -> str:
    del config
    if previous_state == current_signal:
        return current_signal
    if previous_state in {None, "stable"}:
        return current_signal
    return f"{previous_state}->{current_signal}"


__all__ = ["UpgradeAdvisorConfig", "apply_hysteresis", "recommend_chart_transition"]
