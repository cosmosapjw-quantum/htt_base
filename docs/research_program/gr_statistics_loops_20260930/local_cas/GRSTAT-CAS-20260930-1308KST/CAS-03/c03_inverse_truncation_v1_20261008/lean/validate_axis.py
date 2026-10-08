"""Retain the independent stored-envelope schema gate output."""

import datetime as dt
import hashlib
import json
import pathlib
import subprocess

here = pathlib.Path(__file__).resolve().parent
root = pathlib.Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
argv = [
    "python3",
    ".agent-harness/scripts/cas_gate.py",
    "check-axis",
    "--contract",
    str(here.parent / "EXECUTION_CONTRACT.json"),
    "--result",
    str(here / "axis_result.json"),
]
started_at = dt.datetime.now(dt.timezone.utc).isoformat()
proc = subprocess.run(argv, cwd=root, capture_output=True, check=False)
completed_at = dt.datetime.now(dt.timezone.utc).isoformat()
(here / "cas_gate.stdout.log").write_bytes(proc.stdout)
(here / "cas_gate.stderr.log").write_bytes(proc.stderr)
record = {
    "argv": argv,
    "cwd": str(root),
    "started_at": started_at,
    "completed_at": completed_at,
    "exit_code": proc.returncode,
    "stdout_path": str(here / "cas_gate.stdout.log"),
    "stdout_sha256": hashlib.sha256(proc.stdout).hexdigest(),
    "stderr_path": str(here / "cas_gate.stderr.log"),
    "stderr_sha256": hashlib.sha256(proc.stderr).hexdigest(),
}
(here / "gate_validation.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
raise SystemExit(proc.returncode)
