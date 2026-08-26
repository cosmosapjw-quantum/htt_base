from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import shutil

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts/validate_planck_mes_extended_data_plan.py"
SPEC = importlib.util.spec_from_file_location(
    "validate_planck_mes_extended_data_plan", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


@pytest.fixture()
def package_copy(tmp_path: Path) -> Path:
    source = ROOT / "docs/codex_handoff/planck_mes_extended_data_execution"
    target = tmp_path / "package"
    shutil.copytree(source, target)
    return target


def _load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _write_yaml(path: Path, payload) -> None:
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, width=1000),
        encoding="utf-8",
    )


def test_current_package_passes() -> None:
    payload = validator.validate_package(ROOT, check_git=False)
    assert payload["status"] == "PASS"
    assert payload["work_units"] == [
        "PED-WU-001",
        "PED-WU-002",
        "PED-WU-003",
        "PED-WU-004",
    ]
    assert payload["bundle_count"] == 14
    assert payload["route_count"] == 13


def test_missing_smica_cmbonly_route_fails(package_copy: Path) -> None:
    path = package_copy / "DATA_ROUTE_MATRIX.yaml"
    payload = _load_yaml(path)
    payload["routes"] = [
        row for row in payload["routes"]
        if row["id"] != "planck_smica_cmbonly_999"
    ]
    _write_yaml(path, payload)
    with pytest.raises(
        validator.PlanValidationError, match="route coverage drifted"
    ):
        validator.validate_package(ROOT, package=package_copy, check_git=False)


def test_unmapped_p0_p1_fails(package_copy: Path) -> None:
    path = package_copy / "INVARIANT_TEST_MATRIX.yaml"
    payload = _load_yaml(path)
    payload["rows"] = payload["rows"][:-1]
    _write_yaml(path, payload)
    with pytest.raises(
        validator.PlanValidationError, match="matrix coverage drift"
    ):
        validator.validate_package(ROOT, package=package_copy, check_git=False)


def test_missing_pass_transition_fails(package_copy: Path) -> None:
    path = package_copy / "AUDIT_COMPILED_EXEC_PLAN.yaml"
    payload = _load_yaml(path)
    payload["work_units"][0]["transition"]["pass_next_executable_action"] = ""
    _write_yaml(path, payload)
    with pytest.raises(
        validator.PlanValidationError,
        match="lacks pass_next_executable_action",
    ):
        validator.validate_package(ROOT, package=package_copy, check_git=False)


def test_false_npipe_availability_fails(package_copy: Path) -> None:
    path = package_copy / "DATA_AVAILABILITY_SNAPSHOT.yaml"
    payload = _load_yaml(path)
    payload["planck_detail"]["npipe_pr4"]["file_count"] = 1
    payload["planck_detail"]["npipe_pr4"]["status"] = "AVAILABLE"
    _write_yaml(path, payload)
    with pytest.raises(
        validator.PlanValidationError,
        match="Planck inventory contract drifted",
    ):
        validator.validate_package(ROOT, package=package_copy, check_git=False)


def test_implementation_diff_rejects_successor_planning_package() -> None:
    with pytest.raises(
        validator.PlanValidationError,
        match="planning package",
    ):
        validator.validate_implementation_diff(
            [
                "docs/codex_handoff/planck_mes_extended_data_execution_v2/"
                "ANOTHER_PLAN.yaml"
            ]
        )


def test_implementation_diff_requires_objective_path() -> None:
    with pytest.raises(
        validator.PlanValidationError,
        match="no objective or enabling implementation path",
    ):
        validator.validate_implementation_diff(["docs/notes/process.md"])


def test_implementation_diff_accepts_real_worker_and_test() -> None:
    payload = validator.validate_implementation_diff(
        [
            "scripts/observed_runs/inspect_planck_mes_extended_data.py",
            "tests/integration/test_planck_mes_extended_data_inventory.py",
            "docs/generated/planck_mes_extended_data/intake_summary.json",
        ]
    )
    assert payload["status"] == "PASS_IMPLEMENTATION_DIFF"
