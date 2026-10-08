#!/usr/bin/env python3
"""Run the independent Wolfram+xTensor PORT-CAS-01 finite check."""

import hashlib
import json
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


AXIS = Path(__file__).resolve().parent
CONTRACT = AXIS.parent / "EXECUTION_CONTRACT.json"
INPUTS = AXIS.parent / "ADMITTED_INPUTS.json"
SOURCE = AXIS / "proof.wl"
RESULT = AXIS / "axis_result.json"
EXPECTED_CONTRACT = "1085005167c4bfeeb2ec6c7199f94c73d2b0651b381bcce00fdc05275f090169"
EXPECTED_INPUTS = "e6c66e6a944ee4f67c591d54281f5c3577d32852f66084767a5a6fec215d2992"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def emit_gate(passed, diff=None, counterexample=None):
    print(json.dumps({"checks": {"PORT-CAS-01": bool(passed)},
                      "domain_assumption_diff": diff or [],
                      "counterexample": counterexample}, separators=(",", ":")))


def main():
    if len(sys.argv) != 1:
        emit_gate(False, ["runner requires no arguments"])
        return 2

    contract_hash = sha256(CONTRACT)
    inputs_hash = sha256(INPUTS)
    input_seals_match = contract_hash == EXPECTED_CONTRACT and inputs_hash == EXPECTED_INPUTS
    executable = shutil.which("wolframscript")
    attempt = 1
    while (AXIS / f"attempt-{attempt:03d}.stdout.log").exists():
        attempt += 1
    stdout_path = AXIS / f"attempt-{attempt:03d}.stdout.log"
    stderr_path = AXIS / f"attempt-{attempt:03d}.stderr.log"
    argv = [executable, "-file", str(SOURCE)] if executable else []
    start = now()
    exit_code = None
    error = None
    stdout = ""
    stderr = ""
    if not input_seals_match:
        error = "frozen input SHA-256 mismatch"
    elif not executable:
        error = "wolframscript executable unavailable"
    else:
        try:
            proc = subprocess.run(argv, cwd=AXIS, capture_output=True, text=True, timeout=1800,
                                  check=False)
            stdout, stderr, exit_code = proc.stdout, proc.stderr, proc.returncode
        except subprocess.TimeoutExpired as exc:
            stdout = (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = (exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            error = "WolframScript exceeded the 1800-second contract wall limit"
        except OSError as exc:
            error = f"WolframScript launch failed: {exc}"
    completed = now()
    stdout_path.write_text(stdout)
    stderr_path.write_text(stderr)

    match = re.search(r"^PORT_CAS01_CHECKS_JSON=(\{[^\r\n]*\})$", stdout, re.MULTILINE)
    checks = None
    if match:
        try:
            checks = json.loads(match.group(1))
        except json.JSONDecodeError:
            error = error or "malformed Wolfram checks JSON"
    if checks is None and error is None:
        error = "Wolfram checks marker missing"
    passed = bool(input_seals_match and exit_code == 0 and checks and all(checks.values()))
    if not passed and error is None:
        error = "one or more exact obligations failed or WolframScript exited nonzero"

    version_match = re.search(r"^WOLFRAM_VERSION=(.*)$", stdout, re.MULTILINE)
    xact_path_match = re.search(r"^XACT_PACKAGE_PATH=(.*)$", stdout, re.MULTILINE)
    xact_symbols_match = re.search(r"^XACT_VERSION_SYMBOLS=(.*)$", stdout, re.MULTILINE)
    xact_version_match = re.search(r"^XACT_VERSION=(.*)$", stdout, re.MULTILINE)
    result = {
        "axis": "wolfram_xact",
        "status": "PASS" if passed else "BLOCKED",
        "check_axis": "PASS" if passed else "BLOCKED",
        "contract_sha256": contract_hash,
        "input_sha256": inputs_hash,
        "checks": {"PORT-CAS-01": passed},
        "subchecks": checks,
        "domain_assumption_diff": [],
        "counterexample": None,
        "evidence_class": "exact",
        "execution_evidence": "direct_local_runner_observed_exact_symbolic",
        "statement_alignment": {
            "scope": "PORT-CAS-01 finite exact algebra only",
            "signature": "(-,+,+,+)",
            "beta_domain": "real b1,b2,b3; s<1",
            "gamma_branch": "positive 1/sqrt(1-s), gamma+1>0",
            "converse_branch": "real zeta; zeta0>=1; zeta0^2-|zeta|^2=1",
            "units": "dimensionless U/c",
            "excluded_boundary": "s=1",
        },
        "commands": [{
            "argv": argv,
            "cwd": str(AXIS),
            "started_at": start,
            "completed_at": completed,
            "exit_code": exit_code,
            "timeout_seconds": 1800,
        }],
        "completed_at": completed,
        "hashes": {
            "source_sha256": sha256(SOURCE),
            "runner_sha256": sha256(Path(__file__)),
            "stdout_sha256": sha256(stdout_path),
            "stderr_sha256": sha256(stderr_path),
        },
        "evidence": {
            "source": str(SOURCE),
            "runner": str(Path(__file__).resolve()),
            "stdout": str(stdout_path),
            "stderr": str(stderr_path),
            "error": error,
        },
        "tool_versions": {
            "wolfram": version_match.group(1) if version_match else None,
            "xact_package_path": xact_path_match.group(1) if xact_path_match else None,
            "xact_version": xact_version_match.group(1) if xact_version_match else None,
            "xact_version_symbols": xact_symbols_match.group(1) if xact_symbols_match else None,
            "python": platform.python_version(),
        },
        "launch_id": None,
        "global_harness_used": False,
        "observed_model": "UNKNOWN",
        "observed_effort": "UNKNOWN",
        "lifecycle_status": "BLOCKED_NO_GLOBAL_REGISTERED_LAUNCH",
        "scientific_admission": "HOLD",
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    emit_gate(passed)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
