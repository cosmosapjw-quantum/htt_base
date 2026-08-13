#!/usr/bin/env python3
"""Independent frozen-replay oracle for assignment A-PR286-FROZEN-REPLAY."""

from __future__ import annotations

from contextlib import redirect_stdout
from datetime import datetime, timezone
import hashlib
import importlib.util
from io import BytesIO, StringIO
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
from unittest import mock

import yaml


ROOT = Path(__file__).resolve().parents[4]
RUN_ID = "pr286-candidate-review-20260810"
ASSIGNMENT_ID = "A-PR286-FROZEN-REPLAY"
ARTIFACT_DIR = ROOT / ".agent-harness" / "runs" / RUN_ID / "artifacts"
OUTPUT = ARTIFACT_DIR / f"{ASSIGNMENT_ID}-oracle-output.json"
BASE = "16bc6db511b8b7228e5c4dcb95c65074fe519f24"
CANDIDATE = "f2fb069d4ac5bdcd18564839ffa236bd242ca115"
TARGET_REF = "refs/remotes/origin/changeset/pr285-pillar-t-adjudication-recovery-20260810"
EXPECTED_AUDIT_SHA256 = "c42b44641a7655edc36c11e23a747433275285a4f342a824fa69dda88bd6f436"
AUDIT = Path(
    "/home/cosmosapjw/Dropbox/bianchi/htt_base/"
    "HTT_PROCESS_INFLATION_SALVAGE_AUDIT_20260810.md"
)
SEAL_PATH = ROOT / ".prguard/runtime/PR286_CANDIDATE_SEAL.json"
REHEARSAL_PATH = ROOT / ".prguard/runtime/PR286_CANDIDATE_INTEGRATION_REHEARSAL.json"
POLICY_PATH = ROOT / "docs/research_program/post_pr275/pr286_publication_policy.json"
SPEC_PATH = ROOT / "docs/research_program/post_pr275/pr286_spec.yaml"
RECEIPT_PATH = ROOT / (
    "docs/research_program/post_pr275/pillar_s_adjudication/"
    "PILLAR_S_COMPLETE_ADJUDICATION_V1.json"
)
RUNNER_PATH = ROOT / "scripts/codex_harness/run_pr286_pillar_s_adjudication.py"


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_file(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def canonical_digest(value: object) -> str:
    return digest_bytes(canonical_bytes(value))


def run(argv: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None) -> dict[str, object]:
    started = datetime.now(timezone.utc)
    completed = subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        capture_output=True,
        check=False,
    )
    ended = datetime.now(timezone.utc)
    return {
        "argv": argv,
        "returncode": completed.returncode,
        "timed_out": False,
        "started_at": started.isoformat(),
        "completed_at": ended.isoformat(),
        "stdout_sha256": digest_bytes(completed.stdout),
        "stdout_bytes": len(completed.stdout),
        "stderr_sha256": digest_bytes(completed.stderr),
        "stderr_bytes": len(completed.stderr),
    }


def git_bytes(*args: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, input=input_bytes
    )


def git_text(*args: str) -> str:
    return git_bytes(*args).decode("utf-8").strip()


def patch_id(commit: str) -> str:
    patch = git_bytes("show", "--pretty=format:", commit)
    value = git_bytes("patch-id", "--stable", input_bytes=patch).decode("ascii").split()
    if len(value) != 2:
        raise AssertionError(f"unexpected patch-id output for {commit}: {value}")
    return value[0]


def tracked_manifest(root: Path, tracked: list[str]) -> dict[str, object]:
    identities: dict[str, str] = {}
    for relative in tracked:
        path = root / relative
        if path.is_symlink() or not path.is_file():
            raise AssertionError(f"non-regular tracked member: {relative}")
        identities[relative] = digest_file(path)
    return {
        "file_count": len(identities),
        "manifest_sha256": canonical_digest(identities),
        "path_inventory_sha256": digest_bytes("\0".join(identities).encode()),
        "content_identity_inventory_sha256": digest_bytes(
            "\0".join(identities.values()).encode("ascii")
        ),
    }


