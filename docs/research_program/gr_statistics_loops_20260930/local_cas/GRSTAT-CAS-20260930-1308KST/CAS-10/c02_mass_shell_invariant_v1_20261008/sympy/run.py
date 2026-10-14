#!/usr/bin/env python3
"""Execute and preserve the CAS-10-C02 SymPy axis evidence."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


AXIS_DIR = Path(__file__).resolve().parent
VERIFY = AXIS_DIR / "verify.py"
STDOUT_LOG = AXIS_DIR / "sympy.stdout.log"
STDERR_LOG = AXIS_DIR / "sympy.stderr.log"
RESULT = AXIS_DIR / "result.json"
EXECUTION = AXIS_DIR / "execution.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    argv = [sys.executable, str(VERIFY)]
    completed = subprocess.run(
        argv,
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=False,
    )
    STDOUT_LOG.write_text(completed.stdout, encoding="utf-8")
    STDERR_LOG.write_text(completed.stderr, encoding="utf-8")

    parse_error = None
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        parse_error = str(exc)
        result = {
            "schema": "htt.cas-axis-result.v1",
            "axis": "sympy",
            "component": "CAS-10-C02",
            "status": "FAIL",
            "checks": {"CAS-10-C02": False},
            "domain_assumption_diff": [],
            "counterexample": "Engine result was not valid JSON; inspect raw stderr/stdout.",
            "scientific_admission": "HOLD",
        }

    result["execution"] = {
        "argv": argv,
        "cwd": str(Path.cwd().resolve()),
        "exit_code": completed.returncode,
        "stdout_path": str(STDOUT_LOG.relative_to(Path.cwd())),
        "stderr_path": str(STDERR_LOG.relative_to(Path.cwd())),
        "stdout_sha256": sha256(STDOUT_LOG),
        "stderr_sha256": sha256(STDERR_LOG),
        "parse_error": parse_error,
    }
    result["source_hashes"] = {
        "verify.py": sha256(VERIFY),
        "run.py": sha256(Path(__file__).resolve()),
    }
    if completed.returncode != 0:
        result["status"] = "FAIL"
        result["checks"] = {"CAS-10-C02": False}
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    execution = {
        "schema": "htt.cas-axis-execution.v1",
        "axis": "sympy",
        "component": "CAS-10-C02",
        "argv": argv,
        "cwd": str(Path.cwd().resolve()),
        "exit_code": completed.returncode,
        "raw_stdout": {
            "path": str(STDOUT_LOG.relative_to(Path.cwd())),
            "sha256": sha256(STDOUT_LOG),
        },
        "raw_stderr": {
            "path": str(STDERR_LOG.relative_to(Path.cwd())),
            "sha256": sha256(STDERR_LOG),
        },
        "source_hashes": result["source_hashes"],
        "result_path": str(RESULT.relative_to(Path.cwd())),
        "result_sha256": sha256(RESULT),
    }
    EXECUTION.write_text(
        json.dumps(execution, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    envelope = {
        "status": result["status"],
        "checks": result["checks"],
        "domain_assumption_diff": result["domain_assumption_diff"],
        "counterexample": result["counterexample"],
        "result_path": str(RESULT.relative_to(Path.cwd())),
    }
    print(json.dumps(envelope, separators=(",", ":"), sort_keys=True))
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
