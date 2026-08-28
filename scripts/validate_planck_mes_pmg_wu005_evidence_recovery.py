#!/usr/bin/env python3
"""Validate the PMG-WU-005 evidence-recovery execution binding."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

import yaml

ROOT = Path(__file__).resolve().parents[1]
PKG_REL = Path("docs/codex_handoff/planck_mes_pmg_wu005_evidence_recovery")
PKG = ROOT / PKG_REL
PACKAGE_ID = "PLANCK_MES_PMG_WU005_EVIDENCE_RECOVERY_20260828"
EXECUTED_SHA = "dded7702f319191e2dd1a88a7a25c64353ea3fb8"
EXECUTED_TREE = "318dae5fa3535d0f3d4e32c3558aa6bc8d0058bc"
REPAIR_SEED_SHA = "28ab4a5750550deb5b581d845e71d591e85dfa60"
REPAIR_SEED_TREE = "648872bf7dc0396ba57678df85d1329af82d9003"
BRANCH = "changeset/planck-mes-paired300-evidence-repair-v2-20260828"
EXPECTED_FILES = {
    "PACKAGE_INDEX.yaml",
    "AUTHORITY_AND_SCOPE.yaml",
    "RECOVERY_CONTRACT.yaml",
    "P0_P1_THREAT_CATALOG.json",
    "INVARIANT_TEST_MATRIX.yaml",
    "LOCAL_CHECKPOINT_AND_CLEANUP.yaml",
    "GUIDE_BINDING.yaml",
    "FRESH_REVIEW_RECEIPT_TEMPLATE.json",
    "CODEX_HANDOFF.md",
    "CODEX_HANDOFF_PROMPT.md",
}
EXPECTED_FAILURES = {f"PMG5R-FM-{index:03d}" for index in range(1, 10)}


class ValidationError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise ValidationError(message)


def load_yaml(name: str) -> Any:
    try:
        return yaml.safe_load((PKG / name).read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"invalid YAML {name}: {exc}")


def load_json(name: str) -> Any:
    try:
        return json.loads((PKG / name).read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"invalid JSON {name}: {exc}")


def mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        fail(f"{label} must be a mapping")
    return value


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True, check=False
    )
    if result.returncode:
        fail(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def validate(*, check_git: bool = False) -> dict[str, object]:
    actual = {path.name for path in PKG.iterdir() if path.is_file()}
    if actual != EXPECTED_FILES:
        fail(
            f"package file set drifted: missing={sorted(EXPECTED_FILES-actual)} "
            f"extra={sorted(actual-EXPECTED_FILES)}"
        )
    index = mapping(load_yaml("PACKAGE_INDEX.yaml"), "package index")
    if (
        index.get("package_id") != PACKAGE_ID
        or index.get("classification")
        != "EXECUTION_RECOVERY_BINDING_NOT_SUCCESSOR_PLAN"
        or set(index.get("files", [])) != EXPECTED_FILES
        or index.get("raw_map_rerun_required") is not False
        or index.get("PMG_WU006_authorized") is not False
    ):
        fail("package identity or transition semantics drifted")
    authority = mapping(load_yaml("AUTHORITY_AND_SCOPE.yaml"), "authority")
    executed = mapping(authority.get("executed_candidate"), "executed candidate")
    repair = mapping(authority.get("repair_candidate"), "repair candidate")
    if (
        executed.get("sha") != EXECUTED_SHA
        or executed.get("tree") != EXECUTED_TREE
        or executed.get("committed_terminal_status")
        != "REJECTED_PRE_REVIEW_SELF_ATTESTATION"
        or repair.get("branch") != BRANCH
        or repair.get("sha") != REPAIR_SEED_SHA
        or repair.get("tree") != REPAIR_SEED_TREE
    ):
        fail("authority binding drifted")
    threats = mapping(load_json("P0_P1_THREAT_CATALOG.json"), "threat catalog")
    rows = threats.get("failure_modes")
    if not isinstance(rows, list):
        fail("failure-mode list is missing")
    identifiers = {row.get("id") for row in rows if isinstance(row, Mapping)}
    if identifiers != EXPECTED_FAILURES:
        fail("failure-mode coverage drifted")
    for row in rows:
        if (
            not isinstance(row, Mapping)
            or row.get("severity") not in {"P0", "P1"}
            or not row.get("detection")
            or not row.get("blocked_state")
        ):
            fail(f"failure-mode detector incomplete: {row}")
    matrix = mapping(load_yaml("INVARIANT_TEST_MATRIX.yaml"), "matrix")
    mapped = {
        row.get("failure_mode")
        for row in matrix.get("rows", [])
        if isinstance(row, Mapping)
    }
    if mapped != EXPECTED_FAILURES:
        fail("invariant matrix coverage drifted")
    contract = mapping(load_yaml("RECOVERY_CONTRACT.yaml"), "contract")
    if (
        contract.get("schema") != "audit-compiled-work-unit/v1"
        or contract.get("id") != "PMG-WU-005-EVIDENCE-RECOVERY"
        or contract.get("transition", {}).get("pass_next_executable_action") is None
        or contract.get("review_gate", {}).get("maximum_targeted_repairs") != 0
    ):
        fail("recovery contract or stopping rule drifted")
    cleanup = mapping(
        load_yaml("LOCAL_CHECKPOINT_AND_CLEANUP.yaml"), "cleanup firewall"
    )
    firewall = mapping(cleanup.get("legacy_cleanup_firewall"), "cleanup firewall")
    if (
        firewall.get("policy")
        != "PRESERVE_IN_ORIGINAL_WORKTREE_AND_EXCLUDE_FROM_REPAIR_PR"
        or cleanup.get("checkpoint_policy", {}).get("current_result_may_be_recovered_without_map_rerun")
        is not True
    ):
        fail("local cleanup or checkpoint policy drifted")
    prompt = (PKG / "CODEX_HANDOFF_PROMPT.md").read_text(encoding="utf-8")
    for phrase in (
        BRANCH,
        "Do not rerun the 301 maps",
        "PLANCK_PR3_PAIRED300_REVIEWED_TERMINAL_V1",
        "PMG-WU-006 may start only after",
    ):
        if phrase not in prompt:
            fail(f"handoff prompt missing: {phrase}")
    if check_git:
        for sha, tree in (
            (EXECUTED_SHA, EXECUTED_TREE),
            (REPAIR_SEED_SHA, REPAIR_SEED_TREE),
        ):
            git("cat-file", "-e", f"{sha}^{{commit}}")
            if git("rev-parse", f"{sha}^{{tree}}") != tree:
                fail(f"authority tree mismatch: {sha}")
            result = subprocess.run(
                ["git", "merge-base", "--is-ancestor", sha, "HEAD"],
                cwd=ROOT,
                check=False,
            )
            if result.returncode:
                fail(f"HEAD is not descended from authority: {sha}")
    return {
        "status": "PASS",
        "package_id": PACKAGE_ID,
        "failure_modes": len(EXPECTED_FAILURES),
        "first_local_action": "PRESERVE_CLEANUP_AND_CREATE_SEPARATE_WORKTREE",
        "raw_map_rerun_required": False,
        "PMG_WU006_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-git", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = validate(check_git=args.check_git)
    except ValidationError as exc:
        if args.json:
            print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2))
        else:
            print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"PASS: {PACKAGE_ID}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
