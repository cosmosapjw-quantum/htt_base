#!/usr/bin/env python3
"""Read-only invariant oracle for the bounded PR-288 final-seal closeout."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[5]
BASE = "319835cc4b4e2e3270a0b27787ce5d5a44ea16b7"
IMPLEMENTATION = "5c20df43241f5156e17b1c25b2fcf38592d99ca0"
REVIEWED = "dcde762d1ce3027e01edcf2744398f7588bb5fb1"
FINAL = "27df5da040e27eeaad44873ba3424ff73fb4bb09"
FINAL_TREE = "93ead987a1a750a5dd34cbe9e98baf8fc7b48746"
PRODUCTION_HASH = "7d2ce119e4f176aacaa870f0c7bc0dc1e5e0aa843bf2984f6ac7af7d4d148a79"
FINAL_SEAL_SHA = "3650528494b927678836a8a14abeab6840d88e4a0a24f0ae311aa79fe143c330"
FINAL_SEAL_FILE_SHA = "a0823a01fdcccf0d854652507ab35861ffe9fb2e042cf4a32403e5668a199f12"
FINAL_RECEIPT_FILE_SHA = "d5e251f7691ec31bed3ab56b025b785e3f1faf1b62b0317693644810b222ff55"
PRIOR_RECEIPT_FILE_SHA = "83058061456d05535e300faf9ee5780d3d0428ca694e8d41a43dc85b5c77b570"
POLICY_SHA = "c1e088fa12716ef9bc9870bad0213b8d37ae28e0dc96edec6e2cc66f1f81910b"

EXPECTED_INPUT_HASHES = {
    ".prguard/runtime/PR288_FINAL_CANDIDATE_SEAL.json": FINAL_SEAL_FILE_SHA,
    ".prguard/runtime/PR288_FINAL_INTEGRATION_REHEARSAL.json": FINAL_RECEIPT_FILE_SHA,
    ".prguard/runtime/PR288_FINAL_EVIDENCE_CARRY_FORWARD.py": "5525f896e0ea2d0207ec881cc19d651390781d010dccf6614f6bb709e9f5f824",
    ".prguard/runtime/PR288_VALIDATED_CANDIDATE_SEAL.json": "cdde24653257c03c34fc94b2af1d58eff55f8aad4575bff07e8190c4d6a637fe",
    ".prguard/runtime/PR288_IMPLEMENTATION_INTEGRATION_REHEARSAL.json": PRIOR_RECEIPT_FILE_SHA,
    ".agent-harness/runs/pr288-frozen-independent-review-20260811/results/A-PR288-FROZEN-PHYSCODE.json": "36f74aee7c15fbf9c2a3cd4fd8ebe56cdd0fb714389e5bc728fbba9f423aebdd",
    ".agent-harness/runs/pr288-frozen-independent-review-20260811/results/A-PR288-FROZEN-REPLAY.json": "42f69c5a75af3e2489372f663a3b755ecc71d5aea30dbcf0cda0c97f2357a75b",
    ".agent-harness/runs/pr288-frozen-independent-review-20260811/results/A-PR288-FROZEN-CLAIM.json": "213f4437dcf2ade61b6973760dbf3cfa8f8aaef6376dbaea790be60a20d580d9",
    ".agent-harness/runs/pr288-frozen-independent-review-20260811/results/A-PR288-FROZEN-CLAIM-R2.json": "136de5cc22cb5b420b8fead290301c28717c720f3eab256642ba0867e0d51540",
    ".agent-harness/runs/pr288-frozen-independent-review-20260811/MERGED_RESULTS.json": "8fc22567c61b715fdc06fd87d85a622d64e13faeac2050867020e2ebba24a1b1",
    ".agent-harness/runs/pr288-frozen-independent-review-20260811/RUN_SUMMARY.json": "b1745d363f87cd2e74b892293c915620b6995e21e2bf2cc24bf384e83fcee9b5",
    "docs/research_program/post_pr275/pr288_publication_policy.json": POLICY_SHA,
    "docs/research_program/post_pr275/pr288_spec.yaml": "994603817e0546a1abb10b026cb3fcb31ebf5bee829c4e452798a808e19d4233",
    "docs/PR_DELTAS/pr-288.md": "018137eebcbed5acd9aa64036bc2add9db5ecc137a9d16dea4e4e44df0b1ce41",
    "docs/codex_handoff/pr_status.yaml": "2d598032f6cdfac2674b61a2f90d57169ffc158aa2b632380b1073b601cfcfe6",
    "machine_readable/pr_status.yaml": "2d598032f6cdfac2674b61a2f90d57169ffc158aa2b632380b1073b601cfcfe6",
    ".agent-harness/scripts/_harness.py": "388f66e208bc460fb916eeca8603fc6f5ebfd914e448e59e93382152fde3f6ce",
}

CARRIED = [
    "pr288-focused",
    "pr288-engine-crosscheck",
    "pr288-adjacent",
    "pr288-receipt-replay",
    "pr288-publication-policy-cross-binding",
]
FRESH = [
    "pr288-claim-language",
    "pr288-dag-strict",
    "pr288-portable-clean-replay",
]
METADATA_PATHS = [
    "docs/PR_DELTAS/pr-288.md",
    "docs/codex_handoff/pr_status.yaml",
    "machine_readable/pr_status.yaml",
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def canonical_hash(value: dict[str, Any], omit: str) -> str:
    payload = dict(value)
    payload.pop(omit, None)
    return sha256(canonical(payload))


def git(*args: str, input_bytes: bytes | None = None, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def load_json(path: str) -> dict[str, Any]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def status_at(commit: str) -> dict[str, Any]:
    raw = git("show", f"{commit}:docs/codex_handoff/pr_status.yaml").stdout
    value = yaml.safe_load(raw)
    assert isinstance(value, dict)
    return value


def command_rows(receipt: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = receipt["commands"]
    assert isinstance(rows, list)
    return {str(row["id"]): row for row in rows}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    output.relative_to(ROOT)

    checks: list[dict[str, Any]] = []

    def record(name: str, ok: bool, evidence: Any) -> None:
        checks.append({"check": name, "status": "PASS" if ok else "FAIL", "evidence": evidence})

    for rel, expected in EXPECTED_INPUT_HASHES.items():
        actual = sha256((ROOT / rel).read_bytes())
        record(f"input_hash:{rel}", actual == expected, {"expected": expected, "actual": actual})

    seal = load_json(".prguard/runtime/PR288_FINAL_CANDIDATE_SEAL.json")
    prior_seal = load_json(".prguard/runtime/PR288_VALIDATED_CANDIDATE_SEAL.json")
    receipt = load_json(".prguard/runtime/PR288_FINAL_INTEGRATION_REHEARSAL.json")
    prior_receipt = load_json(".prguard/runtime/PR288_IMPLEMENTATION_INTEGRATION_REHEARSAL.json")
    policy = load_json("docs/research_program/post_pr275/pr288_publication_policy.json")
    physcode = load_json(".agent-harness/runs/pr288-frozen-independent-review-20260811/results/A-PR288-FROZEN-PHYSCODE.json")
    replay = load_json(".agent-harness/runs/pr288-frozen-independent-review-20260811/results/A-PR288-FROZEN-REPLAY.json")
    claim1 = load_json(".agent-harness/runs/pr288-frozen-independent-review-20260811/results/A-PR288-FROZEN-CLAIM.json")
    claim2 = load_json(".agent-harness/runs/pr288-frozen-independent-review-20260811/results/A-PR288-FROZEN-CLAIM-R2.json")
    merged = load_json(".agent-harness/runs/pr288-frozen-independent-review-20260811/MERGED_RESULTS.json")
    summary = load_json(".agent-harness/runs/pr288-frozen-independent-review-20260811/RUN_SUMMARY.json")
    spec = yaml.safe_load((ROOT / "docs/research_program/post_pr275/pr288_spec.yaml").read_text(encoding="utf-8"))
    assert isinstance(spec, dict)

    head = git("rev-parse", "HEAD").stdout.decode().strip()
    branch = git("symbolic-ref", "--quiet", "--short", "HEAD").stdout.decode().strip()
    dirty = git("status", "--porcelain=v2", "--untracked-files=all").stdout.decode()
    target = git("rev-parse", "refs/remotes/origin/changeset/pr287-entropy-truth-recovery-20260811").stdout.decode().strip()
    merge_base = git("merge-base", BASE, FINAL).stdout.decode().strip()
    tree = git("rev-parse", f"{FINAL}^{{tree}}").stdout.decode().strip()
    commits = git("rev-list", "--reverse", f"{BASE}..{FINAL}").stdout.decode().splitlines()
    record("live_candidate_identity", head == FINAL and branch == "changeset/pr288-bayesian-evidence-recovery-20260811" and not dirty, {"head": head, "branch": branch, "porcelain_v2": dirty})
    record("exact_pr287_predecessor_base", target == BASE and merge_base == BASE and seal["target_branch"] == "changeset/pr287-entropy-truth-recovery-20260811", {"target": target, "merge_base": merge_base, "seal_base": seal["base_sha"]})
    record("final_tree_identity", tree == FINAL_TREE == seal["candidate_tree_sha"], {"tree": tree})
    record("nine_commit_lineage", commits == seal["candidate_commits"] and len(commits) == 9, {"commits": commits})

    patch_rows: list[dict[str, str]] = []
    for commit in commits:
        diff = git("show", "--pretty=format:", "--binary", commit).stdout
        result = git("patch-id", "--stable", input_bytes=diff).stdout.decode().strip().split()
        patch_rows.append({"commit": commit, "stable_patch_id": result[0]})
    record("nine_unique_stable_patch_ids", patch_rows == seal["stable_patch_ids"] and len({row["stable_patch_id"] for row in patch_rows}) == 9, {"stable_patch_ids": patch_rows})

    diff = git(
        "diff", "--binary", "--full-index", "--no-color", "--no-ext-diff",
        "--no-textconv", "--no-renames", "--submodule=short", f"{BASE}..{FINAL}"
    ).stdout
    record("final_diff_digest", sha256(diff) == seal["diff_sha256"], {"actual": sha256(diff), "sealed": seal["diff_sha256"]})
    record("final_seal_canonical_checksum", canonical_hash(seal, "seal_sha256") == FINAL_SEAL_SHA == seal["seal_sha256"], {"seal_sha256": seal["seal_sha256"]})
    record("final_seal_binding", seal["candidate_sha"] == FINAL and seal["base_sha"] == BASE and seal["merge_base_sha"] == BASE and seal["production_hash"] == PRODUCTION_HASH and seal["integration_policy"]["sha256"] == POLICY_SHA and seal["dirty"] is False, {"candidate_sha": seal["candidate_sha"], "base_sha": seal["base_sha"], "production_hash": seal["production_hash"]})

    def changed_names(left: str, right: str) -> list[str]:
        rows = git("diff", "--name-only", f"{left}..{right}").stdout.decode().splitlines()
        return sorted(rows)

    combined_names = changed_names(IMPLEMENTATION, FINAL)
    first_names = changed_names(IMPLEMENTATION, REVIEWED)
    second_names = changed_names(REVIEWED, FINAL)
    record("metadata_only_review_and_final_commits", combined_names == METADATA_PATHS and first_names == METADATA_PATHS and second_names == METADATA_PATHS, {"combined": combined_names, "first": first_names, "second": second_names})
    parent_reviewed = git("rev-parse", f"{REVIEWED}^").stdout.decode().strip()
    parent_final = git("rev-parse", f"{FINAL}^").stdout.decode().strip()
    record("linear_metadata_commit_range", parent_reviewed == IMPLEMENTATION and parent_final == REVIEWED, {"reviewed_parent": parent_reviewed, "final_parent": parent_final})

    current_status_bytes = (ROOT / "docs/codex_handoff/pr_status.yaml").read_bytes()
    mirror_status_bytes = (ROOT / "machine_readable/pr_status.yaml").read_bytes()
    current_status = yaml.safe_load(current_status_bytes)
    status_impl = status_at(IMPLEMENTATION)
    status_reviewed = status_at(REVIEWED)
    records = [s["stacked_pr_execution"]["prs"]["PR-288"] for s in (status_impl, status_reviewed, current_status)]
    evidence_keys = [{"production_hash": row["production_hash"], "dependency_hashes": row["dependency_hashes"]} for row in records]
    record("status_mirrors_byte_identical", current_status_bytes == mirror_status_bytes, {"sha256": sha256(current_status_bytes)})
    record("production_dependency_evidence_key_unchanged", evidence_keys[1] == evidence_keys[2] == summary["evidence_key"] and evidence_keys[2]["production_hash"] == PRODUCTION_HASH and evidence_keys[0] == {"production_hash": None, "dependency_hashes": {}}, {"implementation_status_before_projection": evidence_keys[0], "reviewed_and_final_evidence_key": evidence_keys[2]})

    pr287 = current_status["stacked_pr_execution"]["prs"]["PR-287"]
    pr288 = current_status["stacked_pr_execution"]["prs"]["PR-288"]
    pr289 = current_status["stacked_pr_execution"]["prs"]["PR-289"]
    record("pr288_reviewed_lifecycle", pr288["lifecycle"] == "REVIEWED" and pr288["lifecycle_history"] == ["PLANNED", "ACTIVE", "IMPLEMENTED", "VALIDATED", "REVIEWED"] and current_status["stacked_pr_execution"]["active_implementation_pr"] == "PR-288" and current_status["in_progress"] == "PR-288", {"lifecycle": pr288["lifecycle"], "history": pr288["lifecycle_history"]})
    record("pr287_predecessor_status_binding", pr287["lifecycle"] == "PR_OPEN" and pr287["sealed_head"] == BASE and pr288["predecessor_pr"] == "PR-287" and pr288["predecessor_sealed_sha"] == BASE and pr288["base_sha"] == BASE, {"pr287_sealed_head": pr287["sealed_head"], "pr288_base": pr288["base_sha"]})
    record("assurance_budget_closeout_projection", pr288["assurance_budget"] == {"consumed": 6, "maximum": 16} and pr288["assurance_budget"]["consumed"] + 1 == 7, {"before_assignment": pr288["assurance_budget"], "after_this_assignment": {"consumed": 7, "maximum": 16}})
    record("pr289_planned_ineligible_zero_budget", pr289["lifecycle"] == "PLANNED" and pr289["gate_dispositions"] == {"eligibility": "INELIGIBLE"} and pr289["assurance_budget"] == {"consumed": 0, "maximum": 16} and pr289["base_sha"] is None, {"pr289": pr289})

    record("final_receipt_canonical_checksum", canonical_hash(receipt, "receipt_sha256") == receipt["receipt_sha256"], {"receipt_sha256": receipt["receipt_sha256"]})
    record("final_receipt_seal_binding", receipt["candidate_seal_sha256"] == FINAL_SEAL_SHA and receipt["candidate_sha"] == FINAL and receipt["candidate_tree_sha"] == FINAL_TREE and receipt["diff_sha256"] == seal["diff_sha256"] and receipt["changed_files_sha256"] == seal["changed_files_sha256"] and receipt["latest_target_sha"] == BASE and receipt["merged_tree_sha"] == FINAL_TREE and receipt["status"] == "PASS", {"candidate_sha": receipt["candidate_sha"], "candidate_seal_sha256": receipt["candidate_seal_sha256"], "status": receipt["status"]})
    freshness = receipt["evidence_freshness"]
    record("freshness_contract", freshness["mode"] == "UNCHANGED_SUBSTANTIVE_EVIDENCE_KEY_CARRY_FORWARD" and freshness["reason"] == "EVIDENCE_KEY_UNCHANGED" and freshness["substantive_rerun_required"] is False and freshness["previous_candidate_sha"] == IMPLEMENTATION and freshness["current_candidate_sha"] == FINAL and freshness["production_hash"] == PRODUCTION_HASH and freshness["previous_integration_receipt_file_sha256"] == PRIOR_RECEIPT_FILE_SHA and freshness["tracked_delta_since_previous_candidate"] == METADATA_PATHS, freshness)
    prior_rows = command_rows(prior_receipt)
    final_rows = command_rows(receipt)
    record("policy_command_inventory", set(final_rows) == set(policy["required_commands"][i]["id"] for i in range(len(policy["required_commands"]))) and len(final_rows) == 8, {"command_ids": sorted(final_rows)})
    carried_equal = {key: canonical(prior_rows[key]) == canonical(final_rows[key]) for key in CARRIED}
    fresh_changed = {key: canonical(prior_rows[key]) != canonical(final_rows[key]) for key in FRESH}
    record("five_substantive_rows_carried_byte_for_byte", all(carried_equal.values()) and freshness["carried_forward_command_ids"] == CARRIED, carried_equal)
    record("only_three_metadata_sensitive_rows_fresh", all(fresh_changed.values()) and freshness["fresh_metadata_sensitive_command_ids"] == sorted(FRESH), fresh_changed)
    record("all_final_policy_rows_pass", all(row["returncode"] == 0 and row["timed_out"] is False for row in final_rows.values()), {key: {"returncode": row["returncode"], "timed_out": row["timed_out"]} for key, row in final_rows.items()})

    old_binding = {
        "candidate_sha": REVIEWED,
        "seal_path": ".prguard/runtime/PR288_VALIDATED_CANDIDATE_SEAL.json",
        "seal_file_sha256": EXPECTED_INPUT_HASHES[".prguard/runtime/PR288_VALIDATED_CANDIDATE_SEAL.json"],
    }
    review_bindings_ok = all(
        row["candidate_binding"][key] == value
        for row in (physcode, replay, claim1, claim2)
        for key, value in old_binding.items()
    )
    record("closed_review_immutable_binding", review_bindings_ok and prior_seal["candidate_sha"] == REVIEWED and prior_seal["production_hash"] == PRODUCTION_HASH, old_binding)
    original_outcome = claim1["claim_results"][0]
    replacement_outcome = claim2["claim_results"][0]
    record("claim_contamination_chronology_preserved", claim1["status"] == "error" and claim1["gate_disposition"] == "INCONCLUSIVE" and original_outcome["outcome"] == "not_examined" and any("BLIND_RESULTS_ISOLATION_BREACH" in item for item in claim1["errors"]) and claim2["status"] == "pass" and claim2["gate_disposition"] == "PASS" and replacement_outcome["outcome"] == "examined_no_findings", {"first": {"status": claim1["status"], "gate_disposition": claim1["gate_disposition"], "outcome": original_outcome["outcome"]}, "replacement": {"status": claim2["status"], "gate_disposition": claim2["gate_disposition"], "outcome": replacement_outcome["outcome"]}})
    record("physics_code_and_replay_pass", physcode["status"] == replay["status"] == "pass" and physcode["gate_disposition"] == replay["gate_disposition"] == "PASS", {"physcode": physcode["status"], "replay": replay["status"]})
    dispositions = {row["assignment_id"]: (row["status"], row["gate_disposition"]) for row in merged["result_dispositions"]}
    record("aggregate_preserves_all_four_results", merged["process_status"] == "STRUCTURALLY_VALID" and merged["claim_gate_status"] == "NOT_EVALUATED" and merged["validated_result_count"] == 4 and not merged["errors"] and not merged["conflicts"] and dispositions == {"A-PR288-FROZEN-CLAIM": ("error", "INCONCLUSIVE"), "A-PR288-FROZEN-CLAIM-R2": ("pass", "PASS"), "A-PR288-FROZEN-PHYSCODE": ("pass", "PASS"), "A-PR288-FROZEN-REPLAY": ("pass", "PASS")}, {"process_status": merged["process_status"], "claim_gate_status": merged["claim_gate_status"], "dispositions": dispositions})

    remote_candidate = git("show-ref", "--verify", "--quiet", "refs/remotes/origin/changeset/pr288-bayesian-evidence-recovery-20260811", check=False)
    candidate_in_target = git("merge-base", "--is-ancestor", FINAL, "refs/remotes/origin/changeset/pr287-entropy-truth-recovery-20260811", check=False)
    remote_contains = git("for-each-ref", "--format=%(refname)", "--contains", FINAL, "refs/remotes").stdout.decode().splitlines()
    record("no_local_publication_evidence", pr288["pushed_ref"] is None and pr288["pr_url"] is None and pr288["sealed_head"] is None and remote_candidate.returncode == 1 and candidate_in_target.returncode == 1 and not remote_contains and summary["github_pr_created_by_harness"] is False and summary["publication_state"] == "NOT_PUBLISHED_BY_HARNESS", {"pushed_ref": pr288["pushed_ref"], "pr_url": pr288["pr_url"], "sealed_head": pr288["sealed_head"], "candidate_remote_ref_returncode": remote_candidate.returncode, "candidate_is_target_ancestor_returncode": candidate_in_target.returncode, "remote_refs_containing_candidate": remote_contains, "prior_review_publication_state": summary["publication_state"]})
    record("publication_authority_remains_external_human_only", policy["ordinary_agent_push_forbidden"] is True and policy["ordinary_agent_pr_mutation_forbidden"] is True and policy["unattended_publication_requires_external_publisher"] is True and current_status["stacked_pr_execution"]["merge_policy"] == "HUMAN_ONLY", {"ordinary_agent_push_forbidden": policy["ordinary_agent_push_forbidden"], "ordinary_agent_pr_mutation_forbidden": policy["ordinary_agent_pr_mutation_forbidden"], "merge_policy": current_status["stacked_pr_execution"]["merge_policy"]})
    record("scientific_ceiling_unchanged", spec["owner"] == "HTT" and spec["claim_tier"] == "diagnostic_only" and spec["observed_data_executed"] is False and spec["public_use"] is False and spec["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS" and spec["transfer_source"] == "none", {key: spec[key] for key in ["owner", "claim_tier", "observed_data_executed", "public_use", "family_identification_gate", "transfer_source"]})

    failures = [row for row in checks if row["status"] != "PASS"]
    report = {
        "schema_version": 1,
        "oracle_id": "PR288-FINAL-SEAL-CLOSEOUT-INVARIANTS",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if not failures else "FAIL",
        "scope": "bounded metadata, freshness, lifecycle, and local publication-state closeout; no substantive scientific assurance rerun",
        "check_count": len(checks),
        "failure_count": len(failures),
        "checks": checks,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "check_count": len(checks), "failure_count": len(failures), "output": args.output}, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
