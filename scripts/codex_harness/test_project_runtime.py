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


def test_session_hook_is_advisory_without_global_service(tmp_path):
    import os
    p = subprocess.run([sys.executable, "-B", str(ROOT / ".codex/hooks/session_start_context.py")], capture_output=True, text=True, check=True,
                       env={**os.environ, "CODEX_HOME": str(tmp_path / "unavailable")})
    result = json.loads(p.stdout)
    assert "decision" not in result and "stopReason" not in result
    assert len(result["hookSpecificOutput"]["additionalContext"]) < 2000
    context = result["hookSpecificOutput"]["additionalContext"]
    assert "native subagent execution with explicit supported model and effort" in context
    assert "separate independent read-only reviewer" in context
    assert "unobserved settings remain UNKNOWN" in context
    assert "not prerequisites for new native tasks" in context
    assert "Actual system/developer and managed restrictions still apply" in context
    assert "selected task's live RETURN" in context
    assert "conditional_synthesis_v1_20261008" not in context
    assert "CAS15 Frobenius" not in context
    assert "Scientific admission remains HOLD" in context
    assert "Use the current global CUH-G descriptor" not in context
    assert "Reuse the registered launch" not in context
    assert "cuhg.models.local_assistance run" not in context
    assert not (tmp_path / "unavailable").exists()


def test_session_hook_does_not_restore_or_use_removed_registration(tmp_path):
    import os
    home = tmp_path / "client"
    result = subprocess.run([sys.executable, "-B", str(ROOT / ".codex/hooks/session_start_context.py")],
                            env={**os.environ, "CODEX_HOME": str(home)}, capture_output=True, text=True, check=True)
    output = json.loads(result.stdout)
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "decision" not in output and "stopReason" not in output
    assert "do not recreate them" in context
    assert "historical routing text" in context
    assert "PYTHONPATH=" not in context
    assert not home.exists()


def _assert_native_spawn_limits(agents):
    assert type(agents["max_threads"]) is int and agents["max_threads"] == 4
    assert type(agents["max_depth"]) is int and agents["max_depth"] == 1


def _assert_agent_asset_shape(data):
    # Versioned assets include historical pins and model-free domain guidance.
    # Supported model/effort must be selected at native dispatch; a TOML pin
    # does not prove that its historical model is available in this runtime.
    if "model" in data:
        model = data["model"]
        assert isinstance(model, str) and model and not any(c.isspace() for c in model)
    assert data["model_reasoning_effort"] in {"low", "medium", "high", "xhigh"}
    if "agents" in data:
        # A role may further disable children, never explicitly enable them.
        assert data["agents"].get("enabled") is False
        for key, lower, upper in (("max_depth", 0, 1), ("max_threads", 1, 4)):
            if key in data["agents"]:
                value = data["agents"][key]
                assert type(value) is int and lower <= value <= upper


def test_versioned_agent_assets_preserve_native_spawn_contract():
    import tomllib
    config = tomllib.loads((ROOT / ".codex/config.toml").read_text())
    _assert_native_spawn_limits(config["agents"])
    paths = subprocess.check_output(
        ["git", "ls-files", ".codex/agents/*.toml"], cwd=ROOT, text=True
    ).splitlines()
    assert paths, "No versioned agent assets found"
    for rel in paths:
        data = tomllib.loads((ROOT / rel).read_text())
        try:
            _assert_agent_asset_shape(data)
        except (AssertionError, KeyError, TypeError, AttributeError) as exc:
            raise AssertionError(rel) from exc


def test_agent_asset_contract_rejects_invalid_overrides_and_nested_spawn():
    import pytest
    base = {"model_reasoning_effort": "high"}
    _assert_agent_asset_shape(base)
    _assert_agent_asset_shape({**base, "model": "gpt-6-astra", "agents": {"enabled": False}})
    _assert_agent_asset_shape({**base, "agents": {"enabled": False, "max_depth": 0, "max_threads": 1}})
    for model in ("", " ", " gpt-6-sol", "gpt 6", "gpt\n6", None, 6):
        with pytest.raises(AssertionError):
            _assert_agent_asset_shape({**base, "model": model})
    with pytest.raises(AssertionError):
        _assert_agent_asset_shape({"model_reasoning_effort": "unbounded"})
    for child_config in ({"enabled": True}, {"max_depth": 2},
                         {"enabled": False, "max_depth": 2},
                         {"enabled": False, "max_threads": 5},
                         {"enabled": False, "max_depth": True},
                         {"enabled": False, "max_threads": 4.0},
                         {"enabled": False, "max_depth": -1},
                         {"enabled": False, "max_threads": 0}):
        with pytest.raises(AssertionError):
            _assert_agent_asset_shape({**base, "agents": child_config})
    for limits in ({"max_threads": 5, "max_depth": 1},
                   {"max_threads": 4, "max_depth": 2},
                   {"max_threads": True, "max_depth": 1},
                   {"max_threads": 4, "max_depth": True},
                   {"max_threads": 4.0, "max_depth": 1},
                   {"max_threads": 4, "max_depth": 1.0}):
        with pytest.raises(AssertionError):
            _assert_native_spawn_limits(limits)
