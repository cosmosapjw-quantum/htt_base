#!/usr/bin/env python3
"""Validate the repository's supported project-local Codex configuration.

The shared-context harness requires a versioned ``.codex/config.toml``.  Current
Codex releases define the concurrency controls below as scalar fields in the
global ``[agents]`` table, while named role definitions remain nested tables.
Reject malformed values and unknown scalars without rejecting that supported
shape.
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib

SUPPORTED_AGENT_GLOBALS = {
    "max_threads": int,
    "max_depth": int,
    "job_max_runtime_seconds": int,
    "interrupt_message": bool,
}


def _is_exact_type(value: object, expected: type[object]) -> bool:
    # ``bool`` is a subclass of ``int``; Codex integer controls must not accept
    # true/false by accident.
    return type(value) is expected


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    cfg = root / ".codex" / "config.toml"
    if not cfg.exists():
        print("OK: no project-local .codex/config.toml present.")
        return 0

    data = tomllib.loads(cfg.read_text(encoding="utf-8"))
    agents = data.get("agents", {})
    if not isinstance(agents, dict):
        print("FAIL: [agents] must be a TOML table.")
        return 1

    errors: list[str] = []
    for key, value in agents.items():
        expected = SUPPORTED_AGENT_GLOBALS.get(key)
        if expected is None:
            if not isinstance(value, dict):
                errors.append(
                    f"agents.{key} is an unsupported scalar; named roles must be tables"
                )
            continue
        if not _is_exact_type(value, expected):
            errors.append(
                f"agents.{key} must be {expected.__name__}, got {type(value).__name__}"
            )
        elif expected is int and value <= 0:
            errors.append(f"agents.{key} must be greater than zero")

    if "project_doc_max_bytes" in data:
        value = data["project_doc_max_bytes"]
        if not _is_exact_type(value, int) or value <= 0:
            errors.append("project_doc_max_bytes must be a positive integer")

    if "approvals_reviewer" in data and data["approvals_reviewer"] not in {
        "user",
        "auto_review",
    }:
        errors.append("approvals_reviewer must be 'user' or 'auto_review'")

    features = data.get("features", {})
    if not isinstance(features, dict):
        errors.append("[features] must be a TOML table")
    elif "hooks" in features and not _is_exact_type(features["hooks"], bool):
        errors.append("features.hooks must be boolean")

    if errors:
        print("FAIL: unsupported project Codex configuration shape.")
        for error in errors:
            print(f"  {error}")
        return 1

    print("OK: project Codex config uses supported shared-context harness fields.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
