"""Native event routing with two real Git worktrees and identical task names."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".codex/hooks"))
from _common import resolve_hook_context, record_bound_start

spec = importlib.util.spec_from_file_location("r8_binding", ROOT / ".agent-harness/scripts/bind_hook_context.py")
binding_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(binding_module)
stage_binding = binding_module.stage_binding


@pytest.fixture
def trees(tmp_path, monkeypatch):
    base, other = tmp_path / "launcher", tmp_path / "linked"
    base.mkdir()
    def git(*args):
        subprocess.run(["git", "-C", str(base), *args], check=True, capture_output=True)
    git("init")
    git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "--allow-empty", "-m", "fixture")
    git("worktree", "add", "-b", "linked", str(other))
    for root, run in ((base, "run-a"), (other, "run-b")):
        directory = root / ".agent-harness/runs" / run
        directory.joinpath("assignments").mkdir(parents=True)
        context = root / ".agent-harness/context"
        context.mkdir()
        context.joinpath("CONTEXT_INDEX.json").write_text(json.dumps({"context_version": run}))
        directory.joinpath("RUN_PLAN.json").write_text(json.dumps({"context_version": run}))
        directory.joinpath("assignments/same_task.json").write_text(json.dumps({
            "run_id": run, "assignment_id": "same_task", "agent_type": "harness_engineer", "context_version": run}))
    monkeypatch.chdir(base)
    return base, other


def event(base, session, agent):
    return {"session_id": session, "agent_id": agent, "cwd": str(base), "agent_type": "harness_engineer"}


def test_same_task_two_worktrees_keep_start_stop_bindings(trees):
    base, other = trees
    for root, run, session, agent in ((base, "run-a", "parent-a", "child-a"),
                                       (other, "run-b", "parent-b", "child-b")):
        stage_binding(base, root, session, run, "same_task")
        actual, binding = resolve_hook_context(event(base, session, agent), "start")
        assert actual == root and binding["run_id"] == run
        record_bound_start(binding)
        stopped, evidence = resolve_hook_context(event(base, session, agent), "stop")
        assert stopped == root and evidence["context_delivered"]
    assert resolve_hook_context(event(base, "parent-a", "child-a"), "stop")[0] != other


def test_same_session_new_pending_does_not_retarget_old_child(trees):
    base, other = trees
    stage_binding(base, base, "parent", "run-a", "same_task")
    _, first = resolve_hook_context(event(base, "parent", "first"), "start")
    record_bound_start(first)
    stage_binding(base, other, "parent", "run-b", "same_task")
    assert resolve_hook_context(event(base, "parent", "first"), "stop")[0] == base
    _, second = resolve_hook_context(event(base, "parent", "second"), "start")
    record_bound_start(second)
    assert resolve_hook_context(event(base, "parent", "second"), "stop")[0] == other


def test_swapped_stale_missing_or_duplicate_binding_refused(trees):
    base, other = trees
    pending = stage_binding(base, other, "parent", "run-b", "same_task")
    with pytest.raises(FileExistsError):
        stage_binding(base, other, "parent", "run-b", "same_task")
    saved = json.loads(pending.read_text())
    wrong = dict(saved, worktree_root=str(base))
    pending.write_text(json.dumps(wrong))
    with pytest.raises(ValueError):
        resolve_hook_context(event(base, "parent", "child"), "start")
    pending.write_text(json.dumps(saved))
    _, binding = resolve_hook_context(event(base, "parent", "child"), "start")
    record_bound_start(binding)
    with pytest.raises(ValueError):
        resolve_hook_context(event(base, "parent", "child"), "start")
    with pytest.raises(FileNotFoundError):
        resolve_hook_context(event(base, "parent", "unknown"), "stop")
    path = other / ".agent-harness/runs/run-b/assignments/same_task.json"
    path.write_text(path.read_text() + " ")
    with pytest.raises(ValueError, match="assignment changed"):
        resolve_hook_context(event(base, "parent", "child"), "stop")


def test_unbound_legacy_context_preserved(trees):
    base, _ = trees
    assert resolve_hook_context({}, "start") == (base, None)
    assert resolve_hook_context(event(base, "unbound", "child"), "stop") == (base, None)


def test_actual_hooks_emit_rejection_for_stale_git_root(trees, tmp_path):
    base, other = trees
    stage_binding(base, other, "parent", "run-b", "same_task")
    _, binding = resolve_hook_context(event(base, "parent", "child"), "start")
    record_bound_start(binding)
    # A directory remains at the registered root but it is no longer a Git tree.
    other.joinpath(".git").unlink()
    # Reuse the recorded binding as another pending start fixture.
    (base / ".agent-harness/runtime/hook_context/parent/pending.json").write_text(json.dumps(binding))
    for phase, script, child in (("start", "subagent_start_context.py", "new-child"),
                                  ("stop", "subagent_stop_validate.py", "child")):
        out = subprocess.run([sys.executable, str(ROOT / ".codex/hooks" / script)],
                             input=json.dumps(event(base, "parent", child)),
                             text=True, capture_output=True, cwd=base)
        assert out.returncode == 0 and not out.stderr
        payload = json.loads(out.stdout)
        if phase == "stop":
            assert payload["decision"] == "block"
        else:
            assert "CONTEXT CONTRACT VIOLATION" in payload["hookSpecificOutput"]["additionalContext"]
        assert "no longer a valid Git worktree" in out.stdout
