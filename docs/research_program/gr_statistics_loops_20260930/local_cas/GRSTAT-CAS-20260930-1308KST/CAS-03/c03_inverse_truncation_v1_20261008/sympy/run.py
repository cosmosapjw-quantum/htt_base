#!/usr/bin/env python3
"""Runner-owned SymPy replay for observed CAS adjudication."""

import json
import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).resolve().parent
proc = subprocess.run(
    ["/usr/bin/python3", str(here / "verify_c03.py")],
    cwd=here,
    capture_output=True,
    text=True,
    check=False,
)
(here / "runner.stdout.log").write_text(proc.stdout, encoding="utf-8")
(here / "runner.stderr.log").write_text(proc.stderr, encoding="utf-8")
ok = (
    proc.returncode == 0
    and not proc.stderr.strip()
    and '"component": "CAS-03-C03"' in proc.stdout
    and '"status": "PASS"' in proc.stdout
)
print(json.dumps({
    "status": "PASS" if ok else "FAIL",
    "checks": {"CAS-03-C03": ok},
    "domain_assumption_diff": [],
    "counterexample": None if ok else "SymPy replay did not satisfy all exact checks",
    "result_path": str(here / "result.json"),
}, separators=(",", ":")))
raise SystemExit(0 if ok else 1)
