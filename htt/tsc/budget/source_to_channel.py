"""Source-to-channel adequacy budgets for the VER2 TSC service."""
from __future__ import annotations

from collections.abc import Mapping

from common.contracts import ArtifactManifest, TscChannelAdequacyBudget
from common.contracts import TscDomainReport, TscResidualReport, TscSourceBridgeReport
from tsc.contracts import CHANNEL_DEFAULT_CLAIM_CEILINGS, validate_tsc_service_labels
from tsc.residuals.observable_bridge import (
    TscResidualBridgeReport,
    build_residual_bridge_from_reports,
)


def source_to_field_prebudget(
    source_error_bound: float | None,
    propagator_norm_bound: float | None = None,
    *,
    amplification_bound: float | None = None,
) -> float | None:
    if source_error_bound is None:
        return None
    if propagator_norm_bound is None:
        return None
    amplification = 1.0 if amplification_bound is None else abs(amplification_bound)
    return float(
        abs(source_error_bound) * abs(propagator_norm_bound) * amplification
    )


def _status_labels(
    *,
    channel: str,
    source_status: str,
    propagation_status: str,
    residual_bridge_report: TscResidualBridgeReport | None = None,
) -> tuple[str, ...]:
    if channel == "BB":
        return validate_tsc_service_labels(("trace_only__bb_claim_forbidden",))

    labels: list[str] = []
    if propagation_status == "blocked" and source_status != "adequate":
        labels.append("source_invalid_domain__blocked")
    elif source_status == "adequate" and propagation_status == "validated":
        labels.append("source_adequate__propagation_validated")
    elif source_status == "adequate":
        labels.append("source_adequate__propagation_pending")
    else:
        labels.append("source_inadequate__propagation_not_evaluated")

    if channel in {"EE", "TE"}:
        labels.append("trace_ok__spin2_required")
    if channel == "TE":
        labels.append("te_mixed_channel_requires_spin2")
    if channel == "BiPoSH":
        labels.append("biposh_requires_external_validation")
    if channel == "template":
        labels.append("template_family_claim_blocked")
    if channel in {"TT", "scalar_summary"}:
        if residual_bridge_report is None:
            labels.append("observable_bridge_missing_state_residual")
        elif residual_bridge_report.bridge_status in {
            "conditional_state_bound",
            "validated_dynamical_bridge",
        }:
            labels.append("observable_bridge_conditional")
        elif residual_bridge_report.bridge_status == "blocked_collision_state_mismatch":
            labels.append("observable_bridge_blocked_collision_state_mismatch")
        elif residual_bridge_report.bridge_status == "blocked_missing_state_residual":
            labels.append("observable_bridge_missing_state_residual")
            if channel == "scalar_summary":
                labels.append("scalar_summary_requires_state_residual")
        elif residual_bridge_report.bridge_status in {
            "blocked_jacobian_conditioning",
            "blocked_invalid_domain",
        }:
            labels.append("observable_bridge_blocked_jacobian_conditioning")
    return validate_tsc_service_labels(labels)


def _claim_ceiling(
    *,
    channel: str,
    source_status: str,
    propagation_status: str,
    residual_bridge_report: TscResidualBridgeReport | None = None,
) -> str:
    if channel in {"BB", "TB", "EB", "template"}:
        return "blocked"
    if channel == "BiPoSH":
        return "exploratory"
    if source_status != "adequate":
        return "exploratory"
    if channel in {"EE", "TE"}:
        return "conditional" if propagation_status == "validated" else "exploratory"
    if channel in {"TT", "scalar_summary"}:
        if residual_bridge_report is None:
            return "exploratory"
        if residual_bridge_report.bridge_status in {
            "conditional_state_bound",
            "validated_dynamical_bridge",
        }:
            return "conditional"
        return "exploratory"
    return CHANNEL_DEFAULT_CLAIM_CEILINGS[channel]


