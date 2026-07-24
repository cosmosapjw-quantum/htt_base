from __future__ import annotations

import json
import math

import numpy as np
import pytest

from common.contracts import ClaimTier


_COMMAND = "python -m pytest tests/htt/test_local_boost_nulls.py -q"
_WORKTREE = "test-worktree"


def _sha(char: str) -> str:
    return "sha256:" + char * 64


def _audit():
    from htt.departure.response_overlap import build_response_overlap_audit

    return build_response_overlap_audit(
        local_boost_response=(1.0, 0.0),
        global_tilt_response=(0.0, 1.0),
        covariance=np.eye(2),
        observable_labels=("depth_coherence", "template_axis"),
        artifact_id="htt-response-overlap-pr061-fixture",
        artifact_path="memory://htt-response-overlap-pr061-fixture.json",
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
        observable_labels=("depth_coherence", "template_axis"),
        artifact_id="htt-response-overlap-pr061-rank-deficient",
        artifact_path="memory://htt-response-overlap-pr061-rank-deficient.json",
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
            response_weight=0.55,
        ),
        DepthBinSpec(
            label="far",
            z_min=0.075,
            z_max=0.15,
            distance_mpc_min=300.0,
            distance_mpc_max=650.0,
            response_weight=0.22,
        ),
    )


