#!/usr/bin/python3.12
"""Execute the frozen CAS-06 Wolfram axis and retain each raw attempt."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[9]
AXIS = Path(__file__).resolve().parent
BASE = AXIS.parent
CONTRACT = BASE / "EXECUTION_CONTRACT.json"
SOURCE = AXIS / "finite_tov.wl"
COMPONENTS = tuple(f"CAS-06-C0{i}" for i in range(1, 5))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    attempts = AXIS / "attempts"
    attempts.mkdir(exist_ok=True)
    number = 1
    while (attempts / f"attempt_{number:03d}").exists():
        number += 1
    target = attempts / f"attempt_{number:03d}"
    target.mkdir()
    payload_file = target / "engine.json"
    inputs = {"source": SOURCE, "runner": Path(__file__).resolve(),
              "contract": CONTRACT, "neutral_inputs": BASE / "ADMITTED_INPUTS.json",
              "common_spec": ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"}
    hashes_at_start = {key: sha(path) for key, path in inputs.items()}
    shutil.copy2(SOURCE, target / "source_at_start.wl")
    shutil.copy2(Path(__file__).resolve(), target / "runner_at_start.py")
    (target / "input_hashes_at_start.json").write_text(json.dumps(hashes_at_start, indent=2) + "\n")
    argv = ["wolframscript", "-file", str(SOURCE)]
    env = os.environ.copy()
    env["CAS06_ENGINE_OUT"] = str(payload_file)
    started = now()
    timed_out = False
    try:
        completed = subprocess.run(argv, cwd=ROOT, env=env, text=True,
                                   capture_output=True, timeout=1800)
        code = completed.returncode
        stdout, stderr = completed.stdout, completed.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        code = 124
        stdout = (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = (exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
    (target / "stdout.log").write_text(stdout)
    (target / "stderr.log").write_text(stderr)
    messages = re.findall(r"\b(?:[A-Za-z$][\w$`]*::[A-Za-z$][\w$]*|Message\[|Abort\[|\$Failed)\b", stdout + "\n" + stderr)
    payload = None
    parse_error = None
    if payload_file.exists():
        try:
            payload = json.loads(payload_file.read_text())
        except (OSError, ValueError) as exc:
            parse_error = str(exc)
    else:
        parse_error = "engine payload missing"
    hashes_at_end = {key: sha(path) for key, path in inputs.items()}
    inputs_unchanged = hashes_at_end == hashes_at_start
    checks = payload.get("checks", {}) if isinstance(payload, dict) else {}
    check_values_valid = set(checks) == set(COMPONENTS) and all(type(checks[k]) is bool for k in COMPONENTS if k in checks)
    domain_diff = payload.get("domain_assumption_diff", []) if isinstance(payload, dict) else []
    counterexample = payload.get("counterexample") if isinstance(payload, dict) else None
    success = (code == 0 and not timed_out and not messages and parse_error is None
               and inputs_unchanged
               and check_values_valid and all(checks.values())
               and domain_diff == [] and counterexample is None)
    command = {"argv": argv, "cwd": str(ROOT), "started_at": started,
               "completed_at": now(), "exit_code": code, "timeout_seconds": 1800,
               "timed_out": timed_out, "stdout_path": str(target / "stdout.log"),
               "stderr_path": str(target / "stderr.log"), "engine_payload_path": str(payload_file),
               "messages": messages, "parse_error": parse_error}
    command["input_hashes_at_start"] = hashes_at_start
    command["input_hashes_at_end"] = hashes_at_end
    command["inputs_unchanged"] = inputs_unchanged
    (target / "execution.json").write_text(json.dumps(command, indent=2) + "\n")
    result = {"schema_version": 1, "axis": "wolfram_xact",
              "status": "PASS" if success else "FAIL",
              "evidence_class": "exact", "contract_sha256": sha(CONTRACT),
              "completed_at": now(), "commands": [command],
              "checks": checks, "domain_assumption_diff": domain_diff,
              "counterexample": counterexample,
              "source_input_hashes": {str(SOURCE.relative_to(ROOT)): sha(SOURCE),
                                      str(BASE.joinpath("ADMITTED_INPUTS.json").relative_to(ROOT)): sha(BASE / "ADMITTED_INPUTS.json"),
                                      "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md": sha(ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md")},
              "statement_alignment": "owner-adopted finite C01-C04 only; analytic local existence, DEC persistence and distinct-germ interpretation remain HOLD",
              "version": payload.get("details", {}).get("wolfram_version") if isinstance(payload, dict) else None,
              "raw_attempt": str(target), "engine_payload": payload}
    (target / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    (AXIS / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"checks": checks if check_values_valid else {k: False for k in COMPONENTS},
                      "domain_assumption_diff": domain_diff if isinstance(domain_diff, list) else ["invalid engine domain diff"],
                      "counterexample": counterexample}, separators=(",", ":")))
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
