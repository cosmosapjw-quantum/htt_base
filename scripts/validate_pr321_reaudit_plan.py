#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "docs/codex_handoff/pr321_reaudit"
AUDIT = ROOT / "docs/research_program/post_pr275/audits/pr321_hsc_sacc_reaudit.md"

def fail(message: str) -> None:
    raise SystemExit(message)

def main() -> int:
    required = [
        AUDIT,
        PKG / "P0_P1_THREAT_CATALOG.json",
        PKG / "AUDIT_COMPILED_EXEC_PLAN.yaml",
        PKG / "CODEX_HANDOFF.md",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        fail(f"missing PR-321 re-audit files: {missing}")

    threats = json.loads((PKG / "P0_P1_THREAT_CATALOG.json").read_text(encoding="utf-8"))
    plan = yaml.safe_load((PKG / "AUDIT_COMPILED_EXEC_PLAN.yaml").read_text(encoding="utf-8"))
    ids = {row["id"] for row in threats["findings"]}
    if len(ids) != 6:
        fail("expected exactly six P1 failure classes")
    for row in threats["findings"]:
        if row["severity"] != "P1" or not row.get("detector") or not row.get("stop"):
            fail(f"incomplete failure contract: {row.get('id')}")
    if plan["authority"]["pr"] != 412:
        fail("PR authority drifted")
    if len(plan["ordered_steps"]) != 7:
        fail("repair steps drifted")
    if "Do not reorder any existing DAG node or edge." not in plan["scope"]["forbidden_changes"]:
        fail("DAG prefix guard missing")
    print(json.dumps({
        "schema": "htt.pr321.reaudit.plan_validation.v1",
        "status": "PASS",
        "P0": 0,
        "P1": len(ids),
        "canonical_DAG_changed": False,
        "science_repair_executed": False,
    }, sort_keys=True))
    return 0

if __name__ == "__main__":
    sys.exit(main())
