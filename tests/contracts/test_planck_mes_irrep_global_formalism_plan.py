from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "scripts/validate_planck_mes_irrep_global_formalism_plan.py"
SPEC = importlib.util.spec_from_file_location(
    "planck_mes_irrep_plan_validator", VALIDATOR_PATH
)
assert SPEC is not None and SPEC.loader is not None
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def _copy_minimal_root(tmp_path: Path) -> Path:
    target = tmp_path / "repo"
    package_src = ROOT / validator.PACKAGE_REL
    package_dst = target / validator.PACKAGE_REL
    package_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(package_src, package_dst)

    for rel in (
        validator.ACTIVE_POINTER_REL,
        validator.WORKFLOW_REL,
        validator.ARCHITECTURE_COMPAT_REL,
        Path("scripts/validate_planck_mes_irrep_global_formalism_plan.py"),
        Path("tests/contracts/test_planck_mes_irrep_global_formalism_plan.py"),
    ):
        destination = target / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, destination)
    return target


def test_active_package_validates_without_git() -> None:
    result = validator.validate_package(ROOT, check_git=False)
    assert result["status"] == "PASS"
    assert result["active_work_units"] == validator.EXPECTED_WUS
    assert result["first_objective_execution"] == "PMG-WU-003"
    assert result["threat_count"] == 25
    assert result["P0"] == 11
    assert result["P1"] == 14
    assert result["migration_paths"] == len(validator.REQUIRED_MIGRATION_PATHS)


def test_architecture_compatibility_contract_is_required_and_allowed() -> None:
    assert str(validator.ARCHITECTURE_COMPAT_REL) in validator.PLAN_ONLY_ALLOWED
    assert (ROOT / validator.ARCHITECTURE_COMPAT_REL).is_file()
    assert (ROOT / "scripts/architecture/test_import_boundaries.py").is_file()


def test_active_pointer_mutation_is_rejected(tmp_path: Path) -> None:
    root = _copy_minimal_root(tmp_path)
    path = root / validator.ACTIVE_POINTER_REL
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["first_objective_execution"] = "PMG-WU-007"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    with pytest.raises(validator.PlanValidationError, match="objective transition"):
        validator.validate_package(root, check_git=False)


def test_exact_mes_identity_mutation_is_rejected(tmp_path: Path) -> None:
    root = _copy_minimal_root(tmp_path)
    path = root / validator.PACKAGE_REL / "FORMALISM_CONTRACT.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["mes_coordinate_identities"]["exact_identities"][0] = (
        "W2_max = C_2/(15*pi*T0^2)"
    )
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    with pytest.raises(validator.PlanValidationError, match="identities"):
        validator.validate_package(root, check_git=False)


def test_information_gain_promotion_is_rejected(tmp_path: Path) -> None:
    root = _copy_minimal_root(tmp_path)
    path = root / validator.PACKAGE_REL / "FORMALISM_CONTRACT.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["mes_coordinate_identities"]["independent_information_gain"] = True
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    with pytest.raises(validator.PlanValidationError, match="information-gain"):
        validator.validate_package(root, check_git=False)


def test_threat_without_detector_is_rejected(tmp_path: Path) -> None:
    root = _copy_minimal_root(tmp_path)
    path = root / validator.PACKAGE_REL / "P0_P1_THREAT_CATALOG.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["failure_modes"][0]["detection"]["executable"] = ""
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(validator.PlanValidationError, match="detector"):
        validator.validate_package(root, check_git=False)


def test_invariant_coverage_loss_is_rejected(tmp_path: Path) -> None:
    root = _copy_minimal_root(tmp_path)
    path = root / validator.PACKAGE_REL / "INVARIANT_TEST_MATRIX.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["rows"].pop()
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    with pytest.raises(validator.PlanValidationError, match="cover"):
        validator.validate_package(root, check_git=False)


def test_work_unit_without_positive_transition_is_rejected(tmp_path: Path) -> None:
    root = _copy_minimal_root(tmp_path)
    path = root / validator.PACKAGE_REL / "AUDIT_COMPILED_EXEC_PLAN.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["work_units"][2]["transition"]["pass_next_executable_action"] = ""
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    with pytest.raises(validator.PlanValidationError, match="transition"):
        validator.validate_package(root, check_git=False)


def test_migration_bypass_is_rejected(tmp_path: Path) -> None:
    root = _copy_minimal_root(tmp_path)
    path = root / validator.PACKAGE_REL / "FORMALISM_MIGRATION_MATRIX.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["rows"] = payload["rows"][1:]
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    with pytest.raises(validator.PlanValidationError, match="migration path coverage"):
        validator.validate_package(root, check_git=False)


def test_superseded_work_unit_reactivation_is_rejected(tmp_path: Path) -> None:
    root = _copy_minimal_root(tmp_path)
    path = root / validator.PACKAGE_REL / "PRIOR_PLAN_SUPERSESSION.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["execution_lock"]["forbidden_active_ids"].remove("PED-WU-002")
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    with pytest.raises(validator.PlanValidationError, match="Superseded|superseded|lock"):
        validator.validate_package(root, check_git=False)


def test_process_starvation_brake_mutation_is_rejected(tmp_path: Path) -> None:
    root = _copy_minimal_root(tmp_path)
    path = root / validator.PACKAGE_REL / "PROCESS_COST_ASSESSMENT.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["process_starvation_brake"]["trigger"] = "optional"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    with pytest.raises(validator.PlanValidationError, match="starvation"):
        validator.validate_package(root, check_git=False)


def test_workflow_must_consume_the_package(tmp_path: Path) -> None:
    root = _copy_minimal_root(tmp_path)
    path = root / validator.WORKFLOW_REL
    text = path.read_text(encoding="utf-8").replace(
        "Run Planck MES irrep/global-formalism planning contracts",
        "Removed contract",
    )
    path.write_text(text, encoding="utf-8")
    with pytest.raises(validator.PlanValidationError, match="workflow"):
        validator.validate_package(root, check_git=False)


def test_tail_registry_mutation_is_rejected(tmp_path: Path) -> None:
    root = _copy_minimal_root(tmp_path)
    path = root / validator.PACKAGE_REL / "FORMALISM_CONTRACT.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["tail_registries"][1]["coordinates"]["multipole_plane_alignment_max_l2_l3"] = (
        "two-sided"
    )
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    with pytest.raises(validator.PlanValidationError, match="tail registry"):
        validator.validate_package(root, check_git=False)
