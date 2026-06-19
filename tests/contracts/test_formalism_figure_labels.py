from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_script(name: str):
    path = REPO_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_canonical_formalism_rows_pass_registry():
    module = _load_script("verify_formalism_figure_labels")
    x_display_metadata = {
        "requires_sector_profile": True,
        "requires_absolute_component_total": True,
        "requires_cancellation_index": True,
        "requires_magnitude_companion_M": True,
        "requires_comparator_label": True,
        "comparator": "CMB_FLRW_reference",
        "frame": "normal_frame",
        "units": "dimensionless_hubble_normalized",
        "interpretation": "near-zero x_C can reflect cancellation, not isotropy",
    }
    q_display_metadata = {
        "requires_comparator_label": True,
        "comparator": "CMB_FLRW_reference",
        "frame": "normal_frame",
        "units": "dimensionless_hubble_normalized",
        "numerator_policy": "absolute",
        "denominator_policy": "MES_linear",
        "denominator_use": "signed_projection_normalization",
        "comparator_multiverse_ref": "/transfer_sensitivity/q_comparator_multiverse",
        "comparator_labels": ["CMB_FLRW_reference", "observer_frame_reference"],
        "q_spread_absolute": 0.2,
        "spread_role": "specification_curve_sensitivity_only",
        "comparator_axis_status": "registered_current_code_display_axis",
        "admissible_set_status": "explicit_display_set_not_exhaustive",
        "rank_equivalence_status": "not_evaluated_no_equivalence_or_morphology_claim",
    }
    pi_display_metadata = {
        "requires_measure_kind": True,
        "source_score_label": "Q",
        "source_kind": "normalized_score.q_value",
        "measure_kind": "sample_distribution",
        "threshold_policy": "curve_only",
        "threshold_registration_status": "curve_only_no_selected_threshold",
        "threshold_grid": [0.25, 0.75],
        "look_elsewhere_trials": 1,
        "exceedance_rule": "sample_value > threshold",
        "calibration_status": "raw_exceedance_only_uncalibrated_no_p_value",
        "covariance_status": "not_statistical",
        "null_mock_status": "not_statistical",
        "p_value_interpretation_status": "blocked_exceedance_not_p_value",
        "blocked_use_codes": [
            "p_value_claim",
            "truth_probability",
            "htt_inference_consumption",
            "model_selection",
            "solver_validation",
            "scalar_classification",
        ],
    }
    gf_display_metadata = {
        "requires_floor_applied_by_bin": True,
        "requires_raw_effective_f_by_bin": True,
        "requires_denominator_evolution_split": True,
        "requires_depth_bin_metadata": True,
        "floor_applied_by_bin_ref": "/semantic_and_vectors/g_f_display_contract/floor_applied_by_bin",
        "denominator_evolution_split_ref": "/semantic_and_vectors/g_f_display_contract/denominator_evolution_split",
        "depth_bin_metadata_ref": "/semantic_and_vectors/g_f_display_contract/depth_bins",
        "matched_null_forecast_status": "forecast_matched_null_blocked",
        "local_global_separation_status": "blocked_existing_null_bank_insufficient",
        "forecast_only": True,
        "observed_data_evidence": False,
        "global_tilt_wording_allowed": False,
        "blocked_use_codes": [
            "htt_evidence",
            "posterior_claim",
            "global_tilt_claim",
            "family_identification",
            "native_solver_validation",
            "geometry_detection",
        ],
    }
    rows = [
        {
            "symbol": "x",
            "owner": "MIO",
            "definition": "raw diagnostic departure scalar in the stress payload",
            "display_metadata": x_display_metadata,
        },
        {
            "symbol": "Q",
            "owner": "MIO",
            "definition": "x divided by explicit denominator policy",
            "display_metadata": q_display_metadata,
        },
        {
            "symbol": "Pi",
            "owner": "MIO",
            "definition": "exceedance curve over explicit threshold grid for Q samples",
            "display_metadata": pi_display_metadata,
        },
        {
            "symbol": "F",
            "owner": "MIO",
            "definition": "certified filling fraction under sign-clean admissible ceiling",
            "display_metadata": x_display_metadata,
        },
        {
            "symbol": "G_F",
            "owner": "MIO",
            "definition": "depth-gap diagnostic with depth-bin metadata and null calibration",
            "display_metadata": gf_display_metadata,
        },
        {
            "symbol": "Q-spread",
            "owner": "MIO",
            "definition": "specification-curve spread across explicit Q comparators",
            "display_metadata": {
                "spread_role": "specification_curve_sensitivity_only",
                "comparator_labels": [
                    "CMB_FLRW_reference",
                    "observer_frame_reference",
                ],
                "q_spread_absolute": 0.2,
            },
        },
    ]

    assert module.validate_rows(rows) == []


