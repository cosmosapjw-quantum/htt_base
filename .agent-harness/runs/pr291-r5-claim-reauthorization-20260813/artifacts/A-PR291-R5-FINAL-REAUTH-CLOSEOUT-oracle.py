#!/usr/bin/env python3
"""Metadata-only failed-closeout oracle for PR-291 R5 reauthorization."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[4]
RUN = ROOT / ".agent-harness/runs/pr291-r5-claim-reauthorization-20260813"
ASSIGNMENT_ID = "A-PR291-R5-FINAL-REAUTH-CLOSEOUT"
CONTEXT_VERSION = "e9b385d7fbc4f8e47c97c3b0c7edae4e522d9be4e025d9342e26ab24829e3019"
BASE = "06ac20605ebc371b0f97ad6e91c802a51a9bf764"
FIRST_R5 = "5395853386b08b1fbf0b56a9e6c7a2a6e104ae5a"
HEAD = "82532a2a71abc385f1176dce4b99a4917929155d"
TREE = "68e3a83249ada011f984b67078c003086b1fc6aa"
FINAL_SEAL_FILE_SHA256 = "7d79f1858b8e3bb63d7dbcd1af51e3d480d76ab9a3c8170d702980d0cd0cb9d1"
FINAL_SEAL_SHA256 = "c9e2b7a8ee86f8951b5bf90175033d5a45824a5487542f1cd9ef5b7c56b8b348"
RECEIPT_SHA256 = "322d30749c3dc1e812882ab8196df9567c6f21a0f41a54dc13078383dad9b592"
TARGET = "refs/remotes/origin/changeset/pr290-planck-native-replay-recovery-20260811"


def load_json(path: str | Path) -> dict:
    with (ROOT / path).open(encoding="utf-8") as handle:
        return json.load(handle)


def sha256(path: str | Path) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def git(*args: str, input_text: str | None = None) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        text=True,
        input=input_text,
        capture_output=True,
    ).stdout.strip()


def patch_id(commit: str) -> str:
    patch = git("show", "--pretty=format:", commit)
    output = git("patch-id", "--stable", input_text=patch)
    return output.split()[0]


def git_bytes(*args: str) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True
    ).stdout


assignment = load_json(RUN / "assignments" / f"{ASSIGNMENT_ID}.json")
context = load_json(".agent-harness/context/CONTEXT_INDEX.json")
plan = load_json(RUN / "RUN_PLAN.json")
seal = load_json(".prguard/runtime/PR291_R5_FINAL_CANDIDATE_SEAL.json")
receipt = load_json("docs/research_program/post_pr275/data_runs/cf4/PR291_NONEXECUTION_RECEIPT.json")
policy = load_json("docs/research_program/post_pr275/pr291_publication_policy.json")
ordinary_summary = load_json(".agent-harness/runs/pr291-authorized-r5-review-20260813/RUN_SUMMARY.json")
ordinary_merged = load_json(".agent-harness/runs/pr291-authorized-r5-review-20260813/MERGED_RESULTS.json")
extension_summary = load_json(".agent-harness/runs/pr291-r5-claim-closeout-extension-20260813/RUN_SUMMARY.json")
extension_merged = load_json(".agent-harness/runs/pr291-r5-claim-closeout-extension-20260813/MERGED_RESULTS.json")
code = load_json(".agent-harness/runs/pr291-authorized-r5-review-20260813/results/A-PR291-R5-CODE-REPLAY.json")
physstat = load_json(".agent-harness/runs/pr291-authorized-r5-review-20260813/results/A-PR291-R5-PHYSSTAT.json")
first_claim = load_json(".agent-harness/runs/pr291-r5-claim-closeout-extension-20260813/results/A-PR291-R5-CLAIM.json")
first_closeout = load_json(".agent-harness/runs/pr291-r5-claim-closeout-extension-20260813/results/A-PR291-R5-FINAL-CLOSEOUT.json")
fresh_claim = load_json(RUN / "results/A-PR291-R5-CLAIM-CODE-REVIEW.json")
with (ROOT / "docs/codex_handoff/pr_status.yaml").open(encoding="utf-8") as handle:
    status_document = yaml.safe_load(handle)
    statuses = status_document["stacked_pr_execution"]["prs"]

assert assignment["assignment_id"] == ASSIGNMENT_ID
assert assignment["context_version"] == context["context_version"] == plan["context_version"] == CONTEXT_VERSION
assert sha256(".prguard/runtime/PR291_R5_FINAL_CANDIDATE_SEAL.json") == FINAL_SEAL_FILE_SHA256
assert seal["seal_sha256"] == FINAL_SEAL_SHA256
assert seal["base_sha"] == seal["merge_base_sha"] == BASE
assert seal["candidate_sha"] == HEAD and seal["candidate_tree_sha"] == TREE and seal["dirty"] is False
assert git("rev-parse", "HEAD") == HEAD and git("rev-parse", "HEAD^{tree}") == TREE
assert git("rev-parse", TARGET) == BASE and git("merge-base", TARGET, "HEAD") == BASE
assert git("status", "--porcelain=v2", "--untracked-files=all") == ""

commits = git("rev-list", "--reverse", f"{BASE}..HEAD").splitlines()
assert commits == seal["candidate_commits"]
computed_patch_ids = [patch_id(commit) for commit in commits]
sealed_patch_ids = [entry["stable_patch_id"] for entry in seal["stable_patch_ids"]]
assert computed_patch_ids == sealed_patch_ids and len(set(computed_patch_ids)) == len(computed_patch_ids) == 15

post_first_r5 = set(git("diff", "--name-only", f"{FIRST_R5}..HEAD").splitlines())
assert post_first_r5 == {
    "docs/PR_DELTAS/pr-291.md",
    "docs/codex_handoff/pr_status.yaml",
    "docs/research_program/post_pr275/data_runs/cf4/PR291_NONEXECUTION_RECEIPT.json",
    "htt/src/common/semantic_guards/no_overclaim.py",
    "machine_readable/pr_status.yaml",
    "tests/contracts/test_claim_language_lint.py",
}
numerical_paths = (
    "htt/obsstat/cf4_post275_lane.py",
    "htt/src/common/cf4_observed_lane_activation.py",
    "scripts/codex_harness/run_pr291_cf4_lane.py",
    "tests/integration/test_cf4_post275_lane.py",
)
for path in numerical_paths:
    assert hashlib.sha256(git_bytes("show", f"{FIRST_R5}:{path}")).hexdigest() == sha256(path)

assert sha256("docs/research_program/post_pr275/data_runs/cf4/PR291_NONEXECUTION_RECEIPT.json") == RECEIPT_SHA256
assert receipt["terminal"] == "BLOCKED_PREDECESSOR_FINAL_SUCCESS"
assert receipt["observed_data_executed"] is False and receipt["public_use"] is False
assert receipt["network_or_download_side_effect"] is False and receipt["numeric_outputs_written"] == []

assert ordinary_summary["lifecycle_state"] == extension_summary["lifecycle_state"] == plan["lifecycle_state"] == "VALIDATED"
assert ordinary_merged["process_status"] == extension_merged["process_status"] == "STRUCTURALLY_VALID"
assert code["status"] == "pass" and code["gate_disposition"] == "PASS"
assert physstat["status"] == "pass" and physstat["gate_disposition"] == "PASS"
assert first_claim["status"] == first_closeout["status"] == "fail"
assert first_claim["gate_disposition"] == first_closeout["gate_disposition"] == "FAIL"
assert fresh_claim["status"] == "fail" and fresh_claim["gate_disposition"] == "FAIL"
assert [finding["finding_id"] for finding in fresh_claim["findings"]] == ["F-PR291-R5-CLAIM-QUANTIFIER-FN"]

pr291 = statuses["PR-291"]
pr292 = statuses["PR-292"]
assert pr291["lifecycle"] == "VALIDATED" and pr291["assurance_budget"] == {"maximum": 16, "consumed": 16}
assert pr291["authorized_assurance_extension_maximum"] == pr291["authorized_assurance_extension_consumed"] == 2
assert pr291["authorized_assurance_reauthorization_maximum"] == 2
assert pr291["sealed_head"] is pr291["pushed_ref"] is pr291["pr_url"] is None
assert pr292["lifecycle"] == "PLANNED" and pr292["gate_dispositions"]["eligibility"] == "INELIGIBLE"
assert pr292["assurance_budget"] == {"maximum": 16, "consumed": 0}
assert status_document["stacked_pr_execution"]["merge_policy"] == "HUMAN_ONLY"

exception = plan["budget_exception"]
assert exception["additional_assignments"] == 2 and exception["single_use"] is True
assert exception["allowed_assignment_ids"] == ["A-PR291-R5-CLAIM-CODE-REVIEW", ASSIGNMENT_ID]
assert policy["ordinary_agent_push_forbidden"] is True and policy["ordinary_agent_pr_mutation_forbidden"] is True
assert "merge" in policy["attended_publication"]["forbidden_actions"]

print(json.dumps({
    "status": "PASS",
    "closeout_disposition": "FAIL",
    "blocking_finding": "F-PR291-R5-CLAIM-QUANTIFIER-FN",
    "lifecycle_advance": False,
    "lifecycle_state": "VALIDATED",
    "ordinary_assurance": "16/16",
    "first_extension": "2/2",
    "reauthorization": "2/2",
    "carried_code_replay": "PASS",
    "carried_physstat": "PASS",
    "fresh_claim_code": "FAIL",
    "pr292": "PLANNED/INELIGIBLE",
    "publication": "NOT_AUTHORIZED_OR_PERFORMED",
}, sort_keys=True))
