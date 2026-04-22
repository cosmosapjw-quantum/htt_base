"""Tests for the TSC -> HTT caveat handoff."""
from __future__ import annotations

import numpy as np

from common.contracts import ArtifactManifest
from tsc.adapters.htt_inference import overlay_to_htt_caveats
from tsc.integration.active_service import build_active_service_bundle_from_samples


def _manifest() -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id="tsc.htt.adapter",
        artifact_path="artifacts/tsc/htt_adapter.json",
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


def _overlay_with_tt_validated():
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
    return bundle.overlay


def test_overlay_to_htt_caveats_defaults_to_pending_required_channels():
    caveats = overlay_to_htt_caveats(_overlay_with_tt_validated())

    assert caveats.required_channels == ("TT", "TE", "EE")
    assert "propagation_pending:EE,TE" in caveats.publication_blockers
    assert caveats.channel_validity["EE"] == "pending"


def test_overlay_to_htt_caveats_can_narrow_required_channel_scope():
    caveats = overlay_to_htt_caveats(
        _overlay_with_tt_validated(),
        required_channels=("TT",),
        uses_scalar_only_geometry=True,
    )

    assert caveats.required_channels == ("TT",)
    assert caveats.publication_blockers == ()
    assert "scalar_only_discrimination_insufficient" in caveats.caveats
