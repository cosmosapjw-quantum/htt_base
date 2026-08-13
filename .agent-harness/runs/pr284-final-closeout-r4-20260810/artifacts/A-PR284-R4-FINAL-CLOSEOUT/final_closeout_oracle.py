#!/usr/bin/env python3
"""PR-284 final closeout oracle; performs no substantive assurance rerun."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


RUN_ID = "pr284-final-closeout-r4-20260810"
ASSIGNMENT_ID = "A-PR284-R4-FINAL-CLOSEOUT"
CONTEXT_VERSION = (
    "e9b385d7fbc4f8e47c97c3b0c7edae4e522d9be4e025d9342e26ab24829e3019"
)
BASE = "b6b6952d52f59bbe05477ef3b02292a98fe92baa"
REVIEW_CANDIDATE = "50fea58d2bd4d33dfac017f46bf22df5ccd289d1"
FINAL_CANDIDATE = "30bf45339cf517ff77606c3f8abcdeb2949b36e9"
FINAL_TREE = "d8352d6ca5286a6b1f364429c218d307b3dea28d"
PRODUCTION_HASH = (
    "842d469e906b2b55eadcdda56cac59924ae2189ac2677ef8a5e605e03a0be034"
)
SEAL_FILE_SHA256 = (
    "f98552fabd7062a76093bcbc7a2d700ed7d588cf12b3cf4d71bb5f853217241e"
)
INTEGRATION_FILE_SHA256 = (
    "6efc73e5bcdc3b0e3134396696fc1d006b74b7f412172cbf72154d7dfc1ad504"
)
PRIOR_RESULTS = {
    "A-PR284-R4-PHYSCODE": (
        "4da3f4ef8ced651dfb08239e6e3d0177f1e9fe534e99c48be502e8240df68ee4"
    ),
    "A-PR284-R4-REPLAY": (
        "2da1ac0e0d7af42486770fe226b429f0266fdf1393fc9db3546372deda9e1d7e"
    ),
    "A-PR284-R4-CLAIM": (
        "5eab74802cb8a849250b46edc111cdf4f63002baea1ead9f81ecee3b2024eda6"
    ),
}
PRIOR_AGGREGATE_SHA256 = (
    "02c3e7fa89830d0096929cc1667e0df4b836a20525c4f6572d293a51d0153215"
)
PRIOR_SUMMARY_SHA256 = (
    "0ecddabe0a1186c20f40d9396d32883d32e20e01c5a68bf7bd3f3c171839ac7c"
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _json(root: Path, relative: str) -> tuple[bytes, dict[str, Any]]:
    data = (root / relative).read_bytes()
    value = json.loads(data)
    if not isinstance(value, dict):
        raise AssertionError(f"{relative} is not a JSON object")
    return data, value


def _git(root: Path, *args: str, binary: bool = False) -> str | bytes:
    completed = subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True
    )
    if binary:
        return completed.stdout
    return completed.stdout.decode("utf-8").strip()


def _patch_id(root: Path, commit: str) -> str:
    shown = _git(
        root,
        "show",
        "--pretty=format:",
        "--binary",
        "--full-index",
        commit,
        binary=True,
    )
    assert isinstance(shown, bytes) and shown
    row = subprocess.run(
        ["git", "patch-id", "--stable"],
        cwd=root,
        input=shown,
        check=True,
        capture_output=True,
    ).stdout.decode("ascii").strip()
    if not row:
        raise AssertionError(f"no stable patch ID for {commit}")
    return row.split()[0]


def _base_patch_ids(root: Path) -> set[str]:
    history = subprocess.run(
        [
            "git",
            "log",
            "--no-merges",
            "--pretty=format:commit %H",
            "-p",
            BASE,
        ],
        cwd=root,
        check=True,
        capture_output=True,
    ).stdout
    rows = subprocess.run(
        ["git", "patch-id", "--stable"],
        cwd=root,
        input=history,
        check=True,
        capture_output=True,
    ).stdout.decode("ascii")
    return {row.split()[0] for row in rows.splitlines() if row.strip()}


def _changed_files(root: Path, start: str, end: str) -> list[dict[str, str]]:
    raw = _git(
        root,
        "diff",
        "--name-status",
        "--no-renames",
        "-z",
        f"{start}..{end}",
        binary=True,
    )
    assert isinstance(raw, bytes)
    parts = [part for part in raw.split(b"\0") if part]
    if len(parts) % 2:
        raise AssertionError("malformed changed-file inventory")
    return [
        {
            "status": parts[index].decode("ascii"),
            "path": parts[index + 1].decode("utf-8"),
        }
        for index in range(0, len(parts), 2)
    ]


def _build(root: Path) -> dict[str, Any]:
    started = _now()
    seal_data, seal = _json(root, ".prguard/runtime/PR284_R4_FINAL_CANDIDATE_SEAL.json")
    integration_data, integration = _json(
        root, ".prguard/runtime/PR284_R4_FINAL_INTEGRATION_REHEARSAL.json"
    )
    _, policy = _json(
        root, "docs/research_program/post_pr275/pr284_publication_policy.json"
    )
    _, plan = _json(
        root, ".agent-harness/runs/pr284-final-closeout-r4-20260810/RUN_PLAN.json"
    )
    aggregate_data, aggregate = _json(
        root, ".agent-harness/runs/pr284-proper-subset-r4-20260810/MERGED_RESULTS.json"
    )
    summary_data, summary = _json(
        root, ".agent-harness/runs/pr284-proper-subset-r4-20260810/RUN_SUMMARY.json"
    )
    status_data = (root / "docs/codex_handoff/pr_status.yaml").read_bytes()
    mirror_data = (root / "machine_readable/pr_status.yaml").read_bytes()
    status = yaml.safe_load(status_data)
    index = json.loads(
        (root / ".agent-harness/context/CONTEXT_INDEX.json").read_text(
            encoding="utf-8"
        )
    )

    assert index["context_version"] == CONTEXT_VERSION
    assert _sha(seal_data) == SEAL_FILE_SHA256
    assert _sha(integration_data) == INTEGRATION_FILE_SHA256
    seal_payload = {key: value for key, value in seal.items() if key != "seal_sha256"}
    assert _sha(_canonical(seal_payload)) == seal["seal_sha256"]
    integration_payload = {
        key: value for key, value in integration.items() if key != "receipt_sha256"
    }
    assert _sha(_canonical(integration_payload)) == integration["receipt_sha256"]

    head = str(_git(root, "rev-parse", "HEAD"))
    tree = str(_git(root, "rev-parse", "HEAD^{tree}"))
    target = str(_git(root, "rev-parse", f"{seal['target_ref']}^{{commit}}"))
    merge_base = str(_git(root, "merge-base", BASE, FINAL_CANDIDATE))
    assert head == seal["candidate_sha"] == FINAL_CANDIDATE
    assert tree == seal["candidate_tree_sha"] == FINAL_TREE
    assert target == seal["base_sha"] == seal["merge_base_sha"] == BASE
    assert merge_base == BASE
    assert seal["production_hash"] == plan["production_hash"] == PRODUCTION_HASH
    assert _git(root, "status", "--porcelain=v1") == ""

    commits = str(
        _git(root, "rev-list", "--reverse", f"{BASE}..{FINAL_CANDIDATE}")
    ).splitlines()
    assert commits == seal["candidate_commits"]
    assert _sha(_canonical({"commits": commits})) == seal["candidate_commits_sha256"]
    patch_rows = [
        {"commit": commit, "stable_patch_id": _patch_id(root, commit)}
        for commit in commits
    ]
    patch_ids = [row["stable_patch_id"] for row in patch_rows]
    assert patch_rows == seal["stable_patch_ids"]
    assert len(patch_ids) == len(set(patch_ids)) == 11
    assert not set(patch_ids) & _base_patch_ids(root)
    assert _sha(_canonical({"stable_patch_ids": patch_rows})) == seal[
        "stable_patch_ids_sha256"
    ]

    diff = _git(
        root,
        "diff",
        "--binary",
        "--full-index",
        "--no-color",
        "--no-ext-diff",
        "--no-textconv",
        "--no-renames",
        "--submodule=short",
        f"{BASE}..{FINAL_CANDIDATE}",
        binary=True,
    )
    assert isinstance(diff, bytes) and _sha(diff) == seal["diff_sha256"]
    final_changed = _changed_files(root, BASE, FINAL_CANDIDATE)
    assert final_changed == seal["changed_files"]
    assert _sha(_canonical({"changed_files": final_changed})) == seal[
        "changed_files_sha256"
    ]

    post_review_changed = _changed_files(root, REVIEW_CANDIDATE, FINAL_CANDIDATE)
    assert post_review_changed == [
        {"status": "M", "path": "docs/PR_DELTAS/pr-284.md"},
        {"status": "M", "path": "docs/codex_handoff/pr_status.yaml"},
        {"status": "M", "path": "machine_readable/pr_status.yaml"},
    ]
    post_review_commits = str(
        _git(
            root,
            "rev-list",
            "--reverse",
            f"{REVIEW_CANDIDATE}..{FINAL_CANDIDATE}",
        )
    ).splitlines()
    assert post_review_commits == [FINAL_CANDIDATE]

    assert integration["status"] == "PASS"
    for key in (
        "candidate_seal_sha256",
        "candidate_sha",
        "candidate_tree_sha",
        "diff_sha256",
        "changed_files_sha256",
    ):
        seal_key = "seal_sha256" if key == "candidate_seal_sha256" else key
        assert integration[key] == seal[seal_key]
    assert integration["latest_target_sha"] == BASE
    assert integration["merged_tree_sha"] == integration["candidate_tree_sha"] == FINAL_TREE
    expected_commands = policy["required_commands"]
    observed_commands = integration["commands"]
    assert len(observed_commands) == len(expected_commands) == 7
    assert [row["id"] for row in observed_commands] == [
        row["id"] for row in expected_commands
    ]
    assert [row["policy_argv"] for row in observed_commands] == [
        row["argv"] for row in expected_commands
    ]
    assert all(
        row["returncode"] == 0 and row["timed_out"] is False
        for row in observed_commands
    )

    assert _sha(aggregate_data) == PRIOR_AGGREGATE_SHA256
    assert _sha(summary_data) == PRIOR_SUMMARY_SHA256
    assert aggregate["process_status"] == "STRUCTURALLY_VALID"
    assert aggregate["assignment_count"] == aggregate["result_count"] == 3
    assert aggregate["validated_result_count"] == 3
    assert aggregate["findings"] == aggregate["conflicts"] == aggregate["errors"] == []
    assert aggregate["raw_finding_count"] == aggregate["unique_finding_count"] == 0

    summary_results = {row["assignment_id"]: row for row in summary["results"]}
    merge_inputs = {row["path"]: row for row in aggregate["merge_inputs"]}
    for assignment_id, expected_sha in PRIOR_RESULTS.items():
        relative = (
            ".agent-harness/runs/pr284-proper-subset-r4-20260810/results/"
            f"{assignment_id}.json"
        )
        data, result = _json(root, relative)
        assert _sha(data) == expected_sha
        assert result["status"] == "pass" and result["gate_disposition"] == "PASS"
        assert result["findings"] == result["errors"] == []
        assert summary_results[assignment_id]["sha256"] == expected_sha
        assert summary_results[assignment_id]["bytes"] == len(data)
        assert merge_inputs[relative]["sha256"] == expected_sha
        assert merge_inputs[relative]["bytes"] == len(data)
    assert summary["merged_results"] == {
        "path": ".agent-harness/runs/pr284-proper-subset-r4-20260810/MERGED_RESULTS.json",
        "sha256": PRIOR_AGGREGATE_SHA256,
        "bytes": len(aggregate_data),
    }
    assert summary["lifecycle_state"] == "VALIDATED"
    assert summary["assurance_budget"] == {"maximum": 16, "consumed": 12}
    assert summary["production_state"] if "production_state" in summary else True
    assert summary["evidence_key"] == plan["evidence_key"]

    assert status_data == mirror_data
    stack = status["stacked_pr_execution"]
    pr284 = stack["prs"]["PR-284"]
    pr285 = stack["prs"]["PR-285"]
    assert pr284["lifecycle"] == plan["lifecycle_state"] == "REVIEWED"
    assert pr284["assurance_budget"] == plan["assurance_budget"] == {
        "maximum": 16,
        "consumed": 15,
    }
    assert pr284["production_hash"] == PRODUCTION_HASH
    assert pr284["dependency_hashes"] == plan["dependency_hashes"]
    assert pr284["gate_dispositions"]["review"] == "PASS"
    assert pr284["gate_dispositions"]["seal"] == "DEFERRED"
    assert pr284["gate_dispositions"]["push"] == "INELIGIBLE"
    assert pr284["gate_dispositions"]["publication"] == "INELIGIBLE"
    assert pr284["sealed_head"] is pr284["pushed_ref"] is pr284["pr_url"] is None
    assert pr285["lifecycle"] == "PLANNED"
    assert pr285["gate_dispositions"] == {"eligibility": "INELIGIBLE"}
    assert pr285["assurance_budget"] == {"maximum": 16, "consumed": 0}
    assert pr285["sealed_head"] is pr285["pushed_ref"] is pr285["pr_url"] is None
    assert plan["github_pr_created_by_harness"] is False
    remote_candidate = subprocess.run(
        [
            "git",
            "show-ref",
            "--verify",
            "--quiet",
            "refs/remotes/origin/changeset/pr284-finite-depth-law-recovery-20260810",
        ],
        cwd=root,
        check=False,
    )
    assert remote_candidate.returncode == 1

    return {
        "schema": "PR284_R4_FINAL_CLOSEOUT_ORACLE_V1",
        "run_id": RUN_ID,
        "assignment_id": ASSIGNMENT_ID,
        "started_at": started,
        "completed_at": _now(),
        "status": "PASS",
        "checks": {
            "candidate_sha": head,
            "candidate_tree_sha": tree,
            "exact_predecessor_sha": target,
            "clean_worktree": True,
            "stable_patch_id_count": len(patch_ids),
            "stable_patch_ids_unique_and_absent_from_base": True,
            "production_hash_unchanged": True,
            "dependency_evidence_key_unchanged": True,
            "post_review_commit_count": len(post_review_commits),
            "post_review_changed_files": post_review_changed,
            "integration_rehearsal_status": integration["status"],
            "integration_command_count": len(observed_commands),
            "all_integration_commands_zero": True,
            "merged_tree_equals_candidate_tree": True,
            "prior_result_count": len(PRIOR_RESULTS),
            "prior_results_all_pass_and_hash_bound": True,
            "prior_aggregate_structurally_valid": True,
            "prior_summary_hash_bound": True,
            "historical_summary_snapshot": {
                "lifecycle": summary["lifecycle_state"],
                "assurance_consumed": summary["assurance_budget"]["consumed"],
            },
            "current_lifecycle": pr284["lifecycle"],
            "current_assurance_consumed": pr284["assurance_budget"]["consumed"],
            "pr285_eligibility": pr285["gate_dispositions"]["eligibility"],
            "pr285_assurance_consumed": pr285["assurance_budget"]["consumed"],
            "repository_recorded_push_pr_or_merge": False,
            "review_grants_merge_authorization": False,
            "historical_live_strict_replay_applicable": False,
            "historical_live_strict_replay_note": (
                "Historical envelopes are hash-bound to the 50fea review snapshot; "
                "the sole 30bf closeout commit intentionally advances PR delta/status "
                "and candidate seal, so immutable hash/internal-summary validation is used."
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[5]
    output = root / args.output
    if output.parent.resolve() != Path(__file__).resolve().parent or output.is_symlink():
        raise SystemExit("output must be a regular assignment-local artifact")
    evidence = _build(root)
    payload = (json.dumps(evidence, indent=2, sort_keys=True) + "\n").encode("utf-8")
    with tempfile.NamedTemporaryFile(
        mode="wb", dir=output.parent, prefix=f".{output.name}.", delete=False
    ) as handle:
        temporary = Path(handle.name)
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, output)
    print(f"PR284_R4_FINAL_CLOSEOUT_ORACLE_PASS {_sha(payload)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
