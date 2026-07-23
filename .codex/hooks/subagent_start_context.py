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

from _harness import (  # noqa: E402
    ActiveRunError,
    active_run_id,
    confined_repo_file,
    format_live_context,
    load_validated_context_pack,
    resolve_live_context,
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


def violation(message: str, warning: str) -> None:
    emit_additional_context(
        "SubagentStart",
        f"CONTEXT CONTRACT VIOLATION: {message}",
        warning=warning,
    )


def main() -> None:
    event = read_stdin_json()
    agent_type = str(event.get("agent_type") or "unknown")
    root = repo_root()
    harness = root / ".agent-harness"
    index_path = harness / "context" / "CONTEXT_INDEX.json"

    if index_path.is_symlink() or not index_path.is_file():
        violation(
            "the machine context index is absent or not a regular file. "
            "Do not perform substantive work; ask the parent to repair the harness.",
            "Subagent started without a valid context index",
        )
        return
    index = load_json(index_path, {}) or {}
    if not isinstance(index, dict):
        violation(
            "CONTEXT_INDEX.json must contain an object. Stop substantive work.",
            "Invalid subagent context index",
        )
        return

    try:
        max_chars = int(index.get("max_injected_chars", 0))
    except (TypeError, ValueError):
        violation(
            "max_injected_chars must be an integer in the 8-12 KiB budget. "
            "Stop substantive work and ask the parent to repair CONTEXT_INDEX.json.",
            "Invalid subagent context budget",
        )
        return
    if not 8192 <= max_chars <= 12288:
        violation(
            "max_injected_chars must stay within the 8-12 KiB budget. "
            "Stop substantive work and ask the parent to repair CONTEXT_INDEX.json.",
            "Invalid subagent context budget",
        )
        return

    try:
        active_run = active_run_id(root, required=True)
    except ActiveRunError as exc:
        violation(
            f"active-run state is invalid: {exc.error_code}: {exc.message} "
            "Do not perform substantive work; ask the parent to initialize, "
            "validate, or explicitly abandon the local pointer.",
            "Subagent started without a valid active run",
        )
        return

    version = str(index.get("context_version", "UNBUILT"))
    try:
        live_state = resolve_live_context(root, index)
        run_state = live_state.get("run")
        if (
            not isinstance(run_state, dict)
            or run_state.get("context_version") != version
        ):
            raise ValueError(
                "Active RUN_PLAN context_version does not match CONTEXT_INDEX.json."
            )
        live_context = format_live_context(live_state)
        pack_text = load_validated_context_pack(root, index)
    except (ActiveRunError, OSError, UnicodeError, ValueError) as exc:
        violation(
            f"the live or generated context cannot be validated: {exc}. "
            "Stop substantive work and ask the parent to run "
            "`python3 .agent-harness/scripts/build_context_pack.py` followed by "
            "`python3 .agent-harness/scripts/validate_harness.py`.",
            "Invalid live subagent context",
        )
        return

    role_map = index.get("role_files", {})
    role_files = role_map.get(agent_type, []) if isinstance(role_map, dict) else None
    if not isinstance(role_files, list) or any(
        not isinstance(rel, str) for rel in role_files
    ):
        violation(
            f"role_files for {agent_type!r} must be a list of paths. "
            "Stop substantive work and ask the parent to repair the context index.",
            "Invalid subagent role context",
        )
        return

    role_sections: list[str] = []
    for rel in role_files:
        try:
            role_text = confined_repo_file(
                root, rel, label="Configured role context"
            ).read_text(encoding="utf-8")
        except (OSError, UnicodeError, ValueError) as exc:
            violation(
                f"configured role context is invalid: {rel}: {exc}. "
                "Stop substantive work and ask the parent to repair the context index.",
                "Invalid subagent role context",
            )
            return
        role_sections.append(f"\n\n## Role context: {rel}\n{role_text.rstrip()}")

    pack_sha256 = hashlib.sha256(pack_text.encode("utf-8")).hexdigest()
    contract = f"""[MANDATORY SUBAGENT BOOTSTRAP]
Agent type: {agent_type}
Active run: {active_run}
Context version: {version}
{live_context}

Your spawn prompt MUST contain RUN_ID, ASSIGNMENT_ID, CONTEXT_VERSION, and INDEPENDENCE_MODE.
Before any broad search or analysis:
1. Verify the prompt CONTEXT_VERSION equals `{version}`.
2. Read `.agent-harness/runs/<RUN_ID>/assignments/<ASSIGNMENT_ID>.json`.
3. Read only files listed by the assignment, plus targeted evidence needed to verify a cited claim.
4. Do not read sibling result files unless INDEPENDENCE_MODE is `adjudication` or the assignment explicitly allows them.
5. Write only to the unique result path in the assignment.
6. Declare every file read in the result's `files_read` list.
7. End with the required one-line HARNESS_RESULT JSON envelope as the final line.
If any required field or file is missing, stop substantive work and return status `error`.

Context was delivered once by this hook (pack sha256={pack_sha256}). You MUST NOT re-read CONTEXT_PACK.md.
""" + "".join(role_sections) + f"""

## Generated shared context view
{pack_text.rstrip()}
"""
    if len(contract) > max_chars:
        violation(
            "the bootstrap and role-reserved generated view require "
            f"{len(contract)} characters, above the {max_chars}-character total "
            "budget. Do not read CONTEXT_PACK.md as a fallback. Stop substantive "
            "work and ask the parent to make the generated view compact.",
            "Subagent context exceeds total budget",
        )
        return

    record_delivery(
        harness,
        active_run,
        agent_type,
        pack_sha256,
        len(contract),
        False,
    )
    emit_additional_context("SubagentStart", contract)


if __name__ == "__main__":
    main()
