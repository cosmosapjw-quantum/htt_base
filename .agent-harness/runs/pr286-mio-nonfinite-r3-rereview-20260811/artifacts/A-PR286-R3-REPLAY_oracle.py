#!/usr/bin/env python3
"""Independent bounded invariant oracle for the frozen PR-286 candidate."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import yaml


RUN_ID = "pr286-mio-nonfinite-r3-rereview-20260811"
ASSIGNMENT_ID = "A-PR286-R3-REPLAY"
BASE = "16bc6db511b8b7228e5c4dcb95c65074fe519f24"
HEAD = "0b1a8ef76df47b0b42e972bb47c9bc294e80aa7c"
TREE = "c92883d3500aff9a7fa07e561ad43bf4088feb9d"
RECEIPT_SHA256 = "b5ea12647f1d7818da3702b3da8d127f490a15cdef8e37fa8958cfe803b3ee5a"
CONTENT_SHA256 = "00948067d29adfcc3cb1c931642cc11ff2bf4df5c85cb2be8087064beb810b76"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(repo: Path, *argv: str, input_bytes: bytes | None = None) -> bytes:
    completed = subprocess.run(
        argv,
        cwd=repo,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        raise AssertionError(
            f"command failed ({completed.returncode}): {argv!r}\n"
            + completed.stderr.decode("utf-8", "replace")
        )
    return completed.stdout


def text(repo: Path, *argv: str) -> str:
    return run(repo, *argv).decode("utf-8").strip()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def stable_patch_id(repo: Path, commit: str) -> str:
    patch = run(
        repo,
        "git",
        "show",
        "--pretty=format:",
        "--binary",
        "--full-index",
        "--no-color",
        "--no-ext-diff",
        "--no-textconv",
        "--no-renames",
        commit,
    )
    output = run(repo, "git", "patch-id", "--stable", input_bytes=patch)
    return output.decode("ascii").split()[0]


def main() -> None:
    repo = Path(__file__).resolve().parents[4]
    assert repo.name == "htt-process-inflation-recovery-pr283-20260810"
    assignment_path = repo / ".agent-harness/runs" / RUN_ID / "assignments" / f"{ASSIGNMENT_ID}.json"
    assignment = json.loads(assignment_path.read_text(encoding="utf-8"))
    seal_path = repo / assignment["candidate_binding"]["seal_path"]
    seal = json.loads(seal_path.read_text(encoding="utf-8"))

    assert text(repo, "git", "rev-parse", "HEAD") == HEAD == seal["candidate_sha"]
    assert text(repo, "git", "rev-parse", "HEAD^{tree}") == TREE == seal["candidate_tree_sha"]
    assert text(repo, "git", "merge-base", BASE, HEAD) == BASE == seal["merge_base_sha"]

    harness_scripts = repo / ".agent-harness/scripts"
    sys.path.insert(0, str(harness_scripts))
    from publication_integrity import validate_candidate_seal_payload

    assert validate_candidate_seal_payload(seal, repo=repo) == []

    commits = text(repo, "git", "rev-list", "--reverse", f"{BASE}..{HEAD}").splitlines()
    assert commits == seal["candidate_commits"]
    patch_rows = [
        {"commit": commit, "stable_patch_id": stable_patch_id(repo, commit)}
        for commit in commits
    ]
    assert patch_rows == seal["stable_patch_ids"]
    patch_ids = [row["stable_patch_id"] for row in patch_rows]
    assert len(patch_ids) == len(set(patch_ids)) == 13

    expected_selective = {
        "b3eb957ce71ee42c3c0692159ca4d624af5526c2": "421304fe944235f8f87a21e3d03500714a4dcff3",
        "eed8a0f5e05fa53b122f66556925870c97ac30c8": "20e5903afde8adf08810b1a404381f3addf5fe95",
        "b2b51e7102d8e3cbaa5b00de9bb5ceeb010d2f8d": "f4559d070c92104aa0a54613d7f947b605d2f535",
    }
    assert all(
        {"commit": commit, "stable_patch_id": patch_id} in patch_rows
        for commit, patch_id in expected_selective.items()
    )
    assert not {
        "9ad9340b058a7ce0bddf9a71466740d87e1a7384",
        "b8bc64ca2d92993d888c7b3278a3e1a3cb5e9e46",
    }.intersection(commits)
    assert not {
        "6ff47e6bbbd19775ea47cc1b9e9f4ab1febc53a1",
        "557612e77a4504b02c72317bd35c3ff8582db721",
        "1475887aebb55340bb028044a64c3631b582e5de",
    }.intersection(patch_ids)

    for required in assignment["required_inputs"]:
        path = repo / required["path"]
        assert path.is_file() and not path.is_symlink()
        assert sha256(path.read_bytes()) == required["sha256"]

    receipt_path = repo / "docs/research_program/post_pr275/pillar_s_adjudication/PILLAR_S_COMPLETE_ADJUDICATION_V1.json"
    assert sha256(receipt_path.read_bytes()) == RECEIPT_SHA256
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    runner = load_module(
        repo / "scripts/codex_harness/run_pr286_pillar_s_adjudication.py",
        "pr286_replay_oracle_runner",
    )
    runner.validate_complete_adjudication_receipt(receipt)
    assert runner.receipt_content_sha256(receipt) == CONTENT_SHA256
    assert receipt["receipt_content_sha256"] == CONTENT_SHA256
    assert len(receipt["rows"]) == 72
    assert receipt["summary"] == {
        "bare_not_adjudicated_count": 0,
        "source_partition_counts": {"BRIDGE": 4, "I": 30, "II": 24},
        "source_proof_class_counts": {"ST": 24, "TC": 30, "U": 4},
        "source_rows": 58,
        "terminal_counts": {
            "BLOCKED_WITH_RECEIPT": 1,
            "FAIL": 0,
            "INCONCLUSIVE_WITH_RECEIPT": 50,
            "PASS": 21,
        },
        "vector_tensor_rows": 14,
    }
    assert len(receipt["source_bindings"]) == 33
    for binding in receipt["source_bindings"]:
        path = repo / binding["path"]
        assert path.is_file() and not path.is_symlink()
        assert path.stat().st_nlink == 1
        assert sha256(path.read_bytes()) == binding["sha256"]
        assert receipt["source_binding_map"][binding["path"]] == binding["sha256"]

    expected_mutations = [row["mutation_id"] for row in receipt["mutation_registry"]]
    results = receipt["mutation_results"]
    assert len(expected_mutations) == len(results) == 20
    assert [row["mutation_id"] for row in results] == expected_mutations
    assert all(
        row["executed"] is True
        and row["activated"] is True
        and row["killed"] is True
        and row["survivor"] is False
        and row["kill_marker"]
        for row in results
    )
    mio_mutation = results[-1]
    assert mio_mutation["mutation_id"] == "MU286-VTS14-MIO-NUMERIC-GUARD-DRIFT"
    assert mio_mutation["kill_marker"] == "SEMANTIC_TYPE_DRIFT"
    assert runner.build_complete_adjudication_receipt() == receipt

    sys.path.insert(0, str(repo / "htt/src"))
    sys.path.insert(0, str(repo / "htt"))
    from common.vector_tensor_statistical_inference import PillarSInferenceError
    from mio.formalism.vector_tensor_validation import build_mio_depth_cross_check

    local = np.asarray((1.0e200, 1.0e200))
    global_ = np.asarray((1.0e200, 1.0e200 + 2.0e185))
    try:
        build_mio_depth_cross_check(
            local,
            local_design=local,
            global_design=global_,
            mask_path_id="pr286-independent-oracle",
        )
    except PillarSInferenceError as exc:
        assert str(exc) == "finite MIO diagnostic outputs are required"
    else:
        raise AssertionError("public MIO non-finite counterexample was accepted")

    status = yaml.safe_load((repo / "docs/codex_handoff/pr_status.yaml").read_text(encoding="utf-8"))
    mirror = yaml.safe_load((repo / "machine_readable/pr_status.yaml").read_text(encoding="utf-8"))
    assert status == mirror
    phase = status["stacked_pr_execution"]["prs"]
    assert phase["PR-286"]["lifecycle"] == "VALIDATED"
    assert phase["PR-286"]["assurance_budget"] == {"maximum": 16, "consumed": 7}
    assert phase["PR-286"]["gate_dispositions"]["seal"] == "INELIGIBLE"
    assert phase["PR-286"]["gate_dispositions"]["publication"] == "INELIGIBLE"
    assert phase["PR-287"]["lifecycle"] == "PLANNED"
    assert phase["PR-287"]["gate_dispositions"] == {"eligibility": "INELIGIBLE"}
    assert phase["PR-287"]["assurance_budget"] == {"maximum": 16, "consumed": 0}

    print(
        json.dumps(
            {
                "ok": True,
                "candidate": {"base": BASE, "head": HEAD, "tree": TREE},
                "stable_patch_ids": len(patch_ids),
                "source_bindings": len(receipt["source_bindings"]),
                "rows": len(receipt["rows"]),
                "mutations_executed_activated_killed": len(results),
                "mio_nonfinite_public_facade": "TYPED_REFUSAL",
                "receipt_content_sha256": receipt["receipt_content_sha256"],
                "lifecycle": "VALIDATED",
                "assurance": "7/16",
                "pr287": "PLANNED_INELIGIBLE_0_OF_16",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
