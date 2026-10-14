#!/usr/bin/env python3
"""Observed Wolfram/xTensor execution for the frozen CAS-10-C01 component."""

import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CONTRACT = ROOT.parent / "EXECUTION_CONTRACT.json"
INPUTS = ROOT.parent / "ADMITTED_INPUTS.json"
SPEC = ROOT.parents[4] / "cas" / "COMMON_SPEC.md"
EXPECTED_CONTRACT = "a1dccb0f256c76c9431b0fb1d46b75b917da1d20e15c90076a53fc693ddae379"
EXPECTED_INPUTS = "704403a7e717c1ff60e8be86d73e359621f0478b7b2a231b9df07ab3d99a2f3b"
EXPECTED_SPEC = "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def main():
    source = ROOT / "check.wls"
    executable = shutil.which("wolframscript")
    if executable is None:
        raise SystemExit("wolframscript executable unavailable")
    executable_path = Path(executable).resolve()
    observed = {"contract": sha256(CONTRACT), "inputs": sha256(INPUTS), "common_spec": sha256(SPEC)}
    expected = {"contract": EXPECTED_CONTRACT, "inputs": EXPECTED_INPUTS, "common_spec": EXPECTED_SPEC}
    if observed != expected:
        raise SystemExit(f"frozen input hash mismatch: {observed}")

    argv = [str(executable_path), "-file", str(source)]
    started_at = datetime.now(timezone.utc).isoformat()
    try:
        run = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=1800, check=False)
        stdout, stderr, exit_code = run.stdout, run.stderr, run.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = (exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        exit_code = 124
    completed_at = datetime.now(timezone.utc).isoformat()
    (ROOT / "wolfram.stdout.log").write_text(stdout)
    (ROOT / "wolfram.stderr.log").write_text(stderr)

    marker_lines = [line.removeprefix("CAS10_JSON=") for line in stdout.splitlines() if line.startswith("CAS10_JSON=")]
    parsed = json.loads(marker_lines[-1]) if marker_lines else {}
    detail_checks = parsed.get("checks", {})
    passed = exit_code == 0 and len(detail_checks) == 9 and all(detail_checks.values())
    command = {"argv": argv, "cwd": str(ROOT), "exit_code": exit_code,
               "started_at": started_at, "completed_at": completed_at,
               "stdout_path": str(ROOT / "wolfram.stdout.log"),
               "stderr_path": str(ROOT / "wolfram.stderr.log"),
               "stdout_sha256": sha256(ROOT / "wolfram.stdout.log"),
               "stderr_sha256": sha256(ROOT / "wolfram.stderr.log")}
    payload = {"checks": {"CAS-10-C01": passed}, "domain_assumption_diff": [],
               "counterexample": None if passed else {"exit_code": exit_code, "checks": detail_checks},
               "details": parsed, "input_sha256": observed,
               "source_sha256": sha256(source), "command": command,
               "successor_reason": "C02 aggregate-rule label and Lean oracle manifest repair; mathematical statement unchanged",
               "executable": {"path": str(executable_path), "sha256": sha256(executable_path)}}
    write_json(ROOT / "result.json", payload)
    axis = {"axis": "wolfram_xact", "status": "PASS" if passed else "FAIL",
            "contract_sha256": observed["contract"], "checks": payload["checks"],
            "domain_assumption_diff": [], "counterexample": payload["counterexample"],
            "evidence_class": "exact", "completed_at": completed_at,
            "commands": [command], "result_path": str(ROOT / "result.json"),
            "source_path": str(source), "source_sha256": payload["source_sha256"],
            "successor_reason": payload["successor_reason"],
            "executable": payload["executable"],
            "runtime": {"launch_id": None, "authority": "UNAVAILABLE",
                        "model": "UNKNOWN", "effort": "UNKNOWN"},
            "tool_versions": {"wolfram": parsed.get("wolfram_version"),
                              "xtensor": parsed.get("xtensor_version")}}
    write_json(ROOT / "axis_result.json", axis)
    print(json.dumps({"checks": payload["checks"],
                      "domain_assumption_diff": [], "counterexample": payload["counterexample"]},
                     sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
