from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts/codex_harness/run_authorized_observational_program.py"


def _module():
    module_spec = importlib.util.spec_from_file_location("authorized_observational_program", RUNNER)
    assert module_spec is not None and module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)
    return module


def test_one_command_program_covers_the_canonical_runbooks_without_execution(monkeypatch) -> None:
    module = _module()
    lanes = module.build_program()
    assert [lane.lane for lane in lanes] == [
        "PLANCK", "CF4", "HSC_KIDS", "ACT", "DESI", "JWST_SN", "CROSS_PROBE",
    ]
    assert all(lane.status == "BLOCKED" for lane in lanes)
    assert any("pr151_formalism_revalidation_required" in lane.blocked_reasons for lane in lanes)
    called = False

    def forbidden_run(*_args, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("blocked program must not invoke an analysis entrypoint")

    monkeypatch.setattr(module.subprocess, "run", forbidden_run)
    assert module.execute_authorized(lanes) == 3
    assert called is False
    report = module.payload(lanes)
    assert report["observed_data_executed"] is False
    assert "--execute-authorized" in report["one_command"]
    command, environment = module._command_and_environment(("PYTHONPATH=htt/src:htt", "python", "-m", "pytest"))
    assert command == ("python", "-m", "pytest")
    assert environment["PYTHONPATH"] == "htt/src:htt"


def test_dispatcher_honors_success_and_terminal_dependency_contracts() -> None:
    module = _module()
    backlog = module._mapping(module.BACKLOG)
    cards = module._cards(backlog)

    planck = cards["PR-290"]
    required_success = planck["depends"][0]
    assert module._dependency_reasons(
        planck,
        {required_success: {"resolution": "COMPLETED_FAILED_WITH_RECEIPT"}},
    ) == (f"upstream_success_not_satisfied:{required_success}",) + tuple(
        f"upstream_success_not_satisfied:{dependency}"
        for dependency in planck["depends"][1:]
    )

    cross_probe = cards["PR-294"]
    terminal_resolutions = {
        dependency: {"resolution": "BLOCKED_WITH_RECEIPT"}
        for dependency in cross_probe["depends"]
    }
    assert module._dependency_reasons(cross_probe, terminal_resolutions) == ()

    assert module._dependency_reasons(
        {"id": "PR-X", "depends": ["PR-Y"]},
        {"PR-Y": {"resolution": "COMPLETED_SUCCESS"}},
    ) == ("upstream_dependency_contract_missing:PR-Y",)
