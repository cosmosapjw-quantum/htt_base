from __future__ import annotations

import pytest

from common.contracts import (
    ArtifactManifest,
    AtlasEntryLite,
    ObservableVector,
    PreferredAxis,
    SkySupport,
    TscAdequacyOverlay,
)
from htt.infer.likelihood_scope_guard import (
    build_directional_likelihood_input,
    evaluate_likelihood_scope,
    guard_tsc_posterior_correction,
)
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
        input_hashes=["x"],
        code_version="0.0-test",
        schema_version="ver2-v1",
    )


def _observable() -> ObservableVector:
    return ObservableVector(
        ell_max=8,
        channels=("TT", "TE", "EE", "BB"),
        cl={},
        alm_features={},
        biposh=None,
        template_fit=None,
        covariance_features=None,
        scan_volume={},
        sky_support=SkySupport(
            selection_mode="mock_calibrated",
            sky_support_hash="sky123",
            mask_hash="mask123",
            mock_coverage_status="passed",
        ),
        manifest=_manifest("BASS", "canonical_BASS"),
    )


def _atlas() -> AtlasEntryLite:
    return AtlasEntryLite(
        atlas_id="atlas1",
        theory_family="BianchiI",
        geometry_params={},
        kinematic_params={},
        tilt_params={},
        solver_output_ref="solver:1",
        observable_vector_ref="obs:1",
        response_blocks={},
        validity_domain={},
        interpolation_status="skeleton",
        manifest=_manifest("BASS", "canonical_BASS"),
    )


def _overlay_pending() -> TscAdequacyOverlay:
    man = _manifest("TSC", "tsc")
    from common.contracts import (
        TscChannelAdequacyBudget,
        TscDomainReport,
        TscResidualReport,
        TscUpgradeRecommendation,
    )

    return TscAdequacyOverlay(
        domain_report=TscDomainReport(
            chart="one_field",
            theta_min=1.0,
            eta_max=None,
            be_eta_nonpositive=None,
            weight_simplex_ok=True,
            jacobian_sigma_min=None,
            domain_margin=1.0,
            status="valid_one_field",
            blocking_reasons=tuple(),
            manifest=man,
        ),
        residual_report=TscResidualReport(
            chart="one_field",
            laguerre_n_ge_2_norm=0.0,
            ambient_defect_rate=None,
            projected_defect_estimate=None,
            onefield_residual=0.0,
            twofield_residual=None,
            eta_tangent_fraction=None,
            trace_residual_q_tr=None,
            spin2_residual=None,
            high_residual=None,
            residual_origin="unknown",
            labels=tuple(),
            manifest=man,
        ),
        source_bridge_report=None,
        channel_budgets=(
            TscChannelAdequacyBudget(
                channel="EE",
                trace_budget=0.1,
                spin2_budget=0.2,
                high_budget=None,
                source_to_field_bound=None,
                spectrum_bound_linear=0.1,
                spectrum_bound_quadratic=None,
                source_status="adequate",
                propagation_status="pending",
                claim_ceiling="conditional",
                labels=("trace_ok__spin2_required",),
                manifest=man,
            ),
        ),
        upgrade_recommendation=TscUpgradeRecommendation(
            current_chart="one_field",
            recommended_chart="two_field",
            reason="eta_tangent_false_trigger",
            severity="warn",
            dwell_time_required=1.0,
            hysteresis_state="pending_upgrade",
            labels=("two_field_recommended__one_field_warn",),
            manifest=man,
        ),
        no_overclaim_flags={},
        quarantine_reasons=tuple(),
        public_caveat_snippet="pending",
        manifest=man,
    )


def test_rejects_mio_certificate_merge():
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
        input_data_hashes=["x"],
        manifest=_manifest("MIO", "mio"),
    )
    with pytest.raises(TypeError, match="MioCertificate"):
        build_directional_likelihood_input(
            observable_vector=_observable(),
            external_artifacts=(cert,),
        )


def test_blocks_spin2_channels_when_tsc_pending():
    bundle = build_directional_likelihood_input(
        observable_vector=_observable(),
        atlas_entry=_atlas(),
        preferred_axis=PreferredAxis(
            l_deg=264.0,
            b_deg=48.0,
            label="diag",
            source="raw_diagnostic",
            weight_mode="native",
            selection_mode="none",
        ),
        tsc_overlay=_overlay_pending(),
        required_channels=("EE",),
        scalar_only_geometry=True,
    )
    decision = evaluate_likelihood_scope(bundle)
    assert not decision.allowed
    assert any(
        reason.startswith("missing_spin2_validation")
        for reason in decision.blocking_reasons
    )
    assert "scalar_only_discrimination_insufficient" in decision.caveats


def test_guard_tsc_posterior_correction_is_hard_block():
    with pytest.raises(RuntimeError, match="disabled by default"):
        guard_tsc_posterior_correction(enabled=True)
