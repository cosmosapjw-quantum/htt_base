#!/usr/bin/env python3
"""Advisory project context; CUH-G owns routing and native lifecycle."""
from __future__ import annotations
import json
import os
from pathlib import Path
import shlex


def assistance_command() -> str:
    """Resolve the installed authority without importing or running a model."""
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    try:
        state = json.loads((codex_home / "runtime/global-execution-policy.json").read_text())
        source = Path(state["policy_authority"]["repo_root"]) / "src"
        prefix = "PYTHONPATH=" + shlex.quote(str(source))
    except (OSError, ValueError, KeyError, TypeError):
        prefix = "PYTHONPATH=<installed-policy-authority>/src"
    return prefix + " python -m cuhg.models.local_assistance run --spec <bound-helper.json> --store <persistent-task-dir> --request <strict-chat.json>"

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
            "do not create a duplicate project lifecycle. No scientific claim promotion. "
            "Owner-authorized narrow CAS helpers use managed leases and exact input/validator receipts: "
            + assistance_command() + ". "
            "See docs/harness/CAS_LOCAL_ASSISTANCE_CONTINUATION.md for the spec and run/validate/reconcile steps. "
            "Unknown full-domain qualification does not exclude a useful narrow helper or stop hosted continuation. "
            "Native token/cost targets are advisory; replan and continue the same task. "
            "No artificial local task token/attempt ceilings; preserve cumulative usage and historical STOP_BUDGET. "
            "Actual RAM/context limits and uncertain in-flight work still require reconciliation. "
            "CAS05 v3 finite PASS + review returned; next CAS06 input readiness. "
            "Scientific HOLD and CAS04 BLOCKED remain. "
            "Finite helper qualification never promotes science.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}))

if __name__ == "__main__":
    main()
