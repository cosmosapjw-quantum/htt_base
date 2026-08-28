from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts/validate_planck_mes_pmg_wu005_evidence_recovery.py"
SPEC = importlib.util.spec_from_file_location("pmg_wu005_recovery_validator", VALIDATOR)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def copy_package(tmp_path: Path) -> Path:
    source = ROOT / module.PKG_REL
    target = tmp_path / "package"
    shutil.copytree(source, target)
    return target


def test_recovery_package_passes() -> None:
    result = module.validate(check_git=False)
    assert result["status"] == "PASS"
    assert result["failure_modes"] == 9
    assert result["raw_map_rerun_required"] is False
    assert result["PMG_WU006_authorized"] is False


def test_package_rejects_raw_map_rerun_authorization(tmp_path: Path, monkeypatch) -> None:
    package = copy_package(tmp_path)
    index = package / "PACKAGE_INDEX.yaml"
    payload = yaml.safe_load(index.read_text())
    payload["raw_map_rerun_required"] = True
    index.write_text(yaml.safe_dump(payload, sort_keys=False))
    monkeypatch.setattr(module, "PKG", package)
    with pytest.raises(module.ValidationError, match="transition semantics"):
        module.validate(check_git=False)


def test_threat_matrix_cannot_drop_a_failure_mode(tmp_path: Path, monkeypatch) -> None:
    package = copy_package(tmp_path)
    matrix = package / "INVARIANT_TEST_MATRIX.yaml"
    payload = yaml.safe_load(matrix.read_text())
    payload["rows"] = payload["rows"][:-1]
    matrix.write_text(yaml.safe_dump(payload, sort_keys=False))
    monkeypatch.setattr(module, "PKG", package)
    with pytest.raises(module.ValidationError, match="matrix coverage"):
        module.validate(check_git=False)


def test_cleanup_firewall_is_mandatory(tmp_path: Path, monkeypatch) -> None:
    package = copy_package(tmp_path)
    path = package / "LOCAL_CHECKPOINT_AND_CLEANUP.yaml"
    payload = yaml.safe_load(path.read_text())
    payload["legacy_cleanup_firewall"]["policy"] = "RESTORE_FROM_REPAIR_BRANCH"
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    monkeypatch.setattr(module, "PKG", package)
    with pytest.raises(module.ValidationError, match="cleanup"):
        module.validate(check_git=False)
