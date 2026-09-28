#!/usr/bin/env python3
"""Identity transport only. All lifecycle/routing policy is canonical global code."""
import json
import os
from pathlib import Path
import sys
home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
state = json.loads((home / "runtime/global-execution-policy.json").read_text())
root = Path(state["policy_authority"]["repo_root"])
os.execv(sys.executable, [sys.executable, str(root / "src/cuhg/codex_hooks/global_dispatch.py")])
