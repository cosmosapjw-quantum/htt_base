#!/usr/bin/env python3
"""Independent PR-285 row/CAS boundary oracle for A-PR285-FROZEN-PHYSMATH."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[5]
OUTPUT = Path(__file__).with_name("oracle_report.json")


def load(path: str) -> dict[str, Any]:
    raw = (ROOT / path).read_text(encoding="utf-8")
    return json.loads(raw) if path.endswith(".json") else yaml.safe_load(raw)


def sha256(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def run_json(argv: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        argv,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=1800,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed rc={completed.returncode}: {argv!r}\n"
            f"stdout={completed.stdout[-2000:]}\nstderr={completed.stderr[-2000:]}"
        )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    return json.loads(lines[-1])


def main() -> int:
    started = datetime.now(timezone.utc).isoformat()
    signatures_path = "docs/research_program/vector_tensor/THEOREM_SIGNATURES_V3.yaml"
    program_path = "docs/research_program/vector_tensor/VECTOR_TENSOR_PROOF_PROGRAM_V1.yaml"
    t_core_path = "docs/research_program/vector_tensor/proofs/PILLAR_T_CORE_PROOFS_V1.yaml"
    cas_proofs_path = "docs/research_program/vector_tensor/proofs/PILLAR_T_CAS_PROOFS_V1.yaml"
    contract_path = "docs/research_program/vector_tensor/cas/CAS_CONTRACT.json"
    adjudication_path = "docs/research_program/vector_tensor/cas/CAS_ADJUDICATION.json"
    receipt_path = (
        "docs/research_program/post_pr275/pillar_t_adjudication/"
        "PILLAR_T_COMPLETE_ADJUDICATION_V1.json"
    )
    pr190_spec_path = "docs/research_program/strengthening/pr190_spec.yaml"
    pr190_report_path = "docs/generated/pr190_attainability/attainability_report.json"

    signatures = load(signatures_path)
    program = load(program_path)
    t_core = load(t_core_path)
    cas_proofs = load(cas_proofs_path)
    contract = load(contract_path)
    adjudication = load(adjudication_path)
    receipt = load(receipt_path)
    pr190_spec = load(pr190_spec_path)
    pr190_report = load(pr190_report_path)
    rows = {row["row_id"]: row for row in receipt["rows"]}

    legacy = signatures["source_groups"]["legacy_signature_inventory"]["entries"]
    legacy_receipts = [
        row for row in receipt["rows"] if row["source_group"] == "legacy_signature_inventory"
    ]
    declared_legacy = [
        row
        for row in legacy
        if row.get("assumption_status") == "DECLARED"
        or row.get("domain_status") == "DECLARED"
    ]
    status_drift = []
    value_drift = []
    for source in legacy:
        actual = rows[source["entry_id"]]
        if actual["premises"] != source["assumptions"] or actual["domains"] != source["domains"]:
            value_drift.append(source["entry_id"])
        if (
            actual["premise_status"] != source["assumption_status"]
            or actual["domain_status"] != source["domain_status"]
        ):
            status_drift.append(
                {
                    "row_id": source["entry_id"],
                    "source_assumption_status": source["assumption_status"],
                    "receipt_premise_status": actual["premise_status"],
                    "source_domain_status": source["domain_status"],
                    "receipt_domain_status": actual["domain_status"],
                }
            )

    typed = {
        **load("docs/research_program/vector_tensor/pr269_spec.yaml")["typed_statements"],
        **load("docs/research_program/vector_tensor/pr270_spec.yaml")["typed_statements"],
    }
    core_records = {
        row["obligation_id"]: row
        for row in t_core["records"]
        if str(row.get("obligation_id", "")).startswith("VT-T")
    }
    cas_records = {row["obligation_id"]: row for row in cas_proofs["records"]}
    proof_records = {**core_records, **cas_records}
    expected_dispositions = {
        **{f"VT-T{i}": "PASS" for i in (1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12)},
        "VT-T8": "INCONCLUSIVE_WITH_RECEIPT",
        "VT-T13": "INCONCLUSIVE_WITH_RECEIPT",
        "VT-T14": "BLOCKED_WITH_RECEIPT",
    }
    vt_mismatches: list[str] = []
    for i in range(1, 15):
        row_id = f"VT-T{i}"
        statement = typed[row_id]
        proof = proof_records[row_id]
        actual = rows[row_id]
        expected_fields = {
            "adjudicated_statement": statement["statement"],
            "statement_relation": statement["relation_to_source"],
            "premises": as_list(statement.get("assumptions", proof.get("assumptions"))),
            "domains": as_list(statement.get("domain", proof.get("domains"))),
            "counterexample_boundary": as_list(
                statement.get(
                    "counterexample_boundary", proof.get("counterexample_boundaries", [])
                )
            ),
            "premise_status": "TYPED_AND_FROZEN",
            "domain_status": "TYPED_AND_FROZEN",
            "verdict": expected_dispositions[row_id],
        }
        for field, expected in expected_fields.items():
            if actual.get(field) != expected:
                vt_mismatches.append(f"{row_id}:{field}")

    required_axes = ["wolfram_xact", "sympy", "sage_singular", "lean"]
    historical_cas_ok = (
        adjudication["contract_sha256"] == sha256(contract_path)
        and adjudication["required_axes"] == required_axes
        and adjudication["aggregate_status"] == "CAS_4AXIS_PASS"
        and adjudication["axis_statuses"] == {axis: "PASS" for axis in required_axes}
        and receipt["cas_evidence"]["aggregate_sha256"] == sha256(adjudication_path)
        and receipt["cas_evidence"]["aggregate_status"] == "CAS_4AXIS_PASS"
        and receipt["cas_evidence"]["majority_vote_forbidden"] is True
    )
    fresh_payloads = {
        "sympy": run_json(
            [sys.executable, "-B", "docs/research_program/vector_tensor/cas/axes/sympy/axis_program.py"]
        ),
        "sage_singular": run_json(
            ["sage", "-python", "docs/research_program/vector_tensor/cas/axes/sage_singular/axis_program.sage"]
        ),
        "lean": run_json(["sh", "docs/research_program/vector_tensor/cas/axes/lean/axis_program"]),
    }
    fresh_available_ok = all(
        payload.get("counterexample") is None
        and payload.get("domain_assumption_diff") == []
        and set(payload.get("checks", {}).values()) == {True}
        for payload in fresh_payloads.values()
    ) and len({json.dumps(p["computed"], sort_keys=True) for p in fresh_payloads.values()}) == 1

    preflight = subprocess.run(
        [sys.executable, "-B", ".agent-harness/scripts/cas_gate.py", "preflight", "--all"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    preflight_statuses = {}
    for line in preflight.stdout.splitlines():
        if ": " in line:
            axis, status = line.split(": ", 1)
            preflight_statuses[axis] = status
    wolfram_raw = preflight_statuses.get("wolfram_xact", "MISSING")
    wolfram_typed_block = wolfram_raw.startswith("BLOCKED_")

    claim = pr190_spec["claim_identity"]
    pr190 = rows[claim["claim_id"]]
    pr190_ok = (
        pr190["source_statement"] == claim["statement"]
        and pr190["adjudicated_statement"] == claim["statement"]
        and pr190["counterexample_boundary"] == pr190_report["result"]["refuted_stages"]
        and [row["target_id"] for row in pr190["counterexample_boundary"]]
        == ["PR190-LOWER-XC-11-100", "PR190-INTERIOR-XC-12-100"]
        and all(row["level"] == "CONSTRAINT" and row["status"] == "REFUTED" for row in pr190["counterexample_boundary"])
        and pr190_report["terminal"] == "COMPLETED_FAILED_WITH_RECEIPT"
        and pr190_report["success_dependency_satisfied"] is False
        and pr190["verdict"] == "FAIL"
        and pr190["success_dependency_satisfied"] is False
    )

    metadata_ok = receipt["metadata"] == {
        **receipt["metadata"],
        "claim_tier": "diagnostic_only",
        "transfer_source": "none",
        "observed_data_executed": False,
        "public_use": False,
        "family_identification_gate": "BLOCKED_PRE_NATIVE_ATLAS",
    }
    findings = []
    if status_drift:
        findings.append(
            {
                "finding_id": "PR285-LEGACY-PREMISE-DOMAIN-STATUS-DRIFT",
                "severity": "high",
                "rows": status_drift,
                "reason": (
                    "Twelve legacy registry rows explicitly declare assumptions and domains, "
                    "but the receipt labels them SOURCE_NOT_TYPED. Values are preserved; source "
                    "typing status and the spec's all-65 premise/domain assertion are not."
                ),
            }
        )

    checks = {
        "legacy_inventory_65": len(legacy) == len(legacy_receipts) == 65,
        "legacy_partition_31T_34S": Counter(row["source_partition"] for row in legacy)
        == Counter({"T": 31, "S": 34}),
        "legacy_all_title_only_and_inconclusive": all(
            source["statement_status"] == "TITLE_ONLY"
            and rows[source["entry_id"]]["verdict"] == "INCONCLUSIVE_WITH_RECEIPT"
            for source in legacy
        ),
        "legacy_premise_domain_values_exact": not value_drift,
        "legacy_premise_domain_status_exact": not status_drift,
        "legacy_declared_premise_domain_count": len(declared_legacy) == 12,
        "vector_tensor_inventory_14": [row["id"] for row in program["theorems"]["pillar_T"]]
        == [f"VT-T{i}" for i in range(1, 15)],
        "vector_tensor_exact_statement_premise_domain_boundary_and_disposition": not vt_mismatches,
        "vt_t8_local_only": rows["VT-T8"]["statement_relation"]
        == "RESTRICTED_GENERIC_LOCAL_ELABORATION"
        and "global orbit separation" in rows["VT-T8"].get("withheld_extension", ""),
        "vt_t13_chain_rule_only": rows["VT-T13"]["statement_relation"]
        == "PARTIAL_CHAIN_RULE_ONLY"
        and "typed full evolution law" in rows["VT-T13"]["verdict_reason"],
        "vt_t14_native_blocker": rows["VT-T14"]["statement_relation"]
        == "EXTERNAL_GATE_REFUSAL"
        and rows["VT-T14"]["verdict"] == "BLOCKED_WITH_RECEIPT",
        "historical_byte_bound_cas_4axis_pass": historical_cas_ok,
        "fresh_sympy_sage_lean_pass": fresh_available_ok,
        "fresh_wolfram_typed_engine_block": wolfram_typed_block,
        "fresh_four_axis_pass_forbidden": wolfram_typed_block,
        "pr190_exact_counterexample_chronology": pr190_ok,
        "claim_and_family_ceiling": metadata_ok,
    }
    report = {
        "schema_version": 1,
        "oracle_id": "PR285-PHYSMATH-ROW-CAS-ORACLE",
        "started_at": started,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "candidate_verdict": "FAIL" if findings else "PASS",
        "checks": checks,
        "findings": findings,
        "details": {
            "legacy_declared_rows": [row["entry_id"] for row in declared_legacy],
            "legacy_value_drift": value_drift,
            "vt_mismatches": vt_mismatches,
            "fresh_axis_statuses": {
                "sympy": "PASS" if fresh_available_ok else "FAIL",
                "sage_singular": "PASS" if fresh_available_ok else "FAIL",
                "lean": "PASS" if fresh_available_ok else "FAIL",
                "wolfram_xact_raw": wolfram_raw,
                "wolfram_xact_normalized": (
                    "BLOCKED_REQUIRED_ENGINE_UNAVAILABLE" if wolfram_typed_block else wolfram_raw
                ),
            },
            "cas_seal_compatibility": (
                "The current run is CAS_BLOCKED/INCONCLUSIVE and cannot be called a fresh "
                "four-axis pass. It is compatible with the PR-285 process seal only as typed "
                "terminal platform evidence while the historical CAS_4AXIS_PASS remains "
                "separately byte-bound; it cannot cure an independent row-contract failure."
            ),
        },
    }
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "candidate_verdict": report["candidate_verdict"], "output": str(OUTPUT.relative_to(ROOT))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
