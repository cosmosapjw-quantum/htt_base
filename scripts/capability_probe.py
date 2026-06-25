#!/usr/bin/env python3
"""PR07 capability probe: records engine/xAct presence as a registered status.

Absence of the Wolfram engine or xAct is reported explicitly so the symbolic
gate can be skipped with a blocker code rather than silently substituted by a
Python calculation.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

mods = {m: importlib.util.find_spec(m) is not None for m in ["numpy", "scipy", "pytest", "wolframclient"]}
exe = {x: shutil.which(x) for x in ["python3", "wolframscript", "WolframKernel", "math", "git", "gh"]}
payload = {"schema": "htt.pr07.capabilities.v1", "python_modules": mods, "executables": exe,
           "xact": "UNKNOWN_NO_ENGINE"}
wl = exe.get("wolframscript")
if wl:
    code = 'Quiet[Check[Needs["xAct`xTensor`"]; Print["XACT_OK"], Print["XACT_MISSING"]]]'
    p = subprocess.run([wl, "-code", code], text=True, capture_output=True)
    payload["xact"] = "AVAILABLE" if "XACT_OK" in p.stdout else "MISSING_OR_UNLOADABLE"
out = REPO / "docs/generated/pr07_capability_probe.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(payload, indent=2) + "\n")
print(json.dumps(payload, indent=2))
