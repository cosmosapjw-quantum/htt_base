#!/usr/bin/env python3
"""Advisory project context; CUH-G owns routing and native lifecycle."""
from __future__ import annotations
import json
from pathlib import Path

def main() -> None:
    root = Path(__file__).resolve().parents[2]
    text = (f"HTT project: {root}\n"
            "Read AGENTS.md and docs/harness/CURRENT_CODEX_RUNTIME.md. "
            "Use the current global CUH-G descriptor for routing and observed runtime. "
            "For native spawn_agent use the registration's exact agent_type/profile, model and effort; "
            "do not substitute cas_sympy or another domain role, even with matching model/effort. "
            "Reuse the registered launch and carry the frozen CAS assignment in its bounded task message. "
            "Default to this repo root; preserve unrelated edits and frozen active runs. "
            "Bonsai outages and telemetry failures do not stop scientific work. "
            "Historical CAS assignments retain their own contracts; ordinary children "
            "do not create a duplicate project lifecycle. No scientific claim promotion.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}))

if __name__ == "__main__":
    main()
