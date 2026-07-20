#!/usr/bin/env python3
"""Create/check the immutable PR-171 generation-1 pre-axis authorization."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pr171_cas_support import (
    ASSIGNMENT_IDS,
    AUTH_PATH,
    CONTRACT_PATH,
    REPO,
    assignment_self_hash,
    atomic_write,
    load,
    render,
    sha,
    validate_contract,
)
from verify_pr171_sources import verify as verify_sources


RUNNER = Path("scripts/codex_harness/run_pr171_axis.py")
COLLECTOR = Path("scripts/codex_harness/collect_pr171_cas_receipts.py")
RESULT_ROUTER = Path("scripts/codex_harness/run_pr171_tilt_relaxation.py")
SUPPORT = Path("scripts/codex_harness/pr171_cas_support.py")
SOURCE_VERIFIER = Path("scripts/codex_harness/verify_pr171_sources.py")


def build(run_dir: Path, *, require_results_absent: bool) -> dict[str, Any]:
    contract = load(REPO / CONTRACT_PATH)
    errors = validate_contract(contract)
    source_receipt = verify_sources(require_raw=True)
    if source_receipt.get("ok") is not True:
        errors.extend(source_receipt.get("errors", []))
    assignments: dict[str, str] = {}
    context_versions: set[str] = set()
    result_prestate: dict[str, str] = {}
    for axis, assignment_id in ASSIGNMENT_IDS.items():
        assignment_path = REPO / run_dir / "assignments" / f"{assignment_id}.json"
        result_path = REPO / run_dir / "results" / f"{assignment_id}.json"
        if not assignment_path.is_file():
            errors.append(f"missing assignment {assignment_id}")
            continue
        assignment = load(assignment_path)
        assignments[assignment_id] = sha(assignment_path)
        context_versions.add(str(assignment.get("context_version")))
        if assignment.get("assignment_sha256") != assignment_self_hash(assignment):
            errors.append(f"{assignment_id}: self-hash mismatch")
        if assignment.get("cas_axis") != axis:
            errors.append(f"{assignment_id}: axis mismatch")
        if assignment.get("independence_mode") != "blind-results" or assignment.get("allowed_sibling_results") != []:
            errors.append(f"{assignment_id}: independence violation")
        if assignment.get("cas_contract", {}).get("sha256") != sha(REPO / CONTRACT_PATH):
            errors.append(f"{assignment_id}: contract mismatch")
        expected_result = str(run_dir / "results" / f"{assignment_id}.json")
        if assignment.get("result_path") != expected_result:
            errors.append(f"{assignment_id}: noncanonical result path")
        result_prestate[assignment_id] = "absent" if not result_path.exists() else "present"
        if require_results_absent and result_path.exists():
            errors.append(f"{assignment_id}: result existed before authorization")
    if len(context_versions) != 1:
        errors.append("assignments do not share exactly one context version")
    payload = {
        "schema": "htt.pr171.preaxis_authorization.v1",
        "generation_id": "PR171-CAS-G3",
        "run_dir": str(run_dir),
        "context_version": next(iter(context_versions), None) if len(context_versions) == 1 else None,
        "contract_path": str(CONTRACT_PATH),
        "contract_sha256": sha(REPO / CONTRACT_PATH),
        "runner_path": str(RUNNER),
        "runner_sha256": sha(REPO / RUNNER),
        "collector_path": str(COLLECTOR),
        "collector_sha256": sha(REPO / COLLECTOR),
        "result_router_path": str(RESULT_ROUTER),
        "result_router_sha256": sha(REPO / RESULT_ROUTER),
        "support_path": str(SUPPORT),
        "support_sha256": sha(REPO / SUPPORT),
        "source_verifier_path": str(SOURCE_VERIFIER),
        "source_verifier_sha256": sha(REPO / SOURCE_VERIFIER),
        "assignments": assignments,
        "result_preauthorization_state": result_prestate,
        "all_results_absent_before_authorization": set(result_prestate.values()) == {"absent"},
        "source_verification_sha256": sha(REPO / "docs/generated/pr171_source_verification.json"),
        "source_verification": source_receipt,
        "errors": errors,
        "axes_authorized": not errors and len(assignments) == 4,
        "scope": "generation-scoped process authorization and input integrity only; not scientific validation",
    }
    return payload


def _validate_stored(existing: dict[str, Any], run_dir: Path) -> list[str]:
    errors: list[str] = []
    if existing.get("run_dir") != str(run_dir) or existing.get("generation_id") != "PR171-CAS-G3":
        errors.append("stored authorization run/generation mismatch")
    bindings = {
        "contract_sha256": CONTRACT_PATH,
        "runner_sha256": RUNNER,
        "collector_sha256": COLLECTOR,
        "result_router_sha256": RESULT_ROUTER,
        "support_sha256": SUPPORT,
        "source_verifier_sha256": SOURCE_VERIFIER,
        "source_verification_sha256": Path("docs/generated/pr171_source_verification.json"),
    }
    for field, path in bindings.items():
        if not (REPO / path).is_file() or existing.get(field) != sha(REPO / path):
            errors.append(f"stored binding drift: {field}")
    for assignment_id, expected in existing.get("assignments", {}).items():
        path = REPO / run_dir / "assignments" / f"{assignment_id}.json"
        if not path.is_file() or sha(path) != expected:
            errors.append(f"stored assignment drift: {assignment_id}")
    if existing.get("all_results_absent_before_authorization") is not True:
        errors.append("stored receipt does not prove absent pre-axis results")
    if existing.get("errors") != [] or existing.get("axes_authorized") is not True:
        errors.append("stored authorization was not clean")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.write:
        payload = build(args.run_dir, require_results_absent=True)
        atomic_write(REPO / AUTH_PATH, render(payload))
        print(json.dumps({"axes_authorized": payload["axes_authorized"], "errors": payload["errors"], "path": str(AUTH_PATH)}, indent=2, sort_keys=True))
        return 0 if payload["axes_authorized"] else 2
    if args.check:
        if not (REPO / AUTH_PATH).is_file():
            print(json.dumps({"ok": False, "errors": ["authorization absent"]}))
            return 2
        existing = load(REPO / AUTH_PATH)
        errors = _validate_stored(existing, args.run_dir)
        print(json.dumps({"ok": not errors, "errors": errors}, indent=2, sort_keys=True))
        return 0 if not errors else 2
    payload = build(args.run_dir, require_results_absent=False)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["axes_authorized"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
