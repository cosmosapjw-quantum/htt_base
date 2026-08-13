#!/usr/bin/env python3
"""Executable, metadata-only oracle for the frozen PR-290 R3 closeout."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[4]
R2_SHA = "8da5ea88ab98aa42c8538198ea2d625f7d0f0555"
R3_SHA = "d73648b01f86333c94c82051415c58cbccbf54d2"
BASE_SHA = "45da1bf54149864fb9d87be3a828df202ee1df7f"
PRODUCTION_HASH = "b9b62e081f702f6b2b1918e5b3f1b599d651bdfa2fb0261e878d7a669d94beaf"
STALE_DIGEST = "75945200f0bf16cab9949b2fbfd31b18a4dbe9187f9665ea3eb311c9fbe58d44"

INPUT_HASHES = {
    ".prguard/runtime/PR290_R3_METADATA_CANDIDATE_SEAL.json": "7878f8797787955287b9aff665910727ae9c7b41071d7be95acbdd9ca7867a29",
    ".prguard/runtime/PR290_R2_CANDIDATE_SEAL.json": "db394a9cb3b243b438062d1769e2f1b11722966d34c45fa531890f08e8ff3ac7",
    ".agent-harness/runs/pr290-science-contract-r2-rereview-20260811/results/A-PR290-R2-PHYSCODE.json": "8a7c48f0c348ca917083f8d05cfabc547716a0bd12cc2b3e1700a1268bff8851",
    ".agent-harness/runs/pr290-science-contract-r2-rereview-20260811/results/A-PR290-R2-REPLAYCLAIM.json": "ea0525991e68c536789824d9eadc1529a0c5b0ff2616913b557596ca2dc92904",
    ".agent-harness/runs/pr290-science-contract-r2-rereview-20260811/MERGED_RESULTS.json": "75fe0dff5abf2a052663f26f0ab26676232b53f503e19b3be0d720e4895e2ac2",
    ".agent-harness/runs/pr290-science-contract-r2-rereview-20260811/RUN_SUMMARY.json": "b90bab618404de6f32e474b598139e75d8ecd01d315f1edd64fa77d3bdd6b4b3",
    "docs/research_program/post_pr275/pr290_spec.yaml": "1ec571a1de15d6b0addc608e2eb5db1dc9df7ae6e3bdd7f66160cf56ebeb5f9a",
    "docs/research_program/post_pr275/pr290_publication_policy.json": "45655b62f02f2d422283aa99780c78e80a022fbd1fd371e8ee7a450ddad320cd",
    "docs/research_program/post_pr275/data_runs/planck/PR290_NONEXECUTION_RECEIPT.json": "64501ed3467290e46bd687ab137ad461257e269925c5e8b235f2237778e19aba",
    "docs/PR_DELTAS/pr-290.md": "a0c9ccc47521b9e72c082b1e38377ee0ebcf3c25be90fd1cdc9136047d411848",
    "docs/codex_handoff/pr_status.yaml": "a56c459bb3d7f0fb3a91f589f3b44d1ffb2464f3f2ebdfe44880bcd10a9f7414",
    "machine_readable/pr_status.yaml": "a56c459bb3d7f0fb3a91f589f3b44d1ffb2464f3f2ebdfe44880bcd10a9f7414",
    "htt/src/common/observed_lane_activation.py": "79066a85eeb7515a9435a15963f26b2fcef02b8eabd11d59fde6ecfd8941d397",
    "htt/obsstat/planck_post275_lane.py": "84a326a2f7cb9ba10101a723ac14377e778260d06035b0435e94192459351959",
    "scripts/codex_harness/run_pr290_planck_lane.py": "abaddb4980839f3b368337e9c800bed7a15c78b8fb7ae78c4a0708dc9e250466",
    "tests/integration/test_planck_post275_lane.py": "58e59dd6f9f89b744757c3b2e87392c22972f531bf844ab8fd51eb1bb5e8f7f9",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*argv: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        argv,
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode:
        raise AssertionError(f"command failed ({result.returncode}): {argv!r}\n{result.stdout}")
    return result


def load_json(path: str) -> dict:
    return json.loads((REPO / path).read_text(encoding="utf-8"))


def main() -> int:
    for relative, expected in INPUT_HASHES.items():
        actual = digest(REPO / relative)
        assert actual == expected, (relative, actual, expected)

    assert run("git", "rev-parse", "HEAD").stdout.strip() == R3_SHA
    changed = run("git", "diff", "--name-only", f"{R2_SHA}..{R3_SHA}").stdout.splitlines()
    assert changed == ["docs/PR_DELTAS/pr-290.md"], changed

    r2_seal = load_json(".prguard/runtime/PR290_R2_CANDIDATE_SEAL.json")
    r3_seal = load_json(".prguard/runtime/PR290_R3_METADATA_CANDIDATE_SEAL.json")
    assert r2_seal["candidate_sha"] == R2_SHA
    assert r3_seal["candidate_sha"] == R3_SHA
    assert r2_seal["base_sha"] == r3_seal["base_sha"] == BASE_SHA
    assert r2_seal["production_hash"] == r3_seal["production_hash"] == PRODUCTION_HASH
    assert r2_seal["changed_files_sha256"] == r3_seal["changed_files_sha256"]
    assert r3_seal["integration_policy"]["sha256"] == INPUT_HASHES[
        "docs/research_program/post_pr275/pr290_publication_policy.json"
    ]

    r2_physics = load_json(
        ".agent-harness/runs/pr290-science-contract-r2-rereview-20260811/results/A-PR290-R2-PHYSCODE.json"
    )
    r2_replay = load_json(
        ".agent-harness/runs/pr290-science-contract-r2-rereview-20260811/results/A-PR290-R2-REPLAYCLAIM.json"
    )
    assert (r2_physics["status"], r2_physics["gate_disposition"]) == ("pass", "PASS")
    assert (r2_replay["status"], r2_replay["gate_disposition"]) == ("fail", "FAIL")
    assert r2_replay["findings"][0]["finding_id"] == "PR290-R2-STALE-PORTABLE-MANIFEST"
    assert r2_physics["candidate_binding"]["production_hash"] == PRODUCTION_HASH
    assert r2_replay["candidate_binding"]["production_hash"] == PRODUCTION_HASH

    delta = (REPO / "docs/PR_DELTAS/pr-290.md").read_text(encoding="utf-8")
    assert STALE_DIGEST not in delta
    normalized_delta = " ".join(delta.split())
    for fact in (
        "distinct clean archive root over 5,919",
        "Source and archive pre/post manifests were identical",
        "no observed input root, network/download side effect, or observed execution",
        "with one PASS and one FAIL",
        "self-referential stale literal",
    ):
        assert fact in normalized_delta, fact

    canonical_bytes = (REPO / "docs/codex_handoff/pr_status.yaml").read_bytes()
    mirror_bytes = (REPO / "machine_readable/pr_status.yaml").read_bytes()
    assert canonical_bytes == mirror_bytes
    status = yaml.safe_load(canonical_bytes)
    prs = status["stacked_pr_execution"]["prs"]
    pr289, pr290, pr291 = prs["PR-289"], prs["PR-290"], prs["PR-291"]
    assert pr289["sealed_head"] == pr290["base_sha"] == pr290["predecessor_sealed_sha"] == BASE_SHA
    assert pr290["lifecycle"] == "VALIDATED"
    assert pr290["production_hash"] == PRODUCTION_HASH
    assert pr290["pushed_ref"] is None and pr290["pr_url"] is None and pr290["sealed_head"] is None
    assert pr291["lifecycle"] == "PLANNED"
    assert pr291["gate_dispositions"] == {"eligibility": "INELIGIBLE"}
    assert pr291["assurance_budget"] == {"consumed": 0, "maximum": 16}

    policy = load_json("docs/research_program/post_pr275/pr290_publication_policy.json")
    assert policy["ordinary_agent_push_forbidden"] is True
    assert policy["ordinary_agent_pr_mutation_forbidden"] is True
    assert "merge" in policy["attended_publication"]["forbidden_actions"]

    portable = run(sys.executable, "-B", "scripts/codex_harness/run_pr290_planck_lane.py", "portable")
    portable_payload = json.loads(portable.stdout)
    manifest = portable_payload["tracked_source_manifest"]
    assert manifest["file_count"] == 5919
    assert portable_payload["source_root_differs_from_execution_root"] is True
    assert portable_payload["source_root_pre_hash"] == portable_payload["source_root_post_hash"]
    assert portable_payload["clean_root_pre_hash"] == portable_payload["clean_root_post_hash"]
    assert portable_payload["source_root_pre_hash"] == portable_payload["clean_root_pre_hash"]
    assert portable_payload["external_roots_supplied"] is False
    assert portable_payload["network_or_download_side_effect"] is False
    assert portable_payload["observed_data_executed"] is False
    assert STALE_DIGEST != manifest["manifest_sha256"]
    assert manifest["manifest_sha256"] not in delta

    claim = run(
        sys.executable,
        "-B",
        "scripts/check_claim_language.py",
        "--strict-missing",
        "--include-archives",
        "docs/research_program/post_pr275/pr290_spec.yaml",
        "htt/src/common/observed_lane_activation.py",
        "htt/obsstat/planck_post275_lane.py",
        "tests/integration/test_planck_post275_lane.py",
        "docs/research_program/post_pr275/data_runs/planck/PR290_NONEXECUTION_RECEIPT.json",
        "docs/PR_DELTAS/pr-290.md",
    )
    assert claim.stdout.strip() == "No forbidden claim language detected."

    print(
        json.dumps(
            {
                "status": "PASS",
                "candidate_sha": R3_SHA,
                "production_hash": PRODUCTION_HASH,
                "r2_chronology": ["PHYSCODE_PASS", "REPLAYCLAIM_FAIL"],
                "fresh_cells": ["portable_clean_integration", "claim_and_family_ceiling"],
                "tracked_files": 5919,
                "fresh_manifest_sha256": manifest["manifest_sha256"],
                "observed_data_executed": False,
                "network_or_download_side_effect": False,
                "claim_language": "PASS",
                "lifecycle": "VALIDATED",
                "pr291": "PLANNED_INELIGIBLE_ZERO_BUDGET",
                "publication_boundary": "NO_PUSH_NO_PR_NO_MERGE_HUMAN_ONLY",
                "assurance_budget": {"pre_assignment": "6/16", "projected": "7/16"},
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
