"""SK-06H regression tests for the VER2 HTT directional shell."""
from __future__ import annotations

import json

import pytest

from common.contracts import (
    ArtifactManifest,
    ObservableVector,
    PreferredAxis,
    SkySupport,
    SolverCoreOutput,
)
from htt.infer.null_competition import NullCompetitionHook


def _manifest(
    owner: str = "BASS",
    *,
    production_status: str = "production_candidate",
) -> ArtifactManifest:
    scope_by_owner = {
        "BASS": "canonical_BASS",
        "HTT": "htt",
        "MIO": "mio",
        "TSC": "tsc",
        "COMMON": "common",
    }
    return ArtifactManifest(
        artifact_id=f"{owner.lower()}.artifact",
        artifact_path=f"artifacts/{owner.lower()}.json",
        owner=owner,  # type: ignore[arg-type]
        implementation_scope=scope_by_owner[owner],  # type: ignore[arg-type]
        claim_tier="conditional",
        production_status=production_status,  # type: ignore[arg-type]
        created_by="test-suite",
        git_commit="abc123",
        config_hash="cfg1",
        input_hashes=["h1"],
        code_version="0.0-test",
        schema_version="ver2-v1",
    )


def _sky_support(
    *,
    selection_mode: str = "mock_calibrated",
    mock_coverage_status: str = "adequate",
) -> SkySupport:
    return SkySupport(
        selection_mode=selection_mode,
        sky_support_hash="sky-1",
        mask_hash="mask-1",
        mock_coverage_status=mock_coverage_status,
        scan_volume_hash="scan-1",
    )


def _observable_vector(
    *,
    owner: str = "BASS",
    sky_support: SkySupport | None = None,
) -> ObservableVector:
    return ObservableVector(
        ell_max=8,
        channels=("TT", "TE"),
        cl={"TT": [1.0, 0.5]},
        alm_features={"quadrupole_axis": {"l_deg": 264.0, "b_deg": 48.0}},
        biposh=None,
        template_fit={"atlas_ref": "template_morphology_atlas_v1.json"},
        covariance_features=None,
        scan_volume={"n_modes": 2},
        sky_support=sky_support or _sky_support(),
        manifest=_manifest(owner),
    )


def _solver_output(*, owner: str = "BASS") -> SolverCoreOutput:
    return SolverCoreOutput(
        alm_T=None,
        alm_E=None,
        alm_B=None,
        map_T=None,
        map_Q=None,
        map_U=None,
        deterministic_template={"template_kind": "bianchi_proxy"},
        anisotropic_covariance={"preferred_axis": [264.0, 48.0, 1.0]},
        metadata={
            "bianchi_type": "VIIh",
            "harmonic_basis": "lowell",
            "eb_sign_convention": "healpix",
            "multipole_cutoff": 8,
            "tilt_enabled": True,
            "thomson_mode": "skeleton",
        },
        manifest=_manifest(owner),
    )


def _preferred_axis(
    *,
    production_allowed: bool = True,
    source: str = "fiducial_posterior",
    selection_mode: str = "mock_calibrated",
) -> PreferredAxis:
    return PreferredAxis(
        l_deg=264.0,
        b_deg=48.0,
        label="posterior_axis",
        source=source,
        weight_mode="native_with_nuisance",
        selection_mode=selection_mode,
        production_allowed=production_allowed,
        provenance_hash="axis-1",
    )


def test_axis_gate_blocks_diagnostic_axis():
    from htt.infer.ver2_directional_shell import evaluate_production_axis_gate

    gate = evaluate_production_axis_gate(
        axis=_preferred_axis(
            production_allowed=False,
            source="raw_diagnostic",
            selection_mode="none",
        ),
        sky_support=_sky_support(),
    )
    assert gate.allowed is False
    assert "PreferredAxis.production_allowed=False" in gate.blocked_reasons
    assert any("fiducial_posterior" in reason for reason in gate.blocked_reasons)


def test_axis_gate_requires_adequate_mock_coverage():
    from htt.infer.ver2_directional_shell import evaluate_production_axis_gate

    gate = evaluate_production_axis_gate(
        axis=_preferred_axis(),
        sky_support=_sky_support(mock_coverage_status="pending"),
    )
    assert gate.allowed is False
    assert any("mock_coverage_status" in reason for reason in gate.blocked_reasons)


