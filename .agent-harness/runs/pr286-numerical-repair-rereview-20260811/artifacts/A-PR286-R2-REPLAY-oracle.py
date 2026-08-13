#!/usr/bin/env python3
"""Independent bounded replay oracle for A-PR286-R2-REPLAY."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

import yaml


ROOT = Path(__file__).resolve().parents[4]
RUN_ID = "pr286-numerical-repair-rereview-20260811"
ASSIGNMENT_ID = "A-PR286-R2-REPLAY"
CONTEXT_VERSION = "e9b385d7fbc4f8e47c97c3b0c7edae4e522d9be4e025d9342e26ab24829e3019"
BASE_SHA = "16bc6db511b8b7228e5c4dcb95c65074fe519f24"
CANDIDATE_SHA = "7ad8176282554670909c28306b3e14e83662a42b"
CANDIDATE_TREE = "d14eedaa79f902f5b47b507fa3951e5a22cbe9b7"
IMPLEMENTATION_SHA = "723c374916fcb39965b7e00d9ef47176e28799e6"
REPAIR_PATCH_ID = "ad98e164e3b5f8201a05fa6a118fc24203dfd4f0"
AUDIT = Path(
    "/home/cosmosapjw/Dropbox/bianchi/htt_base/"
    "HTT_PROCESS_INFLATION_SALVAGE_AUDIT_20260810.md"
)
AUDIT_SHA256 = "c42b44641a7655edc36c11e23a747433275285a4f342a824fa69dda88bd6f436"
RECEIPT = Path(
    "docs/research_program/post_pr275/pillar_s_adjudication/"
    "PILLAR_S_COMPLETE_ADJUDICATION_V1.json"
)
RECEIPT_SHA256 = "ff2fe5f92cc3a6470500905f742dd788d63fd17a53ac00ffb7560cf3c1c503c2"
RECEIPT_CONTENT_SHA256 = "fd042fdb58575ebc8d23c3a2707dababa73d1098ccee7dd7ed6fc0fe5cd6ea7e"
REPORT = ROOT / (
    ".agent-harness/runs/pr286-numerical-repair-rereview-20260811/"
    "artifacts/A-PR286-R2-REPLAY-oracle-report.json"
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def git(*args: str, input_bytes: bytes | None = None) -> bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        input=input_bytes,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"git {' '.join(args)} failed: {completed.stderr.decode(errors='replace')}"
        )
    return completed.stdout


def patch_id(commit: str, paths: tuple[str, ...] = ()) -> str:
    if paths:
        diff = git("diff", f"{commit}^", commit, "--", *paths)
    else:
        diff = git("show", "--pretty=email", "--binary", commit)
    completed = subprocess.run(
        ["git", "patch-id", "--stable"],
        cwd=ROOT,
        input=diff,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0 or not completed.stdout.strip():
        raise AssertionError(f"stable patch-id failed for {commit}")
    return completed.stdout.decode("ascii").split()[0]


def load_runner():
    path = ROOT / "scripts/codex_harness/run_pr286_pillar_s_adjudication.py"
    spec = importlib.util.spec_from_file_location("pr286_r2_replay_runner", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def expect_preflight_error(runner, root: Path, output: Path, marker: str) -> None:
    old_root, old_output = runner.ROOT, runner.OUTPUT
    try:
        runner.ROOT, runner.OUTPUT = root, output
        try:
            runner._validate_output_destination_for_write()
        except runner.PillarSAdjudicationError as exc:
            assert marker in str(exc), (marker, str(exc))
        else:
            raise AssertionError(f"destination preflight did not reject {marker}")
    finally:
        runner.ROOT, runner.OUTPUT = old_root, old_output


def main() -> int:
    started = datetime.now(timezone.utc).isoformat()
    checks: list[str] = []

    assignment = json.loads(
        (
            ROOT
            / f".agent-harness/runs/{RUN_ID}/assignments/{ASSIGNMENT_ID}.json"
        ).read_text(encoding="utf-8")
    )
    index = json.loads(
        (ROOT / ".agent-harness/context/CONTEXT_INDEX.json").read_text(
            encoding="utf-8"
        )
    )
    assert assignment["context_version"] == CONTEXT_VERSION
    assert index["context_version"] == CONTEXT_VERSION
    checks.append("assignment_and_context_binding")

    required_hashes = {
        row["path"]: row["sha256"] for row in assignment["required_inputs"]
    }
    for relative, expected in required_hashes.items():
        assert sha256_bytes((ROOT / relative).read_bytes()) == expected, relative
    assert sha256_bytes(AUDIT.read_bytes()) == AUDIT_SHA256
    checks.append("required_input_and_external_audit_hashes")

    seal_path = ROOT / ".prguard/runtime/PR286_R2_CANDIDATE_SEAL.json"
    seal_bytes = seal_path.read_bytes()
    seal = json.loads(seal_bytes)
    assert sha256_bytes(seal_bytes) == assignment["required_inputs"][0]["sha256"]
    assert seal["candidate_sha"] == CANDIDATE_SHA
    assert seal["candidate_tree_sha"] == CANDIDATE_TREE
    assert seal["base_sha"] == BASE_SHA
    assert seal["merge_base_sha"] == BASE_SHA
    assert seal["dirty"] is False
    seal_without_digest = dict(seal)
    seal_without_digest.pop("seal_sha256")
    assert sha256_bytes(canonical_json(seal_without_digest)) == seal["seal_sha256"]
    assert git("rev-parse", "HEAD").decode().strip() == CANDIDATE_SHA
    assert git("rev-parse", "HEAD^{tree}").decode().strip() == CANDIDATE_TREE
    assert git("status", "--porcelain=v1").decode() == ""
    checks.append("final_candidate_seal_and_clean_tree")

    implementation_seal = json.loads(
        (
            ROOT
            / ".prguard/runtime/PR286_REPAIR_IMPLEMENTATION_CANDIDATE_SEAL.json"
        ).read_text(encoding="utf-8")
    )
    assert implementation_seal["candidate_sha"] == IMPLEMENTATION_SHA
    assert git("rev-parse", f"{CANDIDATE_SHA}^").decode().strip() == IMPLEMENTATION_SHA
    predecessor_seal = json.loads(
        (ROOT / ".prguard/runtime/PR285_R2_FINAL_CANDIDATE_SEAL.json").read_text(
            encoding="utf-8"
        )
    )
    assert predecessor_seal["candidate_sha"] == BASE_SHA
    assert git("merge-base", BASE_SHA, CANDIDATE_SHA).decode().strip() == BASE_SHA
    remote_target = "refs/remotes/origin/changeset/pr285-pillar-t-adjudication-recovery-20260810"
    assert git("rev-parse", remote_target).decode().strip() == BASE_SHA
    commits = git("rev-list", "--reverse", f"{BASE_SHA}..{CANDIDATE_SHA}").decode().split()
    assert commits == seal["candidate_commits"]
    assert git("rev-parse", f"{commits[0]}^").decode().strip() == BASE_SHA
    for left, right in zip(commits, commits[1:]):
        assert git("rev-parse", f"{right}^").decode().strip() == left
    checks.append("exact_pr285_predecessor_and_linear_candidate_chain")

    current_patch_ids = [patch_id(commit) for commit in commits]
    assert len(current_patch_ids) == len(set(current_patch_ids))
    assert current_patch_ids == [row["stable_patch_id"] for row in seal["stable_patch_ids"]]
    source_g23 = (
        "a87439735e7735359231bbd7620bbfb0f282d84e",
        "421304fe944235f8f87a21e3d03500714a4dcff3",
        "b3eb957ce71ee42c3c0692159ca4d624af5526c2",
    )
    source_g25 = (
        "b2013b44d8b7dbd3fb6ee4fc0aec089ddd64013c",
        "20e5903afde8adf08810b1a404381f3addf5fe95",
        "eed8a0f5e05fa53b122f66556925870c97ac30c8",
    )
    for source, expected_patch, current in (source_g23, source_g25):
        assert patch_id(source) == expected_patch
        assert patch_id(current) == expected_patch
        assert current_patch_ids.count(expected_patch) == 1
    retained_g27_paths = (
        "docs/research_program/post_pr275/pr286_spec.yaml",
        "scripts/codex_harness/run_pr286_pillar_s_adjudication.py",
        "tests/contracts/test_pillar_s_complete_adjudication.py",
    )
    assert patch_id(
        "77f9bad2ce8deb534d1622f2455120131b8f441b", retained_g27_paths
    ) == patch_id("b2b51e7102d8e3cbaa5b00de9bb5ceeb010d2f8d", retained_g27_paths)
    assert patch_id("b2b51e7102d8e3cbaa5b00de9bb5ceeb010d2f8d") == (
        "f4559d070c92104aa0a54613d7f947b605d2f535"
    )
    excluded = {
        patch_id("9ad9340b058a7ce0bddf9a71466740d87e1a7384"),
        patch_id("b8bc64ca2d92993d888c7b3278a3e1a3cb5e9e46"),
    }
    assert excluded == {
        "6ff47e6bbbd19775ea47cc1b9e9f4ab1febc53a1",
        "557612e77a4504b02c72317bd35c3ff8582db721",
    }
    assert excluded.isdisjoint(current_patch_ids)
    assert patch_id(IMPLEMENTATION_SHA) == REPAIR_PATCH_ID
    assert current_patch_ids.count(REPAIR_PATCH_ID) == 1
    audit_text = AUDIT.read_text(encoding="utf-8")
    for token in (
        "| G23 | 286 |",
        "| G24 | 286 |",
        "| G25 | 286 |",
        "| G26 | 286 |",
        "| G27 | 286 |",
        "G23,G25,G27",
        "G24,G26",
    ):
        assert token in audit_text
    checks.append("selective_salvage_patch_identity_and_exclusions")

    receipt_bytes = (ROOT / RECEIPT).read_bytes()
    receipt = json.loads(receipt_bytes)
    spec = yaml.safe_load(
        (ROOT / "docs/research_program/post_pr275/pr286_spec.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert sha256_bytes(receipt_bytes) == RECEIPT_SHA256
    assert len(receipt["rows"]) == 72
    assert len(receipt["source_bindings"]) == 33
    assert receipt["source_binding_map"] == {
        row["path"]: row["sha256"] for row in receipt["source_bindings"]
    }
    for binding in receipt["source_bindings"]:
        path = ROOT / binding["path"]
        assert path.is_file() and not path.is_symlink()
        assert sha256_bytes(path.read_bytes()) == binding["sha256"], binding["path"]
    content_payload = dict(receipt)
    content_payload.pop("receipt_content_sha256")
    content_digest = sha256_bytes(canonical_json(content_payload))
    assert content_digest == receipt["receipt_content_sha256"] == RECEIPT_CONTENT_SHA256
    expected_mutations = spec["mutation_registry"]
    assert receipt["mutation_registry"] == expected_mutations
    mutation_ids = [row["mutation_id"] for row in expected_mutations]
    results = receipt["mutation_results"]
    assert len(mutation_ids) == 19
    assert [row["mutation_id"] for row in results] == mutation_ids
    assert all(
        row["executed"] is True
        and row["activated"] is True
        and row["killed"] is True
        and row["survivor"] is False
        and row["kill_marker"]
        for row in results
    )
    numeric = results[-1]
    assert numeric["mutation_id"] == "MU286-VTS14-NUMERIC-GUARD-DRIFT"
    assert numeric["kill_marker"] == "SEMANTIC_TYPE_DRIFT"
    checks.append("receipt_inventory_bindings_content_address_and_19_mutations")

    runner = load_runner()
    built_one = runner.build_complete_adjudication_receipt()
    built_two = runner.build_complete_adjudication_receipt()
    assert built_one == built_two == receipt
    assert runner._serialized(built_one) == receipt_bytes
    checks.append("deterministic_receipt_recomputation")

    protected = (
        "docs/research_program/vector_tensor/pr271_spec.yaml",
        "docs/research_program/vector_tensor/proofs/PILLAR_S_CORE_PROOFS_V1.yaml",
        "docs/research_program/vector_tensor/proofs/PR271_PILLAR_S_CORE.md",
        "scripts/codex_harness/build_pr271_pillar_s_core.py",
        "docs/research_program/vector_tensor/pr272_spec.yaml",
        "docs/research_program/vector_tensor/proofs/PILLAR_S_INFERENCE_VALIDATION_V1.yaml",
        "scripts/codex_harness/build_pr272_pillar_s_inference.py",
        "docs/research_program/vector_tensor/pr273_spec.yaml",
        "docs/research_program/vector_tensor/integration/PR273_DIAGNOSTIC_PACK.json",
        "scripts/codex_harness/build_pr273_blind_synthetic.py",
    )
    for relative in protected:
        assert git("rev-parse", f"{BASE_SHA}:{relative}") == git(
            "rev-parse", f"{CANDIDATE_SHA}:{relative}"
        ), relative
    checks.append("pr271_pr272_pr273_frozen_record_preservation")

    status_a = (ROOT / "docs/codex_handoff/pr_status.yaml").read_bytes()
    status_b = (ROOT / "machine_readable/pr_status.yaml").read_bytes()
    backlog_a = (ROOT / "docs/codex_handoff/pr_backlog.yaml").read_bytes()
    backlog_b = (ROOT / "machine_readable/pr_backlog.yaml").read_bytes()
    backlog_json_a = (ROOT / "docs/codex_handoff/pr_backlog.json").read_bytes()
    backlog_json_b = (ROOT / "machine_readable/pr_backlog.json").read_bytes()
    assert status_a == status_b
    assert backlog_a == backlog_b
    assert backlog_json_a == backlog_json_b
    status = yaml.safe_load(status_a)
    states = status["stacked_pr_execution"]["prs"]
    assert status["in_progress"] == "PR-286"
    assert states["PR-286"]["lifecycle"] == "VALIDATED"
    assert states["PR-286"]["base_sha"] == BASE_SHA
    assert states["PR-286"]["predecessor_sealed_sha"] == BASE_SHA
    assert states["PR-286"]["gate_dispositions"]["review"] == "DEFERRED"
    assert states["PR-286"]["gate_dispositions"]["seal"] == "INELIGIBLE"
    assert states["PR-287"]["lifecycle"] == "PLANNED"
    assert states["PR-287"]["gate_dispositions"] == {"eligibility": "INELIGIBLE"}
    checks.append("synchronized_status_and_backlog_mirrors")

    policy_path = ROOT / "docs/research_program/post_pr275/pr286_publication_policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    assert policy["change_set_id"] == seal["change_set_id"]
    assert policy["publication_group_id"] == seal["publication_group_id"]
    assert policy["target_sha"] == seal["base_sha"] == BASE_SHA
    assert policy["target_ref"] == f"origin/{seal['target_branch']}"
    assert seal["integration_policy"]["sha256"] == sha256_bytes(
        policy_path.read_bytes()
    )
    command_ids = [row["id"] for row in policy["required_commands"]]
    assert len(command_ids) == len(set(command_ids)) == 10
    checks.append("dag_and_publication_policy_identity_cross_binding")

    with tempfile.TemporaryDirectory(prefix="pr286-r2-oracle-") as raw_tmp:
        tmp = Path(raw_tmp)
        root = tmp / "root"
        root.mkdir()
        parent = root / "generated"
        parent.mkdir()
        outside = tmp / "outside.json"
        outside.write_text("preserve\n", encoding="utf-8")

        hardlink = parent / "hardlink.json"
        os.link(outside, hardlink)
        expect_preflight_error(
            runner, root, hardlink, "OUTPUT_DESTINATION_NOT_SINGLE_LINK_FILE"
        )
        hardlink.unlink()

        symlink = parent / "symlink.json"
        symlink.symlink_to(outside)
        expect_preflight_error(runner, root, symlink, "OUTPUT_DESTINATION_SYMLINK")
        symlink.unlink()

        real_parent = tmp / "real-parent"
        real_parent.mkdir()
        linked_parent = root / "linked-parent"
        linked_parent.symlink_to(real_parent, target_is_directory=True)
        expect_preflight_error(
            runner,
            root,
            linked_parent / "receipt.json",
            "OUTPUT_PARENT_NOT_REGULAR",
        )

        expect_preflight_error(
            runner, root, tmp / "escape.json", "OUTPUT_ESCAPES_REPOSITORY_ROOT"
        )

        destination = parent / "receipt.json"
        destination.write_bytes(b"old\n")
        old_output = runner.OUTPUT
        try:
            runner.OUTPUT = destination
            runner._atomic_write(b"new\n")
        finally:
            runner.OUTPUT = old_output
        assert destination.read_bytes() == b"new\n"
        assert destination.stat().st_nlink == 1
        assert not list(parent.glob(f".{destination.name}.*"))
        assert outside.read_text(encoding="utf-8") == "preserve\n"
    checks.append("destination_containment_hardlink_symlink_and_atomic_write")

    report = {
        "schema": "A_PR286_R2_REPLAY_ORACLE_REPORT_V1",
        "run_id": RUN_ID,
        "assignment_id": ASSIGNMENT_ID,
        "context_version": CONTEXT_VERSION,
        "status": "PASS",
        "started_at": started,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "candidate_sha": CANDIDATE_SHA,
        "candidate_tree_sha": CANDIDATE_TREE,
        "base_sha": BASE_SHA,
        "receipt_sha256": RECEIPT_SHA256,
        "receipt_content_sha256": RECEIPT_CONTENT_SHA256,
        "row_count": len(receipt["rows"]),
        "source_binding_count": len(receipt["source_bindings"]),
        "mutation_ids": mutation_ids,
        "stable_patch_ids": current_patch_ids,
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
