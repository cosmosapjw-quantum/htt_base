#!/usr/bin/env python3
"""Conservative Codex project-config validator for this handoff package.

This repo package intentionally avoids project-local .codex/config.toml because
Codex config schemas differ across releases. This script fails if a risky
[agents] table contains scalar values that have triggered AgentRoleToml parser
errors in some versions.
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib

RISKY_SCALAR_TYPES = (str, int, float, bool)


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    cfg = root / ".codex" / "config.toml"
    if not cfg.exists():
        print("OK: no project-local .codex/config.toml present.")
        return 0

    data = tomllib.loads(cfg.read_text(encoding="utf-8"))
    agents = data.get("agents")
    if isinstance(agents, dict):
        risky = {k: v for k, v in agents.items() if isinstance(v, RISKY_SCALAR_TYPES)}
        if risky:
            print("FAIL: .codex/config.toml contains scalar values under [agents].")
            print("These can trigger: expected struct AgentRoleToml in agents")
            for k, v in risky.items():
                print(f"  agents.{k} = {v!r}")
            print(
                "Fix: rm -f .codex/config.toml, or move version-specific "
                "config to user scope after verifying schema."
            )
            return 1
    print("OK: project config did not contain known-risk [agents] scalar values.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
