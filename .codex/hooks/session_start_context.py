#!/usr/bin/env python3
"""Advisory project context for owner-directed native execution."""
from __future__ import annotations
import json
import os
from pathlib import Path
import shlex


def assistance_command() -> str:
    """Resolve the installed authority without importing or running a model."""
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    try:
        state = json.loads((codex_home / "runtime/global-execution-policy.json").read_text())
        source = Path(state["policy_authority"]["repo_root"]) / "src"
        prefix = "PYTHONPATH=" + shlex.quote(str(source))
    except (OSError, ValueError, KeyError, TypeError):
        prefix = "PYTHONPATH=<installed-policy-authority>/src"
    return prefix + " python -m cuhg.models.local_assistance run --spec <bound-helper.json> --store <persistent-task-dir> --request <strict-chat.json>"

def active_controller_context(root: Path) -> str:
    """Read a host-installed pointer; never initialize, replay or launch work."""
    pointer = root / ".agent-harness/runtime/ACTIVE_CONTROLLER.json"
    if not pointer.is_file():
        return " No active-controller pointer is installed; inspect the selected task's current source before continuation."
    try:
        binding = json.loads(pointer.read_text())
        path = Path(binding["state_path"])
        if not path.is_absolute():
            path = root / path
        path = path.resolve()
        if not path.is_relative_to((root / ".agent-harness/runtime").resolve()):
            raise ValueError("state source outside project runtime")
        state = json.loads(path.read_text())
        if (state["campaign_id"] != binding["campaign_id"]
                or state["campaign_identity"] != binding["campaign_identity"]):
            raise ValueError("active campaign binding mismatch")
        import hashlib
        identity = hashlib.sha256(json.dumps(state["campaign"], sort_keys=True,
                                 ensure_ascii=False).encode()).hexdigest()
        if identity != state["campaign_identity"]:
            raise ValueError("campaign identity changed")
        counts = {}
        pending = []
        for task_id, task in state["tasks"].items():
            counts[task["state"]] = counts.get(task["state"], 0) + 1
            if task["state"] in {"planned", "running"}:
                packet = state["packets"].get(task.get("packet_id"), {})
                pending.append({"task_id": task_id, "state": task["state"],
                    "packet_id": task.get("packet_id"), "agent_id": packet.get("agent_id"),
                    "observed_runtime": packet.get("observed_runtime", "UNKNOWN")})
        for packet in state.get("adaptive", {}).get("packets", {}).values():
            if packet["state"] in {"planned", "running"}:
                pending.append({key: packet.get(key) for key in
                                ("task_id", "state", "packet_id", "agent_id", "observed_runtime")})
        details = {"state_path": str(path), "campaign_id": state["campaign_id"],
                   "campaign_identity": state["campaign_identity"], "task_counts": counts,
                   "pending_count": len(pending), "pending": pending[:4]}
        return (" Read-only active campaign snapshot: " + json.dumps(details, ensure_ascii=False) +
                " Reconcile every planned packet against actual native host launch receipts before any dispatch; "
                "a running or acknowledged UNKNOWN outcome must be awaited/reconciled, never replayed. "
                "Then record actual results, independently review candidates and request next through "
                "docs/harness/CONTINUOUS_RESEARCH_CONTROLLER.md. Empty fixed READY is not research exhaustion. "
                "This startup hint neither dispatches nor grants scientific acceptance or live activation.")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return " Active-controller pointer unavailable or invalid: " + type(exc).__name__ + "; reconcile its exact state binding before continuing."


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    text = (f"HTT project: {root}\n"
            "Read AGENTS.md and docs/harness/CURRENT_CODEX_RUNTIME.md. "
            "Current owner-directed mode is native subagent execution with explicit supported model and effort, "
            "fresh bounded contexts, disjoint writer ownership, and a separate independent read-only reviewer. "
            "Record requested and observed runtime separately; unobserved settings remain UNKNOWN. "
            "Removed CUH-G descriptor, hooks and registration are not prerequisites for new native tasks; "
            "do not recreate them or treat historical routing text as active instructions. "
            "Actual system/developer and managed restrictions still apply; identify their source rather than bypass them. "
            "Default to this repo root; preserve dirty/untracked candidates, frozen contracts, raw failures, "
            "historical adjudications, task identities and cumulative usage. No new clone/worktree, reset, clean or automatic stash. "
            "Read the selected task's live RETURN and source identities before acting; "
            "reuse unchanged components and validate affected changes only. "
            "New strength-based proof division does not pass historical four-axis validators. Scientific admission remains HOLD.")
    text += active_controller_context(root)
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}))

if __name__ == "__main__":
    main()
