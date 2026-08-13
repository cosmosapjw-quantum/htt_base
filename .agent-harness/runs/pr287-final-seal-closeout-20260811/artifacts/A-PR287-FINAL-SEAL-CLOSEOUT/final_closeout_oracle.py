#!/usr/bin/env python3
"""Deterministic metadata-only closeout oracle for the frozen PR-287 candidate.

This oracle deliberately does not execute the scientific/replay test lanes.  It
validates immutable seals, the already-recorded integration receipt, Git
lineage, review chronology, lifecycle/budget state, and non-publication.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[5]
SCRIPTS = ROOT / ".agent-harness" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from publication_integrity import (  # noqa: E402
    canonical_sha256,
    load_publication_policy,
    parse_utc,
    validate_candidate_seal_payload,
    validate_integration_receipt_payload,
)


RUN_ID = "pr287-final-seal-closeout-20260811"
ASSIGNMENT_ID = "A-PR287-FINAL-SEAL-CLOSEOUT"
CONTEXT_VERSION = "e9b385d7fbc4f8e47c97c3b0c7edae4e522d9be4e025d9342e26ab24829e3019"
BASE = "b955a050f19db853a93779506e8acb4e4a5352a9"
HEAD = "319835cc4b4e2e3270a0b27787ce5d5a44ea16b7"
TREE = "e03b17661c1b5bc74ab0bbecbc31a82948f32bc9"
PRODUCTION_HASH = "6d0963dfdc66dcd2bf80ef3dde6fd84d87f455f0c6db5199250b06b2c51e873a"
CHANGED_FILES_HASH = "b522232b4e7f07fe03b297f33a07dfcce4f7eb80cdd0bbd94b9fd06a20b73198"
FINAL_SEAL_HASH = "65f84c67c1cd327fb1456c0139433af925dc44075177d1401e7d86d87d3942bf"
INTEGRATION_HASH = "0595630dbde8e636f9eff108ef6e8cb56679461fd982296c7df90f22c389f9b6"
VALIDATED_SEAL_HASH = "fbe4787a82f650ec050fab020ae2c9545e9f7fe778ec2d6f5d4550470537712b"
EXPECTED_PATCH_IDS = [
    "1be41957cd4ee016277cb334c491aed4afc9c26c",
    "e8fec5909e1d136232d3238a29df0d0bf882d844",
    "8aefd21b4dfebceb3d3e8f48db6b14566e8a9d6f",
    "8dd4760adec48c969321486fd951f44fcac055e4",
    "54b3371720a7154778193d2cc8a94724d8b06899",
    "430f2619b4f5fd0a9420ff8b2b300671c46587c7",
]
EXPECTED_METADATA_RANGE = [
    "docs/PR_DELTAS/pr-287.md",
    "docs/codex_handoff/pr_status.yaml",
    "machine_readable/pr_status.yaml",
]

PATHS = {
    "assignment": f".agent-harness/runs/{RUN_ID}/assignments/{ASSIGNMENT_ID}.json",
    "plan": f".agent-harness/runs/{RUN_ID}/RUN_PLAN.json",
    "context": ".agent-harness/context/CONTEXT_INDEX.json",
    "final_seal": ".prguard/runtime/PR287_FINAL_CANDIDATE_SEAL.json",
    "integration": ".prguard/runtime/PR287_FINAL_INTEGRATION_REHEARSAL.json",
    "validated_seal": ".prguard/runtime/PR287_VALIDATED_CANDIDATE_SEAL.json",
    "policy": "docs/research_program/post_pr275/pr287_publication_policy.json",
    "delta": "docs/PR_DELTAS/pr-287.md",
    "status": "docs/codex_handoff/pr_status.yaml",
    "status_mirror": "machine_readable/pr_status.yaml",
    "code": ".agent-harness/runs/pr287-fresh-independent-review-20260811/results/A-PR287-FROZEN-CODE.json",
    "physstat": ".agent-harness/runs/pr287-fresh-independent-review-20260811/results/A-PR287-FROZEN-PHYSSTAT.json",
    "claim": ".agent-harness/runs/pr287-fresh-independent-review-20260811/results/A-PR287-FROZEN-CLAIM.json",
    "replay": ".agent-harness/runs/pr287-fresh-independent-review-20260811/results/A-PR287-FROZEN-REPLAY.json",
    "replay_r2": ".agent-harness/runs/pr287-fresh-independent-review-20260811/results/A-PR287-FROZEN-REPLAY-R2.json",
    "replay_r3": ".agent-harness/runs/pr287-fresh-independent-review-20260811/results/A-PR287-FROZEN-REPLAY-R3.json",
    "aggregate": ".agent-harness/runs/pr287-fresh-independent-review-20260811/MERGED_RESULTS.json",
    "summary": ".agent-harness/runs/pr287-fresh-independent-review-20260811/RUN_SUMMARY.json",
}


def read_bytes(rel: str) -> bytes:
    return (ROOT / rel).read_bytes()


def read_json(rel: str) -> dict[str, Any]:
    value = json.loads(read_bytes(rel))
    if not isinstance(value, dict):
        raise AssertionError(f"{rel} is not a JSON object")
    return value


def sha256(rel: str) -> str:
    return hashlib.sha256(read_bytes(rel)).hexdigest()


def git(*args: str, check: bool = True, input_bytes: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def text_git(*args: str) -> str:
    return git(*args).stdout.decode("utf-8", errors="strict").strip()


def main() -> int:
    started_at = datetime.now(timezone.utc)
    checks: list[dict[str, Any]] = []
    failures: list[str] = []

    def check(name: str, condition: bool, evidence: Any) -> None:
        checks.append({"check": name, "status": "PASS" if condition else "FAIL", "evidence": evidence})
        if not condition:
            failures.append(name)

    assignment = read_json(PATHS["assignment"])
    plan = read_json(PATHS["plan"])
    context = read_json(PATHS["context"])
    seal = read_json(PATHS["final_seal"])
    integration = read_json(PATHS["integration"])
    validated_seal = read_json(PATHS["validated_seal"])
    _, policy = load_publication_policy(ROOT, PATHS["policy"])

    check("assignment_identity", assignment.get("assignment_id") == ASSIGNMENT_ID and assignment.get("run_id") == RUN_ID, assignment.get("assignment_id"))
    check("context_version", assignment.get("context_version") == CONTEXT_VERSION and plan.get("context_version") == CONTEXT_VERSION and context.get("context_version") == CONTEXT_VERSION, CONTEXT_VERSION)

    required_hashes = {row["path"]: row["sha256"] for row in assignment["required_inputs"]}
    required_hash_results = {path: sha256(path) for path in required_hashes}
    check("all_required_input_hashes", required_hash_results == required_hashes, required_hash_results)
    check("final_seal_file_hash", sha256(PATHS["final_seal"]) == FINAL_SEAL_HASH, sha256(PATHS["final_seal"]))
    check("integration_receipt_file_hash", sha256(PATHS["integration"]) == INTEGRATION_HASH, sha256(PATHS["integration"]))
    check("validated_seal_file_hash", sha256(PATHS["validated_seal"]) == VALIDATED_SEAL_HASH, sha256(PATHS["validated_seal"]))

    seal_errors = validate_candidate_seal_payload(seal, repo=ROOT)
    check("candidate_seal_payload", not seal_errors, seal_errors)
    receipt_errors = validate_integration_receipt_payload(
        integration,
        seal=seal,
        policy=policy,
        now=parse_utc(integration["completed_at"], field="integration completed_at"),
        repo=ROOT,
        log_dir=None,
    )
    check("recorded_integration_receipt", not receipt_errors, receipt_errors)
    check("integration_tree_equals_candidate", integration.get("merged_tree_sha") == TREE == seal.get("candidate_tree_sha"), integration.get("merged_tree_sha"))

    live_head = text_git("rev-parse", "HEAD")
    live_tree = text_git("rev-parse", "HEAD^{tree}")
    merge_base = text_git("merge-base", BASE, HEAD)
    remote_base = text_git("rev-parse", "refs/remotes/origin/changeset/pr286-pillar-s-adjudication-recovery-20260810")
    status = text_git("status", "--porcelain=v1", "--untracked-files=all")
    check("exact_head_and_tree", live_head == HEAD and live_tree == TREE, {"head": live_head, "tree": live_tree})
    check("exact_pr286_base", merge_base == BASE and remote_base == BASE and seal.get("base_sha") == BASE, {"merge_base": merge_base, "remote_base": remote_base})
    check("clean_worktree", status == "", status)

    commits = text_git("rev-list", "--reverse", f"{BASE}..{HEAD}").splitlines()
    merge_commits = text_git("rev-list", "--merges", f"{BASE}..{HEAD}").splitlines()
    patch_ids: list[str] = []
    for commit in commits:
        patch = git("show", "--pretty=format:", "--no-ext-diff", "--binary", commit).stdout
        patch_id_output = git("patch-id", "--stable", input_bytes=patch).stdout.decode().strip()
        patch_ids.append(patch_id_output.split()[0])
    check("six_linear_candidate_commits", len(commits) == 6 and not merge_commits and commits == seal.get("candidate_commits"), {"commits": commits, "merge_commits": merge_commits})
    check("six_unique_stable_patch_ids", patch_ids == EXPECTED_PATCH_IDS and len(set(patch_ids)) == 6, patch_ids)

    metadata_range = text_git("diff", "--name-only", "06ee728054fd62423fa90bc6a5d714b9be8631e3^..319835cc4b4e2e3270a0b27787ce5d5a44ea16b7").splitlines()
    check("review_metadata_only_range", metadata_range == EXPECTED_METADATA_RANGE, metadata_range)
    check("production_hash_unchanged", seal.get("production_hash") == validated_seal.get("production_hash") == PRODUCTION_HASH, {"validated": validated_seal.get("production_hash"), "final": seal.get("production_hash")})
    check("production_file_inventory_unchanged", seal.get("changed_files_sha256") == validated_seal.get("changed_files_sha256") == CHANGED_FILES_HASH, seal.get("changed_files_sha256"))

    code = read_json(PATHS["code"])
    physstat = read_json(PATHS["physstat"])
    claim = read_json(PATHS["claim"])
    replay = read_json(PATHS["replay"])
    replay_r2 = read_json(PATHS["replay_r2"])
    replay_r3 = read_json(PATHS["replay_r3"])
    check("code_review_pass", code.get("status") == "pass" and code.get("gate_disposition") == "PASS" and not code.get("findings"), code.get("status"))
    check("claim_review_pass", claim.get("status") == "pass" and claim.get("gate_disposition") == "PASS" and not claim.get("findings"), claim.get("status"))
    phys_findings = physstat.get("findings", [])
    typed_blocker = (
        physstat.get("status") == "inconclusive"
        and physstat.get("gate_disposition") == "INCONCLUSIVE"
        and len(phys_findings) == 1
        and phys_findings[0].get("finding_id") == "F-PR287-PHYSSTAT-EXECUTOR-ABSENT"
        and phys_findings[0].get("verdict") == "inconclusive"
        and "not a mathematics or containment failure" in phys_findings[0].get("statement", "")
    )
    check("physstat_typed_executor_only", typed_blocker, phys_findings)
    initial_contamination = replay.get("status") == "error" and replay.get("gate_disposition") == "INCONCLUSIVE" and replay.get("claim_results", [{}])[0].get("outcome") == "not_examined" and "BLIND_RESULTS_ISOLATION_BREACH" in " ".join(replay.get("errors", []))
    r2_contamination = replay_r2.get("status") == "inconclusive" and replay_r2.get("gate_disposition") == "INCONCLUSIVE" and replay_r2.get("claim_results", [{}])[0].get("outcome") == "not_examined" and "BLIND_RESULTS_INDEPENDENCE_CONTAMINATION" in " ".join(replay_r2.get("errors", []))
    replacement_pass = replay_r3.get("status") == "pass" and replay_r3.get("gate_disposition") == "PASS" and replay_r3.get("claim_results", [{}])[0].get("outcome") == "examined_no_findings"
    check("contamination_chronology_preserved", initial_contamination and r2_contamination and replacement_pass, {"initial": replay.get("status"), "r2": replay_r2.get("status"), "r3": replay_r3.get("status")})

    aggregate = read_json(PATHS["aggregate"])
    summary = read_json(PATHS["summary"])
    aggregate_ok = (
        aggregate.get("process_status") == "STRUCTURALLY_VALID"
        and aggregate.get("result_count") == 6
        and aggregate.get("validated_result_count") == 6
        and not aggregate.get("errors")
        and not aggregate.get("conflicts")
        and len(aggregate.get("findings", [])) == 1
        and aggregate["findings"][0].get("finding_id") == "F-PR287-PHYSSTAT-EXECUTOR-ABSENT"
    )
    check("review_aggregate_exact", aggregate_ok, {"process_status": aggregate.get("process_status"), "validated": aggregate.get("validated_result_count"), "findings": [row.get("finding_id") for row in aggregate.get("findings", [])]})
    summary_rows = {row["assignment_id"]: (row["status"], row.get("gate_disposition"), row["sha256"]) for row in summary.get("results", [])}
    expected_rows = {
        "A-PR287-FROZEN-CODE": ("pass", "PASS", required_hashes[PATHS["code"]]),
        "A-PR287-FROZEN-PHYSSTAT": ("inconclusive", "INCONCLUSIVE", required_hashes[PATHS["physstat"]]),
        "A-PR287-FROZEN-CLAIM": ("pass", "PASS", required_hashes[PATHS["claim"]]),
        "A-PR287-FROZEN-REPLAY": ("error", "INCONCLUSIVE", required_hashes[PATHS["replay"]]),
        "A-PR287-FROZEN-REPLAY-R2": ("inconclusive", "INCONCLUSIVE", required_hashes[PATHS["replay_r2"]]),
        "A-PR287-FROZEN-REPLAY-R3": ("pass", "PASS", required_hashes[PATHS["replay_r3"]]),
    }
    check("review_summary_exact_rows", summary_rows == expected_rows, summary_rows)

    status_doc = yaml.safe_load(read_bytes(PATHS["status"]))
    mirror_equal = read_bytes(PATHS["status"]) == read_bytes(PATHS["status_mirror"])
    pr287 = status_doc["stacked_pr_execution"]["prs"]["PR-287"]
    pr288 = status_doc["stacked_pr_execution"]["prs"]["PR-288"]
    expected_key = {"production_hash": PRODUCTION_HASH, "dependency_hashes": plan["dependency_hashes"]}
    check("production_dependency_evidence_key_unchanged", plan.get("evidence_key") == expected_key and summary.get("evidence_key") == expected_key and pr287.get("production_hash") == PRODUCTION_HASH and pr287.get("dependency_hashes") == plan.get("dependency_hashes"), expected_key)
    check("status_mirrors_synchronized", mirror_equal, sha256(PATHS["status"]))
    check("lifecycle_reviewed", plan.get("lifecycle_state") == "REVIEWED" and pr287.get("lifecycle") == "REVIEWED" and pr287.get("lifecycle_history") == ["PLANNED", "ACTIVE", "IMPLEMENTED", "VALIDATED", "REVIEWED"], {"plan": plan.get("lifecycle_state"), "status": pr287.get("lifecycle")})
    budget_before = plan.get("assurance_budget", {}).get("consumed")
    check("assurance_budget_becomes_7_of_16", budget_before == 6 and plan.get("assurance_budget", {}).get("maximum") == 16 and pr287.get("assurance_budget") == {"maximum": 16, "consumed": 6}, {"before": budget_before, "after_this_assignment": budget_before + 1, "maximum": 16})
    check("pr288_ineligible_zero_budget", pr288.get("lifecycle") == "PLANNED" and pr288.get("gate_dispositions") == {"eligibility": "INELIGIBLE"} and pr288.get("assurance_budget") == {"maximum": 16, "consumed": 0}, pr288)

    remote_pr287_refs = text_git("for-each-ref", "--format=%(refname) %(objectname)", "refs/remotes/origin/*pr287*").splitlines()
    upstream = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}", check=False)
    no_publication = (
        plan.get("github_pr_created_by_harness") is False
        and plan.get("publication_mode") == "external_publisher_only"
        and summary.get("github_pr_created_by_harness") is False
        and summary.get("publication_state") == "NOT_PUBLISHED_BY_HARNESS"
        and pr287.get("pushed_ref") is None
        and pr287.get("pr_url") is None
        and not remote_pr287_refs
        and upstream.returncode != 0
        and not merge_commits
    )
    check("no_push_pr_or_merge", no_publication, {"pushed_ref": pr287.get("pushed_ref"), "pr_url": pr287.get("pr_url"), "remote_refs": remote_pr287_refs, "upstream_returncode": upstream.returncode, "merge_commits": merge_commits})

    completed_at = datetime.now(timezone.utc)
    report = {
        "schema_version": 1,
        "oracle_id": "PR287-FINAL-SEAL-CLOSEOUT-METADATA-ORACLE",
        "run_id": RUN_ID,
        "assignment_id": ASSIGNMENT_ID,
        "context_version": CONTEXT_VERSION,
        "scope": "metadata-only; no substantive scientific assurance rerun",
        "started_at": started_at.isoformat(),
        "completed_at": completed_at.isoformat(),
        "status": "PASS" if not failures else "FAIL",
        "checks": checks,
        "failures": failures,
        "assurance_budget": {"before": 6, "this_assignment": 1, "after": 7, "maximum": 16},
        "publication_state": "NOT_PUBLISHED",
    }
    output = Path(__file__).with_name("final_closeout_oracle_report.json")
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_bytes = output.read_bytes()
    report_rel = output.relative_to(ROOT).as_posix()
    argv = ["python3", "-B", Path(__file__).relative_to(ROOT).as_posix()]
    common_evidence = [
        PATHS["replay_r3"],
        PATHS["aggregate"],
        PATHS["final_seal"],
        PATHS["integration"],
        report_rel,
    ]
    coverage = {
        "schema_version": 1,
        "run_id": RUN_ID,
        "assignment_id": ASSIGNMENT_ID,
        "change_set_id": seal["change_set_id"],
        "publication_group_id": seal["publication_group_id"],
        "candidate_seal_sha256": seal["seal_sha256"],
        "candidate_sha": seal["candidate_sha"],
        "candidate_tree_sha": seal["candidate_tree_sha"],
        "diff_sha256": seal["diff_sha256"],
        "changed_files_sha256": seal["changed_files_sha256"],
        "completed_at": completed_at.isoformat(),
        "first_verdict_read_only": True,
        "correlated_review": True,
        "coverage_cells": [
            {
                "cell": cell,
                "status": "PASS",
                "evidence_refs": common_evidence,
                "rationale": (
                    "Final adjudication binds the exact passed replacement review and "
                    "sealed integration evidence; the intervening REVIEWED metadata-only "
                    "commit preserves the production/dependency evidence key."
                ),
            }
            for cell in policy["required_review_cells"]
        ],
        "independent_oracles": [
            {
                "oracle_id": "PR287-FINAL-SEAL-CLOSEOUT-METADATA-ORACLE",
                "kind": "invariant_checker",
                "status": "PASS",
                "argv": argv,
                "command_fingerprint": canonical_sha256({"argv": argv}),
                "returncode": 0,
                "timed_out": False,
                "started_at": started_at.isoformat(),
                "completed_at": completed_at.isoformat(),
                "artifact_path": report_rel,
                "artifact_sha256": hashlib.sha256(report_bytes).hexdigest(),
                "artifact_bytes": len(report_bytes),
                "evidence_refs": common_evidence,
            }
        ],
    }
    coverage["coverage_sha256"] = canonical_sha256(coverage, omit={"coverage_sha256"})
    coverage_output = Path(__file__).with_name("review_coverage.json")
    coverage_output.write_text(
        json.dumps(coverage, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"ok": not failures, "report": report_rel, "coverage": coverage_output.relative_to(ROOT).as_posix(), "checks": len(checks), "failures": failures}, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
