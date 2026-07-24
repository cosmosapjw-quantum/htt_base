#!/usr/bin/env python3
"""Validate both frozen PR-169 CAS attempts as historical diagnostics.

The collector is deliberately not an adjudicator shortcut.  It first binds each
assignment to its self-hash, required inputs, declared result path, contract,
outer harness envelope, and complete nested CAS result.  Only then may the four
axis statuses be aggregated.  Version-1 inputs that were intentionally replaced
by the repaired version-2 run can resolve only through the immutable text source
snapshot stored with the v1 failure evidence; v2 never receives that fallback.
Neither stored attempt supplies current CAS authority; only parent-observed
``cas_gate.py run-adjudicate`` execution can do so.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[2]
AXES = ("wolfram_xact", "sympy", "sage_singular", "lean")
HEX64 = re.compile(r"[0-9a-f]{64}")
VERSIONS = {
    "v1": {
        "run_id": "pr169-cas-20260719",
        "contract": "docs/generated/pr169_cas/CAS_CONTRACT_PR169_UNSIGNED_LEAKAGE.json",
        "contract_sha256": "b4b2cf6a247209ff22406b7c1f493387934b9e4d2b2824b396a8f3fbc23c2781",
        "ids": {
            "wolfram_xact": "A-PR169-CAS-WOLFRAM",
            "sympy": "A-PR169-CAS-SYMPY",
            "sage_singular": "A-PR169-CAS-SAGE",
            "lean": "A-PR169-CAS-LEAN",
        },
        "expected_aggregate": "CAS_FAIL",
    },
    "v2": {
        "run_id": "pr169-cas-v2-20260719",
        "contract": "docs/generated/pr169_cas/CAS_CONTRACT_PR169_UNSIGNED_LEAKAGE_V2.json",
        "contract_sha256": "963e19b76eec31c74c27c0b014a80484f798528ab5c7cf5dab067f50916b5aad",
        "ids": {
            "wolfram_xact": "A-PR169-CAS-V2-WOLFRAM",
            "sympy": "A-PR169-CAS-V2-SYMPY",
            "sage_singular": "A-PR169-CAS-V2-SAGE",
            "lean": "A-PR169-CAS-V2-LEAN",
        },
        "expected_aggregate": "CAS_4AXIS_PASS",
    },
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _render(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()


def _canonical_assignment_sha256(assignment: dict[str, Any]) -> str:
    unsigned = dict(assignment)
    claimed = unsigned.pop("assignment_sha256", None)
    if not isinstance(claimed, str) or not HEX64.fullmatch(claimed):
        raise ValueError("assignment_sha256 is absent or malformed")
    sealed = json.dumps(unsigned, sort_keys=True, ensure_ascii=False).encode("utf-8")
    actual = hashlib.sha256(sealed).hexdigest()
    if actual != claimed:
        raise ValueError(f"assignment self-hash mismatch: {actual} != {claimed}")
    return actual


def _safe_repo_path(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} path is absent")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{label} path is not repository-relative: {value}")
    return path.as_posix()


def _validate_hashed_refs(refs: object, *, label: str) -> list[dict[str, str]]:
    if not isinstance(refs, list) or not refs:
        raise ValueError(f"{label} must be a non-empty list")
    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, ref in enumerate(refs):
        if not isinstance(ref, dict) or set(ref) != {"path", "sha256"}:
            raise ValueError(f"{label}[{index}] must contain only path and sha256")
        path = _safe_repo_path(ref["path"], label=f"{label}[{index}]")
        digest = ref["sha256"]
        if not isinstance(digest, str) or not HEX64.fullmatch(digest):
            raise ValueError(f"{label}[{index}] has malformed sha256")
        if path in seen:
            raise ValueError(f"{label} contains duplicate path: {path}")
        seen.add(path)
        normalized.append({"path": path, "sha256": digest})
    return normalized


def _resolve_input(version: str, ref: dict[str, str]) -> dict[str, str]:
    requested = ref["path"]
    expected = ref["sha256"]
    current = REPO / requested
    if current.is_file() and _sha(current) == expected:
        return {
            "requested_path": requested,
            "expected_sha256": expected,
            "resolved_path": requested,
            "resolution": "current_repository_input",
        }
    if version == "v1":
        snapshot_rel = Path("docs/generated/pr169_cas/v1/source_snapshot") / requested
        snapshot = REPO / snapshot_rel
        if snapshot.is_file() and _sha(snapshot) == expected:
            return {
                "requested_path": requested,
                "expected_sha256": expected,
                "resolved_path": snapshot_rel.as_posix(),
                "resolution": "sealed_v1_source_snapshot",
            }
    current_status = _sha(current) if current.is_file() else "missing"
    raise ValueError(
        f"{version} required input drift: {requested} expected {expected}, "
        f"current {current_status}"
    )


def _dedupe_refs(groups: Iterable[list[dict[str, str]]]) -> list[dict[str, str]]:
    by_path: dict[str, str] = {}
    for refs in groups:
        for ref in refs:
            prior = by_path.setdefault(ref["path"], ref["sha256"])
            if prior != ref["sha256"]:
                raise ValueError(
                    f"one evidence bundle assigns two hashes to {ref['path']}"
                )
    return [
        {"path": path, "sha256": digest}
        for path, digest in sorted(by_path.items())
    ]


def _validate_assignment(
    version: str,
    config: dict[str, Any],
    axis: str,
    assignment: dict[str, Any],
) -> list[dict[str, str]]:
    assignment_id = config["ids"][axis]
    _canonical_assignment_sha256(assignment)
    expected_result = (
        f".agent-harness/runs/{config['run_id']}/results/{assignment_id}.json"
    )
    exact = {
        "schema_version": 2,
        "run_id": config["run_id"],
        "assignment_id": assignment_id,
        "independence_mode": "blind-results",
        "cas_axis": axis,
        "status": "registered",
        "result_path": expected_result,
    }
    for key, expected in exact.items():
        if assignment.get(key) != expected:
            raise ValueError(
                f"{version}/{axis} assignment {key} drifted: "
                f"{assignment.get(key)!r} != {expected!r}"
            )
    if not isinstance(assignment.get("context_version"), str):
        raise ValueError(f"{version}/{axis} assignment context version absent")
    if assignment.get("allowed_sibling_results") != []:
        raise ValueError(f"{version}/{axis} allowed sibling results")
    claim_ids = assignment.get("claim_ids")
    if not isinstance(claim_ids, list) or not claim_ids or not all(
        isinstance(value, str) and value for value in claim_ids
    ):
        raise ValueError(f"{version}/{axis} assignment claim IDs invalid")
    if assignment.get("required_outputs") != [expected_result]:
        raise ValueError(f"{version}/{axis} required output is not canonical")
    contract_ref = assignment.get("cas_contract")
    expected_contract = {
        "path": config["contract"],
        "sha256": config["contract_sha256"],
    }
    if contract_ref != expected_contract:
        raise ValueError(f"{version}/{axis} assignment contract drifted")
    required_inputs = _validate_hashed_refs(
        assignment.get("required_inputs"), label=f"{version}/{axis} required_inputs"
    )
    if expected_contract not in required_inputs:
        raise ValueError(f"{version}/{axis} contract absent from required inputs")
    return required_inputs


def _nonempty_counterexample(value: object) -> bool:
    if not isinstance(value, dict) or not value:
        return False
    failures = value.get("failures")
    return isinstance(failures, list) and bool(failures) and all(
        isinstance(item, str) and item for item in failures
    )


def _validate_nested(
    version: str,
    config: dict[str, Any],
    contract: dict[str, Any],
    axis: str,
    nested: dict[str, Any],
) -> tuple[str, list[dict[str, str]], list[dict[str, str]]]:
    contract_id = contract["identity"]["contract_id"]
    exact = {
        "schema_version": 1,
        "axis": axis,
        "contract_id": contract_id,
        "contract_sha256": config["contract_sha256"],
        "evidence_class": "exact",
        "domain_assumption_diff": [],
        "sibling_results_read": [],
    }
    for key, expected in exact.items():
        if nested.get(key) != expected:
            raise ValueError(f"{version}/{axis} nested {key} drifted")

    commands = nested.get("commands")
    if not isinstance(commands, list) or not commands:
        raise ValueError(f"{version}/{axis} nested commands absent")
    exits: list[int] = []
    for command in commands:
        if (
            not isinstance(command, dict)
            or not isinstance(command.get("cmd"), str)
            or not isinstance(command.get("cwd"), str)
            or not isinstance(command.get("exit"), int)
        ):
            raise ValueError(f"{version}/{axis} malformed command receipt")
        exits.append(command["exit"])

    obligations = set(contract["target"]["exact_test_obligations"])
    expected_values = contract["target"]["expected_exact_values"]
    checks = nested.get("checks")
    computed = nested.get("computed")
    status = nested.get("status")
    if status == "PASS":
        if not isinstance(checks, dict) or set(checks) != obligations:
            raise ValueError(f"{version}/{axis} PASS check obligations incomplete")
        if not all(value is True for value in checks.values()):
            raise ValueError(f"{version}/{axis} PASS contains a false check")
        if computed != expected_values:
            raise ValueError(f"{version}/{axis} PASS computed values drifted")
        if nested.get("fixture_matches") is not True:
            raise ValueError(f"{version}/{axis} PASS fixture is not exact")
        if nested.get("counterexample") is not None:
            raise ValueError(f"{version}/{axis} PASS carries a counterexample")
        if any(exit_code != 0 for exit_code in exits):
            raise ValueError(f"{version}/{axis} PASS has nonzero command")
    elif status == "FAIL":
        if not _nonempty_counterexample(nested.get("counterexample")):
            raise ValueError(f"{version}/{axis} FAIL lacks counterexample receipt")
        if checks is not None and (
            not isinstance(checks, dict) or set(checks) != obligations
        ):
            raise ValueError(f"{version}/{axis} FAIL check keyset is malformed")
        false_or_missing_check = checks is None or any(
            value is not True for value in checks.values()
        )
        if not false_or_missing_check and not any(code != 0 for code in exits):
            raise ValueError(f"{version}/{axis} FAIL has no failing evidence")
        if checks is None and not any(code != 0 for code in exits):
            raise ValueError(
                f"{version}/{axis} missing checks require a nonzero command"
            )
    else:
        raise ValueError(f"{version}/{axis} unsupported nested status: {status}")

    contract_sources = _validate_hashed_refs(
        contract["axes"][axis]["sources"],
        label=f"{version}/{axis} contract axis sources",
    )
    nested_sources = _validate_hashed_refs(
        nested.get("source_output_hashes"),
        label=f"{version}/{axis} nested source hashes",
    )
    if nested_sources != contract_sources:
        raise ValueError(f"{version}/{axis} source hashes do not match contract")
    contract_inputs = _validate_hashed_refs(
        contract["identity"]["source_input_hashes"],
        label=f"{version} contract identity sources",
    )
    nested_inputs = _validate_hashed_refs(
        nested.get("verified_input_hashes"),
        label=f"{version}/{axis} nested verified inputs",
    )
    if nested_inputs != contract_inputs:
        raise ValueError(f"{version}/{axis} verified inputs do not match contract")
    return status, contract_sources, contract_inputs


def _validate_axis_evidence(
    version: str,
    config: dict[str, Any],
    contract: dict[str, Any],
    axis: str,
    assignment: dict[str, Any],
    outer: dict[str, Any],
) -> dict[str, Any]:
    """Validate one complete axis bundle; exposed for negative mutation tests."""

    required_inputs = _validate_assignment(version, config, axis, assignment)
    assignment_id = config["ids"][axis]
    result_path = assignment["result_path"]
    exact_outer = {
        "schema_version": 2,
        "run_id": config["run_id"],
        "assignment_id": assignment_id,
        "context_version": assignment["context_version"],
        "independence_mode": "blind-results",
        "claim_ids": assignment["claim_ids"],
        "result_path": result_path,
    }
    for key, expected in exact_outer.items():
        if outer.get(key) != expected:
            raise ValueError(f"{version}/{axis} outer {key} drifted")
    if set(outer.get("payload", {})) != {"cas_axis_result"}:
        raise ValueError(f"{version}/{axis} outer payload schema drifted")
    nested = outer["payload"]["cas_axis_result"]
    if not isinstance(nested, dict):
        raise ValueError(f"{version}/{axis} lacks nested CAS result")
    status, contract_sources, contract_inputs = _validate_nested(
        version, config, contract, axis, nested
    )
    expected_outer_status = "pass" if status == "PASS" else "fail"
    if outer.get("status") != expected_outer_status:
        raise ValueError(f"{version}/{axis} outer status does not match nested")
    if outer.get("commands_run") != nested.get("commands"):
        raise ValueError(f"{version}/{axis} outer commands do not match nested")
    if outer.get("tool_versions") != nested.get("tool_versions"):
        raise ValueError(f"{version}/{axis} outer tool versions do not match nested")

    all_refs = _dedupe_refs((required_inputs, contract_sources, contract_inputs))
    resolutions = [_resolve_input(version, ref) for ref in all_refs]
    return {
        "status": status,
        "nested": nested,
        "required_input_resolution": resolutions,
    }


def _publish(path: Path, content: bytes, *, check: bool) -> None:
    if check:
        if not path.is_file() or path.read_bytes() != content:
            raise ValueError(f"artifact differs from sealed expectation: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and path.read_bytes() == content:
        return
    with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _aggregate(statuses: dict[str, str]) -> str:
    if any(value == "FAIL" for value in statuses.values()):
        return "CAS_FAIL"
    if set(statuses) != set(AXES):
        return "CAS_BLOCKED"
    if all(value == "PASS" for value in statuses.values()):
        return "CAS_4AXIS_PASS"
    return "CAS_BLOCKED"


def _collect_version(version: str, config: dict[str, Any], *, check: bool) -> dict[str, Any]:
    contract_path = REPO / config["contract"]
    if _sha(contract_path) != config["contract_sha256"]:
        raise ValueError(f"{version} contract hash drifted")
    contract = _json(contract_path)

    statuses: dict[str, str] = {}
    completed: list[str] = []
    receipt_hashes: dict[str, dict[str, str]] = {}
    input_resolutions: dict[str, list[dict[str, str]]] = {}
    for axis in AXES:
        assignment_id = config["ids"][axis]
        source_dir = REPO / ".agent-harness/runs" / config["run_id"]
        assignment_source = source_dir / "assignments" / f"{assignment_id}.json"
        outer_source = source_dir / "results" / f"{assignment_id}.json"
        assignment = _json(assignment_source)
        outer = _json(outer_source)
        validated = _validate_axis_evidence(
            version, config, contract, axis, assignment, outer
        )
        nested = validated["nested"]

        destination = REPO / f"docs/generated/pr169_cas/{version}"
        assignment_target = destination / "harness_receipts" / f"assignment_{axis}.json"
        outer_target = destination / "harness_receipts" / f"outer_result_{axis}.json"
        normalized_target = destination / f"axis_result_{axis}.json"
        _publish(assignment_target, assignment_source.read_bytes(), check=check)
        _publish(outer_target, outer_source.read_bytes(), check=check)
        _publish(normalized_target, _render(nested), check=check)
        statuses[axis] = validated["status"]
        completed_at = nested.get("completed_at")
        if not isinstance(completed_at, str) or not completed_at:
            raise ValueError(f"{version}/{axis} completion timestamp absent")
        completed.append(completed_at)
        input_resolutions[axis] = validated["required_input_resolution"]
        receipt_hashes[axis] = {
            "assignment_sha256": _sha(assignment_source),
            "outer_result_sha256": _sha(outer_source),
            "normalized_result_sha256": hashlib.sha256(_render(nested)).hexdigest(),
        }

    aggregate = _aggregate(statuses)
    if aggregate != config["expected_aggregate"]:
        raise ValueError(
            f"{version} aggregate {aggregate} != {config['expected_aggregate']}"
        )
    adjudication = {
        "schema_version": 1,
        "contract_id": contract["identity"]["contract_id"],
        "contract_sha256": config["contract_sha256"],
        "aggregate_status": aggregate,
        "axis_statuses": statuses,
        "missing_axes": [],
        "exceptions_applied": [],
        "errors": [],
        "adjudicated_from_axis_receipts_at": max(completed),
        "note": (
            "CAS_4AXIS_PASS requires four validated PASS envelopes under one "
            "contract hash; majority vote and unvalidated receipt synthesis are forbidden."
        ),
    }
    adjudication_path = REPO / f"docs/generated/pr169_cas/adjudication_{version}.json"
    _publish(adjudication_path, _render(adjudication), check=check)
    return {
        "contract_path": config["contract"],
        "contract_sha256": config["contract_sha256"],
        "aggregate_status": aggregate,
        "axis_statuses": statuses,
        "adjudication_path": adjudication_path.relative_to(REPO).as_posix(),
        "adjudication_sha256": hashlib.sha256(_render(adjudication)).hexdigest(),
        "receipt_hashes": receipt_hashes,
        "required_input_resolution": input_resolutions,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        print(
            "refusing to overwrite frozen historical PR-169 CAS receipts; "
            "current authority requires cas_gate.py run-adjudicate",
            file=sys.stderr,
        )
        return 2

    versions = {
        version: _collect_version(version, config, check=True)
        for version, config in VERSIONS.items()
    }
    receipt = {
        "schema": "htt.pr169.cas_collection_receipt.v2",
        "validation_profile": {
            "assignment_self_hash": "required",
            "required_input_hashes": "required_with_v1_snapshot_only_fallback",
            "outer_nested_alignment": "required",
            "exact_obligation_keyset": "required_for_PASS_and_parseable_FAIL",
            "pass_value_equality": "required",
        },
        "versions": versions,
        "v1_disposition": (
            "CAS_FAIL: registered projection fixture and Lean executable "
            "harness were defective; no v1 result is reusable as PASS"
        ),
        "v2_disposition": "fresh four-axis rerun after hash-changing harness repair",
        "cross_version_result_reuse": False,
        "exceptions": [],
    }
    target = REPO / "docs/generated/pr169_cas_collection_receipt.json"
    _publish(target, _render(receipt), check=True)
    print(json.dumps({
        "ok": False,
        "mode": "historical_replay_check",
        "path": target.relative_to(REPO).as_posix(),
        "sha256": _sha(target),
        "current_aggregate": "CAS_BLOCKED",
        "historical_aggregates": {
            version: row["aggregate_status"] for version, row in versions.items()
        },
        "stored_cas_diagnostic_only": True,
        "claim_promotion_cas_eligible": False,
    }, indent=2))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
