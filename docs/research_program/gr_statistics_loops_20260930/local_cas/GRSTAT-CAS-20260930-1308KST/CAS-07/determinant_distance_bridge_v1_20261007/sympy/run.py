"""Stdlib-only frozen SymPy-axis runner; invoke from the repository root."""

import hashlib
import json
import pathlib
import subprocess
import sys
import time


AXIS = pathlib.Path(__file__).resolve().parent
BRIDGE = AXIS.parent
REPO = pathlib.Path.cwd().resolve()
PYTHON = pathlib.Path("/usr/bin/python3.12")
COMMON = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
EXPECTED = {
    BRIDGE / "EXECUTION_CONTRACT.json": "24e3ae1e11d2a75335cd7fac436e8d1656100dc7877672d08464a4612a19348e",
    BRIDGE / "ADMITTED_INPUTS.json": "22fbf2a3fcc428d25f8e9fb0d6e1866c8057ebc7e76dd4ad248bd144300a5a75",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}
TAGS = [
    "CAS-07-M05-REWRITE",
    "CAS-07-M05-C02-PREMISE",
    "CAS-07-M05-DETERMINANT-SIGN",
    "CAS-07-M05-DISTANCE-BOUND",
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    started = time.monotonic()
    hashes = {str(p.relative_to(REPO)): sha(p) for p in EXPECTED}
    for p, expected in EXPECTED.items():
        if hashes[str(p.relative_to(REPO))] != expected:
            raise RuntimeError("frozen input hash mismatch: " + str(p))

    source = AXIS / "m05_bridge.py"
    command = [str(PYTHON), "-B", str(source)]
    completed = subprocess.run(command, cwd=REPO, capture_output=True, text=True, timeout=1800)
    (AXIS / "sympy.stdout.log").write_text(completed.stdout, encoding="utf-8")
    (AXIS / "sympy.stderr.log").write_text(completed.stderr, encoding="utf-8")
    parsed = json.loads(completed.stdout) if completed.stdout.strip() else {}
    checks = parsed.get("checks", {})
    valid = (
        completed.returncode == 0
        and parsed.get("sympy_version") == "1.14.0"
        and set(checks) == set(TAGS)
        and all(checks.get(tag) is True for tag in TAGS)
        and parsed.get("domain_assumption_diff") == []
        and parsed.get("counterexample") is None
    )
    sympy_path = pathlib.Path("/home/cosmosapjw/.local/lib/python3.12/site-packages/sympy/__init__.py")
    artifacts = {}
    for p in [PYTHON, sympy_path, pathlib.Path(__file__).resolve(), source,
              AXIS / "PROOF.md", AXIS / "sympy.stdout.log", AXIS / "sympy.stderr.log"]:
        artifacts[str(p)] = {"sha256": sha(p), "bytes": p.stat().st_size}

    result = {
        "schema_version": 2,
        "run_id": "GRSTAT-CAS-20260930-1308KST",
        "axis": "sympy",
        "contract_id": "GRSTAT-20260930-CAS-07-M05-DETERMINANT-DISTANCE-BRIDGE-V1",
        "contract_sha256": EXPECTED[BRIDGE / "EXECUTION_CONTRACT.json"],
        "admitted_inputs_sha256": EXPECTED[BRIDGE / "ADMITTED_INPUTS.json"],
        "source_input_hashes": hashes,
        "status": "PASS" if valid else "BLOCKED",
        "checks": {tag: checks.get(tag) is True for tag in TAGS},
        "domain_assumption_diff": parsed.get("domain_assumption_diff"),
        "counterexample": parsed.get("counterexample"),
        "accepted_theorems_used": parsed.get("accepted_theorems_used"),
        "exact_controls": parsed.get("exact_controls"),
        "tool_versions": {"python": sys.version.split()[0], "sympy": parsed.get("sympy_version")},
        "executable_artifacts": artifacts,
        "execution": {"argv": command, "cwd": str(REPO), "exit_code": completed.returncode,
                      "elapsed_seconds": round(time.monotonic() - started, 6)},
        "launch_id": None,
        "authority_status": "UNAVAILABLE",
        "observed_model": "UNKNOWN",
        "observed_effort": "UNKNOWN",
        "scope": "M01+M04+C02 determinant and distance bridge only",
        "scientific_admission": "HOLD",
    }
    (AXIS / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "checks": result["checks"],
        "domain_assumption_diff": result["domain_assumption_diff"],
        "counterexample": result["counterexample"],
        "result_path": str(AXIS / "result.json"),
    }, sort_keys=True))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
