#!/usr/bin/env python3
"""Independent PR-284 R4 proper-subset, identity, and receipt oracle."""

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


RUN_ID = "pr284-proper-subset-r4-20260810"
ASSIGNMENT_ID = "A-PR284-R4-REPLAY"
CONTEXT_VERSION = (
    "e9b385d7fbc4f8e47c97c3b0c7edae4e522d9be4e025d9342e26ab24829e3019"
)
SEAL_FILE_SHA256 = (
    "93c3dadced3fec69db081092e66f96eac5632b4713f652642d470cc2f6fdacd4"
)
BASE_SHA = "b6b6952d52f59bbe05477ef3b02292a98fe92baa"
CANDIDATE_SHA = "50fea58d2bd4d33dfac017f46bf22df5ccd289d1"
CANDIDATE_TREE = "6104ff701c82c78b113002131dec3bd493a54795"
RECEIPT_CONTENT_SHA256 = (
    "de87bc2f96d6133fb45149784f4d081f24525d61a8c2dcc46f9e018fbdee6b5e"
)
MUTATION_IDS = (
    "MU284-SUPPORT-NESTING-AS-PROOF",
    "MU284-NONNESTED-SUPPORT",
    "MU284-NONSTRICT-SUPPORT",
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


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(value: object, *, ensure_ascii: bool = False) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=ensure_ascii,
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
    value = subprocess.run(
        ["git", "patch-id", "--stable"],
        cwd=root,
        input=shown,
        check=True,
        capture_output=True,
    ).stdout.decode("ascii").strip()
    if not value:
        raise AssertionError(f"no stable patch ID for {commit}")
    return value.split()[0]


def _base_patch_ids(root: Path) -> set[str]:
    history = subprocess.run(
        [
            "git",
            "log",
            "--no-merges",
            "--pretty=format:commit %H",
            "-p",
            BASE_SHA,
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


def _changed_files(root: Path) -> list[dict[str, str]]:
    raw = _git(
        root,
        "diff",
        "--name-status",
        "--no-renames",
        "-z",
        f"{BASE_SHA}..{CANDIDATE_SHA}",
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


def _proper_subset_discriminator(root: Path) -> dict[str, object]:
    for entry in (root, root / "htt/src", root / "htt"):
        text = str(entry)
        if text not in sys.path:
            sys.path.insert(0, text)

    from common.depth_path import DepthPathError, revalidate_depth_path
    from htt.infer.depth_path_calibration import (
        build_depth_path_doob_calibration,
        build_depth_path_reverse_martingale_report,
        build_unproved_depth_path_reverse_martingale_report,
    )
    from scripts.codex_harness import run_pr284_depth_path_doob as fixtures

    path = fixtures._equal_support_path()
    replayed_path = revalidate_depth_path(path)
    source = set(replayed_path.strata[0].support_unit_ids)
    equal_target = set(replayed_path.strata[1].support_unit_ids)
    if source != equal_target:
        raise AssertionError("hostile path does not contain equal adjacent support")
    law = fixtures._law()
    threshold = fixtures._threshold()
    try:
        build_depth_path_reverse_martingale_report(
            report_id="A-PR284-R4-EQUAL-SUPPORT-PROVED",
            path=path,
            threshold_contract=threshold,
            finite_target_law=law,
            selection_contract=fixtures._selection(law),
            path_partitions=(
                ("a", "b", "c", "d"),
                ("left", "left", "right", "right"),
                ("all", "all", "all", "all"),
            ),
            sigma_field_ids=("sha256:F1", "sha256:F2", "sha256:F3"),
            filtration_id="sha256:decreasing-filtration-v1",
            preprocessing_id="sha256:common-preprocessing-v1",
            estimator_id="sha256:conditional-estimator-v1",
            premise_evidence_id="sha256:pr271-finite-tower-v1",
        )
    except DepthPathError as exc:
        marker = "proved report requires strictly nested sky supports"
        if marker not in str(exc):
            raise AssertionError(f"proved path failed at wrong boundary: {exc}")
    else:
        raise AssertionError("equal-support path minted a proved report")

    plan = fixtures._mock_plan(path, threshold)
    unproved = build_unproved_depth_path_reverse_martingale_report(
        report_id="A-PR284-R4-EQUAL-SUPPORT-UNPROVED",
        path=path,
        threshold_contract=threshold,
        filtration_id="sha256:equal-support-unproved",
        preprocessing_id="sha256:common-preprocessing-v1",
        estimator_id="sha256:conditional-estimator-v1",
        premise_evidence_id="sha256:strict-nesting-unproved",
        unresolved_reasons=("proper support reduction is unproved",),
        matched_mock_plan=plan,
    )
    fallback = build_depth_path_doob_calibration(
        calibration_id="A-PR284-R4-EQUAL-SUPPORT-FALLBACK",
        report=unproved,
        threshold_contract=threshold,
    )
    if fallback.probability_upper_bound is not None:
        raise AssertionError("unproved equal-support path emitted a probability bound")
    if fallback.status.value != "MATCHED_MOCKS_REQUIRED":
        raise AssertionError("unproved equal-support path did not require matched mocks")
    return {
        "generic_depth_path_accepts_equal_support": True,
        "proved_report_rejection_marker": marker,
        "unproved_status": fallback.status.value,
        "unproved_probability_bound": fallback.probability_upper_bound,
        "matched_mock_plan_content_id": fallback.matched_mock_plan_content_id,
    }


def _build(root: Path) -> dict[str, Any]:
    started = _now()
    seal_data, seal = _json(root, ".prguard/runtime/PR284_R4_CANDIDATE_SEAL.json")
    policy_data, policy = _json(
        root, "docs/research_program/post_pr275/pr284_publication_policy.json"
    )
    _, receipt = _json(root, "docs/generated/pr284_depth_path_doob_receipt.json")
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

    assert index["context_version"] == CONTEXT_VERSION
    assert _sha(seal_data) == SEAL_FILE_SHA256
    seal_payload = {key: value for key, value in seal.items() if key != "seal_sha256"}
    assert _sha(_canonical(seal_payload)) == seal["seal_sha256"]
    assert seal["base_sha"] == seal["merge_base_sha"] == BASE_SHA
    assert seal["candidate_sha"] == CANDIDATE_SHA
    assert seal["candidate_tree_sha"] == CANDIDATE_TREE
    assert policy["target_sha"] == BASE_SHA
    assert _sha(policy_data) == seal["integration_policy"]["sha256"]

    head = str(_git(root, "rev-parse", "HEAD"))
    tree = str(_git(root, "rev-parse", "HEAD^{tree}"))
    target = str(_git(root, "rev-parse", f"{seal['target_ref']}^{{commit}}"))
    merge_base = str(_git(root, "merge-base", BASE_SHA, CANDIDATE_SHA))
    assert head == CANDIDATE_SHA
    assert tree == CANDIDATE_TREE
    assert target == merge_base == BASE_SHA
    assert _git(root, "status", "--porcelain=v1") == ""

    commits = str(
        _git(root, "rev-list", "--reverse", f"{BASE_SHA}..{CANDIDATE_SHA}")
    ).splitlines()
    assert commits == seal["candidate_commits"]
    assert _sha(_canonical({"commits": commits})) == seal["candidate_commits_sha256"]
    patch_rows = [
        {"commit": commit, "stable_patch_id": _patch_id(root, commit)}
        for commit in commits
    ]
    patch_ids = [row["stable_patch_id"] for row in patch_rows]
    assert patch_rows == seal["stable_patch_ids"]
    assert len(patch_ids) == len(set(patch_ids)) == 10
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
        f"{BASE_SHA}..{CANDIDATE_SHA}",
        binary=True,
    )
    assert isinstance(diff, bytes) and _sha(diff) == seal["diff_sha256"]
    changed = _changed_files(root)
    assert changed == seal["changed_files"]
    assert _sha(_canonical({"changed_files": changed})) == seal[
        "changed_files_sha256"
    ]

    receipt_payload = dict(receipt)
    content_hash = receipt_payload.pop("receipt_content_sha256")
    assert content_hash == RECEIPT_CONTENT_SHA256
    assert _sha(_canonical(receipt_payload, ensure_ascii=True)) == content_hash
    source_hashes = {
        row["path"]: _sha((root / row["path"]).read_bytes())
        for row in receipt["source_bindings"]
    }
    assert source_hashes == {
        row["path"]: row["sha256"] for row in receipt["source_bindings"]
    }
    assert list(source_hashes) == spec["receipt_contract"]["required_bindings"]

    mutations = receipt["mutations"]
    spec_mutations = spec["mutation_registry"]
    assert [row["mutation_id"] for row in mutations] == list(MUTATION_IDS)
    assert [
        (row["mutation_id"], row["mutation_kind"]) for row in mutations
    ] == [
        (row["mutation_id"], row["mutation_kind"]) for row in spec_mutations
    ]
    assert all(
        row["executed"] is True
        and row["activated"] is True
        and row["killed"] is True
        and row["observed_outcome"]
        == "BLOCKED_DEPTH_PATH_CALIBRATION_CONTRACT"
        for row in mutations
    )
    nonstrict = mutations[2]
    assert nonstrict["mutation_id"] == "MU284-NONSTRICT-SUPPORT"
    assert nonstrict["observed_reason"] == "NONSTRICT_SUPPORT_REJECTED"
    discriminator = _proper_subset_discriminator(root)

    assert policy["ordinary_agent_push_forbidden"] is True
    assert policy["ordinary_agent_pr_mutation_forbidden"] is True
    assert policy["default_publication_mode"] == "unattended_external_publisher_only"
    assert policy["attended_publication"]["requires_current_turn_authorization"] is True
    assert "merge" in policy["attended_publication"]["forbidden_actions"]

    return {
        "schema": "PR284_R4_PROPER_SUBSET_REPLAY_ORACLE_V1",
        "run_id": RUN_ID,
        "assignment_id": ASSIGNMENT_ID,
        "started_at": started,
        "completed_at": _now(),
        "status": "PASS",
        "checks": {
            "context_version": CONTEXT_VERSION,
            "candidate_sha": head,
            "candidate_tree_sha": tree,
            "exact_predecessor_base_sha": merge_base,
            "target_tracking_ref_sha": target,
            "candidate_commit_count": len(commits),
            "unique_stable_patch_id_count": len(patch_ids),
            "stable_patch_ids_absent_from_predecessor_history": True,
            "diff_sha256": seal["diff_sha256"],
            "changed_files_sha256": seal["changed_files_sha256"],
            "receipt_content_sha256": content_hash,
            "receipt_binding_count": len(source_hashes),
            "mutation_count": len(mutations),
            "all_mutations_executed_activated_killed": True,
            "proper_subset_discriminator": discriminator,
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
    print(f"PR284_R4_PROPER_SUBSET_ORACLE_PASS {_sha(payload)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
