from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess

from common.artifact_manifest import validate_manifest_payload


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts/result_packs/generate_pack_B_local_global.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("pack_b_generator", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _payload(**overrides):
    module = _load_module()
    return module.build_result_pack_payload(
        repo_root=REPO_ROOT,
        generating_command=(
            "python scripts/result_packs/generate_pack_B_local_global.py --dry-run"
        ),
        worktree_state="test-worktree",
        **overrides,
    )


def _assert_no_forbidden_language(text: str) -> None:
    lowered = text.lower()
    assert ("global " + "tilt candidate") not in lowered
    assert ("global-" + "tilt candidate") not in lowered
    assert ("global " + "tilt detected") not in lowered
    assert ("global " + "tilt favored") not in lowered
    assert ("posterior " + "odds") not in lowered
    assert ("native " + "solver result") not in lowered
    assert ("family " + "identified") not in lowered
    assert ("geometry " + "detected") not in lowered
    assert ("external transfer " + "validated " + "as native") not in lowered


def test_pack_b_payload_includes_required_surfaces_and_manifest():
    payload = _payload()

    assert payload["owner"] == "COMMON"
    assert payload["implementation_scope"] == "common"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["transfer_source"] == "none"
    assert payload["artifact_id"] == "result_pack_B_local_global"
    assert validate_manifest_payload(
        payload,
        manifest_path="memory://result_pack_B.md",
    ) == ()

    assert payload["global_tilt_claim_tier_ceiling"] == "conditional"
    assert payload["dependency_status"]["PR-066"]["implemented"] is True
    assert payload["dependency_status"]["PR-100"]["implemented"] is True
    assert payload["dependency_status"]["PR-101"]["implemented"] is True
    assert payload["legacy_ver2_context"]["pr111_use"] == (
        "legacy_context_only_not_promoted"
    )
    assert payload["legacy_ver2_context"]["source_production_status"] == (
        "production_candidate"
    )

    categories = {row["category"] for row in payload["gate_summary"]}
    assert {
        "rank_audit",
        "local_null_fpr",
        "survey_systematic_null_fpr",
        "depth_gap",
        "directional_coherence",
        "posterior_pushforward",
    } <= categories
    assert payload["claim_boundaries"]["mio_coherence_use"] == (
        "diagnostic_cross_check_not_htt_evidence"
    )
    assert payload["claim_boundaries"]["native_solver_status"] == (
        "not_native_solver_output"
    )
    depth_gap = next(
        row for row in payload["gate_summary"] if row["category"] == "depth_gap"
    )
    assert depth_gap["G_F_floor_report_ref"].endswith(
        "#/semantic_and_vectors/g_f_display_contract"
    )
    assert depth_gap["denominator_evolution_split_ref"].endswith(
        "#/semantic_and_vectors/g_f_display_contract/denominator_evolution_split"
    )
    assert depth_gap["matched_null_forecast_report_ref"] == (
        "docs/generated/gf_matched_null_forecast_report.json"
    )
    assert depth_gap["matched_null_forecast_status"] == "forecast_matched_null_blocked"
    assert depth_gap["local_global_separation_status"] == (
        "blocked_existing_null_bank_insufficient"
    )
    _assert_no_forbidden_language(json.dumps(payload, sort_keys=True))


def test_pack_b_markdown_is_conditional_at_most_and_caveated():
    module = _load_module()
    payload = _payload()

    markdown = module.render_markdown(payload)

    assert "# Result Pack B - Local Global Discrimination" in markdown
    assert "owner: COMMON" in markdown
    assert "claim_tier: diagnostic_only" in markdown
    assert "Global tilt claim tier ceiling: conditional" in markdown
    assert "rank audit" in markdown
    assert "local/systematic null FPR" in markdown
    assert "G_F depth gap" in markdown
    assert "directional coherence" in markdown
    assert "diagnostic cross-check, not HTT evidence" in markdown
    assert "legacy_context_only_not_promoted" in markdown
    _assert_no_forbidden_language(markdown)


def test_pack_b_rank_deficient_scenarios_block_candidate_language():
    payload = _payload()
    scenarios = {row["scenario_id"]: row for row in payload["rank_scenarios"]}

    for scenario_id in (
        "rank_deficient_projected_response",
        "overlap_degenerate_response",
        "full_design_condition_too_high",
    ):
        scenario = scenarios[scenario_id]
        assert scenario["claim_tier"] == "blocked"
        assert scenario["production_status"].startswith("blocked_")
        assert scenario["local_global_candidate_status"] == "blocked_no_claim"
        assert scenario["allowed_report_phrase"] == (
            "no-claim rank or overlap blocker"
        )
        _assert_no_forbidden_language(json.dumps(scenario, sort_keys=True))


def test_pack_b_null_fpr_failures_block_candidate_language():
    payload = _payload()
    scenarios = {row["scenario_id"]: row for row in payload["rank_scenarios"]}

    for scenario_id in (
        "missing_local_null_fpr",
        "high_survey_systematic_fpr",
    ):
        scenario = scenarios[scenario_id]
        assert scenario["claim_tier"] == "blocked"
        assert scenario["local_global_candidate_status"] == "blocked_no_claim"
        assert "fpr" in " ".join(scenario["blocked_reasons"]).lower()
        _assert_no_forbidden_language(json.dumps(scenario, sort_keys=True))


def test_pack_b_cli_dry_run_does_not_write_output(tmp_path):
    output = tmp_path / "result_pack_B.md"

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
    assert "Result Pack B - Local Global Discrimination" in result.stdout
    assert not output.exists()


def test_pack_b_cli_writes_report(tmp_path):
    output = tmp_path / "result_pack_B.md"

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
    assert "Result Pack B - Local Global Discrimination" in content
    assert "wrote" in result.stdout
    _assert_no_forbidden_language(content)


def test_pack_b_cli_check_detects_missing_and_stale_without_writing(tmp_path):
    output = tmp_path / "result_pack_B.md"

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


def test_pack_b_cli_check_reuses_existing_worktree_state(tmp_path):
    module = _load_module()
    output = tmp_path / "result_pack_B.md"
    command = (
        "python scripts/result_packs/generate_pack_B_local_global.py "
        f"--output {output}"
    )
    payload = module.build_result_pack_payload(
        repo_root=REPO_ROOT,
        generating_command=command,
        worktree_state="stored-head+dirty",
    )
    output.write_text(module.render_markdown(payload), encoding="utf-8")

    result = subprocess.run(
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

    assert result.returncode == 0, result.stderr
    assert "up-to-date" in result.stdout
