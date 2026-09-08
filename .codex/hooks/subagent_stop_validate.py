#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from _common import load_json, read_stdin_json, resolve_hook_context

# Strict last-line rule (audit H6): the envelope must be the FINAL line of
# the message with no trailing text after it — a MULTILINE search allowed a
# marker followed by arbitrary prose.
MARKER_LINE_RE = re.compile(r"^HARNESS_RESULT:\s*(\{.*\})$")


def block(reason: str) -> None:
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))


def main() -> None:
    event = read_stdin_json()
    try:
        root, binding = resolve_hook_context(event, "stop")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        block(f"Explicit launch context rejected: {exc}")
        return
    code_root = root if binding is not None else Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(code_root / ".agent-harness/scripts"))
    from _harness import ActiveRunError, active_run_id
    from strict_result_validation import load_and_validate_registered_result_file
    harness = root / ".agent-harness"

    # Outside an explicitly active harness run, do not impose the result envelope.
    try:
        active_run = active_run_id(root, required=False)
    except ActiveRunError as exc:
        block(f"Invalid active-run state: {exc.error_code}: {exc.message}")
        return
    if binding is not None and active_run != binding["run_id"]:
        block("Bound run is not active in target worktree")
        return
    if active_run is None:
        return

    if bool(event.get("stop_hook_active")):
        return

    message = str(event.get("last_assistant_message") or "")
    lines = message.rstrip().splitlines()
    match = MARKER_LINE_RE.fullmatch(lines[-1].strip()) if lines else None
    if not match:
        block(
            "Before stopping, write the assignment result artifact and finish "
            "with exactly one FINAL line "
            "(no text after it): "
            'HARNESS_RESULT: {"assignment_id":"...","context_version":"...",'
            '"status":"pass|fail|inconclusive|error","result_path":"..."}'
        )
        return

    try:
        envelope = json.loads(match.group(1))
    except json.JSONDecodeError:
        block(
            "HARNESS_RESULT is not valid single-line JSON. Correct it before stopping."
        )
        return

    required = {"assignment_id", "context_version", "status", "result_path"}
    missing = sorted(required - set(envelope))
    if missing:
        block(f"HARNESS_RESULT is missing required fields: {', '.join(missing)}")
        return

    if binding is not None and envelope["assignment_id"] != binding["assignment_id"]:
        block("Result assignment differs from native start binding")
        return

    index = load_json(harness / "context" / "CONTEXT_INDEX.json", {}) or {}
    current_version = str(index.get("context_version", "UNBUILT"))
    validation = load_and_validate_registered_result_file(
        root,
        Path(str(envelope["result_path"])),
        run_id=active_run,
        context_version=current_version,
        envelope=envelope,
    )
    if validation.errors:
        block("Invalid result artifact: " + "; ".join(validation.errors))


if __name__ == "__main__":
    main()
