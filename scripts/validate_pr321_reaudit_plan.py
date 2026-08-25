#!/usr/bin/env python3
from __future__ import annotations

import ast
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
EXPECTED_GUARDS = {
    "PR321-FM-P0-001": {
        "name": "DIRECTIONLESS_SACC_USED_AS_MES_DIRECTIONAL_EVIDENCE",
        "severity": "P0",
        "detector": (
            "test_pr321_sacc_is_scalar_tomographic_control_not_directional_mes_input"
        ),
        "stop": "BLOCKED_NO_DIRECTION_INDEXED_HSC_FIELD",
    },
    "PR321-FM-P0-002": {
        "name": "CMB_MES_ANCHOR_APPLIED_CROSS_CHANNEL",
        "severity": "P0",
        "detector": (
            "test_pr321_rejects_cmb_mes_anchor_without_channel_matched_transfer"
        ),
        "stop": "BLOCKED_CROSS_CHANNEL_NO_PHYSICAL_TRANSFER",
    },
    "PR321-FM-P1-001": {
        "name": "FULL_RELEASE_VECTOR_USED_AS_FIDUCIAL_SCIENCE_VECTOR",
        "severity": "P1",
        "detector": "test_pr321_fiducial_indices_and_covariance_slice",
        "stop": "BLOCKED_HSC_FIDUCIAL_SCALE_SELECTION",
    },
    "PR321-FM-P1-002": {
        "name": "TRACER_NZ_OMITTED_OR_MALFORMED",
        "severity": "P1",
        "detector": "test_pr321_rejects_malformed_source_nz",
        "stop": "BLOCKED_HSC_TRACER_NZ",
    },
    "PR321-FM-P1-003": {
        "name": "LEGACY_SACC_ORDER_NOT_INDEPENDENTLY_CROSSCHECKED",
        "severity": "P1",
        "detector": (
            "test_pr321_legacy_order_crosschecks_mean_pair_api_and_covariance"
        ),
        "stop": "BLOCKED_HSC_SACC_ORDERING",
    },
    "PR321-FM-P1-004": {
        "name": "OBSERVED_STATISTIC_PROVENANCE_UNDERSTATED",
        "severity": "P1",
        "detector": (
            "test_pr321_hsc_sacc_contract_is_hsc_only_and_covariance_bound"
        ),
        "stop": "BLOCKED_HSC_OBSERVED_STATE",
    },
    "PR321-FM-P1-005": {
        "name": "PORTABLE_OPERATOR_DIGEST_NOT_ARRAY_BOUND",
        "severity": "P1",
        "detector": "test_pr321_window_and_fiducial_digests_mutate",
        "stop": "BLOCKED_HSC_PORTABLE_OPERATOR_IDENTITY",
    },
    "PR321-FM-P1-006": {
        "name": "PR_URL_STATUS_PROVENANCE_MISBOUND",
        "severity": "P1",
        "detector": "test_pr321_status_urls_are_bound_to_correct_internal_prs",
        "stop": "BLOCKED_PR321_STATUS_PROVENANCE",
    },
    "PR321-FM-P1-007": {
        "name": "ANTI_DRIFT_METRIC_CONTRACT_ALREADY_VIOLATED",
        "severity": "P1",
        "detector": "test_pr321_semantic_scope_replaces_false_loc_cap",
        "stop": "BLOCKED_PR321_SCOPE_CONTRACT",
    },
    "PR321-FM-P1-008": {
        "name": "MES_PLAN_AND_REPAIRED_DATA_STACK_HAVE_SIBLING_ANCESTRY",
        "severity": "P1",
        "detector": f"STOP:{EXPECTED_MES_STOP}",
        "stop": EXPECTED_MES_STOP,
    },
}

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
    if threats.get("schema") != "htt.pr321.reaudit.threat_catalog.v2":
        fail("PR-321 threat catalogue schema drifted")
    if any(not isinstance(row, dict) for row in findings):
        fail("PR-321 threat catalogue rows must be objects")
    ids = [row.get("id") for row in findings]
    if len(findings) != len(EXPECTED_GUARDS) or len(set(ids)) != len(ids):
        fail("expected exactly ten unique PR-321 failure classes")
    by_id = {row["id"]: row for row in findings}
    if set(by_id) != set(EXPECTED_GUARDS):
        fail("PR-321 threat catalogue failure IDs drifted")
    for finding_id, expected_guard in EXPECTED_GUARDS.items():
        row = by_id[finding_id]
        for field, expected_value in expected_guard.items():
            if row.get(field) != expected_value:
                fail(f"PR-321 threat catalogue {finding_id} {field} drifted")
    counts = Counter(row.get("severity") for row in findings)
    if counts != {"P0": 2, "P1": 8}:
        fail("expected exactly two P0 and eight P1 guarded failure classes")

    try:
        integration_tree = ast.parse(integration_source, filename=str(INTEGRATION_TEST))
    except SyntaxError as exc:
        fail(f"PR-321 integration test source is not valid Python: {exc}")
    collected_test_functions = {
        node.name
        for node in integration_tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    guards_present = 0
    for row in findings:
        if not row.get("detector") or not row.get("stop"):
            fail(f"incomplete failure contract: {row.get('id')}")
        detector = row["detector"]
        if detector.startswith("test_"):
            if detector not in collected_test_functions:
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
