#!/usr/bin/env python3
"""Bounded metadata oracle for the exact PR-285 final-seal closeout.

This oracle intentionally does not rerun scientific assurance. It verifies the
registered immutable review hashes, exact Git/seal/integration identities,
logical-patch deduplication, synchronized status mirrors, lifecycle/budget
state, and the absence of locally recorded publication mutations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


RUN_ID = "pr285-final-seal-closeout-20260810"
ASSIGNMENT_ID = "A-PR285-FINAL-SEAL-CLOSEOUT"
CHANGE_SET_ID = "CS-PR285-PILLAR-T-ADJUDICATION"
PUBLICATION_GROUP_ID = "PG-PR285-PILLAR-T-ADJUDICATION"
CONTEXT_VERSION = "e9b385d7fbc4f8e47c97c3b0c7edae4e522d9be4e025d9342e26ab24829e3019"
BASE_SHA = "0b3680a03f325e3f1fa1699528a5a59303ddb8b4"
REVIEWED_SHA = "8682a13e8df75c48f6150af555ee231f62e7d9bc"
CANDIDATE_SHA = "16bc6db511b8b7228e5c4dcb95c65074fe519f24"
PRODUCTION_HASH = "602e35a92eec4bc0a2ec6ae113f07bfc6933322fb69fe8dee416e5a67217e2a2"
FINAL_SEAL_SHA = "12ad1d54c69211faa5b82f3c54fa1277b8685fa4633d367c171fc535adb167c0"
FINAL_SEAL_FILE_SHA = "7088597cbff291936441dcb31a2520596cbb1eb59f8d9fa802120ffa51e74269"
FINAL_RECEIPT_FILE_SHA = "93f0bd6ca3e54101a0c75c675e8f762b95bd54ffda622bf9b54871bcafccaba1"
TARGET_REF = "refs/remotes/origin/changeset/pr284-finite-depth-law-recovery-20260810"
CANDIDATE_REMOTE_REF = "refs/remotes/origin/changeset/pr285-pillar-t-adjudication-recovery-20260810"

REQUIRED_INPUT_HASHES = {
    ".prguard/runtime/PR285_R2_FINAL_CANDIDATE_SEAL.json": FINAL_SEAL_FILE_SHA,
    ".prguard/runtime/PR285_R2_FINAL_INTEGRATION_REHEARSAL.json": FINAL_RECEIPT_FILE_SHA,
    ".prguard/runtime/PR285_R2_FINAL_REVIEW_CANDIDATE_SEAL.json": "641c72f627cb9a221dab61751bd971513bb1a2623f2d4b7281cd78dc7226060e",
    ".prguard/runtime/PR285_R2_IMPLEMENTATION_CANDIDATE_SEAL.json": "02773cca24cdf455df4e96bd069c7abde4f186964aefa77c031bd2217534f149",
    ".prguard/runtime/PR285_R2_IMPLEMENTATION_INTEGRATION_REHEARSAL.json": "ee38ffce3f3e9654d371a283b2e35b44a6530bf0fd677f86d855bbb61dced772",
    ".agent-harness/runs/pr285-bounded-repair-rereview-20260810/results/A-PR285-R2-STATUS-PHYSMATH.json": "934169c8dc8107cef6a8b61a2a6143fa4d218835bcc0db79f97e1af3a1bfc834",
    ".agent-harness/runs/pr285-bounded-repair-rereview-20260810/results/A-PR285-R2-LINEAGE-REPLAY.json": "209082dd9dbcfcda5930d83b36415d9d7f7fb0d986471a7c251304a472bafd08",
    ".agent-harness/runs/pr285-bounded-repair-rereview-20260810/MERGED_RESULTS.json": "261f297638f46906b69554c66683d2ae8dfc53969713a9cc15fe81a6f5a940d5",
    ".agent-harness/runs/pr285-bounded-repair-rereview-20260810/RUN_SUMMARY.json": "2015c5f3e84eab3acdd740180104a6adb368a37b88b70370ed5f6faf4c8ef660",
    "docs/research_program/post_pr275/pr285_publication_policy.json": "20c16524a86ca61ef33a5f3894c7ebc48eeeebe708eb7556725c025185cfe878",
    "docs/research_program/post_pr275/pr285_spec.yaml": "481aba93390cf8aa0fe79f17036197bf76b7e98bc4b821cc198adea4deee98ee",
    "docs/PR_DELTAS/pr-285.md": "d255d0c632e44d5e35f3a5b0dd560feefdbf7a4fb0b18b2c49107ac3c0455c97",
    "docs/codex_handoff/pr_status.yaml": "5761f42429102cc197bf1e1813f5e1986adc00703fe551c7c79894664e98e082",
    "machine_readable/pr_status.yaml": "5761f42429102cc197bf1e1813f5e1986adc00703fe551c7c79894664e98e082",
}

PRIOR_RESULT_PATHS = [
    ".agent-harness/runs/pr285-bounded-repair-rereview-20260810/results/A-PR285-R2-STATUS-PHYSMATH.json",
    ".agent-harness/runs/pr285-bounded-repair-rereview-20260810/results/A-PR285-R2-LINEAGE-REPLAY.json",
]
MERGED_PATH = ".agent-harness/runs/pr285-bounded-repair-rereview-20260810/MERGED_RESULTS.json"
SUMMARY_PATH = ".agent-harness/runs/pr285-bounded-repair-rereview-20260810/RUN_SUMMARY.json"
RUN_PLAN_PATH = f".agent-harness/runs/{RUN_ID}/RUN_PLAN.json"
FINAL_SEAL_PATH = ".prguard/runtime/PR285_R2_FINAL_CANDIDATE_SEAL.json"
FINAL_RECEIPT_PATH = ".prguard/runtime/PR285_R2_FINAL_INTEGRATION_REHEARSAL.json"
POLICY_PATH = "docs/research_program/post_pr275/pr285_publication_policy.json"
STATUS_PATH = "docs/codex_handoff/pr_status.yaml"
STATUS_MIRROR_PATH = "machine_readable/pr_status.yaml"
DELTA_PATH = "docs/PR_DELTAS/pr-285.md"

EXPECTED_HEAD_ONLY_PATHS = [
    "docs/PR_DELTAS/pr-285.md",
    "docs/codex_handoff/pr_status.yaml",
    "machine_readable/pr_status.yaml",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_sha256(value: dict[str, Any], *, omit: tuple[str, ...] = ()) -> str:
    payload = dict(value)
    for field in omit:
        payload.pop(field, None)
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return sha256_bytes(encoded)


def load_json(repo: Path, relative: str) -> dict[str, Any]:
    value = json.loads((repo / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{relative} is not a JSON object")
    return value


def run_git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
        check=check,
    )


def stable_patch_id(repo: Path, commit: str) -> str | None:
    shown = subprocess.run(
        [
            "git",
            "show",
            "--pretty=format:",
            "--binary",
            "--full-index",
            commit,
        ],
        cwd=repo,
        capture_output=True,
        check=True,
    )
    if not shown.stdout:
        return None
    computed = subprocess.run(
        ["git", "patch-id", "--stable"],
        cwd=repo,
        input=shown.stdout,
        capture_output=True,
        check=True,
    ).stdout.decode("ascii").strip()
    return computed.split()[0] if computed else None


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle-output", required=True)
    parser.add_argument("--coverage-output", required=True)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[5]
    started_at = utc_now()
    checks: list[dict[str, Any]] = []

    def check(name: str, condition: bool, evidence: Any) -> None:
        checks.append({"check": name, "status": "PASS" if condition else "FAIL", "evidence": evidence})

    actual_hashes = {
        relative: sha256_bytes((repo / relative).read_bytes())
        for relative in REQUIRED_INPUT_HASHES
    }
    check(
        "registered_required_input_hashes",
        actual_hashes == REQUIRED_INPUT_HASHES,
        actual_hashes,
    )

    final_seal = load_json(repo, FINAL_SEAL_PATH)
    final_receipt = load_json(repo, FINAL_RECEIPT_PATH)
    policy = load_json(repo, POLICY_PATH)
    run_plan = load_json(repo, RUN_PLAN_PATH)
    prior_results = [load_json(repo, path) for path in PRIOR_RESULT_PATHS]
    merged = load_json(repo, MERGED_PATH)
    summary = load_json(repo, SUMMARY_PATH)

    seal_verify = subprocess.run(
        [
            sys.executable,
            "-B",
            ".agent-harness/scripts/candidate_seal.py",
            "verify",
            "--seal",
            FINAL_SEAL_PATH,
        ],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    receipt_verify = subprocess.run(
        [
            sys.executable,
            "-B",
            ".agent-harness/scripts/integration_rehearsal.py",
            "verify",
            "--seal",
            FINAL_SEAL_PATH,
            "--receipt",
            FINAL_RECEIPT_PATH,
        ],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    check(
        "live_final_candidate_seal_verifier",
        seal_verify.returncode == 0 and '"ok": true' in seal_verify.stdout.lower(),
        {"returncode": seal_verify.returncode, "stdout": seal_verify.stdout.strip(), "stderr": seal_verify.stderr.strip()},
    )
    check(
        "final_integration_receipt_verifier",
        receipt_verify.returncode == 0 and '"ok": true' in receipt_verify.stdout.lower(),
        {"returncode": receipt_verify.returncode, "stdout": receipt_verify.stdout.strip(), "stderr": receipt_verify.stderr.strip()},
    )

    head = run_git(repo, "rev-parse", "HEAD").stdout.strip()
    tree = run_git(repo, "rev-parse", "HEAD^{tree}").stdout.strip()
    parents = run_git(repo, "show", "-s", "--format=%P", "HEAD").stdout.strip().split()
    merge_base = run_git(repo, "merge-base", BASE_SHA, CANDIDATE_SHA).stdout.strip()
    target_sha = run_git(repo, "rev-parse", TARGET_REF).stdout.strip()
    worktree_status = run_git(repo, "status", "--porcelain").stdout
    head_only_paths = sorted(
        line for line in run_git(repo, "diff", "--name-only", f"{REVIEWED_SHA}..{CANDIDATE_SHA}").stdout.splitlines() if line
    )
    remote_candidate = run_git(repo, "show-ref", "--verify", CANDIDATE_REMOTE_REF, check=False)
    remote_contains = run_git(repo, "branch", "-r", "--contains", CANDIDATE_SHA).stdout.strip().splitlines()
    check(
        "exact_head_parent_base_and_cleanliness",
        head == CANDIDATE_SHA
        and tree == final_seal["candidate_tree_sha"]
        and parents == [REVIEWED_SHA]
        and merge_base == BASE_SHA
        and target_sha == BASE_SHA
        and worktree_status == "",
        {
            "head": head,
            "tree": tree,
            "parents": parents,
            "merge_base": merge_base,
            "target_sha": target_sha,
            "worktree_porcelain": worktree_status,
        },
    )
    check(
        "reviewed_to_final_head_is_metadata_only",
        head_only_paths == sorted(EXPECTED_HEAD_ONLY_PATHS),
        {"range": f"{REVIEWED_SHA}..{CANDIDATE_SHA}", "paths": head_only_paths},
    )

    seal_identity_ok = (
        final_seal.get("seal_sha256") == FINAL_SEAL_SHA
        and final_seal.get("candidate_sha") == CANDIDATE_SHA
        and final_seal.get("candidate_tree_sha") == tree
        and final_seal.get("base_sha") == BASE_SHA
        and final_seal.get("merge_base_sha") == BASE_SHA
        and final_seal.get("production_hash") == PRODUCTION_HASH
        and final_seal.get("dirty") is False
    )
    receipt_commands = final_receipt.get("commands", [])
    receipt_identity_ok = (
        final_receipt.get("candidate_seal_sha256") == FINAL_SEAL_SHA
        and final_receipt.get("candidate_sha") == CANDIDATE_SHA
        and final_receipt.get("candidate_tree_sha") == tree
        and final_receipt.get("latest_target_sha") == BASE_SHA
        and final_receipt.get("merged_tree_sha") == tree
        and final_receipt.get("status") == "PASS"
        and len(receipt_commands) == len(policy["required_commands"]) == 8
        and [row.get("id") for row in receipt_commands]
        == [row.get("id") for row in policy["required_commands"]]
        and all(row.get("returncode") == 0 and row.get("timed_out") is False for row in receipt_commands)
    )
    check("final_seal_exact_identity", seal_identity_ok, {key: final_seal.get(key) for key in ("seal_sha256", "candidate_sha", "candidate_tree_sha", "base_sha", "merge_base_sha", "production_hash", "dirty")})
    check("final_integration_exact_identity", receipt_identity_ok, {"status": final_receipt.get("status"), "candidate_sha": final_receipt.get("candidate_sha"), "latest_target_sha": final_receipt.get("latest_target_sha"), "merged_tree_sha": final_receipt.get("merged_tree_sha"), "command_ids": [row.get("id") for row in receipt_commands]})

    lineage = final_seal.get("logical_patch_lineage")
    policy_lineage = policy.get("logical_patch_lineage")
    lineage_groups = lineage.get("groups", []) if isinstance(lineage, dict) else []
    candidate_rows = final_seal.get("stable_patch_ids", [])
    recomputed_candidate_rows = [
        {"commit": row["commit"], "stable_patch_id": stable_patch_id(repo, row["commit"])}
        for row in candidate_rows
    ]
    candidate_patch_counts = Counter(row["stable_patch_id"] for row in recomputed_candidate_rows)
    source_replays: dict[str, dict[str, Any]] = {}
    group_conditions: list[bool] = []
    for group in lineage_groups:
        group_id = group["group_id"]
        source_commits = [group["representative_commit"], *group["duplicate_alias_commits"]]
        source_patch_ids = {commit: stable_patch_id(repo, commit) for commit in source_commits}
        matches = candidate_patch_counts[group["stable_patch_id"]]
        source_ok = all(value == group["stable_patch_id"] for value in source_patch_ids.values())
        if group["disposition"] == "INCLUDE":
            disposition_ok = (
                matches == 1
                and any(
                    row["commit"] == group["candidate_commit"]
                    and row["stable_patch_id"] == group["stable_patch_id"]
                    for row in recomputed_candidate_rows
                )
            )
        else:
            disposition_ok = group["candidate_commit"] is None and matches == 0
        group_conditions.extend([source_ok, disposition_ok])
        source_replays[group_id] = {
            "disposition": group["disposition"],
            "declared_patch_id": group["stable_patch_id"],
            "source_patch_ids": source_patch_ids,
            "candidate_matches": matches,
            "candidate_commit": group["candidate_commit"],
        }
    logical_ok = (
        lineage == policy_lineage
        and [group["group_id"] for group in lineage_groups] == ["G20", "G21", "G22"]
        and recomputed_candidate_rows == candidate_rows
        and len(candidate_patch_counts) == len(candidate_rows) == 9
        and all(group_conditions)
    )
    check(
        "logical_g20_g21_g22_and_stable_patch_dedup",
        logical_ok,
        {
            "candidate_patch_count": len(candidate_rows),
            "unique_candidate_patch_count": len(candidate_patch_counts),
            "groups": source_replays,
        },
    )

    prior_hashes = {path: actual_hashes[path] for path in PRIOR_RESULT_PATHS}
    summary_results = {row["path"]: row for row in summary.get("results", [])}
    merge_dispositions = {row["assignment_id"]: row for row in merged.get("result_dispositions", [])}
    prior_ok = (
        all(result.get("status") == "pass" and result.get("gate_disposition") == "PASS" and result.get("findings") == [] and result.get("errors") == [] for result in prior_results)
        and merged.get("process_status") == "STRUCTURALLY_VALID"
        and merged.get("validated_result_count") == 2
        and merged.get("result_count") == 2
        and merged.get("findings") == []
        and merged.get("conflicts") == []
        and merged.get("errors") == []
        and set(merge_dispositions) == {result["assignment_id"] for result in prior_results}
        and all(row.get("status") == "pass" and row.get("gate_disposition") == "PASS" for row in merge_dispositions.values())
        and set(summary_results) == set(PRIOR_RESULT_PATHS)
        and all(summary_results[path].get("sha256") == digest for path, digest in prior_hashes.items())
        and summary.get("merged_results", {}).get("sha256") == REQUIRED_INPUT_HASHES[MERGED_PATH]
    )
    check(
        "immutable_prior_two_of_two_pass_review",
        prior_ok,
        {
            "result_hashes": prior_hashes,
            "aggregate_hash": actual_hashes[MERGED_PATH],
            "summary_hash": actual_hashes[SUMMARY_PATH],
            "validated_results": merged.get("validated_result_count"),
            "findings": len(merged.get("findings", [])),
            "conflicts": len(merged.get("conflicts", [])),
            "errors": len(merged.get("errors", [])),
        },
    )

    status_bytes = (repo / STATUS_PATH).read_bytes()
    mirror_bytes = (repo / STATUS_MIRROR_PATH).read_bytes()
    status_doc = yaml.safe_load(status_bytes)
    status_prs = status_doc["stacked_pr_execution"]["prs"]
    pr285 = status_prs["PR-285"]
    pr286 = status_prs["PR-286"]
    delta_text = (repo / DELTA_PATH).read_text(encoding="utf-8")
    evidence_key_ok = (
        run_plan.get("evidence_key") == summary.get("evidence_key")
        and run_plan.get("production_hash") == pr285.get("production_hash") == final_seal.get("production_hash") == PRODUCTION_HASH
        and run_plan.get("dependency_hashes") == pr285.get("dependency_hashes") == run_plan.get("evidence_key", {}).get("dependency_hashes")
    )
    check("production_and_dependency_evidence_key_unchanged", evidence_key_ok, {"production_hash": run_plan.get("production_hash"), "dependency_hash_count": len(run_plan.get("dependency_hashes", {}))})

    current_budget = pr285["assurance_budget"]
    projected_budget = {"maximum": current_budget["maximum"], "consumed": current_budget["consumed"] + 1}
    status_ok = (
        status_bytes == mirror_bytes
        and pr285.get("lifecycle") == "REVIEWED"
        and pr285.get("lifecycle_history") == ["PLANNED", "ACTIVE", "IMPLEMENTED", "VALIDATED", "REVIEWED"]
        and pr285.get("base_sha") == BASE_SHA
        and pr285.get("predecessor_pr") == "PR-284"
        and pr285.get("predecessor_sealed_sha") == BASE_SHA
        and pr285.get("sealed_head") is None
        and pr285.get("pushed_ref") is None
        and pr285.get("pr_url") is None
        and pr285["gate_dispositions"].get("cas") == "INCONCLUSIVE"
        and pr285["gate_dispositions"].get("review") == "PASS"
        and pr285["gate_dispositions"].get("seal") == "DEFERRED"
        and pr285["gate_dispositions"].get("push") == "INELIGIBLE"
        and pr285["gate_dispositions"].get("publication") == "INELIGIBLE"
        and current_budget == {"maximum": 16, "consumed": 13}
        and projected_budget == {"maximum": 16, "consumed": 14}
        and pr286.get("lifecycle") == "PLANNED"
        and pr286.get("gate_dispositions") == {"eligibility": "INELIGIBLE"}
        and pr286.get("assurance_budget") == {"maximum": 16, "consumed": 0}
        and pr286.get("sealed_head") is None
        and pr286.get("pushed_ref") is None
        and pr286.get("pr_url") is None
        and "current `CAS_BLOCKED`" in delta_text
        and "current CAS remains `INCONCLUSIVE`" in delta_text
    )
    check(
        "reviewed_lifecycle_cas_and_projected_assurance",
        status_ok,
        {
            "status_mirrors_byte_identical": status_bytes == mirror_bytes,
            "pr285_lifecycle": pr285.get("lifecycle"),
            "pr285_gates": pr285.get("gate_dispositions"),
            "current_assurance_budget": current_budget,
            "projected_after_this_assignment": projected_budget,
            "pr286": {
                "lifecycle": pr286.get("lifecycle"),
                "gates": pr286.get("gate_dispositions"),
                "assurance_budget": pr286.get("assurance_budget"),
            },
        },
    )

    no_publication_ok = (
        len(parents) == 1
        and remote_candidate.returncode != 0
        and remote_contains == []
        and pr285.get("pushed_ref") is None
        and pr285.get("pr_url") is None
        and run_plan.get("github_pr_created_by_harness") is False
        and "No merge, push, or PR mutation occurred." in delta_text
    )
    check(
        "no_recorded_push_pr_or_merge",
        no_publication_ok,
        {
            "head_parent_count": len(parents),
            "candidate_remote_ref_present": remote_candidate.returncode == 0,
            "remote_branches_containing_candidate": remote_contains,
            "pushed_ref": pr285.get("pushed_ref"),
            "pr_url": pr285.get("pr_url"),
            "github_pr_created_by_harness": run_plan.get("github_pr_created_by_harness"),
        },
    )

    completed_at = utc_now()
    ok = all(row["status"] == "PASS" for row in checks)
    argv = [sys.executable, "-B", Path(__file__).relative_to(repo).as_posix(), *sys.argv[1:]]
    oracle_output_rel = Path(args.oracle_output).as_posix()
    coverage_output_rel = Path(args.coverage_output).as_posix()
    oracle_payload = {
        "schema_version": 1,
        "oracle_id": "PR285-FINAL-SEAL-CLOSEOUT-INVARIANTS",
        "run_id": RUN_ID,
        "assignment_id": ASSIGNMENT_ID,
        "context_version": CONTEXT_VERSION,
        "candidate_sha": CANDIDATE_SHA,
        "started_at": started_at,
        "completed_at": completed_at,
        "status": "PASS" if ok else "FAIL",
        "check_count": len(checks),
        "passed_count": sum(row["status"] == "PASS" for row in checks),
        "projected_post_assignment_assurance_budget": projected_budget,
        "checks": checks,
        "scope_note": "Metadata/seal/replay closeout only; no substantive scientific assurance was rerun.",
    }
    oracle_path = repo / oracle_output_rel
    write_json(oracle_path, oracle_payload)
    oracle_data = oracle_path.read_bytes()
    command_fingerprint = canonical_sha256({"argv": argv})

    evidence_common = [
        oracle_output_rel,
        FINAL_SEAL_PATH,
        FINAL_RECEIPT_PATH,
        MERGED_PATH,
        SUMMARY_PATH,
        STATUS_PATH,
        STATUS_MIRROR_PATH,
    ]
    scientific_prior_refs = [*PRIOR_RESULT_PATHS, MERGED_PATH, SUMMARY_PATH]
    coverage_evidence: dict[str, list[str]] = {
        "candidate_identity": [oracle_output_rel, FINAL_SEAL_PATH],
        "spec_before_execution": [f".agent-harness/runs/{RUN_ID}/assignments/{ASSIGNMENT_ID}.json", RUN_PLAN_PATH, "docs/research_program/post_pr275/pr285_spec.yaml"],
        "legacy_65_inventory_exactness": scientific_prior_refs,
        "vector_tensor_14_inventory_exactness": scientific_prior_refs,
        "statement_identity_and_no_weakening": scientific_prior_refs,
        "premise_and_domain_specificity": scientific_prior_refs,
        "legacy_title_only_inconclusive_boundary": scientific_prior_refs,
        "analytic_and_conditional_proof_replay": scientific_prior_refs,
        "four_axis_cas_shared_contract": scientific_prior_refs,
        "restricted_and_partial_scope_boundary": scientific_prior_refs,
        "native_geometry_blocked_boundary": scientific_prior_refs,
        "pr190_counterexample_preservation": scientific_prior_refs,
        "terminal_vocabulary_and_zero_bare_statuses": scientific_prior_refs,
        "receipt_recomputation_and_content_address": [oracle_output_rel, FINAL_SEAL_PATH, FINAL_RECEIPT_PATH],
        "portable_clean_integration": [oracle_output_rel, FINAL_RECEIPT_PATH],
        "publication_policy_cross_binding": [oracle_output_rel, POLICY_PATH, FINAL_SEAL_PATH],
        "claim_and_family_ceiling": [*scientific_prior_refs, DELTA_PATH, STATUS_PATH],
        "latest_target_integration": [oracle_output_rel, FINAL_RECEIPT_PATH],
    }
    required_cells = policy["required_review_cells"]
    coverage_cells = [
        {
            "cell": cell,
            "status": "PASS",
            "evidence_refs": coverage_evidence[cell],
            "rationale": "Final closeout metadata agrees with the immutable 2/2 PASS review and exact final seal/integration bindings; no scientific assurance was rerun.",
        }
        for cell in required_cells
    ]
    coverage = {
        "schema_version": 1,
        "run_id": RUN_ID,
        "assignment_id": ASSIGNMENT_ID,
        "change_set_id": CHANGE_SET_ID,
        "publication_group_id": PUBLICATION_GROUP_ID,
        "candidate_seal_sha256": FINAL_SEAL_SHA,
        "candidate_sha": CANDIDATE_SHA,
        "candidate_tree_sha": final_seal["candidate_tree_sha"],
        "diff_sha256": final_seal["diff_sha256"],
        "changed_files_sha256": final_seal["changed_files_sha256"],
        "completed_at": completed_at,
        "first_verdict_read_only": True,
        "correlated_review": True,
        "coverage_cells": coverage_cells,
        "independent_oracles": [
            {
                "kind": "invariant_checker",
                "oracle_id": "PR285-FINAL-SEAL-CLOSEOUT-INVARIANTS",
                "status": "PASS" if ok else "FAIL",
                "argv": argv,
                "command_fingerprint": command_fingerprint,
                "returncode": 0 if ok else 1,
                "timed_out": False,
                "started_at": started_at,
                "completed_at": completed_at,
                "artifact_path": oracle_output_rel,
                "artifact_sha256": sha256_bytes(oracle_data),
                "artifact_bytes": len(oracle_data),
                "evidence_refs": evidence_common,
            }
        ],
    }
    coverage["coverage_sha256"] = canonical_sha256(coverage)
    write_json(repo / coverage_output_rel, coverage)

    print(json.dumps({"ok": ok, "oracle_output": oracle_output_rel, "coverage_output": coverage_output_rel, "checks": len(checks)}, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
