#!/usr/bin/env python3
"""Deterministic metadata-only oracle for the final PR-290 closeout."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
RUN_ID = "pr290-final-seal-closeout-20260811"
ASSIGNMENT_ID = "A-PR290-FINAL-SEAL-CLOSEOUT"
CONTEXT_VERSION = "e9b385d7fbc4f8e47c97c3b0c7edae4e522d9be4e025d9342e26ab24829e3019"
BASE = "45da1bf54149864fb9d87be3a828df202ee1df7f"
R3_HEAD = "d73648b01f86333c94c82051415c58cbccbf54d2"
HEAD = "06ac20605ebc371b0f97ad6e91c802a51a9bf764"
PRODUCTION_HASH = "b9b62e081f702f6b2b1918e5b3f1b599d651bdfa2fb0261e878d7a669d94beaf"
SEAL_PATH = ".prguard/runtime/PR290_FINAL_CANDIDATE_SEAL.json"
INTEGRATION_PATH = ".prguard/runtime/PR290_FINAL_INTEGRATION_REHEARSAL.json"
COVERAGE_PATH = (
    ".agent-harness/runs/pr290-final-seal-closeout-20260811/"
    "A-PR290-FINAL-SEAL-CLOSEOUT_REVIEW_COVERAGE.json"
)

REQUIRED_HASHES = {
    SEAL_PATH: "f30163cc748f3162a7de8f9f1232515b47911ea92998f3ba0f51536739382aed",
    INTEGRATION_PATH: "4fae957da4e9b53d0755197a30ed4d3c5d4e392812ceec8bbdfb3b4611b5ba28",
    ".agent-harness/runs/pr290-frozen-independent-review-20260811/results/A-PR290-FROZEN-CODE.json": "664a5b28fa5068563ef9e36e224de62646820a1f545edf4f6fb5cf9359658870",
    ".agent-harness/runs/pr290-frozen-independent-review-20260811/results/A-PR290-FROZEN-PHYSSTAT.json": "b19c6ed4bbe03cee597067f00d5a23a334167c858dfe7f4fb54848b3a6890b4e",
    ".agent-harness/runs/pr290-frozen-independent-review-20260811/results/A-PR290-FROZEN-REPLAYCLAIM.json": "77ed839b339784a7d504cfccef6b6823a0d97b692f3b99e67072f77918b88bc4",
    ".agent-harness/runs/pr290-frozen-independent-review-20260811/MERGED_RESULTS.json": "548877159287e552e0f4f19fe39c9ced7d1168d7060928386fc390de2d10a881",
    ".agent-harness/runs/pr290-frozen-independent-review-20260811/RUN_SUMMARY.json": "9c96fb76163bf1f54a3a6d8f44bf9463d62de8536730474b22c61cf7f8c939cf",
    ".agent-harness/runs/pr290-science-contract-r2-rereview-20260811/results/A-PR290-R2-PHYSCODE.json": "8a7c48f0c348ca917083f8d05cfabc547716a0bd12cc2b3e1700a1268bff8851",
    ".agent-harness/runs/pr290-science-contract-r2-rereview-20260811/results/A-PR290-R2-REPLAYCLAIM.json": "ea0525991e68c536789824d9eadc1529a0c5b0ff2616913b557596ca2dc92904",
    ".agent-harness/runs/pr290-science-contract-r2-rereview-20260811/MERGED_RESULTS.json": "75fe0dff5abf2a052663f26f0ab26676232b53f503e19b3be0d720e4895e2ac2",
    ".agent-harness/runs/pr290-science-contract-r2-rereview-20260811/RUN_SUMMARY.json": "b90bab618404de6f32e474b598139e75d8ecd01d315f1edd64fa77d3bdd6b4b3",
    ".agent-harness/runs/pr290-portable-prose-r3-closeout-20260811/results/A-PR290-R3-METADATA-CLOSEOUT.json": "d72192e1b8de79ec560b2d8cf5f889a6c4e82db743258f405f5b46f765c3eda1",
    ".agent-harness/runs/pr290-portable-prose-r3-closeout-20260811/MERGED_RESULTS.json": "c038293e28ff3fbcc9c452dc8f8781eeecc642e16df63571a134af10cb125693",
    ".agent-harness/runs/pr290-portable-prose-r3-closeout-20260811/RUN_SUMMARY.json": "14bb11e8f545f86fcbe3c28a64909b00940ed3bbafa5af3f3e00e9b817778668",
    "docs/research_program/post_pr275/pr290_spec.yaml": "1ec571a1de15d6b0addc608e2eb5db1dc9df7ae6e3bdd7f66160cf56ebeb5f9a",
    "docs/research_program/post_pr275/pr290_publication_policy.json": "45655b62f02f2d422283aa99780c78e80a022fbd1fd371e8ee7a450ddad320cd",
    "docs/research_program/post_pr275/data_runs/planck/PR290_NONEXECUTION_RECEIPT.json": "501e5fb2a812e14deea6fc5e81094e766b38fe6b6e00df49b904a16ba345f0e1",
    "docs/PR_DELTAS/pr-290.md": "59b3031af346658bdaabdd7d5d3f3cd94a167bcc7bd745a6e602fad8f96c4b44",
    "docs/codex_handoff/pr_status.yaml": "03feaaf86abb3d5c12767d168b7f169740e911d11f525543b9fffabbc42360e8",
    "machine_readable/pr_status.yaml": "03feaaf86abb3d5c12767d168b7f169740e911d11f525543b9fffabbc42360e8",
    ".agent-harness/scripts/_harness.py": "388f66e208bc460fb916eeca8603fc6f5ebfd914e448e59e93382152fde3f6ce",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(rel: str) -> dict:
    value = json.loads((ROOT / rel).read_text(encoding="utf-8"))
    assert isinstance(value, dict), rel
    return value


def canonical_digest_without(value: dict, key: str) -> str:
    payload = dict(value)
    payload.pop(key)
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def git(*args: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    ).stdout


def main() -> None:
    for rel, expected in REQUIRED_HASHES.items():
        assert sha256(ROOT / rel) == expected, f"registered input drift: {rel}"

    seal = load_json(SEAL_PATH)
    integration = load_json(INTEGRATION_PATH)
    policy = load_json("docs/research_program/post_pr275/pr290_publication_policy.json")
    receipt = load_json(
        "docs/research_program/post_pr275/data_runs/planck/PR290_NONEXECUTION_RECEIPT.json"
    )
    r1_code = load_json(
        ".agent-harness/runs/pr290-frozen-independent-review-20260811/results/A-PR290-FROZEN-CODE.json"
    )
    r1_phys = load_json(
        ".agent-harness/runs/pr290-frozen-independent-review-20260811/results/A-PR290-FROZEN-PHYSSTAT.json"
    )
    r1_replay = load_json(
        ".agent-harness/runs/pr290-frozen-independent-review-20260811/results/A-PR290-FROZEN-REPLAYCLAIM.json"
    )
    r2_phys = load_json(
        ".agent-harness/runs/pr290-science-contract-r2-rereview-20260811/results/A-PR290-R2-PHYSCODE.json"
    )
    r2_replay = load_json(
        ".agent-harness/runs/pr290-science-contract-r2-rereview-20260811/results/A-PR290-R2-REPLAYCLAIM.json"
    )
    r3 = load_json(
        ".agent-harness/runs/pr290-portable-prose-r3-closeout-20260811/results/A-PR290-R3-METADATA-CLOSEOUT.json"
    )

    assert canonical_digest_without(seal, "seal_sha256") == seal["seal_sha256"]
    assert seal["seal_sha256"] == "77e07224080bcea620674881ebe9aee78e6172b1692f8dfededa7e00a600cc3f"
    assert seal["base_sha"] == seal["merge_base_sha"] == BASE
    assert seal["candidate_sha"] == HEAD
    assert seal["candidate_tree_sha"] == git("rev-parse", f"{HEAD}^{{tree}}").decode().strip()
    assert seal["dirty"] is False
    assert seal["production_hash"] == PRODUCTION_HASH
    assert git("rev-parse", "HEAD").decode().strip() == HEAD
    assert git("status", "--porcelain=v1") == b""
    assert git("merge-base", BASE, HEAD).decode().strip() == BASE

    commits = git("rev-list", "--reverse", f"{BASE}..{HEAD}").decode().splitlines()
    assert commits == seal["candidate_commits"] and len(commits) == 8
    parent_rows = git("rev-list", "--reverse", "--parents", f"{BASE}..{HEAD}").decode().splitlines()
    expected_parent = BASE
    for row, commit in zip(parent_rows, commits, strict=True):
        fields = row.split()
        assert fields == [commit, expected_parent], f"nonlinear commit: {row}"
        expected_parent = commit
    patch_ids = []
    for commit in commits:
        patch = git("show", commit, "--pretty=format:", "--no-ext-diff")
        patch_id = git("patch-id", "--stable", input_bytes=patch).decode().split()[0]
        patch_ids.append({"commit": commit, "stable_patch_id": patch_id})
    assert patch_ids == seal["stable_patch_ids"]
    assert len({row["stable_patch_id"] for row in patch_ids}) == 8

    final_paths = git("diff", "--name-only", f"{R3_HEAD}..{HEAD}").decode().splitlines()
    assert final_paths == [
        "docs/PR_DELTAS/pr-290.md",
        "docs/codex_handoff/pr_status.yaml",
        "docs/research_program/post_pr275/data_runs/planck/PR290_NONEXECUTION_RECEIPT.json",
        "machine_readable/pr_status.yaml",
    ]
    assert git("rev-list", "--reverse", f"{R3_HEAD}..{HEAD}").decode().splitlines() == [HEAD]

    assert canonical_digest_without(integration, "receipt_sha256") == integration["receipt_sha256"]
    for key in ("candidate_sha", "candidate_tree_sha", "diff_sha256", "changed_files_sha256"):
        assert integration[key] == seal[key], key
    assert integration["candidate_seal_sha256"] == seal["seal_sha256"]
    assert integration["latest_target_sha"] == BASE
    assert integration["status"] == "PASS"
    command_ids = [row["id"] for row in integration["commands"]]
    assert command_ids == [row["id"] for row in policy["required_commands"]]
    assert len(command_ids) == 7 and len(set(command_ids)) == 7
    assert all(row["returncode"] == 0 and row["timed_out"] is False for row in integration["commands"])

    assert (ROOT / "docs/codex_handoff/pr_status.yaml").read_bytes() == (
        ROOT / "machine_readable/pr_status.yaml"
    ).read_bytes()
    status = yaml.safe_load((ROOT / "docs/codex_handoff/pr_status.yaml").read_text())
    stack = status["stacked_pr_execution"]
    pr290 = stack["prs"]["PR-290"]
    pr291 = stack["prs"]["PR-291"]
    assert stack["merge_policy"] == "HUMAN_ONLY"
    assert pr290["lifecycle"] == "REVIEWED"
    assert pr290["lifecycle_history"] == ["PLANNED", "ACTIVE", "IMPLEMENTED", "VALIDATED", "REVIEWED"]
    assert pr290["base_sha"] == pr290["predecessor_sealed_sha"] == BASE
    assert pr290["production_hash"] == PRODUCTION_HASH
    assert pr290["assurance_budget"] == {"maximum": 16, "consumed": 7}
    assert pr290["sealed_head"] is pr290["pushed_ref"] is pr290["pr_url"] is None
    assert all(value == "PASS" for value in pr290["gate_dispositions"].values())
    assert pr291["lifecycle"] == "PLANNED"
    assert pr291["gate_dispositions"] == {"eligibility": "INELIGIBLE"}
    assert pr291["assurance_budget"] == {"maximum": 16, "consumed": 0}
    assert 7 + 1 == 8 <= pr290["assurance_budget"]["maximum"]

    assert receipt["terminal"] == "BLOCKED_PREDECESSOR_FINAL_SUCCESS"
    assert receipt["numeric_outputs_written"] == []
    assert receipt["observed_data_executed"] is False
    assert receipt["network_or_download_side_effect"] is False
    assert receipt["public_use"] is False
    assert receipt["human_gate_snapshot"]["status"] == "NOT_AUTHORIZED"
    assert receipt["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
    assert receipt["owner_scope_and_claim_boundary"]["claim_tier"] == "diagnostic_only"
    assert receipt["owner_scope_and_claim_boundary"]["transfer_source"] == "none"
    assert receipt["source_bindings"]["docs/codex_handoff/pr_status.yaml"] == "sha256:" + REQUIRED_HASHES["docs/codex_handoff/pr_status.yaml"]

    assert (r1_code["status"], r1_phys["status"], r1_replay["status"]) == ("pass", "fail", "pass")
    assert r1_phys["findings"][0]["finding_id"] == "F-PR290-PHYSSTAT-SPEC-GUARD-GAP"
    assert (r2_phys["status"], r2_replay["status"]) == ("pass", "fail")
    assert r2_phys["candidate_binding"]["production_hash"] == PRODUCTION_HASH
    assert r2_replay["findings"][0]["finding_id"] == "PR290-R2-STALE-PORTABLE-MANIFEST"
    assert r3["status"] == "pass"
    assert r3["candidate_binding"]["candidate_sha"] == R3_HEAD
    assert r3["candidate_binding"]["production_hash"] == PRODUCTION_HASH
    assert any("2 fresh and 13 carried" in row.get("summary", "") for row in r3["commands"])

    coverage = load_json(COVERAGE_PATH)
    required_cells = policy["required_review_cells"]
    cells = coverage["cells"]
    assert coverage["required_cell_count"] == len(required_cells) == 15
    assert [row["cell_id"] for row in cells] == required_cells
    assert len({row["cell_id"] for row in cells}) == 15
    assert all(row["status"] == "PASS" for row in cells)
    assert [row["cell_id"] for row in cells if row["provenance"] == "fresh"] == [
        "candidate_identity", "latest_target_integration"
    ]
    assert sum(row["provenance"] == "carried" for row in cells) == 13
    assert coverage["missing_cells"] == [] and coverage["extra_cells"] == []

    remote_candidate = git(
        "for-each-ref",
        "--format=%(refname)",
        "refs/remotes/origin/changeset/pr290-planck-native-replay-recovery-20260811",
    ).decode().strip()
    assert remote_candidate == ""
    print("PASS: PR-290 final metadata closeout; 15 cells; projected budget 8/16")


if __name__ == "__main__":
    main()
