import json
import subprocess
from pathlib import Path

import pytest

from common.artifact_manifest import validate_manifest_payload


ROOT = Path(__file__).resolve().parents[2]
ASSET_JSON = ROOT / "docs/generated/revision_experiment_assets.json"
MAIN_SNIPPET = ROOT / "docs/manuscript/generated/revision_diagnostic_main_figure.tex"
APPENDIX_SNIPPET = ROOT / "docs/manuscript/generated/revision_diagnostic_appendix_figures.tex"
EXTERNAL_AUDIT_SNIPPET = ROOT / "docs/generated/revision_diagnostic_external_audit_figures.tex"


def test_revision_experiment_assets_check_mode_passes():
    result = subprocess.run(
        [
            "venv/bin/python",
            "scripts/generate_revision_experiment_assets.py",
            "--check",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_revision_experiment_assets_are_lane_limited():
    payload = json.loads(ASSET_JSON.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "htt.revision_experiment_assets.v1"
    assert payload["owner"] == "COMMON"
    assert payload["claim_tier"] == "diagnostic_only"
    expected = {
        "E1_prior_support_surface",
        "E2_sigma_beta_band",
        "E3_per_channel_occupancy",
        "E5_tomographic_forecast",
        "FPR_rule_of_three",
    }
    assert set(payload["assets"]) == expected
    expected_lanes = {
        "E1_prior_support_surface": (
            "paper_appendix_conditioned",
            "paper_appendix",
            "empirical_proxy",
        ),
        "E2_sigma_beta_band": (
            "paper_appendix_conditioned",
            "paper_appendix",
            "empirical_proxy",
        ),
        "FPR_rule_of_three": (
            "external_audit_conditioned",
            "external_audit",
            "none",
        ),
        "E3_per_channel_occupancy": (
            "paper_appendix_conditioned",
            "paper_appendix",
            "none",
        ),
        "E5_tomographic_forecast": (
            "paper_main_candidate",
            "paper_main",
            "empirical_proxy",
        ),
    }
    for asset_id, asset in payload["assets"].items():
        artifact_mode, allowed_use, transfer_source = expected_lanes[asset_id]
        assert asset["artifact_mode"] == artifact_mode
        assert asset["allowed_use"] == allowed_use
        assert asset["transfer_source"] == transfer_source
        assert asset["claim_tier"] == "diagnostic_only"
        assert "not native transfer" in " ".join(asset["caveats"])
        assert "not family identification" in " ".join(asset["caveats"])
        figure_path = ROOT / asset["figure_path"]
        manifest_path = ROOT / asset["manifest_path"]
        assert figure_path.exists()
        assert manifest_path.exists()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert validate_manifest_payload(
            manifest,
            manifest_path=manifest_path,
            expected_artifact_path=asset["figure_path"],
        ) == ()
        assert manifest["artifact_mode"] == artifact_mode
        assert manifest["allowed_use"] == allowed_use
        assert manifest["transfer_source"] == transfer_source
        assert manifest["caption_policy"]
        assert manifest["promotion_blockers"]
        assert manifest["failed_gates"]
        assert manifest["statistics_definitions"]["input_mode"] in {
            "repo_observed_input",
            "analytic_scaffold",
        }

    fpr = payload["assets"]["FPR_rule_of_three"]["statistics"]
    assert "observed_false_positive_count" in fpr
    assert fpr["observed_false_positive_count"] is None or fpr["observed_false_positive_count"] >= 0
    assert fpr["finite_mock_confidence"] == 0.95
    assert 0.0 < fpr["exact_zero_trigger_upper_bound_at_observed_n"]
    assert (
        fpr["exact_zero_trigger_upper_bound_at_observed_n"]
        < fpr["rule_of_three_at_observed_n"]
    )
    if payload["assets"]["FPR_rule_of_three"]["input_mode"] == "repo_observed_input":
        assert fpr["observed_false_positive_count"] is not None
        assert fpr["observed_raw_fpr"] is not None
        assert fpr["observed_adjusted_fpr"] is not None
    assert "0/N is an upper bound" in " ".join(
        payload["assets"]["FPR_rule_of_three"]["caveats"]
    )
    forecast = payload["assets"]["E5_tomographic_forecast"]["statistics"]
    assert forecast["forecast_design_rank"] <= forecast["forecast_design_columns"]
    assert forecast["forecast_rank_status"] in {
        "full_rank_diagnostic",
        "rank_deficient_diagnostic",
    }
    assert "local_global_template_correlation" in forecast
    assert "local_global_separation_score" in forecast
    assert "forecast_projected_singular_values" in forecast
    assert "forecast_rank_no_claim_reasons" in forecast
    assert "forecast_promotion_blockers" in forecast
    assert "forecast_no_claim_reasons" in forecast
    assert "publication_grade_covariance_not_bound" in forecast["forecast_no_claim_reasons"]
    assert "held_out_validation_not_bound" in forecast["forecast_no_claim_reasons"]

    prior = payload["assets"]["E1_prior_support_surface"]["statistics"]
    assert prior["prior_floor_min"] < prior["prior_floor_max"]
    assert prior["prior_ceiling_min"] < prior["prior_ceiling_max"]
    assert "proxy_lnb_definition" in prior

    sigma_beta = payload["assets"]["E2_sigma_beta_band"]["statistics"]
    assert sigma_beta["beta_min"] < sigma_beta["beta_max"]
    assert sigma_beta["sigma_beta_min"] < sigma_beta["sigma_beta_max"]
    assert sigma_beta["look_elsewhere_trials"] >= 1
    assert "proxy_lnb_definition" in sigma_beta

    occupancy = payload["assets"]["E3_per_channel_occupancy"]["statistics"]
    channels = occupancy["channel_occupancy"]
    assert {row["channel"] for row in channels} == {
        "shear",
        "vorticity",
        "tilt",
        "anisotropic curvature",
    }
    assert all(0.0 <= row["occupancy"] <= 1.0 for row in channels)
    assert all(row["denominator_policy"] == "channel_matched" for row in channels)
    assert occupancy["negative_components_allowed"] is False
    assert occupancy["posterior_compatible"] is False
    assert occupancy["evidence_compatible"] is False
    assert occupancy["truth_certificate"] is False

    diagnostics = payload["method_diagnostics"]
    assert diagnostics["finite_mock"]["owner"] == "HTT"
    assert diagnostics["finite_mock"]["claim_tier"] == "diagnostic_only"
    assert diagnostics["finite_mock"]["exact_zero_trigger_upper_bound_at_observed_n"] == pytest.approx(
        fpr["exact_zero_trigger_upper_bound_at_observed_n"]
    )
    assert "not zero false-positive rate" in diagnostics["finite_mock"]["caveats"]
    assert diagnostics["nuisance_rank"]["owner"] == "HTT"
    assert (
        diagnostics["nuisance_rank"]["projected_rank"]
        <= diagnostics["nuisance_rank"]["target_dimension"]
    )
    fisher = diagnostics["fisher_compression"]
    assert fisher["owner"] == "HTT"
    assert fisher["full_fisher"][0][0] == pytest.approx(1.0)
    assert fisher["diagonal_fisher"][0][0] == pytest.approx(0.0)
    channel = diagnostics["channel_occupancy"]
    assert channel["owner"] == "MIO"
    assert channel["posterior_compatible"] is False
    assert channel["evidence_compatible"] is False
    stability = diagnostics["evidence_stability"]
    assert stability["owner"] == "BASS"
    assert stability["claim_tier"] == "diagnostic_only"
    assert stability["transfer_conditional"] is True
    assert stability["native_solver_result"] is False
    assert stability["bound_status"] == "not_evaluated_missing_loglike_delta"
    assert stability["required_input_kind"] == "max_loglike_delta"
    assert stability["rejected_proxy_input_kind"] == "denominator_relative_shift"
    assert stability["evidence_shift_upper_bound"] is None
    assert "not native solver validation" in stability["caveats"]
    for row in diagnostics.values():
        assert row["implementation_scope"]
        assert row["config_hash"].startswith("sha256:")
        assert row["input_hashes"]
        assert row["sky_support_status"]
        assert row["null_mock_status"]
        assert row["generating_command"]
        assert row["git_commit_or_worktree_state"]


def test_revision_generator_occupancy_fails_closed_without_clipping(monkeypatch, tmp_path):
    import scripts.generate_revision_experiment_assets as generator

    inputs = generator.RepoInputs(
        inventory={"rows": [{"collection": "test", "present": True}]},
        longrun=None,
        science_payload=None,
    )
    monkeypatch.setattr(generator, "_q_center", lambda _payload: -1.0)

    with pytest.raises(ValueError, match="numerator"):
        generator._plot_per_channel_occupancy(inputs, tmp_path / "occupancy.png")


def test_revision_latex_snippets_respect_manifest_lanes():
    main = MAIN_SNIPPET.read_text(encoding="utf-8")
    appendix = APPENDIX_SNIPPET.read_text(encoding="utf-8")
    external = EXTERNAL_AUDIT_SNIPPET.read_text(encoding="utf-8")

    assert "fig_revision_tomographic_forecast" in main
    assert "fig_revision_prior_support_surface" not in main
    assert "fig_revision_sigma_beta_band" not in main
    assert "fig_revision_per_channel_occupancy" not in main
    assert "fig_revision_rule_of_three_fpr" not in main

    assert "fig_revision_prior_support_surface" in appendix
    assert "fig_revision_sigma_beta_band" in appendix
    assert "fig_revision_per_channel_occupancy" in appendix
    assert "fig_revision_rule_of_three_fpr" not in appendix

    assert "fig_revision_rule_of_three_fpr" in external
    assert "not input by the manuscript" in external
