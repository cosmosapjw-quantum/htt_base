#!/usr/bin/env python3
"""No-argument, runner-observable wrapper for the frozen SymPy axis."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import uuid


CONTRACT_SHA256 = "d62613255f18b2d2d2140cc6d73fbac27f6b2f8ac40ed9b268b9f5fc0fa166af"
INPUT_SHA256 = "849f9ebde2894f1deb15ba61452a3cc911d46af960b8630694cfe8cc15e3620a"
SOURCE_SHA256 = "5a1d4eb9c355b75c98bf74011aaaca44aba628a36f00aff6215cb91839a0925c"
OBLIGATION = "PORT-CAS-02"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main() -> int:
    axis_dir = Path(__file__).resolve().parent
    repo = axis_dir.parents[6]
    source = axis_dir / "null_form_lift.py"
    contract = axis_dir.parent / "EXECUTION_CONTRACT.json"
    inputs = axis_dir.parent / "ADMITTED_INPUTS.json"
    run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + uuid.uuid4().hex[:8]
    run_dir = axis_dir / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    actual_hashes = {
        "contract": sha256(contract.read_bytes()),
        "inputs": sha256(inputs.read_bytes()),
        "source": sha256(source.read_bytes()),
    }
    expected_hashes = {
        "contract": CONTRACT_SHA256,
        "inputs": INPUT_SHA256,
        "source": SOURCE_SHA256,
    }
    drift = [name for name in expected_hashes if actual_hashes[name] != expected_hashes[name]]
    argv = [sys.executable, "-B", str(source)]
    raw_stdout = b""
    raw_stderr = b""
    exit_code = None
    timed_out = False
    launch_error = None
    if not drift:
        try:
            proc = subprocess.run(argv, cwd=repo, capture_output=True, timeout=1800, check=False)
            raw_stdout, raw_stderr, exit_code = proc.stdout, proc.stderr, proc.returncode
        except subprocess.TimeoutExpired as exc:
            raw_stdout = exc.stdout or b""
            raw_stderr = exc.stderr or b""
            timed_out = True
        except OSError as exc:
            launch_error = str(exc)

    stdout_path = run_dir / "stdout.log"
    stderr_path = run_dir / "stderr.log"
    stdout_path.write_bytes(raw_stdout)
    stderr_path.write_bytes(raw_stderr)
    completed_at = dt.datetime.now(dt.timezone.utc).isoformat()
    receipt = {
        "argv": argv,
        "cwd": str(repo),
        "completed_at": completed_at,
        "exit": exit_code,
        "timed_out": timed_out,
        "launch_error": launch_error,
        "actual_hashes": actual_hashes,
        "expected_hashes": expected_hashes,
        "raw_stdout_sha256": sha256(raw_stdout),
        "raw_stderr_sha256": sha256(raw_stderr),
        "raw_stdout": str(stdout_path),
        "raw_stderr": str(stderr_path),
    }
    receipt_path = run_dir / "execution.json"
    write_json(receipt_path, receipt)

    output = None
    parse_error = None
    if raw_stdout:
        try:
            output = json.loads(raw_stdout)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            parse_error = str(exc)
    checks = output.get("checks") if isinstance(output, dict) else None
    valid_checks = (
        isinstance(checks, dict)
        and len(checks) == 23
        and all(type(value) is bool for value in checks.values())
    )
    algebra_pass = (
        not drift
        and exit_code == 0
        and isinstance(output, dict)
        and output.get("axis") == "sympy"
        and output.get("status") == "PASS"
        and valid_checks
        and all(checks.values())
    )
    if drift:
        axis_status = "MISALIGNED_ASSUMPTIONS"
    elif timed_out:
        axis_status = "BLOCKED_RESOURCE_LIMIT"
    elif launch_error:
        axis_status = "BLOCKED_PACKAGE_UNAVAILABLE"
    elif valid_checks and any(not value for value in checks.values()):
        axis_status = "FAIL"
    elif algebra_pass:
        axis_status = "PASS"
    else:
        axis_status = "INCONCLUSIVE"

    axis_result = {
        "axis": "sympy",
        "status": axis_status,
        "evidence_class": "exact",
        "contract_sha256": actual_hashes["contract"],
        "admitted_inputs_sha256": actual_hashes["inputs"],
        "contract_id": "TYPEFREE-PORT-CAS-02-NULL-FORM-LIFT-V1",
        "scope": "PORT-CAS-02 finite exact algebra only",
        "completed_at": completed_at,
        "tool_versions": {
            "python": output.get("python_version") if isinstance(output, dict) else sys.version.split()[0],
            "sympy": output.get("sympy_version") if isinstance(output, dict) else "UNKNOWN",
            "python_executable": sys.executable,
        },
        "commands": [{
            "argv": argv,
            "cwd": str(repo),
            "exit": exit_code,
            "timed_out": timed_out,
            "stdout": str(stdout_path),
            "stdout_sha256": receipt["raw_stdout_sha256"],
            "stderr": str(stderr_path),
            "stderr_sha256": receipt["raw_stderr_sha256"],
        }],
        "artifacts": {
            "source": str(source),
            "source_sha256": actual_hashes["source"],
            "execution_receipt": str(receipt_path),
            "raw_stdout": str(stdout_path),
            "raw_stderr": str(stderr_path),
        },
        "alignment": {
            "metric": "diag(-1,1,1,1), inverse equal to itself",
            "K": "contravariant (-1,n), real n.n=1",
            "S": "covariant symmetric S00=h0, S0i=-h1_i/2, Sij=qij",
            "q": "real symmetric; tracefree specialization qzz=-qxx-qyy; identity also checked before restriction",
            "u": "future unit timelike for physical interpretation; equivalence algebra valid for arbitrary real u",
            "st": "real mixed-index eigenvalue",
            "branch": "future timelike; no eigenline existence inferred from algebra",
            "gauge": "S->S+a*g, st->st+a, a real",
        },
        "checks": checks if valid_checks else {},
        "canonical": output.get("canonical", {}) if isinstance(output, dict) else {},
        "independence": "No sibling scripts, derivations, threads, or result files consulted during axis proof",
        "global_launch_id": None,
        "global_registration_observed": False,
        "observed_model": "UNKNOWN",
        "observed_effort": "UNKNOWN",
        "lifecycle_status": "BLOCKED_UNREGISTERED_LAUNCH",
        "runner_observed_four_axis_eligibility": False,
        "scientific_admission": "HOLD",
        "run_id": run_id,
        "parse_error": parse_error,
        "drift": drift,
        "limitations": [
            "Stored axis result alone cannot confer four-axis CAS status",
            "No analytic existence, uniqueness, geodesicity, vorticity, or scientific claim",
        ],
    }
    write_json(axis_dir / "axis_result.json", axis_result)

    assumption_diff = [f"{name} SHA256 drift" for name in drift]
    if timed_out:
        assumption_diff.append("SymPy source timed out")
    if launch_error:
        assumption_diff.append("SymPy source launch failed")
    counterexample = None
    if axis_status == "FAIL":
        counterexample = {"failed_checks": sorted(key for key, value in checks.items() if not value)}
    # This is exactly the parent gate's minimum payload for one obligation.
    payload = {
        "checks": {OBLIGATION: algebra_pass},
        "domain_assumption_diff": assumption_diff,
        "counterexample": counterexample,
    }
    print(json.dumps(payload, sort_keys=True))
    return 0 if algebra_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
