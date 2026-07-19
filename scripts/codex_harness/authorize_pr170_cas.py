#!/usr/bin/env python3
"""Create/check PR-170's content-addressed pre-axis authorization receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from verify_pr170_sources import verify as verify_sources

try:
    from .run_pr170_axis import _validate_contract
except ImportError:  # direct script execution
    from run_pr170_axis import _validate_contract


REPO = Path(__file__).resolve().parents[2]
CONTRACT_PATH = Path("docs/generated/pr170_cas/CAS_CONTRACT_PR170_BUCHERT_TWO_PATCH.json")
RUNNER_PATH = Path("scripts/codex_harness/run_pr170_axis.py")
OUTPUT_PATH = Path("docs/generated/pr170_cas/preaxis_authorization.json")
ASSIGNMENTS = (
    "A-PR170-CAS-WOLFRAM",
    "A-PR170-CAS-SYMPY",
    "A-PR170-CAS-SAGE",
    "A-PR170-CAS-LEAN",
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def build(run_dir: Path) -> dict[str, Any]:
    contract = _load(REPO / CONTRACT_PATH)
    errors: list[str] = _validate_contract(contract)
    assignment_hashes: dict[str, str] = {}
    context_versions: set[str] = set()
    for assignment_id in ASSIGNMENTS:
        path = REPO / run_dir / "assignments" / f"{assignment_id}.json"
        if not path.is_file():
            errors.append(f"missing assignment {assignment_id}")
            continue
        assignment = _load(path)
        assignment_hashes[assignment_id] = _sha(path)
        context_versions.add(str(assignment.get("context_version")))
        if assignment.get("independence_mode") != "blind-results":
            errors.append(f"{assignment_id}: not blind-results")
        if assignment.get("allowed_sibling_results") != []:
            errors.append(f"{assignment_id}: sibling results allowed")
        if assignment.get("cas_contract", {}).get("sha256") != _sha(REPO / CONTRACT_PATH):
            errors.append(f"{assignment_id}: stale contract")
    if len(context_versions) != 1:
        errors.append("assignments do not share exactly one context version")
    source_receipt = verify_sources(require_raw=True)
    if not source_receipt["ok"]:
        errors.extend(source_receipt["errors"])
    for row in contract.get("identity", {}).get("source_input_hashes", []):
        path = REPO / row["path"]
        if not path.is_file() or _sha(path) != row["sha256"]:
            errors.append(f"contract source input mismatch: {row['path']}")
    for details in contract.get("axes", {}).values():
        for row in details.get("sources", []):
            path = REPO / row["path"]
            if not path.is_file() or _sha(path) != row["sha256"]:
                errors.append(f"axis source mismatch: {row['path']}")
    return {
        "schema": "htt.pr170.preaxis_authorization.v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "run_dir": str(run_dir),
        "context_version": next(iter(context_versions), None) if len(context_versions) == 1 else None,
        "contract_path": str(CONTRACT_PATH),
        "contract_sha256": _sha(REPO / CONTRACT_PATH),
        "runner_path": str(RUNNER_PATH),
        "runner_sha256": _sha(REPO / RUNNER_PATH),
        "assignments": assignment_hashes,
        "source_verification": source_receipt,
        "errors": errors,
        "axes_authorized": not errors and len(assignment_hashes) == 4,
        "scope": "authorization and tool-input integrity only; not scientific validation",
    }


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload = build(args.run_dir)
    if args.check:
        if not (REPO / OUTPUT_PATH).is_file():
            print(json.dumps({"ok": False, "errors": ["authorization receipt absent"]}, indent=2))
            return 2
        existing = _load(REPO / OUTPUT_PATH)
        # Timestamps are evidence, so check stable identity fields only.
        ignored = {"created_at_utc"}
        errors = [
            key for key in payload if key not in ignored and existing.get(key) != payload.get(key)
        ]
        print(json.dumps({"ok": not errors, "mismatched_fields": errors}, indent=2, sort_keys=True))
        return 0 if not errors else 2
    _write(REPO / OUTPUT_PATH, payload)
    print(json.dumps({"axes_authorized": payload["axes_authorized"], "path": str(OUTPUT_PATH)}, sort_keys=True))
    return 0 if payload["axes_authorized"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
