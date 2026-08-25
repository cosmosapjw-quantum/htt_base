from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts/validate_pr321_reaudit_plan.py"


def _validator():
    name = "pr321_reaudit_plan_validator"
    spec = importlib.util.spec_from_file_location(name, VALIDATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

def test_pr321_reaudit_package_is_machine_valid() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/validate_pr321_reaudit_plan.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload == {
        "canonical_DAG_changed": False,
        "contract_failure_classes": {"P0": 2, "P1": 8},
        "generated_result_terminal": (
            "READY_FOR_PREREGISTERED_FIDUCIAL_WINDOW_CONVOLVED_REFERENCE"
        ),
        "guards_present": 10,
        "schema": "htt.pr321.reaudit.plan_validation.v2",
        "science_repair_executed": True,
        "status": "PASS",
    }

def test_pr321_reaudit_handoff_preserves_mes_boundary() -> None:
    text = (
        ROOT / "docs/codex_handoff/pr321_reaudit/CODEX_HANDOFF.md"
    ).read_text(encoding="utf-8")
    assert "SCALAR_TOMOGRAPHIC_CONTROL_ONLY" in text
    assert "NONE_COMPRESSED_ROTATION_INVARIANT_POWER_SPECTRA" in text
    assert "PROJECTED_OUT_IN_TOMOGRAPHIC_CL_EE" not in text
    assert "FORBIDDEN_NO_DIRECTION_INDEXED_FIELD" in text
    assert "NOT_APPLICABLE_NO_DIRECTIONAL_RESPONSE" in text
    assert "BLOCKED_CROSS_CHANNEL_NO_PHYSICAL_TRANSFER" in text
    assert "fiducial_vector_length: 60" in text
    assert "claim_unexecuted_rerun: forbidden" in text


def test_pr321_reaudit_validator_rejects_comment_only_detectors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _validator()
    catalog = json.loads(
        (module.PKG / "P0_P1_THREAT_CATALOG.json").read_text(encoding="utf-8")
    )
    detector_source = tmp_path / "comment_only_detectors.py"
    detector_source.write_text(
        "\n".join(
            f"# def {row['detector']}("
            for row in catalog["findings"]
            if row["detector"].startswith("test_")
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "INTEGRATION_TEST", detector_source)

    with pytest.raises(SystemExit, match="missing controlling PR-321 test"):
        module.main()


def test_pr321_reaudit_validator_binds_catalog_v2_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _validator()
    catalog_path = module.PKG / "P0_P1_THREAT_CATALOG.json"
    baseline = json.loads(catalog_path.read_text(encoding="utf-8"))
    original_read_text = Path.read_text
    replacement = {"text": ""}

    def patched_read_text(path: Path, *args, **kwargs) -> str:
        if path == catalog_path:
            return replacement["text"]
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", patched_read_text)

    for mutation in ("schema", "id", "name", "stop"):
        payload = json.loads(json.dumps(baseline))
        if mutation == "schema":
            payload["schema"] = "htt.pr321.reaudit.threat_catalog.v1"
        else:
            payload["findings"][0][mutation] = f"DRIFTED_{mutation.upper()}"
        replacement["text"] = json.dumps(payload)
        with pytest.raises(SystemExit, match="threat catalogue"):
            module.main()
