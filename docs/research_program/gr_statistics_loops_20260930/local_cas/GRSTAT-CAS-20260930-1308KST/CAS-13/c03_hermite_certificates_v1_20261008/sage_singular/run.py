#!/usr/bin/env python3
"""Stdlib entrypoint for the frozen CAS-13-C03 Sage/Singular axis.

The aggregate runner invokes this file with ordinary Python and no arguments.
It delegates mathematical work to the pinned Sage environment, then checks the
exact child output and Singular evidence before emitting the gate envelope.
"""

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


HERE = Path(__file__).resolve().parent
SAGE = Path("/usr/local/bin/sage")
SINGULAR = Path("/home/cosmosapjw/opt/sage/local/bin/Singular")
SOURCE = HERE / "verify_c03.py"
EXPECTED = {
    SAGE: "b190e6cec5027031be752260d9b21a8e23f11a313cc620e5dcd1be28390643c1",
    SINGULAR: "9430832b7c972b6b26d29ded4d91a3e1df8fd87d67f4b8d3f14d8201a75f923c",
    SOURCE: "44355387a64c620f25e2b6bf4ca47967a8612834b76119733ca0bd283690caea",
}
CHILD_STDOUT = '{"CAS-13-C03":true}\n'
GATE_STDOUT = '{"checks":{"CAS-13-C03":true},"domain_assumption_diff":[],"counterexample":null}'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    require(len(sys.argv) == 1, "run.py accepts no arguments")
    for path, digest in EXPECTED.items():
        require(path.is_file() and sha256(path) == digest,
                "pinned executable/source mismatch: " + str(path))

    completed = subprocess.run(
        [str(SAGE), "-python", SOURCE.name], cwd=HERE, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=1800, check=False,
    )
    (HERE / "wrapper_child.stdout.log").write_text(completed.stdout)
    (HERE / "wrapper_child.stderr.log").write_text(completed.stderr)
    require(completed.returncode == 0, "Sage axis exit " + str(completed.returncode))
    require(completed.stdout == CHILD_STDOUT, "Sage axis output mismatch")
    require(completed.stderr == "", "Sage axis stderr is nonempty")

    singular_out = (HERE / "singular.stdout.log").read_text()
    singular_err = (HERE / "singular.stderr.log").read_text()
    sage_raw = (HERE / "sage_raw.log").read_text()
    require(singular_err == "", "Singular stderr is nonempty")
    require(not re.search(r"(?i)(error|warning|undefined)", singular_out),
            "Singular emitted diagnostic text despite zero exit")
    require("Sage version: 10.9\n" in sage_raw, "Sage version mismatch")
    require("Singular division exit: 0\n" in sage_raw,
            "Singular division exit is not zero")
    require("Singular executable sha256: " + EXPECTED[SINGULAR] in sage_raw,
            "Singular executable evidence mismatch")
    require("Singular division stdout sha256: " + hashlib.sha256(singular_out.encode()).hexdigest() in sage_raw,
            "Singular stdout digest mismatch")
    require("Singular division stderr sha256: " + hashlib.sha256(singular_err.encode()).hexdigest() in sage_raw,
            "Singular stderr digest mismatch")
    for p in (5, 6):
        for marker in ("NF_ZERO", "DIVISION_ZERO", "TARGET_EQUAL"):
            require(re.search(rf"P{p}_{marker}\s*\n1\s*\n", singular_out) is not None,
                    f"Singular p={p} {marker} certificate missing")
        require(f"P{p}_QUOTIENT\n" in singular_out,
                f"Singular p={p} quotient missing")

    # JSON serialization fixes the exact external gate key order and booleans.
    require(json.loads(GATE_STDOUT) == {
        "checks": {"CAS-13-C03": True},
        "domain_assumption_diff": [],
        "counterexample": None,
    }, "internal gate envelope mismatch")
    sys.stdout.write(GATE_STDOUT + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"CAS-13-C03 wrapper failure: {exc}", file=sys.stderr)
        raise SystemExit(1)
