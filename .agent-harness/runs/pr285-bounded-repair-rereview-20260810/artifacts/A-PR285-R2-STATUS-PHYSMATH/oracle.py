#!/usr/bin/env python3
"""Independent read-only oracle for A-PR285-R2-STATUS-PHYSMATH.

This oracle deliberately does not import the PR-285 production runner.  It
reconstructs the assigned source-to-receipt invariants directly from the
frozen YAML/JSON inputs, performs a discriminating flattening mutation, and
checks the implementation-to-review candidate delta through Git object data.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[5]
SOURCE = ROOT / "docs/research_program/vector_tensor/THEOREM_SIGNATURES_V3.yaml"
RECEIPT = ROOT / (
    "docs/research_program/post_pr275/pillar_t_adjudication/"
    "PILLAR_T_COMPLETE_ADJUDICATION_V1.json"
)
CAS_CONTRACT = ROOT / "docs/research_program/vector_tensor/cas/CAS_CONTRACT.json"
CAS_ADJUDICATION = ROOT / "docs/research_program/vector_tensor/cas/CAS_ADJUDICATION.json"
PR190_SPEC = ROOT / "docs/research_program/strengthening/pr190_spec.yaml"
PR190_RECEIPT = ROOT / "docs/generated/pr190_attainability/attainability_report.json"
FINAL_SEAL = ROOT / ".prguard/runtime/PR285_R2_FINAL_REVIEW_CANDIDATE_SEAL.json"
IMPLEMENTATION_SEAL = ROOT / ".prguard/runtime/PR285_R2_IMPLEMENTATION_CANDIDATE_SEAL.json"
IMPLEMENTATION_SHA = "8640cb23c78a2eea9dddf6fb21a1e3176d449c95"
FINAL_SHA = "8682a13e8df75c48f6150af555ee231f62e7d9bc"
REQUIRED_AXES = ["wolfram_xact", "sympy", "sage_singular", "lean"]


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return deepcopy(value)
    if isinstance(value, tuple):
        return list(value)
    return [deepcopy(value)]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: Any, *, omit: set[str] | None = None) -> str:
    if omit and isinstance(value, dict):
        value = {key: item for key, item in value.items() if key not in omit}
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)


def validate_legacy(source_rows: list[dict[str, Any]], receipt_rows: list[dict[str, Any]]) -> None:
    check(len(source_rows) == 65, "source legacy inventory must contain 65 rows")
    check(len(receipt_rows) == 65, "receipt legacy inventory must contain 65 rows")
    for source, actual in zip(source_rows, receipt_rows, strict=True):
        expected = {
            "row_id": source["entry_id"],
            "source_statement": source["statement"],
            "source_statement_identity_sha256": source["statement_identity_sha256"],
            "source_record_sha256": source["source_record_sha256"],
            "premises": as_list(source.get("assumptions")),
            "premise_status": source["assumption_status"],
            "domains": as_list(source.get("domains")),
            "domain_status": source["domain_status"],
            "verdict": "INCONCLUSIVE_WITH_RECEIPT",
        }
        for field, expected_value in expected.items():
            check(
                actual.get(field) == expected_value,
                f"legacy exact replay mismatch: {source['entry_id']}:{field}",
            )


def parse_current_cas() -> dict[str, str]:
    completed = subprocess.run(
        [
            "/usr/bin/python3",
            "-B",
            str(ROOT / ".agent-harness/scripts/cas_gate.py"),
            "preflight",
            "--all",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    statuses: dict[str, str] = {}
    for line in completed.stdout.splitlines():
        if ": " in line:
            axis, status = line.split(": ", 1)
            statuses[axis] = status
    return {axis: statuses.get(axis, "MISSING") for axis in REQUIRED_AXES}


def main() -> int:
    source_doc = yaml.safe_load(SOURCE.read_text(encoding="utf-8"))
    source_rows = source_doc["source_groups"]["legacy_signature_inventory"]["entries"]
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    legacy = [row for row in receipt["rows"] if row["source_group"] == "legacy_signature_inventory"]
    vt = {
        row["row_id"]: row
        for row in receipt["rows"]
        if row["source_group"] == "vector_tensor_successor"
    }
    failed = [row for row in receipt["rows"] if row["source_group"] == "failed_candidate"]

    validate_legacy(source_rows, legacy)
    source_status_pairs = Counter(
        (row["assumption_status"], row["domain_status"]) for row in source_rows
    )
    check(
        source_status_pairs
        == Counter({("DECLARED", "DECLARED"): 12, ("SOURCE_NOT_TYPED", "SOURCE_NOT_TYPED"): 53}),
        "legacy source status cardinality mismatch",
    )
    check(Counter(row["source_partition"] for row in source_rows) == {"T": 31, "S": 34}, "legacy partition mismatch")

    mutated = deepcopy(legacy)
    flattened = next(row for row in mutated if row["premise_status"] == "DECLARED")
    flattened["premise_status"] = "SOURCE_NOT_TYPED"
    flattened["domain_status"] = "SOURCE_NOT_TYPED"
    mutation_killed = False
    mutation_error = ""
    try:
        validate_legacy(source_rows, mutated)
    except AssertionError as exc:
        mutation_killed = True
        mutation_error = str(exc)
    check(mutation_killed, "flattening mutation survived independent source replay")

    expected_vt = {
        **{f"VT-T{i}": "PASS" for i in (1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12)},
        "VT-T8": "INCONCLUSIVE_WITH_RECEIPT",
        "VT-T13": "INCONCLUSIVE_WITH_RECEIPT",
        "VT-T14": "BLOCKED_WITH_RECEIPT",
    }
    check(set(vt) == set(expected_vt), "VT 14-row inventory mismatch")
    check({row_id: row["verdict"] for row_id, row in vt.items()} == expected_vt, "VT disposition mismatch")
    check(vt["VT-T8"]["statement_relation"] == "RESTRICTED_GENERIC_LOCAL_ELABORATION", "VT-T8 local/global ceiling drift")
    check("global orbit separation" in vt["VT-T8"]["withheld_extension"], "VT-T8 global extension not withheld")
    check(vt["VT-T13"]["statement_relation"] == "PARTIAL_CHAIN_RULE_ONLY", "VT-T13 chain-rule ceiling drift")
    check("no single branch/sign/domain convention" in vt["VT-T13"]["withheld_extension"], "VT-T13 full dynamics extension not withheld")
    check(vt["VT-T14"]["statement_relation"] == "EXTERNAL_GATE_REFUSAL", "VT-T14 native blocker drift")

    check(len(receipt["rows"]) == 80, "complete receipt must contain 80 rows")
    check(len(failed) == 1, "PR-190 failed candidate cardinality mismatch")
    expected_terminal_counts = {
        "PASS": 11,
        "FAIL": 1,
        "INCONCLUSIVE_WITH_RECEIPT": 67,
        "BLOCKED_WITH_RECEIPT": 1,
    }
    check(Counter(row["verdict"] for row in receipt["rows"]) == expected_terminal_counts, "80-row terminal disposition mismatch")
    check(receipt["summary"]["bare_not_adjudicated_count"] == 0, "bare status survived")
    check(receipt["receipt_content_sha256"] == canonical_sha256(receipt, omit={"receipt_content_sha256"}), "receipt content address drift")

    pr190_spec = yaml.safe_load(PR190_SPEC.read_text(encoding="utf-8"))
    pr190_receipt = json.loads(PR190_RECEIPT.read_text(encoding="utf-8"))
    pr190 = failed[0]
    check(pr190["row_id"] == pr190_spec["claim_identity"]["claim_id"], "PR-190 claim id drift")
    check(pr190["source_statement"] == pr190_spec["claim_identity"]["statement"], "PR-190 full statement drift")
    check(pr190["verdict"] == "FAIL", "PR-190 FAIL laundered")
    check(pr190["terminal_source_status"] == "COMPLETED_FAILED_WITH_RECEIPT", "PR-190 terminal chronology drift")
    check(pr190["success_dependency_satisfied"] is False, "PR-190 dependency improperly opened")
    check(pr190_receipt["terminal"] == "COMPLETED_FAILED_WITH_RECEIPT", "PR-190 source terminal drift")
    check(pr190["counterexample_boundary"] == pr190_receipt["result"]["refuted_stages"], "PR-190 counterexample chronology drift")
    check({item["target_id"] for item in pr190["counterexample_boundary"]} == {"PR190-LOWER-XC-11-100", "PR190-INTERIOR-XC-12-100"}, "PR-190 exact falsifier target drift")

    report = pr190_receipt["result"]["report"]
    check(report["metric_signature"] == "(-,+,+,+)", "metric signature drift")
    check(report["comparator"] == "x_C=Sigma2-W2+Omega_tilt+DeltaOmega_k", "comparator sign drift")
    for witness in report["witnesses"]:
        target = witness["target"]
        exact = (
            Fraction(target["Sigma2"])
            - Fraction(target["W2"])
            + Fraction(target["Omega_tilt"])
            + Fraction(target["DeltaOmega_k"])
        )
        check(exact == Fraction(target["x_C"]), f"exact comparator sign error: {witness['target_id']}")
        check(witness["units_convention"] == "EXPLICIT_C_THETA_NORMALIZED", f"unit convention drift: {witness['target_id']}")

    cas_contract = json.loads(CAS_CONTRACT.read_text(encoding="utf-8"))
    historical_cas = json.loads(CAS_ADJUDICATION.read_text(encoding="utf-8"))
    check(historical_cas["contract_sha256"] == sha256(CAS_CONTRACT), "historical CAS contract drift")
    check(historical_cas["required_axes"] == REQUIRED_AXES, "historical CAS axes drift")
    check(historical_cas["aggregate_status"] == "CAS_4AXIS_PASS", "historical CAS aggregate drift")
    check(all(historical_cas["axis_statuses"][axis] == "PASS" for axis in REQUIRED_AXES), "historical CAS axis failure")
    check(receipt["cas_evidence"]["claim_promotion_effect"] == "CAS_COMPONENT_ONLY_NO_SCIENTIFIC_PROMOTION", "CAS scientific scope promotion")
    check(cas_contract["identity"]["claim_ceiling"] == "diagnostic_only", "CAS claim ceiling drift")
    current_cas = parse_current_cas()
    check(current_cas["wolfram_xact"].startswith("BLOCKED_"), "current Wolfram/xAct must remain a typed platform blocker")
    check(all(current_cas[axis] == "PASS" for axis in ("sympy", "sage_singular", "lean")), "available CAS axis preflight failure")

    final_seal = json.loads(FINAL_SEAL.read_text(encoding="utf-8"))
    implementation_seal = json.loads(IMPLEMENTATION_SEAL.read_text(encoding="utf-8"))
    diff = subprocess.run(
        ["git", "diff", "--name-status", f"{IMPLEMENTATION_SHA}..{FINAL_SHA}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.splitlines()
    expected_delta = [
        "M\tdocs/PR_DELTAS/pr-285.md",
        "M\tdocs/codex_handoff/pr_status.yaml",
        "M\tmachine_readable/pr_status.yaml",
    ]
    check(diff == expected_delta, "implementation-to-review candidate delta is substantive or incomplete")
    check(final_seal["candidate_sha"] == FINAL_SHA, "final candidate SHA drift")
    check(implementation_seal["candidate_sha"] == IMPLEMENTATION_SHA, "implementation candidate SHA drift")
    check(final_seal["production_hash"] == implementation_seal["production_hash"], "production hash changed after implementation validation")
    check(final_seal["changed_files_sha256"] == implementation_seal["changed_files_sha256"], "candidate changed-file inventory changed after implementation validation")

    metadata = receipt["metadata"]
    check(metadata["claim_tier"] == "diagnostic_only", "claim tier promotion")
    check(metadata["transfer_source"] == "none", "transfer-source laundering")
    check(metadata["observed_data_executed"] is False and metadata["public_use"] is False, "observed/public claim promotion")
    check(metadata["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS", "family-identification gate opened")

    output = {
        "schema": "A_PR285_R2_STATUS_PHYSMATH_ORACLE_V1",
        "status": "PASS",
        "independent_of_candidate_runner": True,
        "legacy": {
            "rows": len(legacy),
            "partitions": dict(sorted(Counter(row["source_partition"] for row in legacy).items())),
            "status_pairs": {"DECLARED/DECLARED": 12, "SOURCE_NOT_TYPED/SOURCE_NOT_TYPED": 53},
            "verdict": "INCONCLUSIVE_WITH_RECEIPT",
        },
        "flattening_mutation": {"killed": mutation_killed, "error": mutation_error},
        "disposition": {"rows": len(receipt["rows"]), "terminal_counts": expected_terminal_counts},
        "restricted_boundaries": {"VT-T8": vt["VT-T8"]["verdict"], "VT-T13": vt["VT-T13"]["verdict"], "VT-T14": vt["VT-T14"]["verdict"]},
        "pr190": {"verdict": pr190["verdict"], "terminal": pr190["terminal_source_status"], "success_dependency_satisfied": False},
        "physics_boundary": {
            "metric_signature": report["metric_signature"],
            "comparator": report["comparator"],
            "exact_target_checks": len(report["witnesses"]),
            "units_convention": "EXPLICIT_C_THETA_NORMALIZED",
            "priors_likelihood_q_pi_f_g": "NOT_APPLICABLE_NO_PRODUCTION_OR_INFERENCE_CHANGE",
            "local_global_rank": "NO_CLAIM_VT_T8_GLOBAL_SEPARATION_WITHHELD",
            "family_identification_gate": metadata["family_identification_gate"],
        },
        "cas": {
            "current_aggregate_status": "CAS_BLOCKED",
            "current_axis_statuses": current_cas,
            "historical_aggregate_status": historical_cas["aggregate_status"],
            "historical_contract_sha256": historical_cas["contract_sha256"],
            "claim_promotion_from_current_run": False,
        },
        "candidate_delta": {
            "implementation_sha": IMPLEMENTATION_SHA,
            "final_review_sha": FINAL_SHA,
            "paths": diff,
            "production_hash_unchanged": True,
            "changed_files_inventory_unchanged": True,
            "substantive_rerun_required": False,
        },
        "input_sha256": {
            "source": sha256(SOURCE),
            "receipt": sha256(RECEIPT),
            "cas_contract": sha256(CAS_CONTRACT),
            "cas_adjudication": sha256(CAS_ADJUDICATION),
            "pr190_spec": sha256(PR190_SPEC),
            "pr190_receipt": sha256(PR190_RECEIPT),
            "final_seal": sha256(FINAL_SEAL),
            "implementation_seal": sha256(IMPLEMENTATION_SEAL),
        },
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
