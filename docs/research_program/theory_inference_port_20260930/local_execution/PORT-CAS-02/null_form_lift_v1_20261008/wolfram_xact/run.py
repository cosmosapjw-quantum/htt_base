#!/usr/bin/env python3
"""No-argument, raw-evidence-preserving PORT-CAS-02 Wolfram axis runner."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[6]
CONTRACT = HERE.parent / "EXECUTION_CONTRACT.json"
INPUTS = HERE.parent / "ADMITTED_INPUTS.json"
SCRIPT = HERE / "null_form_lift.wl"
RESULT = HERE / "axis_result.json"
CONTRACT_SHA = "d62613255f18b2d2d2140cc6d73fbac27f6b2f8ac40ed9b268b9f5fc0fa166af"
INPUT_SHA = "849f9ebde2894f1deb15ba61452a3cc911d46af960b8630694cfe8cc15e3620a"
SCRIPT_SHA = "89d016cbb6b871e60c572d606c5b6d5ea598f8e8d67b76f7107fe26a3f44a9c8"
EXPECTED_CHECKS = {
    "metric_inverse", "null_on_unit_sphere", "S_null_polynomial",
    "B_null_equals_S", "mixed_eigenpair_kernel_identity",
    "metric_nondegenerate", "S_symmetric", "B_symmetric",
    "q_tracefree_branch", "spatial_monopole_removed",
    "quadratic_laplacian_is_twice_trace", "gauge_B_invariant",
    "gauge_null_invariant", "xAct_raised_kernel_identity",
    "xAct_metric_gauge_identity", "test_vector_null",
    "test_vector_polynomial", "pure_metric_B_zero",
}


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def write_json_exclusive(path: Path, obj: dict) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(obj, stream, indent=2)
        stream.write("\n")


def payload(passed: bool) -> dict:
    return {
        "checks": {"PORT-CAS-02": True if passed else None},
        "domain_assumption_diff": [],
        "counterexample": None,
    }


def main() -> int:
    if len(sys.argv) != 1:
        print(json.dumps(payload(False), separators=(",", ":")))
        return 2

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "_" + uuid.uuid4().hex[:8]
    prefix = HERE / f"run_{run_id}"
    stdout_path = prefix.with_suffix(".stdout.log")
    stderr_path = prefix.with_suffix(".stderr.log")
    receipt_path = prefix.with_suffix(".execution.json")
    argv = ["/usr/bin/wolframscript", "-file", rel(SCRIPT)]
    started_at = stamp()
    timeout = False
    launch_error = None
    exit_code = None
    identities_match = (
        sha256(CONTRACT) == CONTRACT_SHA
        and sha256(INPUTS) == INPUT_SHA
        and sha256(SCRIPT) == SCRIPT_SHA
    )
    if identities_match:
        with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
            try:
                completed = subprocess.run(
                    argv, cwd=REPO, stdout=stdout, stderr=stderr,
                    timeout=1800, check=False,
                )
                exit_code = completed.returncode
            except subprocess.TimeoutExpired:
                timeout = True
            except OSError as exc:
                launch_error = str(exc)
    else:
        stdout_path.open("xb").close()
        stderr_path.open("xb").close()
        launch_error = "contract, admitted input, or Wolfram source identity mismatch"

    completed_at = stamp()
    stdout = stdout_path.read_text(encoding="utf-8", errors="replace")
    stderr = stderr_path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"CHECKS=InputForm\[<\|(.*?)\|>\]", stdout, flags=re.S)
    parsed_checks = {}
    if match:
        for part in match.group(1).split(","):
            pair = re.fullmatch(r"\s*([A-Za-z][A-Za-z0-9_]*)\s*->\s*(True|False)\s*", part)
            if pair:
                parsed_checks[pair.group(1)] = pair.group(2) == "True"
    passed = (
        identities_match and exit_code == 0 and not timeout and launch_error is None
        and not stderr and "::" not in stdout
        and stdout.count("PORT_CAS_02_WOLFRAM_XACT=PASS") == 1
        and parsed_checks.keys() == EXPECTED_CHECKS
        and all(parsed_checks.values())
        and "XACT_XTENSOR_LOADED=True" in stdout
        and "XACT_RAISED_KERNEL=InputForm[0]" in stdout
        and "XACT_GAUGE=InputForm[0]" in stdout
    )
    receipt = {
        "runner_argv": [sys.executable, str(Path(__file__).resolve())],
        "argv": argv, "cwd": str(REPO), "started_at": started_at,
        "completed_at": completed_at, "exit_code": exit_code,
        "timed_out": timeout, "launch_error": launch_error,
        "contract_sha256": sha256(CONTRACT), "input_sha256": sha256(INPUTS),
        "script_sha256": sha256(SCRIPT), "runner_sha256": sha256(Path(__file__)),
        "stdout": rel(stdout_path), "stdout_sha256": sha256(stdout_path),
        "stderr": rel(stderr_path), "stderr_sha256": sha256(stderr_path),
        "parsed_checks": parsed_checks, "semantic_outcome": "PASS" if passed else "INCONCLUSIVE",
    }
    write_json_exclusive(receipt_path, receipt)

    result = json.loads(RESULT.read_text(encoding="utf-8"))
    result["status"] = "PASS" if passed else "INCONCLUSIVE"
    result["completed_at"] = completed_at
    result["commands"].append({
        "argv": argv, "cwd": str(REPO), "exit_code": exit_code,
        "started_at": started_at, "completed_at": completed_at,
        "timed_out": timeout, "semantic_outcome": receipt["semantic_outcome"],
        "execution_receipt": rel(receipt_path),
        "stdout": rel(stdout_path), "stderr": rel(stderr_path),
    })
    result["raw_evidence"] = {
        "stdout": rel(stdout_path), "stdout_sha256": receipt["stdout_sha256"],
        "stderr": rel(stderr_path), "stderr_sha256": receipt["stderr_sha256"],
    }
    result["runner_artifact"] = {"path": rel(Path(__file__)), "sha256": receipt["runner_sha256"]}
    temporary = HERE / f"axis_result.{run_id}.tmp"
    write_json_exclusive(temporary, result)
    temporary.replace(RESULT)
    print(json.dumps(payload(passed), separators=(",", ":")))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