def test_x_and_f_rows_require_cancellation_display_metadata():
    module = _load_script("verify_formalism_figure_labels")

    rows = [
        {
            "symbol": "x",
            "owner": "MIO",
            "definition": "raw diagnostic departure scalar",
        },
        {
            "symbol": "F",
            "owner": "MIO",
            "definition": "certified filling fraction under sign-clean admissible ceiling",
            "display_metadata": {
                "requires_sector_profile": True,
                "requires_absolute_component_total": True,
                "requires_cancellation_index": True,
                "interpretation": "signed projection fraction",
            },
        },
    ]

    issue_keys = {
        (issue.symbol, issue.issue_type) for issue in module.validate_rows(rows)
    }

    assert ("x", "missing_cancellation_display_metadata") in issue_keys
    assert ("F", "missing_magnitude_companion_metadata") in issue_keys
    assert ("F", "unsafe_cancellation_interpretation") in issue_keys


def test_x_and_q_rows_require_explicit_comparator_display_metadata():
    module = _load_script("verify_formalism_figure_labels")

    rows = [
        {
            "symbol": "x",
            "owner": "MIO",
            "definition": "raw diagnostic departure scalar",
            "display_metadata": {
                "requires_sector_profile": True,
                "requires_absolute_component_total": True,
                "requires_cancellation_index": True,
                "requires_magnitude_companion_M": True,
                "interpretation": "near-zero x_C can reflect cancellation, not isotropy",
            },
        },
        {
            "symbol": "Q",
            "owner": "MIO",
            "definition": "x divided by explicit denominator policy",
            "display_metadata": {
                "requires_comparator_label": True,
                "comparator": "CMB_FLRW_reference",
                "frame": "normal_frame",
                "units": "dimensionless_hubble_normalized",
                "numerator_policy": "absolute",
                "denominator_policy": "MES_linear",
                "denominator_use": "signed_projection_normalization",
            },
        },
    ]

    issue_keys = {
        (issue.symbol, issue.issue_type) for issue in module.validate_rows(rows)
    }

    assert ("x", "missing_comparator_display_metadata") in issue_keys
    assert ("Q", "missing_comparator_multiverse_metadata") in issue_keys


def test_payload_verifier_rejects_q_row_summary_mismatch():
    module = _load_script("verify_formalism_figure_labels")
    payload = json.loads(
        (REPO_ROOT / "docs" / "generated" / "current_science_plot_payload.json").read_text(
            encoding="utf-8"
        )
    )
    rows = payload["semantic_and_vectors"]["semantic_split"]
    q_row = next(row for row in rows if row["symbol"] == "Q")
    q_row["display_value"] = 0.0
    q_row["display_metadata"]["comparator"] = "bogus_comparator"
    q_row["display_metadata"]["comparator_labels"] = ["bogus_comparator"]
    q_row["display_metadata"]["q_spread_absolute"] = 0.0

    issue_keys = {
        (issue.symbol, issue.issue_type)
        for issue in module.validate_payload(payload)
    }

    assert ("Q", "q_comparator_summary_mismatch") in issue_keys


def test_payload_verifier_requires_q_and_pi_policy_summaries():
    module = _load_script("verify_formalism_figure_labels")
    payload = json.loads(
        (REPO_ROOT / "docs" / "generated" / "current_science_plot_payload.json").read_text(
            encoding="utf-8"
        )
    )

    del payload["transfer_sensitivity"]["q_comparator_multiverse"]
    del payload["transfer_sensitivity"]["pi_policy_summary"]

    issue_keys = {
        (issue.symbol, issue.issue_type)
        for issue in module.validate_payload(payload)
    }

    assert ("Q", "missing_q_comparator_multiverse_summary") in issue_keys
    assert ("Pi", "missing_pi_policy_summary") in issue_keys


def test_q_spread_rows_require_specification_curve_metadata():
    module = _load_script("verify_formalism_figure_labels")

    rows = [
        {
            "symbol": "Q-spread",
            "owner": "MIO",
            "definition": "uncertainty band around Q",
            "display_metadata": {"spread_role": "uncertainty_interval"},
        }
    ]

    issue_keys = {
        (issue.symbol, issue.issue_type) for issue in module.validate_rows(rows)
    }

    assert ("Q-spread", "missing_q_spread_contract") in issue_keys


