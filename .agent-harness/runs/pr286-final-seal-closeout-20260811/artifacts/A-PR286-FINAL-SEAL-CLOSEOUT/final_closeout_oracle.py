#!/usr/bin/env python3
"""Bounded metadata oracle for the exact PR-286 final-seal closeout."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


RUN_ID = "pr286-final-seal-closeout-20260811"
ASSIGNMENT_ID = "A-PR286-FINAL-SEAL-CLOSEOUT"
CONTEXT_VERSION = "e9b385d7fbc4f8e47c97c3b0c7edae4e522d9be4e025d9342e26ab24829e3019"
BASE_SHA = "16bc6db511b8b7228e5c4dcb95c65074fe519f24"
CANDIDATE_SHA = "b955a050f19db853a93779506e8acb4e4a5352a9"
REVIEWED_SHA = "0b1a8ef76df47b0b42e972bb47c9bc294e80aa7c"
PRODUCTION_HASH = "99ad99e15ff863b63945663c112767d1f6dc90e8f697a407798c281cb39c2b30"

SEAL_PATH = ".prguard/runtime/PR286_FINAL_CANDIDATE_SEAL.json"
RECEIPT_PATH = ".prguard/runtime/PR286_FINAL_INTEGRATION_REHEARSAL.json"
R3_SEAL_PATH = ".prguard/runtime/PR286_R3_MIO_CANDIDATE_SEAL.json"
POLICY_PATH = "docs/research_program/post_pr275/pr286_publication_policy.json"
SPEC_PATH = "docs/research_program/post_pr275/pr286_spec.yaml"
DELTA_PATH = "docs/PR_DELTAS/pr-286.md"
STATUS_PATH = "docs/codex_handoff/pr_status.yaml"
STATUS_MIRROR_PATH = "machine_readable/pr_status.yaml"
PLAN_PATH = f".agent-harness/runs/{RUN_ID}/RUN_PLAN.json"
ASSIGNMENT_PATH = f".agent-harness/runs/{RUN_ID}/assignments/{ASSIGNMENT_ID}.json"

REREVIEW = ".agent-harness/runs/pr286-mio-nonfinite-r3-rereview-20260811"
RESULT_PATHS = {
    "A-PR286-R3-MIO-PHYSCODE": f"{REREVIEW}/results/A-PR286-R3-MIO-PHYSCODE.json",
    "A-PR286-R3-REPLAY": f"{REREVIEW}/results/A-PR286-R3-REPLAY.json",
    "A-PR286-R3-CLAIM": f"{REREVIEW}/results/A-PR286-R3-CLAIM.json",
    "A-PR286-R3-CLAIM-REPLACEMENT": f"{REREVIEW}/results/A-PR286-R3-CLAIM-REPLACEMENT.json",
}
MERGED_PATH = f"{REREVIEW}/MERGED_RESULTS.json"
SUMMARY_PATH = f"{REREVIEW}/RUN_SUMMARY.json"

REQUIRED_HASHES = {
    SEAL_PATH: "a3f30d393b84f3d53a112c944952f1129978208a9f28f1e1c5eee4be599f28f7",
    RECEIPT_PATH: "c12471b2f9f03d93adc5c6d3fcc86229d378c394f8db7bad7a8e1ac9b6f6f959",
    R3_SEAL_PATH: "d95f5a26bab5be25afb550e64d75ce4f8419fca8b61b232682c960e9e5e1fc95",
    RESULT_PATHS["A-PR286-R3-MIO-PHYSCODE"]: "b1d5f3504dc2752a8dbdade1e464864ea985f147a8258671159e7779c5188617",
    RESULT_PATHS["A-PR286-R3-REPLAY"]: "a9448fef082115cf74df6f2be04460571939e4019fbb130af3a0129d7e18e326",
    RESULT_PATHS["A-PR286-R3-CLAIM"]: "2d585f6eada9756508dd71594480e8c12e1a088fb70aff2748e2d7578bb33d0f",
    RESULT_PATHS["A-PR286-R3-CLAIM-REPLACEMENT"]: "e4ca970913b33a7c12f8a279ffadcd35778ef1369d4bc2d4de69b4147ec4a851",
    MERGED_PATH: "cb7cdafecee97de9b172161dc95f6638ec1cb110bb6aa29e7bc84fa8374f2796",
    SUMMARY_PATH: "92e06e59d67f513547a80fe8ab4000cff6f4f56679992ad40e0f2d4f763199aa",
    POLICY_PATH: "768b5263096154770e48762704e363d127ea1c1ef89a8c973f94a14173ec086d",
    SPEC_PATH: "6fca230213eea5c914842c63513a9047cb3221d0646564692464a82d7a03fc05",
    DELTA_PATH: "f08a04710b1b0849558e774f10bacd451f5452b54cca398e793f01e4ecf81cc5",
    STATUS_PATH: "dc466d9ccd50421d72c56b24a6214b35f7a9e3c5eed4ccab93f369ae1bce1b27",
    STATUS_MIRROR_PATH: "dc466d9ccd50421d72c56b24a6214b35f7a9e3c5eed4ccab93f369ae1bce1b27",
}

PASS_RESULT_IDS = {
    "A-PR286-R3-MIO-PHYSCODE",
    "A-PR286-R3-REPLAY",
    "A-PR286-R3-CLAIM-REPLACEMENT",
}
ERROR_RESULT_ID = "A-PR286-R3-CLAIM"
FINAL_ONLY_PATHS = {
    DELTA_PATH,
    STATUS_PATH,
    STATUS_MIRROR_PATH,
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_sha256(value: dict[str, Any], *, omit: set[str] | None = None) -> str:
    payload = dict(value)
    for field in omit or set():
        payload.pop(field, None)
    data = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return sha256_bytes(data)


def read_json(repo: Path, relative: str) -> dict[str, Any]:
    value = json.loads((repo / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{relative} is not a JSON object")
    return value


def git(repo: Path, *args: str, input_bytes: bytes | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"git {' '.join(args)} failed ({result.returncode}): "
            f"{result.stderr.decode('utf-8', errors='replace').strip()}"
        )
    return result.stdout.decode("utf-8").strip()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def stable_patch_id(repo: Path, commit: str) -> str:
    diff = subprocess.run(
        ["git", "show", "--pretty=format:", "--binary", commit],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    require(diff.returncode == 0, f"cannot render patch for {commit}")
    patch = subprocess.run(
        ["git", "patch-id", "--stable"],
        cwd=repo,
        input=diff.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    require(patch.returncode == 0, f"cannot compute stable patch id for {commit}")
    fields = patch.stdout.decode("utf-8").split()
    require(len(fields) >= 1, f"empty stable patch id for {commit}")
    return fields[0]


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--coverage-output", required=True)
    args = parser.parse_args()

    started_at = iso_now()
    repo = Path(git(Path.cwd(), "rev-parse", "--show-toplevel")).resolve()
    scripts = repo / ".agent-harness" / "scripts"
    sys.path.insert(0, str(scripts))
    from publication_integrity import (  # pylint: disable=import-error
        load_publication_policy,
        parse_utc,
        validate_candidate_seal_payload,
        validate_integration_receipt_payload,
    )

    output_rel = Path(args.output).as_posix()
    coverage_rel = Path(args.coverage_output).as_posix()
    require(not Path(output_rel).is_absolute(), "output must be repository-relative")
    require(
        not Path(coverage_rel).is_absolute(),
        "coverage output must be repository-relative",
    )

    checks: dict[str, bool] = {}
    details: dict[str, Any] = {}

    observed_hashes = {
        relative: sha256_bytes((repo / relative).read_bytes())
        for relative in REQUIRED_HASHES
    }
    require(observed_hashes == REQUIRED_HASHES, "required input hash drift")
    checks["required_input_hashes_exact"] = True

    plan = read_json(repo, PLAN_PATH)
    assignment = read_json(repo, ASSIGNMENT_PATH)
    seal = read_json(repo, SEAL_PATH)
    receipt = read_json(repo, RECEIPT_PATH)
    r3_seal = read_json(repo, R3_SEAL_PATH)
    policy = read_json(repo, POLICY_PATH)
    merged = read_json(repo, MERGED_PATH)
    summary = read_json(repo, SUMMARY_PATH)
    results = {key: read_json(repo, path) for key, path in RESULT_PATHS.items()}

    require(assignment["context_version"] == CONTEXT_VERSION, "assignment context drift")
    require(plan["context_version"] == CONTEXT_VERSION, "run context drift")
    require(plan["candidate_binding"] == assignment["candidate_binding"], "plan/assignment binding drift")
    checks["context_and_candidate_binding_exact"] = True

    require(git(repo, "rev-parse", "HEAD") == CANDIDATE_SHA, "HEAD drift")
    require(git(repo, "status", "--porcelain=v1", "--untracked-files=all") == "", "worktree is dirty")
    require(seal["candidate_sha"] == CANDIDATE_SHA, "final seal candidate drift")
    require(seal["base_sha"] == BASE_SHA, "final seal base drift")
    require(seal["merge_base_sha"] == BASE_SHA, "final seal merge-base drift")
    require(git(repo, "merge-base", BASE_SHA, CANDIDATE_SHA) == BASE_SHA, "live merge-base drift")
    predecessor_ref = "refs/remotes/origin/changeset/pr285-pillar-t-adjudication-recovery-20260810"
    require(git(repo, "rev-parse", predecessor_ref) == BASE_SHA, "PR-285 predecessor ref drift")
    require(plan["predecessor_pr"] == "PR-285", "predecessor identity drift")
    require(plan["predecessor_sealed_sha"] == BASE_SHA, "predecessor seal drift")
    checks["exact_head_clean_predecessor_and_merge_base"] = True

    seal_errors = validate_candidate_seal_payload(seal, repo=repo)
    require(not seal_errors, f"candidate seal validation failed: {seal_errors}")
    require(seal["seal_sha256"] == "f9907e837137ee5315f26b0c891de1264ab089ed0a6ffbd7b5a9f0d2005ee107", "seal identity drift")
    checks["final_candidate_seal_strict_valid"] = True

    _, loaded_policy = load_publication_policy(
        repo,
        POLICY_PATH,
        expected_sha256=REQUIRED_HASHES[POLICY_PATH],
    )
    require(loaded_policy == policy, "loaded policy drift")
    receipt_errors = validate_integration_receipt_payload(
        receipt,
        seal=seal,
        policy=policy,
        now=parse_utc(receipt["completed_at"], field="integration completed_at"),
        repo=repo,
        log_dir=None,
    )
    require(not receipt_errors, f"integration receipt validation failed: {receipt_errors}")
    require(receipt["status"] == "PASS", "integration receipt is not PASS")
    require(len(receipt["commands"]) == len(policy["required_commands"]) == 10, "integration command coverage drift")
    require(
        [row["id"] for row in receipt["commands"]]
        == [row["id"] for row in policy["required_commands"]],
        "integration command order drift",
    )
    checks["final_integration_receipt_strict_valid"] = True

    commits = git(repo, "rev-list", "--reverse", f"{BASE_SHA}..{CANDIDATE_SHA}").splitlines()
    require(commits == seal["candidate_commits"], "candidate commit list drift")
    require(len(commits) == 14, "candidate lineage must contain exactly 14 commits")
    patch_ids = [stable_patch_id(repo, commit) for commit in commits]
    registered_patch_ids = [row["stable_patch_id"] for row in seal["stable_patch_ids"]]
    require(patch_ids == registered_patch_ids, "stable patch-id replay drift")
    require(len(set(patch_ids)) == 14, "stable patch ids are not unique")
    require(git(repo, "rev-list", "--merges", f"{BASE_SHA}..{CANDIDATE_SHA}") == "", "candidate lineage contains a merge commit")
    checks["fourteen_unique_stable_patch_ids_linear_lineage"] = True

    final_slice = git(
        repo,
        "diff-tree",
        "--no-commit-id",
        "--name-only",
        "-r",
        f"{REVIEWED_SHA}^..{CANDIDATE_SHA}",
    ).splitlines()
    require(set(final_slice) == FINAL_ONLY_PATHS, "review-to-final slice changed unexpected paths")
    require(
        int(git(repo, "rev-list", "--count", f"{REVIEWED_SHA}^..{CANDIDATE_SHA}")) == 2,
        "review-to-final slice must contain exactly two commits",
    )
    require(r3_seal["candidate_sha"] == REVIEWED_SHA, "rereview seal candidate drift")
    require(seal["production_hash"] == r3_seal["production_hash"] == PRODUCTION_HASH, "production hash changed after rereview")
    require(seal["changed_files_sha256"] == r3_seal["changed_files_sha256"], "changed-file set drifted after rereview")
    checks["post_review_changes_metadata_only_and_production_unchanged"] = True

    require(merged["process_status"] == "STRUCTURALLY_VALID", "rereview aggregate is not structurally valid")
    require(merged["result_count"] == merged["validated_result_count"] == 4, "aggregate result count drift")
    require(merged["findings"] == merged["conflicts"] == merged["errors"] == [], "aggregate contains findings/conflicts/errors")
    dispositions = {row["assignment_id"]: row for row in merged["result_dispositions"]}
    require(set(dispositions) == PASS_RESULT_IDS | {ERROR_RESULT_ID}, "aggregate assignment set drift")
    for assignment_id in PASS_RESULT_IDS:
        require(results[assignment_id]["status"] == "pass", f"{assignment_id} did not pass")
        require(results[assignment_id]["gate_disposition"] == "PASS", f"{assignment_id} gate drift")
        require(dispositions[assignment_id]["status"] == "pass", f"aggregate lost PASS for {assignment_id}")
    error_result = results[ERROR_RESULT_ID]
    require(error_result["status"] == "error", "isolated claim attempt status drift")
    require(error_result["gate_disposition"] == "INCONCLUSIVE", "isolated claim gate drift")
    require(error_result["errors"] and "BLIND_RESULTS_ISOLATION_BREACH" in error_result["errors"][0], "isolated claim chronology missing")
    require(all(row["outcome"] == "not_examined" for row in error_result["claim_results"]), "isolated claim attempt was regraded")
    require(dispositions[ERROR_RESULT_ID]["status"] == "error", "aggregate hid isolated error")
    summary_rows = {row["assignment_id"]: row for row in summary["results"]}
    require(set(summary_rows) == set(dispositions), "summary result set drift")
    for assignment_id, path in RESULT_PATHS.items():
        require(summary_rows[assignment_id]["sha256"] == REQUIRED_HASHES[path], f"summary hash drift for {assignment_id}")
    require(summary["merged_results"]["sha256"] == REQUIRED_HASHES[MERGED_PATH], "summary aggregate hash drift")
    checks["immutable_review_three_pass_one_error_preserved"] = True

    status_bytes = (repo / STATUS_PATH).read_bytes()
    require(status_bytes == (repo / STATUS_MIRROR_PATH).read_bytes(), "status mirrors differ")
    status = yaml.safe_load(status_bytes)
    pr286 = status["stacked_pr_execution"]["prs"]["PR-286"]
    pr287 = status["stacked_pr_execution"]["prs"]["PR-287"]
    require(pr286["lifecycle"] == "REVIEWED", "PR-286 lifecycle is not REVIEWED")
    require(pr286["assurance_budget"] == {"maximum": 16, "consumed": 11}, "PR-286 pre-assignment assurance drift")
    require(pr286["production_hash"] == PRODUCTION_HASH, "status production hash drift")
    require(pr286["dependency_hashes"] == plan["dependency_hashes"], "status/plan dependency hash drift")
    require(plan["evidence_key"] == {"production_hash": PRODUCTION_HASH, "dependency_hashes": pr286["dependency_hashes"]}, "plan evidence key drift")
    require(summary["evidence_key"] == plan["evidence_key"], "rereview/current evidence key drift")
    require(pr287["lifecycle"] == "PLANNED", "PR-287 lifecycle drift")
    require(pr287["gate_dispositions"] == {"eligibility": "INELIGIBLE"}, "PR-287 eligibility drift")
    require(pr287["assurance_budget"] == {"maximum": 16, "consumed": 0}, "PR-287 budget drift")
    require(pr287["base_sha"] is None and pr287["sealed_head"] is None, "PR-287 acquired candidate authority")
    require(plan["lifecycle_state"] == "REVIEWED", "run plan lifecycle drift")
    require(plan["assurance_budget"] == {"maximum": 16, "consumed": 11}, "run plan budget drift")
    checks["reviewed_lifecycle_evidence_key_and_pr287_gate_exact"] = True

    require(pr286["pushed_ref"] is None and pr286["pr_url"] is None, "PR-286 recorded push or PR")
    require(plan["github_pr_created_by_harness"] is False, "harness recorded PR creation")
    require(summary["github_pr_created_by_harness"] is False, "rereview recorded PR creation")
    remote_refs = git(repo, "for-each-ref", "--format=%(refname)", "refs/remotes/origin/changeset/pr286*")
    require(remote_refs == "", "local remote-tracking evidence of PR-286 push exists")
    upstream = git(repo, "for-each-ref", "--format=%(upstream)", "refs/heads/changeset/pr286-pillar-s-adjudication-recovery-20260810")
    require(upstream == "", "PR-286 branch has an upstream")
    checks["no_recorded_push_pr_or_merge"] = True

    delta = (repo / DELTA_PATH).read_text(encoding="utf-8")
    require("Lifecycle advances legally from `VALIDATED` to `REVIEWED`." in delta, "delta lacks REVIEWED chronology")
    require("Assurance consumption is 11 of 16, including the isolated error attempt." in delta, "delta lacks assurance chronology")
    require(REQUIRED_HASHES[MERGED_PATH] in delta and REQUIRED_HASHES[SUMMARY_PATH] in delta, "delta lacks immutable aggregate hashes")
    require(REQUIRED_HASHES[RESULT_PATHS["A-PR286-R3-CLAIM"]] in observed_hashes.values(), "isolated error hash unavailable")
    checks["pr_delta_records_current_review_chronology"] = True

    assurance_after = pr286["assurance_budget"]["consumed"] + 1
    require(assurance_after == 12 and assurance_after <= pr286["assurance_budget"]["maximum"], "post-assignment assurance accounting drift")
    checks["post_assignment_assurance_is_twelve_of_sixteen"] = True

    require(all(checks.values()), "one or more closeout checks failed")
    completed_at = iso_now()
    details.update(
        {
            "base_sha": BASE_SHA,
            "candidate_sha": CANDIDATE_SHA,
            "candidate_tree_sha": seal["candidate_tree_sha"],
            "candidate_seal_sha256": seal["seal_sha256"],
            "integration_receipt_sha256": receipt["receipt_sha256"],
            "candidate_commit_count": len(commits),
            "unique_stable_patch_id_count": len(set(patch_ids)),
            "review_pass_assignments": sorted(PASS_RESULT_IDS),
            "preserved_nonacceptance_assignment": ERROR_RESULT_ID,
            "production_hash": PRODUCTION_HASH,
            "assurance_before_assignment": 11,
            "assignment_cost": 1,
            "assurance_after_registered_result": assurance_after,
            "assurance_maximum": 16,
            "pr286_lifecycle": pr286["lifecycle"],
            "pr287_lifecycle": pr287["lifecycle"],
            "pr287_eligibility": pr287["gate_dispositions"]["eligibility"],
            "pr287_assurance_consumed": pr287["assurance_budget"]["consumed"],
            "final_metadata_only_paths": sorted(FINAL_ONLY_PATHS),
            "publication_observation_scope": "repository-local recorded state only; no network query performed",
        }
    )
    report = {
        "schema_version": 1,
        "oracle_id": "PR286-FINAL-SEAL-CLOSEOUT-INVARIANTS",
        "run_id": RUN_ID,
        "assignment_id": ASSIGNMENT_ID,
        "context_version": CONTEXT_VERSION,
        "started_at": started_at,
        "completed_at": completed_at,
        "status": "PASS",
        "checks": checks,
        "details": details,
        "required_input_hashes": observed_hashes,
    }
    output_path = repo / output_rel
    write_json(output_path, report)
    report_bytes = output_path.read_bytes()

    script_rel = Path(__file__).resolve().relative_to(repo).as_posix()
    argv = [
        str(Path(os.path.abspath(sys.executable))),
        "-B",
        script_rel,
        "--output",
        output_rel,
        "--coverage-output",
        coverage_rel,
    ]
    common_evidence = [output_rel, SEAL_PATH, RECEIPT_PATH, MERGED_PATH, SUMMARY_PATH]
    coverage_cells = []
    for cell in policy["required_review_cells"]:
        coverage_cells.append(
            {
                "cell": cell,
                "status": "PASS",
                "evidence_refs": common_evidence,
                "rationale": (
                    "Adjudication closeout inherits the substantive verdict only from "
                    "the exact registered rereview aggregate and summary; this oracle "
                    "rechecks immutable metadata, seal, receipt, lineage, lifecycle, and "
                    "non-publication invariants without rerunning scientific assurance."
                ),
            }
        )
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
        "completed_at": completed_at,
        "first_verdict_read_only": True,
        "correlated_review": True,
        "coverage_cells": coverage_cells,
        "independent_oracles": [
            {
                "oracle_id": "PR286-FINAL-SEAL-CLOSEOUT-INVARIANTS",
                "kind": "invariant_checker",
                "status": "PASS",
                "argv": argv,
                "command_fingerprint": canonical_sha256({"argv": argv}),
                "returncode": 0,
                "timed_out": False,
                "started_at": started_at,
                "completed_at": completed_at,
                "artifact_path": output_rel,
                "artifact_sha256": sha256_bytes(report_bytes),
                "artifact_bytes": len(report_bytes),
                "evidence_refs": common_evidence,
            }
        ],
    }
    coverage["coverage_sha256"] = canonical_sha256(
        coverage, omit={"coverage_sha256"}
    )
    write_json(repo / coverage_rel, coverage)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
