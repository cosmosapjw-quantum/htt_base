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
from htt.infer.matched_complexity import MatchedComplexityHook
from htt.infer.null_competition import NullCompetitionHook
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
            mock_coverage_status="adequate",
            scan_volume_hash="scan123",
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
                channel="TT",
                trace_budget=0.1,
                spin2_budget=None,
                high_budget=None,
                source_to_field_bound=None,
                spectrum_bound_linear=None,
                spectrum_bound_quadratic=None,
                source_status="adequate",
                propagation_status="validated",
                claim_ceiling="exploratory",
                labels=(
                    "source_adequate__propagation_validated",
                    "observable_bridge_missing_state_residual",
                ),
                manifest=man,
            ),
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
    with pytest.raises(TypeError, match="MIO certificates are diagnostic-only"):
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
    assert bundle.tsc_caveats is not None
    assert bundle.tsc_caveats.required_channels == ("EE",)
    assert "source_bridge_missing" in bundle.tsc_caveats.publication_blockers
    assert "propagation_pending:EE" in bundle.tsc_caveats.publication_blockers
    decision = evaluate_likelihood_scope(bundle)
    assert not decision.allowed
    assert any(
        reason.startswith("missing_spin2_validation")
        for reason in decision.blocking_reasons
    )
    assert "scalar_only_discrimination_insufficient" in decision.caveats


def test_blocks_tt_when_tsc_claim_ceiling_is_only_exploratory():
    bundle = build_directional_likelihood_input(
        observable_vector=_observable(),
        tsc_overlay=_overlay_pending(),
        required_channels=("TT",),
    )
    assert bundle.tsc_caveats is not None
    assert bundle.tsc_caveats.required_channels == ("TT",)
    assert "source_bridge_missing" in bundle.tsc_caveats.publication_blockers
    assert (
        "claim_ceiling_insufficient:TT=exploratory"
        in bundle.tsc_caveats.publication_blockers
    )
    decision = evaluate_likelihood_scope(bundle)
    assert decision.allowed is False
    assert "tsc_claim_ceiling_insufficient:TT=exploratory" in decision.blocking_reasons
    assert "observable_bridge_missing_state_residual" in decision.caveats


def test_matched_complexity_failure_is_a_hard_block():
    bundle = build_directional_likelihood_input(
        observable_vector=_observable(),
        matched_complexity_hook=MatchedComplexityHook(
            controls_required=("C1", "C2", "C3"),
            overall_pass=False,
            violations=("prior_width_mismatch",),
        ),
        null_competition_hook=NullCompetitionHook(
            required_families=("mask_leakage",),
            fpr_threshold=0.10,
            ready_for_inference=True,
            worst_family="mask_leakage",
            worst_fpr=0.01,
        ),
    )
    decision = evaluate_likelihood_scope(bundle)
    assert decision.allowed is False
    assert "matched_complexity_failed" in decision.blocking_reasons


def test_integration_helper_binds_common_contracts_without_solver_output():
    from htt.integration.from_bass import ingest_ver2_directional_inputs

    bundle = ingest_ver2_directional_inputs(
        _observable(),
        required_channels=("TT",),
    )
    decision = evaluate_likelihood_scope(bundle)
    assert bundle.observable_vector.manifest.owner == "BASS"
    assert decision.allowed is True
    assert "null_competition_hook_pending" in decision.caveats
    assert "solver_coupled_wiring_pending" in decision.caveats


def test_guard_tsc_posterior_correction_is_hard_block():
    with pytest.raises(RuntimeError, match="disabled by default"):
        guard_tsc_posterior_correction(enabled=True)
