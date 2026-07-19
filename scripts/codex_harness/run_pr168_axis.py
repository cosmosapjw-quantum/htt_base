#!/usr/bin/env python3
"""Execute exactly one registered PR-168 CAS axis and seal its envelope."""
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

import run_pr168_mes_four_acceleration_honesty as pr168


REPO = pr168.REPO


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                return payload
    return None


def _run(
    cmd: list[str], cwd: Path, timeout: int = 1800,
    env: dict[str, str] | None = None,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], str]:
    completed = subprocess.run(
        cmd, cwd=cwd, text=True, capture_output=True, timeout=timeout, env=env
    )
    command = {
        "cmd": " ".join(cmd),
        "cwd": cwd.relative_to(REPO).as_posix() if cwd != REPO else ".",
        "exit": completed.returncode,
    }
    transcript = (completed.stdout + completed.stderr)[-12000:]
    return _last_json(completed.stdout), [command], transcript


def _execute(axis: str) -> tuple[dict[str, Any] | None, list[dict[str, Any]], str]:
    if axis == "sympy":
        interpreter = REPO / "venv/bin/python"
        python = str(interpreter if interpreter.is_file() else Path(sys.executable))
        return _run(
            [python, "-B", str(REPO / "htt/src/common/pr168_sympy_axis.py")],
            REPO,
        )
    if axis == "wolfram_xact":
        return _run(
            ["wolframscript", "-file", str(REPO / "wolfram/pr168_accel_kinematic_axis.wls")],
            REPO,
        )
    if axis == "sage_singular":
        sage_cache = tempfile.mkdtemp(prefix="htt_pr168_sage_")
        env = os.environ.copy()
        env["DOT_SAGE"] = sage_cache
        return _run(
            ["sage", str(REPO / "sage/pr168_accel_kinematic_axis.sage")],
            REPO,
            env=env,
        )
    build = subprocess.run(
        ["lake", "build"], cwd=REPO / "formal_pr168",
        text=True, capture_output=True, timeout=1800,
    )
    commands = [{
        "cmd": "lake build",
        "cwd": "formal_pr168",
        "exit": build.returncode,
    }]
    transcript = (build.stdout + build.stderr)[-12000:]
    if build.returncode != 0:
        return None, commands, transcript
    execute = subprocess.run(
        ["lake", "exe", "pr168accelkinematic"], cwd=REPO / "formal_pr168",
        text=True, capture_output=True, timeout=1800,
    )
    commands.append({
        "cmd": "lake exe pr168accelkinematic",
        "cwd": "formal_pr168",
        "exit": execute.returncode,
    })
    transcript = (transcript + execute.stdout + execute.stderr)[-12000:]
    return _last_json(execute.stdout), commands, transcript


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--axis", required=True, choices=pr168.AXES)
    parser.add_argument("--run-dir", required=True, type=Path)
    args = parser.parse_args()
    axis = args.axis
    assignment_id = pr168.ASSIGNMENT_IDS[axis]
    assignment_path = REPO / args.run_dir / "assignments" / f"{assignment_id}.json"
    result_path = REPO / args.run_dir / "results" / f"{assignment_id}.json"
    assignment = pr168._load_json(assignment_path)
    contract = pr168._load_json(REPO / pr168.CONTRACT_PATH)
    contract_errors = pr168._contract_errors(contract)
    if contract_errors:
        raise SystemExit("contract validation failed before axis run: " + "; ".join(contract_errors))
    if assignment.get("cas_axis") != axis:
        raise SystemExit("assignment CAS axis mismatch")
    if assignment.get("independence_mode") != "blind-results":
        raise SystemExit("assignment is not blind-results")
    if assignment.get("allowed_sibling_results") != []:
        raise SystemExit("blind assignment unexpectedly allows sibling results")

    payload, commands, transcript = _execute(axis)
    expected_checks = set(contract["target"]["exact_test_obligations"])
    expected_values = contract["target"]["expected_exact_values"]
    failures: list[str] = []
    if payload is None:
        failures.append("axis emitted no parseable JSON payload")
    else:
        if commands[-1]["exit"] != 0:
            failures.append("axis command returned nonzero")
        if payload.get("all_pass") is not True:
            failures.append("axis all_pass is not true")
        checks = payload.get("checks")
        if not isinstance(checks, dict) or set(checks) != expected_checks:
            failures.append("axis check keyset mismatch")
        elif not all(value is True for value in checks.values()):
            failures.append("one or more axis checks failed")
        if payload.get("computed") != expected_values:
            failures.append("axis exact values differ from the frozen contract")
        if payload.get("redistributed_fixture_matches") is not True:
            failures.append("redistribution fixture mismatch")

    contract_sha = pr168._sha(REPO / pr168.CONTRACT_PATH)
    nested = {
        "schema_version": 1,
        "axis": axis,
        "contract_id": contract["identity"]["contract_id"],
        "contract_sha256": contract_sha,
        "status": "PASS" if not failures else "FAIL",
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
        "redistributed_fixture_matches": (payload or {}).get(
            "redistributed_fixture_matches"
        ),
        "counterexample": None if not failures else {"failures": failures},
        "completed_at": _now(),
        "sibling_results_read": [],
        "transcript_tail": transcript,
    }
    outer = {
        "schema_version": 1,
        "run_id": assignment["run_id"],
        "assignment_id": assignment_id,
        "context_version": assignment["context_version"],
        "independence_mode": "blind-results",
        "status": "pass" if not failures else "fail",
        "claim_ids": assignment["claim_ids"],
        "evidence_refs": [
            pr168.CONTRACT_PATH.as_posix(),
            *[row["path"] for row in contract["axes"][axis]["sources"]],
        ],
        "assumptions": contract["semantics"]["assumptions"],
        "tool_versions": nested["tool_versions"],
        "commands_run": commands,
        "result_path": result_path.relative_to(REPO).as_posix(),
        "payload": {"cas_axis_result": nested},
    }
    pr168._write_json(result_path, outer)
    print(json.dumps({
        "ok": not failures,
        "axis": axis,
        "result_path": outer["result_path"],
        "result_sha256": pr168._sha(result_path),
        "failures": failures,
    }, indent=2))
    raise SystemExit(0 if not failures else 2)


if __name__ == "__main__":
    main()
