#!/usr/bin/env python3
"""Bounded independent replay oracle for the frozen PR-285 candidate."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


REPO = Path(__file__).resolve().parents[5]
HARNESS = REPO / ".agent-harness" / "scripts"
sys.path.insert(0, str(HARNESS))

from publication_integrity import (  # noqa: E402
    load_publication_policy,
    validate_candidate_seal_payload,
    validate_integration_receipt_payload,
)


SEAL_REL = ".prguard/runtime/PR285_FINAL_CANDIDATE_SEAL.json"
INTEGRATION_REL = ".prguard/runtime/PR285_FINAL_INTEGRATION_REHEARSAL.json"
POLICY_REL = "docs/research_program/post_pr275/pr285_publication_policy.json"
RECEIPT_REL = (
    "docs/research_program/post_pr275/pillar_t_adjudication/"
    "PILLAR_T_COMPLETE_ADJUDICATION_V1.json"
)
RUNNER_REL = "scripts/codex_harness/run_pr285_pillar_t_adjudication.py"
LOG_DIR = REPO / ".prguard/runtime/PR285_FINAL_INTEGRATION_REHEARSAL.logs"


def load(rel: str) -> dict:
    return json.loads((REPO / rel).read_text(encoding="utf-8"))


def sha(rel: str) -> str:
    return hashlib.sha256((REPO / rel).read_bytes()).hexdigest()


def git(*args: str, input_bytes: bytes | None = None) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=REPO,
        input=input_bytes,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.decode("utf-8", errors="replace"))
    return completed.stdout.decode("utf-8").strip()


def load_runner():
    spec = importlib.util.spec_from_file_location("pr285_reviewer_runner", REPO / RUNNER_REL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def expect_preflight_rejection(runner, root: Path, output: Path, marker: str) -> str:
    runner.ROOT = root
    runner.OUTPUT = output
    try:
        runner._validate_output_destination_for_write()
    except runner.PillarTAdjudicationError as exc:
        assert marker in str(exc), (marker, str(exc))
        return marker
    raise AssertionError(f"destination preflight admitted {marker}")


def main() -> None:
    seal = load(SEAL_REL)
    integration = load(INTEGRATION_REL)
    receipt = load(RECEIPT_REL)
    policy_bytes, policy = load_publication_policy(REPO, POLICY_REL)

    assert sha(SEAL_REL) == "7baf4ec6b941c0a29b247604b71cd94f43cb18de007afda9d1c2cc77d59e5d21"
    assert sha(INTEGRATION_REL) == "14f95ba8ab1b2f5dd39dbaa89c17f808ecb44be98aed0bdc56b3a0901ddd4d18"
    assert sha(RECEIPT_REL) == "1a6aa668d9aea071dd712a9143fea0fdf88d0523f3b4e41e8ca4e9002c927b82"
    assert hashlib.sha256(policy_bytes).hexdigest() == "973b1b1521d6a9ff4fd783839719fb3866ee0078a325f5ef968cf9c9aedf55b8"
    assert validate_candidate_seal_payload(seal, repo=REPO) == []
    assert git("rev-parse", "HEAD") == seal["candidate_sha"]
    assert git("rev-parse", "HEAD^{tree}") == seal["candidate_tree_sha"]
    assert git("merge-base", seal["base_sha"], "HEAD") == seal["merge_base_sha"]

    commits = git("rev-list", "--reverse", f"{seal['base_sha']}..{seal['candidate_sha']}").splitlines()
    assert commits == seal["candidate_commits"]
    sealed_patch_ids = [item["stable_patch_id"] for item in seal["stable_patch_ids"]]
    assert len(sealed_patch_ids) == len(set(sealed_patch_ids)) == len(commits)
    replayed_patch_ids: list[str] = []
    for commit in commits:
        patch = subprocess.run(
            ["git", "show", "--pretty=format:", "--binary", commit],
            cwd=REPO,
            capture_output=True,
            check=True,
        ).stdout
        result = subprocess.run(
            ["git", "patch-id", "--stable"],
            cwd=REPO,
            input=patch,
            capture_output=True,
            check=True,
        ).stdout.decode("ascii").strip()
        replayed_patch_ids.append(result.split()[0])
    assert replayed_patch_ids == sealed_patch_ids

    # The seal proves an exact unique patch-id lineage, but carries no logical
    # G20/G21/G22 source-group identities. Only self-authored PR delta prose
    # names those groups, so named selective-transplant provenance is not
    # independently machine-verifiable from the registered inputs.
    lineage_fields = {key for key in seal if "lineage" in key or "group" in key}
    has_named_group_map = any(
        key in seal for key in ("logical_patch_groups", "source_patch_groups", "recovery_groups")
    )
    assert not has_named_group_map

    assert integration["status"] == "PASS"
    assert integration["candidate_seal_sha256"] == seal["seal_sha256"]
    assert integration["candidate_sha"] == seal["candidate_sha"]
    assert integration["candidate_tree_sha"] == seal["candidate_tree_sha"]
    assert integration["diff_sha256"] == seal["diff_sha256"]
    assert integration["changed_files_sha256"] == seal["changed_files_sha256"]
    assert integration["integration_policy_sha256"] == sha(POLICY_REL)
    assert integration["latest_target_sha"] == seal["base_sha"]
    assert integration["merged_tree_sha"] == seal["candidate_tree_sha"]
    assert len(integration["commands"]) == 8
    assert all(row["returncode"] == 0 and row["timed_out"] is False for row in integration["commands"])
    assert validate_integration_receipt_payload(
        integration, seal=seal, policy=policy, repo=REPO, log_dir=LOG_DIR
    ) == []

    runner = load_runner()
    rebuilt = runner.build_complete_adjudication_receipt()
    assert rebuilt == receipt
    assert len(rebuilt["rows"]) == 80
    assert rebuilt["summary"] == {
        "source_rows": 65,
        "source_partition_counts": {"S": 34, "T": 31},
        "vector_tensor_rows": 14,
        "failed_candidate_rows": 1,
        "terminal_counts": {
            "PASS": 11,
            "FAIL": 1,
            "INCONCLUSIVE_WITH_RECEIPT": 67,
            "BLOCKED_WITH_RECEIPT": 1,
        },
        "bare_not_adjudicated_count": 0,
    }
    assert rebuilt["receipt_content_sha256"] == runner.receipt_content_sha256(rebuilt)
    for binding in rebuilt["source_bindings"]:
        path = REPO / binding["path"]
        assert path.is_file() and not path.is_symlink()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == binding["sha256"]
        assert rebuilt["source_binding_map"][binding["path"]] == binding["sha256"]
    registered = [row["mutation_id"] for row in rebuilt["mutation_registry"]]
    results = rebuilt["mutation_results"]
    assert [row["mutation_id"] for row in results] == registered
    assert all(
        row["executed"] is True
        and row["activated"] is True
        and row["killed"] is True
        and row["survivor"] is False
        for row in results
    )

    preflight: dict[str, str] = {}
    original_root, original_output = runner.ROOT, runner.OUTPUT
    try:
        with tempfile.TemporaryDirectory(prefix="pr285-review-preflight-") as directory:
            root = Path(directory)
            generated = root / "generated"
            generated.mkdir()

            fifo = generated / "fifo.json"
            os.mkfifo(fifo)
            preflight["fifo"] = expect_preflight_rejection(
                runner, root, fifo, "OUTPUT_DESTINATION_NOT_SINGLE_LINK_FILE"
            )

            outside = root / "outside.json"
            outside.write_text("preserve\n", encoding="utf-8")
            symlink = generated / "symlink.json"
            symlink.symlink_to(outside)
            preflight["symlink"] = expect_preflight_rejection(
                runner, root, symlink, "OUTPUT_DESTINATION_SYMLINK"
            )

            hardlink = generated / "hardlink.json"
            hardlink.hardlink_to(outside)
            preflight["multilink"] = expect_preflight_rejection(
                runner, root, hardlink, "OUTPUT_DESTINATION_NOT_SINGLE_LINK_FILE"
            )
            assert outside.read_text(encoding="utf-8") == "preserve\n"

            real_parent = root / "real-parent"
            real_parent.mkdir()
            linked_parent = root / "linked-parent"
            linked_parent.symlink_to(real_parent, target_is_directory=True)
            preflight["parent_symlink"] = expect_preflight_rejection(
                runner,
                root,
                linked_parent / "receipt.json",
                "OUTPUT_PARENT_NOT_REGULAR",
            )

            atomic = generated / "atomic.json"
            runner.ROOT, runner.OUTPUT = root, atomic
            runner._validate_output_destination_for_write()
            runner._atomic_write(b'{"atomic":true}\n')
            assert atomic.read_bytes() == b'{"atomic":true}\n'
            assert atomic.is_file() and not atomic.is_symlink() and atomic.stat().st_nlink == 1
            assert list(generated.glob(f".{atomic.name}.*")) == []
    finally:
        runner.ROOT, runner.OUTPUT = original_root, original_output

    assert {
        "max_open_prs": policy["max_open_prs"],
        "max_stack_depth": policy["max_stack_depth"],
        "max_file_overlap_prs": policy["max_file_overlap_prs"],
    } == {"max_open_prs": 3, "max_stack_depth": 3, "max_file_overlap_prs": 2}
    assert policy["claim_ceiling"] == "diagnostic_only"
    assert policy["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"

    print(json.dumps({
        "status": "FAIL_LINEAGE_PROVENANCE_UNVERIFIABLE",
        "candidate": {
            "sha": seal["candidate_sha"],
            "tree": seal["candidate_tree_sha"],
            "commit_count": len(commits),
            "stable_patch_ids": sealed_patch_ids,
            "unique_patch_ids": True,
        },
        "lineage_provenance": {
            "named_group_map_present": has_named_group_map,
            "seal_lineage_like_fields": sorted(lineage_fields),
            "verdict": "G20_G21_INCLUDED_AND_G22_EXCLUDED_NOT_INDEPENDENTLY_VERIFIABLE",
        },
        "receipt_replay": {
            "rows": len(rebuilt["rows"]),
            "content_sha256": rebuilt["receipt_content_sha256"],
            "source_bindings": len(rebuilt["source_bindings"]),
            "mutation_order": registered,
            "all_mutations_killed": True,
        },
        "destination_controls": {
            "rejections": preflight,
            "atomic_write": "PASS",
        },
        "integration": {
            "receipt_sha256": integration["receipt_sha256"],
            "passed_commands": [row["id"] for row in integration["commands"]],
        },
        "policy": {
            "sha256": sha(POLICY_REL),
            "max_open_prs": policy["max_open_prs"],
            "max_stack_depth": policy["max_stack_depth"],
            "max_file_overlap_prs": policy["max_file_overlap_prs"],
            "claim_ceiling": policy["claim_ceiling"],
            "family_identification_gate": policy["family_identification_gate"],
        },
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