def test_response_library_keeps_local_boost_and_global_tilt_distinct():
    from htt.infer.ver2_directional_shell import DEFAULT_DIRECTIONAL_RESPONSE_LIBRARY

    library = {
        spec.hypothesis_id: spec
        for spec in DEFAULT_DIRECTIONAL_RESPONSE_LIBRARY.hypotheses
    }
    assert set(library) >= {
        "flrw_isotropic_null",
        "local_boost",
        "global_tilt",
        "bianchi_geometry",
        "systematic_template",
    }
    assert library["local_boost"].response_side != library["global_tilt"].response_side
    assert library["systematic_template"].claim_role == "systematic_control"


def test_policy_rejects_mio_merge_and_tsc_posterior_correction():
    from htt.infer.ver2_directional_shell import DirectionalInferencePolicy

    with pytest.raises(ValueError, match="MIO certificate semantics"):
        DirectionalInferencePolicy(allow_mio_certificate_merge=True)
    with pytest.raises(ValueError, match="TSC diagnostics"):
        DirectionalInferencePolicy(allow_tsc_posterior_correction=True)


def test_directional_shell_requires_bass_observable_owner():
    from htt.infer.ver2_directional_shell import build_directional_likelihood_inputs

    with pytest.raises(ValueError, match="must come from BASS"):
        build_directional_likelihood_inputs(
            observable_vector=_observable_vector(owner="HTT"),
            preferred_axis=_preferred_axis(),
            manifest=_manifest("HTT"),
        )


def test_build_ver2_directional_inputs_carries_solver_forward():
    from htt.integration.from_bass import build_ver2_directional_inputs

    shell = build_ver2_directional_inputs(
        _observable_vector(),
        _preferred_axis(),
        manifest=_manifest("HTT"),
    )
    assert shell.axis_gate.allowed is True
    assert shell.manifest is not None and shell.manifest.owner == "HTT"
    assert shell.evidence_hooks.matched_complexity_ref == "matched_complexity_report_v1.json"
    assert shell.evidence_hooks.matched_complexity.scope == "pre_inference_only"
    assert shell.evidence_hooks.null_competition.scope == "pre_posterior"
    assert shell.evidence_hooks.posterior_predictive_ref == "posterior_predictive_v1.json"
    assert shell.evidence_hooks.loocv_ref == "loocv_report_v1.json"
    assert shell.discrimination_matrix.hypotheses == ("local_boost", "global_tilt")
    assert any("SK-01S1 -> SK-03S3" in note for note in shell.carry_forward)


def test_build_posterior_bundle_preserves_htt_manifest(tmp_path):
    from htt.integration.to_mio import build_posterior_bundle

    results_path = tmp_path / "integrated_pipeline_results.json"
    results_path.write_text(
        json.dumps(
            {
                "departure": {
                    "FLRW_tilt": {
                        "layer_1_departure": {
                            "x": {"median": 0.2, "hpd_68": [0.1, 0.3], "hpd_95": [0.05, 0.35]}
                        },
                        "layer_2_occupancy": {"Q": {"median": 0.4, "hpd_68": [0.2, 0.5]}},
                        "layer_3_exceedance": {"Pi": {"0.05": 0.1, "0.1": 0.2, "0.01": 0.05}},
                    }
                },
                "evidence": {"FLRW_tilt": {"lnB": 5.0, "neff": 128}, "FLRW": {"lnB": 0.0}},
                "filling_fraction": {"F_S3_mc_median": 0.07, "F_S3_mc_68": [0.05, 0.09]},
            }
        ),
        encoding="utf-8",
    )

    manifest = _manifest("HTT")
    bundle = build_posterior_bundle(
        results_path=str(results_path),
        model="FLRW_tilt",
        manifest=manifest,
    )
    assert bundle.manifest == manifest
    assert bundle.model == "FLRW_tilt"
    assert bundle.is_cross_check_only is True


def test_directional_output_manifest_stays_diagnostic_without_live_hooks():
    from htt.infer.ver2_directional_shell import (
        assess_directional_readiness,
        build_directional_output_manifest,
        build_directional_likelihood_inputs,
    )

    shell = build_directional_likelihood_inputs(
        observable_vector=_observable_vector(),
        preferred_axis=_preferred_axis(),
    )
    readiness = assess_directional_readiness(shell)
    manifest = build_directional_output_manifest(
        inputs=shell,
        artifact_id="htt.directional.posterior.shell",
        artifact_path="artifacts/htt/directional_posterior_shell.json",
        model_name="FLRW_tilt",
        posterior_ref="results.json#departure/FLRW_tilt",
        evidence_ref="results.json#evidence/FLRW_tilt",
    )
    assert readiness.production_status == "diagnostic_only"
    assert "solver_coupled_wiring_pending" in readiness.caveats
    assert "null_competition_hook_pending" in readiness.caveats
    assert "posterior_predictive_hook_pending" in readiness.caveats
    assert "loocv_hook_pending" in readiness.caveats
    assert manifest.owner == "HTT"
    assert manifest.production_status == "diagnostic_only"
    assert "policy_firewall_intact" in manifest.passed_gates
    assert "solver_payload_ready" in manifest.failed_gates


