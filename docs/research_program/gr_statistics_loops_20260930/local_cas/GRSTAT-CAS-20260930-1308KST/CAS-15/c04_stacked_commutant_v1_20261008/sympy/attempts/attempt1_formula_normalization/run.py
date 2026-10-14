#!/usr/bin/env python3
"""Run and package the CAS-15-C04 SymPy axis without sibling evidence."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CONTRACT = ROOT / "EXECUTION_CONTRACT.json"
INPUTS = ROOT / "ADMITTED_INPUTS.json"
VERIFY = HERE / "verify.py"
RESULT = HERE / "result.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> int:
    expected_contract = "67422619e47fda896d7516d48e980ec693d878f3c63e5d61e0c151ffaef65ed8"
    expected_inputs = "1b98962616a8a43aca614c18a7e69304653c84f0d1b54846a81811642d2491d8"
    actual_contract = sha256(CONTRACT)
    actual_inputs = sha256(INPUTS)
    argv = ["/usr/bin/python3.12", "-B", str(VERIFY)]
    seal_ok = actual_contract == expected_contract and actual_inputs == expected_inputs

    if seal_ok:
        proc = subprocess.run(argv, cwd=Path.cwd(), capture_output=True, text=True)
        stdout = proc.stdout
        stderr = proc.stderr
        exit_code = proc.returncode
    else:
        stdout = ""
        stderr = "source/input seal mismatch"
        exit_code = 65

    (HERE / "sympy.stdout.log").write_text(stdout, encoding="utf-8")
    (HERE / "sympy.stderr.log").write_text(stderr, encoding="utf-8")

    try:
        engine_result = json.loads(stdout) if stdout.strip() else {}
    except json.JSONDecodeError as exc:
        engine_result = {"parse_error": str(exc)}

    passed = (
        seal_ok
        and exit_code == 0
        and engine_result.get("status") == "PASS"
        and engine_result.get("checks", {}).get("CAS-15-C04") is True
        and engine_result.get("domain_assumption_diff") == []
        and engine_result.get("counterexample") is None
    )
    packaged = dict(engine_result)
    packaged.update(
        {
            "status": "PASS" if passed else "FAIL",
            "checks": {"CAS-15-C04": passed},
            "contract_sha256": actual_contract,
            "admitted_inputs_sha256": actual_inputs,
            "source_sha256": sha256(VERIFY),
            "runner_sha256_at_execution": sha256(Path(__file__)),
            "execution": {
                "argv": argv,
                "cwd": str(Path.cwd()),
                "exit_code": exit_code,
                "stdout_log": str(HERE / "sympy.stdout.log"),
                "stderr_log": str(HERE / "sympy.stderr.log"),
            },
        }
    )
    if not passed and packaged.get("counterexample") is None:
        packaged["counterexample"] = {
            "kind": "execution_or_seal_failure",
            "seal_ok": seal_ok,
            "exit_code": exit_code,
            "stderr": stderr,
        }
    packaged.setdefault("domain_assumption_diff", [])
    atomic_json(RESULT, packaged)
    atomic_json(
        HERE / "certificate.engine.json",
        {
            "axis": "sympy",
            "status": packaged["status"],
            "contract_sha256": actual_contract,
            "admitted_inputs_sha256": actual_inputs,
            "source_sha256": packaged["source_sha256"],
            "runner_sha256_at_execution": packaged["runner_sha256_at_execution"],
            "result_sha256": sha256(RESULT),
            "argv": argv,
            "exit_code": exit_code,
            "sympy_version": engine_result.get("runtime", {}).get("sympy", "UNKNOWN"),
            "python_version": engine_result.get("runtime", {}).get("python", "UNKNOWN"),
            "launch_id": None,
            "authority_status": "UNAVAILABLE_BY_OWNER_DIRECT_LOCAL_INSTRUCTION",
            "observed_model": "UNKNOWN",
            "observed_effort": "UNKNOWN",
        },
    )

    gate = {
        "status": packaged["status"],
        "checks": {"CAS-15-C04": passed},
        "domain_assumption_diff": packaged.get("domain_assumption_diff", []),
        "counterexample": packaged.get("counterexample"),
        "result_path": str(RESULT),
    }
    print(json.dumps(gate, sort_keys=True, separators=(",", ":")))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
