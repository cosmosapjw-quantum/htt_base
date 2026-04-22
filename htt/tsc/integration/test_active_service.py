from __future__ import annotations

import numpy as np
import pytest

from common.contracts import ArtifactManifest
from tsc.integration.active_service import (
    active_service_bundle_to_dict,
    active_service_bundle_to_markdown,
    build_active_service_bundle,
    build_active_service_bundle_from_samples,
)
from tsc.admissibility.domain import build_domain_report
from tsc.residuals.blockwise import ambient_vs_projected_defect_report


def _manifest() -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id="tsc.active.service",
        artifact_path="artifacts/tsc/active_service.json",
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


def test_active_service_bundle_from_samples_keeps_source_propagation_split():
    mu, weights = np.polynomial.legendre.leggauss(32)
    weights = weights / np.sum(weights)
    theta = 1.0 + 0.10 * mu

    bundle = build_active_service_bundle_from_samples(
        chart="one_field",
        theta_samples=theta.tolist(),
        directions=mu.tolist(),
        weights=weights.tolist(),
        manifest=_manifest(),
        laguerre_n_ge_2_norm=0.1,
        onefield_residual=0.1,
        trace_residual_q_tr=0.1,
        spin2_residual=0.2,
        jacobian_singular_values=[0.1, 0.2],
        propagation_status_by_channel={"TT": "validated", "EE": "pending", "TE": "pending"},
        propagator_norm_bound=3.0,
    )

    assert bundle.overlay.source_bridge_report is not None
    assert bundle.overlay.source_bridge_report.source_status == "adequate"
    assert bundle.residual_bridge_report.bridge_status == "conditional_state_bound"
    assert bundle.bass_suggestion.source_status == "adequate"
    assert set(bundle.bass_suggestion.restricted_channels) == {"EE", "TE"}
    assert bundle.htt_caveats.required_channels == ("TT", "TE", "EE")
    assert "propagation_pending:EE,TE" in bundle.htt_caveats.publication_blockers
    assert bundle.htt_caveats.channel_validity["EE"] == "pending"
    assert bundle.htt_caveats.channel_claim_ceiling["TT"] == "conditional"
    assert bundle.mio_fields.trace_source_adequacy == "adequate"
    assert bundle.mio_fields.required_channels == ("TT", "TE", "EE")
    assert "propagation_pending:EE,TE" in bundle.mio_fields.publication_blockers
    assert bundle.mio_fields.channel_claim_ceiling["TT"] == "conditional"
    assert bundle.publication_ready is False
    assert any(str(blocker).startswith("propagation_pending:") for blocker in bundle.publication_blockers)
    assert "BB remains outside trace-only validation" in bundle.overlay.public_caveat_snippet


def test_active_service_bundle_mio_fields_follow_required_channel_scope():
    mu, weights = np.polynomial.legendre.leggauss(32)
    weights = weights / np.sum(weights)
    theta = 1.0 + 0.10 * mu

    bundle = build_active_service_bundle_from_samples(
        chart="one_field",
        theta_samples=theta.tolist(),
        directions=mu.tolist(),
        weights=weights.tolist(),
        manifest=_manifest(),
        laguerre_n_ge_2_norm=0.1,
        onefield_residual=0.1,
        trace_residual_q_tr=0.1,
        spin2_residual=0.2,
        jacobian_singular_values=[0.1, 0.2],
        propagation_status_by_channel={"TT": "validated", "EE": "pending", "TE": "pending"},
        propagator_norm_bound=3.0,
        required_channels=("TT",),
    )

    payload = active_service_bundle_to_dict(bundle)

    assert bundle.publication_ready is True
    assert bundle.publication_blockers == ()
    assert bundle.bass_suggestion.recommended_label == "source_adequate__propagation_validated"
    assert bundle.bass_suggestion.restricted_channels == ()
    assert bundle.htt_caveats.required_channels == ("TT",)
    assert bundle.htt_caveats.publication_blockers == ()
    assert bundle.mio_fields.required_channels == ("TT",)
    assert bundle.mio_fields.propagation_status_required == ()
    assert bundle.mio_fields.publication_blockers == ()
    assert bundle.mio_fields.diagnostic_only is False
    assert payload["htt_caveats"]["required_channels"] == ("TT",)
    assert payload["htt_caveats"]["publication_blockers"] == ()
    assert payload["mio_fields"]["required_channels"] == ("TT",)
    assert payload["mio_fields"]["publication_blockers"] == ()


def test_active_service_bundle_invalid_domain_can_raise_when_guarded():
    man = _manifest()
    domain = build_domain_report(chart="one_field", theta_samples=[-0.1, 0.2], manifest=man)
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

    with pytest.raises(RuntimeError, match="invalid chart domain"):
        build_active_service_bundle(
            domain_report=domain,
            residual_report=residual,
            source_bridge_report=None,
            enforce_production_domain=True,
        )


def test_active_service_bundle_blocks_publication_when_tt_claim_ceiling_is_exploratory():
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
    bundle = build_active_service_bundle(
        domain_report=domain,
        residual_report=residual,
        source_bridge_report=None,
        required_channels=("TT",),
    )

    assert bundle.publication_ready is False
    assert "source_bridge_missing" in bundle.publication_blockers
    assert "claim_ceiling_insufficient:TT=exploratory" in bundle.publication_blockers


def test_active_service_bundle_export_summarizes_policy_and_bridge_state():
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
    bundle = build_active_service_bundle(
        domain_report=domain,
        residual_report=residual,
        source_bridge_report=None,
        required_channels=("TT",),
    )

    payload = active_service_bundle_to_dict(bundle)
    markdown = active_service_bundle_to_markdown(bundle)

    assert payload["publication_ready"] is False
    assert payload["residual_bridge_status"] == "blocked_collision_state_mismatch"
    assert payload["bass_suggestion"]["recommended_label"] == "source_bridge_bound_pending"
    assert payload["htt_caveats"]["required_channels"] == ("TT",)
    assert "source_bridge_missing" in payload["htt_caveats"]["publication_blockers"]
    assert payload["overlay_policy_ledger"]["channel_claim_ceiling"]["TT"] == "exploratory"
    assert "source_bridge_missing" in payload["publication_blockers"]
    assert "publication blockers: `source_bridge_missing" in markdown
