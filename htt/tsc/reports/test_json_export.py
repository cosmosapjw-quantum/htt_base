from __future__ import annotations

from common.contracts import ArtifactManifest, FullCovMESReport
from common.departure_contracts import DepartureReport
from tsc.admissibility.domain import build_domain_report
from tsc.budget.source_to_channel import build_channel_budgets, build_channel_budgets_from_reports
from tsc.control.upgrade_advisor import recommend_chart_transition
from tsc.reports.json_export import (
    attach_overlay_to_departure_report,
    attach_overlay_to_mes_report,
    attach_overlay_to_mio_certificate,
    overlay_to_policy_ledger_dict,
    overlay_to_policy_ledger_markdown,
    overlay_to_json_dict,
    overlay_to_markdown,
)
from tsc.reports.overlay_builder import build_tsc_overlay
from tsc.residuals.blockwise import ambient_vs_projected_defect_report
from tsc.source.thomson_bridge import build_source_bridge_report
from workspace.contracts.mio_certificate import MioCertificate


def _manifest(owner: str, scope: str) -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id=f"{owner.lower()}.artifact",
        artifact_path=f"artifacts/{owner.lower()}.json",
        owner=owner,  # type: ignore[arg-type]
        implementation_scope=scope,  # type: ignore[arg-type]
        claim_tier="conditional",
        production_status="production_candidate",
        created_by="test-suite",
        git_commit="abc123",
        config_hash="cfg",
        input_hashes=["a"],
        code_version="0.0-test",
        schema_version="ver2-v1",
    )


def _overlay_pending():
    man = _manifest("TSC", "tsc")
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
        source_error_bound=0.01,
        propagator_norm_bound=4.0,
        spin2_budget=0.2,
    )
    return build_tsc_overlay(
        domain_report=domain,
        residual_report=residual,
        source_bridge_report=source,
        channel_budgets=budgets,
        upgrade_recommendation=recommend_chart_transition(domain, residual, source),
        artifact_manifest=man,
    )


def _overlay_tt_claim_limited():
    man = _manifest("TSC", "tsc")
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
    return build_tsc_overlay(
        domain_report=domain,
        residual_report=residual,
        source_bridge_report=source,
        channel_budgets=budgets,
        upgrade_recommendation=recommend_chart_transition(domain, residual, source),
        artifact_manifest=man,
    )


def test_overlay_export_marks_pending_propagation_as_publication_blocker():
    overlay = _overlay_pending()

    payload = overlay_to_json_dict(overlay)
    markdown = overlay_to_markdown(overlay)

    assert payload["publication_ready"] is False
    assert any(
        str(blocker).startswith("propagation_pending:")
        for blocker in payload["publication_blockers"]
    )
    assert "propagation validation is still pending" in markdown


def test_attach_overlay_helpers_set_ref_and_propagate_public_snippet():
    overlay = _overlay_pending()

    departure = DepartureReport(
        comparator_policy="flat",
        bundle_B={},
        x_value=0.1,
        numerator_policy="signed",
        denominator_policy="toy_budget",
        U_value=0.1,
        Q_value=0.2,
        F_value=None,
        F_status="linear_proxy_score",
        Pi_curve_ref=None,
        G_values={},
        component_filling={},
        channel_filling={},
        caveats=[],
        manifest=_manifest("HTT", "htt"),
    )
    mes = FullCovMESReport(
        parameter_block="sigma",
        diagonal_bound=1.0,
        covariance_bound=None,
        dynamical_bound=None,
        final_bound=1.0,
        information_gain=0.1,
        response_rank=1,
        singular_values=[1.0],
        nuisance_projection_status="none",
        observable_set=["TT"],
        covariance_assumption="diag",
        validity_radius=None,
        manifest=_manifest("COMMON", "common"),
    )
    cert = MioCertificate(
        report_type="directional_coherence",
        probe_name="Planck_TT",
        channel="low_ell",
        departure_variables={},
        adequacy_indicators={},
        consistency_metrics={},
        domain_caveats=[],
        channel_caveats=[],
        reduction_status="diagnostic-only",
        generated_by="test-suite",
        git_commit="abc123",
        config_hash="cfg",
        input_data_hashes=["a"],
        manifest=_manifest("MIO", "mio"),
    )

    attached_departure = attach_overlay_to_departure_report(departure, overlay)
    attached_mes = attach_overlay_to_mes_report(mes, overlay)
    attached_cert = attach_overlay_to_mio_certificate(cert, overlay)

    assert attached_departure.tsc_overlay_ref == overlay.manifest.artifact_id
    assert overlay.public_caveat_snippet in attached_departure.caveats
    assert attached_mes.tsc_overlay_ref == overlay.manifest.artifact_id
    assert attached_cert.tsc_overlay_ref == overlay.manifest.artifact_id
    assert overlay.public_caveat_snippet in attached_cert.domain_caveats


def test_overlay_export_blocks_exploratory_claim_ceiling_even_when_propagation_validated():
    overlay = _overlay_tt_claim_limited()

    payload = overlay_to_json_dict(overlay, required_channels=("TT",))
    markdown = overlay_to_markdown(overlay, required_channels=("TT",))

    assert payload["publication_ready"] is False
    assert "claim_ceiling_insufficient:TT=exploratory" in payload["publication_blockers"]
    assert payload["channel_claim_ceiling"]["TT"] == "exploratory"
    assert "TT:adequate/validated/exploratory" in markdown


def test_overlay_policy_ledger_summarizes_claim_and_no_overclaim_state():
    overlay = _overlay_tt_claim_limited()

    ledger = overlay_to_policy_ledger_dict(overlay, required_channels=("TT",))
    markdown = overlay_to_policy_ledger_markdown(overlay, required_channels=("TT",))

    assert ledger["advisory_only"] is True
    assert ledger["publication_ready"] is False
    assert ledger["channel_claim_ceiling"]["TT"] == "exploratory"
    assert "TT" in ledger["claim_limited_channels"]
    assert ledger["failed_no_overclaim_flags"] == ()
    assert "claim-limited channels:" in markdown
    assert "BB, TT" in markdown
