from __future__ import annotations

import pytest

from common.contracts import ArtifactManifest
from tsc.admissibility.domain import build_domain_report
from tsc.budget.source_to_channel import (
    build_channel_budgets,
    build_channel_budgets_from_reports,
    source_to_field_prebudget,
)
from tsc.residuals.blockwise import ambient_vs_projected_defect_report
from tsc.source.thomson_bridge import build_source_bridge_report


def _manifest() -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id="tsc.channel.budget",
        artifact_path="artifacts/tsc/channel_budget.json",
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


def test_source_to_field_prebudget_respects_propagator_and_amplification():
    assert source_to_field_prebudget(0.2, 3.0, amplification_bound=2.0) == pytest.approx(
        1.2
    )


def test_build_channel_budgets_keep_pending_split_without_validated_spectrum_bounds():
    budgets = build_channel_budgets(
        manifest=_manifest(),
        source_status="adequate",
        propagation_status="pending",
        source_error_bound=0.02,
        propagator_norm_bound=4.0,
        spin2_budget=0.30,
    )
    by_channel = {budget.channel: budget for budget in budgets}

    assert by_channel["TT"].source_to_field_bound == pytest.approx(0.08)
    assert by_channel["TT"].spectrum_bound_linear is None
    assert "source_adequate__propagation_pending" in by_channel["TT"].labels
    assert "trace_ok__spin2_required" in by_channel["EE"].labels
    assert by_channel["BB"].claim_ceiling == "blocked"
    assert by_channel["BB"].spectrum_bound_linear is None


def test_validated_budgets_emit_field_bounds_but_keep_bb_claim_blocked():
    budgets = build_channel_budgets(
        manifest=_manifest(),
        source_status="adequate",
        propagation_status="validated",
        source_error_bound=0.02,
        propagator_norm_bound=4.0,
        spin2_budget=0.30,
        high_budget=0.50,
    )
    by_channel = {budget.channel: budget for budget in budgets}

    assert by_channel["TT"].spectrum_bound_linear == pytest.approx(0.08)
    assert by_channel["EE"].spectrum_bound_quadratic == pytest.approx(0.30)
    assert by_channel["TE"].spectrum_bound_linear == pytest.approx(0.08)
    assert by_channel["BB"].propagation_status == "validated"
    assert by_channel["BB"].claim_ceiling == "blocked"
    assert by_channel["BB"].spectrum_bound_quadratic is None


def test_inadequate_source_uses_conservative_nonclaim_label():
    budgets = build_channel_budgets(
        manifest=_manifest(),
        source_status="inadequate",
        propagation_status="pending",
        trace_budget=0.10,
    )
    by_channel = {budget.channel: budget for budget in budgets}

    assert by_channel["TT"].labels[0] == "source_inadequate__propagation_not_evaluated"
    assert by_channel["TE"].labels[0] == "source_inadequate__propagation_not_evaluated"
    assert by_channel["TT"].claim_ceiling == "exploratory"


def test_build_channel_budgets_from_reports_blocks_all_channels_for_invalid_domain():
    man = _manifest()
    domain = build_domain_report(
        chart="one_field",
        theta_samples=[-0.1, 0.2],
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
        spin2_residual=None,
        high_residual=None,
        labels=tuple(),
        manifest=man,
    )
    budgets = build_channel_budgets_from_reports(
        manifest=man,
        domain_report=domain,
        residual_report=residual,
        source_report=None,
    )

    assert {budget.propagation_status for budget in budgets} == {"blocked"}


def test_build_channel_budgets_from_reports_allows_per_channel_overrides():
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
        spin2_residual=0.2,
        high_residual=0.3,
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
        propagation_status_by_channel={"EE": "validated", "TE": "blocked"},
    )
    by_channel = {budget.channel: budget for budget in budgets}

    assert by_channel["TT"].propagation_status == "validated"
    assert by_channel["EE"].propagation_status == "validated"
    assert by_channel["TE"].propagation_status == "blocked"
    assert by_channel["BB"].propagation_status == "blocked"


def test_tt_claim_ceiling_requires_state_residual_bridge():
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
        high_residual=0.3,
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
    )
    by_channel = {budget.channel: budget for budget in budgets}

    assert by_channel["TT"].claim_ceiling == "exploratory"
    assert "observable_bridge_blocked_collision_state_mismatch" in by_channel["TT"].labels


def test_tt_claim_ceiling_becomes_conditional_with_state_residual_bridge():
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
        onefield_residual=0.08,
        twofield_residual=0.04,
        eta_tangent_fraction=0.5,
        trace_residual_q_tr=0.1,
        spin2_residual=0.2,
        high_residual=0.3,
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
        include_extended_channels=True,
    )
    by_channel = {budget.channel: budget for budget in budgets}

    assert by_channel["TT"].claim_ceiling == "conditional"
    assert by_channel["scalar_summary"].claim_ceiling == "conditional"
    assert by_channel["BiPoSH"].claim_ceiling == "exploratory"
    assert by_channel["template"].claim_ceiling == "blocked"
    assert "observable_bridge_conditional" in by_channel["TT"].labels
    assert "biposh_requires_external_validation" in by_channel["BiPoSH"].labels
    assert "template_family_claim_blocked" in by_channel["template"].labels
