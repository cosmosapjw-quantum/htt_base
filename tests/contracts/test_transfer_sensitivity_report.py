from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from common.artifact_manifest import validate_manifest_payload
from common.semantic_guards.no_overclaim import scan_text
from common.transfer_registry import TransferFunctionSpec, TransferValidRange


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "generate_transfer_sensitivity_report.py"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "generate_transfer_sensitivity_report",
        SCRIPT_PATH,
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _report():
    module = _load_module()
    return module, module.build_transfer_sensitivity_report(
        command="python scripts/generate_transfer_sensitivity_report.py --dry-run"
    )


def test_report_lists_all_current_external_transfer_dependencies() -> None:
    _module, report = _report()

    rows = report["current_transfer_rows"]
    assert {row["transfer_id"] for row in rows} == {
        "aniclass.lowell.f2_vector.v1",
        "aniclass.lowell.f2_tensor.v1",
        "aniclass.lowell.f3_vector.v1",
        "aniclass.lowell.f3_tensor.v1",
        "aniclass.lowell.shear_to_D2.v1",
        "aniclass.lowell.shear_to_D3.v1",
        "bass.empirical_proxy.shear_to_D2.v1",
    }
    assert {row["transfer_source"] for row in rows} == {
        "AniCLASS_external",
        "empirical_proxy",
    }


def test_report_marks_current_rows_transfer_conditional_not_native() -> None:
    _module, report = _report()

    for row in report["current_transfer_rows"]:
        assert row["transfer_conditional"] is True
        assert row["native_solver_result"] is False
        assert row["claim_tier"] == "conditional"
        assert row["production_status"] == "diagnostic_only"
        assert row["passed_validation_gates"] == []
        assert row["family_label_role"] == "provenance_only_not_classification"


def test_report_includes_downstream_result_card_transfer_status() -> None:
    _module, report = _report()

    rows = {row["row_id"]: row for row in report["downstream_result_card_rows"]}
    assert {
        "mio.departure_report.sections",
        "mio.budget_spec.external_transfer",
        "bass.budget_ceiling_policy_result",
        "bass.atlas_entry_lite.current_external_proxy",
        "bass.native_schema.future_only",
    } <= set(rows)
    assert (
        rows["mio.departure_report.sections"]["transfer_conditional_status"]
        == "section_inherits_external_or_proxy_transfer_metadata"
    )
    assert rows["bass.native_schema.future_only"]["claim_tier"] == "blocked"
    assert (
        rows["bass.native_schema.future_only"]["transfer_conditional_status"]
        == "schema_only_non_consumable_no_values"
    )


def test_payload_summary_preserves_downstream_transfer_conditional_status() -> None:
    module = _load_module()
    payload = {
        "owner": "MIO",
        "implementation_scope": "mio",
        "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "report_role": "mio_diagnostic_report_card",
        "config_hash": "sha256:fixture-report",
        "input_hashes": ["sha256:fixture-input"],
        "transfer_provenance_by_section": {
            "x_C": {
                "status": "available",
                "transfer_source": "AniCLASS_external",
                "transfer_spec_id": "aniclass.report.x.v1",
            },
            "Q": {"status": "available", "transfer_source": "none"},
        },
    }

    row = module.summarize_downstream_result_card_payload(
        row_id="payload.fixture.mio-report",
        payload=payload,
        source_path="memory://fixture",
        generating_command="pytest fixture",
    )

    assert row["transfer_source"] == "AniCLASS_external"
    assert row["transfer_spec_ids"] == ["aniclass.report.x.v1"]
    assert row["transfer_conditional"] is True
    assert row["transfer_conditional_status"] == "transfer_conditional_result_card"
    assert row["claim_tier"] == "diagnostic_only"


