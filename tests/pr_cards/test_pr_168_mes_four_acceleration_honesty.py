"""PR-168 acceptance tests for the failed-contract closeout."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import yaml

from common.pr248_pr168_integrity_supersession import (
    authorized_pr168_transition,
)


REPO = Path(__file__).resolve().parents[2]
GENERATED = REPO / "docs/generated"
CONTRACT = GENERATED / (
    "pr168_cas/CAS_CONTRACT_PR168_ACCEL_KINEMATIC_SOURCE_BASIS.json"
)
AXES = ("wolfram_xact", "sympy", "sage_singular", "lean")


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _runner_module():
    path = REPO / (
        "scripts/codex_harness/"
        "run_pr168_mes_four_acceleration_honesty.py"
    )
    spec = importlib.util.spec_from_file_location("pr168_fail_runner", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_original_four_axis_agreement_is_preserved_but_superseded() -> None:
    contract_sha = _sha(CONTRACT)
    original = _json(GENERATED / "pr168_cas_adjudication.json")
    final = _json(GENERATED / "pr168_contract_failure_adjudication.json")

    assert original["aggregate_status"] == "CAS_4AXIS_PASS"
    assert original["contract_sha256"] == contract_sha
    assert final["aggregate_status"] == "CAS_FAIL"
    assert final["original_computational_aggregate"] == "CAS_4AXIS_PASS"
    assert final["scientific_contract_status"] == "INVALID_UNDERDEFINED"
    assert final["production_authorized"] is False
    assert final["contract_sha256"] == contract_sha
    assert final["supersedes_provisional_production_authorization"][
        "sha256"
    ] == _sha(GENERATED / "pr168_cas_collection_receipt.json")

    receipt = _json(GENERATED / "pr168_cas_collection_receipt.json")
    for axis in AXES:
        result_path = GENERATED / f"pr168_cas/axis_result_{axis}.json"
        result = _json(result_path)
        assert receipt["normalized_axis_sha256"][axis] == _sha(result_path)
        assert result["status"] == "PASS"
        assert result["contract_sha256"] == contract_sha
        assert result["commands"]
        assert result["completed_at"]
        assert result["verified_input_hashes"]
        assert result["counterexample"] is None
        assert result["sibling_results_read"] == []


def test_registered_normalization_has_exact_factor_three_counterexample() -> None:
    final = _json(GENERATED / "pr168_contract_failure_adjudication.json")
    counterexample = final["normalization_counterexample"]
    assert counterexample == {
        "acceleration_amplitude": "6",
        "thermodynamic_factor": "15",
        "defined_acceleration_source_ell1": "30",
        "defined_source_divided_by_amplitude": "5",
        "registered_normalized_target_ell1": "15",
        "mismatch": True,
        "explanation": (
            "With S_A=(A*G/3) delta_ell1, ordinary amplitude normalization "
            "gives S_A/A=G/3.  The registered target G would require the "
            "unstated operator 3*S_A/A."
        ),
    }


def test_fail_branch_leaves_every_inventoried_consumer_unchanged() -> None:
    inventory = yaml.safe_load(
        (
            REPO
            / "docs/research_program/long_horizon_rescue/"
            "pr168_active_b_accel_consumers.yaml"
        ).read_text(encoding="utf-8")
    )
    receipt = _json(GENERATED / "pr168_code_integrity_receipt.json")
    expected = {
        row["path"]: row["sha256_before"]
        for row in inventory["migration_required"]
    }
    observed = {
        row["path"]: row["actual_sha256"]
        for row in receipt["production_rows"]
    }
    assert observed == expected
    assert receipt["all_inventoried_consumers_unchanged"] is True
    assert receipt["pass_only_status_source_absent"] is True
    for rel, expected_sha in expected.items():
        current_sha = _sha(REPO / rel)
        assert current_sha == expected_sha or authorized_pr168_transition(
            REPO,
            relative_path=rel,
            prior_sha256=expected_sha,
            current_sha256=current_sha,
        )
    assert not (REPO / "htt/src/common/mes_acceleration_status.py").exists()


def test_hostile_review_failures_are_hash_bound() -> None:
    final = _json(GENERATED / "pr168_contract_failure_adjudication.json")
    reviews = final["review_receipts"]
    assert set(reviews) == {"physics", "code", "claim"}
    assert {row["status"] for row in reviews.values()} == {"fail"}
    for row in reviews.values():
        path = REPO / row["path"]
        assignment_path = REPO / row["assignment_path"]
        assert row["path"].startswith("docs/generated/pr168_reviews/")
        assert row["assignment_path"].startswith(
            "docs/generated/pr168_reviews/"
        )
        assert path.is_file()
        assert assignment_path.is_file()
        assert row["sha256"] == _sha(path)
        assert row["assignment_sha256"] == _sha(assignment_path)
        assert row["assignment_id"]
        assert row["context_version"]

    fatal = set(final["fatal_finding_ids"])
    assert {
        "F-PR168-PHYS-001",
        "F-PR168-PHYS-002",
        "F-PR168-CODE-001",
        "F-PR168-CODE-002",
        "F-PR168-CODE-003",
    } <= fatal


def test_blind_axis_assignment_and_outer_envelopes_are_durable() -> None:
    receipt = _json(GENERATED / "pr168_cas_collection_receipt.json")
    for axis in AXES:
        assignment_path = GENERATED / (
            f"pr168_cas/harness_receipts/assignment_{axis}.json"
        )
        outer_path = GENERATED / (
            f"pr168_cas/harness_receipts/outer_result_{axis}.json"
        )
        normalized_path = GENERATED / f"pr168_cas/axis_result_{axis}.json"
        assignment = _json(assignment_path)
        outer = _json(outer_path)
        normalized = _json(normalized_path)

        assert receipt["outer_envelope_sha256"][axis] == _sha(outer_path)
        assert outer["payload"]["cas_axis_result"] == normalized
        assert outer["assignment_id"] == assignment["assignment_id"]
        assert outer["run_id"] == assignment["run_id"]
        assert outer["context_version"] == assignment["context_version"]
        assert assignment["cas_axis"] == axis
        assert assignment["independence_mode"] == "blind-results"
        assert assignment["allowed_sibling_results"] == []


def test_result_and_theorem_stay_exploratory_and_non_public() -> None:
    card = _json(GENERATED / "pr168_result_card.json")
    theorem = _json(GENERATED / "pr168_theorem_signature.json")

    assert card["result_status"] == (
        "CAS_FAIL_CONTRACT_INVALID_PRODUCTION_UNCHANGED"
    )
    assert card["claim_tier"] == "exploratory"
    assert card["public_use"] is False
    assert card["final_adjudicated_result"]["production_authorized"] is False
    assert card["production_disposition"] == "unchanged"

    assert theorem["signature_status"] == "WITHHELD_CONTRACT_INVALID"
    assert theorem["aggregate_status"] == "CAS_FAIL"
    assert theorem["counts_as_independent_derivation"] is False
    assert theorem["target_identity"] is None
    assert theorem["result"] is None
    assert theorem["public_use"] is False

    required_metadata = {
        "owner",
        "implementation_scope",
        "claim_tier",
        "transfer_source",
        "config_hash",
        "input_hashes",
        "sky_support_mask_status",
        "covariance_null_mock_status",
        "caveats",
        "generating_command",
        "git_commit_or_worktree_state",
        "runtime",
    }
    assert required_metadata <= set(card)
    assert required_metadata <= set(theorem)


def test_manifest_requires_exact_nonempty_hash_sets() -> None:
    runner = _runner_module()
    manifest = _json(GENERATED / "pr168_artifact_manifest.json")
    assert runner._hash_map_errors(
        manifest["input_hashes"],
        runner._manifest_input_paths(),
        "input_hashes",
    ) == []
    assert runner._hash_map_errors(
        manifest["artifact_hashes"],
        runner._manifest_artifact_paths(),
        "artifact_hashes",
    ) == []
    assert runner._hash_map_errors(
        {}, runner._manifest_input_paths(), "input_hashes"
    )
    assert runner._hash_map_errors(
        {}, runner._manifest_artifact_paths(), "artifact_hashes"
    )
    assert manifest["affected_owner_review"] == (
        "rejected_by_adversarial_closeout"
    )
    assert manifest["outcome"] == (
        "CAS_FAIL_CONTRACT_INVALID_PRODUCTION_UNCHANGED"
    )
    assert not any(
        path.startswith(".agent-harness/")
        for path in (*manifest["input_hashes"], *manifest["artifact_hashes"])
    )


def test_pass_only_outputs_are_absent_and_closeout_gate_passes() -> None:
    for rel in (
        "docs/generated/pr168_stale_consumer_scan.json",
        "docs/generated/pr168_mutation_report.json",
        "htt/src/common/mes_acceleration_status.py",
        "figures/pr168/fig_MES_two_supported_bounds.png",
        "figures/pr168/fig_MES_two_supported_bounds.png.manifest.json",
    ):
        assert not (REPO / rel).exists()

    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "scripts/codex_harness/"
            "run_pr168_mes_four_acceleration_honesty.py",
            "check",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert json.loads(completed.stdout)["ok"] is True
