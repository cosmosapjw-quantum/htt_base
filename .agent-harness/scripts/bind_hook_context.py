#!/usr/bin/env python3
"""Stage explicit worktree context immediately before one native spawn.

No model dispatch, profile attestation or scientific acceptance is implied.
The start hook consumes this intent and records the platform-supplied child ID.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".codex/hooks"))
from _common import _identifier, git_identity, validate_hook_binding


def stage_binding(launcher: Path, root: Path, session: str, run: str, assignment_id: str) -> Path:
    session, run, assignment_id = map(_identifier, (session, run, assignment_id))
    launcher_identity, identity = git_identity(launcher), git_identity(root)
    root = Path(identity["worktree_root"])
    run_dir = root / ".agent-harness/runs" / run
    assignment_path = run_dir / "assignments" / f"{assignment_id}.json"
    raw = assignment_path.read_bytes()
    assignment = json.loads(raw)
    value = dict(identity, launcher_root=launcher_identity["worktree_root"],
                 session_id=session, run_id=run, assignment_id=assignment_id,
                 run_directory=str(run_dir.resolve(strict=True)),
                 assignment_file_sha256=hashlib.sha256(raw).hexdigest(),
                 context_version=assignment["context_version"],
                 agent_type=assignment["agent_type"])
    validate_hook_binding(value)
    directory = launcher / ".agent-harness/runtime/hook_context" / session
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "pending.json"
    with target.open("x") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--launcher-root", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--assignment-id", required=True)
    args = parser.parse_args()
    print(stage_binding(args.launcher_root, args.repo_root, args.session_id,
                        args.run_id, args.assignment_id))
