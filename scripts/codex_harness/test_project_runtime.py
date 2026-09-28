from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]


def module():
    spec = importlib.util.spec_from_file_location("project_runtime", ROOT / "scripts/codex_harness/project_runtime.py")
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def fixture(tmp_path):
    root = tmp_path / "repo"
    (root / ".codex").mkdir(parents=True)
    (root / ".codex/hooks.json").write_text(json.dumps({"hooks": {"SessionStart": [], "SubagentStart": [], "SubagentStop": []}}))
    (root / ".codex/config.toml").write_text("[agents]\nmax_threads=4\nmax_depth=1\n")
    (root / "AGENTS.md").write_text("core\nfragment\n")
    (root / "AGENTS.md.fragment").write_text("fragment\n")
    for relative in ("docs/harness/CURRENT_CODEX_RUNTIME.md",
                     "docs/harness/LEGACY_SHARED_CONTEXT_V1.md",
                     "scripts/install_codex_handoff.sh"):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture asset\n")
    return root


def test_activation_preserves_frozen_active_run_and_user_file(tmp_path):
    m = module(); root = fixture(tmp_path)
    active = root / ".agent-harness/runtime/ACTIVE_RUN"
    active.parent.mkdir(parents=True); active.write_text("R9\n")
    result = m.activate(root, tmp_path / "missing-codex-home")
    assert active.read_text() == "R9\n"
    assert result["global_authority"]["status"] == "UNAVAILABLE"
    assert result["client_hook_trust"] == "NOT_OBSERVED"
    assert result["scientific_admission"] is False
    assert json.loads((active.parent / "current-runtime.json").read_text())["active_run_preserved"] == "R9"


def test_duplicate_lifecycle_and_fragment_drift_fail_before_activation(tmp_path):
    m = module(); root = fixture(tmp_path)
    (root / ".codex/hooks.json").write_text(json.dumps({"hooks": {"SubagentStart": [{"hooks": [{"command": "legacy"}]}]}}))
    (root / "AGENTS.md.fragment").write_text("different")
    result = m.inspect(root, tmp_path)
    assert result["status"] == "FAIL"
    assert any("SubagentStart" in e for e in result["errors"])
    assert any("fragment" in e for e in result["errors"])
    assert not (root / ".agent-harness/runtime/current-runtime.json").exists()


def test_missing_runtime_instructions_cannot_be_activated(tmp_path):
    m = module(); root = fixture(tmp_path)
    (root / "docs/harness/CURRENT_CODEX_RUNTIME.md").unlink()
    assert m.activate(root, tmp_path)["status"] == "FAIL"
    assert not (root / ".agent-harness/runtime/current-runtime.json").exists()


def test_session_hook_is_advisory_without_global_service():
    p = subprocess.run([sys.executable, "-B", str(ROOT / ".codex/hooks/session_start_context.py")], capture_output=True, text=True, check=True)
    result = json.loads(p.stdout)
    assert "decision" not in result and "stopReason" not in result
    assert len(result["hookSpecificOutput"]["additionalContext"]) < 2000
    assert "duplicate project lifecycle" in p.stdout


def test_versioned_profiles_pin_current_model_and_forbid_nested_spawn():
    import tomllib
    paths = subprocess.check_output(["git", "ls-files", ".codex/agents"], cwd=ROOT, text=True).splitlines()
    for rel in paths:
        data = tomllib.loads((ROOT / rel).read_text())
        assert data["model"] in {"gpt-6-sol", "gpt-6-luna"}, rel
        assert data["model_reasoning_effort"] in {"low", "medium", "high", "xhigh"}
