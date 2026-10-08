#!/usr/bin/env python3
"""Execute the blind CAS-13-C02 Wolfram+xAct finite component."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
CONTRACT = HERE.parent / "EXECUTION_CONTRACT.json"
INPUTS = HERE.parent / "ADMITTED_INPUTS.json"
TEFF_SPEC = HERE.parents[4] / "cas" / "TEFF_INTERVAL_SPEC.md"
COMMON_SPEC = HERE.parents[4] / "cas" / "COMMON_SPEC.md"
EXPECTED = {
    CONTRACT: "66b839cb44573842f36f73c234c4b5b6c8cca639465c58e525b86be8aea754b0",
    INPUTS: "83bb552d9cbc733c58bd57bef88a53ac060261b343b6e9596181586104a68725",
    TEFF_SPEC: "bc055d391d3231c634a14e146f228d3b8179a043485c41ce08754cdeac4fd0fe",
    COMMON_SPEC: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}
SOURCE = HERE / "check_two_node.wl"
STDOUT = HERE / "wolfram.stdout.log"
STDERR = HERE / "wolfram.stderr.log"
RESULT = HERE / "axis_result.json"
MARKER = "CAS13_C02_RESULT_JSON="


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    start = time.monotonic()
    observed_hashes = {str(path): sha256(path) for path in EXPECTED}
    inputs_match = all(observed_hashes[str(path)] == digest for path, digest in EXPECTED.items())
    executable = shutil.which("wolframscript")
    argv = [executable, "-file", str(SOURCE)] if executable else []
    stdout = b""
    stderr = b""
    exit_code: int | None = None
    error: str | None = None
    if not inputs_match:
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
    raw_text = stdout.decode("utf-8", errors="replace")
    marker_position = raw_text.rfind(MARKER)
    if marker_position >= 0:
        try:
            parsed = json.loads(raw_text[marker_position + len(MARKER) :].strip())
        except json.JSONDecodeError as exc:
            error = f"WOLFRAM_RESULT_JSON_ERROR: {exc}"
    elif error is None:
        error = "WOLFRAM_RESULT_MARKER_MISSING"

    status = (
        "PASS"
        if error is None and exit_code == 0 and parsed and parsed.get("status") == "PASS"
        else "INCONCLUSIVE"
    )
    completed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    result = {
        "axis": "wolfram_xact",
        "component": "CAS-13-C02",
        "status": status,
        "contract_sha256": EXPECTED[CONTRACT],
        "admitted_inputs_sha256": EXPECTED[INPUTS],
        "teff_interval_spec_sha256": EXPECTED[TEFF_SPEC],
        "common_spec_sha256": EXPECTED[COMMON_SPEC],
        "observed_input_hashes": observed_hashes,
        "source": {"path": str(SOURCE), "sha256": sha256(SOURCE)},
        "wrapper": {"path": str(Path(__file__).resolve()), "sha256": sha256(Path(__file__))},
        "commands": [
            {"cmd": shlex.join(argv), "cwd": str(HERE), "exit": exit_code}
        ] if argv else [{"cmd": "wolframscript unavailable", "cwd": str(HERE), "exit": None}],
        "evidence_class": "exact",
        "completed_at": completed_at,
        "execution": {
            "argv": argv,
            "cwd": str(HERE),
            "exit_code": exit_code,
            "elapsed_seconds": round(time.monotonic() - start, 3),
            "executable": executable,
            "executable_resolved": str(Path(executable).resolve()) if executable else None,
            "executable_sha256": sha256(Path(executable)) if executable else None,
            "stdout_path": str(STDOUT),
            "stdout_sha256": sha256(STDOUT),
            "stderr_path": str(STDERR),
            "stderr_sha256": sha256(STDERR),
            "error": error,
        },
        "engine_result": parsed,
        "domain_assumption_diff": parsed.get("domain_assumption_diff") if parsed else [],
        "claim_ceiling": "CAS-13-C02 two-node existence/uniqueness/feasibility only; no general extremizer/full/scientific admission",
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    gate = {
        "checks": {"CAS-13-C02": status == "PASS"},
        "domain_assumption_diff": result["domain_assumption_diff"],
        "counterexample": None if status == "PASS" else {
            "error": error,
            "checks": parsed.get("checks") if parsed else None,
        },
    }
    print(json.dumps(gate, separators=(",", ":")))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
