from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/validate_planck_mes_irrep_execution_plan.py"
SPEC = importlib.util.spec_from_file_location(
    "validate_planck_mes_irrep_execution_plan", SCRIPT
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_planck_mes_irrep_execution_package_passes_without_git() -> None:
    result = MODULE.validate_package(check_git=False)
    assert result["status"] == "PASS"
    assert result["work_units"] == [
        "PMI-WU-001",
        "PMI-WU-002",
        "PMI-WU-003",
        "PMI-WU-004",
        "PMI-WU-005",
        "PMI-WU-006",
        "PMI-WU-007",
    ]
    assert result["failure_modes"] == 24
    assert result["P0"] == 14
    assert result["P1"] == 10
    assert result["first_objective_work_unit"] == "PMI-WU-002"
    assert result["large_data_carrier_gate"] == "REQUIRED"


def test_every_p0_p1_has_one_matrix_detector_and_work_unit() -> None:
    package = ROOT / MODULE.PKG_REL
    threats = json.loads(
        (package / "P0_P1_THREAT_CATALOG.json").read_text(encoding="utf-8")
    )["failure_modes"]
    matrix = yaml.safe_load(
        (package / "INVARIANT_TEST_MATRIX.yaml").read_text(encoding="utf-8")
    )["rows"]
    plan = yaml.safe_load(
        (package / "AUDIT_COMPILED_EXEC_PLAN.yaml").read_text(encoding="utf-8")
    )
    threat_ids = {row["id"] for row in threats}
    rows_by_failure = {row["failure_mode"]: row for row in matrix}
    assert set(rows_by_failure) == threat_ids
    work_units = set(plan["ordered_work_units"])
    for threat in threats:
        assert threat["severity"] in {"P0", "P1"}
        assert isinstance(threat["current_task_blocking"], bool)
        assert threat["detection"]["executable"].strip()
        assert threat["prevention"]["mechanism"].strip()
        row = rows_by_failure[threat["id"]]
        assert row["mechanical_detector"].strip()
        assert row["work_unit"] in work_units
        assert row["pass_transition"].strip()


def test_contract_rejects_frozen_formalism_content_drift(tmp_path: Path) -> None:
    source = ROOT / MODULE.PKG_REL
    copied = tmp_path / "package"
    shutil.copytree(source, copied)
    formalism = copied / "FORMALISM_CONTRACT.yaml"
    text = formalism.read_text(encoding="utf-8")
    formalism.write_text(
        text.replace("total_dimension_ell2_to_ell5: 32", "total_dimension_ell2_to_ell5: 31"),
        encoding="utf-8",
    )
    with pytest.raises(MODULE.PlanValidationError, match="frozen package content drifted"):
        MODULE.validate_package(package=copied, check_git=False)


def test_transition_policy_forbids_process_only_success() -> None:
    package = ROOT / MODULE.PKG_REL
    plan = yaml.safe_load(
        (package / "AUDIT_COMPILED_EXEC_PLAN.yaml").read_text(encoding="utf-8")
    )
    policy = plan["global_transition_policy"]
    assert policy["first_objective_output_required_by"] == "PMI-WU-002"
    assert policy["large_data_execution_must_preserve_harmonic_carrier"] is True
    assert policy["process_starvation_trigger"] == "two substantial process-only cycles"
    assert policy["full_repository_suite_default"] is False
    for work_unit in plan["work_units"]:
        assert work_unit["review_gate"]["pass_condition"] == {"P0": 0, "P1": 0}
        assert work_unit["review_gate"]["read_only_first_pass"] is True
        assert work_unit["transition"]["pass_next_executable_action"].strip()
        assert work_unit["transition"]["fail_next_action"].strip()
