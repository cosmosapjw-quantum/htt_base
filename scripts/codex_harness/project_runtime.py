#!/usr/bin/env python3
"""Inspect/activate project assets without rebinding or executing research tasks."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import tomllib


def inspect(root: Path, codex_home: Path) -> dict:
    root = root.resolve()
    errors = []
    for relative in ("docs/harness/CURRENT_CODEX_RUNTIME.md",
                     "docs/harness/LEGACY_SHARED_CONTEXT_V1.md",
                     "scripts/install_codex_handoff.sh"):
        if not (root / relative).is_file():
            errors.append(f"Required runtime asset is missing: {relative}")
    try:
        hooks = json.loads((root / ".codex/hooks.json").read_text())["hooks"]
        for event in ("SubagentStart", "SubagentStop"):
            if hooks.get(event):
                errors.append(f"Duplicate project {event} lifecycle must be disabled")
        config = tomllib.loads((root / ".codex/config.toml").read_text())
        if config.get("agents", {}).get("max_depth") != 1:
            errors.append("New native children must not spawn nested children")
        if "job_max_runtime_seconds" in config.get("agents", {}):
            errors.append("Use task-scoped execution limits, not a project-wide worker cutoff")
        fragment = (root / "AGENTS.md.fragment").read_text().strip()
        agents = (root / "AGENTS.md").read_text().strip()
        if not fragment or not agents.endswith(fragment) or agents.count(fragment) != 1:
            errors.append("AGENTS.md.fragment is not the single authoritative suffix")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(f"Project configuration unavailable: {type(exc).__name__}")
    descriptor = codex_home / "runtime/global-execution-policy.json"
    authority = {"status": "UNAVAILABLE", "descriptor": str(descriptor)}
    try:
        state = json.loads(descriptor.read_text())
        source = Path(state["policy_authority"]["repo_root"])
        if source.is_dir() and (source / "docs/GLOBAL_EXECUTION_POLICY.md").is_file():
            authority.update(status="CONFIGURED", source=str(source), head=state["policy_authority"]["head"])
    except (OSError, ValueError, KeyError, TypeError):
        pass
    active = root / ".agent-harness/runtime/ACTIVE_RUN"
    old_active = root / ".agent-harness/ACTIVE_RUN"
    active_values = {str(p.relative_to(root)): p.read_text().strip() for p in (active, old_active) if p.is_file()}
    return {"schema": "htt-project-runtime/v5", "status": "FAIL" if errors else "PASS",
            "root": str(root), "errors": errors, "global_authority": authority,
            "active_run_preserved": next(iter(active_values.values()), None),
            "active_run_pointers": active_values, "workspace_default": "REPO_ROOT",
            "client_hook_trust": "NOT_OBSERVED", "telemetry_delivery": "NOT_OBSERVED",
            "scientific_admission": False}


def activate(root: Path, codex_home: Path) -> dict:
    result = inspect(root, codex_home)
    if result["status"] != "PASS":
        return result
    target = root / ".agent-harness/runtime/current-runtime.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".runtime-", dir=target.parent)
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(result, handle, indent=2); handle.write("\n")
            handle.flush(); os.fsync(handle.fileno())
        os.replace(name, target)
    finally:
        if os.path.exists(name):
            os.unlink(name)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "activate"))
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--codex-home", type=Path, default=Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))))
    args = parser.parse_args()
    result = (activate if args.command == "activate" else inspect)(args.repo_root, args.codex_home)
    try:
        result["codex_version"] = subprocess.check_output(["codex", "--version"], text=True, timeout=10).strip()
    except (OSError, subprocess.SubprocessError):
        result["codex_version"] = "UNAVAILABLE"
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
