from __future__ import annotations

import json
import math

import numpy as np
import pytest

from common.contracts import ClaimTier


_COMMAND = "python -m pytest tests/htt/test_survey_nulls.py -q"
_WORKTREE = "test-worktree"


def _sha(char: str) -> str:
    return "sha256:" + char * 64


def _audit():
    from htt.departure.response_overlap import build_response_overlap_audit

    return build_response_overlap_audit(
        local_boost_response=(1.0, 0.0),
        global_tilt_response=(0.0, 1.0),
        covariance=np.eye(2),
        observable_labels=("depth_coherence", "survey_axis_template"),
        artifact_id="htt-response-overlap-pr062-fixture",
        artifact_path="memory://htt-response-overlap-pr062-fixture.json",
        input_hashes=(_sha("a"),),
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
        sky_support_status="pr040_sky_support_attached",
        mask_status="mask_hash_recorded",
        covariance_status="diagnostic_covariance_supplied",
        null_mock_status="rank_audit_without_null_fpr",
    )


def _rank_deficient_audit():
    from htt.departure.response_overlap import build_response_overlap_audit

    return build_response_overlap_audit(
        local_boost_response=(1.0, 0.0),
        global_tilt_response=(2.0, 0.0),
        covariance=np.eye(2),
        observable_labels=("depth_coherence", "survey_axis_template"),
        artifact_id="htt-response-overlap-pr062-rank-deficient",
        artifact_path="memory://htt-response-overlap-pr062-rank-deficient.json",
        input_hashes=(_sha("a"),),
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
        sky_support_status="pr040_sky_support_attached",
        mask_status="mask_hash_recorded",
        covariance_status="diagnostic_covariance_supplied",
        null_mock_status="rank_audit_without_null_fpr",
    )


def _depth_bins():
    from htt.nulls import DepthBinSpec

    return (
        DepthBinSpec(
            label="near",
            z_min=0.0,
            z_max=0.025,
            distance_mpc_min=0.0,
            distance_mpc_max=100.0,
            response_weight=1.0,
        ),
        DepthBinSpec(
            label="mid",
            z_min=0.025,
            z_max=0.075,
            distance_mpc_min=100.0,
            distance_mpc_max=300.0,
            response_weight=0.7,
        ),
        DepthBinSpec(
            label="far",
            z_min=0.075,
            z_max=0.15,
            distance_mpc_min=300.0,
            distance_mpc_max=650.0,
            response_weight=0.35,
        ),
    )


def _config(**overrides):
    from htt.nulls import LocalBoostNullConfig

    values = {
        "n_mocks": 40,
        "seed": 62062,
        "depth_bins": _depth_bins(),
        "target_direction": (1.0, 0.0, 0.0),
        "gf_threshold": 1.08,
        "direction_threshold_deg": 75.0,
        "look_elsewhere_trials": 2,
        "max_false_positive_rate": 0.2,
        "amplitude_beta_mean": 1.2e-3,
        "amplitude_beta_sigma": 1.5e-4,
        "direction_jitter_sigma": 0.045,
        "gf_beta_scale": 1.0e-3,
        "sky_support_hash": _sha("1"),
        "mask_hash": _sha("2"),
        "scan_volume_hash": _sha("3"),
        "config_hash": _sha("4"),
        "input_hashes": (_sha("5"),),
        "covariance_status": "diagnostic_covariance_supplied",
        "sky_support_status": "pr040_sky_support_attached",
        "generating_command": _COMMAND,
        "worktree_state": _WORKTREE,
        "git_commit": None,
    }
    values.update(overrides)
    return LocalBoostNullConfig(**values)


def _selection_metadata(**overrides):
    from htt.nulls import SelectionResponseMetadata

    values = {
        "selection_function_id": "catwise_depth_completeness_v1",
        "selection_function_hash": _sha("6"),
        "selection_metadata_hash": _sha("7"),
        "depth_response_hash": _sha("8"),
        "source_catalog": "calibration_fixture",
        "completeness_status": "depth_dependent_selection_metadata_attached",
        "completeness_axis": (1.0, 0.0, 0.0),
        "depth_response_label": "near_to_far_monotone_completeness_gradient",
    }
    values.update(overrides)
    return SelectionResponseMetadata(**values)


