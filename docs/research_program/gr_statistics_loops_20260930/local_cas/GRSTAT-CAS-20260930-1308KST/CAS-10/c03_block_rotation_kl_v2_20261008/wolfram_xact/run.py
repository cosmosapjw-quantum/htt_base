#!/usr/bin/env python3
"""Execute and record the independent Wolfram+xTensor CAS-10-C03 v2 axis."""
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTRACT = HERE.parent / "EXECUTION_CONTRACT.json"
INPUTS = HERE.parent / "ADMITTED_INPUTS.json"
EXPECTED_CONTRACT = "d64d348c940ea7b37c522fb1043eaa29a6558798104d953fe554b3844ca9811e"
EXPECTED_INPUTS = "d538b90a28b749702209c68e0c73444607295e4b66f2c55d1640d9bd75cf5e53"
OBLIGATION = "CAS-10-C03"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def main():
    if sha(CONTRACT) != EXPECTED_CONTRACT or sha(INPUTS) != EXPECTED_INPUTS:
        raise SystemExit("frozen contract or admitted input bytes drifted")
    contract = json.loads(CONTRACT.read_text())
    if contract["target"]["exact_test_obligations"] != [OBLIGATION]:
        raise SystemExit("unexpected obligation set")
    argv = ["wolframscript", "-file", str(HERE / "proof.wl")]
    start = utc()
    completed = subprocess.run(argv, cwd=HERE, capture_output=True, text=True, timeout=1800)
    end = utc()
    (HERE / "engine.stdout.log").write_text(completed.stdout)
    (HERE / "engine.stderr.log").write_text(completed.stderr)
    version_lines = {key: next((line.split("=", 1)[1] for line in completed.stdout.splitlines()
                                if line.startswith(key + "=")), None)
                     for key in ("WOLFRAM_VERSION", "XTENSOR_VERSION")}
    marker0, marker1 = "CAS10_C03_JSON_BEGIN", "CAS10_C03_JSON_END"
    try:
        result = json.loads(completed.stdout.split(marker0, 1)[1].split(marker1, 1)[0].strip())
        checks = result["checks"]
        passed = (completed.returncode == 0 and bool(checks)
                  and all(v is True for v in checks.values())
                  and (version_lines["WOLFRAM_VERSION"] or "").startswith("15.0.0")
                  and (version_lines["XTENSOR_VERSION"] or "").startswith("{1.3.0"))
        error = None
    except (IndexError, KeyError, ValueError, TypeError) as exc:
        result, checks, passed, error = None, {}, False, str(exc)
    payload = {"checks": {OBLIGATION: bool(passed)}, "domain_assumption_diff": [], "counterexample": None}
    execution = {
        "argv": argv, "cwd": str(HERE), "started_at": start, "completed_at": end,
        "exit_code": completed.returncode, "stdout_path": "engine.stdout.log",
        "stderr_path": "engine.stderr.log", "stdout_sha256": sha(HERE / "engine.stdout.log"),
        "stderr_sha256": sha(HERE / "engine.stderr.log"), "source_sha256": sha(HERE / "proof.wl"),
        "parse_error": error, "parsed_result": result, "versions": version_lines,
    }
    (HERE / "execution.json").write_text(json.dumps(execution, indent=2) + "\n")
    axis = {
        "schema_version": 1, "axis": "wolfram_xact", "status": "PASS" if passed else "INCONCLUSIVE",
        "contract_sha256": EXPECTED_CONTRACT, "completed_at": end, "evidence_class": "exact",
        "commands": [{"argv": argv, "cwd": str(HERE), "exit": completed.returncode,
                      "stdout": "engine.stdout.log", "stderr": "engine.stderr.log"}],
        "proof_source": "proof.wl", "execution_receipt": "execution.json",
        "version_observation": "engine.stdout.log", "versions": version_lines,
        "toolchain": "Wolfram+xTensor",
        "independence_mode": "blind-results-and-derivations", "domain_assumption_diff": [],
        "statement_alignment": "Real H; five Euclidean blocks (1,3,1,3,5) ordered Z monopole, Z dipole, m, p slope, T; sigma_j>0 and sigma_p fourth; no branch or limit.",
        "finite_component": OBLIGATION, "checks": checks,
        "launch_id": None, "observed_model": "UNKNOWN", "observed_effort": "UNKNOWN",
        "scientific_admission": "HOLD",
        "remaining": ["compressed probability-law equality", "test-power conclusion", "science"],
    }
    (HERE / "axis_result.json").write_text(json.dumps(axis, indent=2) + "\n")
    print(json.dumps(payload, separators=(",", ":")))
    return 0 if passed else 2


if __name__ == "__main__":
    sys.exit(main())
