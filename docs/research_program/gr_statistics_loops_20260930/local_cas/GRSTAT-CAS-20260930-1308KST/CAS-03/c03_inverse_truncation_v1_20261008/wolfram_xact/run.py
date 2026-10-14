#!/usr/bin/env python3
"""Runner-owned Wolfram replay for observed CAS adjudication."""

import json
import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).resolve().parent
proc = subprocess.run(
    [sys.executable, "-B", str(here / "run_verify.py")],
    cwd=here,
    capture_output=True,
    text=True,
    check=False,
)
raw = (here / "stdout.log").read_text(encoding="utf-8", errors="replace")
err = (here / "stderr.log").read_text(encoding="utf-8", errors="replace")
ok = (
    proc.returncode == 0
    and not err.strip()
    and "COMPONENT_STATUS\tPASS" in raw
    and "FAILED_CHECKS\t{}" in raw
)
payload = {
    "status": "PASS" if ok else "FAIL",
    "checks": {"CAS-03-C03": ok},
    "domain_assumption_diff": [],
    "counterexample": None if ok else "Wolfram replay did not satisfy all exact checks",
    "result_path": str(here / "result.json"),
}
print(json.dumps(payload, separators=(",", ":")))
raise SystemExit(0 if ok else 1)
