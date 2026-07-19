#!/usr/bin/env python3
"""Execute one blind PR-170 CAS axis and seal its result envelope."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
CONTRACT_PATH = Path("docs/generated/pr170_cas/CAS_CONTRACT_PR170_BUCHERT_TWO_PATCH.json")
AUTHORIZATION_PATH = Path("docs/generated/pr170_cas/preaxis_authorization.json")
AXES = ("wolfram_xact", "sympy", "sage_singular", "lean")
ASSIGNMENT_IDS = {
    "wolfram_xact": "A-PR170-CAS-WOLFRAM",
    "sympy": "A-PR170-CAS-SYMPY",
    "sage_singular": "A-PR170-CAS-SAGE",
    "lean": "A-PR170-CAS-LEAN",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(rendered)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if not (line.startswith("{") and line.endswith("}")):
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None


def _run(command: list[str], cwd: Path, *, env: dict[str, str] | None = None) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=1800,
            env=env,
            check=False,
        )
        return completed.returncode, completed.stdout, completed.stderr
    except FileNotFoundError as exc:
        return 127, "", str(exc)
    except subprocess.TimeoutExpired as exc:
        return 124, exc.stdout or "", exc.stderr or "axis timeout"


def _validate_contract(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if contract.get("schema_version") != 2:
        errors.append("contract schema_version is not 2")
    if set(contract.get("axes", {})) != set(AXES):
        errors.append("contract axis set differs from required four axes")
    if contract.get("exceptions_adjudication", {}).get("preregistered_exceptions") != []:
        errors.append("PR-170 contract must not register an exception")
    identity = contract.get("identity")
    if not isinstance(identity, dict):
        errors.append("contract identity must be an object")
        identity = {}
    for field in ("contract_id", "statement", "pr_id"):
        if not isinstance(identity.get(field), str) or not identity.get(field, "").strip():
            errors.append(f"contract identity {field} must be nonblank")
    source_inputs = identity.get("source_input_hashes")
    if not isinstance(source_inputs, list) or not source_inputs:
        errors.append("contract must bind at least one source input hash")
        source_inputs = []
    for row in source_inputs:
        if not isinstance(row, dict) or not _valid_hash_row(row):
            errors.append("contract source input row is malformed")
            continue
        path = REPO / str(row.get("path"))
        if not path.is_file() or _sha(path) != row.get("sha256"):
            errors.append(f"source input hash mismatch: {row.get('path')}")
    for axis, details in contract.get("axes", {}).items():
        if not isinstance(details, dict):
            errors.append(f"{axis} contract details must be an object")
            continue
        for field in ("command", "required_tool"):
            if not isinstance(details.get(field), str) or not details.get(field, "").strip():
                errors.append(f"{axis} {field} must be nonblank")
        sources = details.get("sources")
        if not isinstance(sources, list) or not sources:
            errors.append(f"{axis} must bind at least one axis source")
            sources = []
        for row in sources:
            if not isinstance(row, dict) or not _valid_hash_row(row):
                errors.append(f"{axis} source row is malformed")
                continue
            path = REPO / str(row.get("path"))
            if not path.is_file() or _sha(path) != row.get("sha256"):
                errors.append(f"{axis} source hash mismatch: {row.get('path')}")
    obligations = contract.get("target", {}).get("exact_test_obligations")
    expected = contract.get("target", {}).get("expected_exact_values")
    if not isinstance(obligations, list) or len(obligations) != 15 or len(set(obligations)) != 15:
        errors.append("contract must define exactly fifteen unique obligations")
    if not isinstance(expected, dict) or len(expected) != 16:
        errors.append("contract must define exactly sixteen expected values")
    types = contract.get("target", {}).get("canonical_type_registry")
    if not isinstance(types, list) or len(types) != 11 or len(set(types)) != 11:
        errors.append("contract must define eleven unique canonical Bianchi labels")
    return errors


def _valid_hash_row(row: dict[str, Any]) -> bool:
    path = row.get("path")
    digest = row.get("sha256")
    if not isinstance(path, str) or not path or Path(path).is_absolute() or ".." in Path(path).parts:
        return False
    return isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest) is not None


def _execute(axis: str) -> tuple[dict[str, Any] | None, list[dict[str, Any]], str]:
    commands: list[dict[str, Any]] = []
    if axis == "sympy":
        executable = str(REPO / "venv/bin/python") if (REPO / "venv/bin/python").is_file() else sys.executable
        command = [executable, "-B", str(REPO / "htt/src/common/pr170_sympy_axis.py")]
        code, stdout, stderr = _run(command, REPO)
        commands.append({"cmd": " ".join(command), "cwd": ".", "exit": code})
        return _last_json(stdout), commands, (stdout + stderr)[-12000:]
    if axis == "wolfram_xact":
        command = ["wolframscript", "-file", str(REPO / "wolfram/pr170_buchert_two_patch_axis.wls")]
        code, stdout, stderr = _run(command, REPO)
        commands.append({"cmd": " ".join(command), "cwd": ".", "exit": code})
        return _last_json(stdout), commands, (stdout + stderr)[-12000:]
    if axis == "sage_singular":
        environment = os.environ.copy()
        environment["DOT_SAGE"] = tempfile.mkdtemp(prefix="htt_pr170_sage_")
        command = ["sage", str(REPO / "sage/pr170_buchert_two_patch_axis.sage")]
        code, stdout, stderr = _run(command, REPO, env=environment)
        commands.append({"cmd": " ".join(command), "cwd": ".", "exit": code})
        return _last_json(stdout), commands, (stdout + stderr)[-12000:]

    build = ["lake", "build"]
    code, stdout, stderr = _run(build, REPO / "formal_pr170")
    commands.append({"cmd": "lake build", "cwd": "formal_pr170", "exit": code})
    transcript = stdout + stderr
    if code != 0:
        return None, commands, transcript[-12000:]
    execute = ["lake", "exe", "pr170bucherttwopatch"]
    code, stdout, stderr = _run(execute, REPO / "formal_pr170")
    commands.append({"cmd": "lake exe pr170bucherttwopatch", "cwd": "formal_pr170", "exit": code})
    transcript += stdout + stderr
    return _last_json(stdout), commands, transcript[-12000:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--axis", required=True, choices=AXES)
    parser.add_argument("--run-dir", required=True, type=Path)
    args = parser.parse_args()

    axis = args.axis
    assignment_id = ASSIGNMENT_IDS[axis]
    assignment_path = REPO / args.run_dir / "assignments" / f"{assignment_id}.json"
    result_path = REPO / args.run_dir / "results" / f"{assignment_id}.json"
    assignment = _json(assignment_path)
    contract = _json(REPO / CONTRACT_PATH)
    errors = _validate_contract(contract)
    if errors:
        raise SystemExit("contract validation failed before axis run: " + "; ".join(errors))
    if assignment.get("assignment_sha256") != _sha_for_assignment(assignment):
        raise SystemExit("assignment self-hash mismatch")
    if assignment.get("cas_axis") != axis:
        raise SystemExit("assignment CAS axis mismatch")
    if assignment.get("independence_mode") != "blind-results":
        raise SystemExit("assignment is not blind-results")
    if assignment.get("allowed_sibling_results") != []:
        raise SystemExit("blind assignment unexpectedly allows sibling results")
    contract_sha = _sha(REPO / CONTRACT_PATH)
    if assignment.get("cas_contract", {}).get("sha256") != contract_sha:
        raise SystemExit("assignment contract hash mismatch")
    for row in assignment.get("required_inputs", []):
        path = REPO / str(row.get("path"))
        if not path.is_file() or _sha(path) != row.get("sha256"):
            raise SystemExit(f"assignment input hash mismatch: {row.get('path')}")
    authorization = _json(REPO / AUTHORIZATION_PATH)
    if authorization.get("axes_authorized") is not True:
        raise SystemExit("pre-axis authorization is not active")
    if authorization.get("run_dir") != str(args.run_dir):
        raise SystemExit("pre-axis authorization run mismatch")
    if authorization.get("contract_sha256") != contract_sha:
        raise SystemExit("pre-axis authorization contract hash mismatch")
    if authorization.get("runner_sha256") != _sha(Path(__file__)):
        raise SystemExit("pre-axis authorization runner hash mismatch")
    if authorization.get("assignments", {}).get(assignment_id) != _sha(assignment_path):
        raise SystemExit("pre-axis authorization assignment hash mismatch")
    authorization_sha = _sha(REPO / AUTHORIZATION_PATH)

    payload, commands, transcript = _execute(axis)
    failures: list[str] = []
    status = "PASS"
    if commands[-1]["exit"] in {124, 127}:
        status = "BLOCKED_PLATFORM_OR_LICENSE"
        failures.append("required axis tool unavailable or timed out")
    elif payload is None:
        status = "FAIL"
        failures.append("axis emitted no parseable JSON payload")
    else:
        if any(row["exit"] != 0 for row in commands):
            failures.append("one or more axis commands returned nonzero")
        obligations = set(contract["target"]["exact_test_obligations"])
        checks = payload.get("checks")
        if not isinstance(checks, dict) or set(checks) != obligations:
            failures.append("axis exact check keyset mismatch")
        elif not all(value is True for value in checks.values()):
            failures.append("one or more registered exact checks failed")
        if payload.get("computed") != contract["target"]["expected_exact_values"]:
            failures.append("axis canonical values differ from contract")
        if payload.get("fixture_matches") is not True or payload.get("all_pass") is not True:
            failures.append("axis fixture/all-pass receipt is false")
        if axis == "wolfram_xact" and payload.get("xact_loaded") is not True:
            failures.append("xAct/xTensor was not loaded")
        if failures:
            status = "FAIL"

    nested = {
        "schema_version": 1,
        "axis": axis,
        "contract_id": contract["identity"]["contract_id"],
        "contract_sha256": contract_sha,
        "preaxis_authorization_sha256": authorization_sha,
        "status": status,
        "commands": commands,
        "tool_versions": {
            "reported": (payload or {}).get("engine_version", "unavailable"),
            "singular": (payload or {}).get("singular_version"),
            "xact_loaded": (payload or {}).get("xact_loaded"),
        },
        "source_output_hashes": contract["axes"][axis]["sources"],
        "verified_input_hashes": contract["identity"]["source_input_hashes"],
        "domain_assumption_diff": [],
        "evidence_class": "exact",
        "checks": (payload or {}).get("checks"),
        "computed": (payload or {}).get("computed"),
        "fixture_matches": (payload or {}).get("fixture_matches"),
        "counterexample": None if not failures else {"failures": failures},
        "completed_at": _now(),
        "sibling_results_read": [],
        "transcript_tail": transcript,
    }
    outer = {
        "schema_version": 2,
        "run_id": assignment["run_id"],
        "assignment_id": assignment_id,
        "context_version": assignment["context_version"],
        "independence_mode": "blind-results",
        "status": "pass" if status == "PASS" else "fail",
        "claim_ids": assignment.get("claim_ids", []),
        "assumptions": [
            "the frozen Buchert conventions and domain guard hold",
            "the two-patch weights are exact positive rationals summing to one",
            "typed scalar rows do not assert type-curvature or physical closure",
        ],
        "commands_run": commands,
        "tool_versions": nested["tool_versions"],
        "evidence_refs": [str(CONTRACT_PATH), *[row["path"] for row in contract["axes"][axis]["sources"]]],
        "payload": {"cas_axis_result": nested},
        "result_path": str(args.run_dir / "results" / f"{assignment_id}.json"),
    }
    _write_json(result_path, outer)
    print(json.dumps({"axis": axis, "status": status, "result_path": str(result_path.relative_to(REPO))}, sort_keys=True))
    return 0 if status == "PASS" else 2


def _sha_for_assignment(assignment: dict[str, Any]) -> str:
    material = dict(assignment)
    material.pop("assignment_sha256", None)
    rendered = json.dumps(material, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
