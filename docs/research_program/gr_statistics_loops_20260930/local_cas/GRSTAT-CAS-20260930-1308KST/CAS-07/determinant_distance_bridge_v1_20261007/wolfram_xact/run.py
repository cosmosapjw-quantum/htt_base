#!/usr/bin/env python3
"""Run the frozen CAS-07 M05 Wolfram+xTensor bridge; stdlib only."""

from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
from datetime import datetime, timezone


HERE = pathlib.Path(__file__).resolve().parent
REPO = next(parent for parent in HERE.parents if (parent / "AGENTS.md").is_file())
BASE = HERE.parent
CONTRACT = BASE / "EXECUTION_CONTRACT.json"
INPUTS = BASE / "ADMITTED_INPUTS.json"
COMMON = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
SOURCE = HERE / "m05_bridge.wl"
EXPECTED = {
    CONTRACT: "24e3ae1e11d2a75335cd7fac436e8d1656100dc7877672d08464a4612a19348e",
    INPUTS: "22fbf2a3fcc428d25f8e9fb0d6e1866c8057ebc7e76dd4ad248bd144300a5a75",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}
CHECK_KEYS = (
    "CAS-07-M05-REWRITE",
    "CAS-07-M05-C02-PREMISE",
    "CAS-07-M05-DETERMINANT-SIGN",
    "CAS-07-M05-DISTANCE-BOUND",
)


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: pathlib.Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    observed = {str(path.relative_to(REPO)): sha256(path) for path in EXPECTED}
    mismatches = [str(path.relative_to(REPO)) for path, digest in EXPECTED.items()
                  if sha256(path) != digest]
    binary = shutil.which("wolframscript")
    kernel = shutil.which("WolframKernel")
    result = {
        "schema": "htt.cas07.m05.wolfram-xact-result.v1",
        "axis": "wolfram_xact",
        "contract_sha256": EXPECTED[CONTRACT],
        "admitted_inputs_sha256": EXPECTED[INPUTS],
        "common_spec_sha256": EXPECTED[COMMON],
        "observed_source_hashes": observed,
        "source_sha256": sha256(SOURCE),
        "runner_sha256": sha256(pathlib.Path(__file__)),
        "launch_id": None,
        "authority_status": "UNAVAILABLE",
        "observed_model": "UNKNOWN",
        "observed_effort": "UNKNOWN",
        "independence_mode": "blind-results-and-derivations",
        "domain_assumption_diff": [],
        "counterexample": None,
        "claim_ceiling": "determinant_and_distance_bridge_only_no_full_theorem_or_science",
        "tool": {
            "wolframscript": binary,
            "wolframscript_sha256": sha256(pathlib.Path(binary)) if binary else None,
            "wolfram_kernel": str(pathlib.Path(kernel).resolve()) if kernel else None,
            "wolfram_kernel_sha256": sha256(pathlib.Path(kernel).resolve()) if kernel else None,
            "python": sys.executable,
            "python_version": sys.version,
        },
        "artifacts": ["m05_bridge.wl", "PROOF.md", "run.py", "wolfram.stdout.log", "wolfram.stderr.log", "result.json",
                      "attempt1.wolfram.stdout.log", "attempt1.wolfram.stderr.log", "attempt1.result.json"],
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    result.update({key: False for key in CHECK_KEYS})
    if mismatches or binary is None:
        result.update(status="BLOCKED", open_lemma="Frozen input mismatch or wolframscript missing", input_mismatches=mismatches)
        write_json(HERE / "result.json", result)
        return 2
    command = [binary, "-file", str(SOURCE)]
    result["executable_command"] = command
    try:
        completed = subprocess.run(command, cwd=REPO, text=True, capture_output=True, timeout=1800, check=False)
    except subprocess.TimeoutExpired as exc:
        (HERE / "wolfram.stdout.log").write_text((exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else exc.stdout or "", encoding="utf-8")
        (HERE / "wolfram.stderr.log").write_text((exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes) else exc.stderr or "", encoding="utf-8")
        result.update(status="BLOCKED", open_lemma="Wolfram execution timed out")
        write_json(HERE / "result.json", result)
        return 2
    (HERE / "wolfram.stdout.log").write_text(completed.stdout, encoding="utf-8")
    (HERE / "wolfram.stderr.log").write_text(completed.stderr, encoding="utf-8")
    result["exit_code"] = completed.returncode
    marker = completed.stdout.split("M05_JSON:", 1)[1] if "M05_JSON:" in completed.stdout else None
    if marker is None:
        result.update(status="BLOCKED", open_lemma="Missing Wolfram JSON receipt")
    else:
        try:
            payload = json.loads(marker)
            checks = payload["checks"]
            if set(checks) != set(CHECK_KEYS) or any(type(checks[key]) is not bool for key in CHECK_KEYS):
                raise ValueError("Unexpected check keys or nonboolean check")
            result.update(checks)
            result["tool"].update(payload["details"])
            result["status"] = "PASS" if completed.returncode == 0 and all(checks.values()) else "BLOCKED"
            if result["status"] != "PASS":
                result["open_lemma"] = "At least one exact check did not close"
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            result.update(status="BLOCKED", open_lemma=f"Invalid Wolfram JSON receipt: {exc}")
    result["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    result["artifact_sha256"] = {name: sha256(HERE / name) for name in
                                 ("m05_bridge.wl", "PROOF.md", "run.py", "wolfram.stdout.log", "wolfram.stderr.log",
                                  "attempt1.wolfram.stdout.log", "attempt1.wolfram.stderr.log", "attempt1.result.json")
                                 if (HERE / name).is_file()}
    write_json(HERE / "result.json", result)
    print(json.dumps({
        "status": result["status"],
        "checks": {key: result[key] for key in CHECK_KEYS},
        "domain_assumption_diff": result["domain_assumption_diff"],
        "counterexample": result["counterexample"],
        "result_path": str(HERE / "result.json"),
    }))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
