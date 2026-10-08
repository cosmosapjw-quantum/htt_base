#!/usr/bin/env python3
"""No-argument gate entrypoint for the independent SymPy C03 certificate."""

import json
import subprocess
import sys
from pathlib import Path


EXPECTED_STDOUT = '{"checks":{"CAS-13-C03":true},"domain_assumption_diff":[],"counterexample":null}\n'


def main():
    if len(sys.argv) != 1:
        print("run.py takes no arguments", file=sys.stderr)
        return 2

    axis = Path(__file__).resolve().parent
    package = axis.parent
    spec_dir = package.parents[3] / "cas"
    argv = [
        sys.executable, "-B", str(axis / "run_sympy.py"),
        "--contract", str(package / "EXECUTION_CONTRACT.json"),
        "--inputs", str(package / "ADMITTED_INPUTS.json"),
        "--teff", str(spec_dir / "TEFF_INTERVAL_SPEC.md"),
        "--common", str(spec_dir / "COMMON_SPEC.md"),
        "--evidence", str(axis / "evidence.json"),
    ]
    completed = subprocess.run(argv, cwd=package.parents[4], capture_output=True, text=True)
    if completed.returncode != 0:
        sys.stderr.write(completed.stderr)
        return completed.returncode
    if completed.stdout != EXPECTED_STDOUT or completed.stderr:
        sys.stderr.write("unexpected inner SymPy output\n")
        sys.stderr.write(completed.stderr)
        return 1
    parsed = json.loads(completed.stdout)
    if parsed != {"checks": {"CAS-13-C03": True}, "domain_assumption_diff": [], "counterexample": None}:
        sys.stderr.write("unexpected inner SymPy result\n")
        return 1
    sys.stdout.write(EXPECTED_STDOUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
