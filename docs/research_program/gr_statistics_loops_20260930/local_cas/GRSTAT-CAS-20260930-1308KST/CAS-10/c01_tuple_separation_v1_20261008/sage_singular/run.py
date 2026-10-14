"""Run both pinned engines for the frozen CAS-10-C01 Sage/Singular axis."""

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
UNIT = ROOT / "docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-10/c01_tuple_separation_v1_20261008"
HERE = Path(__file__).resolve().parent
SINGULAR = Path("/home/cosmosapjw/opt/sage/local/bin/Singular")
CONTRACT = UNIT / "EXECUTION_CONTRACT.json"
INPUTS = UNIT / "ADMITTED_INPUTS.json"
COMMON = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
EXPECTED = {
    CONTRACT: "e438beb0e304e7a84e062cb5ab5946829951e035b3f6ac2923c28e07fd25f08d",
    INPUTS: "704403a7e717c1ff60e8be86d73e359621f0478b7b2a231b9df07ab3d99a2f3b",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    SINGULAR: "9430832b7c972b6b26d29ded4d91a3e1df8fd87d67f4b8d3f14d8201a75f923c",
}
SINGULAR_MARKERS = [
    "u_timelike_unit", "B1u_zero", "B2u_exact", "uT_b2_zero",
    "b2_lorentz_norm_exact", "tuple1_separate_powers",
    "tuple2_separate_powers", "H0_boundary", "H0_powers", "H1_control", "H1_powers",
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def run_command(name, argv):
    completed = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=600)
    stdout_path = HERE / (name + ".stdout.log")
    stderr_path = HERE / (name + ".stderr.log")
    stdout_path.write_bytes(completed.stdout)
    stderr_path.write_bytes(completed.stderr)
    return {
        "argv": argv,
        "cwd": str(ROOT),
        "exit_code": completed.returncode,
        "stdout_path": str(stdout_path),
        "stdout_sha256": digest(stdout_path),
        "stderr_path": str(stderr_path),
        "stderr_sha256": digest(stderr_path),
    }


def main():
    seals = {str(path): {"expected_sha256": expected, "actual_sha256": digest(path)}
             for path, expected in EXPECTED.items()}
    seal_ok = all(item["actual_sha256"] == item["expected_sha256"] for item in seals.values())
    commands = []
    if seal_ok:
        commands.append(run_command("sage_version", ["sage", "--version"]))
        commands.append(run_command("singular_version", [str(SINGULAR), "-v"]))
        commands.append(run_command("sage", ["sage", "-python", str(HERE / "sage_axis.py")]))
        commands.append(run_command("singular", [str(SINGULAR), "-q", str(HERE / "singular_axis.sing")]))

    sage_text = (HERE / "sage.stdout.log").read_text() if seal_ok else ""
    sage_err = (HERE / "sage.stderr.log").read_text() if seal_ok else ""
    singular_text = (HERE / "singular.stdout.log").read_text() if seal_ok else ""
    singular_err = (HERE / "singular.stderr.log").read_text() if seal_ok else ""
    try:
        sage_result = json.loads(sage_text.strip())
    except json.JSONDecodeError:
        sage_result = None
    sage_ok = bool(sage_result and all(sage_result["checks"].values())
                   and commands[2]["exit_code"] == 0 and not sage_err) if seal_ok else False
    singular_errors = bool(re.search(r"(^|\n)\s*(\?|//\s*\*\*)", singular_text)
                           or re.search(r"\berror\b", singular_text + singular_err, re.I))
    singular_ok = bool(seal_ok and commands[3]["exit_code"] == 0
                       and not singular_err and not singular_errors
                       and "CAS10_C01_PASS" in singular_text
                       and "CAS10_C01_FAIL" not in singular_text
                       and all("PASS " + marker in singular_text for marker in SINGULAR_MARKERS))
    version_ok = bool(seal_ok and commands[0]["exit_code"] == 0
                      and "SageMath version 10.9" in (HERE / "sage_version.stdout.log").read_text()
                      and commands[1]["exit_code"] == 0
                      and "version 4.4.1 (44100" in (HERE / "singular_version.stdout.log").read_text())
    passed = seal_ok and sage_ok and singular_ok and version_ok
    sources = {str(path): digest(path) for path in (HERE / "sage_axis.py", HERE / "singular_axis.sing", HERE / "run.py")}
    versions = {
        "sage": "SageMath version 10.9, Release Date: 2026-05-04" if version_ok else "unverified",
        "singular": "4.4.1/44100" if version_ok else "unverified",
        "singular_binary_sha256": seals[str(SINGULAR)]["actual_sha256"],
    }
    completed_at = datetime.now(timezone.utc).isoformat()
    result_path = HERE / "result.json"
    result = {
        "component": "CAS-10-C01",
        "status": "PASS" if passed else "FAIL",
        "checks": {"CAS-10-C01": passed},
        "engine_checks": {"sage": sage_ok, "singular": singular_ok, "versions": version_ok, "seals": seal_ok},
        "sage_computed": sage_result,
        "singular_stdout": singular_text,
        "singular_stderr": singular_err,
        "singular_error_detected": singular_errors,
        "retained_first_failure": {
            "path": str(HERE / "singular.first_failure.stdout.log"),
            "sha256": digest(HERE / "singular.first_failure.stdout.log"),
            "classification": "Singular script syntax error before final checks; corrected by explicit products",
        },
        "commands": commands,
        "seals": seals,
        "sources": sources,
        "versions": versions,
        "domain_assumption_diff": [],
        "counterexample": None,
        "statement_alignment": "Exact equalities over Q[H] imply real-H polynomial identities; strict Lorentz norm only for real H != 0. c>0 is unused in this finite algebraic component. No branch or limit is used.",
        "remaining": ["compressed probability-law equality", "test-power conclusion", "science"],
        "scientific_admission": "HOLD",
        "completed_at": completed_at,
    }
    write_json(result_path, result)
    axis_result = {
        "axis": "sage_singular",
        "status": "PASS" if passed else "FAIL",
        "contract_sha256": EXPECTED[CONTRACT],
        "evidence_class": "exact",
        "completed_at": completed_at,
        "checks": {"CAS-10-C01": passed},
        "domain_assumption_diff": [],
        "counterexample": None,
        "commands": commands,
        "versions": versions,
        "source_artifacts": sources,
        "result_path": str(result_path),
        "result_sha256": digest(result_path),
        "runtime": {"launch_id": None, "authority": "UNAVAILABLE", "model": "UNKNOWN", "effort": "UNKNOWN"},
        "independence_mode": "blind-results-and-derivations",
        "scope": "finite CAS-10-C01 tuple/power and nongeodesic control",
        "scientific_admission": "HOLD",
    }
    write_json(HERE / "axis_result.json", axis_result)
    print(json.dumps({"checks": {"CAS-10-C01": passed}, "domain_assumption_diff": [], "counterexample": None},
                     sort_keys=True, separators=(",", ":")))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
