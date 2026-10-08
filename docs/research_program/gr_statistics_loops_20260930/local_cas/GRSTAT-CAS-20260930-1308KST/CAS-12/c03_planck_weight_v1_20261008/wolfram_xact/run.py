#!/usr/bin/env python3
"""Run the independent CAS-12-C03 Wolfram+xAct finite component check."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
CONTRACT = HERE.parent / "EXECUTION_CONTRACT.json"
INPUTS = HERE.parent / "ADMITTED_INPUTS.json"
SPEC = HERE.parents[4] / "cas" / "COMMON_SPEC.md"
EXPECTED = {
    CONTRACT: "1950de303557d1b805f17a45dc478011bd24e73f06f5444b2ebf9cc3ce06c4a4",
    INPUTS: "22967352d8773a6324fc413d0da748081af52b1a63907af1f3d80119438a2a63",
    SPEC: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}
SOURCE = HERE / "check_planck_weight.wl"
STDOUT = HERE / "wolfram.stdout.log"
STDERR = HERE / "wolfram.stderr.log"
RESULT = HERE / "axis_result.json"
MARKER = "CAS12_C03_RESULT_JSON="


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    observed_hashes = {str(path): sha256(path) for path in EXPECTED}
    matching = all(observed_hashes[str(path)] == expected for path, expected in EXPECTED.items())
    executable = shutil.which("wolframscript")
    argv = [executable, "-file", str(SOURCE)] if executable else []
    start = time.time()
    stdout = b""
    stderr = b""
    exit_code: int | None = None
    error: str | None = None
    if not matching:
        error = "FROZEN_INPUT_HASH_MISMATCH"
    elif not executable:
        error = "WOLFRAMSCRIPT_NOT_FOUND"
    else:
        try:
            completed = subprocess.run(argv, cwd=HERE, capture_output=True, timeout=1800)
            stdout, stderr, exit_code = completed.stdout, completed.stderr, completed.returncode
        except subprocess.TimeoutExpired as exc:
            stdout, stderr = exc.stdout or b"", exc.stderr or b""
            error = "WOLFRAM_TIMEOUT_1800_SECONDS"
        except OSError as exc:
            error = f"WOLFRAM_EXECUTION_ERROR: {exc}"

    STDOUT.write_bytes(stdout)
    STDERR.write_bytes(stderr)
    parsed: dict | None = None
    output_text = stdout.decode("utf-8", errors="replace")
    marker_position = output_text.rfind(MARKER)
    if marker_position >= 0:
        try:
            parsed = json.loads(output_text[marker_position + len(MARKER) :].strip())
        except json.JSONDecodeError as exc:
            error = f"WOLFRAM_RESULT_JSON_ERROR: {exc}"
    if parsed is None and error is None:
        error = "WOLFRAM_RESULT_MARKER_MISSING"
    status = "PASS" if error is None and exit_code == 0 and parsed and parsed.get("status") == "PASS" else "FAIL"
    result = {
        "axis": "wolfram_xact",
        "component": "CAS-12-C03",
        "status": status,
        "contract_sha256": EXPECTED[CONTRACT],
        "admitted_inputs_sha256": EXPECTED[INPUTS],
        "common_spec_sha256": EXPECTED[SPEC],
        "observed_input_hashes": observed_hashes,
        "source": {"path": str(SOURCE), "sha256": sha256(SOURCE)},
        "execution": {
            "argv": argv,
            "cwd": str(HERE),
            "exit_code": exit_code,
            "elapsed_seconds": round(time.time() - start, 3),
            "executable": executable,
            "stdout_path": str(STDOUT),
            "stdout_sha256": sha256(STDOUT),
            "stderr_path": str(STDERR),
            "stderr_sha256": sha256(STDERR),
            "error": error,
        },
        "engine_result": parsed,
        "domain_assumption_diff": parsed.get("domain_assumption_diff") if parsed else [],
        "claim_ceiling": "CAS-12-C03 finite component only; no CAS-12/full/scientific admission",
    }
    write_json(RESULT, result)
    gate = {
        "checks": {"CAS-12-C03": status == "PASS"},
        "domain_assumption_diff": result["domain_assumption_diff"],
        "counterexample": None if status == "PASS" else {"error": error, "engine_result": parsed},
    }
    print(json.dumps(gate, separators=(",", ":")))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
