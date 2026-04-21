from __future__ import annotations

import pytest

from common.contracts import ArtifactManifest
from tsc.admissibility.domain import build_domain_report
from tsc.residuals.blockwise import ambient_vs_projected_defect_report
from tsc.residuals.observable_bridge import build_residual_bridge_from_reports


def _manifest() -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id="tsc.residual.bridge",
        artifact_path="artifacts/tsc/residual_bridge.json",
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


def test_collision_residual_alone_cannot_claim_observable_bound():
    man = _manifest()
    domain = build_domain_report(chart="one_field", theta_samples=[1.0, 1.1], manifest=man)
    residual = ambient_vs_projected_defect_report(
        chart="one_field",
        laguerre_n_ge_2_norm=0.2,
        ambient_defect_rate=None,
        projected_defect_estimate=None,
        onefield_residual=None,
        twofield_residual=None,
        eta_tangent_fraction=None,
        trace_residual_q_tr=0.1,
        spin2_residual=None,
        high_residual=None,
        labels=tuple(),
        manifest=man,
    )

    bridge = build_residual_bridge_from_reports(
        domain_report=domain,
        residual_report=residual,
    )

    assert bridge.observable_bound is None
    assert bridge.bridge_status == "blocked_collision_state_mismatch"
    assert "observable_bridge_blocked_collision_state_mismatch" in bridge.warnings


def test_state_residual_and_sigma_min_yield_conditional_observable_bound():
    man = _manifest()
    domain = build_domain_report(
        chart="one_field",
        theta_samples=[1.0, 1.1],
        jacobian_singular_values=[0.1, 0.2],
        manifest=man,
    )
    residual = ambient_vs_projected_defect_report(
        chart="one_field",
        laguerre_n_ge_2_norm=0.2,
        ambient_defect_rate=None,
        projected_defect_estimate=None,
        onefield_residual=0.08,
        twofield_residual=0.04,
        eta_tangent_fraction=0.5,
        trace_residual_q_tr=0.1,
        spin2_residual=None,
        high_residual=None,
        labels=tuple(),
        manifest=man,
    )

    bridge = build_residual_bridge_from_reports(
        domain_report=domain,
        residual_report=residual,
    )

    assert bridge.bridge_status == "conditional_state_bound"
    assert bridge.observable_bound == pytest.approx(0.4)
    assert "observable_bridge_conditional" in bridge.warnings


def test_small_sigma_min_blocks_observable_claim_even_with_state_residual():
    man = _manifest()
    domain = build_domain_report(
        chart="one_field",
        theta_samples=[1.0, 1.1],
        jacobian_singular_values=[1.0e-12, 2.0e-12],
        sigma_min_floor=1.0e-8,
        manifest=man,
    )
    residual = ambient_vs_projected_defect_report(
        chart="one_field",
        laguerre_n_ge_2_norm=0.2,
        ambient_defect_rate=None,
        projected_defect_estimate=None,
        onefield_residual=0.08,
        twofield_residual=None,
        eta_tangent_fraction=None,
        trace_residual_q_tr=0.1,
        spin2_residual=None,
        high_residual=None,
        labels=tuple(),
        manifest=man,
    )

    bridge = build_residual_bridge_from_reports(
        domain_report=domain,
        residual_report=residual,
        sigma_min_floor=1.0e-8,
    )

    assert bridge.observable_bound is None
    assert bridge.bridge_status == "blocked_jacobian_conditioning"
    assert "observable_bridge_blocked_jacobian_conditioning" in bridge.warnings
