from __future__ import annotations

import json
import math

import numpy as np
import pytest


_COMMAND = "python -m pytest tests/htt/test_local_global_mixture.py -q"
_WORKTREE = "test-worktree"


def _sha(char: str) -> str:
    return "sha256:" + char * 64


def _audit():
    from htt.departure.response_overlap import build_response_overlap_audit

    return build_response_overlap_audit(
        local_boost_response=(1.0, 0.0, 0.2),
        global_tilt_response=(0.0, 1.0, 0.2),
        covariance=np.diag((1.0, 1.2, 1.5)),
        observable_labels=("depth", "template", "survey_axis"),
        artifact_id="htt-response-overlap-pr063-fixture",
        artifact_path="memory://htt-response-overlap-pr063-fixture.json",
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
            z_max=0.03,
            distance_mpc_min=0.0,
            distance_mpc_max=120.0,
            response_weight=1.0,
        ),
        DepthBinSpec(
            label="mid",
            z_min=0.03,
            z_max=0.12,
            distance_mpc_min=120.0,
            distance_mpc_max=520.0,
            response_weight=0.45,
        ),
    )


def _null_config(**overrides):
    from htt.nulls import LocalBoostNullConfig

    values = {
        "n_mocks": 96,
        "seed": 63063,
        "depth_bins": _depth_bins(),
        "target_direction": (1.0, 0.0, 0.0),
        "gf_threshold": 1.0e9,
        "direction_threshold_deg": 3.0,
        "look_elsewhere_trials": 1,
        "max_false_positive_rate": 0.1,
        "amplitude_beta_mean": 1.0e-3,
        "amplitude_beta_sigma": 1.0e-4,
        "direction_jitter_sigma": 0.03,
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


def _selection_metadata():
    from htt.nulls import SelectionResponseMetadata

    return SelectionResponseMetadata(
        selection_function_id="pr063_selection_fixture",
        selection_function_hash=_sha("6"),
        selection_metadata_hash=_sha("7"),
        depth_response_hash=_sha("8"),
        source_catalog="calibration_fixture",
        completeness_status="depth_dependent_selection_metadata_attached",
        completeness_axis=(1.0, 0.0, 0.0),
        depth_response_label="near_to_mid_selection_response",
    )


def _survey_axis_metadata():
    from htt.nulls import SurveyAxisMetadata

    return SurveyAxisMetadata(
        survey_axis_id="pr063_survey_axis_fixture",
        survey_axis_hash=_sha("9"),
        survey_axis=(1.0, 0.0, 0.0),
        axis_origin="survey_window_calibration_fixture",
        coordinate_frame="galactic_cartesian_unit_vector",
        coherence_status="survey_axis_coherence_calibration_attached",
    )


def _local_fpr_report(audit=None):
    from htt.nulls import LocalBoostDepthNull, build_local_boost_null_fpr_report

    resolved_audit = _audit() if audit is None else audit
    bank = LocalBoostDepthNull(_null_config()).generate()
    return build_local_boost_null_fpr_report(
        bank,
        response_overlap_audit=resolved_audit,
    )


def _survey_fpr_report(audit=None):
    from htt.nulls import (
        SurveyAxisCoherenceNull,
        build_survey_systematic_null_fpr_report,
    )

    resolved_audit = _audit() if audit is None else audit
    bank = SurveyAxisCoherenceNull(
        _null_config(seed=63064),
        selection_metadata=_selection_metadata(),
        survey_axis_metadata=_survey_axis_metadata(),
    ).generate()
    return build_survey_systematic_null_fpr_report(
        bank,
        response_overlap_audit=resolved_audit,
    )


def _blocks():
    from htt.departure.local_global_mixture import LocalGlobalMixtureBlock

    return (
        LocalGlobalMixtureBlock(
            name="observer_local_boost",
            kind="local_boost",
            response=(1.0, 0.0, 0.2),
            parameter_name="beta_local",
            field_id="observer_local_beta_field",
        ),
        LocalGlobalMixtureBlock(
            name="background_global_tilt",
            kind="global_tilt",
            response=(0.0, 1.0, 0.2),
            parameter_name="beta_global",
            field_id="matter_frame_global_beta_field",
        ),
        LocalGlobalMixtureBlock(
            name="survey_window_axis",
            kind="survey_systematic",
            response=(0.18, -0.12, 0.5),
            parameter_name="beta_survey_axis",
            field_id="survey_axis_nuisance_field",
        ),
        LocalGlobalMixtureBlock(
            name="diagonal_noise_floor",
            kind="noise",
            response=(1.0, 1.0, 1.0),
            parameter_name="sigma_noise",
            field_id="noise_variance_field",
        ),
    )


def test_mixture_likelihood_separates_blocks_and_generates_functionals():
    from htt.departure.local_global_mixture import (
        LocalGlobalMixtureSpec,
        build_local_global_mixture_report,
    )

    audit = _audit()
    local_report = _local_fpr_report(audit)
    survey_report = _survey_fpr_report(audit)
    spec = LocalGlobalMixtureSpec(
        observable_vector=(0.16, -0.03, 0.08),
        covariance=np.diag((0.9, 1.1, 1.4)),
        blocks=_blocks(),
        response_overlap_audit=audit,
        local_null_fpr_report=local_report,
        survey_systematic_null_fpr_report=survey_report,
        local_null_report_hash=local_report.report_hash,
        survey_systematic_null_config_hash=survey_report.bank.config.config_hash,
        survey_systematic_null_input_hashes=survey_report.bank.input_hashes,
        survey_systematic_null_report_hash=survey_report.report_hash,
        response_overlap_config_hash=audit.manifest.config_hash,
        selection_metadata_hash=survey_report.bank.selection_metadata.selection_metadata_hash,
        survey_axis_hash=survey_report.bank.survey_axis_metadata.survey_axis_hash,
        artifact_id="htt.pr063.local_global_mixture",
        config_hash=_sha("c"),
        input_hashes=(_sha("d"),),
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )
    report = build_local_global_mixture_report(
        spec,
        parameter_values={
            "beta_local": 0.10,
            "beta_global": -0.06,
            "beta_survey_axis": 0.03,
            "sigma_noise": 0.04,
        },
    )
    payload = report.as_payload()

    assert report.evaluation_status == "ready_diagnostic_likelihood"
    assert math.isfinite(report.total_log_likelihood)
    assert payload["owner"] == "HTT"
    assert payload["implementation_scope"] == "htt"
    assert payload["claim_tier"] == "conditional"
    assert payload["production_status"] == "diagnostic_only"
    assert payload["transfer_source"] == "none"
    assert set(payload["blocks"]) == {
        "local_boost",
        "global_tilt",
        "survey_systematic",
        "noise",
    }
    assert payload["blocks"]["local_boost"]["field_id"] != (
        payload["blocks"]["global_tilt"]["field_id"]
    )
    assert payload["primitive_parameters"] == [
        "beta_local",
        "beta_global",
        "beta_survey_axis",
        "sigma_noise",
    ]
    generated = payload["generated_functionals"]
    assert "fit_attenuation_score" in generated
    assert "gaussian_density_score" in generated
    assert "survey_penalized_fit_score" in generated
    assert generated["canonical_xqpi_fg_labels_used"] is False
    assert "F_total" not in generated
    assert "G_total" not in generated
    assert "G_F" not in generated
    assert "F_total" not in payload["primitive_parameters"]
    assert "G_F" not in payload["primitive_parameters"]
    assert payload["sky_support_status"] == "not_directional"
    assert payload["null_mock_status"] == (
        "local_and_survey_systematic_null_fpr_prerequisites_recorded"
    )
    assert payload["git_commit_or_worktree_state"] == _WORKTREE
    assert "local_null_fpr_gate" in payload["manifest"]["statistics_definitions"]
    assert (
        "full_local_global_survey_design_rank_gate"
        in payload["manifest"]["statistics_definitions"]
    )
    assert (
        "response_overlap_audit_response_consistency_gate"
        in payload["manifest"]["statistics_definitions"]
    )
    assert local_report.report_hash in payload["manifest"]["input_hashes"]
    assert survey_report.report_hash in payload["manifest"]["input_hashes"]
    assert audit.manifest.config_hash in payload["manifest"]["input_hashes"]

    text = json.dumps(payload, sort_keys=True).lower()
    assert "mio posterior" not in text
    assert "native solver result" not in text
    assert "family identified" not in text
    assert "geometry detected" not in text


def test_report_payload_satisfies_manifest_validator():
    from common.artifact_manifest import validate_manifest_payload
    from htt.departure.local_global_mixture import (
        LocalGlobalMixtureSpec,
        build_local_global_mixture_report,
    )

    audit = _audit()
    local_report = _local_fpr_report(audit)
    survey_report = _survey_fpr_report(audit)
    spec = LocalGlobalMixtureSpec(
        observable_vector=(0.16, -0.03, 0.08),
        covariance=np.diag((0.9, 1.1, 1.4)),
        blocks=_blocks(),
        response_overlap_audit=audit,
        local_null_fpr_report=local_report,
        survey_systematic_null_fpr_report=survey_report,
        local_null_report_hash=local_report.report_hash,
        survey_systematic_null_config_hash=survey_report.bank.config.config_hash,
        survey_systematic_null_input_hashes=survey_report.bank.input_hashes,
        survey_systematic_null_report_hash=survey_report.report_hash,
        response_overlap_config_hash=audit.manifest.config_hash,
        selection_metadata_hash=survey_report.bank.selection_metadata.selection_metadata_hash,
        survey_axis_hash=survey_report.bank.survey_axis_metadata.survey_axis_hash,
        artifact_id="htt.pr063.local_global_mixture.manifest",
        config_hash=_sha("m"),
        input_hashes=(_sha("n"),),
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )
    report = build_local_global_mixture_report(
        spec,
        parameter_values={
            "beta_local": 0.10,
            "beta_global": -0.06,
            "beta_survey_axis": 0.03,
            "sigma_noise": 0.04,
        },
    )

    assert validate_manifest_payload(
        report.as_payload(),
        manifest_path="memory://pr063-local-global-mixture.json",
    ) == ()


def test_shared_local_and_global_beta_field_is_rejected():
    from htt.departure.local_global_mixture import LocalGlobalMixtureBlock

    blocks = list(_blocks())
    blocks[1] = LocalGlobalMixtureBlock(
        name="bad_global_tilt",
        kind="global_tilt",
        response=(0.0, 1.0, 0.0),
        parameter_name="beta_global",
        field_id=blocks[0].field_id,
    )

    with pytest.raises(ValueError, match="single beta field"):
        LocalGlobalMixtureBlock.require_collection(tuple(blocks))


def test_all_mixture_field_ids_are_distinct():
    from htt.departure.local_global_mixture import LocalGlobalMixtureBlock

    blocks = list(_blocks())
    blocks[2] = LocalGlobalMixtureBlock(
        name="bad_survey_field",
        kind="survey_systematic",
        response=(0.18, -0.12, 0.5),
        parameter_name="beta_survey_axis",
        field_id=blocks[3].field_id,
    )

    with pytest.raises(ValueError, match="distinct field IDs"):
        LocalGlobalMixtureBlock.require_collection(tuple(blocks))


def test_functionals_are_rejected_as_primitive_parameters():
    from htt.departure.local_global_mixture import LocalGlobalMixtureBlock

    with pytest.raises(ValueError, match="generated functional"):
        LocalGlobalMixtureBlock(
            name="bad_functional_input",
            kind="local_boost",
            response=(1.0, 0.0, 0.0),
            parameter_name="G_F",
            field_id="observer_local_beta_field",
        )


def test_missing_gates_blocks_report_without_likelihood_value():
    from htt.departure.local_global_mixture import (
        LocalGlobalMixtureSpec,
        build_local_global_mixture_report,
    )

    audit = _audit()
    spec = LocalGlobalMixtureSpec(
        observable_vector=(0.16, -0.03, 0.08),
        covariance=np.diag((0.9, 1.1, 1.4)),
        blocks=_blocks(),
        response_overlap_audit=audit,
        local_null_fpr_report=None,
        survey_systematic_null_fpr_report=None,
        artifact_id="htt.pr063.local_global_mixture.blocked",
        config_hash=_sha("e"),
        input_hashes=(_sha("f"),),
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )

    report = build_local_global_mixture_report(
        spec,
        parameter_values={
            "beta_local": 0.10,
            "beta_global": -0.06,
            "beta_survey_axis": 0.03,
            "sigma_noise": 0.04,
        },
    )

    assert report.evaluation_status == "blocked_missing_prerequisites"
    assert report.total_log_likelihood is None
    assert "local_boost_null_fpr_missing" in report.blocked_reasons
    assert "survey_systematic_null_fpr_missing" in report.blocked_reasons
    assert report.manifest.claim_tier.value == "blocked"
    assert report.manifest.production_status == "blocked_missing_null_mocks"


def test_audit_responses_must_match_mixture_blocks():
    from htt.departure.local_global_mixture import (
        LocalGlobalMixtureBlock,
        LocalGlobalMixtureSpec,
        build_local_global_mixture_report,
    )

    audit = _audit()
    local_report = _local_fpr_report(audit)
    survey_report = _survey_fpr_report(audit)
    blocks = list(_blocks())
    blocks[1] = LocalGlobalMixtureBlock(
        name="mismatched_global_tilt",
        kind="global_tilt",
        response=(0.0, 1.0, 0.4),
        parameter_name="beta_global",
        field_id="matter_frame_global_beta_field",
    )
    spec = LocalGlobalMixtureSpec(
        observable_vector=(0.16, -0.03, 0.08),
        covariance=np.diag((0.9, 1.1, 1.4)),
        blocks=tuple(blocks),
        response_overlap_audit=audit,
        local_null_fpr_report=local_report,
        survey_systematic_null_fpr_report=survey_report,
        local_null_report_hash=local_report.report_hash,
        survey_systematic_null_config_hash=survey_report.bank.config.config_hash,
        survey_systematic_null_input_hashes=survey_report.bank.input_hashes,
        survey_systematic_null_report_hash=survey_report.report_hash,
        response_overlap_config_hash=audit.manifest.config_hash,
        selection_metadata_hash=survey_report.bank.selection_metadata.selection_metadata_hash,
        survey_axis_hash=survey_report.bank.survey_axis_metadata.survey_axis_hash,
        artifact_id="htt.pr063.local_global_mixture.audit_mismatch",
        config_hash=_sha("g"),
        input_hashes=(_sha("h"),),
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )

    report = build_local_global_mixture_report(
        spec,
        parameter_values={
            "beta_local": 0.10,
            "beta_global": -0.06,
            "beta_survey_axis": 0.03,
            "sigma_noise": 0.04,
        },
    )

    assert report.evaluation_status == "blocked_missing_prerequisites"
    assert report.total_log_likelihood is None
    assert "response_overlap_global_response_mismatch" in report.blocked_reasons
    assert (
        report.as_payload()["gates"][
            "response_overlap_audit_response_consistency_gate"
        ]["global_tilt_response_matches_audit"]
        is False
    )


def test_full_design_rank_blocks_collinear_survey_systematic():
    from htt.departure.local_global_mixture import (
        LocalGlobalMixtureBlock,
        LocalGlobalMixtureSpec,
        build_local_global_mixture_report,
    )

    audit = _audit()
    local_report = _local_fpr_report(audit)
    survey_report = _survey_fpr_report(audit)
    blocks = list(_blocks())
    blocks[2] = LocalGlobalMixtureBlock(
        name="collinear_survey_window_axis",
        kind="survey_systematic",
        response=(1.0, 1.0, 0.4),
        parameter_name="beta_survey_axis",
        field_id="survey_axis_nuisance_field",
    )
    spec = LocalGlobalMixtureSpec(
        observable_vector=(0.16, -0.03, 0.08),
        covariance=np.diag((0.9, 1.1, 1.4)),
        blocks=tuple(blocks),
        response_overlap_audit=audit,
        local_null_fpr_report=local_report,
        survey_systematic_null_fpr_report=survey_report,
        local_null_report_hash=local_report.report_hash,
        survey_systematic_null_config_hash=survey_report.bank.config.config_hash,
        survey_systematic_null_input_hashes=survey_report.bank.input_hashes,
        survey_systematic_null_report_hash=survey_report.report_hash,
        response_overlap_config_hash=audit.manifest.config_hash,
        selection_metadata_hash=survey_report.bank.selection_metadata.selection_metadata_hash,
        survey_axis_hash=survey_report.bank.survey_axis_metadata.survey_axis_hash,
        artifact_id="htt.pr063.local_global_mixture.full_design_rank",
        config_hash=_sha("i"),
        input_hashes=(_sha("j"),),
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )

    report = build_local_global_mixture_report(
        spec,
        parameter_values={
            "beta_local": 0.10,
            "beta_global": -0.06,
            "beta_survey_axis": 0.03,
            "sigma_noise": 0.04,
        },
    )

    assert report.evaluation_status == "blocked_missing_prerequisites"
    assert report.total_log_likelihood is None
    assert "full_design_rank_deficient" in report.blocked_reasons
    assert (
        report.as_payload()["gates"][
            "full_local_global_survey_design_rank_gate"
        ]["rank"]
        < 3
    )


def test_full_design_rank_blocks_near_collinear_survey_systematic():
    from htt.departure.local_global_mixture import (
        LocalGlobalMixtureBlock,
        LocalGlobalMixtureSpec,
        build_local_global_mixture_report,
    )

    audit = _audit()
    local_report = _local_fpr_report(audit)
    survey_report = _survey_fpr_report(audit)
    blocks = list(_blocks())
    blocks[2] = LocalGlobalMixtureBlock(
        name="near_collinear_survey_window_axis",
        kind="survey_systematic",
        response=(1.0, 1.0, 0.400000001),
        parameter_name="beta_survey_axis",
        field_id="survey_axis_nuisance_field",
    )
    spec = LocalGlobalMixtureSpec(
        observable_vector=(0.16, -0.03, 0.08),
        covariance=np.diag((0.9, 1.1, 1.4)),
        blocks=tuple(blocks),
        response_overlap_audit=audit,
        local_null_fpr_report=local_report,
        survey_systematic_null_fpr_report=survey_report,
        local_null_report_hash=local_report.report_hash,
        survey_systematic_null_config_hash=survey_report.bank.config.config_hash,
        survey_systematic_null_input_hashes=survey_report.bank.input_hashes,
        survey_systematic_null_report_hash=survey_report.report_hash,
        response_overlap_config_hash=audit.manifest.config_hash,
        selection_metadata_hash=survey_report.bank.selection_metadata.selection_metadata_hash,
        survey_axis_hash=survey_report.bank.survey_axis_metadata.survey_axis_hash,
        artifact_id="htt.pr063.local_global_mixture.full_design_condition",
        config_hash=_sha("k"),
        input_hashes=(_sha("l"),),
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )

    report = build_local_global_mixture_report(
        spec,
        parameter_values={
            "beta_local": 0.10,
            "beta_global": -0.06,
            "beta_survey_axis": 0.03,
            "sigma_noise": 0.04,
        },
    )

    assert report.evaluation_status == "blocked_missing_prerequisites"
    assert report.total_log_likelihood is None
    assert "full_design_condition_too_high" in report.blocked_reasons


def test_noise_block_is_required_and_distinct():
    from htt.departure.local_global_mixture import LocalGlobalMixtureBlock

    with pytest.raises(ValueError, match="noise"):
        LocalGlobalMixtureBlock.require_collection(
            tuple(block for block in _blocks() if block.kind != "noise")
        )


@pytest.mark.parametrize(
    ("parameter_name", "boolean_value"),
    (
        ("beta_local", True),
        ("sigma_noise", np.bool_(False)),
    ),
)
def test_boolean_primitive_parameters_are_rejected(parameter_name, boolean_value):
    from htt.departure.local_global_mixture import (
        LocalGlobalMixtureSpec,
        build_local_global_mixture_report,
    )

    audit = _audit()
    local_report = _local_fpr_report(audit)
    survey_report = _survey_fpr_report(audit)
    spec = LocalGlobalMixtureSpec(
        observable_vector=(0.16, -0.03, 0.08),
        covariance=np.diag((0.9, 1.1, 1.4)),
        blocks=_blocks(),
        response_overlap_audit=audit,
        local_null_fpr_report=local_report,
        survey_systematic_null_fpr_report=survey_report,
        local_null_report_hash=local_report.report_hash,
        survey_systematic_null_config_hash=survey_report.bank.config.config_hash,
        survey_systematic_null_input_hashes=survey_report.bank.input_hashes,
        survey_systematic_null_report_hash=survey_report.report_hash,
        response_overlap_config_hash=audit.manifest.config_hash,
        selection_metadata_hash=(
            survey_report.bank.selection_metadata.selection_metadata_hash
        ),
        survey_axis_hash=survey_report.bank.survey_axis_metadata.survey_axis_hash,
        artifact_id="htt.pr063.local_global_mixture.boolean_parameter",
        config_hash=_sha("o"),
        input_hashes=(_sha("p"),),
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )
    parameter_values = {
        "beta_local": 0.10,
        "beta_global": -0.06,
        "beta_survey_axis": 0.03,
        "sigma_noise": 0.04,
    }
    parameter_values[parameter_name] = boolean_value

    with pytest.raises(ValueError, match="not boolean"):
        build_local_global_mixture_report(
            spec,
            parameter_values=parameter_values,
        )
