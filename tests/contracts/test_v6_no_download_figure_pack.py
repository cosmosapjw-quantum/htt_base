from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from common.artifact_manifest import validate_manifest_payload


REPO_ROOT = Path(__file__).resolve().parents[2]
FIGURE_DIR = REPO_ROOT / "figures" / "quarantined_meta" / "v6_no_download"
PACK_JSON = REPO_ROOT / "docs" / "generated" / "v6_no_download_figure_pack.json"
PACK_MD = REPO_ROOT / "docs" / "generated" / "v6_no_download_figure_pack.md"
COMMANDS_JSON = REPO_ROOT / "docs" / "generated" / "v6_k5_k6_user_commands.json"
COMMANDS_MD = REPO_ROOT / "docs" / "generated" / "v6_k5_k6_user_commands.md"

EXPECTED_FIGURES = (
    "fig_v6_component_source_matrix.png",
    "fig_v6_denominator_sensitivity.png",
    "fig_v6_response_class_ledger.png",
    "fig_v6_optical_ansatz_readiness.png",
    "fig_v6_depth_gap_and_readiness.png",
)


def _read_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_v6_figure_pack_outputs_are_manifest_backed() -> None:
    pack = _read_json(PACK_JSON)

    assert pack["owner"] == "COMMON"
    assert pack["claim_tier"] == "diagnostic_only"
    assert pack["k5_k6_execution_policy"] == "commands_exported_for_user_not_run_by_generator"
    assert [row["file_name"] for row in pack["figures"]] == list(EXPECTED_FIGURES)
    assert PACK_MD.is_file()

    for file_name in EXPECTED_FIGURES:
        figure_path = FIGURE_DIR / file_name
        sidecar = figure_path.with_suffix("").with_name(figure_path.stem + ".manifest.json")
        assert figure_path.is_file()
        assert figure_path.stat().st_size > 2000
        assert sidecar.is_file()
        manifest = _read_json(sidecar)
        rel_path = figure_path.relative_to(REPO_ROOT).as_posix()
        issues = validate_manifest_payload(
            manifest,
            manifest_path=sidecar.relative_to(REPO_ROOT),
            expected_artifact_path=rel_path,
        )
        assert issues == ()
        assert manifest["artifact_path"] == rel_path
        assert manifest["artifact_mode"] == "internal_exploratory"
        assert manifest["allowed_use"] == "internal_only"
        assert (
            manifest["statistics_definitions"]["v6_figure_lane"]
            == "quarantined_meta_v6_no_download"
        )
        assert manifest["null_mock_status"] in {
            "mixed_diagnostic_and_blocked",
            "not_statistical",
        }
        assert "docs/generated/v6_no_download_research_cards.json" in " ".join(
            manifest["input_hashes"]
        )


def test_v6_k5_k6_user_commands_are_exported_without_run_claims() -> None:
    commands = _read_json(COMMANDS_JSON)

    assert commands["execution_policy"] == "user_runs_commands_generator_did_not_execute_k5_k6"
    assert commands["claim_tier"] == "diagnostic_only"
    assert COMMANDS_MD.is_file()
    lanes = commands["commands"]
    assert lanes["K5"]["run_command"] == "venv/bin/python scripts/k5_cf4_release_coverage.py"
    assert lanes["K6"]["run_command"] == "venv/bin/python scripts/k6_cf4_curl_posterior.py"
    assert lanes["K5"]["check_command"].endswith(" --check")
    assert lanes["K6"]["check_command"].endswith(" --check")
    assert lanes["K5"]["generator_executed_this_turn"] is False
    assert lanes["K6"]["generator_executed_this_turn"] is False


def test_v6_figure_generator_check_mode_is_current() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "make_v6_no_download_figures.py"),
            "--check",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_v6_figure_pack_does_not_use_forbidden_current_claims() -> None:
    rendered = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (PACK_MD, COMMANDS_MD)
        if path.exists()
    )
    for phrase in (
        "Bianchi geometry detected",
        "Bianchi family identified",
        "model-independent truth certificate",
        "MIO posterior",
        "external transfer validated as native",
    ):
        assert phrase not in rendered
