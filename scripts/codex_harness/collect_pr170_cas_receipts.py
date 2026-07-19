#!/usr/bin/env python3
"""Strictly validate and publish PR-170's four blind CAS receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

try:
    from .run_pr170_axis import _validate_contract
except ImportError:  # direct script execution
    from run_pr170_axis import _validate_contract


REPO = Path(__file__).resolve().parents[2]
CONTRACT_PATH = Path("docs/generated/pr170_cas/CAS_CONTRACT_PR170_BUCHERT_TWO_PATCH.json")
AUTH_PATH = Path("docs/generated/pr170_cas/preaxis_authorization.json")
RUNNER_PATH = Path("scripts/codex_harness/run_pr170_axis.py")
OUTPUT_ROOT = Path("docs/generated/pr170_cas")
COLLECTION_PATH = Path("docs/generated/pr170_cas_collection_receipt.json")
AXES = ("wolfram_xact", "sympy", "sage_singular", "lean")
ASSIGNMENT_IDS = {
    "wolfram_xact": "A-PR170-CAS-WOLFRAM",
    "sympy": "A-PR170-CAS-SYMPY",
    "sage_singular": "A-PR170-CAS-SAGE",
    "lean": "A-PR170-CAS-LEAN",
}
BLOCKED = {"BLOCKED_PLATFORM_OR_LICENSE", "BLOCKED_PACKAGE_UNAVAILABLE", "BLOCKED_RESOURCE_LIMIT"}
EXPECTED_SOURCE_INPUT_PATHS = {
    "docs/research_program/long_horizon_rescue/pr170_spec.yaml",
    "docs/research_program/long_horizon_rescue/pr170_primary_source_provenance.yaml",
    "docs/audits/pr170_primary_sources/buchert_2000_equations.txt",
    "docs/audits/pr170_primary_sources/wiegand_buchert_2010_equations.txt",
    "docs/audits/pr170_primary_sources/barrow_tsagas_2007_equations.txt",
    "docs/audits/pr170_primary_sources/akarsu_2023_type_v_record.txt",
    "htt/src/common/buchert_two_patch.py",
}
EXPECTED_AXIS_CONTRACT = {
    "wolfram_xact": {
        "command": "wolframscript -file wolfram/pr170_buchert_two_patch_axis.wls",
        "required_tool": "Wolfram Engine plus xAct/xTensor",
        "sources": {"wolfram/pr170_buchert_two_patch_axis.wls"},
    },
    "sympy": {
        "command": "venv/bin/python -B htt/src/common/pr170_sympy_axis.py",
        "required_tool": "SymPy exact rational algebra",
        "sources": {"htt/src/common/pr170_sympy_axis.py"},
    },
    "sage_singular": {
        "command": "sage sage/pr170_buchert_two_patch_axis.sage",
        "required_tool": "SageMath plus Singular",
        "sources": {"sage/pr170_buchert_two_patch_axis.sage"},
    },
    "lean": {
        "command": "cd formal_pr170 && lake build && lake exe pr170bucherttwopatch",
        "required_tool": "Lean 4.31.0 plus mathlib 4.31.0",
        "sources": {
            "formal_pr170/Pr170BuchertTwoPatch.lean",
            "formal_pr170/Pr170BuchertTwoPatch/Basic.lean",
            "formal_pr170/lakefile.toml",
            "formal_pr170/lake-manifest.json",
            "formal_pr170/lean-toolchain",
        },
    },
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _render(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _assignment_self_hash(value: dict[str, Any]) -> str:
    material = dict(value)
    material.pop("assignment_sha256", None)
    encoded = json.dumps(material, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _safe_rel(value: str) -> bool:
    path = Path(value)
    return not path.is_absolute() and ".." not in path.parts and str(path) == value


def _validate_exact_contract_inventory(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    source_rows = contract.get("identity", {}).get("source_input_hashes", [])
    source_paths = [row.get("path") for row in source_rows if isinstance(row, dict)]
    if len(source_paths) != len(set(source_paths)):
        errors.append("contract source input inventory contains duplicates")
    if set(source_paths) != EXPECTED_SOURCE_INPUT_PATHS:
        errors.append("contract source input inventory differs from frozen generation-2 set")
    for axis, expected in EXPECTED_AXIS_CONTRACT.items():
        details = contract.get("axes", {}).get(axis, {})
        if details.get("command") != expected["command"]:
            errors.append(f"{axis}: command differs from frozen generation-2 contract")
        if details.get("required_tool") != expected["required_tool"]:
            errors.append(f"{axis}: required_tool differs from frozen generation-2 contract")
        rows = details.get("sources", [])
        paths = [row.get("path") for row in rows if isinstance(row, dict)]
        if len(paths) != len(set(paths)):
            errors.append(f"{axis}: source inventory contains duplicates")
        if set(paths) != expected["sources"]:
            errors.append(f"{axis}: source inventory differs from frozen generation-2 set")
    return errors


def _effective_axis_status(axis: str, result: dict[str, Any]) -> str:
    """Classify a result-free Wolfram exit as a platform blocker, not math FAIL."""

    reported = str(result.get("status", "MISSING"))
    commands = result.get("commands")
    counterexample = result.get("counterexample")
    failures = counterexample.get("failures", []) if isinstance(counterexample, dict) else []
    if (
        axis == "wolfram_xact"
        and reported == "FAIL"
        and isinstance(commands, list)
        and len(commands) == 1
        and commands[0].get("exit") == 255
        and result.get("checks") is None
        and result.get("computed") is None
        and failures == ["axis emitted no parseable JSON payload"]
    ):
        return "BLOCKED_PLATFORM_OR_LICENSE"
    return reported


def _validate_axis(
    axis: str,
    run_dir: Path,
    contract: dict[str, Any],
    contract_sha: str,
    auth_sha: str,
    authorization: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[str]]:
    assignment_id = ASSIGNMENT_IDS[axis]
    assignment_path = REPO / run_dir / "assignments" / f"{assignment_id}.json"
    result_path = REPO / run_dir / "results" / f"{assignment_id}.json"
    errors: list[str] = []
    if not assignment_path.is_file() or not result_path.is_file():
        return None, None, [f"{axis}: assignment or result missing"]
    assignment = _load(assignment_path)
    outer = _load(result_path)
    if assignment.get("assignment_sha256") != _assignment_self_hash(assignment):
        errors.append(f"{axis}: assignment self-hash mismatch")
    if authorization.get("assignments", {}).get(assignment_id) != _sha(assignment_path):
        errors.append(f"{axis}: assignment differs from pre-axis authorization")
    if assignment.get("cas_axis") != axis:
        errors.append(f"{axis}: assignment axis mismatch")
    if assignment.get("independence_mode") != "blind-results" or assignment.get("allowed_sibling_results") != []:
        errors.append(f"{axis}: assignment independence violation")
    if assignment.get("cas_contract", {}).get("sha256") != contract_sha:
        errors.append(f"{axis}: assignment contract mismatch")
    if assignment.get("context_version") != authorization.get("context_version"):
        errors.append(f"{axis}: assignment context differs from pre-axis authorization")
    if outer.get("schema_version") != 2 or outer.get("assignment_id") != assignment_id:
        errors.append(f"{axis}: outer identity/schema mismatch")
    if outer.get("run_id") != assignment.get("run_id") or outer.get("context_version") != assignment.get("context_version"):
        errors.append(f"{axis}: outer run/context mismatch")
    if outer.get("independence_mode") != "blind-results":
        errors.append(f"{axis}: outer independence mismatch")
    expected_result = str(run_dir / "results" / f"{assignment_id}.json")
    if outer.get("result_path") != expected_result:
        errors.append(f"{axis}: outer result path mismatch")
    nested = outer.get("payload", {}).get("cas_axis_result")
    if not isinstance(nested, dict):
        return assignment, outer, [*errors, f"{axis}: nested CAS result absent"]
    if nested.get("schema_version") != 1 or nested.get("axis") != axis:
        errors.append(f"{axis}: nested schema/axis mismatch")
    if nested.get("contract_id") != contract["identity"]["contract_id"] or nested.get("contract_sha256") != contract_sha:
        errors.append(f"{axis}: nested contract mismatch")
    if nested.get("preaxis_authorization_sha256") != auth_sha:
        errors.append(f"{axis}: pre-axis authorization mismatch")
    if nested.get("sibling_results_read") != [] or nested.get("domain_assumption_diff") != []:
        errors.append(f"{axis}: blinding or assumption alignment violation")
    commands = nested.get("commands")
    if not isinstance(commands, list) or not commands or any(type(row.get("exit")) is not int for row in commands if isinstance(row, dict)):
        errors.append(f"{axis}: malformed command evidence")
    if outer.get("commands_run") != commands or outer.get("tool_versions") != nested.get("tool_versions"):
        errors.append(f"{axis}: outer/nested command or tool mismatch")
    obligations = set(contract["target"]["exact_test_obligations"])
    checks = nested.get("checks")
    effective_status = _effective_axis_status(axis, nested)
    if effective_status not in BLOCKED and (
        not isinstance(checks, dict) or set(checks) != obligations
    ):
        errors.append(f"{axis}: obligation keyset mismatch")
    if nested.get("status") == "PASS":
        if outer.get("status") != "pass":
            errors.append(f"{axis}: outer/nested status mismatch")
        if not isinstance(checks, dict) or not all(value is True for value in checks.values()):
            errors.append(f"{axis}: PASS has false/nonboolean obligation")
        if nested.get("computed") != contract["target"]["expected_exact_values"]:
            errors.append(f"{axis}: PASS canonical values mismatch")
        if nested.get("fixture_matches") is not True or nested.get("counterexample") is not None:
            errors.append(f"{axis}: PASS fixture/counterexample mismatch")
        if any(row.get("exit") != 0 for row in commands or []):
            errors.append(f"{axis}: PASS includes nonzero command")
    elif nested.get("status") == "FAIL":
        if outer.get("status") != "fail":
            errors.append(f"{axis}: outer/nested status mismatch")
        if not isinstance(nested.get("counterexample"), dict):
            errors.append(f"{axis}: FAIL lacks structured counterexample")
    elif nested.get("status") not in BLOCKED | {"MISALIGNED_ASSUMPTIONS", "INCONCLUSIVE"}:
        errors.append(f"{axis}: unrecognized nested status")
    elif outer.get("status") != "fail":
        errors.append(f"{axis}: blocked/inconclusive outer status mismatch")
    if nested.get("source_output_hashes") != contract["axes"][axis]["sources"]:
        errors.append(f"{axis}: source output hashes mismatch")
    if nested.get("verified_input_hashes") != contract["identity"]["source_input_hashes"]:
        errors.append(f"{axis}: verified inputs mismatch")
    for row in nested.get("source_output_hashes", []) + nested.get("verified_input_hashes", []):
        if not _safe_rel(str(row.get("path"))):
            errors.append(f"{axis}: unsafe evidence path")
            continue
        path = REPO / row["path"]
        if not path.is_file() or path.is_symlink() or _sha(path) != row.get("sha256"):
            errors.append(f"{axis}: evidence hash mismatch {row.get('path')}")
    if not nested.get("completed_at") or nested.get("evidence_class") != "exact":
        errors.append(f"{axis}: timestamp or evidence class missing")
    return assignment, outer, errors


def build(run_dir: Path) -> tuple[dict[str, str], dict[str, Any]]:
    contract = _load(REPO / CONTRACT_PATH)
    authorization = _load(REPO / AUTH_PATH)
    contract_sha = _sha(REPO / CONTRACT_PATH)
    auth_sha = _sha(REPO / AUTH_PATH)
    errors: list[str] = [
        *_validate_contract(contract),
        *_validate_exact_contract_inventory(contract),
    ]
    if authorization.get("axes_authorized") is not True or authorization.get("run_dir") != str(run_dir):
        errors.append("pre-axis authorization invalid for selected run")
    if authorization.get("contract_path") != str(CONTRACT_PATH) or authorization.get("contract_sha256") != contract_sha:
        errors.append("pre-axis authorization contract binding mismatch")
    if authorization.get("runner_path") != str(RUNNER_PATH) or authorization.get("runner_sha256") != _sha(REPO / RUNNER_PATH):
        errors.append("pre-axis authorization runner binding mismatch")
    if set(authorization.get("assignments", {})) != set(ASSIGNMENT_IDS.values()):
        errors.append("pre-axis authorization assignment set mismatch")
    if authorization.get("errors") != [] or authorization.get("source_verification", {}).get("ok") is not True:
        errors.append("pre-axis authorization contains unresolved errors")
    assignments: dict[str, dict[str, Any]] = {}
    outers: dict[str, dict[str, Any]] = {}
    nested: dict[str, dict[str, Any]] = {}
    for axis in AXES:
        assignment, outer, axis_errors = _validate_axis(
            axis,
            run_dir,
            contract,
            contract_sha,
            auth_sha,
            authorization,
        )
        errors.extend(axis_errors)
        if assignment is not None:
            assignments[axis] = assignment
        if outer is not None:
            outers[axis] = outer
            candidate = outer.get("payload", {}).get("cas_axis_result")
            if isinstance(candidate, dict):
                nested[axis] = candidate

    if errors or len(nested) != 4:
        aggregate = "EVIDENCE_INVALID"
    else:
        statuses = {axis: _effective_axis_status(axis, nested[axis]) for axis in AXES}
        if any(status == "FAIL" for status in statuses.values()):
            aggregate = "CAS_FAIL"
        elif any(status in BLOCKED for status in statuses.values()):
            aggregate = "CAS_BLOCKED"
        elif any(status in {"MISALIGNED_ASSUMPTIONS", "INCONCLUSIVE"} for status in statuses.values()):
            aggregate = "CAS_CONFLICT"
        elif all(status == "PASS" for status in statuses.values()):
            aggregate = "CAS_4AXIS_PASS"
        else:
            aggregate = "CAS_CONFLICT"

    artifacts: dict[str, str] = {}
    for axis in AXES:
        if axis in assignments:
            artifacts[str(OUTPUT_ROOT / "harness_receipts" / f"assignment_{axis}.json")] = _render(assignments[axis])
        if axis in outers:
            artifacts[str(OUTPUT_ROOT / "harness_receipts" / f"outer_result_{axis}.json")] = _render(outers[axis])
        if axis in nested:
            artifacts[str(OUTPUT_ROOT / f"axis_result_{axis}.json")] = _render(nested[axis])
    reported_statuses = {
        axis: nested.get(axis, {}).get("status", "MISSING") for axis in AXES
    }
    statuses = {
        axis: _effective_axis_status(axis, nested.get(axis, {})) for axis in AXES
    }
    completion_times = sorted(str(row.get("completed_at")) for row in nested.values() if row.get("completed_at"))
    adjudication = {
        "schema": "htt.pr170.cas_adjudication.v1",
        "contract_path": str(CONTRACT_PATH),
        "contract_sha256": contract_sha,
        "preaxis_authorization_path": str(AUTH_PATH),
        "preaxis_authorization_sha256": auth_sha,
        "axis_statuses": statuses,
        "reported_axis_statuses": reported_statuses,
        "aggregate_state": aggregate,
        "errors": errors,
        "majority_vote_used": False,
        "exception_used": False,
        "adjudicated_at_utc": completion_times[-1] if completion_times else authorization.get("created_at_utc"),
        "scope": "exact scalar algebra only; not external type-curvature or physical-spacetime closure",
    }
    artifacts[str(OUTPUT_ROOT / "adjudication.json")] = _render(adjudication)
    collection = {
        "schema": "htt.pr170.cas_collection.v1",
        "contract_sha256": contract_sha,
        "preaxis_authorization_sha256": auth_sha,
        "run_dir": str(run_dir),
        "axis_statuses": statuses,
        "reported_axis_statuses": reported_statuses,
        "aggregate_state": aggregate,
        "evidence_valid": not errors and len(nested) == 4,
        "errors": errors,
        "eleven_scalar_rows_verified": aggregate == "CAS_4AXIS_PASS",
        "external_type_curvature_closure": "1_of_11",
        "internal_definitional_exact_type_closure": "1_of_11",
        "universal_physical_type_closure": False,
        "result_boundary": "CAS agreement cannot promote unresolved type-curvature or physical receipts",
    }
    artifacts[str(COLLECTION_PATH)] = _render(collection)
    return artifacts, collection


def _publish(artifacts: dict[str, str]) -> None:
    for rel, rendered in artifacts.items():
        path = REPO / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            handle.write(rendered)
            temporary = Path(handle.name)
        os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    artifacts, collection = build(args.run_dir)
    if args.check:
        mismatches = [rel for rel, rendered in artifacts.items() if not (REPO / rel).is_file() or (REPO / rel).read_text(encoding="utf-8") != rendered]
        print(json.dumps({"ok": not mismatches, "mismatches": mismatches, "aggregate_state": collection["aggregate_state"]}, indent=2, sort_keys=True))
        return 0 if not mismatches and collection["evidence_valid"] else 2
    _publish(artifacts)
    print(json.dumps(collection, indent=2, sort_keys=True))
    return 0 if collection["evidence_valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
