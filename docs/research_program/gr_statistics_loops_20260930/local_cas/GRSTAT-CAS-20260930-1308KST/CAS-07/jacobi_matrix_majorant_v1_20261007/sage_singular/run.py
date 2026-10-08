#!/usr/bin/python3.12
"""Execute the frozen CAS-07 M04 Sage+Singular axis, writing only this directory."""

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[8]
AXIS = Path(__file__).resolve().parent
BASE = AXIS.parent
SAGE = Path("/usr/local/bin/sage")
SINGULAR = Path("/home/cosmosapjw/opt/sage/local/bin/Singular")
CONTRACT = BASE / "EXECUTION_CONTRACT.json"
INPUTS = BASE / "ADMITTED_INPUTS.json"
COMMON = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
EXPECTED = {
    CONTRACT: "553502c17d46c3b47c5a7b892f149f603235239d8504392b9bd19923f4edde7a",
    INPUTS: "f4d3b3b96a86fabcf83c7134193ec70da61b15d7a45b1a4b2c6b581312c1d4d8",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    SINGULAR: "9430832b7c972b6b26d29ded4d91a3e1df8fd87d67f4b8d3f14d8201a75f923c",
}
OBLIGATIONS = (
    "CAS-07-M04-VOLTERRA-IDENTITY",
    "CAS-07-M04-SCALAR-PREMISE",
    "CAS-07-M04-D-NORM",
    "CAS-07-M04-D-MINUS-SI",
)


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def call(name, argv, timeout=1800):
    try:
        proc = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True,
                              timeout=timeout, check=False)
        stdout, stderr, code = proc.stdout, proc.stderr, proc.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = (exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        code, timed_out = None, True
    (AXIS / f"{name}.stdout.raw.txt").write_text(stdout)
    (AXIS / f"{name}.stderr.raw.txt").write_text(stderr)
    diagnostic = bool(re.search(r"\b(error|exception|traceback|failed|not found)\b", stdout + "\n" + stderr, re.I))
    return {
        "argv": [str(x) for x in argv], "cwd": str(ROOT),
        "exit_code": code, "timed_out": timed_out,
        "diagnostic_error_scan": diagnostic,
        "stdout_artifact": f"{name}.stdout.raw.txt",
        "stderr_artifact": f"{name}.stderr.raw.txt",
        "stdout_sha256": sha256(AXIS / f"{name}.stdout.raw.txt"),
        "stderr_sha256": sha256(AXIS / f"{name}.stderr.raw.txt"),
        "stdout": stdout,
    }


def main():
    mismatches = [{"path": str(path), "expected": expected,
                   "actual": sha256(path) if path.exists() else None}
                  for path, expected in EXPECTED.items()
                  if not path.exists() or sha256(path) != expected]
    calls = {}
    success = False
    if not mismatches:
        calls["sage_version"] = call("sage_version", [SAGE, "--version"], 60)
        calls["singular_version"] = call("singular_version", [SINGULAR, "--version"], 60)
        versions_ok = (calls["sage_version"]["exit_code"] == 0
                       and "SageMath version 10.9" in calls["sage_version"]["stdout"]
                       and calls["singular_version"]["exit_code"] == 0
                       and "version 4.4.1 (44100" in calls["singular_version"]["stdout"])
        if versions_ok:
            calls["sage"] = call("sage", [SAGE, "-python", AXIS / "sage_check.py"])
            calls["singular"] = call("singular", [SINGULAR, "-q", AXIS / "singular_check.sing"])
            success = (
                calls["sage"]["exit_code"] == 0
                and not calls["sage"]["diagnostic_error_scan"]
                and "SAGE_EXACT_COMPONENT_AND_SCALAR_CHECKS_PASS" in calls["sage"]["stdout"]
                and calls["singular"]["exit_code"] == 0
                and not calls["singular"]["diagnostic_error_scan"]
                and "SINGULAR_JACOBI_COMPOSITION_PASS" in calls["singular"]["stdout"]
                and "SINGULAR_NONCOMMUTING_GENERIC_PASS" in calls["singular"]["stdout"]
                and "SINGULAR_WEIGHTED_KERNEL_PASS" in calls["singular"]["stdout"]
            )
    for record in calls.values():
        record.pop("stdout", None)
    artifacts = {name: {"path": str(AXIS / name), "sha256": sha256(AXIS / name)}
                 for name in ("run.py", "sage_check.py", "singular_check.sing", "proof.md")}
    result = {
        "schema": "htt.cas07.m04.sage-singular-result.v1",
        "contract_sha256": EXPECTED[CONTRACT],
        "inputs_sha256": EXPECTED[INPUTS],
        "common_spec_sha256": EXPECTED[COMMON],
        "axis": "sage_singular",
        "status": "PASS" if success else "BLOCKED",
        "checks": {key: bool(success) for key in OBLIGATIONS},
        "domain_assumption_diff": [],
        "counterexample": None,
        "input_or_tool_hash_mismatches": mismatches,
        "launch_id": None,
        "authority_status": "UNAVAILABLE",
        "observed_model": "UNKNOWN",
        "observed_effort": "UNKNOWN",
        "scientific_admission": "HOLD",
        "tool_versions": {
            "sage": "10.9" if not mismatches else "UNOBSERVED",
            "singular": "4.4.1/44100" if not mismatches else "UNOBSERVED",
        },
        "executables": {
            "sage": {"path": str(SAGE), "sha256": sha256(SAGE) if SAGE.exists() else None},
            "singular": {"path": str(SINGULAR), "sha256": sha256(SINGULAR) if SINGULAR.exists() else None},
        },
        "artifacts": artifacts,
        "calls": calls,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "2D Jacobi Volterra identity and induced operator-norm majorant only",
    }
    (AXIS / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "checks": result["checks"],
                      "domain_assumption_diff": result["domain_assumption_diff"],
                      "counterexample": result["counterexample"],
                      "result_path": str(AXIS / "result.json")}, sort_keys=True))
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
