"""Capture the exact bounded SymPy invocation and raw output."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

axis = Path(__file__).resolve().parent
root = axis.parents[7]
contract = axis.parent / "CONTRACT.json"
argv = ["/usr/bin/python3.12", str(axis / "verify.py")]
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
result = subprocess.run(argv, cwd=root, capture_output=True, text=True, check=False)
ended = datetime.datetime.now(datetime.timezone.utc).isoformat()
(axis / "stdout.log").write_text(result.stdout)
(axis / "stderr.log").write_text(result.stderr)
receipt = {
    "schema": "htt.g03c-exact-boost-map.sympy-execution.v1",
    "contract_sha256": hashlib.sha256(contract.read_bytes()).hexdigest(),
    "script_sha256": hashlib.sha256((axis / "verify.py").read_bytes()).hexdigest(),
    "requested_runtime": "gpt-6-sol/medium",
    "observed_runtime": "UNKNOWN",
    "cwd": str(root), "argv": argv, "start_utc": started, "end_utc": ended,
    "exit_code": result.returncode,
    "stdout": str(axis / "stdout.log"), "stderr": str(axis / "stderr.log"),
    "first_failure": result.stderr.splitlines()[0] if result.stderr else None,
}
(axis / "execution.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt, indent=2))
raise SystemExit(result.returncode)
