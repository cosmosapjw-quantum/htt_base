"""PR-273 blind synthetic vector/tensor integration contracts."""

from __future__ import annotations

import copy
import hashlib
import inspect
import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

from common.blind_synthetic_contract import (
    BlindSyntheticContractError,
    build_blind_synthetic_adjudication,
    build_blind_synthetic_challenge,
    canonical_sha256,
    replay_blind_synthetic_submission,
)
from htt.infer.vector_tensor_blind_integration import (
    DEPTH_ALERT_THRESHOLD,
    analyze_blind_challenge,
)


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "docs/research_program/vector_tensor/pr273_spec.yaml"
POLICY = (
    ROOT
    / "docs/research_program/vector_tensor/pr273_publication_policy.json"
)
BACKLOG = ROOT / "docs/codex_handoff/pr_backlog.yaml"
CHALLENGE = (
    ROOT
    / "docs/research_program/vector_tensor/integration/PR273_CHALLENGE.json"
)
TRUTH = (
    ROOT
    / "docs/research_program/vector_tensor/integration/PR273_TRUTH_VAULT.json"
)
SUBMISSION = (
    ROOT
    / "docs/research_program/vector_tensor/integration/"
    "PR273_ANALYST_SUBMISSION.json"
)
ADJUDICATION = (
    ROOT
    / "docs/research_program/vector_tensor/integration/PR273_ADJUDICATION.json"
)
PACK = (
    ROOT
    / "docs/research_program/vector_tensor/integration/"
    "PR273_DIAGNOSTIC_PACK.json"
)
BUILDER = ROOT / "scripts/codex_harness/build_pr273_blind_synthetic.py"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _challenge():
    return build_blind_synthetic_challenge(_load(CHALLENGE))


def _frozen_submission_content_id() -> str:
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    return spec["analysis_protocol"]["stages"][1][
        "frozen_submission_content_id"
    ]


