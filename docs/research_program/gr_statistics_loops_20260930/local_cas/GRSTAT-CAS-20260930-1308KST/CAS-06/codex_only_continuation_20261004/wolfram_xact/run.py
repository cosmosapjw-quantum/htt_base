#!/usr/bin/env python3
"""Run and retain one exact CAS-06-C03-SCALAR Wolfram/xAct axis attempt."""

import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


AXIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path.cwd().resolve()
CONTRACT = AXIS_DIR.parent / "C03_SCALAR_CONTRACT.json"
COMMON_SPEC = REPO_ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
SOURCE = AXIS_DIR / "check.wl"
EXPECTED_CONTRACT_SHA256 = "7742ee4abac523eabc466435f115de88228a957a3dbed946fa5311f99ab07c27"
OBLIGATION = "CAS-06-C03-SCALAR"
TIMEOUT_SECONDS = 1800


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if (REPO_ROOT / ".git").resolve() != REPO_ROOT / ".git":
        raise RuntimeError("run from the exact existing repository root")
    contract_sha = digest(CONTRACT)
    if contract_sha != EXPECTED_CONTRACT_SHA256:
        raise RuntimeError(f"contract drift: {contract_sha}")
    common_sha = digest(COMMON_SPEC)
    contract = json.loads(CONTRACT.read_text())
    expected_common_sha = contract["identity"]["source_input_hashes"][0]["sha256"]
    if common_sha != expected_common_sha:
        raise RuntimeError(f"common specification drift: {common_sha}")

    argv = ["wolframscript", "-file", "check.wl"]
    exit_code = None
    timed_out = False
    try:
        completed = subprocess.run(
            argv, cwd=AXIS_DIR, capture_output=True, timeout=TIMEOUT_SECONDS
        )
        stdout, stderr, exit_code = completed.stdout, completed.stderr, completed.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout, stderr = exc.stdout or b"", exc.stderr or b""
    attempt_id = str(time.time_ns())
    stdout_path = AXIS_DIR / f"stdout-{attempt_id}.log"
    stderr_path = AXIS_DIR / f"stderr-{attempt_id}.log"
    stdout_path.write_bytes(stdout)
    stderr_path.write_bytes(stderr)

    payload = None
    parse_error = None
    try:
        payload = json.loads(stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        parse_error = str(exc)
    checks = payload.get("checks") if isinstance(payload, dict) else None
    aligned = (
        isinstance(payload, dict)
        and isinstance(checks, dict)
        and set(checks) == {OBLIGATION}
        and type(checks[OBLIGATION]) is bool
        and payload.get("domain_assumption_diff") == []
        and payload.get("counterexample") is None
    )
    if timed_out or parse_error or not aligned:
        status = "INCONCLUSIVE"
    elif exit_code == 0 and checks[OBLIGATION]:
        status = "PASS"
    elif checks[OBLIGATION] is False:
        status = "FAIL"
    else:
        status = "INCONCLUSIVE"

    result = {
        "axis": "wolfram_xact",
        "status": status,
        "contract_sha256": contract_sha,
        "evidence_class": "exact",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "attempt_id": attempt_id,
        "commands": [{
            "argv": argv,
            "cwd": str(AXIS_DIR),
            "timeout_seconds": TIMEOUT_SECONDS,
            "exit_code": exit_code,
            "timed_out": timed_out,
            "stdout_path": str(stdout_path.relative_to(REPO_ROOT)),
            "stdout_sha256": digest(stdout_path),
            "stderr_path": str(stderr_path.relative_to(REPO_ROOT)),
            "stderr_sha256": digest(stderr_path),
        }],
        "source_hashes": {
            "check.wl": digest(SOURCE),
            "run.py": digest(Path(__file__).resolve()),
        },
        "input_hashes": {
            str(CONTRACT.relative_to(REPO_ROOT)): contract_sha,
            str(COMMON_SPEC.relative_to(REPO_ROOT)): common_sha,
        },
        "tool_versions": {
            "wolfram": payload.get("wolfram_version") if isinstance(payload, dict) else None,
            "xAct_xTensor": payload.get("xact_xtensor_version") if isinstance(payload, dict) else None,
        },
        "payload": payload,
        "parse_error": parse_error,
        "statement_alignment": (
            "Exact positive-real scalar P(X)=Pstar exp(s log X), X,Pstar>0, "
            "0<alpha<1 and s=(1+alpha)/(2alpha); first and second derivatives, "
            "algebraic E, ratio, and strictly positive denominator only."
        ),
        "limits": (
            "No metric stress/current variation, TOV, physical sound propagation, "
            "full C03, full CAS06, or scientific admission."
        ),
    }
    rendered = json.dumps(result, indent=2) + "\n"
    (AXIS_DIR / f"result-{attempt_id}.json").write_text(rendered)
    (AXIS_DIR / "result.json").write_text(rendered)
    if status == "PASS":
        final_payload = payload
    else:
        final_payload = {
            "checks": {OBLIGATION: False},
            "domain_assumption_diff": (
                payload.get("domain_assumption_diff", [])
                if isinstance(payload, dict)
                and isinstance(payload.get("domain_assumption_diff", []), list)
                else []
            ),
            "counterexample": {
                "runner_status": status,
                "engine_exit_code": exit_code,
                "timed_out": timed_out,
                "parse_error": parse_error,
            },
        }
    print(json.dumps(final_payload))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
