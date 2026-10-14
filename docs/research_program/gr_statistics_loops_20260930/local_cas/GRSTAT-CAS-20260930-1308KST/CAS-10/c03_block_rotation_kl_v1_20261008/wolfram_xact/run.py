#!/usr/bin/env python3
"""Execute the independent Wolfram+xAct CAS-10-C03 finite component."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone


AXIS_DIR = Path(__file__).resolve().parent
UNIT_DIR = AXIS_DIR.parent
REPO = next(parent for parent in AXIS_DIR.parents if (parent / "AGENTS.md").is_file())
CONTRACT = UNIT_DIR / "EXECUTION_CONTRACT.json"
INPUT = UNIT_DIR / "ADMITTED_INPUTS.json"
COMMON = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
EXPECTED = {
    CONTRACT: "fbb28be7cfe34df459545281460a448947823210615e8c5f7ac2a777b17055de",
    INPUT: "5fda3e643030509d29a096e0daa07dabd5da279cc1bc02a9cd25ca242fd72e78",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}
NAMES = [
    "rotation_orthogonal", "rotation_det_one", "rotation_maps_p",
    "block_rotation_orthogonal", "block_rotation_maps_means",
    "all_five_block_norms", "covariance_positive", "kl_quadratic",
    "h_zero_coincident", "h_zero_kl", "h_one_sigma_one_kl",
]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def main():
    mismatches = {str(path): sha256(path) for path, expected in EXPECTED.items()
                  if sha256(path) != expected}
    if mismatches:
        raise RuntimeError(f"Frozen source hash mismatch: {mismatches}")

    source = AXIS_DIR / "verify.wl"
    argv = ["wolframscript", "-file", str(source)]
    completed = subprocess.run(argv, cwd=REPO, capture_output=True, timeout=1800,
                               check=False)
    stdout_path = AXIS_DIR / "wolfram.stdout.log"
    stderr_path = AXIS_DIR / "wolfram.stderr.log"
    stdout_path.write_bytes(completed.stdout)
    stderr_path.write_bytes(completed.stderr)
    stdout = completed.stdout.decode("utf-8", errors="replace")
    markers = {}
    checks = {}
    for line in stdout.splitlines():
        if line.startswith("CHECK|"):
            _, name, value = line.split("|", 2)
            checks[name] = value == "True"
        elif line.startswith(("WOLFRAM_VERSION|", "XTENSOR_VERSION|", "KL_EXPRESSION|", "ALL_PASS|")):
            name, value = line.split("|", 1)
            markers[name] = value

    exact = (completed.returncode == 0 and set(checks) == set(NAMES)
             and all(checks.values()) and markers.get("ALL_PASS") == "True"
             and markers.get("KL_EXPRESSION") == "(225*h^2)/(64*sP^2)")
    payload = {
        "checks": {"CAS-10-C03": bool(exact)},
        "domain_assumption_diff": [],
        "counterexample": None,
    }
    write_json(AXIS_DIR / "result.json", payload)
    command = {
        "argv": argv,
        "cwd": str(REPO),
        "exit_code": completed.returncode,
        "stdout_path": str(stdout_path.relative_to(REPO)),
        "stdout_sha256": sha256(stdout_path),
        "stderr_path": str(stderr_path.relative_to(REPO)),
        "stderr_sha256": sha256(stderr_path),
    }
    write_json(AXIS_DIR / "execution.json", {
        "command": command,
        "source_path": str(source.relative_to(REPO)),
        "source_sha256": sha256(source),
        "input_sha256": EXPECTED[INPUT],
        "common_spec_sha256": EXPECTED[COMMON],
        "contract_sha256": EXPECTED[CONTRACT],
        "markers": markers,
        "checks": checks,
        "launch_id": None,
        "global_authority": "UNAVAILABLE",
        "observed_model": "UNKNOWN",
        "observed_effort": "UNKNOWN",
    })
    write_json(AXIS_DIR / "axis_result.json", {
        "schema_version": 2,
        "axis": "wolfram_xact",
        "status": "PASS" if exact else "FAIL",
        "contract_sha256": EXPECTED[CONTRACT],
        "source_input_hashes": [
            {"path": str(path.relative_to(REPO)), "sha256": expected}
            for path, expected in EXPECTED.items() if path != CONTRACT
        ],
        "evidence_class": "exact",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "commands": [command],
        "domain_assumption_diff": [],
        "counterexample": None,
        "source_path": str(source.relative_to(REPO)),
        "source_sha256": sha256(source),
        "result_path": str((AXIS_DIR / "result.json").relative_to(REPO)),
        "result_sha256": sha256(AXIS_DIR / "result.json"),
        "versions": {
            "wolfram": markers.get("WOLFRAM_VERSION", "UNKNOWN"),
            "xTensor": markers.get("XTENSOR_VERSION", "UNKNOWN"),
        },
        "launch_id": None,
        "global_authority": "UNAVAILABLE",
        "observed_model": "UNKNOWN",
        "observed_effort": "UNKNOWN",
        "claim_scope": "CAS-10-C03 finite block rotation and equal-covariance KL algebra only",
        "remaining": ["compressed probability-law equality", "test-power conclusion", "science"],
    })
    print(json.dumps(payload, separators=(",", ":")))
    return 0 if exact else 1


if __name__ == "__main__":
    sys.exit(main())
