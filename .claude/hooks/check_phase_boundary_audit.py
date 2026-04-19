#!/usr/bin/env python3
"""PreToolUse hook: detect phase-boundary git commits and require both
the integrated phys-math-code audit AND the physics-gallery refresh
before letting them through.

Fires on every Bash tool invocation. Reads the tool_input from stdin
(Claude Code delivers a JSON payload that includes the shell command).
When the command is a phase-boundary `git commit` (matches the
`LB-\\d+:` or `Phase LB complete` or `rotate NEXT_SESSION_PROMPT`
patterns) AND the most recent commits do NOT contain a matching
`AUDIT(<tag>):` entry, emit ``additionalContext`` so Claude is
reminded to execute the audit + gallery refresh first.

The hook is advisory — it never blocks the commit outright. The
load-bearing mechanisms are two feedback memories:

* ``phase_boundary_audit`` — run the audit, fix P0/P1 inline.
* ``phase_boundary_gallery`` — extend and regenerate
  ``figures/physics_gallery/`` every phase boundary.

This hook is a belt-and-suspenders reminder surfaced via
``additionalContext``. Install via ``.claude/settings.json``
``hooks.PreToolUse`` entry.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


PHASE_COMMIT_PATTERNS = [
    r"git\s+commit.*LB-\d+:",
    r"git\s+commit.*Phase LB complete",
    r"git\s+commit.*rotate NEXT_SESSION_PROMPT",
    r"git\s+commit.*FB-\d+(\.\d+)?:",
    r"git\s+commit.*FB-BOOTSTRAP:",
]
# Accept an already-running audit commit — no nagging.
AUDIT_COMMIT_PATTERN = r"git\s+commit.*AUDIT\("


def _is_phase_boundary(cmd: str) -> bool:
    if re.search(AUDIT_COMMIT_PATTERN, cmd):
        return False
    return any(re.search(p, cmd) for p in PHASE_COMMIT_PATTERNS)


def _recent_audit_exists() -> bool:
    """True if any of the last 5 commits is an AUDIT commit."""
    try:
        out = subprocess.check_output(
            ["git", "log", "-5", "--format=%s"],
            stderr=subprocess.DEVNULL, timeout=3,
        ).decode()
    except (subprocess.SubprocessError, OSError):
        return False
    return any(line.startswith("AUDIT(") for line in out.splitlines())


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0
    tool_input = payload.get("tool_input", {}) or {}
    cmd = tool_input.get("command") or ""
    if not isinstance(cmd, str):
        return 0
    if not _is_phase_boundary(cmd):
        return 0
    if _recent_audit_exists():
        # Audit was run recently in this phase cycle — let commit through.
        return 0

    # Emit additionalContext so Claude sees a reminder.
    reminder = (
        "\n\n"
        "[AUTO-AUDIT REMINDER] Phase-boundary commit detected. Before "
        "completing this commit, two tasks must be done in the same "
        "session:\n"
        "  (1) Load docs/audits/AUDIT_PROMPT.md and execute the "
        "integrated phys-math-code audit inline. Fix any P0/P1 findings "
        "and commit with prefix 'AUDIT(<phase-tag>): <short>'.\n"
        "  (2) Extend scripts/make_physics_gallery.py with a new topic "
        "directory (or new plots in an existing topic) covering every "
        "quantity this phase added, then run "
        "'venv/bin/python scripts/make_physics_gallery.py' to regenerate "
        "all PNGs under figures/physics_gallery/. Update "
        "figures/physics_gallery/README.md with the new entries. Visually "
        "inspect each new plot and correct any rendering / physics / "
        "label issues before committing.\n"
        "This reminder fires because no AUDIT(…) commit was found in "
        "the recent history. See feedback memories phase_boundary_audit "
        "and phase_boundary_gallery for the full procedures."
    )
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": reminder,
        }
    }
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
