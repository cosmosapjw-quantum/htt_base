#!/usr/bin/env python3
"""Execute one blind PR-169 CAS axis and seal its harness envelope."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
CONTRACT_PATH = Path(
    "docs/generated/pr169_cas/CAS_CONTRACT_PR169_UNSIGNED_LEAKAGE.json"
)
AXES = ("wolfram_xact", "sympy", "sage_singular", "lean")
ASSIGNMENT_IDS = {
    "wolfram_xact": "A-PR169-CAS-WOLFRAM",
    "sympy": "A-PR169-CAS-SYMPY",
    "sage_singular": "A-PR169-CAS-SAGE",
    "lean": "A-PR169-CAS-LEAN",
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
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
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


def _contract_errors(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if contract.get("schema_version") != 2:
        errors.append("contract schema_version is not 2")
    if set(contract.get("axes", {})) != set(AXES):
        errors.append("contract axis set differs from the required four axes")
    if contract.get("exceptions_adjudication", {}).get(
        "preregistered_exceptions"
    ) != []:
        errors.append("PR-169 contract must not register an exception")
    for row in contract.get("identity", {}).get("source_input_hashes", []):
        path = REPO / str(row.get("path"))
        if not path.is_file() or _sha(path) != row.get("sha256"):
            errors.append(f"source input hash mismatch: {row.get('path')}")
    for axis, details in contract.get("axes", {}).items():
        for row in details.get("sources", []):
            path = REPO / str(row.get("path"))
            if not path.is_file() or _sha(path) != row.get("sha256"):
                errors.append(f"{axis} source hash mismatch: {row.get('path')}")
    obligations = contract.get("target", {}).get("exact_test_obligations")
    values = contract.get("target", {}).get("expected_exact_values")
    if not isinstance(obligations, list) or len(obligations) != 9:
        errors.append("contract must define exactly nine test obligations")
    if not isinstance(values, dict) or len(values) != 14:
        errors.append("contract must define exactly fourteen canonical values")
    return errors


def _run(
    command: list[str], cwd: Path, *, env: dict[str, str] | None = None
) -> tuple[int, str, str]:
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


def _execute(axis: str) -> tuple[dict[str, Any] | None, list[dict[str, Any]], str]:
    commands: list[dict[str, Any]] = []
    if axis == "sympy":
        python = REPO / "venv/bin/python"
        executable = str(python if python.is_file() else Path(sys.executable))
        command = [executable, "-B", str(REPO / "htt/src/common/pr169_sympy_axis.py")]
        code, stdout, stderr = _run(command, REPO)
        commands.append({"cmd": " ".join(command), "cwd": ".", "exit": code})
        return _last_json(stdout), commands, (stdout + stderr)[-12000:]
    if axis == "wolfram_xact":
        command = [
            "wolframscript", "-file",
            str(REPO / "wolfram/pr169_unsigned_leakage_axis.wls"),
        ]
        code, stdout, stderr = _run(command, REPO)
        commands.append({"cmd": " ".join(command), "cwd": ".", "exit": code})
        return _last_json(stdout), commands, (stdout + stderr)[-12000:]
    if axis == "sage_singular":
        environment = os.environ.copy()
        environment["DOT_SAGE"] = tempfile.mkdtemp(prefix="htt_pr169_sage_")
        command = ["sage", str(REPO / "sage/pr169_unsigned_leakage_axis.sage")]
        code, stdout, stderr = _run(command, REPO, env=environment)
        commands.append({"cmd": " ".join(command), "cwd": ".", "exit": code})
        return _last_json(stdout), commands, (stdout + stderr)[-12000:]

    build = ["lake", "build"]
    code, stdout, stderr = _run(build, REPO / "formal_pr169")
    commands.append({"cmd": "lake build", "cwd": "formal_pr169", "exit": code})
    transcript = stdout + stderr
    if code != 0:
        return None, commands, transcript[-12000:]
    execute = ["lake", "exe", "pr169unsignedleakage"]
    code, stdout, stderr = _run(execute, REPO / "formal_pr169")
    commands.append({
        "cmd": "lake exe pr169unsignedleakage",
        "cwd": "formal_pr169",
        "exit": code,
    })
    transcript += stdout + stderr
    return _last_json(stdout), commands, transcript[-12000:]


def main() -> None:
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
    errors = _contract_errors(contract)
    if errors:
        raise SystemExit("contract validation failed before axis run: " + "; ".join(errors))
    if assignment.get("cas_axis") != axis:
        raise SystemExit("assignment CAS axis mismatch")
    if assignment.get("independence_mode") != "blind-results":
        raise SystemExit("assignment is not blind-results")
    if assignment.get("allowed_sibling_results") != []:
        raise SystemExit("blind assignment unexpectedly allows sibling results")

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
        if commands[-1]["exit"] != 0:
            failures.append("axis command returned nonzero")
        expected_checks = set(contract["target"]["exact_test_obligations"])
        checks = payload.get("checks")
        if not isinstance(checks, dict) or set(checks) != expected_checks:
            failures.append("axis exact check keyset mismatch")
        elif not all(value is True for value in checks.values()):
            failures.append("one or more registered exact checks failed")
        if payload.get("computed") != contract["target"]["expected_exact_values"]:
            failures.append("axis canonical values differ from contract")
        if payload.get("fixture_matches") is not True:
            failures.append("registered fixture receipt is false")
        if payload.get("all_pass") is not True:
            failures.append("axis all_pass is not true")
        if failures:
            status = "FAIL"

    contract_sha = _sha(REPO / CONTRACT_PATH)
    nested = {
        "schema_version": 1,
        "axis": axis,
        "contract_id": contract["identity"]["contract_id"],
        "contract_sha256": contract_sha,
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
        "claim_ids": assignment["claim_ids"],
        "evidence_refs": [
            CONTRACT_PATH.as_posix(),
            *[row["path"] for row in contract["axes"][axis]["sources"]],
        ],
        "assumptions": contract["semantics"]["assumptions"],
        "tool_versions": nested["tool_versions"],
        "commands_run": commands,
        "result_path": result_path.relative_to(REPO).as_posix(),
        "payload": {"cas_axis_result": nested},
    }
    _write_json(result_path, outer)
    print(json.dumps({
        "ok": status == "PASS",
        "axis": axis,
        "axis_status": status,
        "result_path": outer["result_path"],
        "result_sha256": _sha(result_path),
        "failures": failures,
    }, indent=2))
    raise SystemExit(0 if status == "PASS" else 2)


if __name__ == "__main__":
    main()

