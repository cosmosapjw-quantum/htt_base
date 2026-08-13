#!/usr/bin/env python3
"""Metadata-only closeout oracle for the frozen PR-291 clause continuation."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[4]
RUN = ".agent-harness/runs/pr291-r5-clause-continuation-20260813"

EXPECTED_INPUT_HASHES = {
    ".prguard/runtime/PR291_R5_CLAUSE_FINAL_CANDIDATE_SEAL.json":
        "035e67d7239778b553e3475b2bfd3aae782c4fe3a36f7d15d4523788b7482c19",
    "docs/research_program/post_pr275/pr291_publication_policy.json":
        "2354087be93139b2740ea8f6eeacc27f73a287d418fc35fcc012fcc6cf1fb835",
    "docs/codex_handoff/pr_status.yaml":
        "7e931173b3310306a1b03b259ef8414d1a24c2c465649894d80a0134571138e5",
    "machine_readable/pr_status.yaml":
        "7e931173b3310306a1b03b259ef8414d1a24c2c465649894d80a0134571138e5",
    f"{RUN}/results/A-PR291-R5-CLAUSE-CLAIM.json":
        "1f3415a0f1309f2288998691120de0d9e3586948290d567510526a6432fa9883",
}

EXPECTED_BINDING = {
    "base_sha": "06ac20605ebc371b0f97ad6e91c802a51a9bf764",
    "candidate_sha": "6c9d86a22394f512211cb42f9ef60d248f10ce20",
    "merge_base_sha": "06ac20605ebc371b0f97ad6e91c802a51a9bf764",
    "candidate_tree_sha": "4e40985666c5ea82d8d1bed3009f179e22aa12db",
    "diff_sha256": "0338828d09aa6698dd3464a6e7eecb226a90444260a98a5dfc439f0f8e43672a",
    "changed_files_sha256": "c99638c4a52a040e9f8678b3f453284a356b74bd0a09320936aa6fd51435beb3",
    "production_hash": "264931c49f4cd6d0850f1e46b3ba9b441596f7486067e25361cf4aca96a61695",
}

EXPECTED_CF4_HASHES = {
    "pr291_common_module": "4b15529947ea6269bc0ff38b7a58e5433fc6e767e34b732e2ee37cfac07bbeb0",
    "pr291_obsstat_module": "6a3ae13200b381af4502ef0ec0f001c039727a9dcfc1dd49e239a9f0c64e56bb",
    "pr291_runner": "45659be3d9801697272726d1cf8018d3719a7d83127fc89d05781c30db239af8",
    "pr291_contract_test": "ca827a64d0ddc15a7c9072e5163bc6e76236d47e0eca2672f8d25c0d86574ed8",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, check=True, capture_output=True, text=True
    ).stdout.strip()


def main() -> None:
    checks: list[str] = []
    for relative, expected in EXPECTED_INPUT_HASHES.items():
        actual = sha256(REPO / relative)
        assert actual == expected, f"input drift: {relative}: {actual}"
        checks.append(f"input_sha256:{relative}")

    seal = json.loads(
        (REPO / ".prguard/runtime/PR291_R5_CLAUSE_FINAL_CANDIDATE_SEAL.json").read_text()
    )
    for field, expected in EXPECTED_BINDING.items():
        assert seal[field] == expected, f"seal {field} drifted"
    assert seal["seal_sha256"] == "ad585eb8f93a6bef8cbad27c4ef27ca20253e786f226101a8774cf6beb07d070"
    assert seal["dirty"] is False
    assert git("rev-parse", "HEAD") == EXPECTED_BINDING["candidate_sha"]
    assert git("rev-parse", "HEAD^{tree}") == EXPECTED_BINDING["candidate_tree_sha"]
    assert git("merge-base", "HEAD", EXPECTED_BINDING["base_sha"]) == EXPECTED_BINDING["merge_base_sha"]
    assert git("status", "--short", "--untracked-files=no") == ""
    checks.append("frozen_candidate_identity")

    canonical_status_bytes = (REPO / "docs/codex_handoff/pr_status.yaml").read_bytes()
    mirror_status_bytes = (REPO / "machine_readable/pr_status.yaml").read_bytes()
    assert canonical_status_bytes == mirror_status_bytes
    status = yaml.safe_load(canonical_status_bytes)
    stack = status["stacked_pr_execution"]
    pr291 = stack["prs"]["PR-291"]
    pr292 = stack["prs"]["PR-292"]
    assert stack["merge_policy"] == "HUMAN_ONLY"
    assert pr291["lifecycle"] == "VALIDATED"
    assert pr291["lifecycle_history"] == ["PLANNED", "ACTIVE", "IMPLEMENTED", "VALIDATED"]
    assert pr291["sealed_head"] is None
    assert pr291["pushed_ref"] is None
    assert pr291["pr_url"] is None
    assert pr291["production_hash"] == EXPECTED_BINDING["production_hash"]
    for field, expected in EXPECTED_CF4_HASHES.items():
        assert pr291["dependency_hashes"][field] == expected, f"CF4 hash drift: {field}"
    assert pr291["assurance_clause_continuation_id"] == "PR291-R5-CLAUSE-CONTINUATION-20260813"
    assert pr291["authorized_assurance_clause_continuation_maximum"] == 2
    assert pr291["authorized_assurance_clause_continuation_consumed"] == 0
    assert pr292["lifecycle"] == "PLANNED"
    assert pr292["gate_dispositions"] == {"eligibility": "INELIGIBLE"}
    assert pr292["assurance_budget"] == {"maximum": 16, "consumed": 0}
    assert pr292["sealed_head"] is None
    assert pr292["pushed_ref"] is None
    assert pr292["pr_url"] is None
    checks.extend(["status_mirrors", "pr291_validated", "pr292_ineligible_zero_budget", "human_only_no_publication"])

    policy = json.loads(
        (REPO / "docs/research_program/post_pr275/pr291_publication_policy.json").read_text()
    )
    assert policy["ordinary_agent_push_forbidden"] is True
    assert policy["ordinary_agent_pr_mutation_forbidden"] is True
    assert policy["attended_publication"]["forbidden_actions"] == [
        "force_push", "approve", "merge", "ruleset_mutation"
    ]
    assert policy["claim_ceiling"] == "diagnostic_only"
    assert policy["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
    checks.append("publication_and_claim_ceiling")

    claim = json.loads(
        (REPO / RUN / "results/A-PR291-R5-CLAUSE-CLAIM.json").read_text()
    )
    assert claim["status"] == "fail"
    assert claim["gate_disposition"] == "FAIL"
    assert len(claim["findings"]) == 1
    finding = claim["findings"][0]
    assert finding["finding_id"] == "F-PR291-CLAUSE-NEGATION-ORDER"
    assert finding["claim_id"] == "C-PR274-DATA-ADMISSION"
    assert finding["verdict"] == "fail"
    assert finding["evidence_fingerprint"] == "sha256:51821f3446e411f9c0262d202fd6e015c5d70e2891290848d1907c4c84f50bf4"
    assert claim["claim_results"] == [{
        "claim_id": "C-PR274-DATA-ADMISSION",
        "outcome": "findings_present",
        "finding_ids": ["F-PR291-CLAUSE-NEGATION-ORDER"],
        "summary": claim["claim_results"][0]["summary"],
    }]
    checks.append("single_claim_failure")

    print(json.dumps({"status": "PASS", "checks": checks}, sort_keys=True))


if __name__ == "__main__":
    main()
