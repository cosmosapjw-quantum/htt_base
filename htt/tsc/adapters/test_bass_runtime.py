"""Tests for the TSC -> BASS advisory handoff skeleton."""
from __future__ import annotations

from dataclasses import fields

from common.contracts import ArtifactManifest
from tsc.admissibility.domain import build_domain_report
from tsc.adapters.bass_runtime import SourceAdequacySuggestion, overlay_to_bass_suggestion
from tsc.budget.source_to_channel import build_channel_budgets, build_channel_budgets_from_reports
from tsc.control.upgrade_advisor import recommend_chart_transition
from tsc.reports.overlay_builder import build_tsc_overlay
from tsc.residuals.blockwise import ambient_vs_projected_defect_report
from tsc.source.thomson_bridge import build_source_bridge_report


def _manifest() -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id="tsc.bass.adapter",
        artifact_path="artifacts/tsc/bass_adapter.json",
        owner="TSC",
        implementation_scope="tsc",
        claim_tier="conditional",
        production_status="production_candidate",
        created_by="test-suite",
        git_commit="abc123",
        config_hash="cfg",
        input_hashes=["a"],
        code_version="0.0-test",
        schema_version="ver2-v1",
    )


def test_bass_adapter_has_no_allow_reduction_field():
    names = {field.name for field in fields(SourceAdequacySuggestion)}
    assert "allow_reduction" not in names


def test_overlay_to_bass_suggestion_preserves_pending_split():
    man = _manifest()
    domain = build_domain_report(chart="one_field", theta_samples=[1.0, 1.1], manifest=man)
    residual = ambient_vs_projected_defect_report(
        chart="one_field",
        laguerre_n_ge_2_norm=0.1,
        ambient_defect_rate=None,
        projected_defect_estimate=None,
        onefield_residual=0.1,
        twofield_residual=None,
        eta_tangent_fraction=None,
        trace_residual_q_tr=0.1,
        spin2_residual=None,
        high_residual=None,
        labels=tuple(),
        manifest=man,
    )
    source = build_source_bridge_report(
        chart="one_field",
        q2_norm=0.1,
        manifest=man,
        source_error=0.02,
        on_manifold_exact=True,
    )
    budgets = build_channel_budgets_from_reports(
        manifest=man,
        domain_report=domain,
        residual_report=residual,
        source_report=source,
        propagation_status_by_channel={"TT": "validated"},
    )
    overlay = build_tsc_overlay(
        domain_report=domain,
        residual_report=residual,
        source_bridge_report=source,
        channel_budgets=budgets,
        upgrade_recommendation=recommend_chart_transition(domain, residual, source),
        artifact_manifest=man,
    )
    suggestion = overlay_to_bass_suggestion(overlay, overlay_ref="tsc:overlay:1")
    assert suggestion.recommended_label == "source_adequate__propagation_pending"
    assert suggestion.tsc_overlay_ref == "tsc:overlay:1"


def test_overlay_to_bass_suggestion_preserves_inadequate_source_status():
    man = _manifest()
    domain = build_domain_report(chart="one_field", theta_samples=[1.0, 1.1], manifest=man)
    residual = ambient_vs_projected_defect_report(
        chart="one_field",
        laguerre_n_ge_2_norm=0.1,
        ambient_defect_rate=None,
        projected_defect_estimate=None,
        onefield_residual=0.1,
        twofield_residual=None,
        eta_tangent_fraction=None,
        trace_residual_q_tr=0.1,
        spin2_residual=None,
        high_residual=None,
        labels=tuple(),
        manifest=man,
    )
    source = build_source_bridge_report(
        chart="one_field",
        q2_norm=0.1,
        manifest=man,
        source_error=0.3,
        on_manifold_exact=False,
        linear_bridge_requested=False,
    )
    budgets = build_channel_budgets(
        manifest=man,
        source_status="inadequate",
        propagation_status="pending",
        trace_budget=0.1,
    )
    overlay = build_tsc_overlay(
        domain_report=domain,
        residual_report=residual,
        source_bridge_report=source,
        channel_budgets=budgets,
        upgrade_recommendation=recommend_chart_transition(domain, residual, source),
        artifact_manifest=man,
    )

    suggestion = overlay_to_bass_suggestion(overlay)
    assert suggestion.source_status == "inadequate"
    assert suggestion.recommended_label == "source_inadequate__propagation_not_evaluated"


def test_overlay_to_bass_suggestion_marks_tt_bridge_limit_as_pending():
    man = _manifest()
    domain = build_domain_report(
        chart="one_field",
        theta_samples=[1.0, 1.1],
        jacobian_singular_values=[0.1, 0.2],
        manifest=man,
    )
    residual = ambient_vs_projected_defect_report(
        chart="one_field",
        laguerre_n_ge_2_norm=0.1,
        ambient_defect_rate=None,
        projected_defect_estimate=None,
        onefield_residual=None,
        twofield_residual=None,
        eta_tangent_fraction=None,
        trace_residual_q_tr=0.1,
        spin2_residual=0.2,
        high_residual=None,
        labels=tuple(),
        manifest=man,
    )
    source = build_source_bridge_report(
        chart="one_field",
        q2_norm=0.1,
        manifest=man,
        source_error=0.01,
        on_manifold_exact=True,
    )
    budgets = build_channel_budgets_from_reports(
        manifest=man,
        domain_report=domain,
        residual_report=residual,
        source_report=source,
        propagation_status_by_channel={"EE": "validated", "TE": "validated"},
    )
    overlay = build_tsc_overlay(
        domain_report=domain,
        residual_report=residual,
        source_bridge_report=source,
        channel_budgets=budgets,
        upgrade_recommendation=recommend_chart_transition(domain, residual, source),
        artifact_manifest=man,
    )

    suggestion = overlay_to_bass_suggestion(overlay)
    assert suggestion.recommended_label == "source_adequate__propagation_pending"
    assert suggestion.channel_claim_ceiling["TT"] == "exploratory"
    assert suggestion.restricted_channels == ("TT",)


def test_overlay_to_bass_suggestion_can_narrow_required_channel_scope():
    man = _manifest()
    domain = build_domain_report(
        chart="one_field",
        theta_samples=[1.0, 1.1],
        jacobian_singular_values=[0.1, 0.2],
        manifest=man,
    )
    residual = ambient_vs_projected_defect_report(
        chart="one_field",
        laguerre_n_ge_2_norm=0.1,
        ambient_defect_rate=None,
        projected_defect_estimate=None,
        onefield_residual=0.1,
        twofield_residual=None,
        eta_tangent_fraction=None,
        trace_residual_q_tr=0.1,
        spin2_residual=0.2,
        high_residual=None,
        labels=tuple(),
        manifest=man,
    )
    source = build_source_bridge_report(
        chart="one_field",
        q2_norm=0.1,
        manifest=man,
        source_error=0.02,
        on_manifold_exact=True,
    )
    budgets = build_channel_budgets_from_reports(
        manifest=man,
        domain_report=domain,
        residual_report=residual,
        source_report=source,
        propagation_status_by_channel={"TT": "validated"},
    )
    overlay = build_tsc_overlay(
        domain_report=domain,
        residual_report=residual,
        source_bridge_report=source,
        channel_budgets=budgets,
        upgrade_recommendation=recommend_chart_transition(domain, residual, source),
        artifact_manifest=man,
    )

    suggestion = overlay_to_bass_suggestion(
        overlay,
        required_channels=("TT",),
    )
    assert suggestion.recommended_label == "source_adequate__propagation_validated"
    assert suggestion.restricted_channels == ()
