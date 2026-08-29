from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts/validate_planck_mes_pmg_wu007_smica999.py"
SPEC = importlib.util.spec_from_file_location("wu007_validator", VALIDATOR)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def copy_package(tmp_path: Path) -> Path:
    source = ROOT / module.PKG_REL
    target = tmp_path / "package"
    shutil.copytree(source, target)
    return target


def test_package_passes_without_git() -> None:
    result = module.validate_package(check_git=False)
    assert result["status"] == "PASS"
    assert result["work_unit"] == "PMG-WU-007"
    assert result["first_executable_action"] == "RUN_LOCAL_SMICA999_PREFLIGHT"
    assert result["science_executed"] is False
    assert result["github_actions_used"] is False


def test_claim_envelope_forbids_rank_based_promotion(tmp_path: Path) -> None:
    package = copy_package(tmp_path)
    path = package / "EVIDENCE_ADAPTIVE_CLAIM_ENVELOPE.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["rank_based_promotion_forbidden"] = False
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    with pytest.raises(module.ValidationError, match="rank-based"):
        module.validate_package(package=package)


def test_orbit_family_cannot_be_promoted_to_complete(tmp_path: Path) -> None:
    package = copy_package(tmp_path)
    path = package / "EVIDENCE_ADAPTIVE_CLAIM_ENVELOPE.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    for row in payload["axes"]:
        if row["id"] == "orbit_family_completeness":
            row["current_level"] = "COMPLETE"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    with pytest.raises(module.ValidationError, match="orbit-completeness"):
        module.validate_package(package=package)


def test_download_and_actions_gates_are_rejected(tmp_path: Path) -> None:
    package = copy_package(tmp_path)
    path = package / "PACKAGE_INDEX.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["remote_download_required"] = True
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    with pytest.raises(module.ValidationError, match="download"):
        module.validate_package(package=package)

    package = copy_package(tmp_path / "second")
    path = package / "CODEX_HANDOFF_PROMPT.md"
    path.write_text(path.read_text(encoding="utf-8") + "\ngh run rerun 123\n", encoding="utf-8")
    with pytest.raises(module.ValidationError, match="Actions"):
        module.validate_package(package=package)


def test_threat_matrix_must_cover_every_failure_mode(tmp_path: Path) -> None:
    package = copy_package(tmp_path)
    path = package / "INVARIANT_TEST_MATRIX.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["rows"] = payload["rows"][:-1]
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    with pytest.raises(module.ValidationError, match="coverage"):
        module.validate_package(package=package)


def test_pass_transition_is_pmg_wu008_only(tmp_path: Path) -> None:
    package = copy_package(tmp_path)
    path = package / "WU007_EXECUTION_CONTRACT.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["transition"]["pass_next_executable_action"] = "START_PMG-WU-009"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    with pytest.raises(module.ValidationError, match="PASS transition"):
        module.validate_package(package=package)
