from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from pathlib import Path

import yaml

from htt.metamorphic_symmetry import (
    MUTATION_IDS,
    RELATION_IDS,
    build_battery,
    semantic_digest,
    validate_battery,
)


REPO = Path(__file__).resolve().parents[2]
SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr172_spec.yaml"
RESULT_PATH = REPO / "docs/generated/pr172_metamorphic_result.json"


def _json(relative: str) -> dict:
    value = json.loads((REPO / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _spec() -> dict:
    value = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _result() -> dict:
    return _json("docs/generated/pr172_metamorphic_result.json")


def _reseal(payload: dict) -> dict:
    payload["semantic_digest"] = semantic_digest(payload)
    return payload


def test_live_registered_battery_is_reproducible_after_relocation() -> None:
    spec = _spec()
    first = build_battery(spec, REPO)
    second = build_battery(spec, REPO)

    assert first["semantic_digest"] == semantic_digest(first)
    assert second["semantic_digest"] == semantic_digest(second)
    assert first["semantic_digest"] == second["semantic_digest"]
    assert tuple(row["relation_id"] for row in first["relations"]) == RELATION_IDS
    assert tuple(row["mutation_id"] for row in first["mutations"]) == MUTATION_IDS
    assert first["terminal"] == "BLOCKED_METAMORPHIC_RELATION_VIOLATION"


def test_result_is_concrete_split_adapter_evidence_not_a_false_green() -> None:
    result = _result()
    assert tuple(row["relation_id"] for row in result["relations"]) == RELATION_IDS
    by_id = {row["relation_id"]: row for row in result["relations"]}
    assert all(by_id[relation_id]["passed"] for relation_id in RELATION_IDS[:7])
    axisym = by_id["MR172-B-AXISYM-DOC-008"]
    assert axisym["passed"] is False
    metric = axisym["metrics"][0]
    assert metric["value"] == 0.006921858926603516
    assert metric["threshold"] == 0.0
    assert result["adapter_status"] == {
        "cf4_estimator": "PASS_REGISTERED_RELATIONS",
        "b_projector": "BLOCKED_METAMORPHIC_RELATION_VIOLATION",
    }
    assert result["terminal"] == "BLOCKED_METAMORPHIC_RELATION_VIOLATION"
    assert result["scientific_status"] == "OPEN"
    assert result["public_use"] is False
    assert result["lineage"]["independent_numerical_oracle_count"] == 0


def test_cf4_relations_cover_requested_rotation_axis_quadratic_and_monopole() -> None:
    result = _result()
    by_id = {row["relation_id"]: row for row in result["relations"]}
    assert max(row["value"] for row in by_id["MR172-CF4-SO3-001"]["metrics"] if row["comparison"] == "le") <= 1e-10
    assert all(row["passed"] for row in result["relations"][:4])
    quadratic = {row["metric_id"]: row for row in by_id["MR172-CF4-QUADRATIC-003"]["metrics"]}
    assert "bulk_power_quadratic_scaled_residual" in quadratic
    monopole = {row["metric_id"]: row for row in by_id["MR172-CF4-MONOPOLE-004"]["metrics"]}
    assert monopole["flow_only_leakage_challenge_kms"]["value"] >= 50.0


def test_b_checks_are_index_mechanics_and_expose_documented_contract_bug() -> None:
    spec = _spec()
    result = _result()
    assert spec["conventions"]["b_index_mechanics"]["physical_parity_status"] == "UNDERDEFINED_NOT_TESTED"
    assert "not the ell-dependent spatial-parity law" in spec["conventions"]["b_index_mechanics"]["caveat"]
    assert result["relations"][4]["metrics"][0]["value"] == 0.0
    assert result["relations"][5]["metrics"][0]["value"] == 0.0
    assert result["relations"][6]["metrics"][0]["value"] == 0.0
    output_receipt = result["relations"][7]["primitive_receipts"]["projector_output"]
    assert output_receipt["shape"] == [4, 5]
    assert len(output_receipt["sha256"]) == 64
    assert any(float.fromhex(value) != 0.0 for value in output_receipt["float_hex"])


def test_all_registered_mutants_execute_change_surface_and_are_killed() -> None:
    report = _json("docs/generated/pr172_mutation_report.json")
    assert tuple(row["mutation_id"] for row in report["mutations"]) == MUTATION_IDS
    assert report["registered_count"] == 7
    assert report["executed_count"] == 7
    assert report["killed_count"] == 7
    assert report["survivors"] == []
    assert report["all_registered_mutants_killed"] is True
    assert all(row["execution_count"] == 1 for row in report["mutations"])
    assert all(row["activation_delta"] > 0.0 for row in report["mutations"])
    assert all(row["witness_value"] > row["kill_threshold"] for row in report["mutations"])
    for row in report["mutations"]:
        receipt = row["execution_receipt"]
        assert receipt["invoked"] is True
        assert receipt["invocation_count"] == 1
        assert receipt["primitives"]
        encoded = json.dumps(
            receipt["primitives"], sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
        assert hashlib.sha256(encoded).hexdigest() == receipt["primitive_sha256"]


def test_validator_rejects_empty_registry_bool_counts_and_derived_forgery() -> None:
    spec = _spec()

    empty = _reseal({**_result(), "relations": []})
    assert any("missing or empty" in error for error in validate_battery(empty, spec, REPO))

    bool_count = copy.deepcopy(_result())
    bool_count["relations"][0]["execution_count"] = True
    _reseal(bool_count)
    assert any("invalid execution count" in error for error in validate_battery(bool_count, spec, REPO))

    false_green = copy.deepcopy(_result())
    false_green["relations"][-1]["passed"] = True
    false_green["terminal"] = "PASS_METAMORPHIC_SELF_CONSISTENCY_C1"
    _reseal(false_green)
    errors = validate_battery(false_green, spec, REPO)
    assert any("forged relation verdict" in error for error in errors)
    assert any("forged terminal state" in error for error in errors)

    mutation_alias = copy.deepcopy(_result())
    mutation_alias["mutations"][0]["execution_count"] = True
    _reseal(mutation_alias)
    assert any("invalid execution count" in error for error in validate_battery(mutation_alias, spec, REPO))


def test_validator_rejects_resealed_full_threshold_adapter_and_terminal_promotion() -> None:
    forged = copy.deepcopy(_result())
    forged["relations"][-1]["metrics"][0]["threshold"] = 1.0
    forged["relations"][-1]["passed"] = True
    forged["adapter_status"]["b_projector"] = "PASS_REGISTERED_RELATIONS"
    forged["terminal"] = "PASS_METAMORPHIC_SELF_CONSISTENCY_C1"
    forged["config_hash"] = "0" * 64
    _reseal(forged)
    errors = validate_battery(forged, _spec(), REPO)
    assert "config hash mismatch" in errors
    assert any("metric contract mismatch" in error for error in errors)
    assert "forged adapter status" in errors
    assert "forged terminal state" in errors


def test_validator_rejects_claim_and_source_binding_promotion() -> None:
    spec = _spec()
    promoted = copy.deepcopy(_result())
    promoted["public_use"] = True
    promoted["scientific_status"] = "CLOSED"
    promoted["source_bindings"]["b_projector"]["matched"] = False
    _reseal(promoted)
    errors = validate_battery(promoted, spec, REPO)
    assert "claim quarantine mismatch" in errors
    assert any("b_projector: source binding mismatch" == error for error in errors)


def test_fresh_process_replay_and_co04_lineage_are_explicit() -> None:
    replay = _json("docs/generated/pr172_replay_receipt.json")
    result = _result()
    assert replay["fresh_processes"] == 2
    assert replay["digests_match"] is True
    assert replay["semantic_digests"] == [result["semantic_digest"]] * 2

    delta = _json("docs/generated/pr172_co04_delta.json")
    assert delta["lineage_kind"] == "same-production-adapter metamorphic pair"
    assert delta["independent_numerical_oracle_count"] == 0
    assert delta["base_and_transformed_runs_count_as_two_oracles"] is False
    assert delta["pr123_reference_code_or_fixture_reused"] is False
    assert "independent oracle" not in (REPO / "docs/generated/pr172_replay_receipt.json").read_text(encoding="utf-8").lower()


def test_result_card_and_manifest_preserve_blocked_success_edge() -> None:
    card = _json("docs/generated/pr172_result_card.json")
    manifest = _json("docs/generated/pr172_artifact_manifest.json")
    assert card["process_execution_status"] == "PASS_REPRODUCIBLE_TERMINAL_EVIDENCE"
    assert card["success_dependency_satisfied"] is False
    assert card["physical_b_parity_status"] == "UNDERDEFINED_NOT_TESTED"
    assert card["failed_relation_ids"] == ["MR172-B-AXISYM-DOC-008"]
    assert manifest["success_dependency_satisfied"] is False
    assert manifest["artifact_count"] == 6
    assert len(manifest["artifacts"]) == 6
    for row in manifest["artifacts"]:
        path = REPO / row["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]
    for key in (
        "owner",
        "implementation_scope",
        "claim_tier",
        "transfer_source",
        "config_hash",
        "input_hashes",
        "sky_support_status",
        "mask_status",
        "covariance_status",
        "null_mock_status",
        "generating_command",
        "git_commit",
        "worktree_state",
        "worktree_content_receipt",
        "runtime_environment",
    ):
        assert key in manifest

    result = _result()
    assert result["covariance_status"] == "mechanics_only_not_covariance_validation"
    assert result["null_mock_status"] == "not_run_not_applicable"
    # These receipts describe the completed PR-172 run, not the current source
    # layout.  Preserve their internal agreement without forcing a code move to
    # rewrite historical evidence.
    for historical in (
        "htt/src/common/metamorphic_symmetry.py",
        "scripts/codex_harness/run_pr172_metamorphic_battery.py",
    ):
        assert historical in result["input_hashes"]
        assert manifest["input_hashes"][historical] == result["input_hashes"][historical]


def test_intake_reviews_are_byte_preserved_with_fail_verdict() -> None:
    completed = subprocess.run(
        [
            str(REPO / "venv/bin/python"),
            "-B",
            str(REPO / "scripts/codex_harness/archive_pr172_reviews.py"),
            "--check",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    manifest = _json("docs/generated/pr172_reviews/manifest.json")
    assert manifest["copy_mode"] == "byte_for_byte"
    assert manifest["review_count"] == 8
    statuses = {row["role"]: row["status"] for row in manifest["reviews"]}
    assert statuses == {
        "claim_gate": "pass",
        "harness": "pass",
        "physics_statistics": "fail",
        "final_code": "fail",
        "final_science": "pass",
        "final_claim": "fail",
        "remediation_code": "pass",
        "remediation_claim": "pass",
    }


def test_historical_closeout_receipt_preserves_failure_and_remediation() -> None:
    receipt = _json("docs/generated/pr172_closeout_review_receipt.json")
    assert receipt["terminal_ready"] is True
    assert receipt["process_execution_status"] == "PASS"
    assert receipt["scientific_terminal"] == "BLOCKED_METAMORPHIC_RELATION_VIOLATION"
    assert receipt["success_dependency_satisfied"] is False
    assert receipt["preserved_failed_reviews"] == [
        "physics_statistics",
        "final_code",
        "final_claim",
    ]
    assert receipt["remediation_reviews"] == [
        "remediation_code",
        "remediation_claim",
    ]
    assert receipt["errors"] == []
    assert receipt["forbidden_output_hits"] == []
    for key in (
        "owner",
        "implementation_scope",
        "claim_tier",
        "transfer_source",
        "config_hash",
        "input_hashes",
        "sky_support_status",
        "mask_status",
        "covariance_status",
        "null_mock_status",
        "generating_command",
        "git_commit",
        "worktree_state",
        "worktree_content_receipt",
    ):
        assert key in receipt
