#!/usr/bin/env python3
"""Run this independent Wolfram axis once and preserve raw engine output."""

import hashlib
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
SCRIPT = HERE / "run.wl"
ARGV = ["wolframscript", "-file", str(SCRIPT)]

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

proc = subprocess.run(ARGV, cwd=HERE.parents[7], capture_output=True, text=True, timeout=1800)
(HERE / "engine.stdout.log").write_text(proc.stdout)
(HERE / "engine.stderr.log").write_text(proc.stderr)
sentinels = proc.stdout.split("CAS_RESULT_JSON:")
try:
    result, _ = json.JSONDecoder().raw_decode(sentinels[1].lstrip()) if len(sentinels) == 2 else (None, None)
except json.JSONDecodeError:
    result = None
manifest = {
    "argv": ARGV,
    "cwd": str(HERE.parents[7]),
    "exit_code": proc.returncode,
    "script_sha256": sha256(SCRIPT),
    "proof_sha256": sha256(HERE / "proof.md"),
    "stdout_sha256": sha256(HERE / "engine.stdout.log"),
    "stderr_sha256": sha256(HERE / "engine.stderr.log"),
    "wolfram_version": result.get("wolfram_version") if result else None,
    "xtensor_version": result.get("xtensor_version") if result else None,
}
(HERE / "execution.json").write_text(json.dumps(manifest, indent=2) + "\n")
if proc.returncode != 0 or result is None or result.get("checks") != {"CAS-02-C04": True}:
    print(json.dumps({"checks": {"CAS-02-C04": False}, "domain_assumption_diff": [], "counterexample": None}))
    sys.exit(1)
print(json.dumps({"checks": result["checks"], "domain_assumption_diff": result["domain_assumption_diff"], "counterexample": result["counterexample"]}, separators=(",", ":")))
