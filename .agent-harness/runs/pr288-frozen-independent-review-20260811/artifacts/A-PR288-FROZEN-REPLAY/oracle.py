#!/usr/bin/env python3
"""Independent, read-only PR-288 lineage and containment oracle."""

from __future__ import annotations

from contextlib import redirect_stderr
from io import BytesIO, StringIO
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
from types import ModuleType

import yaml


ROOT = Path(__file__).resolve().parents[5]
OUTPUT = Path(__file__).with_name("oracle_evidence.json")
BASE = "319835cc4b4e2e3270a0b27787ce5d5a44ea16b7"
HEAD = "dcde762d1ce3027e01edcf2744398f7588bb5fb1"
TREE = "69d9f00aa1b8a43dfb9287ffbc9103f350fba80e"
SEAL_FILE_SHA256 = "cdde24653257c03c34fc94b2af1d58eff55f8aad4575bff07e8190c4d6a637fe"
AUDIT_BLOB = "9d312f3d3f5ebc6d2fa14e90a5de5edbd92ef0dd"
AUDIT_SHA256 = "c42b44641a7655edc36c11e23a747433275285a4f342a824fa69dda88bd6f436"
RECEIPT_SHA256 = "622dadbcdf4a5d616a78f485fd6a772d1c7823ed8d77e808aa2bfc8f66169b0c"
STATUS_SHA256 = "d0377f0bf3a945947ccc76157962703b478631e17843e951d780714eff42c5b6"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(*args: str, input_bytes: bytes | None = None) -> bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        input=input_bytes,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise AssertionError(
            f"git {' '.join(args)} failed: {completed.stderr.decode(errors='replace')}"
        )
    return completed.stdout


def stable_patch_id(commit: str, paths: tuple[str, ...] = ()) -> str:
    if paths:
        patch = git("diff", f"{commit}^", commit, "--", *paths)
    else:
        patch = git("show", commit, "--pretty=format:")
    completed = subprocess.run(
        ["git", "patch-id", "--stable"],
        cwd=ROOT,
        input=patch,
        capture_output=True,
        check=False,
    )
    if completed.returncode or not completed.stdout:
        raise AssertionError(f"stable patch-id failed for {commit}")
    return completed.stdout.decode("ascii").split()[0]


