#!/usr/bin/env python3
"""Bounded metadata-only oracle for the PR-289 final seal closeout."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "pr289-final-seal-closeout-20260811"
ASSIGNMENT_ID = "A-PR289-FINAL-SEAL-CLOSEOUT"
BASE_SHA = "27df5da040e27eeaad44873ba3424ff73fb4bb09"
R5_SHA = "eec048d4cf19989983986d139c7d0a797b1363e0"
FINAL_SHA = "45da1bf54149864fb9d87be3a828df202ee1df7f"
TARGET_REF = "refs/remotes/origin/changeset/pr288-bayesian-evidence-recovery-20260811"
LOCAL_REF = "refs/heads/changeset/pr289-native-data-identity-recovery-20260811"
REMOTE_CANDIDATE_REF = (
    "refs/remotes/origin/changeset/pr289-native-data-identity-recovery-20260811"
)


def load_json(path: str) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_sha256(value: dict[str, Any], *, omit: set[str]) -> str:
    payload = {key: item for key, item in value.items() if key not in omit}
    return sha256_bytes(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )
    )


def git(*args: str, input_bytes: bytes | None = None) -> bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        input=input_bytes,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"git {' '.join(args)} failed ({completed.returncode}): "
            f"{completed.stderr.decode('utf-8', errors='replace')}"
        )
    return completed.stdout


def patch_id(commit: str) -> str:
    patch = git("show", "--pretty=format:", "--binary", commit)
    output = git("patch-id", "--stable", input_bytes=patch).decode().strip().split()
    assert len(output) == 2
    assert output[1] == "0" * 40
    return output[0]


def command_map(receipt: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = receipt["commands"]
    mapped = {row["id"]: row for row in rows}
    assert len(rows) == len(mapped) == 8
    return mapped


def main() -> None:
    assignment_path = (
        f".agent-harness/runs/{RUN_ID}/assignments/{ASSIGNMENT_ID}.json"
    )
    assignment = load_json(assignment_path)
    context = load_json(".agent-harness/context/CONTEXT_INDEX.json")
    run_plan = load_json(f".agent-harness/runs/{RUN_ID}/RUN_PLAN.json")

    # Registration and every declared input are byte-identical to the assignment.
    assert assignment["run_id"] == RUN_ID
    assert assignment["assignment_id"] == ASSIGNMENT_ID
    assert assignment["context_version"] == context["context_version"]
    registration_payload = dict(assignment)
    declared_assignment_hash = registration_payload.pop("assignment_sha256")
    computed_assignment_hash = sha256_bytes(
        json.dumps(registration_payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    )
    assert declared_assignment_hash == computed_assignment_hash
    for item in assignment["required_inputs"]:
        assert sha256_bytes((ROOT / item["path"]).read_bytes()) == item["sha256"]

    final_seal = load_json(".prguard/runtime/PR289_FINAL_CANDIDATE_SEAL.json")
    final_receipt = load_json(
        ".prguard/runtime/PR289_FINAL_INTEGRATION_REHEARSAL.json"
    )
    r5_seal = load_json(".prguard/runtime/PR289_R5_CANDIDATE_SEAL.json")
    r5_receipt = load_json(".prguard/runtime/PR289_R5_INTEGRATION_REHEARSAL.json")
    r5_summary = load_json(
        ".agent-harness/runs/pr289-r5-authorized-review-extension-20260811/RUN_SUMMARY.json"
    )
    policy = load_json("docs/research_program/post_pr275/pr289_publication_policy.json")

    # Final seal identities and exact PR-288 predecessor/base.
    assert final_seal["seal_sha256"] == canonical_sha256(
        final_seal, omit={"seal_sha256"}
    )
    assert final_receipt["receipt_sha256"] == canonical_sha256(
        final_receipt, omit={"receipt_sha256"}
    )
    assert final_seal["base_sha"] == final_seal["merge_base_sha"] == BASE_SHA
    assert final_seal["candidate_sha"] == FINAL_SHA
    assert final_receipt["latest_target_sha"] == BASE_SHA
    assert final_receipt["candidate_sha"] == FINAL_SHA
    assert final_receipt["candidate_seal_sha256"] == final_seal["seal_sha256"]
    assert final_receipt["candidate_tree_sha"] == final_seal["candidate_tree_sha"]
    assert final_receipt["merged_tree_sha"] == final_seal["candidate_tree_sha"]
    assert final_receipt["diff_sha256"] == final_seal["diff_sha256"]
    assert final_receipt["changed_files_sha256"] == final_seal["changed_files_sha256"]
    assert final_receipt["status"] == "PASS"
    assert run_plan["predecessor_pr"] == "PR-288"
    assert run_plan["predecessor_sealed_sha"] == BASE_SHA
    assert git("rev-parse", "HEAD").decode().strip() == FINAL_SHA
    assert git("rev-parse", "HEAD^{tree}").decode().strip() == final_seal[
        "candidate_tree_sha"
    ]
    assert git("rev-parse", TARGET_REF).decode().strip() == BASE_SHA
    assert git("merge-base", BASE_SHA, FINAL_SHA).decode().strip() == BASE_SHA
    assert not git("status", "--porcelain=v1", "--untracked-files=all")
    current_diff = git("diff", "--binary", "--full-index", BASE_SHA, FINAL_SHA)
    assert sha256_bytes(current_diff) == final_seal["diff_sha256"]

    # Exactly 17 linear candidate commits and 17 unique stable patch IDs.
    commits = git("rev-list", "--reverse", f"{BASE_SHA}..{FINAL_SHA}").decode().splitlines()
    assert commits == final_seal["candidate_commits"]
    assert len(commits) == 17
    assert not git("rev-list", "--merges", f"{BASE_SHA}..{FINAL_SHA}")
    previous = BASE_SHA
    for commit in commits:
        parents = git("show", "-s", "--format=%P", commit).decode().strip().split()
        assert parents == [previous]
        previous = commit
    actual_patch_ids = [patch_id(commit) for commit in commits]
    sealed_patch_ids = [row["stable_patch_id"] for row in final_seal["stable_patch_ids"]]
    assert actual_patch_ids == sealed_patch_ids
    assert len(set(actual_patch_ids)) == 17

    # Final metadata-only commit changes exactly the PR delta and synchronized mirrors.
    final_delta = git("diff", "--name-status", f"{R5_SHA}..{FINAL_SHA}").decode().splitlines()
    assert final_delta == [
        "M\tdocs/PR_DELTAS/pr-289.md",
        "M\tdocs/codex_handoff/pr_status.yaml",
        "M\tmachine_readable/pr_status.yaml",
    ]
    assert git("show", "-s", "--format=%P", FINAL_SHA).decode().strip() == R5_SHA

    # The R5 production/dependency evidence key is unchanged at final seal.
    assert r5_seal["candidate_sha"] == r5_summary["candidate_binding"]["candidate_sha"] == R5_SHA
    assert r5_seal["production_hash"] == final_seal["production_hash"]
    assert r5_summary["evidence_key"]["production_hash"] == final_seal["production_hash"]
    assert run_plan["production_hash"] == final_seal["production_hash"]
    assert run_plan["evidence_key"]["production_hash"] == final_seal["production_hash"]
    assert run_plan["dependency_hashes"] == r5_summary["evidence_key"]["dependency_hashes"]
    assert run_plan["evidence_key"]["dependency_hashes"] == run_plan["dependency_hashes"]

    # Five substantive command rows are carried byte-for-byte; only three
    # metadata-sensitive rows were freshly executed on the final candidate.
    carried = [
        "pr289-focused",
        "pr289-readonly-preflight",
        "pr289-adjacent",
        "pr289-receipt-replay",
        "pr289-publication-policy-cross-binding",
    ]
    fresh = [
        "pr289-portable-clean-replay",
        "pr289-dag-strict",
        "pr289-claim-language",
    ]
    r5_commands = command_map(r5_receipt)
    final_commands = command_map(final_receipt)
    assert [row["id"] for row in final_receipt["commands"]] == [
        row["id"] for row in policy["required_commands"]
    ]
    assert all(final_commands[item] == r5_commands[item] for item in carried)
    assert all(final_commands[item] != r5_commands[item] for item in fresh)
    assert all(final_commands[item]["returncode"] == 0 for item in fresh)
    freshness = final_receipt["evidence_freshness"]
    assert freshness["mode"] == "UNCHANGED_SUBSTANTIVE_EVIDENCE_KEY_CARRY_FORWARD"
    assert freshness["reason"] == "EVIDENCE_KEY_UNCHANGED"
    assert freshness["substantive_rerun_required"] is False
    assert freshness["carried_forward_command_ids"] == carried
    assert freshness["fresh_metadata_sensitive_command_ids"] == fresh
    assert freshness["previous_candidate_sha"] == R5_SHA
    assert freshness["current_candidate_sha"] == FINAL_SHA
    assert freshness["production_hash"] == final_seal["production_hash"]
    assert freshness["tracked_delta_since_previous_candidate"] == [
        "docs/PR_DELTAS/pr-289.md",
        "docs/codex_handoff/pr_status.yaml",
        "machine_readable/pr_status.yaml",
    ]
    assert freshness["previous_integration_receipt_file_sha256"] == sha256_bytes(
        (ROOT / ".prguard/runtime/PR289_R5_INTEGRATION_REHEARSAL.json").read_bytes()
    )

    # Immutable review chronology remains typed; incidents do not become PASS.
    r3_phys = load_json(
        ".agent-harness/runs/pr289-final-r3-review-20260811/results/A-PR289-R3-PHYSCODE.json"
    )
    r3_claim = load_json(
        ".agent-harness/runs/pr289-final-r3-review-20260811/results/A-PR289-R3-REPLAYCLAIM.json"
    )
    r4 = load_json(
        ".agent-harness/runs/pr289-final-r4-replacement-review-20260811/results/A-PR289-R4-FINAL-REVIEW.json"
    )
    r5_phys = load_json(
        ".agent-harness/runs/pr289-r5-authorized-review-extension-20260811/results/A-PR289-R5-PHYSCODE.json"
    )
    r5_claim = load_json(
        ".agent-harness/runs/pr289-r5-authorized-review-extension-20260811/results/A-PR289-R5-REPLAYCLAIM.json"
    )
    assert (r3_claim["status"], r3_claim["gate_disposition"]) == ("fail", "FAIL")
    assert "status header is stale" in r3_claim["findings"][0]["statement"]
    assert (r3_phys["status"], r3_phys["gate_disposition"]) == (
        "error",
        "INCONCLUSIVE",
    )
    assert r3_phys["claim_results"][0]["outcome"] == "not_examined"
    assert "INDEPENDENCE_VIOLATION" in r3_phys["errors"][0]
    assert (r4["status"], r4["gate_disposition"]) == ("error", "INCONCLUSIVE")
    assert r4["claim_results"][0]["outcome"] == "not_examined"
    assert "INDEPENDENCE_BREACH" in r4["errors"][0]
    assert "PRE_EXPOSURE_REPRODUCTION_ONLY" in r4["errors"][1]
    assert "CF4" in r4["errors"][1] and "PLANCK" in r4["errors"][1]
    assert (r5_phys["status"], r5_phys["gate_disposition"]) == ("pass", "PASS")
    assert (r5_claim["status"], r5_claim["gate_disposition"]) == ("pass", "PASS")
    assert r5_phys["claim_results"][0]["outcome"] == "examined_no_findings"
    assert r5_claim["claim_results"][0]["outcome"] == "examined_no_findings"

    # Lifecycle, assurance budget, bounded reauthorization, and downstream stop.
    canonical_status_bytes = (ROOT / "docs/codex_handoff/pr_status.yaml").read_bytes()
    mirror_status_bytes = (ROOT / "machine_readable/pr_status.yaml").read_bytes()
    assert canonical_status_bytes == mirror_status_bytes
    status = yaml.safe_load(canonical_status_bytes)
    pr289 = status["stacked_pr_execution"]["prs"]["PR-289"]
    pr290 = status["stacked_pr_execution"]["prs"]["PR-290"]
    assert pr289["lifecycle"] == run_plan["lifecycle_state"] == "REVIEWED"
    assert pr289["predecessor_pr"] == "PR-288"
    assert pr289["base_sha"] == pr289["predecessor_sealed_sha"] == BASE_SHA
    assert pr289["production_hash"] == final_seal["production_hash"]
    assert pr289["dependency_hashes"] == run_plan["dependency_hashes"]
    assert pr289["assurance_budget"] == {"maximum": 16, "consumed": 14}
    assert run_plan["assurance_budget"] == {"maximum": 16, "consumed": 14}
    exception = run_plan["budget_exception"]
    assert exception["run_id"] == RUN_ID
    assert exception["work_unit_id"] == "PR-289"
    assert exception["additional_assignments"] == 1
    assert exception["allowed_workflow_role"] == "reviewer"
    assert exception["allowed_assignment_ids"] == [ASSIGNMENT_ID]
    assert exception["single_use"] is True
    assert 14 + exception["additional_assignments"] == 15
    assert pr290["lifecycle"] == "PLANNED"
    assert pr290["gate_dispositions"] == {"eligibility": "INELIGIBLE"}
    assert pr290["assurance_budget"] == {"maximum": 16, "consumed": 0}

    # No publication mutation is represented locally: no candidate remote ref,
    # no PR URL, no pushed ref, no seal lifecycle promotion, and no merge commit.
    assert pr289["sealed_head"] is None
    assert pr289["pushed_ref"] is None
    assert pr289["pr_url"] is None
    assert run_plan["github_pr_created_by_harness"] is False
    assert run_plan["publication_mode"] == "external_publisher_only"
    assert status["stacked_pr_execution"]["merge_policy"] == "HUMAN_ONLY"
    refs = git(
        "for-each-ref",
        "--format=%(refname) %(objectname)",
        LOCAL_REF,
        REMOTE_CANDIDATE_REF,
    ).decode().splitlines()
    assert refs == [f"{LOCAL_REF} {FINAL_SHA}"]

    print(
        json.dumps(
            {
                "ok": True,
                "run_id": RUN_ID,
                "assignment_id": ASSIGNMENT_ID,
                "candidate_sha": FINAL_SHA,
                "base_sha": BASE_SHA,
                "candidate_commit_count": len(commits),
                "unique_stable_patch_id_count": len(set(actual_patch_ids)),
                "carried_forward_command_ids": carried,
                "fresh_metadata_command_ids": fresh,
                "review_chronology": [
                    "R3_REPLAYCLAIM_FAIL",
                    "R3_PHYSCODE_ERROR_INCONCLUSIVE",
                    "R4_ERROR_INCONCLUSIVE_PRE_EXPOSURE_OBSERVATION",
                    "R5_PHYSCODE_PASS",
                    "R5_REPLAYCLAIM_PASS",
                ],
                "assurance_pre_closeout": "14/16",
                "assurance_projected_after_closeout": "15/16",
                "pr290": "PLANNED/INELIGIBLE 0/16",
                "publication_mutation": "NONE_REPRESENTED_BY_LOCAL_STATUS_AND_REFS",
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