def test_payload_summary_rejects_provisional_or_ungated_native_sources() -> None:
    module = _load_module()
    base_payload = {
        "owner": "BASS",
        "implementation_scope": "bass_py",
        "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "report_role": "native_payload_fixture",
        "config_hash": "sha256:native-fixture",
        "input_hashes": ["sha256:native-fixture-input"],
    }

    provisional = dict(base_payload)
    provisional["transfer_provenance_by_section"] = {
        "alm_T": {
            "status": "available",
            "transfer_source": "BASS_native_provisional",
            "transfer_spec_id": "bass.native.schema.alm_T.v1",
        }
    }
    with pytest.raises(ValueError, match="schema-only"):
        module.summarize_downstream_result_card_payload(
            row_id="payload.bad.provisional",
            payload=provisional,
            source_path="memory://native-provisional",
            generating_command="pytest fixture",
        )

    ungated_native = dict(base_payload)
    ungated_native["transfer_provenance_by_section"] = {
        "alm_T": {
            "status": "available",
            "transfer_source": "BASS_native_validated",
            "transfer_spec_id": "bass.native.alm_T.v1",
        }
    }
    with pytest.raises(ValueError, match="validation gates"):
        module.summarize_downstream_result_card_payload(
            row_id="payload.bad.native",
            payload=ungated_native,
            source_path="memory://native-ungated",
            generating_command="pytest fixture",
        )

    native_metadata = TransferFunctionSpec(
        transfer_id="bass.native.lowell.temperature.v1",
        source="BASS_native_validated",
        family="BianchiI",
        valid_range=TransferValidRange(
            k_min=1.0e-5,
            k_max=0.2,
            ell_min=2,
            ell_max=30,
        ),
        observable_kind="temperature",
        normalization="unit_primordial_curvature",
        calibration_status="native_validated",
        caveats=("native transfer fixture",),
        passed_validation_gates=("native_transfer_validated",),
    ).to_metadata()
    partially_ungated = dict(base_payload)
    partially_ungated["transfer_provenance_by_section"] = {
        "missing_metadata": {
            "transfer_source": "BASS_native_validated",
            "transfer_spec_id": "bass.native.missing.v1",
        },
        "valid_metadata": {
            "transfer_source": "BASS_native_validated",
            "transfer_spec_id": "bass.native.lowell.temperature.v1",
            "transfer_metadata": native_metadata,
        },
    }
    with pytest.raises(ValueError, match="validation gates"):
        module.summarize_downstream_result_card_payload(
            row_id="payload.bad.partially-ungated-native",
            payload=partially_ungated,
            source_path="memory://native-partially-ungated",
            generating_command="pytest fixture",
        )

    valid_native = dict(base_payload)
    valid_native["transfer_provenance_by_section"] = {
        "alm_T": {
            "transfer_source": "BASS_native_validated",
            "transfer_spec_id": "bass.native.lowell.temperature.v1",
            "transfer_metadata": native_metadata,
        },
    }
    row = module.summarize_downstream_result_card_payload(
        row_id="payload.valid.native",
        payload=valid_native,
        source_path="memory://native-valid",
        generating_command="pytest fixture",
    )
    assert row["transfer_conditional_status"] == "native_validated_result_card"

    mismatched_native = dict(base_payload)
    mismatched_native["transfer_provenance_by_section"] = {
        "alm_T": {
            "transfer_source": "BASS_native_validated",
            "transfer_spec_id": "bass.native.other.v1",
            "transfer_metadata": native_metadata,
        },
    }
    with pytest.raises(ValueError, match="transfer_spec_id must match"):
        module.summarize_downstream_result_card_payload(
            row_id="payload.bad.mismatched-native",
            payload=mismatched_native,
            source_path="memory://native-mismatched",
            generating_command="pytest fixture",
        )


