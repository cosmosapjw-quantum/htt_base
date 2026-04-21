"""TSC-local active-service assembly without runtime or posterior ownership."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from common.contracts import (
    ArtifactManifest,
    TscAdequacyOverlay,
    TscChannelAdequacyBudget,
    TscChart,
    TscDomainReport,
    TscResidualReport,
    TscSourceBridgeReport,
    TscUpgradeRecommendation,
)
from tsc.adapters.bass_runtime import SourceAdequacySuggestion, overlay_to_bass_suggestion
from tsc.adapters.htt_inference import HttTscCaveatBundle, overlay_to_htt_caveats
from tsc.adapters.mio_certificate import MioTscAdequacyFields, overlay_to_mio_fields
from tsc.admissibility.domain import build_domain_report, guard_production_domain
from tsc.budget.source_to_channel import build_channel_budgets_from_reports
from tsc.control.upgrade_advisor import UpgradeAdvisorConfig, recommend_chart_transition
from tsc.reports.json_export import (
    overlay_is_publication_ready,
    overlay_publication_blockers,
    overlay_to_json_dict,
    overlay_to_markdown,
)
from tsc.reports.overlay_builder import build_tsc_overlay
from tsc.residuals.blockwise import ambient_vs_projected_defect_report
from tsc.source.thomson_bridge import build_source_bridge_report_from_samples


_DEFAULT_REQUIRED_CHANNELS = ("TT", "TE", "EE")


@dataclass(frozen=True)
class TscActiveServiceBundle:
    """Single assembled TSC active-service view for downstream consumers."""

    domain_report: TscDomainReport
    residual_report: TscResidualReport
    source_bridge_report: TscSourceBridgeReport | None
    channel_budgets: tuple[TscChannelAdequacyBudget, ...]
    upgrade_recommendation: TscUpgradeRecommendation
    overlay: TscAdequacyOverlay
    bass_suggestion: SourceAdequacySuggestion
    htt_caveats: HttTscCaveatBundle
    mio_fields: MioTscAdequacyFields
    publication_blockers: tuple[str, ...]
    publication_ready: bool
    overlay_json: Mapping[str, object]
    overlay_markdown: str


def build_active_service_bundle(
    *,
    domain_report: TscDomainReport,
    residual_report: TscResidualReport,
    source_bridge_report: TscSourceBridgeReport | None,
    artifact_manifest: ArtifactManifest | None = None,
    artifact_metadata: Mapping[str, object] | None = None,
    upgrade_config: UpgradeAdvisorConfig | None = None,
    propagator_norm_bound: float | None = None,
    amplification_bound: float | None = None,
    propagation_status_by_channel: Mapping[str, str] | None = None,
    uses_scalar_only_geometry: bool = False,
    required_channels: Sequence[str] = _DEFAULT_REQUIRED_CHANNELS,
    overlay_ref: str | None = None,
    enforce_production_domain: bool = False,
) -> TscActiveServiceBundle:
    """Assemble all TSC-local active-service artifacts without taking downstream authority."""
    if enforce_production_domain:
        guard_production_domain(domain_report)

    manifest = artifact_manifest or domain_report.manifest
    upgrade_recommendation = recommend_chart_transition(
        domain_report,
        residual_report,
        source_bridge_report,
        config=upgrade_config,
    )
    channel_budgets = build_channel_budgets_from_reports(
        manifest=manifest,
        domain_report=domain_report,
        residual_report=residual_report,
        source_report=source_bridge_report,
        propagator_norm_bound=propagator_norm_bound,
        amplification_bound=amplification_bound,
        propagation_status_by_channel=propagation_status_by_channel,
    )
    overlay = build_tsc_overlay(
        domain_report=domain_report,
        residual_report=residual_report,
        source_bridge_report=source_bridge_report,
        channel_budgets=channel_budgets,
        upgrade_recommendation=upgrade_recommendation,
        artifact_manifest=manifest,
        artifact_metadata=artifact_metadata,
    )
    blockers = overlay_publication_blockers(
        overlay,
        required_channels=required_channels,
    )
    return TscActiveServiceBundle(
        domain_report=domain_report,
        residual_report=residual_report,
        source_bridge_report=source_bridge_report,
        channel_budgets=tuple(channel_budgets),
        upgrade_recommendation=upgrade_recommendation,
        overlay=overlay,
        bass_suggestion=overlay_to_bass_suggestion(overlay, overlay_ref=overlay_ref),
        htt_caveats=overlay_to_htt_caveats(
            overlay,
            uses_scalar_only_geometry=uses_scalar_only_geometry,
            overlay_ref=overlay_ref,
        ),
        mio_fields=overlay_to_mio_fields(overlay),
        publication_blockers=blockers,
        publication_ready=overlay_is_publication_ready(
            overlay,
            required_channels=required_channels,
        ),
        overlay_json=overlay_to_json_dict(
            overlay,
            required_channels=required_channels,
        ),
        overlay_markdown=overlay_to_markdown(
            overlay,
            required_channels=required_channels,
        ),
    )


def build_active_service_bundle_from_samples(
    *,
    chart: TscChart,
    theta_samples: Sequence[float],
    directions: Sequence[float],
    weights: Sequence[float],
    manifest: ArtifactManifest,
    laguerre_n_ge_2_norm: float,
    onefield_residual: float | None,
    trace_residual_q_tr: float | None,
    ambient_defect_rate: float | None = None,
    projected_defect_estimate: float | None = None,
    twofield_residual: float | None = None,
    eta_tangent_fraction: float | None = None,
    spin2_residual: float | None = None,
    high_residual: float | None = None,
    residual_labels: tuple[str, ...] = (),
    eta_samples: Sequence[float] | None = None,
    be_case: bool = False,
    jacobian_singular_values: Sequence[float] | None = None,
    sigma_min_floor: float = 1e-8,
    T0: float = 1.0,
    xi: int = 0,
    ne: float = 1.0,
    sigma_T: float = 1.0,
    on_manifold_exact: bool = True,
    linear_bridge_requested: bool = False,
    dipole_amplitude: float | None = None,
    source_error: float | None = None,
    q2_op_norm: float | None = None,
    required_bass_primitives: tuple[str, ...] = (),
    artifact_metadata: Mapping[str, object] | None = None,
    propagation_status_by_channel: Mapping[str, str] | None = None,
    propagator_norm_bound: float | None = None,
    amplification_bound: float | None = None,
    uses_scalar_only_geometry: bool = False,
    required_channels: Sequence[str] = _DEFAULT_REQUIRED_CHANNELS,
    enforce_production_domain: bool = False,
) -> TscActiveServiceBundle:
    """Assemble the TSC service bundle directly from sampled angular inputs."""
    domain_report = build_domain_report(
        chart=chart,
        theta_samples=theta_samples,
        manifest=manifest,
        eta_samples=eta_samples,
        weights=weights,
        jacobian_singular_values=jacobian_singular_values,
        be_case=be_case,
        sigma_min_floor=sigma_min_floor,
    )
    residual_report = ambient_vs_projected_defect_report(
        chart=chart,
        laguerre_n_ge_2_norm=laguerre_n_ge_2_norm,
        ambient_defect_rate=ambient_defect_rate,
        projected_defect_estimate=projected_defect_estimate,
        onefield_residual=onefield_residual,
        twofield_residual=twofield_residual,
        eta_tangent_fraction=eta_tangent_fraction,
        trace_residual_q_tr=trace_residual_q_tr,
        spin2_residual=spin2_residual,
        high_residual=high_residual,
        labels=residual_labels,
        manifest=manifest,
    )
    source_bridge_report = build_source_bridge_report_from_samples(
        chart=chart,
        theta_samples=theta_samples,
        directions=directions,
        weights=weights,
        manifest=manifest,
        T0=T0,
        xi=xi,
        eta=eta_samples,
        ne=ne,
        sigma_T=sigma_T,
        on_manifold_exact=on_manifold_exact,
        linear_bridge_requested=linear_bridge_requested,
        dipole_amplitude=dipole_amplitude,
        source_error=source_error,
        q2_op_norm=q2_op_norm,
        required_bass_primitives=required_bass_primitives,
    )
    return build_active_service_bundle(
        domain_report=domain_report,
        residual_report=residual_report,
        source_bridge_report=source_bridge_report,
        artifact_manifest=manifest,
        artifact_metadata=artifact_metadata,
        propagator_norm_bound=propagator_norm_bound,
        amplification_bound=amplification_bound,
        propagation_status_by_channel=propagation_status_by_channel,
        uses_scalar_only_geometry=uses_scalar_only_geometry,
        required_channels=required_channels,
        enforce_production_domain=enforce_production_domain,
    )


__all__ = [
    "TscActiveServiceBundle",
    "build_active_service_bundle",
    "build_active_service_bundle_from_samples",
]
