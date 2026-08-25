#!/usr/bin/env python3
"""Validate the MES-methodology recovery planning contract."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "docs/codex_handoff/mes_methodology_recovery"
REQUIRED = {
    "PACKAGE_INDEX.yaml",
    "ADVERSARIAL_SCIENCE_AUDIT.md",
    "RESEARCH_DECISION_LEDGER.yaml",
    "WOLFRAM_PROOF_RECEIPT.yaml",
    "LOCAL_FORMALIZATION_TASKS.yaml",
    "P0_P1_THREAT_CATALOG.json",
    "INVARIANT_TEST_MATRIX.yaml",
    "AUDIT_COMPILED_EXEC_PLAN.yaml",
    "FRESH_CONTEXT_REVIEW_CONTRACT.yaml",
    "CODEX_HANDOFF.md",
}
EXPECTED_WUS = [f"MR-WU-{index:03d}" for index in range(9)]


def fail(message: str) -> None:
    raise SystemExit(message)


def load_yaml(name: str):
    with (PKG / name).open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    missing = sorted(name for name in REQUIRED if not (PKG / name).is_file())
    if missing:
        fail(f"missing package files: {missing}")

    index = load_yaml("PACKAGE_INDEX.yaml")
    plan = load_yaml("AUDIT_COMPILED_EXEC_PLAN.yaml")
    matrix = load_yaml("INVARIANT_TEST_MATRIX.yaml")
    decisions = load_yaml("RESEARCH_DECISION_LEDGER.yaml")
    with (PKG / "P0_P1_THREAT_CATALOG.json").open(encoding="utf-8") as handle:
        threats = json.load(handle)

    if index.get("canonical_DAG_changed") is not False:
        fail("planning package must not change canonical DAG")
    if index.get("science_code_changed") is not False:
        fail("planning package must not claim science-code changes")
    if plan.get("ordered_work_units") != EXPECTED_WUS:
        fail("work-unit order drifted")

    work_units = plan.get("work_units")
    if not isinstance(work_units, list) or [row.get("id") for row in work_units] != EXPECTED_WUS:
        fail("work-unit records drifted")

    failure_rows = threats.get("failure_modes", [])
    failure_ids = {row.get("id") for row in failure_rows if isinstance(row, dict)}
    required_failures = {
        row.get("id") for row in failure_rows
        if isinstance(row, dict) and row.get("severity") in {"P0", "P1"}
    }
    for row in failure_rows:
        if row.get("severity") in {"P0", "P1"} and not row.get("detector"):
            fail(f"{row.get('id')} lacks detector")

    for work_unit in work_units:
        if work_unit.get("schema") != "audit-compiled-work-unit/v1":
            fail(f"{work_unit.get('id')} schema drifted")
        gate = work_unit.get("review_gate", {}).get("pass_condition", {})
        if gate != {"P0": 0, "P1": 0}:
            fail(f"{work_unit.get('id')} review gate weakened")
        risk = work_unit.get("risk", {})
        refs = set(risk.get("P0_failure_modes", [])) | set(risk.get("P1_failure_modes", []))
        unknown = sorted(refs - failure_ids)
        if unknown:
            fail(f"{work_unit.get('id')} references unknown failures: {unknown}")

    required_axes = {"truth_status", "evidence_status", "replay_status", "release_status"}
    decision_rows = decisions.get("decisions", [])
    for row in decision_rows:
        missing_axes = sorted(required_axes - set(row))
        if missing_axes:
            fail(f"{row.get('id')} missing status axes: {missing_axes}")

    mapped_failures = {row.get("failure_mode") for row in matrix.get("rows", [])}
    if mapped_failures != required_failures:
        fail(
            "invariant matrix coverage drifted: "
            f"missing={sorted(required_failures - mapped_failures)} "
            f"extra={sorted(mapped_failures - required_failures)}"
        )

    handoff = (PKG / "CODEX_HANDOFF.md").read_text(encoding="utf-8")
    for required in (
        "generic Planck low-ell 12-feature rank is a frozen benchmark control",
        "Do not reactivate `htt/bass/observational/planck_mes_bounds.py`",
        "Do not infer a vector, axis or tensor orientation from scalar MES values",
        "Do not identify local boost versus global tilt from one shell",
    ):
        if required.lower() not in handoff.lower():
            fail(f"handoff lost required lock: {required}")

    payload = {
        "schema": "htt.mes_methodology_recovery.plan_validation.v1",
        "status": "PASS",
        "work_units": EXPECTED_WUS,
        "failure_modes": len(required_failures),
        "research_decisions": len(decision_rows),
        "canonical_DAG_changed": False,
        "science_code_changed": False,
    }
    print(json.dumps(payload, sort_keys=True) if args.json else "PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
