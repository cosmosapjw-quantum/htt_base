#!/usr/bin/env python3
"""Runner entry point for the frozen CAS-07 M02 Sage/Singular axis."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import traceback


AXIS = Path(__file__).resolve().parent
SAGE = Path("/home/cosmosapjw/opt/sage/sage")
SAGE_PYTHON = Path("/home/cosmosapjw/opt/sage/local/var/lib/sage/venv-python3.12/bin/python3")
SOURCE = AXIS / "sources/run.py"
CHECK_NAMES = (
    "CAS-07-M02-REMAINDER-IDENTITY",
    "CAS-07-M02-REMAINDER-BOUND",
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    argv = [str(SAGE), "-python", str(SOURCE)]
    completed = subprocess.run(argv, cwd=Path.cwd(), capture_output=True, text=True, timeout=1800)
    (AXIS / "run.stdout.json").write_text(completed.stdout)
    (AXIS / "run.stderr.log").write_text(completed.stderr)
    parsed = json.loads(completed.stdout)
    if not isinstance(parsed, dict):
        raise ValueError("Sage source emitted a non-object JSON document")
    checks = parsed.get("checks")
    if not isinstance(checks, dict) or set(checks) != set(CHECK_NAMES) or any(type(value) is not bool for value in checks.values()):
        raise ValueError("Sage source check schema mismatch")
    parsed.update({name: checks[name] for name in CHECK_NAMES})
    singular_stdout = (AXIS / "singular.stdout.log").read_text()
    singular_stderr = (AXIS / "singular.stderr.log").read_text()
    expected_lines = [
        "SINGULAR_SCHEMA_DERIVATIVE=0",
        "SINGULAR_SCHEMA_ENDPOINTS=0",
        "SINGULAR_WEIGHT_INTEGRAL=0",
        "SINGULAR_QUADRATIC_REMAINDER=0",
    ]
    raw_ok = singular_stdout.splitlines() == expected_lines and singular_stderr == ""
    if not raw_ok or completed.returncode != 0:
        for name in CHECK_NAMES:
            parsed["checks"][name] = False
            parsed[name] = False
        parsed["counterexample"] = "Execution or raw Singular diagnostic failure; inspect preserved logs."
    parsed["axis_status"] = "PASS_COMPONENT" if all(parsed["checks"].values()) else "FAIL_DIAGNOSTIC"
    parsed["execution"] = {
        "mode": "owner-authorized direct local",
        "global_registered_launch": None,
        "entry_argv": sys.orig_argv,
        "entry_executable": sys.executable,
        "entry_exit_code": 0 if all(parsed["checks"].values()) else 1,
        "runner_argv": argv,
        "runner_exit_code": completed.returncode,
        "runner_stdout": "run.stdout.json",
        "runner_stderr": "run.stderr.log",
        "sage_launcher": str(SAGE),
        "sage_launcher_sha256": digest(SAGE),
        "sage_python": str(SAGE_PYTHON),
        "sage_python_sha256": digest(SAGE_PYTHON),
        "singular_binary": "/home/cosmosapjw/opt/sage/local/bin/Singular",
        "raw_singular_diagnostics_inspected": True,
        "raw_singular_stdout_exact": singular_stdout,
        "raw_singular_stderr_exact": singular_stderr,
        "first_attempt": {
            "outcome": "FAIL_DIAGNOSTIC",
            "cause": "Singular polynomial syntax rejected exponent literals; exit code alone was 0",
            "preserved_logs": [
                "run.first_attempt.stdout.json",
                "run.first_attempt.stderr.log",
                "singular.first_attempt.stdout.log",
                "singular.first_attempt.stderr.log",
                "singular_version.first_attempt.stdout.log",
                "singular_version.first_attempt.stderr.log",
            ],
        },
    }
    parsed["proof_scope"] = {
        "identity": "For arbitrary Z under the declared derivative and continuity hypotheses, G(t)=(s-t)Z1(t)+Z(t) has G'(t)=(s-t)Z2(t). FTC on [0,s] gives integral G'=G(s)-G(0)=Z(s)-Z(0)-sZ1(0). The admitted definition H0=cZ1(0), c>0, gives sZ1(0)=H0*s/c.",
        "bound": "For 0<=s<=L and 0<=t<=s, s-t>=0 and |Z2(t)|<=M2. Hence |integral (s-t)Z2(t) dt|<=integral (s-t)|Z2(t)|dt<=M2*integral (s-t)dt=M2*s^2/2. Continuous Z2 makes the integrals valid. At s=0 both sides are zero; M2=0 forces Z2=0 on [0,L].",
        "limitations": "One analytic prerequisite and one CAS axis only; no full theorem, four-axis adjudication, or scientific admission.",
    }
    names = [
        "run.py", "sources/run.py", "sources/endpoint_weight.sing",
        "run.stdout.json", "run.stderr.log",
        "singular.stdout.log", "singular.stderr.log",
        "singular_version.stdout.log", "singular_version.stderr.log",
        "run.first_attempt.stdout.json", "run.first_attempt.stderr.log",
        "singular.first_attempt.stdout.log", "singular.first_attempt.stderr.log",
        "singular_version.first_attempt.stdout.log", "singular_version.first_attempt.stderr.log",
    ]
    parsed["artifact_sha256"] = {name: digest(AXIS / name) for name in names}
    (AXIS / "RESULT.json").write_text(json.dumps(parsed, indent=2, sort_keys=True) + "\n")
    return parsed


if __name__ == "__main__":
    try:
        output = run()
    except Exception as exc:
        output = {
            "checks": {name: False for name in CHECK_NAMES},
            "domain_assumption_diff": [],
            "counterexample": "Execution error, not a mathematical counterexample: " + repr(exc),
            "traceback": traceback.format_exc(),
            "axis_status": "FAIL_DIAGNOSTIC",
        }
        output.update({name: False for name in CHECK_NAMES})
        (AXIS / "RESULT.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, sort_keys=True))
    raise SystemExit(0 if all(output["checks"].values()) else 1)