def load_runner():
    path = ROOT / "scripts/codex_harness/run_pr288_bayesian_semantics.py"
    spec = importlib.util.spec_from_file_location("pr288_independent_runner", path)
    if spec is None or spec.loader is None:
        raise AssertionError("runner import specification unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def lineage_checks() -> dict[str, object]:
    assert git("rev-parse", "HEAD").decode().strip() == HEAD
    assert git("rev-parse", "HEAD^{tree}").decode().strip() == TREE
    assert git("merge-base", BASE, HEAD).decode().strip() == BASE
    assert git(
        "rev-parse",
        "refs/remotes/origin/changeset/pr287-entropy-truth-recovery-20260811",
    ).decode().strip() == BASE
    assert not git("status", "--porcelain=v1")

    seal_path = ROOT / ".prguard/runtime/PR288_VALIDATED_CANDIDATE_SEAL.json"
    seal_data = seal_path.read_bytes()
    assert sha256(seal_data) == SEAL_FILE_SHA256
    seal = json.loads(seal_data)
    assert seal["base_sha"] == BASE
    assert seal["merge_base_sha"] == BASE
    assert seal["candidate_sha"] == HEAD
    assert seal["candidate_tree_sha"] == TREE

    audit = git("cat-file", "blob", AUDIT_BLOB)
    assert sha256(audit) == AUDIT_SHA256
    decoded_audit = audit.decode("utf-8")
    assert "include G41,G43,G44; drop G39,G40,G42" in decoded_audit
    assert seal["production_hash"] == (
        "7d2ce119e4f176aacaa870f0c7bc0dc1e5e0aa843bf2984f6ac7af7d4d148a79"
    )

    candidate_commits = git(
        "rev-list", "--reverse", "--no-merges", f"{BASE}..{HEAD}"
    ).decode().splitlines()
    candidate_ids = {commit: stable_patch_id(commit) for commit in candidate_commits}
    assert len(candidate_commits) == 8
    assert len(set(candidate_ids.values())) == len(candidate_ids)
    assert candidate_ids["35def97004dde564c7aa8704f72f58b84c75dfe3"] == (
        stable_patch_id("97aad7dc06a8cb63864304e5cada994ece0b87c8")
    )
    assert candidate_ids["5b8869f28744db93fd0c88ff391ce7bf4c784d86"] == (
        stable_patch_id("051d35a4bed094aca1fae84d96711b2255a3c033")
    )
    production_test_paths = (
        "htt/htt/htt/infer/bayesian_semantics.py",
        "tests/htt/test_bayesian_semantics_repair.py",
    )
    g44_core_id = stable_patch_id(
        "eb6bc1b0f8ec9fb8587d6ed1e94b4e8805682802",
        production_test_paths,
    )
    assert stable_patch_id(
        "5fe66791c42b682e5a0d3b869fa420847cca287e",
        production_test_paths,
    ) == g44_core_id

    excluded = {
        "G39": stable_patch_id("44091dea7341e96cbf152b1e42d072de977f8522"),
        "G40": stable_patch_id("a757eeee6c97e532a740a67909703d5ad394ab4a"),
        "G42": stable_patch_id("c2037e8ae1163db0f57b36355da24cf20ceea320"),
    }
    assert set(excluded.values()).isdisjoint(candidate_ids.values())
    return {
        "base_sha": BASE,
        "candidate_sha": HEAD,
        "candidate_tree_sha": TREE,
        "latest_target_sha": BASE,
        "candidate_patch_ids": candidate_ids,
        "candidate_patch_ids_unique": True,
        "included_groups": {
            "G41": candidate_ids["35def97004dde564c7aa8704f72f58b84c75dfe3"],
            "G43": candidate_ids["5b8869f28744db93fd0c88ff391ce7bf4c784d86"],
            "G44_production_test_subset": g44_core_id,
        },
        "excluded_group_patch_ids": excluded,
        "audit_blob": AUDIT_BLOB,
        "audit_sha256": AUDIT_SHA256,
    }


def preloaded_module_check(runner) -> dict[str, object]:
    module_name = "htt.infer.bayesian_semantics"
    fake = ModuleType(module_name)
    calls: list[str] = []

    def forbidden(*args, **kwargs):
        del args, kwargs
        calls.append("executed")
        raise AssertionError("preloaded hostile module executed")

    fake.build_bayesian_semantics_receipt = forbidden
    fake.validate_bayesian_semantics_receipt = forbidden
    previous = sys.modules.get(module_name)
    sys.modules[module_name] = fake
    try:
        loaded = runner._load_bound_bayesian_module(ROOT)
        expected = (ROOT / "htt/htt/htt/infer/bayesian_semantics.py").resolve()
        assert loaded is not fake
        assert Path(loaded.__file__).resolve() == expected
        assert not calls
        assert loaded.build_bayesian_semantics_receipt.__module__ == module_name
        assert loaded.validate_bayesian_semantics_receipt.__module__ == module_name
    finally:
        if previous is None:
            sys.modules.pop(module_name, None)
        else:
            sys.modules[module_name] = previous
    return {
        "hostile_preload_executed": False,
        "loaded_origin": str(expected.relative_to(ROOT)),
        "status": "PASS_BOUND_SOURCE_REPLACED_HOSTILE_PRELOAD",
    }


def make_archive(name: str, kind: bytes = tarfile.REGTYPE) -> BytesIO:
    stream = BytesIO()
    with tarfile.open(fileobj=stream, mode="w") as archive:
        info = tarfile.TarInfo(name)
        info.type = kind
        if kind == tarfile.REGTYPE:
            payload = b"candidate-bound"
            info.size = len(payload)
            archive.addfile(info, BytesIO(payload))
        else:
            info.linkname = "../outside"
            archive.addfile(info)
    stream.seek(0)
    return stream


def archive_checks(runner) -> dict[str, object]:
    hostile = [
        ("../escape", tarfile.REGTYPE),
        ("/absolute", tarfile.REGTYPE),
        ("nested/../../escape", tarfile.REGTYPE),
        ("link", tarfile.SYMTYPE),
        ("hard", tarfile.LNKTYPE),
        ("fifo", tarfile.FIFOTYPE),
    ]
    with tempfile.TemporaryDirectory(prefix="pr288-oracle-archive-") as raw:
        root = Path(raw)
        safe = root / "safe"
        safe.mkdir()
        stream = make_archive("nested/value.txt")
        with tarfile.open(fileobj=stream, mode="r:") as archive:
            runner._safe_extract_archive(archive, safe)
        assert (safe / "nested/value.txt").read_bytes() == b"candidate-bound"

        rejected: list[str] = []
        for index, (name, kind) in enumerate(hostile):
            destination = root / f"hostile-{index}"
            destination.mkdir()
            stream = make_archive(name, kind)
            with tarfile.open(fileobj=stream, mode="r:") as archive:
                try:
                    runner._safe_extract_archive(archive, destination)
                except RuntimeError as exc:
                    assert "unsafe archive member" in str(exc)
                    rejected.append(f"{name}:{kind.decode('ascii')}")
                else:
                    raise AssertionError(f"hostile archive accepted: {name}")

        outside = root / "outside"
        outside.mkdir()
        linked = root / "preexisting-link"
        linked.mkdir()
        (linked / "hop").symlink_to(outside, target_is_directory=True)
        stream = make_archive("hop/escape.txt")
        with tarfile.open(fileobj=stream, mode="r:") as archive:
            try:
                runner._safe_extract_archive(archive, linked)
            except RuntimeError:
                rejected.append("preexisting_destination_symlink")
            else:
                raise AssertionError("archive extraction followed destination symlink")
        assert not (outside / "escape.txt").exists()
    return {
        "safe_regular_member_extracted": True,
        "hostile_cases_rejected": rejected,
        "python310_compatible_call": "extractall_without_filter_keyword",
        "status": "PASS_SAFE_ARCHIVE_EXTRACTION",
    }


def atomic_destination_checks(runner) -> dict[str, object]:
    rejected: list[str] = []
    with tempfile.TemporaryDirectory(prefix="pr288-oracle-atomic-") as raw:
        root = Path(raw)
        generated = root / "docs/generated"
        generated.mkdir(parents=True)
        destination = generated / "receipt.json"
        original_root, original_output = runner.ROOT, runner.OUTPUT
        runner.ROOT, runner.OUTPUT = root, destination
        try:
            outside = root / "outside.json"
            outside.write_bytes(b"preserve")
            destination.hardlink_to(outside)
            try:
                runner._validate_output_destination_for_write()
            except RuntimeError:
                rejected.append("hardlinked_destination")
            else:
                raise AssertionError("hardlinked receipt destination accepted")
            destination.unlink()

            destination.symlink_to(outside)
            try:
                runner._validate_output_destination_for_write()
            except RuntimeError:
                rejected.append("symlink_destination")
            else:
                raise AssertionError("symlink receipt destination accepted")
            destination.unlink()

            generated.rmdir()
            external_dir = root / "external-dir"
            external_dir.mkdir()
            generated.symlink_to(external_dir, target_is_directory=True)
            try:
                runner._validate_output_destination_for_write()
            except RuntimeError:
                rejected.append("symlink_parent")
            else:
                raise AssertionError("symlink receipt parent accepted")
            generated.unlink()
            generated.mkdir()

            destination.write_bytes(b"old")
            real_replace = runner.os.replace

            def fail_replace(source, target):
                del source, target
                raise OSError("injected replace failure")

            runner.os.replace = fail_replace
            try:
                try:
                    runner._atomic_write_receipt(b"new")
                except OSError:
                    pass
                else:
                    raise AssertionError("injected replacement failure was hidden")
            finally:
                runner.os.replace = real_replace
            assert destination.read_bytes() == b"old"
            assert not list(generated.glob(".receipt.json.*"))

            runner._atomic_write_receipt(b"new")
            assert destination.read_bytes() == b"new"
            assert destination.stat().st_nlink == 1
            assert not list(generated.glob(".receipt.json.*"))
            assert outside.read_bytes() == b"preserve"
        finally:
            runner.ROOT, runner.OUTPUT = original_root, original_output
    return {
        "preflight_rejections": rejected,
        "failed_replace_preserved_destination": True,
        "failed_replace_removed_temporary": True,
        "successful_replace_single_link": True,
        "status": "PASS_ATOMIC_DESTINATION_DEFENSES",
    }


def receipt_and_status_checks(runner) -> dict[str, object]:
    receipt_path = ROOT / "docs/generated/pr288_bayesian_semantics_receipt.json"
    receipt_data = receipt_path.read_bytes()
    assert sha256(receipt_data) == RECEIPT_SHA256
    receipt = json.loads(receipt_data)
    assert receipt["terminal"] == "PASS_BAYESIAN_SEMANTICS_REPAIR"
    assert receipt["reasons"] == []
    dependency = receipt["dependency_receipt"]
    assert dependency["resolution"] == "COMPLETED_FAILED_WITH_RECEIPT"
    assert dependency["status"] == "PASS_REQUIRED_TERMINAL_RECEIPT"
    assert dependency["success_dependency_satisfied"] is False
    assert dependency["pr280_delta_sha256"] == sha256(
        (ROOT / "docs/PR_DELTAS/pr-280.md").read_bytes()
    )
    assert dependency["inventory_receipt_sha256"] == sha256(
        (
            ROOT
            / "docs/research_program/post_pr275/full_inventory_v4_receipt.json"
        ).read_bytes()
    )

    current_dependency = runner._load_bound_bayesian_module(
        ROOT
    )._load_pr280_dependency_receipt(ROOT)
    assert current_dependency == dependency

    canonical = ROOT / "docs/codex_handoff/pr_status.yaml"
    mirror = ROOT / "machine_readable/pr_status.yaml"
    canonical_data, mirror_data = canonical.read_bytes(), mirror.read_bytes()
    assert canonical_data == mirror_data
    assert sha256(canonical_data) == STATUS_SHA256
    status = yaml.safe_load(canonical_data)
    assert status["in_progress"] == "PR-288"
    pr288 = status["stacked_pr_execution"]["prs"]["PR-288"]
    pr289 = status["stacked_pr_execution"]["prs"]["PR-289"]
    assert pr288["lifecycle"] == "VALIDATED"
    assert pr288["gate_dispositions"]["review"] == "DEFERRED"
    assert pr289["lifecycle"] == "PLANNED"
    assert pr289["predecessor_sealed_sha"] is None
    assert pr289["gate_dispositions"] == {"eligibility": "INELIGIBLE"}
    assert pr289["assurance_budget"]["consumed"] == 0
    return {
        "receipt_sha256": RECEIPT_SHA256,
        "receipt_content_id": receipt["receipt_content_id"],
        "pr280_resolution": dependency["resolution"],
        "pr280_success_dependency_satisfied": False,
        "status_mirrors_byte_identical": True,
        "pr288_lifecycle": "VALIDATED",
        "pr288_review": "DEFERRED",
        "pr289_eligibility": "INELIGIBLE",
        "status": "PASS_RECEIPT_STATUS_BINDINGS",
    }


def main() -> int:
    runner = load_runner()
    evidence = {
        "schema": "PR288_FROZEN_REPLAY_ORACLE_V1",
        "python": sys.version.split()[0],
        "checks": {
            "lineage": lineage_checks(),
            "preloaded_module": preloaded_module_check(runner),
            "archive_extraction": archive_checks(runner),
            "atomic_destination": atomic_destination_checks(runner),
            "receipt_and_status": receipt_and_status_checks(runner),
        },
        "terminal": "PASS_PR288_FROZEN_REPLAY_ORACLE",
    }
    encoded = (
        json.dumps(evidence, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    temporary = OUTPUT.with_suffix(".tmp")
    temporary.write_bytes(encoded)
    os.replace(temporary, OUTPUT)
    print(json.dumps({"terminal": evidence["terminal"], "output": str(OUTPUT)}))
    return 0


if __name__ == "__main__":
    with redirect_stderr(StringIO()):
        raise SystemExit(main())
