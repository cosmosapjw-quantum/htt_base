"""Skeleton source-to-channel responsibility budgets."""
from __future__ import annotations

from common.contracts import ArtifactManifest, TscChannelAdequacyBudget
from tsc.contracts import CHANNEL_DEFAULT_CLAIM_CEILINGS


def source_to_field_prebudget(
    source_error_bound: float | None,
    propagator_norm_bound: float | None = None,
) -> float | None:
    if source_error_bound is None:
        return None
    if propagator_norm_bound is None:
        return None
    return float(abs(source_error_bound) * abs(propagator_norm_bound))


def _base_budget(
    *,
    channel: str,
    manifest: ArtifactManifest,
    trace_budget: float | None,
    spin2_budget: float | None,
    high_budget: float | None,
    source_status: str,
    propagation_status: str,
    labels: tuple[str, ...],
) -> TscChannelAdequacyBudget:
    return TscChannelAdequacyBudget(
        channel=channel,  # type: ignore[arg-type]
        trace_budget=trace_budget,
        spin2_budget=spin2_budget,
        high_budget=high_budget,
        source_to_field_bound=None,
        spectrum_bound_linear=trace_budget,
        spectrum_bound_quadratic=high_budget,
        source_status=source_status,  # type: ignore[arg-type]
        propagation_status=propagation_status,  # type: ignore[arg-type]
        claim_ceiling=CHANNEL_DEFAULT_CLAIM_CEILINGS[channel],  # type: ignore[arg-type]
        labels=labels,
        manifest=manifest,
    )


def channel_budget_TT(*, manifest: ArtifactManifest, trace_budget: float | None, source_status: str, propagation_status: str = "validated") -> TscChannelAdequacyBudget:
    return _base_budget(
        channel="TT",
        manifest=manifest,
        trace_budget=trace_budget,
        spin2_budget=None,
        high_budget=None,
        source_status=source_status,
        propagation_status=propagation_status,
        labels=("source_adequate__propagation_validated" if propagation_status == "validated" else "source_adequate__propagation_pending",),
    )


def channel_budget_EE(*, manifest: ArtifactManifest, trace_budget: float | None, spin2_budget: float | None, source_status: str, propagation_status: str = "pending") -> TscChannelAdequacyBudget:
    return _base_budget(
        channel="EE",
        manifest=manifest,
        trace_budget=trace_budget,
        spin2_budget=spin2_budget,
        high_budget=None,
        source_status=source_status,
        propagation_status=propagation_status,
        labels=("trace_ok__spin2_required",),
    )


def channel_budget_TE(*, manifest: ArtifactManifest, trace_budget: float | None, spin2_budget: float | None, source_status: str, propagation_status: str = "pending") -> TscChannelAdequacyBudget:
    return _base_budget(
        channel="TE",
        manifest=manifest,
        trace_budget=trace_budget,
        spin2_budget=spin2_budget,
        high_budget=None,
        source_status=source_status,
        propagation_status=propagation_status,
        labels=("source_adequate__propagation_pending",),
    )


def channel_budget_BB(*, manifest: ArtifactManifest, source_status: str, propagation_status: str = "blocked", high_budget: float | None = None) -> TscChannelAdequacyBudget:
    return _base_budget(
        channel="BB",
        manifest=manifest,
        trace_budget=None,
        spin2_budget=None,
        high_budget=high_budget,
        source_status=source_status,
        propagation_status=propagation_status,
        labels=("trace_only__bb_claim_forbidden",),
    )


def build_channel_budgets(
    *,
    manifest: ArtifactManifest,
    source_status: str,
    propagation_status: str = "pending",
    trace_budget: float | None = None,
    spin2_budget: float | None = None,
    high_budget: float | None = None,
) -> tuple[TscChannelAdequacyBudget, ...]:
    return (
        channel_budget_TT(
            manifest=manifest,
            trace_budget=trace_budget,
            source_status=source_status,
            propagation_status="validated" if propagation_status == "validated" else "pending",
        ),
        channel_budget_EE(
            manifest=manifest,
            trace_budget=trace_budget,
            spin2_budget=spin2_budget,
            source_status=source_status,
            propagation_status=propagation_status,
        ),
        channel_budget_TE(
            manifest=manifest,
            trace_budget=trace_budget,
            spin2_budget=spin2_budget,
            source_status=source_status,
            propagation_status=propagation_status,
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
