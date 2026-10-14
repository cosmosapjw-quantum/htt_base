#!/usr/bin/env python3
"""Runner-owned Lean replay for observed CAS adjudication."""

import json
import pathlib
import re
import subprocess
import sys

here = pathlib.Path(__file__).resolve().parent
proc = subprocess.run(
    [sys.executable, "-B", str(here / "execute.py")],
    cwd=here,
    capture_output=True,
    text=True,
    check=False,
)
(here / "runner.stdout.log").write_text(proc.stdout, encoding="utf-8")
(here / "runner.stderr.log").write_text(proc.stderr, encoding="utf-8")
lean_log = (here / "lean_check.stdout.log").read_text(encoding="utf-8", errors="replace")
source = (here / "CAS03C03.lean").read_text(encoding="utf-8")
forbidden = re.search(r"\\b(?:sorry|admit|axiom)\\b", source) is not None
ok = (
    proc.returncode == 0
    and not proc.stderr.strip()
    and not forbidden
    and "CAS03C03.exact_inverse" in lean_log
    and "CAS03C03.trunc_defect" in lean_log
)
print(json.dumps({
    "status": "PASS" if ok else "FAIL",
    "checks": {"CAS-03-C03": ok},
    "domain_assumption_diff": [],
    "counterexample": None if ok else "Lean replay or forbidden-source check failed",
    "result_path": str(here / "result.json"),
}, separators=(",", ":")))
raise SystemExit(0 if ok else 1)