def test_report_carries_manifest_metadata_and_claim_guard_passes() -> None:
    module, report = _report()
    metadata = report["metadata"]

    issues = validate_manifest_payload(
        metadata,
        manifest_path=REPO_ROOT / "docs/generated/transfer_sensitivity_report.md",
    )
    assert issues == ()
    assert metadata["owner"] == "COMMON"
    assert metadata["implementation_scope"] == "common"
    assert metadata["claim_tier"] == "diagnostic_only"
    assert metadata["transfer_source"] == "none"
    assert metadata["sky_support_status"] == "not_directional"
    assert metadata["null_mock_status"] == "not_statistical"
    assert metadata["generating_command"].startswith(
        "python scripts/generate_transfer_sensitivity_report.py"
    )
    assert metadata["git_commit_or_worktree_state"]
    assert metadata["config_hash"].startswith("sha256:")
    assert metadata["input_hashes"]

    rendered = module.render_transfer_sensitivity_markdown(report)
    assert "owner: COMMON" in rendered
    assert "transfer-conditional result surfaces" in rendered
    assert not scan_text(rendered, path=Path("transfer_sensitivity_report.md"))


def test_report_fails_closed_when_external_transfer_rows_absent() -> None:
    module, report = _report()
    bad = dict(report)
    bad["current_transfer_rows"] = []

    with pytest.raises(ValueError, match="external-transfer sensitivity"):
        module.validate_transfer_sensitivity_report(bad)


def test_report_rejects_external_rows_marked_native() -> None:
    module, report = _report()
    bad = dict(report)
    rows = [dict(row) for row in report["current_transfer_rows"]]
    rows[0]["native_solver_result"] = True
    bad["current_transfer_rows"] = rows

    with pytest.raises(ValueError, match="native output"):
        module.validate_transfer_sensitivity_report(bad)


def test_report_rejects_missing_required_inputs(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()

    monkeypatch.setattr(module, "INPUT_PATHS", (Path("missing/pr084-input.py"),))

    with pytest.raises(FileNotFoundError, match="required inputs"):
        module.build_transfer_sensitivity_report(command="pytest fixture")


def test_report_rejects_corrupted_required_downstream_rows() -> None:
    module, report = _report()
    bad = dict(report)
    rows = [dict(row) for row in report["downstream_result_card_rows"]]
    rows[0]["transfer_source"] = "none"
    rows[0]["transfer_conditional_status"] = "missing"
    bad["downstream_result_card_rows"] = rows

    with pytest.raises(ValueError, match="unknown downstream transfer status"):
        module.validate_transfer_sensitivity_report(bad)

    missing = dict(report)
    missing["downstream_result_card_rows"] = rows[1:]
    with pytest.raises(ValueError, match="downstream result-card rows are missing"):
        module.validate_transfer_sensitivity_report(missing)


def test_report_rejects_missing_downstream_source_hash() -> None:
    module, report = _report()
    bad = dict(report)
    rows = [dict(row) for row in report["downstream_result_card_rows"]]
    rows[0]["input_hashes"] = ["htt/mio/reports/departure_report.py:missing"]
    bad["downstream_result_card_rows"] = rows

    with pytest.raises(ValueError, match="missing source hash"):
        module.validate_transfer_sensitivity_report(bad)


def test_cli_dry_run_prints_report_without_writing(tmp_path: Path) -> None:
    output = tmp_path / "transfer_sensitivity_report.md"

    completed = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--output", str(output), "--dry-run"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "COMMON transfer sensitivity report" in completed.stdout
    assert "transfer_sensitivity_report.md" in completed.stdout
    assert "aniclass.lowell.shear_to_D2.v1" in completed.stdout
    assert "bass.empirical_proxy.shear_to_D2.v1" in completed.stdout
    assert "mio.departure_report.sections" in completed.stdout
    assert f"artifact_path: {output.as_posix()}" in completed.stdout
    assert not output.exists()


def test_cli_non_dry_run_writes_report(tmp_path: Path) -> None:
    output = tmp_path / "transfer_sensitivity_report.md"

    completed = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--output", str(output)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    rendered = output.read_text(encoding="utf-8")
    assert f"artifact_path: {output.as_posix()}" in rendered
    assert "owner: COMMON" in rendered
    assert "Current Transfer Dependencies" in rendered
    assert "Downstream Result-Card Status" in rendered
    assert "schema_only_non_consumable_no_values" in rendered
