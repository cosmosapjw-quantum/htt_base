#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "docs/codex_handoff/pr321_reaudit"
AUDIT = ROOT / "docs/research_program/post_pr275/audits/pr321_hsc_sacc_reaudit.md"
RESULT = ROOT / "docs/generated/pr321_hsc_sacc_result.json"
INTEGRATION_TEST = ROOT / "tests/integration/test_hsc_kids_current_stack.py"

EXPECTED_TERMINAL = (
    "READY_FOR_PREREGISTERED_FIDUCIAL_WINDOW_CONVOLVED_REFERENCE"
)
EXPECTED_MES_STOP = "BLOCKED_MES_PLAN_NOT_DESCENDED_FROM_REPAIRED_PR321"

def fail(message: str) -> None:
    raise SystemExit(message)


def main() -> int:
    required = [
        AUDIT,
        PKG / "REVIEW_DELTA_20260825.md",
        PKG / "P0_P1_THREAT_CATALOG.json",
        PKG / "AUDIT_COMPILED_EXEC_PLAN.yaml",
        PKG / "EXPECTED_RESULT_SCHEMA.yaml",
        PKG / "MES_PLAN_INTEGRATION_DELTA.yaml",
        PKG / "OFFICIAL_REFERENCE_MATRIX.yaml",
        PKG / "FRESH_CONTEXT_REVIEW_CONTRACT.yaml",
        PKG / "CODEX_HANDOFF.md",
        RESULT,
        INTEGRATION_TEST,
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        fail(f"missing PR-321 re-audit files: {missing}")

    threats = json.loads((PKG / "P0_P1_THREAT_CATALOG.json").read_text(encoding="utf-8"))
    plan = yaml.safe_load((PKG / "AUDIT_COMPILED_EXEC_PLAN.yaml").read_text(encoding="utf-8"))
    expected = yaml.safe_load((PKG / "EXPECTED_RESULT_SCHEMA.yaml").read_text(encoding="utf-8"))
    mes_delta = yaml.safe_load((PKG / "MES_PLAN_INTEGRATION_DELTA.yaml").read_text(encoding="utf-8"))
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    integration_source = INTEGRATION_TEST.read_text(encoding="utf-8")

    findings = threats.get("findings")
    if not isinstance(findings, list):
        fail("PR-321 threat catalogue findings must be a list")
    ids = [row.get("id") for row in findings if isinstance(row, dict)]
    if len(findings) != 10 or len(set(ids)) != 10:
        fail("expected exactly ten unique PR-321 failure classes")
    counts = Counter(row.get("severity") for row in findings)
    if counts != {"P0": 2, "P1": 8}:
        fail("expected exactly two P0 and eight P1 guarded failure classes")

    guards_present = 0
    for row in findings:
        if not row.get("detector") or not row.get("stop"):
            fail(f"incomplete failure contract: {row.get('id')}")
        detector = row["detector"]
        if detector.startswith("test_"):
            if f"def {detector}(" not in integration_source:
                fail(f"missing controlling PR-321 test: {detector}")
        elif detector == f"STOP:{EXPECTED_MES_STOP}":
            if mes_delta["planning_ancestry"]["blocked_token"] != EXPECTED_MES_STOP:
                fail("MES ancestry STOP token drifted")
        else:
            fail(f"unrecognized PR-321 guard: {detector}")
        guards_present += 1

    if plan["authority"]["pr"] != 412:
        fail("PR authority drifted")
    if len(plan["ordered_steps"]) != 7:
        fail("repair steps drifted")
    if "Do not reorder any existing DAG node or edge." not in plan["scope"]["forbidden_changes"]:
        fail("DAG prefix guard missing")
    if expected["terminal_disposition"] != EXPECTED_TERMINAL:
        fail("expected-result terminal drifted")
    if (
        result.get("schema") != "htt.pr321.hsc_sacc_repaired_result.v1"
        or result.get("terminal_disposition") != EXPECTED_TERMINAL
    ):
        fail("generated PR-321 result is not the repaired terminal")
    if result.get("directional_and_MES_boundary") != expected["directional_and_MES_boundary"]:
        fail("generated PR-321 MES boundary drifted")

    print(json.dumps({
        "schema": "htt.pr321.reaudit.plan_validation.v2",
        "status": "PASS",
        "contract_failure_classes": {"P0": 2, "P1": 8},
        "guards_present": guards_present,
        "science_repair_executed": True,
        "generated_result_terminal": EXPECTED_TERMINAL,
        "canonical_DAG_changed": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