def _survey_axis_metadata(**overrides):
    from htt.nulls import SurveyAxisMetadata

    values = {
        "survey_axis_id": "shared_ecliptic_scan_axis_v1",
        "survey_axis_hash": _sha("9"),
        "survey_axis": (1.0, 0.0, 0.0),
        "axis_origin": "survey_window_calibration_fixture",
        "coordinate_frame": "galactic_cartesian_unit_vector",
        "coherence_status": "survey_axis_coherence_calibration_attached",
    }
    values.update(overrides)
    return SurveyAxisMetadata(**values)


def _assert_claim_safe(payload: dict[str, object]) -> None:
    text = json.dumps(payload, sort_keys=True).lower()
    assert "posterior" not in text
    assert "bayes" not in text
    assert "native solver result" not in text
    assert "family identified" not in text
    assert "geometry detected" not in text


def test_selection_response_depth_null_is_runnable_and_carries_selection_metadata():
    from htt.nulls import SelectionResponseDepthNull

    config = _config()
    metadata = _selection_metadata()
    first = SelectionResponseDepthNull(config, selection_metadata=metadata).generate()
    second = SelectionResponseDepthNull(config, selection_metadata=metadata).generate()

    assert first.to_payload() == second.to_payload()
    assert first.null_model_id == "selection_response_depth"
    assert first.owner == "HTT"
    assert first.claim_tier == "diagnostic_only"
    assert first.transfer_source == "none"
    assert len(first.samples) == first.config.n_mocks * len(first.config.depth_bins)
    assert any(sample.triggered for sample in first.samples)

    payload = first.to_payload()
    assert payload["manifest"]["owner"] == "HTT"
    assert payload["manifest"]["implementation_scope"] == "htt"
    assert payload["manifest"]["claim_tier"] == "diagnostic_only"
    assert payload["manifest"]["production_status"] == "diagnostic_only"
    assert payload["manifest"]["input_hashes"] == [
        _sha("5"),
        metadata.selection_metadata_hash,
        metadata.selection_function_hash,
        metadata.depth_response_hash,
    ]
    assert payload["metadata"]["selection_response"]["selection_function_id"] == (
        "catwise_depth_completeness_v1"
    )
    assert payload["metadata"]["selection_response"]["selection_metadata_hash"] == (
        metadata.selection_metadata_hash
    )
    assert payload["metadata"]["selection_response"]["completeness_axis"] == [
        1.0,
        0.0,
        0.0,
    ]
    assert payload["metadata"]["null_model_scope"] == "selection_response_depth_null"
    assert payload["metadata"]["physical_scope"] == "observer_side_survey_selection"
    assert payload["distributions"]["g_f"]["count"] == len(first.samples)
    assert sorted(payload["distributions"]["g_f"]["by_depth"]) == [
        "far",
        "mid",
        "near",
    ]

    for sample in first.samples:
        assert math.isclose(sample.direction_norm, 1.0, rel_tol=0.0, abs_tol=1e-12)
        assert sample.g_f >= 1.0

    _assert_claim_safe(payload)


def test_survey_axis_coherence_null_is_distinct_and_exposes_axis_metadata():
    from htt.nulls import SurveyAxisCoherenceNull

    bank = SurveyAxisCoherenceNull(
        _config(seed=62063),
        selection_metadata=_selection_metadata(),
        survey_axis_metadata=_survey_axis_metadata(),
    ).generate()
    payload = bank.to_payload()

    assert bank.null_model_id == "survey_axis_coherence"
    assert payload["metadata"]["null_model_scope"] == "survey_axis_coherence_null"
    assert payload["metadata"]["physical_scope"] == "observer_side_survey_axis"
    assert payload["metadata"]["survey_axis"]["survey_axis_id"] == (
        "shared_ecliptic_scan_axis_v1"
    )
    assert payload["metadata"]["survey_axis"]["survey_axis_hash"] == _sha("9")
    assert payload["metadata"]["selection_response"]["selection_metadata_hash"] == _sha("7")
    assert payload["metadata"]["axis_coherence"]["axis_alignment_status"] == (
        "survey_axis_directional_null"
    )
    assert len({sample.mock_index for sample in bank.samples}) == bank.config.n_mocks
    assert {sample.depth_label for sample in bank.samples} == {"near", "mid", "far"}
    assert any(sample.triggered for sample in bank.samples)
    assert payload["distributions"]["direction"]["mean_resultant_length"] > 0.5
    assert (
        payload["distributions"]["direction"]["angular_separation_to_target_deg"]["median"]
        < 35.0
    )

    _assert_claim_safe(payload)


