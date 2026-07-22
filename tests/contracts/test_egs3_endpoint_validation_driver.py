"""Contract tests for the independent EGS3 endpoint-integrity validator."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts/validate_egs3_endpoint_integrity.py"
MODULE = REPO_ROOT / "htt/obsstat/egs3_identified_set.py"


def _load_driver():
    spec = importlib.util.spec_from_file_location(
        "validate_egs3_endpoint_integrity", SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def test_default_driver_is_read_only_and_passes_full_frozen_sweeps(
    tmp_path: Path,
) -> None:
    before = tuple(tmp_path.iterdir())
    completed = subprocess.run(
        [sys.executable, "-B", str(SCRIPT)],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert tuple(tmp_path.iterdir()) == before

    payload = json.loads(completed.stdout)
    assert payload["schema"] == "htt.egs3.endpoint_integrity_validation.v1"
    assert payload["status"] == "PASS"
    assert "diagnostic numerical-method validation only" in payload["claim_scope"]
    assert payload["input_hashes"] == {
        "htt/obsstat/egs3_identified_set.py": _sha256(MODULE),
        "scripts/validate_egs3_endpoint_integrity.py": _sha256(SCRIPT),
    }

    oracle = payload["oracle"]
    assert oracle["seed"] == 20260722
    assert oracle["cases"] == 300
    assert oracle["box_active_cases"] >= 150
    assert oracle["max_abs_endpoint_error"] <= oracle["tolerance"] == 2.0e-10
    assert oracle["failures"] == []

    sweep = payload["reparameterization"]
    assert sweep["seed"] == 20260723
    assert sweep["cases"] == 500
    assert sweep["population_cases"] > 0
    assert sweep["positive_radius_cases"] > 0
    assert sweep["min_column_scale"] == 1.0e-12
    assert sweep["max_column_scale"] == 1.0e12
    assert sweep["max_abs_endpoint_difference"] <= sweep["tolerance"] == 2.0e-10
    assert sweep["failures"] == []

    translation = payload["translation"]
    assert translation["seed"] == 20260724
    assert translation["cases"] == 200
    assert translation["min_translation_magnitude"] >= 1.0e5
    assert translation["max_translation_magnitude"] <= 1.0e9
    assert translation["min_strict_feasibility_margin"] > 0.0
    assert (
        translation["max_abs_endpoint_error"]
        <= translation["tolerance"]
        == 2.0e-10
    )
    assert translation["failures"] == []

    translated_geometry = payload["translated_geometry"]
    assert translated_geometry["seed"] == 20260725
    assert translated_geometry["cases"] == 200
    assert translated_geometry["box_active_cases"] >= 100
    assert translated_geometry["min_translation_magnitude"] >= 2.0 ** 17
    assert translated_geometry["max_translation_magnitude"] <= 2.0 ** 30
    assert (
        translated_geometry["max_abs_endpoint_error"]
        <= translated_geometry["tolerance"]
        == 2.0e-6
    )
    assert translated_geometry["failures"] == []


def test_oracle_is_independent_of_production_endpoint_helpers() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    forbidden_shared_helpers = (
        "_constrained_" + "extreme",
        "reachable_endpoints_" + "closed_form",
    )
    assert all(name not in source for name in forbidden_shared_helpers)
    assert "np.linalg.eigh" in source
    assert "math.acos" in source
    assert "Fraction.from_float" in source


def test_oracle_rejects_a_shifted_production_endpoint(monkeypatch) -> None:
    driver = _load_driver()
    real_report = driver.identified_set_report

    def shifted_report(*args, **kwargs):
        report = real_report(*args, **kwargs)
        return replace(
            report,
            reachable_lo=report.reachable_lo + 1.0e-6,
            x_lo=report.x_lo + 1.0e-6,
        )

    monkeypatch.setattr(driver, "identified_set_report", shifted_report)
    result = driver.run_rank_two_oracle(cases=1, seed=driver.ORACLE_SEED)
    assert result["passed"] is False
    assert result["failures"][0]["kind"] == "endpoint_mismatch"
    assert result["failures"][0]["error"] > result["tolerance"]


def test_reparameterization_rejects_a_stressed_call_only_shift(
    monkeypatch,
) -> None:
    driver = _load_driver()
    real_report = driver.identified_set_report
    call_count = 0

    def shifted_stressed_report(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        report = real_report(*args, **kwargs)
        if call_count % 2 == 0:
            return replace(
                report,
                reachable_hi=report.reachable_hi + 1.0e-6,
                x_hi=report.x_hi + 1.0e-6,
            )
        return report

    monkeypatch.setattr(driver, "identified_set_report", shifted_stressed_report)
    result = driver.run_reparameterization_sweep(
        cases=1,
        seed=driver.REPARAMETERIZATION_SEED,
    )
    assert call_count == 2
    assert result["passed"] is False
    assert result["failures"][0]["kind"] == "reparameterization_mismatch"
    assert result["failures"][0]["error"] > result["tolerance"]


def test_translation_sweep_rejects_a_shifted_production_endpoint(
    monkeypatch,
) -> None:
    driver = _load_driver()
    real_report = driver.identified_set_report

    def shifted_report(*args, **kwargs):
        report = real_report(*args, **kwargs)
        return replace(
            report,
            reachable_hi=report.reachable_hi + 1.0e-4,
            x_hi=report.x_hi + 1.0e-4,
        )

    monkeypatch.setattr(driver, "identified_set_report", shifted_report)
    result = driver.run_translation_sweep(
        cases=1,
        seed=driver.TRANSLATION_SEED,
    )
    assert result["passed"] is False
    assert result["failures"][0]["kind"] == "translation_mismatch"
    assert result["failures"][0]["error"] > result["tolerance"]


def test_translated_geometry_rejects_a_shifted_production_endpoint(
    monkeypatch,
) -> None:
    driver = _load_driver()
    real_report = driver.identified_set_report

    def shifted_report(*args, **kwargs):
        report = real_report(*args, **kwargs)
        return replace(
            report,
            reachable_lo=report.reachable_lo + 1.0e-4,
            x_lo=report.x_lo + 1.0e-4,
        )

    monkeypatch.setattr(driver, "identified_set_report", shifted_report)
    result = driver.run_translated_geometry_sweep(
        cases=1,
        seed=driver.TRANSLATED_GEOMETRY_SEED,
    )
    assert result["passed"] is False
    assert result["failures"][0]["kind"] == "translated_geometry_mismatch"
    assert result["failures"][0]["error"] > result["failures"][0]["tolerance"]