def _base_budget(
    *,
    channel: str,
    manifest: ArtifactManifest,
    trace_budget: float | None,
    spin2_budget: float | None,
    high_budget: float | None,
    source_to_field_bound: float | None,
    spectrum_bound_linear: float | None,
    spectrum_bound_quadratic: float | None,
    source_status: str,
    propagation_status: str,
    labels: tuple[str, ...],
    residual_bridge_report: TscResidualBridgeReport | None = None,
) -> TscChannelAdequacyBudget:
    return TscChannelAdequacyBudget(
        channel=channel,  # type: ignore[arg-type]
        trace_budget=trace_budget,
        spin2_budget=spin2_budget,
        high_budget=high_budget,
        source_to_field_bound=source_to_field_bound,
        spectrum_bound_linear=spectrum_bound_linear,
        spectrum_bound_quadratic=spectrum_bound_quadratic,
        source_status=source_status,  # type: ignore[arg-type]
        propagation_status=propagation_status,  # type: ignore[arg-type]
        claim_ceiling=_claim_ceiling(
            channel=channel,
            source_status=source_status,
            propagation_status=propagation_status,
            residual_bridge_report=residual_bridge_report,
        ),  # type: ignore[arg-type]
        labels=labels,
        manifest=manifest,
    )


def channel_budget_TT(
    *,
    manifest: ArtifactManifest,
    trace_budget: float | None,
    source_status: str,
    propagation_status: str = "validated",
    source_to_field_bound: float | None = None,
    residual_bridge_report: TscResidualBridgeReport | None = None,
) -> TscChannelAdequacyBudget:
    return _base_budget(
        channel="TT",
        manifest=manifest,
        trace_budget=trace_budget,
        spin2_budget=None,
        high_budget=None,
        source_to_field_bound=source_to_field_bound,
        spectrum_bound_linear=(
            source_to_field_bound if propagation_status == "validated" else None
        ),
        spectrum_bound_quadratic=None,
        source_status=source_status,
        propagation_status=propagation_status,
        labels=_status_labels(
            channel="TT",
            source_status=source_status,
            propagation_status=propagation_status,
            residual_bridge_report=residual_bridge_report,
        ),
        residual_bridge_report=residual_bridge_report,
    )


def channel_budget_EE(
    *,
    manifest: ArtifactManifest,
    trace_budget: float | None,
    spin2_budget: float | None,
    source_status: str,
    propagation_status: str = "pending",
    source_to_field_bound: float | None = None,
    residual_bridge_report: TscResidualBridgeReport | None = None,
) -> TscChannelAdequacyBudget:
    return _base_budget(
        channel="EE",
        manifest=manifest,
        trace_budget=trace_budget,
        spin2_budget=spin2_budget,
        high_budget=None,
        source_to_field_bound=source_to_field_bound,
        spectrum_bound_linear=(
            source_to_field_bound if propagation_status == "validated" else None
        ),
        spectrum_bound_quadratic=(
            spin2_budget if propagation_status == "validated" else None
        ),
        source_status=source_status,
        propagation_status=propagation_status,
        labels=_status_labels(
            channel="EE",
            source_status=source_status,
            propagation_status=propagation_status,
            residual_bridge_report=residual_bridge_report,
        ),
        residual_bridge_report=residual_bridge_report,
    )


def channel_budget_TE(
    *,
    manifest: ArtifactManifest,
    trace_budget: float | None,
    spin2_budget: float | None,
    source_status: str,
    propagation_status: str = "pending",
    source_to_field_bound: float | None = None,
    residual_bridge_report: TscResidualBridgeReport | None = None,
) -> TscChannelAdequacyBudget:
    return _base_budget(
        channel="TE",
        manifest=manifest,
        trace_budget=trace_budget,
        spin2_budget=spin2_budget,
        high_budget=None,
        source_to_field_bound=source_to_field_bound,
        spectrum_bound_linear=(
            source_to_field_bound if propagation_status == "validated" else None
        ),
        spectrum_bound_quadratic=(
            spin2_budget if propagation_status == "validated" else None
        ),
        source_status=source_status,
        propagation_status=propagation_status,
        labels=_status_labels(
            channel="TE",
            source_status=source_status,
            propagation_status=propagation_status,
            residual_bridge_report=residual_bridge_report,
        ),
        residual_bridge_report=residual_bridge_report,
    )


