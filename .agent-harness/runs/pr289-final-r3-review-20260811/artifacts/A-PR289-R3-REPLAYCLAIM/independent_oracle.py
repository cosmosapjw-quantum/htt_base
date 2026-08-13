#!/usr/bin/env python3
"""Independent read-only lineage, identity, replay, and claim oracle for PR-289."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tarfile

import yaml


RUN_ID = "pr289-final-r3-review-20260811"
ASSIGNMENT_ID = "A-PR289-R3-REPLAYCLAIM"
BASE = "27df5da040e27eeaad44873ba3424ff73fb4bb09"
CANDIDATE = "951b80c140325b74fb31ad648939180eaca4df86"
TREE = "bb946196db0d91451f4c0f87df01d24295f6b2dd"
TARGET_REF = "refs/remotes/origin/changeset/pr288-bayesian-evidence-recovery-20260811"
CANDIDATE_REF = "refs/heads/changeset/pr289-native-data-identity-recovery-20260811"
EXPECTED_ASSIGNMENT_SHA = "948256a6676a202cff666f4262482337da017ce3e4c941c2a932ccdb69467900"
EXPECTED_CONTEXT = "e9b385d7fbc4f8e47c97c3b0c7edae4e522d9be4e025d9342e26ab24829e3019"


def run(root: Path, *argv: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.run(
        argv,
        cwd=root,
        input=input_bytes,
        capture_output=True,
        check=True,
    ).stdout


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def canonical_sha(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return "sha256:" + sha_bytes(encoded)


def git_text(root: Path, *argv: str) -> str:
    return run(root, "git", *argv).decode("utf-8").strip()


def patch_id(root: Path, commit: str) -> str:
    patch = run(root, "git", "show", "--pretty=format:", commit)
    return run(root, "git", "patch-id", "--stable", input_bytes=patch).decode().split()[0]


def resolve_commit(root: Path, abbreviated: str) -> str:
    return git_text(root, "rev-parse", f"{abbreviated}^{{commit}}")


def blob(root: Path, commit: str, path: str) -> str:
    return git_text(root, "rev-parse", f"{commit}:{path}")


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def archive_containment_oracle(root: Path) -> dict[str, object]:
    runner = load_module(
        root / "scripts/codex_harness/run_pr289_data_identity_v2.py",
        "pr289_runner_oracle",
    )
    cases: list[tuple[str, tarfile.TarInfo]] = []
    for name in ("../escape", "/absolute", "safe/../../escape"):
        member = tarfile.TarInfo(name)
        member.size = 0
        cases.append((name, member))
    link = tarfile.TarInfo("unsafe-link")
    link.type = tarfile.SYMTYPE
    link.linkname = "../escape"
    cases.append(("symlink", link))
    rejected: list[str] = []
    import tempfile

    for label, member in cases:
        raw = io.BytesIO()
        with tarfile.open(fileobj=raw, mode="w") as archive:
            archive.addfile(member, io.BytesIO(b"") if member.isfile() else None)
        raw.seek(0)
        with tempfile.TemporaryDirectory(prefix="pr289-oracle-tar-") as temporary:
            with tarfile.open(fileobj=raw, mode="r:") as archive:
                try:
                    runner._safe_extract_archive(archive, Path(temporary))
                except RuntimeError:
                    rejected.append(label)
                else:
                    raise AssertionError(f"unsafe archive case admitted: {label}")
    assert rejected == [label for label, _ in cases]
    return {"unsafe_cases": rejected, "all_rejected": True}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[5]

    assignment_path = root / f".agent-harness/runs/{RUN_ID}/assignments/{ASSIGNMENT_ID}.json"
    assignment = json.loads(assignment_path.read_text(encoding="utf-8"))
    assignment_unsigned = dict(assignment)
    observed_assignment_sha = assignment_unsigned.pop("assignment_sha256")
    recomputed_assignment_sha = sha_bytes(
        json.dumps(assignment_unsigned, sort_keys=True).encode("utf-8")
    )
    assert observed_assignment_sha == EXPECTED_ASSIGNMENT_SHA == recomputed_assignment_sha
    assert assignment["context_version"] == EXPECTED_CONTEXT

    input_hashes = {
        item["path"]: sha_file(root / item["path"])
        for item in assignment["required_inputs"]
    }
    assert all(
        input_hashes[item["path"]] == item["sha256"]
        for item in assignment["required_inputs"]
    )

    seal = json.loads((root / assignment["candidate_binding"]["seal_path"]).read_text())
    assert sha_file(root / assignment["candidate_binding"]["seal_path"]) == assignment["candidate_binding"]["seal_file_sha256"]
    assert git_text(root, "rev-parse", "HEAD") == CANDIDATE
    assert git_text(root, "rev-parse", "HEAD^{tree}") == TREE
    assert git_text(root, "merge-base", BASE, CANDIDATE) == BASE
    assert git_text(root, "rev-parse", TARGET_REF) == BASE
    assert git_text(root, "rev-parse", CANDIDATE_REF) == CANDIDATE

    commits = git_text(root, "rev-list", "--reverse", f"{BASE}..{CANDIDATE}").splitlines()
    assert commits == seal["candidate_commits"]
    parents = [git_text(root, "rev-parse", f"{commit}^") for commit in commits]
    assert parents == [BASE, *commits[:-1]]
    patch_ids = [patch_id(root, commit) for commit in commits]
    assert patch_ids == [row["stable_patch_id"] for row in seal["stable_patch_ids"]]
    assert len(patch_ids) == len(set(patch_ids)) == 14

    historical = {
        "G39": resolve_commit(root, "44091dea"),
        "G40": resolve_commit(root, "a757eeee"),
        "G42": resolve_commit(root, "c2037e8a"),
        "G45": resolve_commit(root, "7f9ac031"),
        "G46": resolve_commit(root, "834e15d7"),
        "G47": resolve_commit(root, "91d8b8ad"),
        "G48": resolve_commit(root, "dde54a71"),
    }
    historical_patch_ids = {key: patch_id(root, value) for key, value in historical.items()}
    assert historical_patch_ids["G45"] == patch_ids[1]
    assert historical_patch_ids["G46"] == patch_ids[2]
    for key in ("G39", "G40", "G42"):
        assert historical_patch_ids[key] not in patch_ids

    g47_subset = commits[3]
    g47_core_paths = [
        "htt/src/common/data_identity.py",
        "scripts/codex_harness/run_pr289_data_identity_v2.py",
        "tests/contracts/test_data_identity_registry_v2.py",
        "docs/research_program/post_pr275/pr289_spec.yaml",
    ]
    assert all(blob(root, historical["G47"], path) == blob(root, g47_subset, path) for path in g47_core_paths)
    g47_subset_paths = git_text(root, "diff-tree", "--no-commit-id", "--name-only", "-r", g47_subset).splitlines()
    assert "docs/generated/pr289_data_identity_v2_receipt.json" not in g47_subset_paths

    g48_subset = commits[4]
    assert blob(root, historical["G48"], "tests/contracts/test_data_identity_registry_v2.py") == blob(root, g48_subset, "tests/contracts/test_data_identity_registry_v2.py")
    assert set(git_text(root, "diff-tree", "--no-commit-id", "--name-only", "-r", g48_subset).splitlines()) == {
        "scripts/codex_harness/run_pr289_data_identity_v2.py",
        "tests/contracts/test_data_identity_registry_v2.py",
    }
    runner_delta = git_text(root, "diff", historical["G48"], g48_subset, "--", "scripts/codex_harness/run_pr289_data_identity_v2.py")
    assert "def _safe_extract_archive" in runner_delta
    assert "archive.extractall(destination, members=members)" in runner_delta

    receipt_path = root / "docs/generated/pr289_data_identity_v2_receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="ascii"))
    assert {
        path: "sha256:" + sha_file(root / path) for path in receipt["source_bindings"]
    } == receipt["source_bindings"]
    expected_generation_state = "BOUND_SOURCE_WORKTREE:" + canonical_sha(receipt["source_bindings"])
    assert receipt["generation_identity"]["git_commit_or_worktree_state"] == expected_generation_state
    assert receipt["git_commit_or_worktree_state"] == expected_generation_state
    unsigned_receipt = dict(receipt)
    observed_content_id = unsigned_receipt.pop("receipt_content_id")
    assert observed_content_id == canonical_sha(unsigned_receipt)
    registry = json.loads((root / "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json").read_text())
    assert receipt["registry_content_id"] == canonical_sha(registry)

    spec = yaml.safe_load((root / "docs/research_program/post_pr275/pr289_spec.yaml").read_text())
    expected_mutations = [row["mutation_id"] for row in spec["mutation_registry"]]
    observed_mutations = [row["mutation_id"] for row in receipt["mutation_results"]]
    assert expected_mutations == observed_mutations
    assert len(observed_mutations) == len(set(observed_mutations)) == 32
    assert all(row["activated"] and row["executed"] and row["killed"] for row in receipt["mutation_results"])

    assert receipt["owner"] == "COMMON"
    assert receipt["claim_level"] == {"scheme": "roadmap_rescue_v1", "level": "C2"}
    assert receipt["claim_tier"] == "diagnostic_only"
    assert receipt["transfer_source"] == "none"
    assert receipt["observed_data_executed"] is False
    assert receipt["public_use"] is False
    assert receipt["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
    assert receipt["aggregate_status"] == "NO_ADMITTED_IDENTITIES"
    assert all(row["status"] == "NOT_AUTHORIZED" for row in receipt["authorization_receipts"])

    result = {
        "schema": "PR289_INDEPENDENT_REPLAYCLAIM_ORACLE_V1",
        "status": "PASS",
        "candidate_identity": {
            "base_sha": BASE,
            "candidate_sha": CANDIDATE,
            "candidate_tree_sha": TREE,
            "linear_commit_count": len(commits),
            "unique_stable_patch_id_count": len(set(patch_ids)),
        },
        "lineage": {
            "exact_groups": ["G45", "G46"],
            "bounded_subsets": ["G47", "G48"],
            "excluded_groups": ["G39", "G40", "G42"],
            "historical_patch_ids": historical_patch_ids,
        },
        "identity_replay": {
            "required_input_hash_count": len(input_hashes),
            "source_binding_count": len(receipt["source_bindings"]),
            "generation_identity": expected_generation_state,
            "receipt_content_id": observed_content_id,
            "registry_content_id": receipt["registry_content_id"],
            "mutation_count": len(observed_mutations),
            "all_mutations_activated_executed_killed": True,
        },
        "claim_boundary": {
            "owner": receipt["owner"],
            "claim_level": receipt["claim_level"],
            "claim_tier": receipt["claim_tier"],
            "transfer_source": receipt["transfer_source"],
            "observed_data_executed": receipt["observed_data_executed"],
            "public_use": receipt["public_use"],
            "family_identification_gate": receipt["family_identification_gate"],
            "authorization_statuses": [row["status"] for row in receipt["authorization_receipts"]],
        },
        "archive_containment": archive_containment_oracle(root),
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "output": args.output.as_posix()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
