from __future__ import annotations

import numpy as np
import pytest

from common.contracts import ArtifactManifest
from tsc.integration.active_service import (
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
        propagation_status_by_channel={"TT": "validated", "EE": "pending", "TE": "pending"},
        propagator_norm_bound=3.0,
    )

    assert bundle.overlay.source_bridge_report is not None
    assert bundle.overlay.source_bridge_report.source_status == "adequate"
    assert bundle.bass_suggestion.source_status == "adequate"
    assert bundle.htt_caveats.channel_validity["EE"] == "pending"
    assert bundle.mio_fields.trace_source_adequacy == "adequate"
    assert bundle.publication_ready is False
    assert any(str(blocker).startswith("propagation_pending:") for blocker in bundle.publication_blockers)
    assert "BB remains outside trace-only validation" in bundle.overlay.public_caveat_snippet


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
