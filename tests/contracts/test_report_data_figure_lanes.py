from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from common.artifact_manifest import validate_manifest_payload


REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "figures" / "data_analysis_current"
META_DIR = REPO_ROOT / "figures" / "quarantined_meta" / "v6_no_download"
LEGACY_ROOT_DIR = REPO_ROOT / "figures" / "quarantined_legacy" / "root_sources"
PACK_JSON = REPO_ROOT / "docs" / "generated" / "report_data_analysis_figure_pack.json"
PACK_MD = REPO_ROOT / "docs" / "generated" / "report_data_analysis_figure_pack.md"

EXPECTED_DATA_FIGURES = (
    "fig_data_planck_tt_binned_residual.png",
    "fig_data_planck_smica_masked_temperature.png",
    "fig_data_cf4_catalog_sky_velocity.png",
    "fig_data_cf4_depth_velocity_profile.png",
    "fig_data_k5_cf4_bulk_flow_coverage.png",
    "fig_data_k6_cf4_wf_curl_shear_diagnostic.png",
    "fig_data_compact_cmb_high_ell_products.png",
    "fig_data_compact_lensing_bandpower_covariance.png",
    "fig_data_act_dr6_lensing_noise_systematics.png",
    "fig_data_desi_bgs_cf4_targets.png",
    "fig_data_desi_redshift_jackknife_ridge.png",
    "fig_data_desi_ngc_sgc_asymmetry_surface.png",
    "fig_data_desi_tracer_handoff_continuity.png",
    "fig_data_cf4_radial_velocity_sign_transition.png",
    "fig_data_cf4_radial_delta_stability.png",
    "fig_data_cf4_forward_coverage_residual.png",
    "fig_data_cf4_depth_apex_phase_portrait.png",
    "fig_data_cf4_shell_apex_separation_matrix.png",
    "fig_data_k5_cf4_vs_affine_consistency.png",
    "fig_data_cf4_affine_gradient_spectrum.png",
    "fig_data_k1_lowell_tensor_conditioning.png",
    "fig_data_k1_maxscan_waterfall.png",
    "fig_data_k1_scalar_biposh_map_stability.png",
    "fig_data_observed_sector_response_vector.png",
    "fig_data_k1_k5_joint_diagnostic_axes.png",
)


def _read_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_root_figures_are_relocated_into_subfolders() -> None:
    root_figures = sorted(
        path.name
        for path in (REPO_ROOT / "figures").iterdir()
        if path.is_file() and path.suffix.lower() in {".png", ".pdf", ".svg", ".jpg", ".jpeg"}
    )

    assert root_figures == []
    assert len(list(LEGACY_ROOT_DIR.glob("fig_*.png"))) >= 70
    assert len(list(LEGACY_ROOT_DIR.glob("fig_*.manifest.json"))) >= 70
    assert not (REPO_ROOT / "figures" / "v6_no_download").exists()
    assert len(list(META_DIR.glob("fig_v6_*.png"))) == 5


def test_conditioned_legacy_manifests_point_to_relocated_root_sources() -> None:
    manifests = sorted((REPO_ROOT / "figures" / "conditioned_legacy").glob("root__*.manifest.json"))
    assert len(manifests) >= 70

    for manifest_path in manifests:
        payload = _read_json(manifest_path)
        legacy_source = payload["statistics_definitions"]["legacy_source_path"]
        assert legacy_source.startswith("figures/quarantined_legacy/root_sources/")
        assert (REPO_ROOT / legacy_source).is_file()
        assert any(
            row.startswith(f"{legacy_source}:sha256:")
            for row in payload["input_hashes"]
        )


def test_relocated_root_sources_have_internal_only_manifests() -> None:
    for figure_path in sorted(LEGACY_ROOT_DIR.glob("fig_*.png")):
        sidecar = figure_path.with_suffix("").with_name(figure_path.stem + ".manifest.json")
        assert sidecar.is_file()
        manifest = _read_json(sidecar)
        rel_path = figure_path.relative_to(REPO_ROOT).as_posix()
        issues = validate_manifest_payload(
            manifest,
            manifest_path=sidecar.relative_to(REPO_ROOT),
            expected_artifact_path=rel_path,
        )
        assert issues == ()
        assert manifest["artifact_mode"] == "internal_exploratory"
        assert manifest["allowed_use"] == "internal_only"
        assert manifest["statistics_definitions"]["figure_lane"] == "quarantined_legacy_root_source"


def test_report_data_analysis_figures_are_actual_data_not_meta_surfaces() -> None:
    pack = _read_json(PACK_JSON)

    assert pack["owner"] == "OBSSTAT"
    assert pack["claim_tier"] == "diagnostic_only"
    assert pack["figure_lane"] == "report_data_analysis_current"
    assert [row["file_name"] for row in pack["figures"]] == list(EXPECTED_DATA_FIGURES)
    assert len(pack["skipped_current_data_candidates"]) >= 4
    assert PACK_MD.is_file()

    banned_meta_terms = (
        "claim gate",
        "claim-gate",
        "adversarial audit",
        "self-review",
        "dag progress",
        "readiness",
        "figure governance",
        "blocker discharge",
    )
    rendered = PACK_MD.read_text(encoding="utf-8").lower()
    for term in banned_meta_terms:
        assert term not in rendered

    for file_name in EXPECTED_DATA_FIGURES:
        figure_path = DATA_DIR / file_name
        sidecar = figure_path.with_suffix("").with_name(figure_path.stem + ".manifest.json")
        assert figure_path.is_file()
        assert figure_path.stat().st_size > 3000
        assert sidecar.is_file()
        manifest = _read_json(sidecar)
        rel_path = figure_path.relative_to(REPO_ROOT).as_posix()
        issues = validate_manifest_payload(
            manifest,
            manifest_path=sidecar.relative_to(REPO_ROOT),
            expected_artifact_path=rel_path,
        )
        assert issues == ()
        assert manifest["artifact_mode"] == "paper_appendix_conditioned"
        assert manifest["allowed_use"] == "paper_appendix"
        assert manifest["statistics_definitions"]["figure_lane"] == "report_data_analysis_current"
        assert any(row.startswith("workdir/") for row in manifest["input_hashes"])

    k5 = _read_json(DATA_DIR / "fig_data_k5_cf4_bulk_flow_coverage.manifest.json")
    assert "docs/generated/k5_cf4_release_coverage.json" in k5["statistics_definitions"]["source_artifacts"]
    assert k5["statistics_definitions"]["measured_bulk_amplitude_kms"] > 300.0
    assert k5["statistics_definitions"]["measurement_only_coverage"] < 0.5
    assert 0.60 <= k5["statistics_definitions"]["cosmic_variance_inclusive_coverage"] <= 0.76

    k6 = _read_json(DATA_DIR / "fig_data_k6_cf4_wf_curl_shear_diagnostic.manifest.json")
    assert "docs/generated/k6_cf4_curl_posterior.json" in k6["statistics_definitions"]["source_artifacts"]
    assert k6["statistics_definitions"]["structural_no_go"] is True
    assert k6["statistics_definitions"]["physical_vorticity_identifiable"] is False
    assert k6["statistics_definitions"]["vorticity_over_shear_ratio_max"] < 0.01
    assert k6["transfer_source"] == "external_proxy_cf4_wf_reconstruction"


def test_report_data_figure_generator_check_mode_is_current() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "make_report_data_analysis_figures.py"),
            "--check",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_figure_lane_curator_check_mode_is_current() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "curate_figure_lanes.py"),
            "--check",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
