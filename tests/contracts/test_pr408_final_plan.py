from __future__ import annotations

import importlib.util
from pathlib import Path
from copy import deepcopy

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/validate_pr408_final_plan.py"


def _module():
    spec = importlib.util.spec_from_file_location("validate_pr408_final_plan", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _valid_unit(module):
    return {
        "schema": "audit-compiled-work-unit/v1",
        "id": "WU-002",
        "title": "fixture",
        "authority": {
            "branch": "ALLOCATE_FROM_LIVE_DAG",
            "upstream_dependencies": ["WU-001"],
        },
        "objective": {"statement": "bounded", "observable_success": "pass"},
        "risk": {"class": "high", "P0_failure_modes": ["FM-0"], "P1_failure_modes": ["FM-1"]},
        "scope": {"allowed_paths": ["docs/**"], "forbidden_paths": [], "forbidden_changes": []},
        "preconditions": [{"id": "PRE", "command": "git status --porcelain", "expect": "empty"}],
        "invariants": [
            {
                "id": "INV-0",
                "severity_if_violated": "P0",
                "statement": "load-bearing",
                "mechanical_check": {"test": "test_p0"},
            }
        ],
        "failure_modes": [
            {"id": "FM-0", "severity": "P0", "trigger": "bad science", "required_detection": {"test": "test_p0"}},
            {"id": "FM-1", "severity": "P1", "trigger": "missing boundary", "required_detection": {"assertion": "typed stop"}},
        ],
        "implementation": {"ordered_steps": [{"id": "STEP", "action": "minimal"}]},
        "verification": {"targeted": ["pytest -q"]},
        "completion_evidence": {"required": ["test_logs", "git_diff_check"]},
        "agent_policy": {
            "ask_user_questions": False,
            "guessing_across_spec_boundary": "forbidden",
            "suppressing_failures": "forbidden",
        },
        "review_gate": {"fresh_context_required": True, "pass_condition": {"P0": 0, "P1": 0}},
    }


def test_final_pr408_package_is_machine_valid() -> None:
    result = _module().validate_package()
    assert result["status"] == "PASS"
    assert result["work_unit_ids"] == [f"WU-{index:03d}" for index in range(1, 8)]


def test_missing_work_unit_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _module()
    copied = tmp_path / "pr408_final"
    copied.mkdir()
    for path in module.PACKAGE_ROOT.glob("*"):
        if path.is_file():
            (copied / path.name).write_bytes(path.read_bytes())
    (copied / "WU-004.yaml").unlink()
    monkeypatch.setattr(module, "PACKAGE_ROOT", copied)
    with pytest.raises(module.PlanValidationError, match="missing"):
        module.validate_package()


def test_p0_without_detector_is_rejected() -> None:
    module = _module()
    payload = _valid_unit(module)
    payload["failure_modes"][0]["required_detection"] = {}
    with pytest.raises(module.PlanValidationError, match="no executable detector"):
        module.validate_work_unit(payload, expected_id="WU-002", previous_id="WU-001")


def test_risk_reference_to_missing_failure_mode_is_rejected() -> None:
    module = _module()
    payload = _valid_unit(module)
    payload["risk"]["P1_failure_modes"] = ["FM-DOES-NOT-EXIST"]
    with pytest.raises(module.PlanValidationError, match="references missing"):
        module.validate_work_unit(payload, expected_id="WU-002", previous_id="WU-001")


def test_nonzero_review_gate_is_rejected() -> None:
    module = _module()
    payload = _valid_unit(module)
    payload["review_gate"]["pass_condition"] = {"P0": 0, "P1": 1}
    with pytest.raises(module.PlanValidationError, match="P0=P1=0"):
        module.validate_work_unit(payload, expected_id="WU-002", previous_id="WU-001")


def test_forbidden_dag_or_science_path_is_rejected() -> None:
    module = _module()
    with pytest.raises(module.PlanValidationError, match="forbidden planning-PR path"):
        module.validate_changed_surface(["docs/codex_handoff/pr_backlog.yaml"])
    with pytest.raises(module.PlanValidationError, match="forbidden planning-PR path"):
        module.validate_changed_surface(["htt/obsstat/new_theory.py"])
