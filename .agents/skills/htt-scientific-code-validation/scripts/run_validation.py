#!/usr/bin/env python3
from __future__ import annotations
import json, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.cwd()
OUT = ROOT / "docs" / "harness" / "validation_runs"
OUT.mkdir(parents=True, exist_ok=True)

COMMAND_SETS = {
    "collect": [["python", "-m", "pytest", "--collect-only", "-q"]],
    "contracts": [["python", "-m", "pytest", "tests/contracts", "-q"]],
    "common": [["python", "-m", "pytest", "tests/common", "src/common", "-q"]],
    "mio": [["python", "-m", "pytest", "mio/tests", "-q"]],
    "htt": [["python", "-m", "pytest", "htt/tests", "-q"]],
    "dag": [["python", "scripts/codex_harness/validate_pr_dag.py", "docs/codex_handoff/pr_backlog.yaml"]],
}

def runnable(cmd):
    if cmd[0] == "python": return True
    return shutil.which(cmd[0]) is not None

def run(cmd, timeout=900):
    started = datetime.now(timezone.utc).isoformat()
    try:
        p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
        return {"command": cmd, "started": started, "returncode": p.returncode, "stdout_tail": p.stdout[-12000:], "stderr_tail": p.stderr[-12000:]}
    except subprocess.TimeoutExpired as e:
        return {"command": cmd, "started": started, "returncode": "TIMEOUT", "stdout_tail": (e.stdout or "")[-12000:] if isinstance(e.stdout, str) else "", "stderr_tail": (e.stderr or "")[-12000:] if isinstance(e.stderr, str) else ""}

def main(argv):
    mode = argv[1] if len(argv) > 1 else "collect"
    cmds = COMMAND_SETS.get(mode)
    if not cmds:
        print(f"Unknown mode {mode}. Available: {', '.join(COMMAND_SETS)}", file=sys.stderr)
        return 2
    results=[]
    for cmd in cmds:
        if runnable(cmd):
            results.append(run(cmd))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = OUT / f"validation_{mode}_{stamp}.json"
    path.write_text(json.dumps({"mode": mode, "results": results}, indent=2), encoding="utf-8")
    print(path)
    return 0 if results and all(r["returncode"] == 0 for r in results) else 1
if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
