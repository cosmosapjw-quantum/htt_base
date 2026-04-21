from __future__ import annotations

from common.contracts import ArtifactManifest
from tsc.admissibility.domain import build_domain_report
from tsc.budget.source_to_channel import build_channel_budgets
from tsc.control.upgrade_advisor import recommend_chart_transition
from tsc.reports.overlay_builder import build_tsc_overlay
from tsc.residuals.blockwise import ambient_vs_projected_defect_report
from tsc.source.thomson_bridge import build_source_bridge_report


def _tsc_manifest(artifact_id: str = "tsc.overlay") -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id=artifact_id,
        artifact_path=f"artifacts/tsc/{artifact_id.replace('.', '_')}.json",
        owner="TSC",
        implementation_scope="tsc",
        claim_tier="conditional",
        production_status="production_candidate",
        created_by="test-suite",
        git_commit="abc123",
        config_hash=f"cfg:{artifact_id}",
        input_hashes=["seed:0"],
        code_version="0.0-test",
        schema_version="ver2-v1",
    )


def build_pending_overlay():
    manifest = _tsc_manifest()
    domain = build_domain_report(chart="one_field", theta_samples=[1.0, 1.1], manifest=manifest)
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
        manifest=manifest,
    )
    source = build_source_bridge_report(
        chart="one_field",
        q2_norm=0.1,
        manifest=manifest,
        source_error=0.01,
        on_manifold_exact=True,
    )
    budgets = build_channel_budgets(
        manifest=manifest,
        source_status="adequate",
        propagation_status="pending",
        trace_budget=0.01,
        spin2_budget=0.2,
    )
    upgrade = recommend_chart_transition(domain, residual, source)
    return build_tsc_overlay(
        domain_report=domain,
        residual_report=residual,
        source_bridge_report=source,
        channel_budgets=budgets,
        upgrade_recommendation=upgrade,
        artifact_manifest=manifest,
    )
