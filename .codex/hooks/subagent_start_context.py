#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from _common import emit_additional_context, load_json, read_stdin_json, repo_root


def read_bounded(path: Path, max_chars: int) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return f"[missing file: {path}]"
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n...[truncated at {max_chars} characters; read the file directly for the rest]"


def main() -> None:
    event = read_stdin_json()
    agent_type = str(event.get("agent_type") or "unknown")
    root = repo_root()
    harness = root / ".agent-harness"
    index_path = harness / "context" / "CONTEXT_INDEX.json"
    pack_path = harness / "generated" / "CONTEXT_PACK.md"
    active_path = harness / "ACTIVE_RUN"
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
    active_run = active_path.read_text(encoding="utf-8").strip() if active_path.exists() else "none"
    pieces = [read_bounded(pack_path, max_chars)]
    used = len(pieces[0])

    role_files = index.get("role_files", {}).get(agent_type, [])
    for rel in role_files:
        path = root / rel
        remaining = max_chars - used
        if remaining <= 512:
            break
        role_text = read_bounded(path, remaining)
        pieces.append(f"\n\n## Role context: {rel}\n{role_text}")
        used += len(role_text)

    contract = f"""[MANDATORY SUBAGENT BOOTSTRAP]
Agent type: {agent_type}
Active run: {active_run}
Canonical context version: {version}

Your spawn prompt MUST contain RUN_ID, ASSIGNMENT_ID, CONTEXT_VERSION, and INDEPENDENCE_MODE.
Before any broad search or analysis:
1. Verify the prompt CONTEXT_VERSION equals `{version}`.
2. Read `.agent-harness/runs/<RUN_ID>/assignments/<ASSIGNMENT_ID>.json`.
3. Read only files listed by the assignment, plus targeted evidence needed to verify a cited claim.
4. Do not read sibling result files unless INDEPENDENCE_MODE is `adjudication` or the assignment explicitly allows them.
5. Write only to the unique result path in the assignment.
6. End with the required one-line HARNESS_RESULT JSON envelope.
If any required field or file is missing, stop substantive work and return status `error`.

""" + "\n".join(pieces)
    emit_additional_context("SubagentStart", contract)


if __name__ == "__main__":
    main()
