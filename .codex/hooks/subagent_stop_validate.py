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
    ActiveRunError,
    RESULT_STATUSES,
    active_run_id,
    declared_result_path,
    is_safe_identifier,
    validate_assignment_payload,
    validate_result_payload,
)

# Strict last-line rule (audit H6): the envelope must be the FINAL line of
# the message with no trailing text after it — a MULTILINE search allowed a
# marker followed by arbitrary prose.
MARKER_LINE_RE = re.compile(r"^HARNESS_RESULT:\s*(\{.*\})$")


def block(reason: str) -> None:
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))


def main() -> None:
    event = read_stdin_json()
    root = repo_root()
    harness = root / ".agent-harness"

    # Outside an explicitly active harness run, do not impose the result envelope.
    try:
        active_run = active_run_id(root, required=False)
    except ActiveRunError as exc:
        block(f"Invalid active-run state: {exc.error_code}: {exc.message}")
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
            "Before stopping, write the assignment result artifact and finish with exactly one FINAL line "
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
    # Audit H6: check the DECLARED path for symlinks component-by-component
    # BEFORE resolve() — resolving first loses the link-ness of the declared
    # path itself.
    probe = root
    for part in result_path.parts:
        probe = probe / part
        if probe.is_symlink():
            block(f"result_path traverses a symlink: {probe.relative_to(root)}")
            return
    resolved = (root / result_path).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        block("result_path escapes the repository root.")
        return
    if not resolved.is_file():
        block(f"Declared result artifact does not exist: {result_path}")
        return

    # Audit H1/H6: bind the stop event to the launcher-owned receipt when
    # one exists — the envelope must prove launch identity, not just name an
    # assignment.
    launch_path = (
        harness / "runs" / active_run / "launches" / f"{assignment_id}.json"
    )
    launch = load_json(launch_path, None) if launch_path.is_file() else None
    if launch is not None:
        if str(envelope.get("launch_id", "")) != str(launch.get("launch_id")):
            block(
                "HARNESS_RESULT launch_id does not match the launch receipt "
                f"for {assignment_id!r}."
            )
            return

    result = load_json(resolved, None)

    # Audit H4 (declared-read gate): when a result declares files_read, any
    # sibling result read must be explicitly allowed by the assignment or an
    # adjudication role.
    if isinstance(result, dict):
        files_read = result.get("files_read")
        if isinstance(files_read, list):
            allowed = set(assignment.get("allowed_sibling_results", []) or [])
            results_prefix = f".agent-harness/runs/{active_run}/results/"
            own_result = str(envelope["result_path"])
            for rel in files_read:
                rel_text = str(rel)
                if (
                    rel_text.startswith(results_prefix)
                    and rel_text != own_result
                    and rel_text not in allowed
                    and assignment.get("independence_mode") != "adjudication"
                ):
                    block(
                        f"Blind-results violation: read sibling result {rel_text!r} "
                        "without an explicit allowance."
                    )
                    return

            # Audit H5 (once-delivery): if the start hook injected the full
            # pack (truncated=false), re-reading CONTEXT_PACK.md is a
            # duplicate-delivery violation.
            pack_rel = ".agent-harness/generated/CONTEXT_PACK.md"
            if any(str(rel).endswith("CONTEXT_PACK.md") for rel in files_read):
                deliveries_path = (
                    harness / "runs" / active_run / "launches" / "deliveries.jsonl"
                )
                agent_type = str(result.get("agent_type") or "")
                delivered_full = False
                if deliveries_path.is_file():
                    for line in deliveries_path.read_text(
                        encoding="utf-8"
                    ).splitlines():
                        try:
                            record = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if (
                            record.get("agent_type") in (agent_type, None)
                            or not agent_type
                        ) and record.get("truncated") is False:
                            delivered_full = True
                if delivered_full:
                    block(
                        "Duplicate-delivery violation: the full context pack "
                        f"was hook-injected (truncated=false) yet {pack_rel} "
                        "was re-read. Consume the injected copy only."
                    )
                    return

    result_errors = validate_result_payload(
        result,
        assignment,
        run_id=active_run,
        context_version=current_version,
        launch=launch,
        result_bytes=resolved.stat().st_size,
    )
    if result_errors:
        block("Invalid result artifact: " + "; ".join(result_errors))
        return
    if str(result.get("status")) != str(envelope["status"]):
        block("HARNESS_RESULT status does not match the result artifact.")
        return


if __name__ == "__main__":
    main()
