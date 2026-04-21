"""Tests for the TSC -> MIO adequacy-field handoff."""
from __future__ import annotations

import numpy as np

from common.contracts import ArtifactManifest
from tsc.adapters.mio_certificate import overlay_to_mio_fields
from tsc.integration.active_service import build_active_service_bundle_from_samples


def _manifest() -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id="tsc.mio.adapter",
        artifact_path="artifacts/tsc/mio_adapter.json",
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


def test_overlay_to_mio_fields_defaults_to_pending_required_channels():
    fields = overlay_to_mio_fields(_overlay_with_tt_validated())

    assert fields.required_channels == ("TT", "TE", "EE")
    assert fields.propagation_status_required == ("EE", "TE")
    assert "propagation_pending:EE,TE" in fields.publication_blockers
    assert fields.diagnostic_only is True


def test_overlay_to_mio_fields_can_narrow_required_channel_scope():
    fields = overlay_to_mio_fields(
        _overlay_with_tt_validated(),
        required_channels=("TT",),
    )

    assert fields.required_channels == ("TT",)
    assert fields.propagation_status_required == ()
    assert fields.publication_blockers == ()
    assert fields.diagnostic_only is False
