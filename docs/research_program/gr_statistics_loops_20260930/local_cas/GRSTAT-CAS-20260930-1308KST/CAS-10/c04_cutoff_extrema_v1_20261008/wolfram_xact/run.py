#!/usr/bin/env python3
"""Execute the frozen CAS-10-C04 Wolfram/xTensor axis once and retain raw evidence."""

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[8]
AXIS = Path(__file__).resolve().parent
UNIT = AXIS.parent
CONTRACT = UNIT / "EXECUTION_CONTRACT.json"
INPUT = UNIT / "ADMITTED_INPUTS.json"
COMMON = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
SCRIPT = AXIS / "proof.wl"
EXPECTED = {
    CONTRACT: "8f2f5e387e8130f605073c650c9c0174253dd70e34ae4d4fbb23c697b53ead3a",
    INPUT: "1df59b533e32a7f21d3a7a1ee90c39cf6451b42bcd10d4ec580bdb031a47e992",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def main() -> int:
    for path, expected in EXPECTED.items():
        if digest(path) != expected:
            raise RuntimeError(f"Frozen input drift: {path}")

    argv = ["wolframscript", "-file", str(SCRIPT)]
    try:
        proc = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=1800)
        stdout, stderr, exit_code = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = (exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        stderr += "\nTIMEOUT after 1800 seconds\n"
        exit_code = 124

    stdout_path = AXIS / "wolfram.stdout.log"
    stderr_path = AXIS / "wolfram.stderr.log"
    stdout_path.write_text(stdout)
    stderr_path.write_text(stderr)

    lines = [line.removeprefix("RESULT_JSON=") for line in stdout.splitlines()
             if line.startswith("RESULT_JSON=")]
    payload = json.loads(lines[-1]) if len(lines) == 1 else {
        "checks": {"CAS-10-C04": False},
        "domain_assumption_diff": [],
        "counterexample": "Missing or duplicate RESULT_JSON marker; inspect raw logs",
    }
    if exit_code != 0:
        payload["checks"]["CAS-10-C04"] = False
        payload["counterexample"] = f"Wolfram exited {exit_code}; inspect raw logs"
    result_path = AXIS / "result.json"
    result_path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")

    version = re.search(r"^WOLFRAM_VERSION=(.*)$", stdout, re.MULTILINE)
    xtensor = re.search(r"^XTENSOR_VERSION=(.*)$", stdout, re.MULTILINE)
    passed = (exit_code == 0 and payload == {
        "checks": {"CAS-10-C04": True},
        "domain_assumption_diff": [], "counterexample": None,
    } and version is not None and xtensor is not None
              and "15.0.0" in version.group(1)
              and "1.3.0" in xtensor.group(1))
    axis_result = {
        "axis": "wolfram_xact",
        "status": "PASS" if passed else "BLOCKED",
        "contract_sha256": EXPECTED[CONTRACT],
        "evidence_class": "exact",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "checks": payload["checks"],
        "domain_assumption_diff": payload["domain_assumption_diff"],
        "counterexample": payload["counterexample"],
        "tool_versions": {
            "wolfram": version.group(1) if version else "UNKNOWN",
            "xTensor": xtensor.group(1) if xtensor else "UNKNOWN",
        },
        "commands": [{
            "argv": argv,
            "cwd": str(ROOT),
            "exit_code": exit_code,
            "stdout_path": rel(stdout_path),
            "stdout_sha256": digest(stdout_path),
            "stderr_path": rel(stderr_path),
            "stderr_sha256": digest(stderr_path),
        }],
        "source_artifacts": [{"path": rel(SCRIPT), "sha256": digest(SCRIPT)},
                             {"path": rel(Path(__file__)), "sha256": digest(Path(__file__))}],
        "result_path": rel(result_path),
        "result_sha256": digest(result_path),
        "input_sha256": EXPECTED[INPUT],
        "common_spec_sha256": EXPECTED[COMMON],
        "launch_id": None,
        "requested_profile": "UNAVAILABLE",
        "observed_model": "UNKNOWN",
        "observed_effort": "UNKNOWN",
        "statement_alignment": "Exact CAS-10-C04 finite polynomial component on real t in [0,1]; exp/sqrt auxiliary inequalities remain stated inputs.",
    }
    (AXIS / "axis_result.json").write_text(json.dumps(axis_result, indent=2, sort_keys=True) + "\n")
    sys.stdout.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
