"""Source-to-channel adequacy budgets for the VER2 TSC service."""
from __future__ import annotations

from common.contracts import ArtifactManifest, TscChannelAdequacyBudget
from tsc.contracts import CHANNEL_DEFAULT_CLAIM_CEILINGS


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
) -> tuple[str, ...]:
    if channel == "BB":
        return ("trace_only__bb_claim_forbidden",)

    labels: list[str] = []
    if source_status == "adequate" and propagation_status == "validated":
        labels.append("source_adequate__propagation_validated")
    elif source_status == "adequate":
        labels.append("source_adequate__propagation_pending")
    else:
        labels.append("source_inadequate__propagation_not_evaluated")

    if channel in {"EE", "TE"}:
        labels.append("trace_ok__spin2_required")
    if channel == "TE":
        labels.append("te_mixed_channel_requires_spin2")
    return tuple(dict.fromkeys(labels))


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
        claim_ceiling=CHANNEL_DEFAULT_CLAIM_CEILINGS[channel],  # type: ignore[arg-type]
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
        ),
    )


def channel_budget_EE(
    *,
    manifest: ArtifactManifest,
    trace_budget: float | None,
    spin2_budget: float | None,
    source_status: str,
    propagation_status: str = "pending",
    source_to_field_bound: float | None = None,
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
        ),
    )


def channel_budget_TE(
    *,
    manifest: ArtifactManifest,
    trace_budget: float | None,
    spin2_budget: float | None,
    source_status: str,
    propagation_status: str = "pending",
    source_to_field_bound: float | None = None,
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
        ),
    )


def channel_budget_BB(
    *,
    manifest: ArtifactManifest,
    source_status: str,
    propagation_status: str = "blocked",
    high_budget: float | None = None,
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
        ),
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
) -> tuple[TscChannelAdequacyBudget, ...]:
    source_budget = trace_budget if trace_budget is not None else source_error_bound
    field_prebudget = source_to_field_prebudget(
        source_budget,
        propagator_norm_bound,
        amplification_bound=amplification_bound,
    )
    return (
        channel_budget_TT(
            manifest=manifest,
            trace_budget=source_budget,
            source_status=source_status,
            propagation_status="validated" if propagation_status == "validated" else "pending",
            source_to_field_bound=field_prebudget,
        ),
        channel_budget_EE(
            manifest=manifest,
            trace_budget=source_budget,
            spin2_budget=spin2_budget,
            source_status=source_status,
            propagation_status=propagation_status,
            source_to_field_bound=field_prebudget,
        ),
        channel_budget_TE(
            manifest=manifest,
            trace_budget=source_budget,
            spin2_budget=spin2_budget,
            source_status=source_status,
            propagation_status=propagation_status,
            source_to_field_bound=field_prebudget,
        ),
        channel_budget_BB(
            manifest=manifest,
            source_status=source_status,
            propagation_status="blocked" if propagation_status != "validated" else "validated",
            high_budget=high_budget,
        ),
    )


__all__ = [
    "build_channel_budgets",
    "channel_budget_BB",
    "channel_budget_EE",
    "channel_budget_TE",
    "channel_budget_TT",
    "source_to_field_prebudget",
]
