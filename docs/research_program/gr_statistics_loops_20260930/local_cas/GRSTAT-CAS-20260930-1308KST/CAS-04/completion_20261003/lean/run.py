#!/usr/bin/env python3
"""Snapshot and execute the pinned Lean source, preserving every attempt."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[7]
FORMAL = REPO / "formal_mathlib"
SOURCE = HERE / "Proof.lean"
TASK = "GRSTAT-CAS-20260930-1308KST-CAS-04-lean"
TIMEOUT = 3500


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    assert (REPO / ".git").exists(), REPO
    assert sha(FORMAL / "lean-toolchain") == "efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee"
    assert sha(FORMAL / "lake-manifest.json") == "bc86de9aed83fc38b0850702d6879ed6f3c97eedb7d1d69d643160731179d6ed"
    attempts = HERE / "attempts"
    attempts.mkdir(exist_ok=True)
    number = 1
    while (attempts / f"{number:03d}").exists():
        number += 1
    out = attempts / f"{number:03d}"
    out.mkdir()
    snapshot = out / "Proof.lean"
    shutil.copyfile(SOURCE, snapshot)
    argv = ["lake", "env", "lean", str(snapshot)]
    wrapped = ["cuhg-telemetry", "run", "--project", str(REPO), "--task", TASK, "--", *argv]
    version_argv = ["lake", "env", "lean", "--version"]
    version = subprocess.run(version_argv, cwd=FORMAL, text=True, capture_output=True, timeout=30)
    (out / "version.stdout").write_text(version.stdout)
    (out / "version.stderr").write_text(version.stderr)
    start = datetime.now(timezone.utc).isoformat()
    try:
        result = subprocess.run(wrapped, cwd=FORMAL, text=True, capture_output=True, timeout=TIMEOUT)
        exit_code = result.returncode
        stdout, stderr = result.stdout, result.stderr
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        exit_code = 124
        stdout = (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = (exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        timed_out = True
    (out / "stdout.log").write_text(stdout)
    (out / "stderr.log").write_text(stderr)
    receipt = {
        "start_utc": start,
        "end_utc": datetime.now(timezone.utc).isoformat(),
        "cwd": str(FORMAL),
        "argv": wrapped,
        "engine_argv": argv,
        "timeout_seconds": TIMEOUT,
        "timed_out": timed_out,
        "exit_code": exit_code,
        "source_sha256": sha(snapshot),
        "stdout_sha256": sha(out / "stdout.log"),
        "stderr_sha256": sha(out / "stderr.log"),
        "version_argv": version_argv,
        "version_exit_code": version.returncode,
        "version_stdout": version.stdout,
        "toolchain_sha256": sha(FORMAL / "lean-toolchain"),
        "manifest_sha256": sha(FORMAL / "lake-manifest.json"),
    }
    (out / "execution.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(out)
    print("exit_code", exit_code)
    print(stdout[-8000:])
    print(stderr[-2000:], file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
