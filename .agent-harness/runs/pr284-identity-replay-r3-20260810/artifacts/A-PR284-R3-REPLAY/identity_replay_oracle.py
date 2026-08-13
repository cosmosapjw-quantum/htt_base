#!/usr/bin/env python3
"""Independent PR-284 frozen-identity and receipt replay oracle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


RUN_ID = "pr284-identity-replay-r3-20260810"
ASSIGNMENT_ID = "A-PR284-R3-REPLAY"
EXPECTED_CONTEXT_VERSION = (
    "e9b385d7fbc4f8e47c97c3b0c7edae4e522d9be4e025d9342e26ab24829e3019"
)
EXPECTED_SEAL_FILE_SHA256 = (
    "da4a16d506e8adbfa5232ab95ca202cf2009e5f1304d6732fb0c92c3cb343b9a"
)
EXPECTED_BASE = "b6b6952d52f59bbe05477ef3b02292a98fe92baa"
EXPECTED_CANDIDATE = "d54ff22dac780d3b159394237416d28b2bd15dc8"
EXPECTED_TREE = "5fe16f62eb7246c455d116d79d2d422b35dee7b7"
EXPECTED_RECEIPT_CONTENT = (
    "5baa74553ac7e300bb0b0c40cac41f49d8249c41a5a4e1b3abd5cd5d22ffe849"
)
EXPECTED_MUTATION_IDS = (
    "MU284-SUPPORT-NESTING-AS-PROOF",
    "MU284-NONNESTED-SUPPORT",
    "MU284-TARGET-DRIFT",
    "MU284-REPORT-BUILDER-BYPASS",
    "MU284-PREPROCESSING-DRIFT",
    "MU284-FILTRATION-DIRECTION-DRIFT",
    "MU284-THRESHOLD-DRIFT",
    "MU284-ATOM-SELECTION-DRIFT",
    "MU284-PATH-MAXIMUM-DRIFT",
    "MU284-PROBABILITY-LAW-DRIFT",
    "MU284-ESTIMATOR-IDENTITY-DRIFT",
    "MU284-FREE-BOUND-ON-UNPROVED",
    "MU284-MATCHED-MOCK-PLAN-OMITTED",
    "MU284-MATCHED-MOCK-PLAN-DRIFT",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(value: object, *, ensure_ascii: bool = False) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=ensure_ascii,
    ).encode("utf-8")


def _load_json(root: Path, relative: str) -> tuple[bytes, dict[str, Any]]:
    data = (root / relative).read_bytes()
    value = json.loads(data)
    if not isinstance(value, dict):
        raise AssertionError(f"{relative} is not a JSON object")
    return data, value


def _git(root: Path, *args: str, binary: bool = False) -> str | bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
    )
    if binary:
        return completed.stdout
    return completed.stdout.decode("utf-8").strip()


def _stable_patch_id(root: Path, commit: str) -> str:
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
    computed = subprocess.run(
        ["git", "patch-id", "--stable"],
        cwd=root,
        input=shown,
        check=True,
        capture_output=True,
    ).stdout.decode("ascii").strip()
    if not computed:
        raise AssertionError(f"no stable patch ID for {commit}")
    return computed.split()[0]


def _base_patch_ids(root: Path, base: str) -> set[str]:
    history = subprocess.run(
        [
            "git",
            "log",
            "--no-merges",
            "--pretty=format:commit %H",
            "-p",
            base,
        ],
        cwd=root,
        check=True,
        capture_output=True,
    ).stdout
    computed = subprocess.run(
        ["git", "patch-id", "--stable"],
        cwd=root,
        input=history,
        check=True,
        capture_output=True,
    ).stdout.decode("ascii")
    return {line.split()[0] for line in computed.splitlines() if line.strip()}


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


def _hostile_builder_replay(root: Path) -> str:
    for entry in (root, root / "htt/src", root / "htt"):
        text = str(entry)
        if text not in sys.path:
            sys.path.insert(0, text)

    from common.depth_path import DepthPathError
    from common.depth_path_calibration import (
        _build_depth_path_reverse_martingale_report_contract,
    )
    from scripts.codex_harness import run_pr284_depth_path_doob as fixture_builder

    fixture = fixture_builder._proved_fixture()
    report = fixture["report"]
    try:
        _build_depth_path_reverse_martingale_report_contract(
            path=fixture["path"],
            report_id="A-PR284-R3-REPLAY-FORGED-PATH",
            path_content_id="sha256:no-registered-depth-path",
            stratum_content_ids=(
                "sha256:no-registered-stratum-1",
                "sha256:no-registered-stratum-2",
                "sha256:no-registered-stratum-3",
            ),
            threshold_contract=report.threshold_contract,
            filtration_id=report.filtration_id,
            filtration_direction=report.filtration_direction,
            preprocessing_id=report.preprocessing_id,
            estimator_id=report.estimator_id,
            premise_evidence_id="sha256:invented-premise-evidence",
            premise_status=report.premise_status,
            finite_target_law=report.finite_target_law,
            selection_contract=report.selection_contract,
            path_partitions=report.path_partitions,
            sigma_field_ids=report.sigma_field_ids,
            path_values=report.path_values,
            path_maximum_abs=report.path_maximum_abs,
            path_maximum_content_id=report.path_maximum_content_id,
            target_second_moment=report.target_second_moment,
            exact_tower_equalities=report.exact_tower_equalities,
            exact_tower_report_content_id=report.exact_tower_report_content_id,
            unresolved_reasons=(),
            matched_mock_plan=None,
        )
    except DepthPathError as exc:
        marker = "path content identity does not match exact DepthPath replay"
        if marker not in str(exc):
            raise AssertionError(f"hostile builder failed at wrong boundary: {exc}")
        return marker
    raise AssertionError("hostile builder minted a proved report from invented identity")


def _build_evidence(root: Path) -> dict[str, Any]:
    started_at = _utc_now()
    seal_data, seal = _load_json(
        root, ".prguard/runtime/PR284_R3_FINAL_REVIEW_CANDIDATE_SEAL.json"
    )
    policy_data, policy = _load_json(
        root, "docs/research_program/post_pr275/pr284_publication_policy.json"
    )
    _, receipt = _load_json(
        root, "docs/generated/pr284_depth_path_doob_receipt.json"
    )
    spec = yaml.safe_load(
        (root / "docs/research_program/post_pr275/pr284_spec.yaml").read_text(
            encoding="utf-8"
        )
    )
    index = json.loads(
        (root / ".agent-harness/context/CONTEXT_INDEX.json").read_text(
            encoding="utf-8"
        )
    )

    assert index["context_version"] == EXPECTED_CONTEXT_VERSION
    assert _sha256(seal_data) == EXPECTED_SEAL_FILE_SHA256
    seal_without_hash = {key: value for key, value in seal.items() if key != "seal_sha256"}
    assert _sha256(_canonical(seal_without_hash)) == seal["seal_sha256"]
    assert seal["base_sha"] == EXPECTED_BASE
    assert seal["merge_base_sha"] == EXPECTED_BASE
    assert seal["candidate_sha"] == EXPECTED_CANDIDATE
    assert seal["candidate_tree_sha"] == EXPECTED_TREE
    assert policy["target_sha"] == EXPECTED_BASE
    assert _sha256(policy_data) == seal["integration_policy"]["sha256"]

    head = str(_git(root, "rev-parse", "HEAD"))
    tree = str(_git(root, "rev-parse", "HEAD^{tree}"))
    target = str(_git(root, "rev-parse", f"{seal['target_ref']}^{{commit}}"))
    merge_base = str(_git(root, "merge-base", EXPECTED_BASE, EXPECTED_CANDIDATE))
    assert head == EXPECTED_CANDIDATE
    assert tree == EXPECTED_TREE
    assert target == EXPECTED_BASE
    assert merge_base == EXPECTED_BASE
    assert _git(root, "status", "--porcelain=v1") == ""

    commits = str(
        _git(root, "rev-list", "--reverse", f"{EXPECTED_BASE}..{EXPECTED_CANDIDATE}")
    ).splitlines()
    assert commits == seal["candidate_commits"]
    assert _sha256(_canonical({"commits": commits})) == seal[
        "candidate_commits_sha256"
    ]

    patch_rows = [
        {"commit": commit, "stable_patch_id": _stable_patch_id(root, commit)}
        for commit in commits
    ]
    patch_ids = [row["stable_patch_id"] for row in patch_rows]
    assert patch_rows == seal["stable_patch_ids"]
    assert len(patch_ids) == len(set(patch_ids)) == 7
    assert not set(patch_ids) & _base_patch_ids(root, EXPECTED_BASE)
    assert _sha256(_canonical({"stable_patch_ids": patch_rows})) == seal[
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
        f"{EXPECTED_BASE}..{EXPECTED_CANDIDATE}",
        binary=True,
    )
    assert isinstance(diff, bytes)
    assert _sha256(diff) == seal["diff_sha256"]
    changed_files = _changed_files(root, EXPECTED_BASE, EXPECTED_CANDIDATE)
    assert changed_files == seal["changed_files"]
    assert _sha256(_canonical({"changed_files": changed_files})) == seal[
        "changed_files_sha256"
    ]

    receipt_for_hash = dict(receipt)
    receipt_hash = receipt_for_hash.pop("receipt_content_sha256")
    assert receipt_hash == EXPECTED_RECEIPT_CONTENT
    assert _sha256(_canonical(receipt_for_hash, ensure_ascii=True)) == receipt_hash
    source_hashes = {
        row["path"]: _sha256((root / row["path"]).read_bytes())
        for row in receipt["source_bindings"]
    }
    assert source_hashes == {
        row["path"]: row["sha256"] for row in receipt["source_bindings"]
    }
    required_bindings = spec["receipt_contract"]["required_bindings"]
    assert list(source_hashes) == required_bindings

    spec_mutations = spec["mutation_registry"]
    mutation_rows = receipt["mutations"]
    assert [row["mutation_id"] for row in mutation_rows] == list(
        EXPECTED_MUTATION_IDS
    )
    assert [
        (row["mutation_id"], row["mutation_kind"]) for row in mutation_rows
    ] == [
        (row["mutation_id"], row["mutation_kind"]) for row in spec_mutations
    ]
    assert all(
        row["executed"] is True
        and row["activated"] is True
        and row["killed"] is True
        and row["observed_outcome"]
        == "BLOCKED_DEPTH_PATH_CALIBRATION_CONTRACT"
        for row in mutation_rows
    )
    bypass = next(
        row
        for row in mutation_rows
        if row["mutation_id"] == "MU284-REPORT-BUILDER-BYPASS"
    )
    assert bypass["observed_reason"] == "CALLER_SUPPLIED_PROVED_REPORT_REJECTED"
    hostile_marker = _hostile_builder_replay(root)

    assert policy["ordinary_agent_push_forbidden"] is True
    assert policy["ordinary_agent_pr_mutation_forbidden"] is True
    assert policy["default_publication_mode"] == "unattended_external_publisher_only"
    assert policy["attended_publication"]["requires_current_turn_authorization"] is True
    assert policy["attended_publication"]["forbidden_actions"] == [
        "force_push",
        "approve",
        "merge",
        "ruleset_mutation",
    ]

    return {
        "schema": "PR284_R3_IDENTITY_REPLAY_ORACLE_V1",
        "run_id": RUN_ID,
        "assignment_id": ASSIGNMENT_ID,
        "started_at": started_at,
        "completed_at": _utc_now(),
        "status": "PASS",
        "checks": {
            "context_version": EXPECTED_CONTEXT_VERSION,
            "candidate_sha": head,
            "candidate_tree_sha": tree,
            "exact_predecessor_base_sha": merge_base,
            "target_tracking_ref_sha": target,
            "candidate_commit_count": len(commits),
            "unique_stable_patch_id_count": len(patch_ids),
            "stable_patch_ids_absent_from_predecessor_history": True,
            "diff_sha256": seal["diff_sha256"],
            "changed_files_sha256": seal["changed_files_sha256"],
            "receipt_content_sha256": receipt_hash,
            "receipt_binding_count": len(source_hashes),
            "mutation_count": len(mutation_rows),
            "all_mutations_executed_activated_killed": True,
            "strengthened_builder_bypass_marker": hostile_marker,
            "ordinary_agent_publication_forbidden": True,
            "review_authorizes_merge_or_publication": False,
        },
        "claim_boundary": {
            "claim_tier": receipt["claim_tier"],
            "claim_level": receipt["claim_level"],
            "transfer_source": receipt["transfer_source"],
            "observed_data_executed": receipt["observed_data_executed"],
            "public_use": receipt["public_use"],
            "family_identification_gate": receipt["family_identification_gate"],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[5]
    output = root / args.output
    allowed_parent = Path(__file__).resolve().parent
    if output.parent.resolve() != allowed_parent or output.is_symlink():
        raise SystemExit("output must be a regular assignment-local artifact")
    evidence = _build_evidence(root)
    payload = (json.dumps(evidence, indent=2, sort_keys=True) + "\n").encode("utf-8")
    with tempfile.NamedTemporaryFile(
        mode="wb", dir=output.parent, prefix=f".{output.name}.", delete=False
    ) as handle:
        temporary = Path(handle.name)
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, output)
    print(f"PR284_R3_REPLAY_ORACLE_PASS {_sha256(payload)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
