from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil

import pytest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts/validate_planck_mes_pmg_wu002_transition.py"
SPEC = importlib.util.spec_from_file_location("pmg_wu002_transition_validator", VALIDATOR)
assert SPEC is not None and SPEC.loader is not None
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


@pytest.fixture()
def package_copy(tmp_path: Path) -> Path:
    source = ROOT / validator.PACKAGE_REL
    target = tmp_path / "package"
    shutil.copytree(source, target)
    return target


def test_current_transition_package_passes() -> None:
    result = validator.validate_package(ROOT, check_git=False)
    assert result["status"] == "PASS"
    assert result["active_work_unit"] == "PMG-WU-002"
    assert result["failure_modes"] == 8
    assert result["P0"] == 4
    assert result["P1"] == 4
    assert result["science_executed"] is False


def test_missing_package_file_fails(package_copy: Path) -> None:
    (package_copy / "GUIDE_BINDING.yaml").unlink()
    with pytest.raises(
        validator.TransitionValidationError, match="package file set drifted"
    ):
        validator.validate_package(ROOT, package=package_copy, check_git=False)


def test_changed_paths_reject_process_only_candidate() -> None:
    with pytest.raises(
        validator.TransitionValidationError,
        match="undeclared paths|no production",
    ):
        validator.validate_changed_paths(
            [
                "docs/codex_handoff/another_plan/CODEX_HANDOFF.md",
                "tests/contracts/test_mes_premise_normalization.py",
            ]
        )


def test_changed_paths_require_objective_outputs() -> None:
    with pytest.raises(
        validator.TransitionValidationError,
        match="required objective outputs",
    ):
        validator.validate_changed_paths(
            [
                "htt/src/common/mes_premise_normalization.py",
                "tests/contracts/test_mes_premise_normalization.py",
            ]
        )


def test_valid_wu002_changed_paths_pass() -> None:
    result = validator.validate_changed_paths(
        [
            "htt/src/common/mes_premise_normalization.py",
            "htt/src/common/response_bound_observable_state.py",
            "tests/contracts/test_mes_premise_normalization.py",
            "tests/contracts/test_response_bound_observable_state.py",
            "docs/generated/planck_mes_irrep_formalism/wu002_terminal.json",
            "docs/generated/planck_mes_irrep_formalism/migration_status.json",
        ]
    )
    assert result["status"] == "PASS"
    assert result["work_unit"] == "PMG-WU-002"
