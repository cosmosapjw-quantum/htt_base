#!/usr/bin/env python3
"""Bounded read-only oracle for the frozen PR-283 final closeout."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[5]
HARNESS_SCRIPTS = REPO / ".agent-harness" / "scripts"
sys.path.insert(0, str(HARNESS_SCRIPTS))

from publication_integrity import (  # noqa: E402
    canonical_sha256,
    load_publication_policy,
    validate_candidate_seal_payload,
    validate_integration_receipt_payload,
)


RUN_ID = "pr283-final-integration-closeout-20260810"
ASSIGNMENT_ID = "A-PR283-FINAL-CLOSEOUT"
R2_SHA = "6fa98399dfe8b0a0735f9938063420457cda7688"
FINAL_SHA = "b6b6952d52f59bbe05477ef3b02292a98fe92baa"
TARGET_SHA = "ff9ef9f45747e559c5343b463cf010dfc3a7432a"
FINAL_TREE = "3f11a22c9e1a0374208596f146bd7def72ff5a1b"
PRODUCTION_HASH = "3d8aa16fe56b8111ad382780c60779d8a091e95cab3d0f4f7c76dcd2b1ba1a7d"
FINAL_SEAL_PATH = REPO / ".prguard/runtime/PR283_FINAL_CANDIDATE_SEAL.json"
FINAL_RECEIPT_PATH = REPO / ".prguard/runtime/PR283_FINAL_INTEGRATION_REHEARSAL.json"
R2_SEAL_PATH = REPO / ".prguard/runtime/PR283_R2_CANDIDATE_SEAL.json"
R2_RECEIPT_PATH = REPO / ".prguard/runtime/PR283_R2_INTEGRATION_REHEARSAL.json"
ASSIGNMENT_PATH = (
    REPO / ".agent-harness/runs" / RUN_ID / "assignments" / f"{ASSIGNMENT_ID}.json"
)
CONTEXT_INDEX_PATH = REPO / ".agent-harness/context/CONTEXT_INDEX.json"
RUN_PLAN_PATH = REPO / ".agent-harness/runs" / RUN_ID / "RUN_PLAN.json"
STATUS_PATH = REPO / "docs/codex_handoff/pr_status.yaml"
MIRROR_STATUS_PATH = REPO / "machine_readable/pr_status.yaml"
POLICY_PATH = REPO / "docs/research_program/post_pr275/pr283_publication_policy.json"
R2_RUN = REPO / ".agent-harness/runs/pr283-frozen-findings-rereview-20260810"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str, input_bytes: bytes | None = None) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=REPO,
        input=input_bytes,
        check=True,
        capture_output=True,
    ).stdout.decode("utf-8").strip()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def patch_id(commit: str) -> str:
    shown = subprocess.run(
        ["git", "show", "--pretty=format:", "--binary", "--full-index", commit],
        cwd=REPO,
        check=True,
        capture_output=True,
    ).stdout
    computed = subprocess.run(
        ["git", "patch-id", "--stable"],
        cwd=REPO,
        input=shown,
        check=True,
        capture_output=True,
    ).stdout.decode("ascii").strip()
    require(bool(computed), f"empty stable patch ID for {commit}")
    return computed.split()[0]


def main() -> None:
    assignment = load_json(ASSIGNMENT_PATH)
    context = load_json(CONTEXT_INDEX_PATH)
    run_plan = load_json(RUN_PLAN_PATH)
    final_seal = load_json(FINAL_SEAL_PATH)
    final_receipt = load_json(FINAL_RECEIPT_PATH)
    r2_seal = load_json(R2_SEAL_PATH)
    r2_receipt = load_json(R2_RECEIPT_PATH)
    policy = load_json(POLICY_PATH)
    status = yaml.safe_load(STATUS_PATH.read_text(encoding="utf-8"))

    required_hashes = {
        row["path"]: sha256(REPO / row["path"])
        for row in assignment["required_inputs"]
    }
    require(
        all(
            required_hashes[row["path"]] == row["sha256"]
            for row in assignment["required_inputs"]
        ),
        "registered input hash drift",
    )
    require(
        context["context_version"] == assignment["context_version"],
        "assignment context version drift",
    )

    head = git("rev-parse", "HEAD")
    tree = git("rev-parse", "HEAD^{tree}")
    merge_base = git("merge-base", TARGET_SHA, "HEAD")
    local_target = git("rev-parse", "refs/remotes/origin/research/pr04-multicomponent")
    require(head == FINAL_SHA, "final HEAD drift")
    require(tree == FINAL_TREE, "final tree drift")
    require(merge_base == TARGET_SHA, "merge base drift")
    require(local_target == TARGET_SHA, "local exact target drift")
    require(not git("status", "--porcelain=v1"), "tracked or unignored worktree drift")

    seal_errors = validate_candidate_seal_payload(final_seal, repo=REPO)
    require(not seal_errors, f"final seal invalid: {seal_errors}")
    _, loaded_policy = load_publication_policy(
        REPO, str(final_seal["integration_policy"]["path"]),
        expected_sha256=final_seal["integration_policy"]["sha256"],
    )
    receipt_errors = validate_integration_receipt_payload(
        final_receipt,
        seal=final_seal,
        policy=loaded_policy,
        now=datetime.now(timezone.utc),
        repo=REPO,
    )
    require(not receipt_errors, f"final integration receipt invalid: {receipt_errors}")

    patch_rows = final_seal["stable_patch_ids"]
    recomputed_patch_rows = [
        {"commit": row["commit"], "stable_patch_id": patch_id(row["commit"])}
        for row in patch_rows
    ]
    require(recomputed_patch_rows == patch_rows, "stable patch inventory drift")
    patch_ids = [row["stable_patch_id"] for row in patch_rows]
    require(len(patch_ids) == 8 and len(set(patch_ids)) == 8, "patch IDs not unique")
    require(
        final_seal["stable_patch_ids_sha256"]
        == canonical_sha256({"stable_patch_ids": patch_rows}),
        "stable patch inventory checksum drift",
    )

    require(final_seal["production_hash"] == PRODUCTION_HASH, "final production hash drift")
    require(r2_seal["production_hash"] == PRODUCTION_HASH, "R2 production hash drift")
    prior_results = []
    for name in (
        "A-PR283-R2-CODE.json",
        "A-PR283-R2-PHYSMATH.json",
        "A-PR283-R2-CLAIM.json",
        "A-PR283-R2-REPLAY.json",
    ):
        row = load_json(R2_RUN / "results" / name)
        require(row["status"] == "pass" and row["gate_disposition"] == "PASS", f"prior PASS drift: {name}")
        require(row["candidate_binding"]["candidate_sha"] == R2_SHA, f"prior candidate drift: {name}")
        require(row["candidate_binding"]["production_hash"] == PRODUCTION_HASH, f"prior production drift: {name}")
        prior_results.append(name)
    merged = load_json(R2_RUN / "MERGED_RESULTS.json")
    require(merged["process_status"] == "STRUCTURALLY_VALID", "prior merge status drift")
    require(merged["result_count"] == 4 and not merged["findings"] and not merged["conflicts"] and not merged["errors"], "prior merged result drift")

    post_r2_paths = git("diff", "--name-only", f"{R2_SHA}..{FINAL_SHA}").splitlines()
    expected_post_r2_paths = sorted(
        [
            ".agent-harness/scripts/integration_rehearsal.py",
            "docs/PR_DELTAS/pr-283.md",
            "docs/codex_handoff/pr_status.yaml",
            "machine_readable/pr_status.yaml",
            "scripts/codex_harness/test_publication_integrity.py",
        ]
    )
    require(sorted(post_r2_paths) == expected_post_r2_paths, "post-R2 scope drift")

    require(r2_receipt["status"] == "FAIL", "historical failed rehearsal not preserved")
    require(len(r2_receipt["commands"]) == 6, "historical failure command count drift")
    require(all(row["returncode"] == 0 for row in r2_receipt["commands"][:5]), "historical pre-failure command drift")
    require(r2_receipt["commands"][5]["id"] == "pr283-portable-clean-replay", "historical failure location drift")
    require(r2_receipt["commands"][5]["returncode"] != 0, "historical failure was erased")

    required_ids = [row["id"] for row in policy["required_commands"]]
    receipt_ids = [row["id"] for row in final_receipt["commands"]]
    require(final_receipt["status"] == "PASS", "final receipt not PASS")
    require(len(receipt_ids) == 11 and receipt_ids == required_ids, "final policy command coverage drift")
    require(all(row["returncode"] == 0 and row["timed_out"] is False for row in final_receipt["commands"]), "final command failure")
    require(final_receipt["latest_target_sha"] == TARGET_SHA, "final receipt target drift")
    require(final_receipt["merged_tree_sha"] == FINAL_TREE, "final merged tree drift")

    portable_run = subprocess.run(
        [sys.executable, "-B", "scripts/codex_harness/run_pr283_weak_identification.py", "portable"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    portable = json.loads(portable_run.stdout)
    manifest = portable["tracked_source_manifest"]
    require(manifest["file_count"] == 5867, "portable file count drift")
    require(portable["source_root_differs_from_execution_root"] is True, "portable clean-root separation drift")
    require(portable["exact_command_exit_code"] == 0, "portable nested replay failed")
    require(
        portable["source_root_pre_hash"]
        == portable["source_root_post_hash"]
        == portable["clean_root_pre_hash"]
        == portable["clean_root_post_hash"]
        == manifest["manifest_sha256"],
        "portable manifest invariance drift",
    )

    stack = status["stacked_pr_execution"]
    pr283 = stack["prs"]["PR-283"]
    pr284 = stack["prs"]["PR-284"]
    require(STATUS_PATH.read_bytes() == MIRROR_STATUS_PATH.read_bytes(), "status mirror drift")
    require(stack["target_sha"] == TARGET_SHA and stack["merge_policy"] == "HUMAN_ONLY", "stack target or merge policy drift")
    require(pr283["lifecycle"] == "REVIEWED", "PR-283 lifecycle drift")
    require(pr283["lifecycle_history"] == ["PLANNED", "ACTIVE", "IMPLEMENTED", "VALIDATED", "REVIEWED"], "PR-283 lifecycle history drift")
    require(pr283["assurance_budget"] == {"maximum": 16, "consumed": 13}, "PR-283 assurance drift")
    require(run_plan["assurance_budget"] == {"maximum": 16, "consumed": 13}, "assignment-start assurance drift")
    require(pr284["lifecycle"] == "PLANNED", "PR-284 lifecycle drift")
    require(pr284["gate_dispositions"] == {"eligibility": "INELIGIBLE"}, "PR-284 deferral drift")
    require(pr284["assurance_budget"] == {"maximum": 16, "consumed": 0}, "PR-284 zero-budget drift")
    require("merge" in policy["attended_publication"]["forbidden_actions"], "human-only merge refusal drift")
    require(policy["ordinary_agent_push_forbidden"] is True, "ordinary agent push refusal drift")
    require(policy["ordinary_agent_pr_mutation_forbidden"] is True, "ordinary agent PR mutation refusal drift")

    output = {
        "schema_version": 1,
        "oracle_id": "pr283-final-closeout",
        "run_id": RUN_ID,
        "assignment_id": ASSIGNMENT_ID,
        "status": "PASS",
        "checks": {
            "required_input_hashes": f"{len(required_hashes)}/{len(required_hashes)}",
            "context_version": context["context_version"],
            "head": head,
            "tree": tree,
            "merge_base": merge_base,
            "exact_target": local_target,
            "stable_patch_count": len(patch_ids),
            "stable_patch_unique_count": len(set(patch_ids)),
            "production_hash": PRODUCTION_HASH,
            "prior_pass_results": prior_results,
            "post_r2_paths": post_r2_paths,
            "preserved_rehearsal_status": r2_receipt["status"],
            "final_rehearsal_status": final_receipt["status"],
            "final_policy_command_count": len(receipt_ids),
            "portable_file_count": manifest["file_count"],
            "portable_manifest_sha256": manifest["manifest_sha256"],
            "lifecycle": pr283["lifecycle"],
            "assurance_before_assignment": pr283["assurance_budget"],
            "pr284_assurance": pr284["assurance_budget"],
            "merge_policy": stack["merge_policy"],
            "ordinary_agent_push_forbidden": policy["ordinary_agent_push_forbidden"],
            "ordinary_agent_pr_mutation_forbidden": policy["ordinary_agent_pr_mutation_forbidden"],
        },
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
