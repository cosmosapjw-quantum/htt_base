#!/usr/bin/env python3
"""Strictly validate and publish PR-171's four blind CAS receipts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pr171_cas_support import (
    ASSIGNMENT_IDS,
    AUTH_PATH,
    AXES,
    BLOCKED_STATUSES,
    COLLECTION_PATH,
    CONTRACT_PATH,
    REPO,
    assignment_self_hash,
    atomic_write,
    load,
    render,
    safe_rel,
    sha,
    validate_contract,
)


OUTPUT_ROOT = Path("docs/generated/pr171_cas/generation_2")


def _validate_axis(
    axis: str,
    run_dir: Path,
    contract: dict[str, Any],
    authorization: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[str]]:
    assignment_id = ASSIGNMENT_IDS[axis]
    assignment_path = REPO / run_dir / "assignments" / f"{assignment_id}.json"
    result_path = REPO / run_dir / "results" / f"{assignment_id}.json"
    errors: list[str] = []
    if not assignment_path.is_file() or not result_path.is_file():
        return None, None, [f"{axis}: assignment or result absent"]
    assignment = load(assignment_path)
    outer = load(result_path)
    contract_sha = sha(REPO / CONTRACT_PATH)
    auth_sha = sha(REPO / AUTH_PATH)
    if assignment.get("assignment_sha256") != assignment_self_hash(assignment):
        errors.append(f"{axis}: assignment self-hash mismatch")
    if authorization.get("assignments", {}).get(assignment_id) != sha(assignment_path):
        errors.append(f"{axis}: assignment differs from authorization")
    if assignment.get("cas_axis") != axis or assignment.get("independence_mode") != "blind-results":
        errors.append(f"{axis}: assignment axis/blinding mismatch")
    if assignment.get("allowed_sibling_results") != []:
        errors.append(f"{axis}: sibling results allowed")
    if assignment.get("cas_contract", {}).get("sha256") != contract_sha:
        errors.append(f"{axis}: assignment contract mismatch")
    if outer.get("schema_version") != 1 or outer.get("assignment_id") != assignment_id:
        errors.append(f"{axis}: outer schema/identity mismatch")
    if outer.get("run_id") != assignment.get("run_id") or outer.get("context_version") != assignment.get("context_version"):
        errors.append(f"{axis}: outer run/context mismatch")
    if outer.get("independence_mode") != "blind-results":
        errors.append(f"{axis}: outer independence mismatch")
    expected_path = str(run_dir / "results" / f"{assignment_id}.json")
    if outer.get("result_path") != expected_path:
        errors.append(f"{axis}: outer result path mismatch")
    nested = outer.get("payload", {}).get("cas_axis_result")
    if not isinstance(nested, dict):
        return assignment, outer, [*errors, f"{axis}: nested result absent"]
    if nested.get("axis") != axis or nested.get("contract_sha256") != contract_sha:
        errors.append(f"{axis}: nested axis/contract mismatch")
    if nested.get("preaxis_authorization_sha256") != auth_sha:
        errors.append(f"{axis}: nested authorization mismatch")
    if nested.get("sibling_results_read") != [] or nested.get("domain_assumption_diff") != []:
        errors.append(f"{axis}: blinding or assumption divergence")
    status = nested.get("status")
    commands = nested.get("commands")
    if not isinstance(commands, list) or not commands:
        errors.append(f"{axis}: command evidence absent")
        commands = []
    if outer.get("commands_run") != commands or outer.get("tool_versions") != nested.get("tool_versions"):
        errors.append(f"{axis}: outer/nested command or tool mismatch")
    checks = nested.get("checks")
    obligations = set(contract["target"]["exact_test_obligations"])
    if status == "PASS":
        if outer.get("status") != "pass" or any(row.get("exit") != 0 for row in commands):
            errors.append(f"{axis}: PASS outer/exit mismatch")
        if not isinstance(checks, dict) or set(checks) != obligations or not all(value is True for value in checks.values()):
            errors.append(f"{axis}: PASS obligation mismatch")
        if nested.get("computed") != contract["target"]["expected_exact_values"]:
            errors.append(f"{axis}: PASS canonical values mismatch")
        if nested.get("fixture_matches") is not True or nested.get("counterexample") is not None:
            errors.append(f"{axis}: PASS fixture/counterexample mismatch")
        if nested.get("precision_digits") != 80:
            errors.append(f"{axis}: high-precision receipt absent")
    elif status in BLOCKED_STATUSES:
        if outer.get("status") != "inconclusive" or not isinstance(nested.get("counterexample"), dict):
            errors.append(f"{axis}: blocked evidence malformed")
    elif status == "FAIL":
        if outer.get("status") != "fail" or not isinstance(nested.get("counterexample"), dict):
            errors.append(f"{axis}: FAIL evidence malformed")
    else:
        errors.append(f"{axis}: unknown nested status {status}")
    if nested.get("source_output_hashes") != contract["axes"][axis]["sources"]:
        errors.append(f"{axis}: axis source inventory mismatch")
    if nested.get("verified_input_hashes") != contract["identity"]["source_input_hashes"]:
        errors.append(f"{axis}: verified input inventory mismatch")
    for row in (nested.get("source_output_hashes") or []) + (nested.get("verified_input_hashes") or []):
        if not safe_rel(row.get("path")):
            errors.append(f"{axis}: unsafe evidence path")
            continue
        target = REPO / row["path"]
        if not target.is_file() or target.is_symlink() or sha(target) != row.get("sha256"):
            errors.append(f"{axis}: evidence hash mismatch {row.get('path')}")
    return assignment, outer, errors


def build(run_dir: Path) -> tuple[dict[str, bytes], dict[str, Any]]:
    contract = load(REPO / CONTRACT_PATH)
    authorization = load(REPO / AUTH_PATH)
    errors = validate_contract(contract)
    if authorization.get("axes_authorized") is not True or authorization.get("run_dir") != str(run_dir):
        errors.append("authorization inactive or run mismatch")
    if authorization.get("contract_sha256") != sha(REPO / CONTRACT_PATH):
        errors.append("authorization contract mismatch")
    if set(authorization.get("assignments", {})) != set(ASSIGNMENT_IDS.values()):
        errors.append("authorization assignment inventory mismatch")
    files: dict[str, bytes] = {}
    statuses: dict[str, str] = {}
    computed: dict[str, dict[str, str] | None] = {}
    receipt_hashes: dict[str, Any] = {}
    for axis in AXES:
        assignment, outer, axis_errors = _validate_axis(axis, run_dir, contract, authorization)
        errors.extend(axis_errors)
        if assignment is None or outer is None:
            statuses[axis] = "MISSING"
            computed[axis] = None
            continue
        nested = outer["payload"]["cas_axis_result"]
        statuses[axis] = nested["status"]
        computed[axis] = nested.get("computed")
        assignment_bytes = render(assignment)
        outer_bytes = render(outer)
        nested_bytes = render(nested)
        files[f"assignments/assignment_{axis}.json"] = assignment_bytes
        files[f"outer_results/outer_result_{axis}.json"] = outer_bytes
        files[f"axis_result_{axis}.json"] = nested_bytes
        receipt_hashes[axis] = {
            "assignment_sha256": sha(REPO / run_dir / "assignments" / f"{ASSIGNMENT_IDS[axis]}.json"),
            "outer_result_sha256": sha(REPO / run_dir / "results" / f"{ASSIGNMENT_IDS[axis]}.json"),
            "normalized_result_sha256": __import__("hashlib").sha256(nested_bytes).hexdigest(),
        }
    if errors:
        aggregate = "PROCESS_EVIDENCE_INVALID"
    elif any(value == "FAIL" for value in statuses.values()):
        aggregate = "CAS_FAIL"
    elif any(value in BLOCKED_STATUSES or value == "MISSING" for value in statuses.values()):
        aggregate = "CAS_BLOCKED"
    elif set(statuses.values()) != {"PASS"}:
        aggregate = "CAS_CONFLICT"
    elif len({json.dumps(value, sort_keys=True) for value in computed.values()}) != 1:
        aggregate = "CAS_CONFLICT"
    else:
        aggregate = "CAS_4AXIS_PASS"
    collection = {
        "schema": "htt.pr171.cas_collection.v1",
        "generation_id": "PR171-CAS-G2",
        "run_dir": str(run_dir),
        "contract_path": str(CONTRACT_PATH),
        "contract_sha256": sha(REPO / CONTRACT_PATH),
        "authorization_path": str(AUTH_PATH),
        "authorization_sha256": sha(REPO / AUTH_PATH),
        "axis_statuses": statuses,
        "aggregate_status": aggregate,
        "majority_vote_used": False,
        "registered_exception_used": False,
        "cross_generation_result_reuse": False,
        "receipt_hashes": receipt_hashes,
        "errors": errors,
    }
    files["adjudication.json"] = render(collection)
    return files, collection


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files, collection = build(args.run_dir)
    collection_bytes = render(collection)
    if args.write:
        for relative, data in files.items():
            atomic_write(REPO / OUTPUT_ROOT / relative, data)
        atomic_write(REPO / COLLECTION_PATH, collection_bytes)
    if args.check:
        mismatches = [
            str(OUTPUT_ROOT / relative)
            for relative, data in files.items()
            if not (REPO / OUTPUT_ROOT / relative).is_file()
            or (REPO / OUTPUT_ROOT / relative).read_bytes() != data
        ]
        if not (REPO / COLLECTION_PATH).is_file() or (REPO / COLLECTION_PATH).read_bytes() != collection_bytes:
            mismatches.append(str(COLLECTION_PATH))
        if mismatches:
            collection = {**collection, "check_mismatches": mismatches}
            print(json.dumps(collection, indent=2, sort_keys=True))
            return 2
    print(json.dumps(collection, indent=2, sort_keys=True))
    return 0 if collection["aggregate_status"] in {"CAS_4AXIS_PASS", "CAS_BLOCKED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
