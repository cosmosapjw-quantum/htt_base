#!/usr/bin/env python3
"""Assignment-local executable oracle for the frozen PR-284 candidate."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Callable

import yaml


ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "pr284-candidate-review-20260810"
ASSIGNMENT_ID = "A-PR284-REPLAY"
ARTIFACTS = Path(__file__).resolve().parent
OUTPUT = ARTIFACTS / "oracle.json"


def _canonical_sha256(value: object, *, omit: set[str] | None = None) -> str:
    if omit and isinstance(value, dict):
        value = {key: item for key, item in value.items() if key not in omit}
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _git(*argv: str, input_bytes: bytes | None = None) -> bytes:
    completed = subprocess.run(
        ["git", *argv],
        cwd=ROOT,
        input=input_bytes,
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"git {' '.join(argv)} failed ({completed.returncode}): "
            f"{completed.stderr.decode('utf-8', errors='replace')}"
        )
    return completed.stdout


def _record(checks: list[dict[str, Any]], name: str, fn: Callable[[], Any]) -> None:
    evidence = fn()
    checks.append({"check": name, "status": "PASS", "evidence": evidence})


def _candidate_identity() -> dict[str, Any]:
    seal = json.loads((ROOT / ".prguard/runtime/PR284_CANDIDATE_SEAL.json").read_text())
    head = _git("rev-parse", "HEAD").decode().strip()
    tree = _git("rev-parse", "HEAD^{tree}").decode().strip()
    target = _git("rev-parse", seal["target_ref"]).decode().strip()
    merge_base = _git("merge-base", seal["target_ref"], head).decode().strip()
    assert head == seal["candidate_sha"]
    assert tree == seal["candidate_tree_sha"]
    assert target == seal["base_sha"] == seal["merge_base_sha"]
    assert merge_base == seal["merge_base_sha"]
    assert subprocess.run(["git", "diff", "--quiet"], cwd=ROOT).returncode == 0
    assert subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode == 0
    return {
        "candidate_sha": head,
        "candidate_tree_sha": tree,
        "target_ref": seal["target_ref"],
        "target_sha": target,
        "merge_base_sha": merge_base,
        "tracked_index_and_worktree_clean": True,
    }


def _stable_patch_id_uniqueness() -> dict[str, Any]:
    seal = json.loads((ROOT / ".prguard/runtime/PR284_CANDIDATE_SEAL.json").read_text())
    expected = {
        row["stable_patch_id"]: row["commit"] for row in seal["stable_patch_ids"]
    }
    history = _git(
        "log",
        "-p",
        "--no-ext-diff",
        "--all",
        "--no-merges",
        "--pretty=format:commit %H",
    )
    completed = subprocess.run(
        ["git", "patch-id", "--stable"],
        cwd=ROOT,
        input=history,
        check=False,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr.decode(errors="replace")
    matches: dict[str, list[str]] = {patch_id: [] for patch_id in expected}
    for line in completed.stdout.decode().splitlines():
        patch_id, commit = line.split()
        if patch_id in matches:
            matches[patch_id].append(commit)
    assert matches == {patch_id: [commit] for patch_id, commit in expected.items()}
    assert len(set(expected)) == len(seal["candidate_commits"])
    assert set(expected.values()) == set(seal["candidate_commits"])
    return {
        "sealed_stable_patch_ids": expected,
        "all_ref_matches": matches,
        "unique_across_all_refs": True,
    }


def _receipt_and_mutations() -> dict[str, Any]:
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "htt/src"))
    sys.path.insert(0, str(ROOT / "htt"))
    from scripts.codex_harness import run_pr284_depth_path_doob as runner

    spec = yaml.safe_load(
        (ROOT / "docs/research_program/post_pr275/pr284_spec.yaml").read_text()
    )
    receipt = json.loads(
        (ROOT / "docs/generated/pr284_depth_path_doob_receipt.json").read_text()
    )
    receipt_digest = receipt["receipt_content_sha256"]
    assert receipt_digest == _canonical_sha256(
        receipt, omit={"receipt_content_sha256"}
    )
    expected_bindings = spec["receipt_contract"]["required_bindings"]
    assert [row["path"] for row in receipt["source_bindings"]] == expected_bindings
    for row in receipt["source_bindings"]:
        assert hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest() == row[
            "sha256"
        ]

    fresh_rows = runner._run_mutations()
    runner._validate_mutations(fresh_rows)
    assert len(fresh_rows) == 13
    assert fresh_rows == receipt["mutations"]
    assert [row["mutation_id"] for row in fresh_rows] == [
        row["mutation_id"] for row in spec["mutation_registry"]
    ]
    assert all(
        row["activated"] is True
        and row["executed"] is True
        and row["killed"] is True
        for row in fresh_rows
    )
    return {
        "receipt_content_sha256": receipt_digest,
        "source_binding_count": len(receipt["source_bindings"]),
        "fresh_mutation_count": len(fresh_rows),
        "fresh_mutation_ids": [row["mutation_id"] for row in fresh_rows],
        "all_fresh_mutations_activated_executed_killed": True,
    }


def _destination_defenses() -> dict[str, Any]:
    sys.path.insert(0, str(ROOT))
    from scripts.codex_harness import run_pr284_depth_path_doob as runner

    original_root = runner.ROOT
    original_output = runner.OUTPUT
    original_replace = runner.os.replace
    evidence: dict[str, Any] = {}
    try:
        with tempfile.TemporaryDirectory(prefix="pr284-review-oracle-") as raw:
            temp_root = Path(raw)
            generated = temp_root / "docs/generated"
            generated.mkdir(parents=True)
            runner.ROOT = temp_root

            outside = temp_root / "outside.json"
            outside.write_bytes(b"preserve-hardlink\n")
            hardlink = generated / "hardlink.json"
            hardlink.hardlink_to(outside)
            runner.OUTPUT = hardlink
            try:
                runner._validate_output_destination_for_write()
            except RuntimeError as exc:
                assert "single-link regular file" in str(exc)
                evidence["hardlink_rejection"] = str(exc)
            else:
                raise AssertionError("hardlinked destination was accepted")
            assert outside.read_bytes() == b"preserve-hardlink\n"

            fifo = generated / "fifo.json"
            os.mkfifo(fifo)
            runner.OUTPUT = fifo
            try:
                runner._validate_output_destination_for_write()
            except RuntimeError as exc:
                assert "single-link regular file" in str(exc)
                evidence["fifo_rejection"] = str(exc)
            else:
                raise AssertionError("FIFO destination was accepted")

            destination = generated / "receipt.json"
            destination.write_bytes(b"old\n")
            runner.OUTPUT = destination
            runner._validate_output_destination_for_write()
            runner._atomic_write(b"new\n")
            assert destination.read_bytes() == b"new\n"
            assert destination.stat().st_nlink == 1
            assert not tuple(generated.glob(f".{destination.name}.*"))
            evidence["atomic_replace_success"] = True

            def fail_replace(source: object, target: object) -> None:
                raise OSError("injected replace failure")

            runner.os.replace = fail_replace
            try:
                runner._atomic_write(b"must-not-land\n")
            except OSError as exc:
                assert "injected replace failure" in str(exc)
                evidence["atomic_replace_failure_injected"] = True
            else:
                raise AssertionError("injected atomic replace failure survived")
            assert destination.read_bytes() == b"new\n"
            assert not tuple(generated.glob(f".{destination.name}.*"))
            evidence["atomic_failure_preserved_original_and_cleaned_temp"] = True
    finally:
        runner.ROOT = original_root
        runner.OUTPUT = original_output
        runner.os.replace = original_replace
    return evidence


def _human_only_merge_refusal() -> dict[str, Any]:
    harness = ROOT / ".agent-harness/scripts"
    sys.path.insert(0, str(harness))
    import _harness
    from publication_integrity import PublicationIntegrityError, classify_publication_command

    status = yaml.safe_load((ROOT / "docs/codex_handoff/pr_status.yaml").read_text())
    policy = json.loads(
        (ROOT / "docs/research_program/post_pr275/pr284_publication_policy.json").read_text()
    )
    stack = status["stacked_pr_execution"]
    assert stack["execution_mode"] == "AUTO_STACKED_PR"
    assert stack["merge_policy"] == "HUMAN_ONLY"
    _harness.validate_execution_mode(stack["execution_mode"])
    try:
        _harness.validate_execution_mode("AUTO_MERGE")
    except PublicationIntegrityError as exc:
        rejection = str(exc)
    else:
        raise AssertionError("AUTO_MERGE execution mode was accepted")
    assert classify_publication_command("gh pr merge 380 --merge")[0] is True
    assert policy["ordinary_agent_pr_mutation_forbidden"] is True
    assert "merge" in policy["attended_publication"]["forbidden_actions"]
    return {
        "execution_mode": stack["execution_mode"],
        "merge_policy": stack["merge_policy"],
        "auto_merge_rejection": rejection,
        "merge_command_classified_forbidden": True,
        "attended_policy_forbids_merge": True,
    }


def main() -> int:
    ARTIFACTS.mkdir(parents=False, exist_ok=True)
    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    for name, check in (
        ("frozen_candidate_and_exact_pr283_target", _candidate_identity),
        ("stable_patch_id_uniqueness", _stable_patch_id_uniqueness),
        ("fresh_receipt_source_and_thirteen_mutations", _receipt_and_mutations),
        ("fifo_hardlink_and_atomic_write_defenses", _destination_defenses),
        ("human_only_merge_refusal", _human_only_merge_refusal),
    ):
        try:
            _record(checks, name, check)
        except BaseException as exc:
            errors.append(f"{name}: {type(exc).__name__}: {exc}")
            checks.append({"check": name, "status": "FAIL", "evidence": {}})
    payload = {
        "schema": "PR284_ASSIGNMENT_LOCAL_REPLAY_ORACLE_V1",
        "run_id": RUN_ID,
        "assignment_id": ASSIGNMENT_ID,
        "candidate_sha": _git("rev-parse", "HEAD").decode().strip(),
        "status": "PASS" if not errors else "FAIL",
        "checks": checks,
        "errors": errors,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
