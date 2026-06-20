from __future__ import annotations

import json

import numpy as np
import pytest


def _sha(char: str = "a") -> str:
    return "sha256:" + char * 64


def _blocks():
    from htt.rest_frame.joint_model import RestFrameResponseBlocks

    return RestFrameResponseBlocks(
        observer_cmb_boost_response=np.asarray([[1.0], [0.0], [0.0], [0.0], [0.0], [0.0], [0.0]]),
        local_flow_basis_response=np.asarray([[0.0], [1.0], [0.0], [0.0], [0.0], [0.0], [0.0]]),
        global_rest_frame_offset_response=np.asarray(
            [
                [0.0, 0.0],
                [0.0, 0.0],
                [0.0, 0.0],
                [1.0, 0.0],
                [0.0, 1.0],
                [1.0, 0.0],
                [0.0, 1.0],
            ]
        ),
        survey_systematic_response=np.asarray([[0.0], [0.0], [1.0], [0.0], [0.0], [0.0], [0.0]]),
        covariance=np.eye(7),
        channel_labels=("cmb", "cf4", "sys", "desi-n", "desi-s", "sn-n", "sn-s"),
        survey_axis_vector=(0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0),
        survey_axis_frame="response_channel_space",
        survey_axis_provenance="toy_fixture_axis_not_interpreted",
        sky_support_status="not_applicable_toy_fixture",
        mask_status="not_applicable_toy_fixture",
        covariance_status="toy_identity_covariance",
        null_mock_status="not_bound_toy_fixture",
        config_hash=_sha("1"),
        input_hashes=(_sha("2"),),
        generating_command="pytest joint rest frame",
        worktree_state="test",
    )


def test_joint_rest_frame_rank_gate_emits_full_rank_candidate() -> None:
    from htt.rest_frame.joint_model import evaluate_joint_rest_frame_rank_gate

    audit = evaluate_joint_rest_frame_rank_gate(_blocks())
    payload = audit.to_payload()

    assert payload["owner"] == "HTT"
    assert payload["implementation_scope"] == "htt"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["rank_status"] == "full_rank_candidate"
    assert payload["claim_status"] == "pre_inference_rank_candidate"
    assert payload["projected_rank"] == 2
    assert payload["target_dimension"] == 2
    assert payload["rank_tolerance"] == 1.0e-10
    assert 0.0 < payload["rank_threshold"] <= 1.0e-9
    assert payload["channel_ablation_stability"]["all_single_channel_ablations_full_rank"] is True
    assert set(payload["channel_ablation_stability"]["per_channel_status"]) == set(_blocks().channel_labels)
    assert payload["survey_axis_overlap"]["status"] in {"finite", "zero_norm_axis"}
    assert payload["survey_axis_metadata"] == {
        "axis_vector": [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        "axis_frame": "response_channel_space",
        "axis_provenance": "toy_fixture_axis_not_interpreted",
        "sky_support_status": "not_applicable_toy_fixture",
        "mask_status": "not_applicable_toy_fixture",
        "covariance_status": "toy_identity_covariance",
        "null_mock_status": "not_bound_toy_fixture",
    }
    assert payload["config_hash"] == _sha("1")
    assert payload["input_hashes"] == [_sha("2")]
    assert payload["native_solver_result"] is False
    text = json.dumps(payload, sort_keys=True).lower()
    assert "mio posterior" not in text
    assert "mio certificate" not in text
    assert ("family " + "identified") not in text


def test_joint_rest_frame_rank_gate_blocks_rank_deficient_design() -> None:
    from htt.rest_frame.joint_model import RestFrameResponseBlocks, evaluate_joint_rest_frame_rank_gate

    base = _blocks()
    deficient = RestFrameResponseBlocks(
        observer_cmb_boost_response=base.observer_cmb_boost_response,
        local_flow_basis_response=base.local_flow_basis_response,
        global_rest_frame_offset_response=np.asarray(
            [[0.0, 0.0], [1.0, 0.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0]]
        ),
        survey_systematic_response=base.survey_systematic_response,
        covariance=base.covariance,
        channel_labels=base.channel_labels,
        survey_axis_vector=base.survey_axis_vector,
        config_hash=_sha("3"),
        input_hashes=(_sha("4"),),
        generating_command="pytest joint rest frame",
        worktree_state="test",
    )

    audit = evaluate_joint_rest_frame_rank_gate(deficient)
    payload = audit.to_payload()

    assert payload["rank_status"] == "rank_deficient_no_claim"
    assert payload["claim_status"] == "no_claim_rank_deficient"
    assert payload["projected_rank"] < payload["target_dimension"]
    assert "rank_deficient_after_nuisance_projection" in payload["no_claim_reasons"]


def test_rest_frame_response_blocks_validate_shapes_hashes_and_covariance() -> None:
    from htt.rest_frame.joint_model import RestFrameResponseBlocks

    with pytest.raises(ValueError, match="covariance"):
        RestFrameResponseBlocks(
            observer_cmb_boost_response=np.ones((2, 1)),
            local_flow_basis_response=np.ones((2, 1)),
            global_rest_frame_offset_response=np.ones((2, 1)),
            survey_systematic_response=np.ones((2, 1)),
            covariance=np.asarray([[1.0, 0.0], [0.0, 0.0]]),
            channel_labels=("a", "b"),
            config_hash=_sha("5"),
            input_hashes=(_sha("6"),),
            generating_command="pytest joint rest frame",
            worktree_state="test",
        )
    with pytest.raises(ValueError, match="config_hash"):
        RestFrameResponseBlocks(
            observer_cmb_boost_response=np.ones((2, 1)),
            local_flow_basis_response=np.ones((2, 1)),
            global_rest_frame_offset_response=np.ones((2, 1)),
            survey_systematic_response=np.ones((2, 1)),
            covariance=np.eye(2),
            channel_labels=("a", "b"),
            config_hash="sha256:not-real",
            input_hashes=(_sha("7"),),
            generating_command="pytest joint rest frame",
            worktree_state="test",
        )

    with pytest.raises(ValueError, match="channel_labels must be unique"):
        RestFrameResponseBlocks(
            observer_cmb_boost_response=np.ones((2, 1)),
            local_flow_basis_response=np.ones((2, 1)),
            global_rest_frame_offset_response=np.ones((2, 1)),
            survey_systematic_response=np.ones((2, 1)),
            covariance=np.eye(2),
            channel_labels=("dup", "dup"),
            config_hash=_sha("8"),
            input_hashes=(_sha("9"),),
            generating_command="pytest joint rest frame",
            worktree_state="test",
        )
