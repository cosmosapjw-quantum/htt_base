#!/usr/bin/env python3
"""Execute the C03 Wolfram+xAct source once and retain full raw evidence."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "weighted_projection.wl"
PROOF = HERE / "PROOF.md"
CONTRACT_SHA256 = "a97dc88082095ba636d326ea390cf629b86ca333577a27638c83c2b7f9a55794"
OBLIGATION = "CAS11-C03-WEIGHTED-PROJECTION"
CHECK_NAMES = {
    "xact_tensor_symmetry",
    "projector_coordinate_idempotence",
    "projector_coordinate_orthogonality",
    "gram_bilinear_polynomial",
    "cauchy_schwarz_square_identity",
    "empty_family_control",
    "dependent_residual_control",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main() -> int:
    started = now()
    executable = shutil.which("wolframscript")
    argv = [executable or "wolframscript", "-file", str(SOURCE)]
    exit_code = None
    timed_out = False
    launch_error = None
    stdout = ""
    stderr = ""
    if executable is None:
        launch_error = "wolframscript executable unavailable"
    else:
        try:
            run = subprocess.run(argv, cwd=HERE, capture_output=True, text=True,
                                 timeout=240, check=False)
            exit_code, stdout, stderr = run.returncode, run.stdout, run.stderr
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout = (exc.stdout or b"").decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = (exc.stderr or b"").decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        except OSError as exc:
            launch_error = str(exc)

    (HERE / "engine.stdout.log").write_text(stdout, encoding="utf-8")
    (HERE / "engine.stderr.log").write_text(stderr, encoding="utf-8")
    marker = "CAS11_C03_CHECKS="
    marker_count = stdout.count(marker)
    checks = None
    parse_error = None
    if marker_count == 1:
        try:
            tail = stdout.split(marker, 1)[1]
            checks, end = json.JSONDecoder().raw_decode(tail.lstrip())
            if tail.lstrip()[end:].strip():
                parse_error = "non-whitespace output after check JSON"
        except json.JSONDecodeError as exc:
            parse_error = str(exc)
    else:
        parse_error = f"expected one check marker, found {marker_count}"
    engine_checks_ok = (isinstance(checks, dict) and set(checks) == CHECK_NAMES
                        and all(value is True for value in checks.values()))
    success = (exit_code == 0 and not timed_out and launch_error is None and parse_error is None
               and engine_checks_ok and PROOF.is_file())
    completed = now()
    execution = {
        "started_at": started,
        "completed_at": completed,
        "argv": argv,
        "cwd": str(HERE),
        "executable": executable,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "launch_error": launch_error,
        "marker_parse_error": parse_error,
        "engine_checks": checks,
        "engine_checks_ok": engine_checks_ok,
        "wolfram_version_line": next((s for s in stdout.splitlines() if s.startswith("WOLFRAM_VERSION=")), None),
        "xact_version_line": next((s for s in stdout.splitlines() if s.startswith("XACT_VERSION=")), None),
        "source_sha256": sha(SOURCE),
        "proof_sha256": sha(PROOF) if PROOF.is_file() else None,
        "stdout_sha256": sha(HERE / "engine.stdout.log"),
        "stderr_sha256": sha(HERE / "engine.stderr.log"),
        "requested_runtime": "parent-assigned wolfram_xact axis; model and effort not provided to this process",
        "observed_author_runtime": "not exposed to this child process",
        "claim_ceiling": "finite mathematical component only; no scientific admission",
    }
    (HERE / "engine.execution.json").write_text(json.dumps(execution, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    axis_result = {
        "axis": "wolfram_xact",
        "status": "PASS" if success else ("BLOCKED_PACKAGE_UNAVAILABLE" if launch_error else "BLOCKED_RESOURCE_LIMIT" if timed_out else "INCONCLUSIVE"),
        "contract_sha256": CONTRACT_SHA256,
        "completed_at": completed,
        "evidence_class": "exact",
        "commands": [{"argv": argv, "cwd": str(HERE), "exit_code": exit_code, "timed_out": timed_out}],
        "source_sha256": sha(SOURCE),
        "proof_sha256": execution["proof_sha256"],
        "raw_stdout": "engine.stdout.log",
        "raw_stderr": "engine.stderr.log",
        "execution_metadata": "engine.execution.json",
        "statement_alignment": "all finite-dimensional real positive-definite W, all subspaces and finite families, including dimension/family zero; no added inverse-R assumption",
        "proof_coverage": "arbitrary-dimension analytic proof in PROOF.md; exact engine algebra checks and scoped xAct tensor symmetry in weighted_projection.wl" if success else "engine or proof obligation incomplete; inspect raw logs",
        "domain_assumption_diff": [],
        "counterexample": None,
    }
    (HERE / "AXIS_RESULT.json").write_text(json.dumps(axis_result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # A failed engine run is inconclusive, never a mathematical counterexample.
    payload = ({"checks": {OBLIGATION: True}, "domain_assumption_diff": [], "counterexample": None}
               if success else {"checks": {}, "domain_assumption_diff": [], "counterexample": None,
                                "engine_error": launch_error or parse_error or "engine check or proof failed"})
    sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")
    return 0 if success else 2


if __name__ == "__main__":
    raise SystemExit(main())
