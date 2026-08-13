#!/usr/bin/env python3
"""Independent, read-only PR-289 R2 replay/lineage oracle.

Default execution checks frozen identities, selective lineage, content hashes,
mutation completeness, status mirrors, and lifecycle containment.  Pass
``--run-policy`` to replay the exact eight commands declared by the frozen
publication policy as an additional (longer) check.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yaml


RUN_ID = "pr289-bounded-repair-r2-review-20260811"
ASSIGNMENT_ID = "A-PR289-R2-REPLAY"
CONTEXT_VERSION = "e9b385d7fbc4f8e47c97c3b0c7edae4e522d9be4e025d9342e26ab24829e3019"
CANONICAL_AUDIT = Path(
    "/home/cosmosapjw/Dropbox/bianchi/htt_base/"
    "HTT_PROCESS_INFLATION_SALVAGE_AUDIT_20260810.md"
)
EXPECTED_AUDIT_SHA256 = "c42b44641a7655edc36c11e23a747433275285a4f342a824fa69dda88bd6f436"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def git(*args: str, binary: bool = False) -> str | bytes:
    out = subprocess.check_output(["git", *args])
    return out if binary else out.decode().strip()


def stable_patch_id(commit: str) -> str:
    patch = git("show", "--format=", "--binary", commit, binary=True)
    out = subprocess.check_output(["git", "patch-id", "--stable"], input=patch)
    return out.decode().split()[0]


def changed_paths(parent: str, commit: str) -> set[str]:
    out = git("diff", "--name-only", parent, commit)
    return set(out.splitlines()) if out else set()


def check(condition: bool, label: str, checks: list[str]) -> None:
    if not condition:
        raise AssertionError(label)
    checks.append(label)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-policy", action="store_true")
    args = parser.parse_args()

    repo = Path.cwd()
    run_root = repo / ".agent-harness" / "runs" / RUN_ID
    assignment_path = run_root / "assignments" / f"{ASSIGNMENT_ID}.json"
    coverage_path = run_root / "results" / f"{ASSIGNMENT_ID}.review_coverage.json"
    seal_path = repo / ".prguard/runtime/PR289_R2_CANDIDATE_SEAL.json"
    assignment = json.loads(assignment_path.read_text())
    context = json.loads((repo / ".agent-harness/context/CONTEXT_INDEX.json").read_text())
    seal = json.loads(seal_path.read_text())
    policy = json.loads(
        (repo / "docs/research_program/post_pr275/pr289_publication_policy.json").read_text()
    )
    spec = yaml.safe_load(
        (repo / "docs/research_program/post_pr275/pr289_spec.yaml").read_text()
    )
    receipt = json.loads(
        (repo / "docs/generated/pr289_data_identity_v2_receipt.json").read_text()
    )
    status_path = repo / "docs/codex_handoff/pr_status.yaml"
    mirror_path = repo / "machine_readable/pr_status.yaml"
    status = yaml.safe_load(status_path.read_text())
    checks: list[str] = []

    check(assignment["run_id"] == RUN_ID, "assignment_run_id", checks)
    check(assignment["assignment_id"] == ASSIGNMENT_ID, "assignment_id", checks)
    check(assignment["context_version"] == CONTEXT_VERSION, "assignment_context", checks)
    check(context["context_version"] == CONTEXT_VERSION, "live_context", checks)
    check(assignment["independence_mode"] == "blind-results", "blind_results", checks)
    check(assignment["allowed_sibling_results"] == [], "no_sibling_results", checks)

    for item in assignment["required_inputs"]:
        check(sha256_file(repo / item["path"]) == item["sha256"], f"input:{item['path']}", checks)

    binding = assignment["candidate_binding"]
    check(sha256_file(seal_path) == binding["seal_file_sha256"], "seal_file_sha256", checks)
    check(git("rev-parse", "HEAD") == binding["candidate_sha"], "candidate_sha", checks)
    check(git("rev-parse", "HEAD^{tree}") == binding["candidate_tree_sha"], "candidate_tree", checks)
    check(
        git("merge-base", binding["base_sha"], binding["candidate_sha"])
        == binding["merge_base_sha"],
        "merge_base",
        checks,
    )
    commits = git("rev-list", "--reverse", f"{seal['base_sha']}..{seal['candidate_sha']}").splitlines()
    check(commits == seal["candidate_commits"], "candidate_commit_order", checks)
    check(
        sha256_bytes(canonical_json({"commits": commits})) == seal["candidate_commits_sha256"],
        "candidate_commits_sha256",
        checks,
    )
    live_patch_ids = [
        {"commit": commit, "stable_patch_id": stable_patch_id(commit)} for commit in commits
    ]
    check(live_patch_ids == seal["stable_patch_ids"], "stable_patch_id_replay", checks)
    check(
        len({row["stable_patch_id"] for row in live_patch_ids}) == len(live_patch_ids),
        "candidate_patch_ids_unique",
        checks,
    )
    check(
        sha256_bytes(canonical_json({"stable_patch_ids": live_patch_ids}))
        == seal["stable_patch_ids_sha256"],
        "stable_patch_ids_sha256",
        checks,
    )
    changed = []
    for line in git("diff", "--name-status", seal["base_sha"], seal["candidate_sha"]).splitlines():
        status_code, path = line.split("\t", 1)
        changed.append({"status": status_code, "path": path})
    check(changed == seal["changed_files"], "changed_files", checks)
    check(
        sha256_bytes(canonical_json({"changed_files": changed})) == seal["changed_files_sha256"],
        "changed_files_sha256",
        checks,
    )
    full_diff = git(
        "diff", "--full-index", "--binary", seal["base_sha"], seal["candidate_sha"], binary=True
    )
    check(sha256_bytes(full_diff) == seal["diff_sha256"], "diff_sha256", checks)
    seal_body = dict(seal)
    seal_body.pop("seal_sha256")
    check(sha256_bytes(canonical_json(seal_body)) == seal["seal_sha256"], "seal_sha256", checks)

    historical = {
        "G39": ["44091dea"],
        "G40": ["a757eeee"],
        "G42": ["c2037e8a", "681285b0", "da3cdb82"],
        "G45": ["7f9ac031", "d697fe08", "db41afc8"],
        "G46": ["834e15d7", "6a9f9d5e"],
        "G47": ["91d8b8ad", "52386845"],
        "G48": ["dde54a71", "48e280d9"],
    }
    historic_pids = {key: {stable_patch_id(c) for c in values} for key, values in historical.items()}
    candidate_pids = {row["stable_patch_id"] for row in live_patch_ids}
    check(len(historic_pids["G45"]) == 1 and historic_pids["G45"] <= candidate_pids, "G45_exact_once", checks)
    check(len(historic_pids["G46"]) == 1 and historic_pids["G46"] <= candidate_pids, "G46_exact_once", checks)
    check(not (historic_pids["G39"] | historic_pids["G40"] | historic_pids["G42"]) & candidate_pids, "obsolete_G39_G40_G42_absent", checks)
    g47_original = changed_paths("834e15d7", "91d8b8ad")
    g47_selected = changed_paths("ac898295", "8cbbdb4d")
    check(g47_selected == g47_original - {"docs/generated/pr289_data_identity_v2_receipt.json"}, "G47_bounded_without_stale_receipt", checks)
    g48_original = changed_paths("91d8b8ad", "dde54a71")
    g48_selected = changed_paths("8cbbdb4d", "fd36d51d")
    check(g48_selected == {"scripts/codex_harness/run_pr289_data_identity_v2.py", "tests/contracts/test_data_identity_registry_v2.py"}, "G48_bounded_runner_test_subset", checks)
    check(g48_selected <= g48_original, "G48_selected_paths_from_lineage", checks)

    expected_mutations = [row["mutation_id"] for row in spec["mutation_registry"]]
    actual_mutations = [row["mutation_id"] for row in receipt["mutation_results"]]
    check(len(expected_mutations) == 32, "mutation_registry_32", checks)
    check(actual_mutations == expected_mutations, "mutation_order_exact", checks)
    check(all(row["activated"] and row["executed"] and row["killed"] for row in receipt["mutation_results"]), "mutations_32_of_32_killed", checks)
    check(receipt["aggregate_status"] == "NO_ADMITTED_IDENTITIES", "zero_admission", checks)
    check(not receipt["observed_data_executed"] and not receipt["public_use"], "no_execution_or_public_use", checks)
    check(all(row["status"] == "NOT_AUTHORIZED" for row in receipt["authorization_receipts"]), "all_not_authorized", checks)

    check(status_path.read_bytes() == mirror_path.read_bytes(), "status_mirror_byte_equal", checks)
    pr289 = status["stacked_pr_execution"]["prs"]["PR-289"]
    pr290 = status["stacked_pr_execution"]["prs"]["PR-290"]
    check(pr289["base_sha"] == binding["base_sha"], "status_pr289_base", checks)
    check(pr289["predecessor_sealed_sha"] == binding["base_sha"], "status_pr288_sealed_predecessor", checks)
    check(pr289["lifecycle"] == "VALIDATED" and pr289["lifecycle_history"][-1] == "VALIDATED", "pr289_lifecycle_preserved", checks)
    check(pr289["gate_dispositions"]["review"] == "FAIL", "r1_review_fail_preserved", checks)
    check(pr290["lifecycle"] == "PLANNED" and pr290["gate_dispositions"] == {"eligibility": "INELIGIBLE"}, "pr290_ineligible", checks)
    check(pr290["predecessor_sealed_sha"] is None, "pr290_no_predecessor_seal", checks)
    check(binding["production_hash"] == seal["production_hash"] == pr289["production_hash"], "production_hash_cross_binding", checks)

    dependency_paths = {
        "pr289_spec": "docs/research_program/post_pr275/pr289_spec.yaml",
        "publication_policy": "docs/research_program/post_pr275/pr289_publication_policy.json",
        "lane_registry": "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json",
        "data_runbooks": "docs/research_program/post_pr275/data_runbooks.yaml",
        "claim_ledger": "docs/harness/CLAIM_LEDGER.md",
        "pr289_runner": "scripts/codex_harness/run_pr289_data_identity_v2.py",
        "pr289_contract_test": "tests/contracts/test_data_identity_registry_v2.py",
        "pr274_registry": "docs/research_program/vector_tensor/data_admission/PR274_DATA_IDENTITY_REGISTRY.yaml",
        "pr274_result": "docs/research_program/vector_tensor/data_admission/PR274_ADMISSION_RESULT.json",
        "data_identity_receipt": "docs/generated/pr289_data_identity_v2_receipt.json",
        "publication_integrity": ".agent-harness/scripts/publication_integrity.py",
        "dag_validator": "scripts/codex_harness/validate_pr_dag.py",
        "claim_linter": "scripts/check_claim_language.py",
    }
    for key, relative in dependency_paths.items():
        check(sha256_file(repo / relative) == pr289["dependency_hashes"][key], f"dependency:{key}", checks)
    check(sha256_file(CANONICAL_AUDIT) == EXPECTED_AUDIT_SHA256, "canonical_audit_hash", checks)
    check(pr289["dependency_hashes"]["salvage_audit"] == EXPECTED_AUDIT_SHA256, "status_audit_binding", checks)

    coverage = json.loads(coverage_path.read_text())
    policy_cells = policy["required_review_cells"]
    check(len(policy["required_commands"]) == 8, "eight_policy_commands", checks)
    check(len(policy_cells) == 36, "thirty_six_review_cells", checks)
    check([row["cell_id"] for row in coverage["cells"]] == policy_cells, "coverage_order_exact", checks)
    check(all(row["outcome"] == "pass" for row in coverage["cells"]), "coverage_all_pass", checks)

    policy_results = []
    if args.run_policy:
        for command in policy["required_commands"]:
            argv = [sys.executable if token == "{python}" else token for token in command["argv"]]
            completed = subprocess.run(argv, capture_output=True, timeout=command["timeout_seconds"])
            policy_results.append(
                {
                    "id": command["id"],
                    "exit_code": completed.returncode,
                    "stdout_sha256": sha256_bytes(completed.stdout),
                    "stderr_sha256": sha256_bytes(completed.stderr),
                }
            )
            check(completed.returncode == 0, f"policy:{command['id']}", checks)

    print(
        json.dumps(
            {
                "schema": "PR289_R2_REPLAY_ORACLE_V1",
                "assignment_id": ASSIGNMENT_ID,
                "context_version": CONTEXT_VERSION,
                "status": "PASS",
                "checks_passed": len(checks),
                "checks": checks,
                "policy_results": policy_results,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
