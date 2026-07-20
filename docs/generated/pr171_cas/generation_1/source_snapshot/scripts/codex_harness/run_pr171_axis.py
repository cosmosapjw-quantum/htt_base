#!/usr/bin/env python3
"""Execute one blind PR-171 CAS axis and seal its harness envelope."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pr171_cas_support import (
    ASSIGNMENT_IDS,
    AUTH_PATH,
    AXES,
    CONTRACT_PATH,
    REPO,
    assignment_self_hash,
    atomic_write,
    load,
    render,
    sha,
    validate_contract,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed(stdout.splitlines()):
        try:
            value = json.loads(line.strip())
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None


def _run(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> tuple[int, str, str]:
    try:
        done = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            timeout=1800,
            check=False,
        )
        return done.returncode, done.stdout, done.stderr
    except FileNotFoundError as exc:
        return 127, "", str(exc)
    except subprocess.TimeoutExpired as exc:
        return 124, exc.stdout or "", exc.stderr or "axis timeout"


def _execute(axis: str) -> tuple[dict[str, Any] | None, list[dict[str, Any]], str]:
    commands: list[dict[str, Any]] = []
    if axis == "sympy":
        exe = str(REPO / "venv/bin/python") if (REPO / "venv/bin/python").is_file() else sys.executable
        command = [exe, "-B", str(REPO / "htt/src/common/pr171_sympy_axis.py")]
        code, stdout, stderr = _run(command, REPO)
        commands.append({"cmd": " ".join(command), "cwd": ".", "exit": code})
    elif axis == "sage_singular":
        env = os.environ.copy()
        env["DOT_SAGE"] = tempfile.mkdtemp(prefix="htt_pr171_sage_")
        command = ["sage", str(REPO / "sage/pr171_tilt_relaxation_axis.sage")]
        code, stdout, stderr = _run(command, REPO, env)
        commands.append({"cmd": " ".join(command), "cwd": ".", "exit": code})
    elif axis == "wolfram_xact":
        command = ["wolframscript", "-file", str(REPO / "wolfram/pr171_tilt_relaxation_axis.wls")]
        code, stdout, stderr = _run(command, REPO)
        commands.append({"cmd": " ".join(command), "cwd": ".", "exit": code})
    else:
        build = ["lake", "build"]
        code, stdout, stderr = _run(build, REPO / "formal_pr171")
        commands.append({"cmd": "lake build", "cwd": "formal_pr171", "exit": code})
        if code == 0:
            execute = ["lake", "exe", "pr171tiltrelaxation"]
            code2, out2, err2 = _run(execute, REPO / "formal_pr171")
            commands.append({"cmd": "lake exe pr171tiltrelaxation", "cwd": "formal_pr171", "exit": code2})
            stdout += out2
            stderr += err2
            code = code2
    return _last_json(stdout), commands, (stdout + stderr)[-12000:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--axis", required=True, choices=AXES)
    parser.add_argument("--run-dir", required=True, type=Path)
    args = parser.parse_args()
    axis = args.axis
    assignment_id = ASSIGNMENT_IDS[axis]
    assignment_path = REPO / args.run_dir / "assignments" / f"{assignment_id}.json"
    result_path = REPO / args.run_dir / "results" / f"{assignment_id}.json"
    assignment = load(assignment_path)
    contract = load(REPO / CONTRACT_PATH)
    errors = validate_contract(contract)
    if errors:
        raise SystemExit("contract invalid before axis: " + "; ".join(errors))
    if assignment.get("assignment_sha256") != assignment_self_hash(assignment):
        raise SystemExit("assignment self-hash mismatch")
    if assignment.get("cas_axis") != axis or assignment.get("allowed_sibling_results") != []:
        raise SystemExit("axis assignment or blinding mismatch")
    contract_sha = sha(REPO / CONTRACT_PATH)
    if assignment.get("cas_contract", {}).get("sha256") != contract_sha:
        raise SystemExit("assignment contract hash mismatch")
    for row in assignment.get("required_inputs", []):
        target = REPO / str(row.get("path"))
        if not target.is_file() or sha(target) != row.get("sha256"):
            raise SystemExit(f"required input mismatch: {row.get('path')}")
    authorization = load(REPO / AUTH_PATH)
    if authorization.get("axes_authorized") is not True or authorization.get("run_dir") != str(args.run_dir):
        raise SystemExit("pre-axis authorization inactive or run mismatch")
    if authorization.get("contract_sha256") != contract_sha:
        raise SystemExit("authorization contract mismatch")
    if authorization.get("runner_sha256") != sha(Path(__file__)):
        raise SystemExit("authorization runner mismatch")
    if authorization.get("assignments", {}).get(assignment_id) != sha(assignment_path):
        raise SystemExit("authorization assignment mismatch")
    authorization_sha = sha(REPO / AUTH_PATH)

    payload, commands, transcript = _execute(axis)
    exits = [row["exit"] for row in commands]
    failures: list[str] = []
    status = "PASS"
    if exits[-1] in {124, 127} or (axis == "wolfram_xact" and exits[-1] == 255 and payload is None):
        status = "BLOCKED_PLATFORM_OR_LICENSE"
        failures.append("required axis tool unavailable, timed out, or emitted the registered license-startup failure")
    elif payload is None:
        status = "FAIL"
        failures.append("axis emitted no parseable JSON payload")
    else:
        obligations = set(contract["target"]["exact_test_obligations"])
        checks = payload.get("checks")
        if any(code != 0 for code in exits):
            failures.append("one or more axis commands returned nonzero")
        if not isinstance(checks, dict) or set(checks) != obligations or not all(value is True for value in checks.values()):
            failures.append("exact obligation keyset or truth values differ from contract")
        if payload.get("computed") != contract["target"]["expected_exact_values"]:
            failures.append("canonical values differ from contract")
        if payload.get("fixture_matches") is not True or payload.get("all_pass") is not True:
            failures.append("axis fixture/all-pass receipt is false")
        if payload.get("precision_digits") != 80:
            failures.append("80-digit replay receipt missing")
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
        "precision_digits": (payload or {}).get("precision_digits"),
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
    outer_status = "pass" if status == "PASS" else "inconclusive" if status.startswith("BLOCKED") else "fail"
    outer = {
        "schema_version": 1,
        "run_id": assignment["run_id"],
        "assignment_id": assignment_id,
        "context_version": assignment["context_version"],
        "agent_type": assignment["agent_type"],
        "independence_mode": "blind-results",
        "status": outer_status,
        "findings": [{
            "finding_id": f"F-PR171-CAS-{axis.upper().replace('_', '-')}",
            "claim_id": assignment["claim_ids"][0],
            "verdict": status,
            "evidence_fingerprint": f"{contract_sha}:{authorization_sha}:{axis}",
        }],
        "assumptions": contract["semantics"]["assumptions"],
        "commands_run": commands,
        "tool_versions": nested["tool_versions"],
        "payload": {"cas_axis_result": nested},
        "result_path": str(args.run_dir / "results" / f"{assignment_id}.json"),
    }
    atomic_write(result_path, render(outer))
    print(json.dumps({"axis": axis, "status": status, "result_path": str(result_path.relative_to(REPO))}, sort_keys=True))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