def channel_budget_BB(
    *,
    manifest: ArtifactManifest,
    source_status: str,
    propagation_status: str = "blocked",
    high_budget: float | None = None,
    residual_bridge_report: TscResidualBridgeReport | None = None,
) -> TscChannelAdequacyBudget:
    return _base_budget(
        channel="BB",
        manifest=manifest,
        trace_budget=None,
        spin2_budget=None,
        high_budget=high_budget,
        source_to_field_bound=None,
        spectrum_bound_linear=None,
        spectrum_bound_quadratic=None,
        source_status=source_status,
        propagation_status=propagation_status,
        labels=_status_labels(
            channel="BB",
            source_status=source_status,
            propagation_status=propagation_status,
            residual_bridge_report=residual_bridge_report,
        ),
        residual_bridge_report=residual_bridge_report,
    )


def channel_budget_BiPoSH(
    *,
    manifest: ArtifactManifest,
    trace_budget: float | None,
    spin2_budget: float | None,
    high_budget: float | None,
    source_status: str,
    propagation_status: str = "pending",
    source_to_field_bound: float | None = None,
) -> TscChannelAdequacyBudget:
    return _base_budget(
        channel="BiPoSH",
        manifest=manifest,
        trace_budget=trace_budget,
        spin2_budget=spin2_budget,
        high_budget=high_budget,
        source_to_field_bound=source_to_field_bound,
        spectrum_bound_linear=None,
        spectrum_bound_quadratic=None,
        source_status=source_status,
        propagation_status=propagation_status,
        labels=_status_labels(
            channel="BiPoSH",
            source_status=source_status,
            propagation_status=propagation_status,
        ),
    )


def channel_budget_template(
    *,
    manifest: ArtifactManifest,
    trace_budget: float | None,
    spin2_budget: float | None,
    source_status: str,
    propagation_status: str = "blocked",
    source_to_field_bound: float | None = None,
) -> TscChannelAdequacyBudget:
    return _base_budget(
        channel="template",
        manifest=manifest,
        trace_budget=trace_budget,
        spin2_budget=spin2_budget,
        high_budget=None,
        source_to_field_bound=source_to_field_bound,
        spectrum_bound_linear=None,
        spectrum_bound_quadratic=None,
        source_status=source_status,
        propagation_status=propagation_status,
        labels=_status_labels(
            channel="template",
            source_status=source_status,
            propagation_status=propagation_status,
        ),
    )


def channel_budget_scalar_summary(
    *,
    manifest: ArtifactManifest,
    trace_budget: float | None,
    source_status: str,
    propagation_status: str = "validated",
    source_to_field_bound: float | None = None,
    residual_bridge_report: TscResidualBridgeReport | None = None,
) -> TscChannelAdequacyBudget:
    return _base_budget(
        channel="scalar_summary",
        manifest=manifest,
        trace_budget=trace_budget,
        spin2_budget=None,
        high_budget=None,
        source_to_field_bound=source_to_field_bound,
        spectrum_bound_linear=(
            source_to_field_bound
            if propagation_status == "validated" and residual_bridge_report is not None
            else None
        ),
        spectrum_bound_quadratic=None,
        source_status=source_status,
        propagation_status=propagation_status,
        labels=_status_labels(
            channel="scalar_summary",
            source_status=source_status,
            propagation_status=propagation_status,
            residual_bridge_report=residual_bridge_report,
        ),
        residual_bridge_report=residual_bridge_report,
    )


