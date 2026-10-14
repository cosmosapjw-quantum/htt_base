"""Run the frozen Wolfram C03 source once and retain complete execution evidence."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[8]
HERE = Path(__file__).resolve().parent
SOURCE = HERE / "verify_c03.wl"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    executable_name = shutil.which("wolframscript")
    if executable_name is None:
        raise RuntimeError("wolframscript is unavailable")
    executable = Path(executable_name).resolve()
    argv = [executable_name, "-file", str(SOURCE)]
    started = datetime.now(timezone.utc).isoformat()
    try:
        completed = subprocess.run(
            argv, cwd=ROOT, capture_output=True, timeout=1800, check=False
        )
        exit_code = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
        timeout = False
    except subprocess.TimeoutExpired as exc:
        exit_code = None
        stdout = exc.stdout or b""
        stderr = exc.stderr or b""
        timeout = True
    (HERE / "stdout.log").write_bytes(stdout)
    (HERE / "stderr.log").write_bytes(stderr)
    receipt = {
        "argv": argv,
        "cwd": str(ROOT),
        "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "exit_code": exit_code,
        "timed_out": timeout,
        "executable_path": str(executable),
        "executable_sha256": sha256(executable),
        "source_path": str(SOURCE),
        "source_sha256": sha256(SOURCE),
        "stdout_path": str(HERE / "stdout.log"),
        "stdout_sha256": sha256(HERE / "stdout.log"),
        "stderr_path": str(HERE / "stderr.log"),
        "stderr_sha256": sha256(HERE / "stderr.log"),
        "contract_sha256": "dbf2a71676fff9aadd9e017ce3853df6d15e9d83b2f53278b38386b7dee1151f",
        "admitted_inputs_sha256": "c198d91d6df5265b6bc2646b4f7d7797f705e4d62c5ca5f09db5faced7dbad45",
        "common_spec_sha256": "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    }
    (HERE / "execution_receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 124 if timeout else (exit_code or 0)


if __name__ == "__main__":
    sys.exit(main())