def test_pi_rows_require_measure_kind_threshold_and_look_elsewhere_metadata():
    module = _load_script("verify_formalism_figure_labels")

    rows = [
        {
            "symbol": "Pi",
            "owner": "MIO",
            "definition": "exceedance curve over explicit threshold grid for Q samples",
            "display_metadata": {
                "source_score_label": "Q",
                "measure_kind": "sample_distribution",
                "threshold_policy": "curve_only",
                "threshold_grid": [0.25, 0.75],
            },
        }
    ]

    issue_keys = {
        (issue.symbol, issue.issue_type) for issue in module.validate_rows(rows)
    }

    assert ("Pi", "missing_threshold_registration_status") in issue_keys
    assert ("Pi", "missing_look_elsewhere_trials") in issue_keys
    assert ("Pi", "missing_p_value_block_status") in issue_keys
    assert ("Pi", "missing_calibration_status") in issue_keys
    assert ("Pi", "missing_pi_blocked_use_codes") in issue_keys


def test_gf_rows_require_floor_split_and_forecast_block_metadata():
    module = _load_script("verify_formalism_figure_labels")

    rows = [
        {
            "symbol": "G_F",
            "owner": "MIO",
            "definition": "depth-gap diagnostic with depth-bin metadata and null calibration",
            "display_metadata": {
                "forecast_only": False,
                "matched_null_forecast_status": "matched_null_ready",
            },
        }
    ]

    issue_keys = {
        (issue.symbol, issue.issue_type) for issue in module.validate_rows(rows)
    }

    assert ("G_F", "missing_gf_floor_display_metadata") in issue_keys
    assert ("G_F", "missing_gf_denominator_split_metadata") in issue_keys
    assert ("G_F", "missing_gf_depth_bin_metadata") in issue_keys
    assert ("G_F", "bad_gf_forecast_only_status") in issue_keys
    assert ("G_F", "bad_gf_observed_data_status") in issue_keys
    assert ("G_F", "bad_gf_global_tilt_wording_status") in issue_keys
    assert ("G_F", "missing_gf_blocked_use_codes") in issue_keys


def test_current_audit_failure_rows_are_rejected():
    module = _load_script("verify_formalism_figure_labels")
    rows = [
        {
            "symbol": "Pi",
            "label": "policy spread",
            "owner": "MIO",
            "definition": "inter-policy spread across current denominator policies",
        },
        {
            "symbol": "F",
            "label": "local-null survival",
            "owner": "HTT",
            "definition": "one minus look-elsewhere adjusted local-null FPR",
        },
        {
            "symbol": "G_F",
            "label": "depth response",
            "owner": "HTT",
            "definition": "normalized log depth-response envelope from null-bank payload",
        },
    ]

    issues = module.validate_rows(rows)
    issue_keys = {(issue.symbol, issue.issue_type) for issue in issues}

    assert ("Pi", "definition_mismatch") in issue_keys
    assert ("F", "owner_mismatch") in issue_keys
    assert ("F", "definition_mismatch") in issue_keys
    assert ("G_F", "owner_mismatch") in issue_keys
    assert ("G_F", "definition_mismatch") in issue_keys


