#!/usr/bin/env python3
"""Verify PR-172 review remediation and emit a terminal closeout receipt."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import yaml


REPO = Path(__file__).resolve().parents[2]
SPEC = Path("docs/research_program/long_horizon_rescue/pr172_spec.yaml")
RESULT = Path("docs/generated/pr172_metamorphic_result.json")
MUTATIONS = Path("docs/generated/pr172_mutation_report.json")
REPLAY = Path("docs/generated/pr172_replay_receipt.json")
CARD = Path("docs/generated/pr172_result_card.json")
MANIFEST = Path("docs/generated/pr172_artifact_manifest.json")
REVIEW_MANIFEST = Path("docs/generated/pr172_reviews/manifest.json")
OUTPUT = Path("docs/generated/pr172_closeout_review_receipt.json")
SCRIPT = Path("scripts/codex_harness/verify_pr172_closeout.py")
PRODUCTION_ARTIFACTS = (
    Path("docs/generated/pr172_metamorphic_relation_registry.json"),
    RESULT,
    MUTATIONS,
    REPLAY,
    Path("docs/generated/pr172_co04_delta.json"),
    CARD,
    MANIFEST,
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _render(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False) as handle:
        handle.write(data)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def build() -> dict[str, Any]:
    spec = yaml.safe_load((REPO / SPEC).read_text(encoding="utf-8"))
    result = _json(REPO / RESULT)
    mutations = _json(REPO / MUTATIONS)
    replay = _json(REPO / REPLAY)
    card = _json(REPO / CARD)
    manifest = _json(REPO / MANIFEST)
    reviews = _json(REPO / REVIEW_MANIFEST)
    errors: list[str] = []

    expected_statuses = {
        "claim_gate": "pass",
        "harness": "pass",
        "physics_statistics": "fail",
        "final_code": "fail",
        "final_science": "pass",
        "final_claim": "fail",
        "remediation_code": "pass",
        "remediation_claim": "pass",
    }
    actual_statuses = {row.get("role"): row.get("status") for row in reviews.get("reviews", [])}
    if actual_statuses != expected_statuses:
        errors.append("review status history mismatch")
    if reviews.get("copy_mode") != "byte_for_byte" or reviews.get("review_count") != 8:
        errors.append("review archive is incomplete")
    for row in reviews.get("reviews", []):
        destination = REPO / str(row.get("destination_path", ""))
        if not destination.is_file() or _sha(destination) != row.get("sha256"):
            errors.append(f"review hash mismatch: {row.get('role')}")

    if result.get("terminal") != "BLOCKED_METAMORPHIC_RELATION_VIOLATION":
        errors.append("scientific terminal drift")
    if result.get("adapter_status") != {
        "cf4_estimator": "PASS_REGISTERED_RELATIONS",
        "b_projector": "BLOCKED_METAMORPHIC_RELATION_VIOLATION",
    }:
        errors.append("per-adapter disposition drift")
    if card.get("success_dependency_satisfied") is not False:
        errors.append("blocked result satisfied a success dependency")
    if card.get("physical_b_parity_status") != "UNDERDEFINED_NOT_TESTED":
        errors.append("physical parity status drift")
    if mutations.get("registered_count") != 7 or mutations.get("executed_count") != 7:
        errors.append("mutation inventory/execution mismatch")
    if mutations.get("killed_count") != 7 or mutations.get("survivors") != []:
        errors.append("mutation survivor mismatch")
    if replay.get("fresh_processes") != 2 or replay.get("digests_match") is not True:
        errors.append("deterministic replay mismatch")
    if replay.get("semantic_digests") != [result.get("semantic_digest")] * 2:
        errors.append("replay digest differs from primary result")

    artifact_rows = manifest.get("artifacts", [])
    if manifest.get("artifact_count") != len(artifact_rows) or len(artifact_rows) != 6:
        errors.append("artifact manifest inventory mismatch")
    for row in artifact_rows:
        path = REPO / str(row.get("path", ""))
        if not path.is_file() or _sha(path) != row.get("sha256") or path.stat().st_size != row.get("bytes"):
            errors.append(f"artifact hash/size mismatch: {row.get('path')}")
    for path, expected in result.get("input_hashes", {}).items():
        candidate = REPO / path
        if not candidate.is_file() or _sha(candidate) != expected:
            errors.append(f"primary input hash mismatch: {path}")

    forbidden_hits: list[str] = []
    for phrase in spec.get("forbidden_output_language", []):
        needle = str(phrase).casefold()
        for path in PRODUCTION_ARTIFACTS:
            if needle in (REPO / path).read_text(encoding="utf-8").casefold():
                forbidden_hits.append(f"{path}:{phrase}")
    if forbidden_hits:
        errors.append("registered forbidden output wording is present")

    input_paths = (
        SPEC,
        RESULT,
        MUTATIONS,
        REPLAY,
        CARD,
        MANIFEST,
        REVIEW_MANIFEST,
        Path("docs/generated/pr172_reviews/final_code.json"),
        Path("docs/generated/pr172_reviews/final_claim.json"),
        Path("docs/generated/pr172_reviews/remediation_code.json"),
        Path("docs/generated/pr172_reviews/remediation_claim.json"),
        Path("htt/src/common/metamorphic_symmetry.py"),
        Path("scripts/codex_harness/run_pr172_metamorphic_battery.py"),
        SCRIPT,
    )
    input_hashes = {str(path): _sha(REPO / path) for path in input_paths}
    content_receipt = hashlib.sha256(
        json.dumps(input_hashes, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "schema": "htt.pr172.closeout_review.v1",
        "pr_id": "PR-172",
        "claim_id": "C-PR172-METAMORPHIC-CONSISTENCY",
        "owner": "COMMON",
        "contributors": ["OBSSTAT"],
        "implementation_scope": "common",
        "claim_tier": "exploratory",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C1"},
        "scientific_artifact_mode": "standard_internal",
        "scientific_status": "OPEN",
        "public_use": False,
        "transfer_source": "none",
        "config_hash": _sha(REPO / SPEC),
        "input_hashes": input_hashes,
        "worktree_content_receipt": content_receipt,
        "sky_support_status": "synthetic_fixture_not_observed_sky",
        "mask_status": "not_applicable_synthetic_fixture",
        "covariance_status": "mechanics_only_not_covariance_validation",
        "null_mock_status": "not_run_not_applicable",
        "generating_command": "venv/bin/python -B scripts/codex_harness/verify_pr172_closeout.py --write",
        "git_commit": result.get("git_commit"),
        "worktree_state": f"{result.get('git_commit')}+content-sha256:{content_receipt}",
        "terminal_ready": not errors,
        "process_execution_status": "PASS" if not errors else "FAIL",
        "scientific_terminal": result.get("terminal"),
        "success_dependency_satisfied": False,
        "review_status_history": expected_statuses,
        "preserved_failed_reviews": ["physics_statistics", "final_code", "final_claim"],
        "remediation_reviews": ["remediation_code", "remediation_claim"],
        "remediated_finding_ids": [
            "F-PR172-FINAL-CODE-001",
            "F-PR172-FINAL-CODE-002",
            "F-PR172-FINAL-CODE-003",
            "F-PR172-FINAL-CLAIM-001",
            "F-PR172-FINAL-CLAIM-002",
        ],
        "forbidden_output_hits": forbidden_hits,
        "errors": errors,
        "caveats": [
            "The closeout validates a reproducible blocked result; it does not turn PR-172 into a successful dependency.",
            "Earlier FAIL reviews remain immutable evidence and are not relabeled by later remediation passes.",
            "Physical spin-harmonic parity remains underdefined and untested.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    receipt = build()
    data = _render(receipt)
    if args.write:
        _write(REPO / OUTPUT, data)
    mismatches = []
    if args.check:
        if not (REPO / OUTPUT).is_file():
            mismatches.append(f"missing:{OUTPUT}")
        elif (REPO / OUTPUT).read_bytes() != data:
            mismatches.append(f"stale:{OUTPUT}")
    print(
        json.dumps(
            {
                "ok": receipt["terminal_ready"] and not mismatches,
                "terminal": receipt["scientific_terminal"],
                "mismatches": mismatches,
                "errors": receipt["errors"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if receipt["terminal_ready"] and not mismatches else 2


if __name__ == "__main__":
    raise SystemExit(main())