def test_survey_systematic_fpr_report_binds_rank_selection_metadata_and_hashes():
    from htt.nulls import (
        SurveyAxisCoherenceNull,
        build_survey_systematic_null_fpr_report,
        evaluate_survey_systematic_null_gate,
    )

    bank = SurveyAxisCoherenceNull(
            _config(
                gf_threshold=50.0,
                direction_threshold_deg=10.0,
                look_elsewhere_trials=1,
                max_false_positive_rate=0.1,
            ),
        selection_metadata=_selection_metadata(),
        survey_axis_metadata=_survey_axis_metadata(),
    ).generate()
    report = build_survey_systematic_null_fpr_report(
        bank,
        response_overlap_audit=_audit(),
    )
    payload = report.to_metadata()
    event_count = sum(
        1
        for mock_index in range(bank.config.n_mocks)
        if any(sample.triggered for sample in bank.samples if sample.mock_index == mock_index)
    )

    assert report.false_positive_count == event_count
    assert payload["artifact_name"] == "survey_systematic_null_fpr_report_v1"
    assert payload["false_positive_rate"]["raw"] == pytest.approx(
        event_count / bank.config.n_mocks
    )
    assert payload["rank_status"]["rank_status"] == "full_rank"
    assert payload["selection_response"]["selection_metadata_hash"] == _sha("7")
    assert payload["survey_axis"]["survey_axis_hash"] == _sha("9")
    assert payload["manifest"]["input_hashes"] == [
        _sha("5"),
        _sha("7"),
        _sha("6"),
        _sha("8"),
        _sha("9"),
        _audit().as_payload()["config_hash"],
    ]
    assert payload["input_hashes"] == payload["manifest"]["input_hashes"]
    assert "survey_systematic_null_fpr_below_threshold" in (
        payload["manifest"]["passed_gates"]
    )
    assert report.allowed_claim_tier == ClaimTier.CONDITIONAL

    decision = evaluate_survey_systematic_null_gate(
        report,
        requested_claim_tier=ClaimTier.CONDITIONAL,
        config_hash=bank.config.config_hash,
        input_hashes=bank.input_hashes,
        report_hash=report.report_hash,
        response_overlap_config_hash=_audit().as_payload()["config_hash"],
        selection_metadata_hash=_sha("7"),
        survey_axis_hash=_sha("9"),
        require_external_bindings=True,
    )
    assert decision.allowed is True
    assert decision.blocked_reasons == ()

    stale = evaluate_survey_systematic_null_gate(
        report,
        requested_claim_tier=ClaimTier.CONDITIONAL,
        selection_metadata_hash=_sha("b"),
        survey_axis_hash=_sha("9"),
    )
    assert stale.allowed is False
    assert "selection_metadata_hash_mismatch" in stale.blocked_reasons


