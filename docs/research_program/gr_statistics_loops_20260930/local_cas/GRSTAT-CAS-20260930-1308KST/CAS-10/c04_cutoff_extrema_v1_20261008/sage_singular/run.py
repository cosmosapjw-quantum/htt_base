#!/usr/bin/env python3
"""Run the independent, exact Sage/Singular CAS-10-C04 axis."""
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[7]
CONTRACT = HERE.parent / "EXECUTION_CONTRACT.json"
INPUT = HERE.parent / "ADMITTED_INPUTS.json"
COMMON = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
SINGULAR = Path("/home/cosmosapjw/opt/sage/local/bin/Singular")
SAGE = Path("/usr/local/bin/sage")
EXPECTED = {
    CONTRACT: "8f2f5e387e8130f605073c650c9c0174253dd70e34ae4d4fbb23c697b53ead3a",
    INPUT: "1df59b533e32a7f21d3a7a1ee90c39cf6451b42bcd10d4ec580bdb031a47e992",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    SINGULAR: "9430832b7c972b6b26d29ded4d91a3e1df8fd87d67f4b8d3f14d8201a75f923c",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute(label, argv):
    p = subprocess.run(argv, cwd=HERE, capture_output=True, text=True, check=False)
    stdout = HERE / (label + ".stdout.log")
    stderr = HERE / (label + ".stderr.log")
    stdout.write_text(p.stdout)
    stderr.write_text(p.stderr)
    return {
        "argv": [str(x) for x in argv],
        "cwd": str(HERE),
        "exit_code": p.returncode,
        "stdout_path": str(stdout.relative_to(ROOT)),
        "stdout_sha256": sha(stdout),
        "stderr_path": str(stderr.relative_to(ROOT)),
        "stderr_sha256": sha(stderr),
    }, p.stdout


def main():
    for path, digest in EXPECTED.items():
        if sha(path) != digest:
            raise RuntimeError(f"frozen input or tool mismatch: {path}")
    source_hashes = {p.name: sha(p) for p in (HERE / "proof_sage.py", HERE / "proof.sing", HERE / "run.py")}
    sage_version_cmd, sage_version = execute("sage_version", [str(SAGE), "--version"])
    singular_version_cmd, singular_version = execute("singular_version", [str(SINGULAR), "--version"])
    if sage_version_cmd["exit_code"] != 0 or "SageMath version 10.9" not in sage_version:
        raise RuntimeError("Sage version check failed")
    if singular_version_cmd["exit_code"] != 0 or "version 4.4.1 (44100" not in singular_version:
        raise RuntimeError("Singular version check failed")
    sage_cmd, sage_output = execute("sage", [str(SAGE), "-python", "proof_sage.py"])
    singular_cmd, singular_output = execute("singular", [str(SINGULAR), "-q", "proof.sing"])
    if sage_cmd["exit_code"] != 0 or singular_cmd["exit_code"] != 0:
        raise RuntimeError("CAS execution failed; inspect engine logs")
    if any((HERE / (label + ".stderr.log")).read_text() for label in
           ("sage_version", "singular_version", "sage", "singular")):
        raise RuntimeError("nonempty CAS stderr; inspect engine logs")
    sage_proof = json.loads(sage_output)
    markers = [
        "D1_FACTOR_REMAINDER", "D2_FACTOR_REMAINDER",
        "D3_FACTOR_REMAINDER", "CRITICAL_VALUE_QUOTIENT_REMAINDER",
    ]
    lines = singular_output.strip().splitlines()
    for marker in markers:
        if lines.count(marker) != 1 or lines[lines.index(marker) + 1] != "0":
            raise RuntimeError(f"Singular failed exact identity: {marker}")
    if not lines or lines[-1] != "SINGULAR_PROOF_END":
        raise RuntimeError("Singular output incomplete")
    if sage_proof["all_exact_checks"] is not True:
        raise RuntimeError("Sage exact checks failed")
    if sage_proof["margin"] != "1147/1152" or sage_proof["sage_version"] != "10.9":
        raise RuntimeError("Sage result/identity mismatch")
    if sage_proof["D1_equality_points"] != ["1/2"]:
        raise RuntimeError("first derivative equality locus mismatch")
    if sage_proof["D2_equality_points"] != ["(3-sqrt(3))/6", "(3+sqrt(3))/6"]:
        raise RuntimeError("second derivative equality locus mismatch")

    payload = {"checks": {"CAS-10-C04": True}, "domain_assumption_diff": [], "counterexample": None}
    result = {
        **payload,
        "scope": "finite polynomial endpoint jets, global absolute derivative extrema and rational margin only",
        "domain": "real t in [0,1]; positive real sqrt(3)",
        "proof": sage_proof,
        "singular_exact_remainders": {m: "0" for m in markers},
        "auxiliary_bounds_used": ["exp(1/25)<25/24", "sqrt(3)>12/7"],
        "auxiliary_bounds_proved": False,
        "full_theorem_or_science_admission": "HOLD",
    }
    result_path = HERE / "result.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    axis_result = {
        "axis": "sage_singular",
        "status": "PASS",
        "contract_sha256": EXPECTED[CONTRACT],
        "evidence_class": "exact",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "checks": payload["checks"],
        "domain_assumption_diff": [],
        "counterexample": None,
        "commands": [sage_version_cmd, singular_version_cmd, sage_cmd, singular_cmd],
        "tool_versions": {"sage": "10.9", "singular": "4.4.1/44100"},
        "sage_executable_path": str(SAGE.resolve()),
        "sage_executable_sha256": sha(SAGE),
        "pinned_singular_path": str(SINGULAR),
        "pinned_singular_sha256": EXPECTED[SINGULAR],
        "diagnostic_inspection": "All CAS exit codes and stderr logs were inspected by the runner; four Singular exact remainders are zero.",
        "source_hashes": source_hashes,
        "result_path": str(result_path.relative_to(ROOT)),
        "result_sha256": sha(result_path),
        "global_launch_id": None,
        "global_launch_status": "UNAVAILABLE",
        "observed_author_model": "UNKNOWN",
        "observed_author_effort": "UNKNOWN",
        "independence_mode": "blind-results-and-derivations",
    }
    (HERE / "axis_result.json").write_text(json.dumps(axis_result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, separators=(",", ":")))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"axis runner failed: {exc}", file=sys.stderr)
        raise