def _config(**overrides):
    from htt.nulls import LocalBoostNullConfig

    values = {
        "n_mocks": 48,
        "seed": 16061,
        "depth_bins": _depth_bins(),
        "target_direction": (1.0, 0.0, 0.0),
        "gf_threshold": 10.0,
        "direction_threshold_deg": 35.0,
        "look_elsewhere_trials": 2,
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


def test_local_boost_null_bank_is_deterministic_and_manifest_backed():
    from htt.nulls import LocalBoostDepthNull

    first = LocalBoostDepthNull(_config()).generate()
    second = LocalBoostDepthNull(_config()).generate()

    assert first.to_payload() == second.to_payload()
    assert first.null_model_id == "local_boost_only"
    assert first.owner == "HTT"
    assert first.claim_tier == "diagnostic_only"
    assert first.transfer_source == "none"
    assert len(first.samples) == first.config.n_mocks * len(first.config.depth_bins)

    payload = first.to_payload()
    assert payload["manifest"]["owner"] == "HTT"
    assert payload["manifest"]["implementation_scope"] == "htt"
    assert payload["manifest"]["claim_tier"] == "diagnostic_only"
    assert payload["manifest"]["production_status"] == "diagnostic_only"
    assert payload["metadata"]["direction_convention"]["coordinate_frame"] == (
        "galactic_cartesian_unit_vector"
    )
    assert payload["metadata"]["g_f_definition"]["status"] == (
        "diagnostic_null_distribution"
    )
    assert payload["distributions"]["g_f"]["count"] == len(first.samples)
    assert payload["distributions"]["direction"]["count"] == len(first.samples)
    assert sorted(payload["distributions"]["g_f"]["by_depth"]) == [
        "far",
        "mid",
        "near",
    ]

    for sample in first.samples:
        assert math.isclose(sample.direction_norm, 1.0, rel_tol=0.0, abs_tol=1e-12)
        assert sample.g_f >= 1.0
        assert sample.log_g_f >= 0.0

    text = json.dumps(payload, sort_keys=True).lower()
    assert "posterior" not in text
    assert "bayes" not in text
    assert "native solver result" not in text
    assert "family identified" not in text
    assert "geometry" not in text


def test_clustering_dipole_depth_null_is_a_distinct_local_structure_bank():
    from htt.nulls import ClusteringDipoleDepthNull

    bank = ClusteringDipoleDepthNull(_config(seed=16062)).generate()
    payload = bank.to_payload()

    assert bank.null_model_id == "local_structure_clustering_dipole"
    assert payload["metadata"]["null_model_scope"] == "local_structure_depth_null"
    assert payload["metadata"]["physical_scope"] == "observer_side_local_structure"
    assert payload["manifest"]["owner"] == "HTT"
    assert payload["transfer_source"] == "none"
    assert len({sample.mock_index for sample in bank.samples}) == bank.config.n_mocks
    assert {sample.depth_label for sample in bank.samples} == {"near", "mid", "far"}


@pytest.mark.parametrize(
    "generator_name",
    ("local_boost", "clustering_dipole"),
)
def test_recorded_mock_seed_replays_each_local_null(generator_name):
    from htt.nulls import ClusteringDipoleDepthNull, LocalBoostDepthNull

    generator = (
        LocalBoostDepthNull
        if generator_name == "local_boost"
        else ClusteringDipoleDepthNull
    )
    seed = 16061
    bank = generator(_config(n_mocks=3, seed=seed)).generate()
    for mock_index in range(bank.config.n_mocks):
        replay = generator(
            _config(n_mocks=1, seed=seed + mock_index),
        ).generate()
        original_samples = [
            sample.to_metadata()
            for sample in bank.samples
            if sample.mock_index == mock_index
        ]
        replay_samples = [sample.to_metadata() for sample in replay.samples]
        for sample in original_samples:
            sample["mock_index"] = 0
        assert original_samples == replay_samples


def test_local_boost_fpr_report_counts_events_and_binds_response_rank():
    from htt.nulls import (
        LocalBoostDepthNull,
        build_local_boost_null_fpr_report,
        evaluate_global_tilt_local_null_gate,
    )

    bank = LocalBoostDepthNull(_config()).generate()
    report = build_local_boost_null_fpr_report(bank, response_overlap_audit=_audit())
    payload = report.to_metadata()

    event_count = sum(
        1
        for mock_index in range(bank.config.n_mocks)
        if any(sample.triggered for sample in bank.samples if sample.mock_index == mock_index)
    )
    assert report.false_positive_count == event_count
    assert payload["false_positive_rate"]["raw"] == pytest.approx(
        event_count / bank.config.n_mocks
    )
    assert payload["false_positive_rate"]["false_positive_denominator"] == (
        bank.config.n_mocks
    )
    assert payload["false_positive_rate"]["adjusted"] == pytest.approx(
        min(1.0, payload["false_positive_rate"]["raw"] * bank.config.look_elsewhere_trials)
    )
    assert payload["false_positive_rate"]["adjusted_interval"][0] <= (
        payload["false_positive_rate"]["adjusted_interval"][1]
    )
    assert payload["rank_status"]["rank_status"] == "full_rank"
    assert payload["rank_status"]["response_overlap_artifact_id"] == (
        "htt-response-overlap-pr061-fixture"
    )
    assert payload["manifest"]["input_hashes"] == [
        _sha("5"),
        _audit().as_payload()["config_hash"],
    ]
    assert report.allowed_claim_tier == ClaimTier.CONDITIONAL

    decision = evaluate_global_tilt_local_null_gate(
        report,
        requested_claim_tier=ClaimTier.CONDITIONAL,
        config_hash=bank.config.config_hash,
        input_hashes=bank.config.input_hashes,
    )
    assert decision.allowed is True
    assert decision.allowed_claim_tier == ClaimTier.CONDITIONAL
    assert decision.blocked_reasons == ()


def test_global_tilt_gate_fails_closed_without_matching_local_null_fpr():
    from htt.nulls import (
        LocalBoostDepthNull,
        build_local_boost_null_fpr_report,
        evaluate_global_tilt_local_null_gate,
    )

    missing = evaluate_global_tilt_local_null_gate(
        None,
        requested_claim_tier=ClaimTier.CONDITIONAL,
    )
    assert missing.allowed is False
    assert "local_boost_null_fpr_missing" in missing.blocked_reasons

    high_fpr_config = _config(gf_threshold=1.0, direction_threshold_deg=180.0)
    high_fpr_report = build_local_boost_null_fpr_report(
        LocalBoostDepthNull(high_fpr_config).generate(),
        response_overlap_audit=_audit(),
    )
    high_fpr = evaluate_global_tilt_local_null_gate(
        high_fpr_report,
        requested_claim_tier=ClaimTier.CONDITIONAL,
        config_hash=high_fpr_config.config_hash,
        input_hashes=high_fpr_config.input_hashes,
    )
    assert high_fpr.allowed is False
    assert "local_boost_null_fpr_exceeds_threshold" in high_fpr.blocked_reasons

    mismatch_report = build_local_boost_null_fpr_report(
        LocalBoostDepthNull(_config()).generate(),
        response_overlap_audit=_audit(),
    )
    mismatch = evaluate_global_tilt_local_null_gate(
        mismatch_report,
        requested_claim_tier=ClaimTier.CONDITIONAL,
        config_hash=_sha("6"),
        input_hashes=(_sha("5"),),
    )
    assert mismatch.allowed is False
    assert "local_boost_null_config_hash_mismatch" in mismatch.blocked_reasons

    input_mismatch = evaluate_global_tilt_local_null_gate(
        mismatch_report,
        requested_claim_tier=ClaimTier.CONDITIONAL,
        config_hash=_config().config_hash,
        input_hashes=(_sha("6"),),
    )
    assert input_mismatch.allowed is False
    assert "local_boost_null_input_hashes_mismatch" in input_mismatch.blocked_reasons

    report_mismatch = evaluate_global_tilt_local_null_gate(
        mismatch_report,
        requested_claim_tier=ClaimTier.CONDITIONAL,
        report_hash=_sha("7"),
    )
    assert report_mismatch.allowed is False
    assert "local_boost_null_report_hash_mismatch" in report_mismatch.blocked_reasons

    requested_validated = evaluate_global_tilt_local_null_gate(
        mismatch_report,
        requested_claim_tier=ClaimTier.VALIDATED,
    )
    assert requested_validated.allowed is False
    assert "requested_claim_tier_exceeds_local_null_ceiling" in (
        requested_validated.blocked_reasons
    )


def test_global_tilt_gate_fails_closed_for_rank_and_covariance_blockers():
    from htt.nulls import (
        LocalBoostDepthNull,
        build_local_boost_null_fpr_report,
        evaluate_global_tilt_local_null_gate,
    )

    rank_report = build_local_boost_null_fpr_report(
        LocalBoostDepthNull(_config()).generate(),
        response_overlap_audit=_rank_deficient_audit(),
    )
    rank_decision = evaluate_global_tilt_local_null_gate(
        rank_report,
        requested_claim_tier=ClaimTier.CONDITIONAL,
    )
    assert rank_decision.allowed is False
    assert "response_overlap_rank_not_full" in rank_decision.blocked_reasons

    covariance_config = _config(covariance_status="diagnostic_covariance_pending")
    covariance_report = build_local_boost_null_fpr_report(
        LocalBoostDepthNull(covariance_config).generate(),
        response_overlap_audit=_audit(),
    )
    covariance_decision = evaluate_global_tilt_local_null_gate(
        covariance_report,
        requested_claim_tier=ClaimTier.CONDITIONAL,
    )
    assert covariance_decision.allowed is False
    assert "covariance_status_not_supported" in covariance_decision.blocked_reasons


def test_local_boost_nulls_reject_invalid_depth_and_direction_metadata():
    from htt.nulls import DepthBinSpec, DepthNullMockBank, LocalBoostDepthNull, LocalBoostNullConfig

    with pytest.raises(ValueError, match="non-overlapping"):
        LocalBoostNullConfig(
            **{
                **_config().__dict__,
                "depth_bins": (
                    DepthBinSpec(
                        "a",
                        z_min=0.0,
                        z_max=0.1,
                        distance_mpc_min=0.0,
                        distance_mpc_max=100.0,
                    ),
                    DepthBinSpec(
                        "b",
                        z_min=0.05,
                        z_max=0.2,
                        distance_mpc_min=100.0,
                        distance_mpc_max=200.0,
                    ),
                ),
            }
        )

    with pytest.raises(ValueError, match="target_direction"):
        LocalBoostNullConfig(**{**_config().__dict__, "target_direction": (0.0, 0.0, 0.0)})

    config = _config(n_mocks=2)
    bank = LocalBoostDepthNull(config).generate()
    with pytest.raises(ValueError, match="unit vector"):
        bank.samples[0].__class__(
            **{**bank.samples[0].__dict__, "direction_unit_vector": (2.0, 0.0, 0.0)}
        )

    with pytest.raises(ValueError, match="complete mock/depth coverage"):
        DepthNullMockBank(
            null_model_id=bank.null_model_id,
            config=bank.config,
            samples=bank.samples[:-1],
            physical_scope=bank.physical_scope,
            null_model_scope=bank.null_model_scope,
        )


def test_local_boost_fpr_gate_can_pin_response_overlap_audit_hash():
    from htt.nulls import (
        LocalBoostDepthNull,
        build_local_boost_null_fpr_report,
        evaluate_global_tilt_local_null_gate,
    )

    bank = LocalBoostDepthNull(_config()).generate()
    audit = _audit()
    report = build_local_boost_null_fpr_report(bank, response_overlap_audit=audit)

    ok = evaluate_global_tilt_local_null_gate(
        report,
        requested_claim_tier=ClaimTier.CONDITIONAL,
        config_hash=bank.config.config_hash,
        input_hashes=bank.config.input_hashes,
        response_overlap_config_hash=audit.as_payload()["config_hash"],
    )
    assert ok.allowed is True

    stale = evaluate_global_tilt_local_null_gate(
        report,
        requested_claim_tier=ClaimTier.CONDITIONAL,
        config_hash=bank.config.config_hash,
        input_hashes=bank.config.input_hashes,
        response_overlap_config_hash=_sha("e"),
    )
    assert stale.allowed is False
    assert "response_overlap_config_hash_mismatch" in stale.blocked_reasons
