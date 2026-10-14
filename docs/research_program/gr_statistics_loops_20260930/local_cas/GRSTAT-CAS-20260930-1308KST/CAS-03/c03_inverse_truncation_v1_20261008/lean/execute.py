"""Run the frozen CAS-03-C03 Lean source and retain unabridged evidence."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
ORACLE = pathlib.Path("/home/cosmosapjw/lean_oracles/viii_oracle")
SOURCE = HERE / "CAS03C03.lean"
ROOT = pathlib.Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
UNIT = HERE.parent
CONTRACT = UNIT / "EXECUTION_CONTRACT.json"
INPUTS = UNIT / "ADMITTED_INPUTS.json"
COMMON = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(name: str, argv: list[str], cwd: pathlib.Path) -> dict:
    start = dt.datetime.now(dt.timezone.utc).isoformat()
    proc = subprocess.run(argv, cwd=cwd, capture_output=True, check=False)
    end = dt.datetime.now(dt.timezone.utc).isoformat()
    stdout = HERE / f"{name}.stdout.log"
    stderr = HERE / f"{name}.stderr.log"
    stdout.write_bytes(proc.stdout)
    stderr.write_bytes(proc.stderr)
    return {
        "argv": argv,
        "cwd": str(cwd),
        "started_at": start,
        "completed_at": end,
        "exit_code": proc.returncode,
        "stdout_path": str(stdout),
        "stdout_sha256": sha256(stdout),
        "stderr_path": str(stderr),
        "stderr_sha256": sha256(stderr),
    }


commands = {
    "lean_version": run("lean_version", ["lake", "env", "lean", "--version"], ORACLE),
    "mathlib_revision": run("mathlib_revision", ["git", "rev-parse", "HEAD"], ORACLE / ".lake/packages/mathlib"),
    "lean_check": run("lean_check", ["lake", "env", "lean", str(SOURCE)], ORACLE),
    "forbidden_source_scan": run(
        "forbidden_source_scan",
        ["rg", "-n", r"\b(sorry|admit|axiom)\b", str(SOURCE)],
        ROOT,
    ),
}
record = {
    "axis": "lean",
    "source": str(SOURCE),
    "source_sha256": sha256(SOURCE),
    "contract_sha256": sha256(CONTRACT),
    "admitted_inputs_sha256": sha256(INPUTS),
    "common_spec_sha256": sha256(COMMON),
    "commands": commands,
    "completed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
}
(HERE / "execution.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
if commands["lean_check"]["exit_code"] != 0:
    raise SystemExit(commands["lean_check"]["exit_code"])
if commands["forbidden_source_scan"]["exit_code"] != 1:
    raise SystemExit("forbidden source scan found a match or failed")
