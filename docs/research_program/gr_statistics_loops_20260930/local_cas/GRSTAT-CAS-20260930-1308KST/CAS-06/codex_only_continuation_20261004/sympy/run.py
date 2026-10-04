"""Run and record the independent SymPy engine under the frozen C03 contract."""

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path


TARGET = "CAS-06-C03-SCALAR"
TIMEOUT_SECONDS = 1800


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    contract_path = args.contract.resolve()
    own_dir = Path(__file__).resolve().parent
    engine = own_dir / "check.py"
    argv = ["/usr/bin/python3.12", "-B", str(engine), "--repo-root", str(repo_root), "--contract", str(contract_path)]
    timed_out = False
    try:
        completed = subprocess.run(argv, cwd=repo_root, capture_output=True, text=True, timeout=TIMEOUT_SECONDS, check=False)
        stdout, stderr, exit_code = completed.stdout, completed.stderr, completed.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = (exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        exit_code = None

    stdout_path = own_dir / "engine.stdout.log"
    stderr_path = own_dir / "engine.stderr.log"
    stdout_path.write_text(stdout)
    stderr_path.write_text(stderr)
    parsed = None
    parse_error = None
    try:
        parsed = json.loads(stdout)
    except (json.JSONDecodeError, TypeError) as exc:
        parse_error = str(exc)
    valid_payload = (
        isinstance(parsed, dict)
        and isinstance(parsed.get("checks"), dict)
        and isinstance(parsed["checks"].get(TARGET), bool)
        and isinstance(parsed.get("domain_assumption_diff"), list)
        and "counterexample" in parsed
    )
    success = (
        not timed_out and exit_code == 0 and valid_payload
        and parsed["checks"][TARGET]
        and parsed["domain_assumption_diff"] == []
        and parsed["counterexample"] is None
    )
    payload = {
        "checks": {TARGET: bool(success)},
        "domain_assumption_diff": parsed["domain_assumption_diff"] if valid_payload else [],
        "counterexample": parsed["counterexample"] if valid_payload else None,
    }
    engine_details = parsed.get("details", {}) if valid_payload else {}
    envelope = {
        "axis": "sympy",
        "status": "PASS" if success else ("INCONCLUSIVE" if timed_out or not valid_payload else "FAIL"),
        "contract_sha256": sha256(contract_path),
        "checks": payload["checks"],
        "domain_assumption_diff": payload["domain_assumption_diff"],
        "counterexample": payload["counterexample"],
        "commands": [{
            "argv": argv,
            "cwd": str(repo_root),
            "exit_code": exit_code,
            "timeout_seconds": TIMEOUT_SECONDS,
            "timed_out": timed_out,
            "stdout_path": str(stdout_path.relative_to(repo_root)),
            "stderr_path": str(stderr_path.relative_to(repo_root)),
        }],
        "evidence_class": "exact",
        "completed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "statement_alignment": engine_details.get("statement_alignment", "Scalar calculus subtarget only; engine details unavailable."),
        "limits": "Only positive-real fixed-action scalar derivatives, algebraic E and derivative ratio. No metric stress/current, TOV, sound propagation, full C03 or scientific admission.",
        "source_hashes": {
            "check.py": sha256(engine),
            "run.py": sha256(Path(__file__).resolve()),
        },
        "contract_source_input_hashes": engine_details.get("common_spec_hashes", []),
        "python_version": engine_details.get("python_version"),
        "python_executable": engine_details.get("python_executable"),
        "sympy_version": engine_details.get("sympy_version"),
        "sympy_origin": engine_details.get("sympy_origin"),
        "engine_details": engine_details,
        "parse_error": parse_error,
    }
    (own_dir / "result.json").write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
