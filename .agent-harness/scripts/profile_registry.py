#!/usr/bin/env python3
"""Unique custom-agent profile registry (audit H1).

Single source of truth for the installed `.codex/agents/*.toml` profiles.
Fails closed on duplicate `name` values across files and on same-name
sandbox conflicts — the silent last-write-wins dict that previously masked
duplicates is the exact defect this replaces
(`scripts/codex_harness/test_codex_assets.py` pre-PR-124).
"""
from __future__ import annotations

import hashlib
import tomllib
from pathlib import Path


class ProfileRegistryError(RuntimeError):
    pass


def load_profile_registry(repo: Path) -> dict[str, dict]:
    """Return {name: {path, config_sha256, sandbox_mode, ...}} or raise."""

    agent_dir = repo / ".codex" / "agents"
    if not agent_dir.is_dir():
        raise ProfileRegistryError(f"missing agent profile dir: {agent_dir}")
    registry: dict[str, dict] = {}
    for path in sorted(agent_dir.glob("*.toml")):
        raw = path.read_bytes()
        try:
            data = tomllib.loads(raw.decode("utf-8"))
        except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
            raise ProfileRegistryError(f"unparseable profile {path.name}: {exc}")
        name = data.get("name")
        if not isinstance(name, str) or not name:
            raise ProfileRegistryError(f"profile {path.name} lacks a name")
        sandbox = data.get("sandbox_mode")
        if sandbox not in {"read-only", "workspace-write"}:
            raise ProfileRegistryError(
                f"profile {path.name} has invalid sandbox_mode: {sandbox!r}"
            )
        if name in registry:
            previous = registry[name]
            conflict = (
                " with CONFLICTING sandbox_mode"
                f" ({previous['sandbox_mode']!r} vs {sandbox!r})"
                if previous["sandbox_mode"] != sandbox
                else ""
            )
            raise ProfileRegistryError(
                f"duplicate profile name {name!r}: {previous['path']} and "
                f"{path.name}{conflict}"
            )
        registry[name] = {
            "path": path.relative_to(repo).as_posix(),
            "config_sha256": hashlib.sha256(raw).hexdigest(),
            "sandbox_mode": sandbox,
            "description": data.get("description", ""),
        }
    if not registry:
        raise ProfileRegistryError("no agent profiles installed")
    return registry


def main() -> None:
    from _harness import root

    registry = load_profile_registry(root())
    for name, row in sorted(registry.items()):
        print(f"{name}\t{row['sandbox_mode']}\t{row['path']}\t{row['config_sha256'][:12]}")


if __name__ == "__main__":
    main()
