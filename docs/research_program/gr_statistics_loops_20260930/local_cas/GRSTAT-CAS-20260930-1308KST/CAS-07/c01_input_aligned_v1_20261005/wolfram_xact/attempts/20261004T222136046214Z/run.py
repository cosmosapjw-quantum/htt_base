#!/usr/bin/python3.12
"""Execute the frozen CAS-07-C01 Wolfram axis and retain raw attempt evidence."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[8]
AXIS = Path(__file__).resolve().parent
CONTRACT = AXIS.parent / "EXECUTION_CONTRACT.json"
ADMITTED = AXIS.parent / "ADMITTED_INPUTS.json"
SPEC = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
SOURCE = AXIS / "proof.wl"
EXPECTED = {
    CONTRACT: "e5342381440cb6456ad27add75a9d23faa52a01b1a0f5998599e3026452a9f1a",
    ADMITTED: "30bbb6fce513eedfd98a693c2acbf3308363a7098a7938f4b5abf7e9282b2e39",
    SPEC: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main():
    AXIS.mkdir(parents=True, exist_ok=True)
    attempt = AXIS / "attempts" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    attempt.mkdir(parents=True)
    shutil.copyfile(SOURCE, attempt / "proof.wl")
    shutil.copyfile(Path(__file__), attempt / "run.py")
    before = {str(p.relative_to(ROOT)): sha(p) for p in EXPECTED}
    before["source"] = sha(SOURCE)
    before["runner"] = sha(Path(__file__))
    write_json(attempt / "inputs_before.json", before)
    argv = ["wolframscript", "-file", str(SOURCE)]
    start = time.monotonic()
    try:
        process = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=1740)
        exit_code = process.returncode
        stdout, stderr = process.stdout, process.stderr
        timeout = False
    except subprocess.TimeoutExpired as exc:
        exit_code = None
        stdout = (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = (exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        timeout = True
    duration = time.monotonic() - start
    (attempt / "stdout.raw.txt").write_text(stdout)
    (attempt / "stderr.raw.txt").write_text(stderr)
    after = {str(p.relative_to(ROOT)): sha(p) for p in EXPECTED}
    after["source"] = sha(SOURCE)
    after["runner"] = sha(Path(__file__))
    write_json(attempt / "inputs_after.json", after)
    payloads = stdout.split("CAS_JSON:")
    payload = None
    parse_error = None
    try:
        if len(payloads) != 2:
            raise ValueError(f"expected one CAS_JSON block, got {len(payloads) - 1}")
        payload = json.loads(payloads[1])
    except (ValueError, json.JSONDecodeError) as exc:
        parse_error = str(exc)
    messages = [line for line in (stdout + "\n" + stderr).splitlines() if "::" in line and ":" in line]
    checks = payload.get("checks", {}) if isinstance(payload, dict) else {}
    expected_checks = ["initial_value", "initial_derivative", "ode", "integral", "zero_limit",
                       "flat_initial", "flat_derivative", "flat_ode", "flat_integral",
                       "xtensor_nonzero_input", "xtensor_index_consistency"]
    valid = (exit_code == 0 and not timeout and not messages and not parse_error
             and before == after and all(before[str(p.relative_to(ROOT))] == digest for p, digest in EXPECTED.items())
             and payload.get("message_list") == "{}"
             and all(checks.get(k) is True for k in expected_checks))
    command = {"argv": argv, "cwd": str(ROOT), "exit_code": exit_code, "timeout": timeout,
               "wall_seconds": duration, "stdout_path": str(attempt / "stdout.raw.txt"),
               "stderr_path": str(attempt / "stderr.raw.txt")}
    write_json(attempt / "command.json", command)
    result = {
        "axis": "wolfram_xact",
        "status": "PASS" if valid else "INCONCLUSIVE",
        "contract_sha256": EXPECTED[CONTRACT],
        "evidence_class": "exact",
        "checks": {"CAS-07-C01": valid},
        "subchecks": checks,
        "domain_assumption_diff": [],
        "counterexample": None,
        "commands": [command],
        "completed_at": utc(),
        "source_path": str(SOURCE),
        "source_sha256": before["source"],
        "runner_sha256": before["runner"],
        "input_sha256_before": before,
        "input_sha256_after": after,
        "statement_alignment": "Exact explicit f on real Kc>0,s>=0; derived initial, ODE and interval identity; separate Kc=0 flat branch and fixed-s positive-side continuous limit. No C02/C03, Jacobi or physical inference.",
        "toolchain": {"wolfram": payload.get("version") if payload else None,
                      "xtensor": payload.get("xtensor_version") if payload else None},
        "raw_failures": {"parse_error": parse_error, "messages": messages, "timeout": timeout,
                         "stderr": stderr if stderr else None},
        "attempt_dir": str(attempt),
        "scientific_admission": "HOLD",
        "author_runtime": {"model": "UNKNOWN", "effort": "UNKNOWN", "usage": "UNKNOWN"},
    }
    write_json(AXIS / "result.json", result)
    shutil.copyfile(AXIS / "result.json", attempt / "result.json")
    print(json.dumps({"checks": {"CAS-07-C01": valid}, "domain_assumption_diff": [],
                      "counterexample": None, "status": result["status"]}, sort_keys=True))
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
