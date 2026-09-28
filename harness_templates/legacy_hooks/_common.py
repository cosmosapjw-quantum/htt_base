from __future__ import annotations

import hashlib
import json
import subprocess
import re
from pathlib import Path
from typing import Any


def read_stdin_json() -> dict[str, Any]:
    import sys

    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def repo_root() -> Path:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if out:
            return Path(out).resolve()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return Path.cwd().resolve()


def load_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def emit_additional_context(event: str, text: str, *, warning: str | None = None) -> None:
    payload: dict[str, Any] = {
        "hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": text,
        }
    }
    if warning:
        payload["systemMessage"] = warning
    print(json.dumps(payload, ensure_ascii=False))


def git_identity(root: Path) -> dict[str, str]:
    """Resolve a real worktree and its individual git-dir, including linked trees."""
    root = root.resolve(strict=True)
    try:
        top = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"], text=True,
            stderr=subprocess.PIPE,
        ).strip()
        git_dir = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "--absolute-git-dir"], text=True,
            stderr=subprocess.PIPE,
        ).strip()
    except subprocess.CalledProcessError as exc:
        raise ValueError("bound root is no longer a valid Git worktree") from exc
    if Path(top).resolve() != root:
        raise ValueError("binding root must be the canonical worktree root")
    return {"worktree_root": str(root), "git_dir": str(Path(git_dir).resolve())}


def _identifier(value: object) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", value):
        raise ValueError("invalid hook session/agent/run/assignment identifier")
    return value


def validate_hook_binding(binding: dict) -> Path:
    """Local source/context identity; this is not model or scientific attestation."""
    root = Path(binding["worktree_root"])
    if git_identity(root) != {k: binding[k] for k in ("worktree_root", "git_dir")}:
        raise ValueError("worktree/git-dir binding changed")
    run_id = _identifier(binding["run_id"])
    assignment_id = _identifier(binding["assignment_id"])
    run_dir = root / ".agent-harness" / "runs" / run_id
    if str(run_dir.resolve(strict=True)) != binding["run_directory"]:
        raise ValueError("run directory binding changed")
    assignment_path = run_dir / "assignments" / f"{assignment_id}.json"
    data = assignment_path.read_bytes()
    if hashlib.sha256(data).hexdigest() != binding["assignment_file_sha256"]:
        raise ValueError("assignment changed after launch binding")
    assignment = json.loads(data)
    index = load_json(root / ".agent-harness/context/CONTEXT_INDEX.json", {})
    plan = load_json(run_dir / "RUN_PLAN.json", {})
    version = binding["context_version"]
    if not isinstance(version, str) or not version or any(not isinstance(o, dict) for o in (assignment, index, plan)):
        raise ValueError("invalid bound context documents")
    if any(o.get("context_version") != version for o in (assignment, index, plan)):
        raise ValueError("bound assignment/context version mismatch")
    if assignment.get("run_id") != run_id or assignment.get("assignment_id") != assignment_id:
        raise ValueError("bound assignment identity mismatch")
    if assignment.get("agent_type") != binding["agent_type"]:
        raise ValueError("bound assignment agent type mismatch")
    return root


def resolve_hook_context(event: dict, phase: str) -> tuple[Path, dict | None]:
    """Consume explicit parent intent, then reuse the actual child's start binding.

    The native client supplies parent session_id and child agent_id. It does not
    change cwd when the parent uses a linked worktree. A parent stages one pending
    assignment immediately before each spawn; start records it by actual agent_id.
    Stop never selects a context from a task name or a current pending assignment.
    """
    launcher = repo_root()
    session = event.get("session_id")
    if session is None:  # Legacy consumers without a session binding keep their contract.
        return launcher, None
    session = _identifier(session)
    directory = launcher / ".agent-harness/runtime/hook_context" / session
    if not directory.exists():
        return launcher, None
    agent_id = _identifier(event.get("agent_id"))
    receipt = directory / "agents" / f"{agent_id}.json"
    if phase == "start":
        if receipt.exists():
            raise ValueError("duplicate native start for already bound agent")
        source = directory / "pending.json"
    elif phase == "stop":
        source = receipt
    else:
        raise ValueError("unknown hook phase")
    binding = json.loads(source.read_text())
    if binding["session_id"] != session or binding["launcher_root"] != str(launcher):
        raise ValueError("launch session/root binding mismatch")
    if event.get("cwd") and Path(event["cwd"]).resolve() != launcher:
        raise ValueError("native event cwd does not match bound launcher")
    if phase == "stop" and (binding.get("agent_id") != agent_id or not binding.get("context_delivered")):
        raise ValueError("no completed native start for this agent")
    if event.get("agent_type") and event["agent_type"] != binding["agent_type"]:
        raise ValueError("native agent type differs from assignment")
    root = validate_hook_binding(binding)
    binding = dict(binding, agent_id=agent_id)
    return root, binding


def record_bound_start(binding: dict | None) -> None:
    if binding is None:
        return
    directory = Path(binding["launcher_root"]) / ".agent-harness/runtime/hook_context" / binding["session_id"]
    directory.joinpath("agents").mkdir(exist_ok=True)
    # Exclusive child receipt: never turn a previous failure into a fresh start.
    target = directory / "agents" / f"{binding['agent_id']}.json"
    with target.open("x") as handle:
        json.dump(dict(binding, context_delivered=True), handle, indent=2)
        handle.write("\n")
    directory.joinpath("pending.json").unlink()