def test_directional_output_manifest_blocks_without_null_mocks_once_other_gates_pass():
    from htt.infer.ver2_directional_shell import (
        assess_directional_readiness,
        build_directional_likelihood_inputs,
    )

    shell = build_directional_likelihood_inputs(
        observable_vector=_observable_vector(),
        preferred_axis=_preferred_axis(),
        solver_core_output=_solver_output(),
        posterior_predictive_ready=True,
        loocv_ready=True,
    )
    readiness = assess_directional_readiness(shell)
    assert readiness.production_status == "blocked_missing_null_mocks"
    assert "null_competition_ready" in readiness.failed_gates


def test_directional_output_manifest_reaches_production_candidate_with_live_hooks():
    from htt.infer.ver2_directional_shell import (
        assess_directional_readiness,
        build_directional_likelihood_inputs,
    )

    shell = build_directional_likelihood_inputs(
        observable_vector=_observable_vector(),
        preferred_axis=_preferred_axis(),
        solver_core_output=_solver_output(),
        null_competition=NullCompetitionHook(
            required_families=("registered_nulls",),
            fpr_threshold=0.10,
            ready_for_inference=True,
            worst_family="mask_leakage",
            worst_fpr=0.01,
        ),
        posterior_predictive_ready=True,
        loocv_ready=True,
        manifest=_manifest("HTT"),
    )
    readiness = assess_directional_readiness(shell)
    assert readiness.production_status == "production_candidate"
    assert "production_axis_ready" in readiness.passed_gates
    assert "null_competition_ready" in readiness.passed_gates
    assert "solver_payload_ready" in readiness.passed_gates
    assert "posterior_predictive_ready" in readiness.passed_gates
    assert "loocv_ready" in readiness.passed_gates


def test_build_posterior_bundle_auto_materializes_htt_manifest(tmp_path):
    from htt.integration.to_mio import build_posterior_bundle
    from htt.integration.from_bass import build_ver2_directional_inputs

    results_path = tmp_path / "integrated_pipeline_results.json"
    results_path.write_text(
        json.dumps(
            {
                "departure": {
                    "FLRW_tilt": {
                        "layer_1_departure": {
                            "x": {"median": 0.2, "hpd_68": [0.1, 0.3], "hpd_95": [0.05, 0.35]}
                        },
                        "layer_2_occupancy": {"Q": {"median": 0.4, "hpd_68": [0.2, 0.5]}},
                        "layer_3_exceedance": {"Pi": {"0.05": 0.1, "0.1": 0.2, "0.01": 0.05}},
                    }
                },
                "evidence": {"FLRW_tilt": {"lnB": 5.0, "neff": 128}, "FLRW": {"lnB": 0.0}},
                "filling_fraction": {"F_S3_mc_median": 0.07, "F_S3_mc_68": [0.05, 0.09]},
            }
        ),
        encoding="utf-8",
    )

    shell = build_ver2_directional_inputs(
        _observable_vector(),
        _preferred_axis(),
        solver_core_output=_solver_output(),
        null_competition=NullCompetitionHook(
            required_families=("registered_nulls",),
            fpr_threshold=0.10,
            ready_for_inference=True,
            worst_family="mask_leakage",
            worst_fpr=0.01,
        ),
        posterior_predictive_ready=True,
        loocv_ready=True,
    )
    bundle = build_posterior_bundle(
        results_path=str(results_path),
        model="FLRW_tilt",
        directional_inputs=shell,
    )
    assert bundle.manifest is not None
    assert bundle.manifest.owner == "HTT"
    assert bundle.manifest.statistics_definitions["surface"] == "posterior_export_bundle"
    assert bundle.manifest.statistics_definitions["cross_check_only"] is True
    assert "mio_cross_check_only_export" in bundle.manifest.caveats
    assert bundle.is_cross_check_only is True


def test_directional_bridge_promotion_gate_is_closed_fail():
    from htt.bridge.metadata import directional_bridge_promotion_gate

    decision = directional_bridge_promotion_gate("v_tilt")
    assert decision.allowed is False
    assert decision.required_gate == "bridge_exploratory_only"
    assert "exploratory-only" in decision.reason
