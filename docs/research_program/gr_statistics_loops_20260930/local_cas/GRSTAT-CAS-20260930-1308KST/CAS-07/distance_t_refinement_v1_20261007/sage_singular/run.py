"""Run the CAS07 M06 Sage and pinned Singular checks with raw receipts."""

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[8]
HERE = Path(__file__).resolve().parent
UNIT = HERE.parent
SINGULAR = Path("/home/cosmosapjw/opt/sage/local/bin/Singular")
CONTRACT = UNIT / "EXECUTION_CONTRACT.json"
INPUTS = UNIT / "ADMITTED_INPUTS.json"
OBLIGATIONS = (
    "CAS-07-M06-T-DOMAIN",
    "CAS-07-M06-ETA-ORDER",
    "CAS-07-M06-REFINED-FD1",
    "CAS-07-M06-NO-WORSE-THAN-FD2",
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def execute(argv, cwd):
    proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=1500)
    return {"argv": argv, "cwd": str(cwd), "exit_code": proc.returncode,
            "stdout": proc.stdout, "stderr": proc.stderr}


def main():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    evidence = HERE / "direct_execution" / stamp
    evidence.mkdir(parents=True, exist_ok=False)
    sage = execute(["sage", "-python", str(HERE / "proof_sage.py")], ROOT)
    singular = execute([str(SINGULAR), "-q", str(HERE / "proof.sing")], ROOT)
    sage_version = execute(["sage", "--version"], ROOT)
    singular_version = execute([str(SINGULAR), "--version"], ROOT)
    for name, record in (("sage", sage), ("singular", singular),
                         ("sage_version", sage_version), ("singular_version", singular_version)):
        (evidence / f"{name}.stdout").write_text(record.pop("stdout"))
        (evidence / f"{name}.stderr").write_text(record.pop("stderr"))

    sage_stdout = (evidence / "sage.stdout").read_text()
    sage_stderr = (evidence / "sage.stderr").read_text()
    singular_stdout = (evidence / "singular.stdout").read_text()
    singular_stderr = (evidence / "singular.stderr").read_text()
    try:
        sage_payload = json.loads(sage_stdout)
    except json.JSONDecodeError:
        sage_payload = {}
    sage_checks = sage_payload.get("checks", {})
    expected_sage_checks = {
        "domain_polynomial_identity", "positive_denominator_ratio_identity",
        "fd1_positive_cone_identity", "fd2_positive_cone_identity",
        "flat_distance_from_two_sided_m05", "flat_ratio", "flat_fd1", "flat_fd2",
    }
    sage_ok = (sage["exit_code"] == 0 and not sage_stderr and
               sage_payload.get("status") == "PASS" and
               isinstance(sage_checks, dict) and set(sage_checks) == expected_sage_checks and
               all(value is True for value in sage_checks.values()))
    expected_singular = (
        "DOMAIN_IDENTITY:", "0", "FD1_IDENTITY:", "0",
        "FD2_IDENTITY:", "0", "RATIO_IDEAL_REMAINDER:", "0",
    )
    diagnostic_pattern = re.compile(r"error|wrong|unknown|undefined|exception|warning", re.I)
    singular_ok = (singular["exit_code"] == 0 and not singular_stderr and
                   tuple(singular_stdout.strip().splitlines()) == expected_singular and
                   diagnostic_pattern.search(singular_stdout) is None)
    pinned_ok = (sha(SINGULAR) ==
                 "9430832b7c972b6b26d29ded4d91a3e1df8fd87d67f4b8d3f14d8201a75f923c" and
                 sha(CONTRACT) == "e4169b089e5c19accb838e3b43daa0fe44bfab43b0a5025a3167280069a6eb13" and
                 sha(INPUTS) == "9c85a30bdde1a294930ae40009b121e0e1a767a5c2d5e97fa9e27a3dc14b5bd3" and
                 "SageMath version 10.9" in (evidence / "sage_version.stdout").read_text() and
                 "version 4.4.1 (44100" in (evidence / "singular_version.stdout").read_text())
    core = sage_ok and singular_ok and pinned_ok
    checks = {key: bool(core) for key in OBLIGATIONS}
    payload = {"status": "PASS" if core else "FAIL", "checks": checks,
               "domain_assumption_diff": [], "counterexample": None,
               "result_path": str((HERE / "result.json").relative_to(ROOT))}
    result = {
        "schema_version": 1,
        "axis": "sage_singular",
        "status": payload["status"],
        "evidence_class": "exact",
        "contract_sha256": sha(CONTRACT),
        "admitted_inputs_sha256": sha(INPUTS),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "launch_id": None,
        "authority_status": "UNAVAILABLE",
        "routing": "DIRECT_BY_OWNER_DIRECTIVE",
        "observed_model": "UNKNOWN",
        "observed_effort": "UNKNOWN",
        "commands": [sage, singular, sage_version, singular_version],
        "source_hashes": {str(path.relative_to(ROOT)): sha(path)
                          for path in (HERE / "proof_sage.py", HERE / "proof.sing", Path(__file__))},
        "toolchain": {"sage": "10.9", "singular": "4.4.1/44100",
                      "singular_path": str(SINGULAR), "singular_sha256": sha(SINGULAR)},
        "evidence_dir": str(evidence.relative_to(ROOT)),
        "raw_diagnostic_review": {
            "singular_stdout_exact_expected_zero_identities": singular_ok,
            "singular_stderr_empty": not singular_stderr,
            "sage_stdout_json_all_exact_checks": sage_ok,
            "toolchain_pinned": pinned_ok,
        },
        "checks": checks,
        "domain_assumption_diff": [],
        "counterexample": None,
        "claim_ceiling": "distance_only_refinement_no_endpoint_identification_or_science",
    }
    (evidence / "command_records.json").write_text(json.dumps(result["commands"], indent=2) + "\n")
    (HERE / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0 if core else 1


if __name__ == "__main__":
    sys.exit(main())
