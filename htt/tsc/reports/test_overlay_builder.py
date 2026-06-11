"""Tests for the TSC overlay builder skeleton."""
from __future__ import annotations

from common.contracts import ArtifactManifest, Owner
from tsc.admissibility.domain import build_domain_report
from tsc.budget.source_to_channel import build_channel_budgets, build_channel_budgets_from_reports
from tsc.control.upgrade_advisor import recommend_chart_transition
from tsc.reports.overlay_builder import build_public_caveat_snippet, build_tsc_overlay
from tsc.residuals.blockwise import ambient_vs_projected_defect_report
from tsc.source.thomson_bridge import build_source_bridge_report


def _manifest() -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id="tsc.overlay",
        artifact_path="artifacts/tsc/overlay.json",
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


def test_overlay_builder_propagation_pending_snippet_and_flags():
    man = _manifest()
    domain = build_domain_report(chart="one_field", theta_samples=[1.0, 1.1], manifest=man)
    residual = ambient_vs_projected_defect_report(
        chart="one_field",
        laguerre_n_ge_2_norm=0.1,
        ambient_defect_rate=None,
        projected_defect_estimate=None,
        onefield_residual=0.1,
        twofield_residual=0.05,
        eta_tangent_fraction=0.2,
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
        source_error=0.01,
        on_manifold_exact=True,
    )
    budgets = build_channel_budgets(
        manifest=man,
        source_status="adequate",
        propagation_status="pending",
        trace_budget=0.01,
        spin2_budget=0.2,
    )
    upgrade = recommend_chart_transition(domain, residual, source)
    overlay = build_tsc_overlay(
        domain_report=domain,
        residual_report=residual,
        source_bridge_report=source,
        channel_budgets=budgets,
        upgrade_recommendation=upgrade,
        artifact_manifest=man,
    )
    assert "propagation validation is still pending" in overlay.public_caveat_snippet
    assert overlay.no_overclaim_flags["full_polarization"]
    assert overlay.manifest.owner is Owner.TSC_LEGACY


def test_overlay_builder_quarantines_forbidden_phrase():
    man = _manifest()
    domain = build_domain_report(chart="one_field", theta_samples=[1.0, 1.1], manifest=man)
    residual = ambient_vs_projected_defect_report(
        chart="one_field",
        laguerre_n_ge_2_norm=0.0,
        ambient_defect_rate=None,
        projected_defect_estimate=None,
        onefield_residual=0.0,
        twofield_residual=None,
        eta_tangent_fraction=None,
        trace_residual_q_tr=0.0,
        spin2_residual=None,
        high_residual=None,
        labels=tuple(),
        manifest=man,
    )
    upgrade = recommend_chart_transition(domain, residual, None)
    overlay = build_tsc_overlay(
        domain_report=domain,
        residual_report=residual,
        source_bridge_report=None,
        channel_budgets=tuple(),
        upgrade_recommendation=upgrade,
        artifact_manifest=man,
        artifact_metadata={"summary": "TSC validates BB"},
        public_snippet="TSC validates BB",
    )
    assert "no_overclaim:full_polarization" in overlay.quarantine_reasons
    assert not overlay.no_overclaim_flags["full_polarization"]
    assert build_public_caveat_snippet(domain, None, tuple()).startswith("TSC source bridge not attached")


def test_overlay_builder_mentions_claim_limited_tt_even_when_propagation_validated():
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

    snippet = build_public_caveat_snippet(domain, source, budgets)
    assert "claim ceilings remain limited for TT" in snippet
