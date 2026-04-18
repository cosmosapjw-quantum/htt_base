#!/usr/bin/env python3
"""PreToolUse hook: detect phase-boundary git commits and require the
integrated phys-math-code audit before letting them through.

Fires on every Bash tool invocation. Reads the tool_input from stdin
(Claude Code delivers a JSON payload that includes the shell command).
When the command is a phase-boundary `git commit` (matches the
`LB-\\d+:` or `Phase LB complete` or `rotate NEXT_SESSION_PROMPT`
patterns) AND the most recent commits do NOT contain a matching
`AUDIT(<tag>):` entry, emit ``additionalContext`` so Claude is
reminded to execute the audit first.

The hook is advisory — it never blocks the commit outright. The
load-bearing mechanism is the feedback memory `phase_boundary_audit`
which tells every future Claude session to run the audit
unprompted; this hook is a belt-and-suspenders reminder.

Install via ``.claude/settings.json`` ``hooks.PreToolUse`` entry.
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
        "completing this commit, load docs/audits/AUDIT_PROMPT.md and "
        "execute the integrated phys-math-code audit inline. Fix any "
        "P0/P1 findings in-session and commit with prefix "
        "'AUDIT(<phase-tag>): <short>'. This reminder fires because no "
        "AUDIT(…) commit was found in the recent history. See feedback "
        "memory phase_boundary_audit for the full procedure."
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
