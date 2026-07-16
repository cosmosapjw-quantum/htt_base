#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from _common import load_json, read_stdin_json, repo_root

HARNESS_SCRIPTS = Path(__file__).resolve().parents[2] / ".agent-harness" / "scripts"
if str(HARNESS_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(HARNESS_SCRIPTS))

from _harness import (  # noqa: E402
    RESULT_STATUSES,
    declared_result_path,
    is_safe_identifier,
    validate_assignment_payload,
    validate_result_payload,
)

MARKER_RE = re.compile(r"HARNESS_RESULT:\s*(\{[^\n]+\})\s*$", re.MULTILINE)


def block(reason: str) -> None:
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))


def main() -> None:
    event = read_stdin_json()
    root = repo_root()
    harness = root / ".agent-harness"
    active_path = harness / "ACTIVE_RUN"

    # Outside an explicitly active harness run, do not impose the result envelope.
    if not active_path.exists() or not active_path.read_text(encoding="utf-8").strip():
        return

    if bool(event.get("stop_hook_active")):
        return

    message = str(event.get("last_assistant_message") or "")
    match = MARKER_RE.search(message)
    if not match:
        block(
            "Before stopping, write the assignment result artifact and finish with exactly one line: "
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

    index = load_json(harness / "context" / "CONTEXT_INDEX.json", {}) or {}
    current_version = str(index.get("context_version", "UNBUILT"))
    if str(envelope["context_version"]) != current_version:
        block(
            f"Stale result context version {envelope['context_version']!r}; current version is "
            f"{current_version!r}. Reconcile or explicitly report an error result against the current context."
        )
        return

    if str(envelope["status"]) not in RESULT_STATUSES:
        block(
            f"Invalid result status {envelope['status']!r}; use one of "
            f"{sorted(RESULT_STATUSES)}"
        )
        return

    active_run = active_path.read_text(encoding="utf-8").strip()
    assignment_id = str(envelope["assignment_id"])
    if not is_safe_identifier(active_run) or not is_safe_identifier(assignment_id):
        block("Active run or assignment_id is unsafe.")
        return
    assignment_path = (
        harness / "runs" / active_run / "assignments" / f"{assignment_id}.json"
    )
    if not assignment_path.is_file() or assignment_path.is_symlink():
        block(f"No regular registered assignment exists for {assignment_id!r}.")
        return
    assignment = load_json(assignment_path, None)
    assignment_errors = validate_assignment_payload(
        assignment,
        run_id=active_run,
        context_version=current_version,
        assignment_id=assignment_id,
    )
    if assignment_errors:
        block("Invalid registered assignment: " + "; ".join(assignment_errors))
        return

    expected_result_path = declared_result_path(active_run, assignment_id)
    if str(envelope["result_path"]) != expected_result_path:
        block("HARNESS_RESULT result_path does not match the registered assignment.")
        return

    result_path = Path(str(envelope["result_path"]))
    if result_path.is_absolute():
        block("result_path must be repository-relative.")
        return
    resolved = (root / result_path).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        block("result_path escapes the repository root.")
        return
    if not resolved.is_file() or resolved.is_symlink():
        block(f"Declared result artifact does not exist: {result_path}")
        return
    result = load_json(resolved, None)
    result_errors = validate_result_payload(
        result,
        assignment,
        run_id=active_run,
        context_version=current_version,
    )
    if result_errors:
        block("Invalid result artifact: " + "; ".join(result_errors))
        return
    if str(result.get("status")) != str(envelope["status"]):
        block("HARNESS_RESULT status does not match the result artifact.")
        return


if __name__ == "__main__":
    main()
