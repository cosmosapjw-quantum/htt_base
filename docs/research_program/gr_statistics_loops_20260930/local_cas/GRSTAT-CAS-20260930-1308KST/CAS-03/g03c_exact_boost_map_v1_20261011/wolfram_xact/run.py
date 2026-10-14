"""One-shot runner retaining exact argv, cwd, exit, and raw Wolfram streams."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "verify.wl"
ARGV = ["/usr/bin/wolframscript", "-file", str(SOURCE)]


def main() -> int:
    result = subprocess.run(ARGV, cwd=HERE, capture_output=True, timeout=1800)
    (HERE / "stdout.log").write_bytes(result.stdout)
    (HERE / "stderr.log").write_bytes(result.stderr)
    receipt = {
        "schema": "htt.g03c.wolfram-axis.execution.v1",
        "contract_sha256": "c6817a1d5f20c0b2d510c82a0c534a73173b12992bb443a45419817a98ad8143",
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "executable": os.path.realpath(ARGV[0]),
        "argv": ARGV,
        "cwd": str(HERE),
        "exit_code": result.returncode,
        "stdout_file": "stdout.log",
        "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
        "stderr_file": "stderr.log",
        "stderr_sha256": hashlib.sha256(result.stderr).hexdigest(),
        "requested_runtime": "gpt-6-sol/medium",
        "observed_runtime": "UNKNOWN",
    }
    (HERE / "execution.json").write_text(json.dumps(receipt, indent=2) + "\n")
    sys.stdout.buffer.write(result.stdout)
    sys.stderr.buffer.write(result.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
