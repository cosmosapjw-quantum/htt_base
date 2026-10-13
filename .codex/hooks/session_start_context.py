#!/usr/bin/env python3
"""Advisory project context for owner-directed native execution."""
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
            "Current owner-directed mode is native subagent execution with explicit supported model and effort, "
            "fresh bounded contexts, disjoint writer ownership, and a separate independent read-only reviewer. "
            "Record requested and observed runtime separately; unobserved settings remain UNKNOWN. "
            "Removed CUH-G descriptor, hooks and registration are not prerequisites for new native tasks; "
            "do not recreate them or treat historical routing text as active instructions. "
            "Actual system/developer and managed restrictions still apply; identify their source rather than bypass them. "
            "Default to this repo root; preserve dirty/untracked candidates, frozen contracts, raw failures, "
            "historical adjudications, task identities and cumulative usage. No new clone/worktree, reset, clean or automatic stash. "
            "Read the selected task's live RETURN and source identities before acting; "
            "reuse unchanged components and validate affected changes only. "
            "New strength-based proof division does not pass historical four-axis validators. Scientific admission remains HOLD.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}))

if __name__ == "__main__":
    main()
