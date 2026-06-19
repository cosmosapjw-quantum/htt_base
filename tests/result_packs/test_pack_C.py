from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess

from common.artifact_manifest import validate_manifest_payload


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts/result_packs/generate_pack_C_mio_certificates.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("pack_c_generator", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _payload():
    module = _load_module()
    return module.build_result_pack_payload(
        repo_root=REPO_ROOT,
        generating_command=(
            "python scripts/result_packs/generate_pack_C_mio_certificates.py --dry-run"
        ),
        worktree_state="test-worktree",
    )


def _assert_no_forbidden_language(text: str) -> None:
    lowered = text.lower()
    assert ("model " + "posterior " + "odds") not in lowered
    assert ("posterior " + "odds") not in lowered
    assert ("mio " + "posterior") not in lowered
    assert ("truth " + "certificate") not in lowered
    assert ("native " + "solver result") not in lowered
    assert ("family " + "identified") not in lowered
    assert ("geometry " + "detected") not in lowered
    assert ("external transfer " + "validated " + "as native") not in lowered


def test_pack_c_payload_gathers_mio_surfaces_with_manifest():
    payload = _payload()

    assert payload["owner"] == "COMMON"
    assert payload["implementation_scope"] == "common"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["transfer_source"] == "none"
    assert payload["artifact_id"] == "result_pack_C_mio_certificates"
    assert validate_manifest_payload(
        payload,
        manifest_path="memory://result_pack_C.md",
    ) == ()

    assert payload["dependency_status"]["PR-100"]["implemented"] is True
    assert payload["dependency_status"]["PR-101"]["implemented"] is True
    assert payload["dependency_status"]["PR-102"]["implemented"] is True
    assert payload["dependency_status"]["PR-103"]["implemented"] is True
    categories = {row["category"] for row in payload["certificate_rows"]}
    assert {
        "directional_coherence_certificate",
        "redshift_binned_coherence_certificate",
        "flrw_null_predictive_certificate",
        "predictive_residual_context",
        "evidence_anatomy_narrative",
    } <= categories
    assert {row["owner"] for row in payload["certificate_rows"]} == {"MIO"}
    assert {
        row["model_ranking_status"] for row in payload["certificate_rows"]
    } == {"forbidden_not_ranked"}
    assert payload["legacy_ver2_context"]["pr112_use"] == (
        "legacy_context_only_not_promoted"
    )
    assert payload["claim_boundaries"]["certificate_ranking_status"] == (
        "forbidden_not_ranked"
    )
    _assert_no_forbidden_language(json.dumps(payload, sort_keys=True))


def test_pack_c_status_scenarios_make_diagnostic_and_production_grade_explicit():
    payload = _payload()
    scenarios = {row["scenario_id"]: row for row in payload["status_scenarios"]}

    assert scenarios["complete_mio_metadata"]["public_readiness_label"] == (
        "diagnostic-only"
    )
    assert scenarios["complete_mio_metadata"]["legacy_readiness_status"] == (
        "legacy_not_current"
    )
    assert scenarios["complete_mio_metadata"]["claim_tier_ceiling"] == "conditional"
    assert scenarios["complete_mio_metadata"]["model_ranking_status"] == (
        "forbidden_not_ranked"
    )
    assert scenarios["missing_covariance_or_null"]["public_readiness_label"] == (
        "diagnostic-only"
    )
    assert scenarios["missing_covariance_or_null"]["claim_tier_ceiling"] == "blocked"
    assert scenarios["descriptive_tail_only"]["certificate_use"] == (
        "diagnostic_only_descriptive"
    )
    assert scenarios["htt_evidence_trace_narrative"]["certificate_use"] == (
        "read_only_context_not_mio_evidence"
    )
    _assert_no_forbidden_language(json.dumps(payload["status_scenarios"], sort_keys=True))


def test_pack_c_markdown_lists_statuses_caveats_and_no_ranking():
    module = _load_module()
    payload = _payload()

    markdown = module.render_markdown(payload)

    assert "# Result Pack C - MIO Observatory Certificates" in markdown
    assert "owner: COMMON" in markdown
    assert "claim_tier: diagnostic_only" in markdown
    assert "Diagnostic-only public readiness is explicit" in markdown
    assert "directional coherence certificate" in markdown
    assert "redshift binned coherence certificate" in markdown
    assert "FLRW null predictive certificate" in markdown
    assert "evidence anatomy narrative" in markdown
    assert "forbidden_not_ranked" in markdown
    assert "legacy_context_only_not_promoted" in markdown
    assert "legacy_not_current" in markdown
    assert "production_candidate" not in markdown
    assert "production-grade" not in markdown
    _assert_no_forbidden_language(markdown)


def test_pack_c_cli_dry_run_does_not_write_output(tmp_path):
    output = tmp_path / "result_pack_C.md"

    result = subprocess.run(
        [
            str(REPO_ROOT / "venv/bin/python"),
            str(SCRIPT_PATH),
            "--dry-run",
            "--output",
            str(output),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "DRY-RUN" in result.stdout
    assert "Result Pack C - MIO Observatory Certificates" in result.stdout
    assert not output.exists()


def test_pack_c_cli_writes_report(tmp_path):
    output = tmp_path / "result_pack_C.md"

    result = subprocess.run(
        [
            str(REPO_ROOT / "venv/bin/python"),
            str(SCRIPT_PATH),
            "--output",
            str(output),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    content = output.read_text(encoding="utf-8")
    assert "Result Pack C - MIO Observatory Certificates" in content
    assert "wrote" in result.stdout
    _assert_no_forbidden_language(content)


def test_pack_c_cli_check_detects_missing_and_stale_without_writing(tmp_path):
    output = tmp_path / "result_pack_C.md"

    missing_result = subprocess.run(
        [
            str(REPO_ROOT / "venv/bin/python"),
            str(SCRIPT_PATH),
            "--check",
            "--output",
            str(output),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert missing_result.returncode == 1
    assert "missing result pack" in missing_result.stdout
    assert not output.exists()

    write_result = subprocess.run(
        [
            str(REPO_ROOT / "venv/bin/python"),
            str(SCRIPT_PATH),
            "--output",
            str(output),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert write_result.returncode == 0, write_result.stderr

    check_result = subprocess.run(
        [
            str(REPO_ROOT / "venv/bin/python"),
            str(SCRIPT_PATH),
            "--check",
            "--output",
            str(output),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert check_result.returncode == 0, check_result.stderr
    assert "up-to-date" in check_result.stdout

    output.write_text(output.read_text(encoding="utf-8") + "\nmanual drift\n")
    stale_result = subprocess.run(
        [
            str(REPO_ROOT / "venv/bin/python"),
            str(SCRIPT_PATH),
            "--check",
            "--output",
            str(output),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert stale_result.returncode == 1
    assert "stale result pack" in stale_result.stdout
