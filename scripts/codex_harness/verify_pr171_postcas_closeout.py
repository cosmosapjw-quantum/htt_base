#!/usr/bin/env python3
"""Verify the additive PR-171 erratum and publish the terminal closeout seal."""

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
ERRATUM = Path("docs/research_program/long_horizon_rescue/pr171_spec_erratum.yaml")
SPEC = Path("docs/research_program/long_horizon_rescue/pr171_spec.yaml")
CONTRACT = Path("docs/generated/pr171_cas/CAS_CONTRACT_PR171_CLASS_CONDITIONAL_TILT_V3.json")
AUTH = Path("docs/generated/pr171_cas/preaxis_authorization_v3.json")
COLLECTION = Path("docs/generated/pr171_cas_collection_receipt.json")
ADJUDICATOR = Path("docs/generated/pr171_reviews/adjudicator.json")
REVIEW_MANIFEST = Path("docs/generated/pr171_reviews/manifest.json")
RESULT = Path("docs/generated/pr171_result_card.json")
COUNTEREXAMPLE = Path("docs/generated/pr171_source_counterexample.json")
OUTPUT = Path("docs/generated/pr171_postcas_contract_review.json")
CLOSEOUT = Path("docs/generated/pr171_closeout_manifest.json")
BASE_ARTIFACTS = (
    Path("docs/generated/pr171_exact_mechanics.json"),
    COUNTEREXAMPLE,
    Path("docs/generated/pr171_source_space_closure.json"),
    Path("docs/generated/pr171_mutation_report.json"),
    RESULT,
    Path("docs/generated/pr171_artifact_manifest.json"),
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected YAML object: {path}")
    return value


def _render(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False) as handle:
        handle.write(data)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def build() -> tuple[dict[str, Any], dict[str, Any]]:
    erratum = _yaml(REPO / ERRATUM)
    contract = _json(REPO / CONTRACT)
    authorization = _json(REPO / AUTH)
    collection = _json(REPO / COLLECTION)
    adjudicator = _json(REPO / ADJUDICATOR)
    review_manifest = _json(REPO / REVIEW_MANIFEST)
    result = _json(REPO / RESULT)
    counterexample = _json(REPO / COUNTEREXAMPLE)
    errors: list[str] = []
    bound = (
        ("frozen_spec", SPEC),
        ("frozen_contract", CONTRACT),
        ("adjudicator", ADJUDICATOR),
    )
    for key, path in bound:
        row = erratum.get(key, {})
        if row.get("path") != str(path) or row.get("sha256") != _sha(REPO / path):
            errors.append(f"erratum {key} binding mismatch")
    if collection.get("aggregate_status") != "CAS_4AXIS_PASS" or collection.get("errors") != []:
        errors.append("generation-3 collection is not clean CAS_4AXIS_PASS")
    if collection.get("cross_generation_result_reuse") is not False or collection.get("majority_vote_used") is not False:
        errors.append("collection reuse/majority guard failed")
    if authorization.get("result_router_sha256") != _sha(REPO / authorization["result_router_path"]):
        errors.append("pre-axis-bound result router drifted")
    if review_manifest.get("copy_mode") != "byte_for_byte" or review_manifest.get("review_count") != 4:
        errors.append("review archive is incomplete or not byte-for-byte")
    review_rows = review_manifest.get("reviews", [])
    for row in review_rows:
        destination = REPO / row.get("destination_path", "")
        if not destination.is_file() or _sha(destination) != row.get("sha256"):
            errors.append(f"review archive hash mismatch: {row.get('role', 'unknown')}")
    finding = next(
        (row for row in adjudicator.get("findings", []) if row.get("finding_id") == "F-PR171-ADJ-FIXTURE-LABEL-DRIFT"),
        None,
    )
    if not isinstance(finding, dict) or "erratum" not in str(finding.get("required_fix", "")):
        errors.append("adjudicator did not authorize the additive erratum route")
    interpretation = erratum.get("interpretation", {})
    alternate = interpretation.get("unregistered_source_only_alternate", {})
    sealed = interpretation.get("sole_generation_3_cas_sealed_fixture", {})
    if alternate != {
        "gamma": "7/6", "w": "1/6",
        "status": "covered_by_externally_attributed_1_less_than_gamma_less_than_2_interval_only",
        "cas_sealed": False,
    }:
        errors.append("alternate source point is not strictly unsealed")
    if sealed != {"gamma": "5/4", "w": "1/4", "Gamma": 0, "cas_sealed": True}:
        errors.append("sole CAS-sealed fixture is not exact")
    fixture = counterexample.get("fixture", {})
    if fixture.get("gamma") != "5/4" or fixture.get("w") != "1/4" or fixture.get("Gamma") != "0":
        errors.append("generated counterexample fixture differs from sealed fixture")
    if result.get("blanket_no_go_status") != "RETIRED_BY_AUTHENTICATED_EXTERNAL_SOURCE":
        errors.append("result did not retire the blanket no-go")
    if result.get("suppression_result") is not None or result.get("suppression_status") != "SUPPRESSION_CEILING_NOT_IDENTIFIED":
        errors.append("result invented a suppression ceiling")
    if result.get("exact_stability_result") != "LOCAL_LINEAR_STABLE_IN_FROZEN_DRAG_CLASS":
        errors.append("result lost the class-conditional stability qualifier")
    if result.get("public_use") is not False:
        errors.append("result public-use quarantine failed")
    review = {
        "schema": "htt.pr171.postcas_contract_review.v1",
        "pr_id": "PR-171",
        "claim_id": "C-PR171-CLASS-CONDITIONAL-STABILITY",
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "conditional",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C2"},
        "scientific_artifact_mode": "hypothesis_only",
        "transfer_source": "none",
        "config_hash": _sha(REPO / SPEC),
        "input_hashes": {
            str(CONTRACT): _sha(REPO / CONTRACT),
            str(COLLECTION): _sha(REPO / COLLECTION),
            str(ADJUDICATOR): _sha(REPO / ADJUDICATOR),
            str(ERRATUM): _sha(REPO / ERRATUM),
            str(RESULT): _sha(REPO / RESULT),
            str(REVIEW_MANIFEST): _sha(REPO / REVIEW_MANIFEST),
        },
        "sky_support_status": "not_applicable_exact_mechanics",
        "mask_status": "not_applicable_exact_mechanics",
        "covariance_status": "not_applicable",
        "null_mock_status": "not_applicable",
        "generating_command": "venv/bin/python -B scripts/codex_harness/verify_pr171_postcas_closeout.py --write",
        "git_commit": result.get("git_commit"),
        "worktree_state": result.get("worktree_state"),
        "contract_sha256": _sha(REPO / CONTRACT),
        "collection_sha256": _sha(REPO / COLLECTION),
        "adjudicator_sha256": _sha(REPO / ADJUDICATOR),
        "erratum_path": str(ERRATUM),
        "erratum_sha256": _sha(REPO / ERRATUM),
        "bound_inputs_unchanged": not any("binding mismatch" in item or "drifted" in item for item in errors),
        "sole_cas_sealed_fixture": {"gamma": "5/4", "w": "1/4", "Gamma": "0"},
        "unregistered_source_only_alternate": {"gamma": "7/6", "w": "1/6"},
        "exact_cas_status": collection.get("aggregate_status"),
        "scientific_result": result.get("scientific_result"),
        "blanket_no_go_status": result.get("blanket_no_go_status"),
        "suppression_status": result.get("suppression_status"),
        "unresolved": ["generic dark-sector closure", "nonlinear shear closure", "khronon shear-leakage bridge", "numerical suppression ceiling"],
        "public_use": False,
        "caveats": [
            "5/4 is the sole CAS-sealed fixture",
            "7/6 is source-only and unsealed",
            "no universal or observational claim",
        ],
        "errors": errors,
        "terminal_ready": not errors,
    }
    rows = []
    for path in (
        SPEC, ERRATUM, CONTRACT, AUTH, COLLECTION, REVIEW_MANIFEST, ADJUDICATOR,
        Path("docs/generated/pr171_reviews/claim_gate.json"),
        Path("docs/generated/pr171_reviews/harness.json"),
        Path("docs/generated/pr171_reviews/physics_statistics.json"),
        Path("docs/generated/pr171_source_verification.json"),
        *BASE_ARTIFACTS,
        Path("docs/generated/pr171_cas/generation_1/adjudication.json"),
        Path("docs/generated/pr171_cas/generation_2/adjudication.json"),
        Path("docs/generated/pr171_cas/generation_3/adjudication.json"),
    ):
        rows.append({"path": str(path), "sha256": _sha(REPO / path), "bytes": (REPO / path).stat().st_size})
    review_bytes = _render(review)
    rows.append({"path": str(OUTPUT), "sha256": hashlib.sha256(review_bytes).hexdigest(), "bytes": len(review_bytes)})
    closeout = {
        "schema": "htt.pr171.closeout_manifest.v1",
        "pr_id": "PR-171",
        "owner": "COMMON",
        "implementation_scope": "common",
        "terminal_ready": review["terminal_ready"],
        "process_gate_status": "PASS" if review["terminal_ready"] else "FAIL",
        "scientific_result": review["scientific_result"] if review["terminal_ready"] else None,
        "claim_tier": "conditional",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C2"},
        "scientific_artifact_mode": "hypothesis_only",
        "public_use": False,
        "transfer_source": "none",
        "config_hash": _sha(REPO / SPEC),
        "input_hashes": {row["path"]: row["sha256"] for row in rows},
        "sky_support_status": "not_applicable_exact_mechanics",
        "mask_status": "not_applicable_exact_mechanics",
        "covariance_status": "not_applicable",
        "null_mock_status": "not_applicable",
        "git_commit": result.get("git_commit"),
        "worktree_state": result.get("worktree_state"),
        "artifacts": rows,
        "generating_command": "venv/bin/python -B scripts/codex_harness/verify_pr171_postcas_closeout.py --write",
        "caveats": ["5/4 is the sole CAS-sealed fixture", "7/6 is source-only and unsealed", "no universal or observational claim"],
    }
    return review, closeout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    review, closeout = build()
    expected = {OUTPUT: _render(review), CLOSEOUT: _render(closeout)}
    mismatches: list[str] = []
    for path, data in expected.items():
        if args.write:
            _write(REPO / path, data)
        if args.check and (not (REPO / path).is_file() or (REPO / path).read_bytes() != data):
            mismatches.append(str(path))
    print(json.dumps({"ok": review["terminal_ready"] and not mismatches, "errors": review["errors"], "mismatches": mismatches, "scientific_result": review["scientific_result"]}, indent=2, sort_keys=True))
    return 0 if review["terminal_ready"] and not mismatches else 2


if __name__ == "__main__":
    raise SystemExit(main())