def load_runner():
    spec = importlib.util.spec_from_file_location("pr286_frozen_oracle_runner", RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("runner import spec unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def assert_raises_marker(callable_obj, marker: str) -> None:
    try:
        callable_obj()
    except Exception as exc:  # oracle intentionally tests the public failure boundary
        if marker not in str(exc):
            raise AssertionError(f"expected {marker!r}, got {exc!r}") from exc
    else:
        raise AssertionError(f"expected failure marker {marker!r}")


def containment_and_atomic_checks() -> dict[str, object]:
    runner = load_runner()
    original_root = runner.ROOT
    original_output = runner.OUTPUT
    checks: list[str] = []
    try:
        with tempfile.TemporaryDirectory(prefix="pr286-oracle-containment-") as temporary:
            base = Path(temporary)
            root = base / "repo"
            outside = base / "outside"
            root.mkdir()
            outside.mkdir()
            runner.ROOT = root

            runner.OUTPUT = outside / "escaped.json"
            assert_raises_marker(
                runner._validate_output_destination_for_write,
                "OUTPUT_ESCAPES_REPOSITORY_ROOT",
            )
            checks.append("lexical_escape_rejected")

            (root / "generated-link").symlink_to(outside, target_is_directory=True)
            runner.OUTPUT = root / "generated-link" / "receipt.json"
            assert_raises_marker(
                runner._validate_output_destination_for_write,
                "OUTPUT_PARENT_NOT_REGULAR",
            )
            checks.append("symlink_parent_rejected")

            generated = root / "generated"
            generated.mkdir()
            external_file = outside / "external.json"
            external_file.write_bytes(b"preserve\n")
            hardlink = generated / "receipt.json"
            hardlink.hardlink_to(external_file)
            runner.OUTPUT = hardlink
            assert_raises_marker(
                runner._validate_output_destination_for_write,
                "OUTPUT_DESTINATION_NOT_SINGLE_LINK_FILE",
            )
            assert external_file.read_bytes() == b"preserve\n"
            checks.append("hardlink_destination_rejected_before_write")
            hardlink.unlink()

            destination = generated / "receipt.json"
            destination.write_bytes(b"old\n")
            runner.OUTPUT = destination
            runner._validate_output_destination_for_write()
            runner._atomic_write(b"new\n")
            assert destination.read_bytes() == b"new\n"
            assert destination.stat().st_nlink == 1
            assert not list(generated.glob(f".{destination.name}.*"))
            checks.append("same_directory_atomic_replace")

            destination.write_bytes(b"preserve-on-replace-error\n")
            with mock.patch.object(runner.os, "replace", side_effect=OSError("oracle replace failure")):
                try:
                    runner._atomic_write(b"must-not-land\n")
                except OSError:
                    pass
                else:
                    raise AssertionError("replace failure was not propagated")
            assert destination.read_bytes() == b"preserve-on-replace-error\n"
            assert not list(generated.glob(f".{destination.name}.*"))
            checks.append("replace_failure_preserves_destination_and_cleans_temp")
    finally:
        runner.ROOT = original_root
        runner.OUTPUT = original_output

    first = runner._serialized(runner.build_complete_adjudication_receipt())
    second = runner._serialized(runner.build_complete_adjudication_receipt())
    assert first == second == RECEIPT_PATH.read_bytes()
    return {
        "status": "PASS",
        "checks": checks,
        "deterministic_receipt_sha256": digest_bytes(first),
    }


def portable_archive_check() -> tuple[dict[str, object], dict[str, object]]:
    tracked = [
        item.decode("utf-8")
        for item in git_bytes("ls-files", "-z").split(b"\0")
        if item
    ]
    source_before = tracked_manifest(ROOT, tracked)
    archived = git_bytes("archive", "--format=tar", "HEAD")
    with tempfile.TemporaryDirectory(prefix="pr286-oracle-portable-") as temporary:
        clean_root = Path(temporary) / "source"
        clean_root.mkdir()
        with tarfile.open(fileobj=BytesIO(archived), mode="r:") as archive:
            archive.extractall(clean_root, filter="data")
        clean_before = tracked_manifest(clean_root, tracked)
        assert clean_before == source_before
        env = dict(os.environ)
        for key in (
            "PYTHONHOME",
            "PYTEST_ADDOPTS",
            "PYTEST_PLUGINS",
            "PYTHONSTARTUP",
            "PYTHONPATH",
        ):
            env.pop(key, None)
        env["PYTHONPATH"] = os.pathsep.join(
            (str(clean_root), str(clean_root / "htt/src"), str(clean_root / "htt"))
        )
        command = run(
            [
                sys.executable,
                "-B",
                "scripts/codex_harness/run_pr286_pillar_s_adjudication.py",
                "check",
            ],
            cwd=clean_root,
            env=env,
        )
        assert command["returncode"] == 0
        clean_after = tracked_manifest(clean_root, tracked)
        source_after = tracked_manifest(ROOT, tracked)
        assert clean_after == clean_before
        assert source_after == source_before
    return (
        {
            "status": "PASS",
            "tracked_manifest": source_before,
            "source_pre_equals_post": True,
            "clean_pre_equals_post": True,
            "source_root_differs_from_execution_root": True,
        },
        command,
    )


def main() -> int:
    started = datetime.now(timezone.utc)
    checks: dict[str, object] = {}

    context = json.loads((ROOT / ".agent-harness/context/CONTEXT_INDEX.json").read_text())
    assignment = json.loads(
        (ROOT / ".agent-harness/runs" / RUN_ID / "assignments" / f"{ASSIGNMENT_ID}.json").read_text()
    )
    assert context["context_version"] == assignment["context_version"]
    checks["context_binding"] = {
        "status": "PASS",
        "context_version": context["context_version"],
    }

    assert digest_file(AUDIT) == EXPECTED_AUDIT_SHA256
    checks["external_audit_identity"] = {
        "status": "PASS",
        "sha256": EXPECTED_AUDIT_SHA256,
    }

    seal = json.loads(SEAL_PATH.read_text())
    rehearsal = json.loads(REHEARSAL_PATH.read_text())
    policy = json.loads(POLICY_PATH.read_text())
    spec = yaml.safe_load(SPEC_PATH.read_text())
    receipt = json.loads(RECEIPT_PATH.read_text())

    assert digest_file(SEAL_PATH) == assignment["candidate_binding"]["seal_file_sha256"]
    seal_body = dict(seal)
    seal_digest = seal_body.pop("seal_sha256")
    assert canonical_digest(seal_body) == seal_digest == assignment["candidate_binding"]["seal_sha256"]
    assert seal["candidate_sha"] == git_text("rev-parse", "HEAD") == CANDIDATE
    assert seal["candidate_tree_sha"] == git_text("rev-parse", "HEAD^{tree}")
    assert seal["base_sha"] == seal["merge_base_sha"] == BASE
    assert git_text("show-ref", "--hash", TARGET_REF) == BASE
    assert git_text("merge-base", BASE, CANDIDATE) == BASE
    assert git_text("rev-parse", f"{seal['candidate_commits'][0]}^") == BASE
    assert git_text("rev-list", "--reverse", f"{BASE}..{CANDIDATE}").splitlines() == seal["candidate_commits"]
    checks["candidate_and_predecessor_identity"] = {
        "status": "PASS",
        "base_sha": BASE,
        "candidate_sha": CANDIDATE,
        "candidate_tree_sha": seal["candidate_tree_sha"],
        "linear_commit_count": len(seal["candidate_commits"]),
        "seal_sha256": seal_digest,
    }

    candidate_patch_ids = {item["commit"]: patch_id(item["commit"]) for item in seal["stable_patch_ids"]}
    assert [
        {"commit": commit, "stable_patch_id": candidate_patch_ids[commit]}
        for commit in seal["candidate_commits"]
    ] == seal["stable_patch_ids"]
    base_patch_stream = git_bytes("log", "-p", "--pretty=format:", BASE)
    base_patch_ids = {
        line.split()[0]
        for line in git_bytes("patch-id", "--stable", input_bytes=base_patch_stream).decode("ascii").splitlines()
        if line.strip()
    }
    assert set(candidate_patch_ids.values()).isdisjoint(base_patch_ids)
    assert patch_id("a8743973") == candidate_patch_ids["b3eb957ce71ee42c3c0692159ca4d624af5526c2"]
    assert patch_id("b2013b44") == candidate_patch_ids["eed8a0f5e05fa53b122f66556925870c97ac30c8"]
    assert patch_id("9ad9340b") not in set(candidate_patch_ids.values())
    assert patch_id("b8bc64ca") not in set(candidate_patch_ids.values())
    g27_paths = [
        "docs/research_program/post_pr275/pr286_spec.yaml",
        "scripts/codex_harness/run_pr286_pillar_s_adjudication.py",
        "tests/contracts/test_pillar_s_complete_adjudication.py",
    ]
    g27_original = git_bytes("diff", "77f9bad2^", "77f9bad2", "--", *g27_paths)
    g27_reconstruction = git_bytes(
        "diff",
        "b2b51e7102d8e3cbaa5b00de9bb5ceeb010d2f8d^",
        "b2b51e7102d8e3cbaa5b00de9bb5ceeb010d2f8d",
        "--",
        *g27_paths,
    )
    assert g27_original == g27_reconstruction
    assert git_text(
        "diff-tree",
        "--no-commit-id",
        "--name-only",
        "-r",
        "b2b51e7102d8e3cbaa5b00de9bb5ceeb010d2f8d",
    ).splitlines() == g27_paths
    checks["selective_salvage_and_patch_ids"] = {
        "status": "PASS",
        "g23_patch_id": patch_id("a8743973"),
        "g25_patch_id": patch_id("b2013b44"),
        "g27_narrow_diff_sha256": digest_bytes(g27_original),
        "g27_narrow_paths": g27_paths,
        "g24_patch_id_excluded": patch_id("9ad9340b"),
        "g26_patch_id_excluded": patch_id("b8bc64ca"),
        "candidate_patch_ids_unique_from_predecessor": True,
    }

    assert digest_file(REHEARSAL_PATH) == "78f13f54bebf60df6781fd8fec7576bb78e20075715e2783eed86bb469e46465"
    rehearsal_body = dict(rehearsal)
    rehearsal_digest = rehearsal_body.pop("receipt_sha256")
    assert canonical_digest(rehearsal_body) == rehearsal_digest
    assert rehearsal["status"] == "PASS"
    assert rehearsal["candidate_seal_sha256"] == seal_digest
    assert rehearsal["candidate_sha"] == CANDIDATE
    assert rehearsal["latest_target_sha"] == BASE
    assert rehearsal["merged_tree_sha"] == seal["candidate_tree_sha"]
    expected_commands = policy["required_commands"]
    assert [row["id"] for row in rehearsal["commands"]] == [row["id"] for row in expected_commands]
    for actual, expected in zip(rehearsal["commands"], expected_commands, strict=True):
        assert actual["policy_argv"] == expected["argv"]
        assert actual["timeout_seconds"] == expected["timeout_seconds"]
        assert actual["returncode"] == 0 and actual["timed_out"] is False
    checks["integration_rehearsal"] = {
        "status": "PASS",
        "receipt_sha256": rehearsal_digest,
        "ordered_command_count": len(rehearsal["commands"]),
        "latest_target_sha": rehearsal["latest_target_sha"],
        "merged_tree_sha": rehearsal["merged_tree_sha"],
    }

    rows = receipt["rows"]
    source_rows = [row for row in rows if row["source_group"] == "proposal_registry_rows"]
    vt_rows = [row for row in rows if row["source_group"] == "vector_tensor_successor"]
    assert len(rows) == 72 and len(source_rows) == 58 and len(vt_rows) == 14
    assert len({row["row_id"] for row in rows}) == 72
    bindings = receipt["source_bindings"]
    assert len(bindings) == len(receipt["source_binding_map"]) == 33
    assert receipt["source_binding_map"] == {row["path"]: row["sha256"] for row in bindings}
    for binding in bindings:
        assert digest_file(ROOT / binding["path"]) == binding["sha256"]
    mutable_orchestration = {
        "docs/codex_handoff/pr_backlog.yaml",
        "machine_readable/pr_backlog.yaml",
        "docs/codex_handoff/pr_backlog.json",
        "machine_readable/pr_backlog.json",
        "scripts/codex_harness/validate_pr_dag.py",
    }
    assert mutable_orchestration.isdisjoint(receipt["source_binding_map"])
    receipt_body = dict(receipt)
    receipt_content_digest = receipt_body.pop("receipt_content_sha256")
    assert canonical_digest(receipt_body) == receipt_content_digest
    checks["receipt_reconstruction"] = {
        "status": "PASS",
        "row_count": len(rows),
        "source_row_count": len(source_rows),
        "vector_tensor_row_count": len(vt_rows),
        "source_binding_count": len(bindings),
        "receipt_content_sha256": receipt_content_digest,
    }

    registry = spec["mutation_registry"]
    results = receipt["mutation_results"]
    assert len(registry) == len(results) == 18
    assert [row["mutation_id"] for row in registry] == [row["mutation_id"] for row in results]
    for result in results:
        assert result["executed"] is result["activated"] is result["killed"] is True
        assert result["survivor"] is False
        assert result["kill_marker"]
        assert result["evidence_fingerprint"] == canonical_digest(
            {"mutation_id": result["mutation_id"], "kill_marker": result["kill_marker"]}
        )
    checks["mutation_execution"] = {
        "status": "PASS",
        "ordered_kills": len(results),
        "mutation_ids": [row["mutation_id"] for row in results],
    }

    checks["containment_atomic_and_determinism"] = containment_and_atomic_checks()
    portable, portable_command = portable_archive_check()
    checks["portable_clean_replay"] = portable

    commands = [portable_command]
    for argv in (
        [sys.executable, "-B", "scripts/codex_harness/build_pr271_pillar_s_core.py", "--check"],
        [sys.executable, "-B", "scripts/codex_harness/build_pr272_pillar_s_inference.py", "--check"],
        [sys.executable, "-B", "scripts/codex_harness/build_pr273_blind_synthetic.py", "--check"],
        [
            sys.executable,
            "-B",
            "scripts/codex_harness/validate_pr_dag.py",
            "docs/codex_handoff/pr_backlog.yaml",
            "--status",
            "docs/codex_handoff/pr_status.yaml",
            "--strict-rescue-slice",
        ],
    ):
        command = run(argv)
        assert command["returncode"] == 0
        commands.append(command)
    checks["predecessor_and_dag_replays"] = {
        "status": "PASS",
        "command_count": 4,
        "all_returncodes_zero": True,
        "pr287_consumer": receipt["future_consumer_contract"]["consumer"],
        "pr287_success_semantics": receipt["future_consumer_contract"]["upstream_success_semantics"],
    }

    assert all(value["status"] == "PASS" for value in checks.values())
    payload = {
        "schema_version": 1,
        "oracle_id": "PR286-FROZEN-REPLAY-INDEPENDENT-ORACLE",
        "run_id": RUN_ID,
        "assignment_id": ASSIGNMENT_ID,
        "started_at": started.isoformat(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "status": "PASS",
        "checks": checks,
        "commands": commands,
    }
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    OUTPUT.write_text(encoded, encoding="utf-8")
    print(json.dumps({"ok": True, "output": OUTPUT.relative_to(ROOT).as_posix()}))
    return 0


if __name__ == "__main__":
    with redirect_stdout(StringIO()) as captured:
        exit_code = main()
    sys.stdout.write(captured.getvalue())
    raise SystemExit(exit_code)
