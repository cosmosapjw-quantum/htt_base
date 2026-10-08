#!/usr/bin/env python3
"""Run the frozen C03 Wolfram axis and emit one JSON gate document on stdout."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[7]
CONTRACT = HERE.parent / "EXECUTION_CONTRACT.json"
ADMITTED = HERE.parent / "ADMITTED_INPUTS.json"
COMMON = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
SOURCE = HERE / "commutator_inverse.wls"
RESULT = HERE / "axis_result.json"
STDOUT = HERE / "attempt_005.stdout.log"
STDERR = HERE / "attempt_005.stderr.log"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    contract = json.loads(CONTRACT.read_text())
    expected = {x["path"]: x["sha256"] for x in contract["identity"]["source_input_hashes"]}
    bound = {
        "contract": sha(CONTRACT),
        "admitted_inputs": sha(ADMITTED),
        "common_spec": sha(COMMON),
        "source": sha(SOURCE),
    }
    source_ok = (
        bound["admitted_inputs"] == expected[str(ADMITTED.relative_to(ROOT))]
        and bound["common_spec"] == expected[str(COMMON.relative_to(ROOT))]
    )
    binary = Path("/usr/bin/wolframscript").resolve()
    argv = [str(binary), "-script", str(SOURCE.relative_to(ROOT))]
    process = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=1800, check=False)
    STDOUT.write_bytes(process.stdout)
    STDERR.write_bytes(process.stderr)
    raw = process.stdout.decode("utf-8", errors="replace")
    marker = "GATE_JSON:"
    computed = None
    try:
        computed = json.loads(raw[raw.index(marker) + len(marker):])
    except (ValueError, json.JSONDecodeError):
        pass
    check_pass = bool(
        source_ok and process.returncode == 0 and isinstance(computed, dict)
        and computed.get("component") == "CAS-15-C03"
        and computed.get("all_pass") is True
        and len(computed.get("checks", [])) == 16
        and all(c.get("pass") is True for c in computed["checks"])
    )
    gate = {
        "checks": {"CAS-15-C03": check_pass},
        "domain_assumption_diff": [],
        "counterexample": None,
        "computed": computed,
    }
    result = {
        "axis": "wolfram_xact",
        "status": "PASS" if check_pass else "FAIL",
        "contract_sha256": bound["contract"],
        "component": "CAS-15-C03",
        "evidence_class": "exact",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "checks": gate["checks"],
        "domain_assumption_diff": [],
        "counterexample": None,
        "commands": [{
            "argv": argv,
            "cwd": str(ROOT),
            "exit_code": process.returncode,
            "stdout": str(STDOUT.relative_to(ROOT)),
            "stderr": str(STDERR.relative_to(ROOT)),
        }],
        "statement_alignment": {
            "scope": "exact finite/local CAS-15-C03 only",
            "domains": "real symmetric M,Mhat; real skew W,What; delta>0,deltahat>0",
            "branches": "ordered real eigenvalues; orthonormal eigenbasis",
            "least_squares": "Frobenius orthogonal projection onto symmetric zero-diagonal commutator image",
            "source": str(SOURCE.relative_to(ROOT)),
            "proof": str((HERE / "PROOF.md").relative_to(ROOT)),
        },
        "hashes": {
            **bound,
            "proof": sha(HERE / "PROOF.md"),
            "stdout": sha(STDOUT),
            "stderr": sha(STDERR),
            "wolframscript_binary": sha(binary),
        },
        "engine_versions": {
            "wolfram": computed.get("wolfram_version") if computed else None,
            "xtensor": computed.get("xtensor_version") if computed else None,
        },
        "executable_artifacts": {
            "wolframscript": str(binary),
            "wolfram_source": str(SOURCE.relative_to(ROOT)),
            "runner": str(Path(__file__).resolve().relative_to(ROOT)),
        },
        "launch_id": None,
        "authority": "UNAVAILABLE_ABSENT",
        "registered_launch_requirement": "NOT_MET",
        "observed_model": "UNKNOWN",
        "observed_effort": "UNKNOWN",
        "lifecycle_status": "BLOCKED",
        "scientific_admission": "HOLD",
        "full_theorem_status": "HOLD",
        "computed": computed,
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(gate, sort_keys=True, separators=(",", ":")))
    return 0 if check_pass else 1


if __name__ == "__main__":
    sys.exit(main())
