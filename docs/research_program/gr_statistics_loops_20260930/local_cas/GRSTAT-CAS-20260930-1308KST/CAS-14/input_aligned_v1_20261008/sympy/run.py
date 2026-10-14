#!/usr/bin/env python3
"""Execute and seal the frozen CAS-14 SymPy axis."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


AXIS_DIR = Path(__file__).resolve().parent
UNIT_DIR = AXIS_DIR.parent
MAIN = AXIS_DIR / "Main.py"
MATH_RESULT = AXIS_DIR / "math_result.json"
CONTRACT = UNIT_DIR / "EXECUTION_CONTRACT.json"
INPUTS = UNIT_DIR / "ADMITTED_INPUTS.json"
EXPECTED_CONTRACT = "afee8b0f823bb89f9a1507a5c8fbcff97c95f152296f88e55e15cdcdbce21639"
EXPECTED_INPUTS = "ed8d777bf74f3b35af925e807a90842af9530355a6f392dab5d5e0bbcf1a7591"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run_command(argv: list[str]) -> dict:
    completed = subprocess.run(argv, cwd=AXIS_DIR, text=True, capture_output=True)
    return {
        "argv": argv,
        "cwd": str(AXIS_DIR),
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def main() -> int:
    contract_sha = sha256(CONTRACT)
    inputs_sha = sha256(INPUTS)
    version_cmd = [
        "/usr/bin/python3",
        "-c",
        "import sys,sympy;print(sys.version);print(sympy.__version__);print(sympy.__file__)",
    ]
    proof_cmd = [
        "/usr/bin/python3",
        "-B",
        str(MAIN),
        "--output",
        str(MATH_RESULT),
    ]
    version = run_command(version_cmd)
    proof = run_command(proof_cmd)
    (AXIS_DIR / "run.stdout.log").write_text(proof["stdout"])
    (AXIS_DIR / "run.stderr.log").write_text(proof["stderr"])

    parse_error = None
    math_result = None
    try:
        math_result = json.loads(proof["stdout"])
    except (json.JSONDecodeError, TypeError) as exc:
        parse_error = str(exc)

    expected_keys = {"CAS-14-C01", "CAS-14-C02", "CAS-14-C03"}
    checks = math_result.get("checks", {}) if isinstance(math_result, dict) else {}
    seals_ok = contract_sha == EXPECTED_CONTRACT and inputs_sha == EXPECTED_INPUTS
    version_ok = version["exit_code"] == 0 and "1.14.0" in version["stdout"]
    structure_ok = (
        isinstance(math_result, dict)
        and set(checks) == expected_keys
        and all(type(value) is bool for value in checks.values())
        and math_result.get("domain_assumption_diff") == []
        and math_result.get("counterexample") is None
    )
    passed = (
        proof["exit_code"] == 0
        and seals_ok
        and version_ok
        and structure_ok
        and all(checks.values())
    )
    completed_at = utc_now()
    execution = {
        "schema": "htt.cas14.sympy-execution.v1",
        "axis": "sympy",
        "completed_at": completed_at,
        "commands": [version, proof],
        "input_seals": {
            "contract_sha256": contract_sha,
            "admitted_inputs_sha256": inputs_sha,
            "match": seals_ok,
        },
        "parse_error": parse_error,
        "launch_id": None,
        "authority_status": "UNAVAILABLE",
        "observed_model": "UNKNOWN",
        "observed_effort": "UNKNOWN",
    }
    (AXIS_DIR / "execution.json").write_text(
        json.dumps(execution, indent=2, sort_keys=True) + "\n"
    )

    result = {
        "schema": "htt.cas-axis-result.v1",
        "axis": "sympy",
        "status": "PASS" if passed else "FAIL",
        "contract_sha256": contract_sha,
        "admitted_inputs_sha256": inputs_sha,
        "evidence_class": "exact",
        "completed_at": completed_at,
        "commands": [
            {
                "argv": version["argv"],
                "cwd": version["cwd"],
                "exit_code": version["exit_code"],
            },
            {
                "argv": proof["argv"],
                "cwd": proof["cwd"],
                "exit_code": proof["exit_code"],
            },
        ],
        "checks": checks,
        "domain_assumption_diff": (
            math_result.get("domain_assumption_diff", [])
            if isinstance(math_result, dict)
            else ["SymPy output was not parseable"]
        ),
        "counterexample": (
            math_result.get("counterexample")
            if isinstance(math_result, dict)
            else None
        ),
        "statement_alignment": {
            "CAS-14-C01": "Exact Levi-Civita/cross-matrix and finite weighted-sum certificates under unit directions.",
            "CAS-14-C02": "Universal PSD quadratic form, kernel intersection, nonparallel positivity, inverse, and boundary controls.",
            "CAS-14-C03": "Universal pseudoinverse inequality chains with full-rank premises, perturbation amplitude bound, Frobenius identity, and 80-digit ancillary tests.",
        },
        "source_hashes": {
            "Main.py": sha256(MAIN),
            "run.py": sha256(Path(__file__).resolve()),
        },
        "artifact_hashes": {
            "math_result.json": sha256(MATH_RESULT) if MATH_RESULT.exists() else None,
            "run.stdout.log": sha256(AXIS_DIR / "run.stdout.log"),
            "run.stderr.log": sha256(AXIS_DIR / "run.stderr.log"),
        },
        "toolchain": {
            "python_argv": version["argv"],
            "version_stdout": version["stdout"],
            "version_stderr": version["stderr"],
            "expected_sympy": "1.14.0",
        },
        "runtime": {
            "launch_id": None,
            "authority_status": "UNAVAILABLE",
            "observed_model": "UNKNOWN",
            "observed_effort": "UNKNOWN",
            "routing": "direct local execution per live owner instruction",
        },
        "limitations": [
            "No calibrated derivative observation was constructed.",
            "No perturbed-operator claim was made without ||omega||<=Omega_*.",
            "No full theorem, observational, physics, or scientific admission follows.",
        ],
        "errors": [] if passed else {
            "parse_error": parse_error,
            "seals_ok": seals_ok,
            "version_ok": version_ok,
            "structure_ok": structure_ok,
            "proof_exit_code": proof["exit_code"],
        },
    }
    (AXIS_DIR / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )

    gate_payload = {
        "checks": {
            key: bool(checks.get(key, False)) and passed for key in sorted(expected_keys)
        },
        "domain_assumption_diff": result["domain_assumption_diff"],
        "counterexample": result["counterexample"],
    }
    print(json.dumps(gate_payload, separators=(",", ":"), sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