def test_pr273_spec_card_and_policy_bind_the_blind_integration_scope() -> None:
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    policy = _load(POLICY)
    backlog = yaml.safe_load(BACKLOG.read_text(encoding="utf-8"))
    card = next(row for row in backlog["prs"] if row["id"] == "PR-273")

    assert spec["dependencies"] == card["depends"] == ["PR-270", "PR-272"]
    assert spec["owner"] == card["owner"] == "HTT"
    assert spec["contributors"] == card["contributors"] == [
        "COMMON",
        "OBSSTAT",
        "MIO",
    ]
    assert spec["claim_ceiling"] == policy["claim_ceiling"] == "diagnostic_only"
    assert spec["observed_data_execution"] == "forbidden"
    assert policy["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
    assert spec["analysis_protocol"]["stages"][0]["id"] == "BLIND_ANALYSIS"
    assert TRUTH.relative_to(ROOT).as_posix() in (
        spec["analysis_protocol"]["stages"][0]["forbidden"]
    )


def test_frozen_challenge_truth_and_upstream_hashes_match_bytes() -> None:
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    for record in spec["frozen_inputs"].values():
        path = ROOT / record["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]
    assert spec["frozen_inputs"]["pillar_t_cas"]["required_verdict"] == (
        "CAS_4AXIS_PASS"
    )
    assert spec["frozen_inputs"]["pillar_s_inference"]["required_verdict"] == (
        "PASS"
    )


def test_challenge_is_truth_free_and_partitions_cases_exactly_once() -> None:
    challenge = _challenge()
    payload = challenge.as_payload()
    encoded = json.dumps(payload, sort_keys=True).lower()
    assert "scenario" not in encoded
    assert "expected_" not in encoded
    assert payload["observed_data"] is False
    assert dict(challenge.partitions) == {
        "development": ("C01", "C02", "C03"),
        "held_out": ("C04", "C05"),
    }
    signature = inspect.signature(analyze_blind_challenge)
    assert tuple(signature.parameters) == ("challenge",)


@pytest.mark.smoke
def test_blind_analysis_runs_every_typed_pipeline_stage_deterministically() -> None:
    challenge = _challenge()
    first = analyze_blind_challenge(challenge)
    second = analyze_blind_challenge(challenge)
    assert first.as_payload() == second.as_payload()
    assert first.truth_accessed is False
    assert first.observed_data is False
    assert tuple(row["case_id"] for row in first.case_results) == (
        "C01",
        "C02",
        "C03",
        "C04",
        "C05",
    )
    for row in first.case_results:
        for field in (
            "state_content_id",
            "orbit_content_id",
            "pushforward_content_id",
            "support_utilization_content_id",
            "occupancy_content_id",
            "conditional_exceedance_content_id",
            "depth_path_content_id",
            "depth_coherence_content_id",
            "type_report_content_id",
        ):
            assert row[field].startswith("sha256:")
        assert len(row["functional_result_ids"]) == 4
        assert len(row["x_values"]) == len(row["q_values"]) == 4
        assert row["conditional_exceedance_status"] == "DEFINED_POINT"
        assert row["depth_coherence_status"] == "DEFINED"
        assert row["claim_ceiling"] == "diagnostic_only"
        assert row["transfer_source"] == "none"


def test_required_negative_and_limit_cases_reach_typed_outcomes() -> None:
    rows = {
        row["case_id"]: row
        for row in analyze_blind_challenge(_challenge()).case_results
    }
    assert rows["C01"]["compatibility_status"] == (
        "RESPONSE_COMPATIBILITY_CANDIDATE"
    )
    assert rows["C02"]["geometry_status"] == "COMPLETE"
    assert rows["C03"]["missing_functional"] is True
    assert "MISSING_COMPONENT" in rows["C03"]["functional_statuses"]
    assert rows["C03"]["compatibility_status"] == "PARTIAL_DIAGNOSTIC"
    assert rows["C04"]["partition"] == "held_out"
    assert rows["C04"]["local_global_status"] == "NON_IDENTIFIED"
    assert rows["C04"]["compatibility_status"] == "INDETERMINATE"
    assert rows["C05"]["partition"] == "held_out"
    assert rows["C05"]["depth_mean_normalized_score"] > DEPTH_ALERT_THRESHOLD
    assert rows["C05"]["depth_alert"] is True


def test_frozen_submission_replays_and_contains_no_hidden_truth() -> None:
    payload = _load(SUBMISSION)
    submission = replay_blind_synthetic_submission(
        payload,
        expected_content_id=_frozen_submission_content_id(),
    )
    generated = analyze_blind_challenge(_challenge())
    assert submission.as_payload() == generated.as_payload()
    encoded = json.dumps(payload, sort_keys=True).lower()
    assert "scenario" not in encoded
    assert "expected_" not in encoded
    assert payload["truth_accessed"] is False
    assert payload["observed_data"] is False


def test_registered_adjudication_matches_all_cases_and_kills_mutations() -> None:
    adjudication = _load(ADJUDICATION)
    truth = _load(TRUTH)
    assert adjudication["status"] == "PASS"
    assert {row["scenario"] for row in adjudication["case_verdicts"]} == {
        row["scenario"] for row in truth["expected_cases"]
    }
    assert all(
        row["status"] == "MATCH" for row in adjudication["case_verdicts"]
    )
    assert set(adjudication["mutation_results"]) == {
        "TRUTH_FIELD_IN_CHALLENGE",
        "OBSERVED_DATA_FLAG",
        "CHALLENGE_AFTER_SUBMISSION",
        "SUBMISSION_AFTER_SEAL",
        "TRUTH_VAULT_COMMITMENT",
    }
    assert set(adjudication["mutation_results"].values()) == {"KILLED"}


def test_truth_vault_schema_is_closed_at_registered_adjudication() -> None:
    challenge = _challenge()
    submission_payload = _load(SUBMISSION)
    submission = replay_blind_synthetic_submission(
        submission_payload,
        expected_content_id=_frozen_submission_content_id(),
    )
    truth = _load(TRUTH)
    truth["aux"] = "SYNTHETIC_SENTINEL"
    raw = (
        json.dumps(truth, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("ascii")
    with pytest.raises(BlindSyntheticContractError, match="truth_vault fields"):
        build_blind_synthetic_adjudication(
            adjudication_id="PR273-TRUTH-SCHEMA-MUTATION",
            challenge=challenge,
            submission=submission,
            truth_vault=truth,
            truth_vault_raw=raw,
            expected_truth_vault_sha256=hashlib.sha256(raw).hexdigest(),
            expected_submission_content_id=submission.content_id,
            mutation_results={
                name: "KILLED" for name in challenge.declared_mutations
            },
        )


@pytest.mark.parametrize(
    "mutation",
    (
        "truth_field",
        "nested_label",
        "case_id_alias",
        "challenge_id_alias",
        "partition_extra",
        "observed_data",
        "challenge_content",
        "submission_scenario",
        "submission_partition_resealed",
        "submission_valid_field_resealed",
        "submission_content",
    ),
)
def test_blind_envelopes_fail_closed_under_boundary_mutations(
    mutation: str,
) -> None:
    challenge_payload = _load(CHALLENGE)
    submission_payload = _load(SUBMISSION)
    if mutation == "truth_field":
        challenge_payload["truth"] = {"scenario": "FORBIDDEN"}
        with pytest.raises(BlindSyntheticContractError, match="truth|unregistered"):
            build_blind_synthetic_challenge(challenge_payload)
    elif mutation == "nested_label":
        challenge_payload["cases"][0]["label"] = "SYNTHETIC_SENTINEL"
        with pytest.raises(
            BlindSyntheticContractError,
            match="truth|fields drifted",
        ):
            build_blind_synthetic_challenge(challenge_payload)
    elif mutation == "case_id_alias":
        challenge_payload["cases"][0]["case_id"] = "SYNTHETIC_SENTINEL"
        challenge_payload["partitions"]["development"][0] = (
            "SYNTHETIC_SENTINEL"
        )
        with pytest.raises(
            BlindSyntheticContractError,
            match="opaque inventory|opaque partition",
        ):
            build_blind_synthetic_challenge(challenge_payload)
    elif mutation == "challenge_id_alias":
        challenge_payload["challenge_id"] = "SYNTHETIC_SENTINEL"
        with pytest.raises(
            BlindSyntheticContractError,
            match="opaque identity",
        ):
            build_blind_synthetic_challenge(challenge_payload)
    elif mutation == "partition_extra":
        challenge_payload["partitions"]["aux"] = []
        with pytest.raises(
            BlindSyntheticContractError,
            match="partition fields",
        ):
            build_blind_synthetic_challenge(challenge_payload)
    elif mutation == "observed_data":
        challenge_payload["observed_data"] = True
        with pytest.raises(BlindSyntheticContractError, match="observed"):
            build_blind_synthetic_challenge(challenge_payload)
    elif mutation == "challenge_content":
        challenge = _challenge()
        payload = challenge.as_payload()
        payload["cases"][0]["state"]["sigma_stf5"][0] += 0.1
        with pytest.raises(BlindSyntheticContractError, match="identity"):
            build_blind_synthetic_challenge(payload)
    elif mutation == "submission_scenario":
        payload = copy.deepcopy(submission_payload)
        payload["scenario"] = "SYNTHETIC_SENTINEL"
        with pytest.raises(
            BlindSyntheticContractError,
            match="envelope fields|truth",
        ):
            replay_blind_synthetic_submission(
                payload,
                expected_content_id=_frozen_submission_content_id(),
            )
    elif mutation == "submission_partition_resealed":
        payload = copy.deepcopy(submission_payload)
        payload["case_results"][3]["partition"] = "development"
        body = {
            key: value for key, value in payload.items() if key != "content_id"
        }
        payload["content_id"] = canonical_sha256(body)
        with pytest.raises(
            BlindSyntheticContractError,
            match="partition",
        ):
            replay_blind_synthetic_submission(
                payload,
                expected_content_id=_frozen_submission_content_id(),
            )
    elif mutation == "submission_valid_field_resealed":
        payload = copy.deepcopy(submission_payload)
        payload["case_results"][0]["depth_alert"] = not payload[
            "case_results"
        ][0]["depth_alert"]
        body = {
            key: value for key, value in payload.items() if key != "content_id"
        }
        payload["content_id"] = canonical_sha256(body)
        with pytest.raises(
            BlindSyntheticContractError,
            match="frozen analysis-stage identity",
        ):
            replay_blind_synthetic_submission(
                payload,
                expected_content_id=_frozen_submission_content_id(),
            )
    else:
        payload = copy.deepcopy(submission_payload)
        payload["case_results"][0]["geometry_status"] = "FORGED"
        with pytest.raises(BlindSyntheticContractError, match="identity"):
            replay_blind_synthetic_submission(
                payload,
                expected_content_id=_frozen_submission_content_id(),
            )


def test_diagnostic_pack_is_synthetic_claim_bounded_and_source_complete() -> None:
    pack = _load(PACK)
    assert pack["adjudication_status"] == "PASS"
    assert pack["case_count"] == 5
    assert pack["held_out_case_count"] == 2
    assert pack["observed_data"] is False
    assert pack["owner"] == "HTT"
    assert pack["contributors"] == ["COMMON", "OBSSTAT", "MIO"]
    assert pack["scope"] == "pre-solver registered synthetic integration"
    assert pack["artifact_mode"] == "synthetic_diagnostic"
    assert pack["analysis_stage_truth_accessed"] is False
    assert pack["transfer_source"] == "none"
    assert pack["claim_ceiling"] == "diagnostic_only"
    assert len(pack["required_pipeline"]) == 10
    assert set(pack["scalar_successor_mapping"]) == {
        "x",
        "Q",
        "F",
        "G_F",
        "Pi",
    }
    assert all(
        value.startswith("sha256:")
        for key, value in pack.items()
        if key.endswith("_content_id")
    )
    assert "Bianchi geometry detected" not in json.dumps(pack)
    assert "Bianchi family identified" not in json.dumps(pack)


def test_generator_rebuilds_the_frozen_artifacts_byte_for_byte() -> None:
    result = subprocess.run(
        [sys.executable, "-B", str(BUILDER), "--check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "5 mutations killed" in result.stdout