def build_channel_budgets(
    *,
    manifest: ArtifactManifest,
    source_status: str,
    propagation_status: str = "pending",
    trace_budget: float | None = None,
    spin2_budget: float | None = None,
    high_budget: float | None = None,
    source_error_bound: float | None = None,
    propagator_norm_bound: float | None = None,
    amplification_bound: float | None = None,
    propagation_status_by_channel: Mapping[str, str] | None = None,
    residual_bridge_report: TscResidualBridgeReport | None = None,
    include_extended_channels: bool = False,
) -> tuple[TscChannelAdequacyBudget, ...]:
    source_budget = trace_budget if trace_budget is not None else source_error_bound
    field_prebudget = source_to_field_prebudget(
        source_budget,
        propagator_norm_bound,
        amplification_bound=amplification_bound,
    )
    status_map = {
        "TT": "validated" if propagation_status == "validated" else "pending",
        "EE": propagation_status,
        "TE": propagation_status,
        "BB": "blocked" if propagation_status != "validated" else "validated",
    }
    if propagation_status_by_channel is not None:
        for channel, status in propagation_status_by_channel.items():
            status_map[str(channel)] = str(status)
    budgets: list[TscChannelAdequacyBudget] = [
        channel_budget_TT(
            manifest=manifest,
            trace_budget=source_budget,
            source_status=source_status,
            propagation_status=status_map["TT"],
            source_to_field_bound=field_prebudget,
            residual_bridge_report=residual_bridge_report,
        ),
        channel_budget_EE(
            manifest=manifest,
            trace_budget=source_budget,
            spin2_budget=spin2_budget,
            source_status=source_status,
            propagation_status=status_map["EE"],
            source_to_field_bound=field_prebudget,
            residual_bridge_report=residual_bridge_report,
        ),
        channel_budget_TE(
            manifest=manifest,
            trace_budget=source_budget,
            spin2_budget=spin2_budget,
            source_status=source_status,
            propagation_status=status_map["TE"],
            source_to_field_bound=field_prebudget,
            residual_bridge_report=residual_bridge_report,
        ),
        channel_budget_BB(
            manifest=manifest,
            source_status=source_status,
            propagation_status=status_map["BB"],
            high_budget=high_budget,
            residual_bridge_report=residual_bridge_report,
        ),
    ]
    if include_extended_channels:
        budgets.extend(
            (
                channel_budget_BiPoSH(
                    manifest=manifest,
                    trace_budget=source_budget,
                    spin2_budget=spin2_budget,
                    high_budget=high_budget,
                    source_status=source_status,
                    propagation_status=status_map.get("BiPoSH", "pending"),
                    source_to_field_bound=field_prebudget,
                ),
                channel_budget_template(
                    manifest=manifest,
                    trace_budget=source_budget,
                    spin2_budget=spin2_budget,
                    source_status=source_status,
                    propagation_status=status_map.get("template", "blocked"),
                    source_to_field_bound=field_prebudget,
                ),
                channel_budget_scalar_summary(
                    manifest=manifest,
                    trace_budget=source_budget,
                    source_status=source_status,
                    propagation_status=status_map.get("scalar_summary", status_map["TT"]),
                    source_to_field_bound=field_prebudget,
                    residual_bridge_report=residual_bridge_report,
                ),
            )
        )
    return tuple(budgets)


def build_channel_budgets_from_reports(
    *,
    manifest: ArtifactManifest,
    domain_report: TscDomainReport,
    residual_report: TscResidualReport,
    source_report: TscSourceBridgeReport | None,
    propagator_norm_bound: float | None = None,
    amplification_bound: float | None = None,
    propagation_status_by_channel: Mapping[str, str] | None = None,
    residual_bridge_report: TscResidualBridgeReport | None = None,
    include_extended_channels: bool = False,
) -> tuple[TscChannelAdequacyBudget, ...]:
    """Build channel budgets from active-service reports without taking propagation ownership."""
    source_status = "pending" if source_report is None else str(source_report.source_status)
    if domain_report.status == "invalid_domain":
        status_map = {"TT": "blocked", "EE": "blocked", "TE": "blocked", "BB": "blocked"}
    else:
        status_map = {
            "TT": "validated" if source_status == "adequate" else "pending",
            "EE": "pending",
            "TE": "pending",
            "BB": "blocked",
        }
        if propagation_status_by_channel is not None:
            status_map.update({str(key): str(value) for key, value in propagation_status_by_channel.items()})
    bridge = residual_bridge_report or build_residual_bridge_from_reports(
        domain_report=domain_report,
        residual_report=residual_report,
    )
    return build_channel_budgets(
        manifest=manifest,
        source_status=source_status,
        propagation_status=status_map["EE"],
        trace_budget=None if source_report is None else source_report.q2_norm,
        spin2_budget=residual_report.spin2_residual,
        high_budget=residual_report.high_residual,
        source_error_bound=None if source_report is None else source_report.source_error_bound,
        propagator_norm_bound=propagator_norm_bound,
        amplification_bound=amplification_bound,
        propagation_status_by_channel=status_map,
        residual_bridge_report=bridge,
        include_extended_channels=include_extended_channels,
    )


__all__ = [
    "build_channel_budgets",
    "build_channel_budgets_from_reports",
    "channel_budget_BiPoSH",
    "channel_budget_BB",
    "channel_budget_EE",
    "channel_budget_TE",
    "channel_budget_TT",
    "channel_budget_scalar_summary",
    "channel_budget_template",
    "source_to_field_prebudget",
]
