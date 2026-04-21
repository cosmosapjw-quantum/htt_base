from __future__ import annotations

import pytest

from common.contracts import ArtifactManifest
from tsc.budget.source_to_channel import (
    build_channel_budgets,
    source_to_field_prebudget,
)


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