def test_cli_exits_nonzero_for_formalism_label_mismatch(tmp_path: Path):
    payload_path = tmp_path / "payload.json"
    payload_path.write_text(
        json.dumps(
            {
                "semantic_and_vectors": {
                    "semantic_split": [
                        {
                            "symbol": "F",
                            "owner": "HTT",
                            "definition": "one minus look-elsewhere adjusted local-null FPR",
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "verify_formalism_figure_labels.py"),
            str(payload_path),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "owner_mismatch" in combined
    assert "definition_mismatch" in combined


def test_checked_in_current_science_payload_has_no_canonical_label_mismatch():
    module = _load_script("verify_formalism_figure_labels")
    payload = json.loads(
        (REPO_ROOT / "docs" / "generated" / "current_science_plot_payload.json").read_text(
            encoding="utf-8"
        )
    )

    assert module.validate_payload(payload) == []


def test_current_payload_has_r066_departure_display_contract():
    payload = json.loads(
        (REPO_ROOT / "docs" / "generated" / "current_science_plot_payload.json").read_text(
            encoding="utf-8"
        )
    )

    contract = payload["semantic_and_vectors"]["departure_display_contract"]
    assert contract["required_for_symbols"] == ["x", "F"]
    assert contract["requires_sector_profile"] is True
    assert contract["requires_absolute_component_total"] is True
    assert contract["requires_cancellation_index"] is True
    assert contract["requires_magnitude_companion_M"] is True

    counter = payload["semantic_and_vectors"]["cancellation_counterexample"]
    assert counter["x_C"] == pytest.approx(0.0)
    assert counter["absolute_component_total"] > 0.0
    assert counter["cancellation_index"] == pytest.approx(1.0)
    assert counter["M_sector_magnitude"] > 0.0
    assert "not isotropy" in counter["interpretation"]


def test_checked_in_current_payload_reports_q_comparator_multiverse_and_pi_policy():
    payload = json.loads(
        (REPO_ROOT / "docs" / "generated" / "current_science_plot_payload.json").read_text(
            encoding="utf-8"
        )
    )

    transfer = payload["transfer_sensitivity"]
    q_summary = transfer["q_comparator_multiverse"]
    pi_summary = transfer["pi_policy_summary"]
    semantic_rows = payload["semantic_and_vectors"]["semantic_split"]
    rows_by_symbol = {
        row["symbol"]: row for row in semantic_rows if isinstance(row, dict)
    }

    assert q_summary["summary_label"] == "Q_comparator_multiverse"
    assert q_summary["display_metadata"]["spread_role"] == (
        "specification_curve_sensitivity_only"
    )
    assert len(q_summary["comparator_labels"]) >= 2
    assert pi_summary["summary_label"] == "Pi_policy_display_contract"
    assert pi_summary["summary_kind"] == "noncanonical_pi_policy_metadata_summary"
    assert pi_summary["calibration_status"] == "raw_exceedance_only_uncalibrated_no_p_value"
    assert "pi_grid" not in pi_summary
    assert "exceedance_fractions" not in pi_summary
    assert pi_summary["display_metadata"]["measure_kind"] == "sample_distribution"
    assert pi_summary["display_metadata"]["look_elsewhere_trials"] >= 1
    assert rows_by_symbol["x"]["display_metadata"]["requires_comparator_label"] is True
    assert rows_by_symbol["Q"]["display_metadata"]["comparator_multiverse_ref"] == (
        "/transfer_sensitivity/q_comparator_multiverse"
    )


def test_checked_in_current_payload_reports_gf_floor_split_and_forecast_block():
    payload = json.loads(
        (REPO_ROOT / "docs" / "generated" / "current_science_plot_payload.json").read_text(
            encoding="utf-8"
        )
    )

    contract = payload["semantic_and_vectors"]["g_f_display_contract"]
    forecast = payload["semantic_and_vectors"]["g_f_matched_null_forecast"]

    assert contract["summary_label"] == "G_F_display_contract"
    assert contract["owner"] == "MIO"
    assert contract["claim_tier"] == "diagnostic_only"
    assert contract["forecast_only"] is True
    assert contract["observed_data_evidence"] is False
    assert contract["global_tilt_wording_allowed"] is False
    assert contract["matched_null_forecast_status"] == "forecast_matched_null_blocked"
    assert contract["local_global_separation_status"] == (
        "blocked_existing_null_bank_insufficient"
    )
    assert contract["floor_value"] > 0.0
    assert contract["floor_label"]
    assert isinstance(contract["floor_applied_by_bin"], dict)
    assert isinstance(contract["raw_F_by_bin"], dict)
    assert isinstance(contract["effective_F_by_bin"], dict)
    assert isinstance(contract["denominator_evolution_split"], dict)
    assert contract["denominator_evolution_split"]["mean_summary_is_decompositional"] is False
    assert contract["floor_applied_by_bin_ref"] == (
        "/semantic_and_vectors/g_f_display_contract/floor_applied_by_bin"
    )
    assert contract["denominator_evolution_split_ref"] == (
        "/semantic_and_vectors/g_f_display_contract/denominator_evolution_split"
    )
    assert "htt_evidence" in contract["blocked_use_codes"]
    assert forecast["artifact_path"] == "docs/generated/gf_matched_null_forecast_report.json"
    assert forecast["artifact_mode"] == "forecast_only"
    assert forecast["allowed_use"] == "external_audit"
    assert forecast["forecast_source_kind"] == "deterministic_current_code_fixture"
    assert forecast["matched_null_status"] == contract["matched_null_forecast_status"]
    assert forecast["observed_data_evidence"] is False
