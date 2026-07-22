#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from _common import emit_additional_context, load_json, read_stdin_json, repo_root

HARNESS_SCRIPTS = Path(__file__).resolve().parents[2] / ".agent-harness" / "scripts"
if str(HARNESS_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(HARNESS_SCRIPTS))

from _harness import ActiveRunError, active_run_id  # noqa: E402


def read_bounded(path: Path, max_chars: int) -> tuple[str, bool]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return f"[missing file: {path}]", False
    if len(text) <= max_chars:
        return text, False
    return (
        text[:max_chars]
        + f"\n...[truncated at {max_chars} characters; perform the file fallback ONCE for the rest]",
        True,
    )


def record_delivery(
    harness: Path,
    active_run: str,
    agent_type: str,
    pack_sha256: str,
    injected_chars: int,
    truncated: bool,
) -> None:
    """Append a once-delivery record (audit H5) — best effort, never blocks."""

    if not active_run or active_run == "none":
        return
    try:
        out_dir = harness / "runs" / active_run / "launches"
        out_dir.mkdir(parents=True, exist_ok=True)
        row = {
            "agent_type": agent_type,
            "pack_sha256": pack_sha256,
            "injected_chars": injected_chars,
            "truncated": truncated,
            "mode": "hook_injected",
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        with (out_dir / "deliveries.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        pass


def main() -> None:
    event = read_stdin_json()
    agent_type = str(event.get("agent_type") or "unknown")
    root = repo_root()
    harness = root / ".agent-harness"
    index_path = harness / "context" / "CONTEXT_INDEX.json"
    pack_path = harness / "generated" / "CONTEXT_PACK.md"
    index = load_json(index_path, {}) or {}

    if not index or not pack_path.exists():
        emit_additional_context(
            "SubagentStart",
            "CONTEXT CONTRACT VIOLATION: the canonical context pack is absent or unbuilt. "
            "Do not perform substantive work. Return an error asking the parent to run "
            "`python3 .agent-harness/scripts/build_context_pack.py`.",
            warning="Subagent started without a built context pack",
        )
        return

    max_chars = int(index.get("max_injected_chars", 24000))
    version = str(index.get("context_version", "UNBUILT"))
    try:
        active_run = active_run_id(root, required=False) or "none"
    except ActiveRunError as exc:
        emit_additional_context(
            "SubagentStart",
            "CONTEXT CONTRACT VIOLATION: active-run state is invalid: "
            f"{exc.error_code}: {exc.message} Do not perform substantive work; "
            "ask the parent to validate or explicitly abandon the local pointer.",
            warning="Subagent started with invalid active-run state",
        )
        return
    pack_text, pack_truncated = read_bounded(pack_path, max_chars)
    pieces = [pack_text]
    used = len(pack_text)

    role_files = index.get("role_files", {}).get(agent_type, [])
    for rel in role_files:
        path = root / rel
        remaining = max_chars - used
        if remaining <= 512:
            break
        role_text, _role_truncated = read_bounded(path, remaining)
        pieces.append(f"\n\n## Role context: {rel}\n{role_text}")
        used += len(role_text)

    try:
        pack_sha256 = hashlib.sha256(pack_path.read_bytes()).hexdigest()
    except OSError:
        pack_sha256 = "UNAVAILABLE"
    record_delivery(harness, active_run, agent_type, pack_sha256, used, pack_truncated)

    delivery_rule = (
        f"Context delivered ONCE by this hook (mode=hook_injected, pack sha256={pack_sha256}, truncated=false). "
        "You MUST NOT re-read CONTEXT_PACK.md — re-reading is a duplicate-delivery violation."
        if not pack_truncated
        else (
            f"Context injection was TRUNCATED (mode=hook_injected, pack sha256={pack_sha256}, truncated=true). "
            "Perform the file fallback exactly once: read CONTEXT_PACK.md one time and record that read in your result's files_read."
        )
    )

    contract = f"""[MANDATORY SUBAGENT BOOTSTRAP]
Agent type: {agent_type}
Active run: {active_run}
Canonical context version: {version}

{delivery_rule}

Your spawn prompt MUST contain RUN_ID, ASSIGNMENT_ID, CONTEXT_VERSION, and INDEPENDENCE_MODE.
Before any broad search or analysis:
1. Verify the prompt CONTEXT_VERSION equals `{version}`.
2. Read `.agent-harness/runs/<RUN_ID>/assignments/<ASSIGNMENT_ID>.json`.
3. Read only files listed by the assignment, plus targeted evidence needed to verify a cited claim.
4. Do not read sibling result files unless INDEPENDENCE_MODE is `adjudication` or the assignment explicitly allows them.
5. Write only to the unique result path in the assignment.
6. Declare every file you read in the result's `files_read` list.
7. End with the required one-line HARNESS_RESULT JSON envelope as the FINAL line (include `launch_id` when a launch receipt exists).
If any required field or file is missing, stop substantive work and return status `error`.

""" + "\n".join(pieces)
    emit_additional_context("SubagentStart", contract)


if __name__ == "__main__":
    main()
