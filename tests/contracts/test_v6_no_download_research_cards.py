from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_script():
    path = REPO_ROOT / "scripts" / "build_v6_no_download_research_cards.py"
    spec = importlib.util.spec_from_file_location("build_v6_no_download_research_cards", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_v6_no_download_research_cards"] = module
    spec.loader.exec_module(module)
    return module


def test_v6_cards_preserve_no_download_claim_boundaries() -> None:
    research = json.loads(
        (REPO_ROOT / "docs/generated/v6_no_download_research_cards.json").read_text(
            encoding="utf-8"
        )
    )

    assert research["claim_tier"] == "diagnostic_only"
    assert "No long-run K1/K5/K6 analysis is executed by this artifact." in research["caveats"]
    cards = research["cards"]
    identified = cards["identified_set_card"]
    assert identified["x_C_interval_status"] == "not_certified_blind_sectors_not_zeroed"
    assert identified["F_status"] == "diagnostic_only_not_certified_filling"
    assert set(identified["fail_closed_columns"]) == {"W2", "Omega_k", "Omega_tilt"}

    omega = next(
        row
        for row in cards["component_source_matrix"]["rows"]
        if row["component"] == "Omega_tilt"
    )
    assert omega["source_status"] == "blocked_open_p0"
    assert omega["source_mode"] == "quarantined_no_active_value"
    assert omega["value_summary"] is None
    assert omega["allowed_use"] == "blocked_source_record_only"

    sigma = next(
        row
        for row in cards["component_source_matrix"]["rows"]
        if row["component"] == "Sigma2"
    )
    assert sigma["blocker"] == "PR3_E2E_ANALYSIS_DEFERRED_TO_PR150"
    assert sigma["pr4_scope"] == (
        "not_downloaded_download_reduction_analysis_skipped_by_user_scope"
    )

    readiness = cards["k1_e2e_data_readiness"]
    assert readiness["current_result_status"] == (
        "measured_partial_isotropic_lcdm_grf_null"
    )
    assert readiness["pr3_ffp10"] == {
        "download_state": "complete",
        "analysis_state": "deferred_to_pr150",
        "claim_effect": "none_until_provenance_complete_analysis",
    }
    assert readiness["pr4_npipe"] == {
        "download_state": "not_downloaded",
        "reduction_state": "skipped_by_user_scope",
        "analysis_state": "skipped_by_user_scope",
        "claim_effect": "none",
    }

    depth = cards["depth_gap_card"]
    assert depth["cf4_shell_attempt_status"] == (
        "not_attempted_current_cf4_shells_lack_matched_covariance_and_calibrated_null"
    )
    assert depth["allowed_use"] == "display_contract_and_readiness_only"

    exceedance = cards["exceedance_calibration_card"]
    assert exceedance["calibration_status"] == "raw_exceedance_only_uncalibrated_no_p_value"
    assert exceedance["forbidden_use"] == "p_value_or_truth_probability"


def test_v6_figure_classification_discards_old_claim_lane() -> None:
    payload = json.loads(
        (REPO_ROOT / "docs/generated/v6_legacy_figure_classification.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["summary"]["classified_old_figures"] >= 80
    assert payload["summary"]["missing_conditioned_replacement_manifest"] == 0
    rows = payload["rows"]
    assert all(row["current_disposition"] == "discarded_from_current_claim_lane" for row in rows)
    assert all(row["allowed_use"] == "none_as_current_result" for row in rows)
    forbidden_text = json.dumps(rows).lower()
    assert "headline_plot" in forbidden_text
    assert "family_identification" in forbidden_text


def test_v6_k5_k6_feasibility_is_check_only_not_execution_claim() -> None:
    research = json.loads(
        (REPO_ROOT / "docs/generated/v6_no_download_research_cards.json").read_text(
            encoding="utf-8"
        )
    )
    feasibility = research["cards"]["k5_k6_next_turn_feasibility"]

    assert feasibility["K5"]["input_present"] is True
    assert feasibility["K6"]["input_present"] is True
    assert feasibility["K5"]["next_turn_runnable"] is False
    assert feasibility["K6"]["next_turn_runnable"] is True
    assert feasibility["K5"]["heavy_run_deferred_this_turn"] is True
    assert feasibility["K6"]["heavy_run_deferred_this_turn"] is True
    assert "execution forbidden" in feasibility["K5"]["expected_runtime_note"]


def test_v6_generator_check_mode_is_current() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "build_v6_no_download_research_cards.py"),
            "--check",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_v6_builder_does_not_use_forbidden_current_claims() -> None:
    module = _load_script()
    figure_payload = module.build_legacy_figure_classification("test")
    research_payload = module.build_research_cards("test", figure_payload)
    rendered = module.render_research_markdown(research_payload)

    forbidden = [
        "Bianchi geometry detected",
        "Bianchi family identified",
        "model-independent truth certificate",
        "MIO posterior",
        "external transfer validated as native",
    ]
    for phrase in forbidden:
        assert phrase not in rendered
