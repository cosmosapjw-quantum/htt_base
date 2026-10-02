#!/usr/bin/env python3
"""Run CAS-03 Wolfram once, retain raw streams, print one typed JSON result."""
import json
import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).resolve().parent
argv = ["wolframscript", "-file", str(here / "check.wl")]
p = subprocess.run(argv, capture_output=True, text=True, cwd=here, timeout=1800)
(here / "raw.stdout.log").write_text(p.stdout)
(here / "raw.stderr.log").write_text(p.stderr)
ids = ["CAS-03-C01", "CAS-03-C02", "CAS-03-C03"]
try:
    payload = p.stdout.split("CAS_JSON_BEGIN\n", 1)[1].split("\nCAS_JSON_END", 1)[0]
    result = json.loads(payload)
    if list(result["checks"]) != ids:
        raise ValueError("check keys differ from contract")
except Exception as exc:
    result = {"checks": {key: False for key in ids}, "domain_assumption_diff": [],
              "counterexample": None, "execution_error": str(exc)}
result["engine_argv"] = argv
result["engine_exit_code"] = p.returncode
result["raw_stdout_path"] = str(here / "raw.stdout.log")
result["raw_stderr_path"] = str(here / "raw.stderr.log")
print(json.dumps(result, separators=(",", ":")))
sys.exit(0 if p.returncode == 0 and all(result["checks"].values()) else 2)