def test_survey_systematic_gate_fails_closed_for_missing_high_fpr_and_rank_blockers():
    from htt.nulls import (
        SelectionResponseDepthNull,
        build_survey_systematic_null_fpr_report,
        evaluate_survey_systematic_null_gate,
    )

    missing = evaluate_survey_systematic_null_gate(
        None,
        requested_claim_tier=ClaimTier.CONDITIONAL,
    )
    assert missing.allowed is False
    assert "survey_systematic_null_fpr_missing" in missing.blocked_reasons

    high_fpr_bank = SelectionResponseDepthNull(
        _config(max_false_positive_rate=0.01, direction_threshold_deg=180.0),
        selection_metadata=_selection_metadata(),
    ).generate()
    high_fpr_report = build_survey_systematic_null_fpr_report(
        high_fpr_bank,
        response_overlap_audit=_audit(),
    )
    high_fpr = evaluate_survey_systematic_null_gate(
        high_fpr_report,
        requested_claim_tier=ClaimTier.CONDITIONAL,
    )
    assert high_fpr.allowed is False
    assert "survey_systematic_null_fpr_exceeds_threshold" in high_fpr.blocked_reasons

    rank_report = build_survey_systematic_null_fpr_report(
        SelectionResponseDepthNull(_config(), selection_metadata=_selection_metadata()).generate(),
        response_overlap_audit=_rank_deficient_audit(),
    )
    rank_decision = evaluate_survey_systematic_null_gate(
        rank_report,
        requested_claim_tier=ClaimTier.CONDITIONAL,
    )
    assert rank_decision.allowed is False
    assert "response_overlap_rank_not_full" in rank_decision.blocked_reasons

    covariance_report = build_survey_systematic_null_fpr_report(
        SelectionResponseDepthNull(
            _config(covariance_status="diagnostic_covariance_pending"),
            selection_metadata=_selection_metadata(),
        ).generate(),
        response_overlap_audit=_audit(),
    )
    covariance_decision = evaluate_survey_systematic_null_gate(
        covariance_report,
        requested_claim_tier=ClaimTier.CONDITIONAL,
    )
    assert covariance_decision.allowed is False
    assert "covariance_status_not_supported" in covariance_decision.blocked_reasons

    permissive_ceiling_report = build_survey_systematic_null_fpr_report(
        SelectionResponseDepthNull(
            _config(max_false_positive_rate=1.0),
            selection_metadata=_selection_metadata(),
        ).generate(),
        response_overlap_audit=_audit(),
    )
    permissive_ceiling = evaluate_survey_systematic_null_gate(
        permissive_ceiling_report,
        requested_claim_tier=ClaimTier.CONDITIONAL,
    )
    assert permissive_ceiling.allowed is False
    assert "survey_systematic_null_fpr_ceiling_not_strict" in (
        permissive_ceiling.blocked_reasons
    )

    pending_status_report = build_survey_systematic_null_fpr_report(
        SelectionResponseDepthNull(
            _config(gf_threshold=10.0, direction_threshold_deg=35.0),
            selection_metadata=_selection_metadata(completeness_status="pending"),
        ).generate(),
        response_overlap_audit=_audit(),
    )
    pending_status = evaluate_survey_systematic_null_gate(
        pending_status_report,
        requested_claim_tier=ClaimTier.CONDITIONAL,
    )
    assert pending_status.allowed is False
    assert "selection_completeness_status_not_attached" in (
        pending_status.blocked_reasons
    )


def test_survey_nulls_reject_invalid_metadata_and_keep_legacy_registry_stable():
    from htt.nulls import (
        NULL_REGISTRY,
        SelectionResponseDepthNull,
        SelectionResponseMetadata,
        SurveyAxisMetadata,
    )

    assert set(NULL_REGISTRY) == {
        "scanning_law",
        "mask_leakage",
        "clustering",
        "selection_response",
        "survey_axis",
    }

    with pytest.raises(ValueError, match="selection_metadata_hash"):
        _selection_metadata(selection_metadata_hash="not-a-sha")

    with pytest.raises(ValueError, match="completeness_axis"):
        _selection_metadata(completeness_axis=(0.0, 0.0, 0.0))

    with pytest.raises(ValueError, match="survey_axis"):
        _survey_axis_metadata(survey_axis=(0.0, 0.0, 0.0))

    with pytest.raises(TypeError, match="SelectionResponseMetadata"):
        SelectionResponseDepthNull(_config(), selection_metadata=object()).generate()

    with pytest.raises(ValueError, match="selection_function_id"):
        SelectionResponseMetadata(
            selection_function_id=" ",
            selection_function_hash=_sha("6"),
            selection_metadata_hash=_sha("7"),
            depth_response_hash=_sha("8"),
            source_catalog="fixture",
            completeness_status="attached",
            completeness_axis=(1.0, 0.0, 0.0),
            depth_response_label="fixture",
        )

    with pytest.raises(ValueError, match="survey_axis_id"):
        SurveyAxisMetadata(
            survey_axis_id=" ",
            survey_axis_hash=_sha("9"),
            survey_axis=(1.0, 0.0, 0.0),
            axis_origin="fixture",
            coordinate_frame="galactic_cartesian_unit_vector",
            coherence_status="attached",
        )
