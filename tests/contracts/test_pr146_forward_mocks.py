"""PR-146 contract tests: CF4 catalogue forward-mock simulator."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import warnings
from pathlib import Path

import numpy as np
import pytest

warnings.filterwarnings("ignore")

from obsstat.cf4_forward_simulator import (
    BoxGrfConfig,
    ForwardSimulatorError,
    RealismConfig,
    band_limited_sigma_v,
    build_cholesky_generator,
    coverage_in_band,
    covariance_uncertainty,
    effective_n_modes,
    forward_mock_coverage,
    generate_caption,
    lint_caption,
    load_sample_and_meta,
    per_depth_coverage,
    realism_from_variant,
    refuse_box_grf_for_covariance,
    refuse_cf4_p0_closure,
    refuse_k6_rebind,
    refuse_rare_tail_without_coverage,
    refuse_same_box_octant_independence,
    refuse_wf_mean_as_ensemble,
    require_idealised_covers,
    subsample_with_meta,
    verify_cholesky_generator,
    verify_independent_reference,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
GROUPS = REPO_ROOT / "workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz"
needs_data = pytest.mark.skipif(not GROUPS.is_file(),
                                reason="CF4 groups npz absent")


def _load_runner():
    runner_path = (
        REPO_ROOT / "scripts/codex_harness/run_pr146_forward_mocks.py"
    )
    spec = importlib.util.spec_from_file_location("run_pr146", runner_path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def test_relocated_sources_are_generation_time_provenance() -> None:
    runner = _load_runner()
    aliases = runner.SOURCE_ALIASES
    historical_simulator = "htt/src/common/cf4_forward_simulator.py"
    current_simulator = aliases[historical_simulator]
    stored_card = {
        "negative_scan": {
            "targets": {
                historical_simulator: {"sha256": "1" * 64, "hits": []},
            },
        },
    }
    current_card = {
        "negative_scan": {
            "targets": {
                current_simulator: {"sha256": "2" * 64, "hits": []},
            },
        },
    }
    card_rel = runner.OUTPUTS["card"]
    assert runner._semantic_artifact(
        card_rel, stored_card
    ) == runner._semantic_artifact(card_rel, current_card)
    current_card["negative_scan"]["targets"][current_simulator]["hits"] = [
        {"line": 1},
    ]
    assert runner._semantic_artifact(
        card_rel, stored_card
    ) != runner._semantic_artifact(card_rel, current_card)

    stored_manifest = {
        "input_hashes": [
            f"{historical}:{'1' * 64}" for historical in aliases
        ],
        "raw_data_pins": {"groups_sha256": "raw"},
    }
    current_manifest = {
        "input_hashes": [
            f"{current}:{'2' * 64}" for current in aliases.values()
        ],
        "raw_data_pins": {"groups_sha256": "raw"},
    }
    manifest_rel = runner.OUTPUTS["manifest"]
    assert runner._semantic_artifact(
        manifest_rel, stored_manifest
    ) == runner._semantic_artifact(manifest_rel, current_manifest)
    current_manifest["raw_data_pins"]["groups_sha256"] = "changed"
    assert runner._semantic_artifact(
        manifest_rel, stored_manifest
    ) != runner._semantic_artifact(manifest_rel, current_manifest)
    current_manifest["raw_data_pins"]["groups_sha256"] = "raw"
    current_manifest["input_hashes"][0] = f"{current_simulator}:not-a-sha"
    assert runner._semantic_artifact(
        manifest_rel, stored_manifest
    ) != runner._semantic_artifact(manifest_rel, current_manifest)


def test_guards() -> None:
    with pytest.raises(ForwardSimulatorError, match="independent mocks"):
        refuse_same_box_octant_independence("same_box_octants")
    refuse_same_box_octant_independence("independent_realisations")   # fine
    with pytest.raises(ForwardSimulatorError, match="Wiener-filter"):
        refuse_wf_mean_as_ensemble("wf_mean")
    with pytest.raises(ForwardSimulatorError, match="K6"):
        refuse_k6_rebind("k6_rebind")
    with pytest.raises(ForwardSimulatorError, match="rare-tail"):
        refuse_rare_tail_without_coverage(False, "rare_tail")
    refuse_rare_tail_without_coverage(True, "mechanics")   # fine
    with pytest.raises(ForwardSimulatorError, match="PR-157"):
        refuse_cf4_p0_closure("cf4_p0_closed")
    with pytest.raises(ForwardSimulatorError, match="finite-box"):
        refuse_box_grf_for_covariance("covariance")
    refuse_box_grf_for_covariance("diagonal_variance_reference")   # fine


@pytest.mark.parametrize("report, message", [
    (
        {
            "variant": "idealised",
            "labels": [],
            "coverage_68": [],
            "coverage_95": [],
            "coverage_68_noise_only": [0.0],
        },
        "one value for every unique component",
    ),
    (
        {
            "variant": "idealised",
            "labels": ["Bx", "By"],
            "coverage_68": [0.68],
            "coverage_95": [0.95],
            "coverage_68_noise_only": [0.0],
        },
        "one value for every unique component",
    ),
    (
        {
            "variant": "idealised",
            "labels": ["Bx"],
            "coverage_68": [1.1],
            "coverage_95": [0.95],
            "coverage_68_noise_only": [0.0],
        },
        "finite and within",
    ),
    (
        {
            "variant": "idealised",
            "labels": ["Bx"],
            "coverage_68": [0.68],
            "coverage_95": [0.95],
            "coverage_68_noise_only": [-1.0],
        },
        "noise-only coverage",
    ),
])
def test_idealised_coverage_guard_rejects_malformed_reports(
    report: dict, message: str
) -> None:
    with pytest.raises(ForwardSimulatorError, match=message):
        require_idealised_covers(report, 0.5, 0.5)


def test_coverage_subset_must_name_observed_components() -> None:
    report = {"labels": ["Bx"], "coverage_68": [0.68]}
    with pytest.raises(ForwardSimulatorError, match="unique report labels"):
        coverage_in_band(report, 0.68, 0.1, labels=["Q"])
    assert coverage_in_band(
        report, 0.68, 0.1, labels=["Bx"]) == {"Bx": True}


def test_caption_gate() -> None:
    text = generate_caption(1.02, 82.0, 0.65)
    lint_caption(text)
    for bad in (" same-box octants are " + "independent.",
                " box grf covariance is " + "the coverage.",
                " cf4 p0 " + "closed."):
        with pytest.raises(ForwardSimulatorError, match="forbidden"):
            lint_caption(text + bad)


def test_band_limited_sigma_v_monotone() -> None:
    # a wider k-band captures at least as much velocity variance
    narrow = band_limited_sigma_v(0.005, 0.2)
    wide = band_limited_sigma_v(1e-4, 10.0)
    assert 0.0 < narrow < wide


def test_covariance_uncertainty_scales() -> None:
    assert covariance_uncertainty(200)[
        "monte_carlo_fractional_uncertainty_per_variance_element"] > \
        covariance_uncertainty(800)[
            "monte_carlo_fractional_uncertainty_per_variance_element"]


@needs_data
def test_cholesky_generator_self_consistency() -> None:
    full, meta = load_sample_and_meta(GROUPS)
    sub, _ = subsample_with_meta(full, meta, 2000, 20260718)
    gen = build_cholesky_generator(sub)
    v = verify_cholesky_generator(gen, n_real=300, seed=20260718)
    # the correlated draw reproduces the per-galaxy velocity dispersion
    assert abs(v["per_galaxy_std_kms"] / v["sigma_v_1d_kms"] - 1.0) < 0.03
    # the ensemble bulk-flow covariance matches the analytic A^-1 M A^-1
    assert all(abs(r - 1.0) < 0.5 for r in v["bulk_flow_cov_diag_ratio"])


@needs_data
def test_independent_box_reference() -> None:
    full, meta = load_sample_and_meta(GROUPS)
    sub, _ = subsample_with_meta(full, meta, 400, 20260720)
    ref = verify_independent_reference(sub, BoxGrfConfig(128, 1500.0),
                                       n_fields=16, seed=20260720)
    # an INDEPENDENT FFT path reproduces the band-limited dispersion (~1)
    assert 0.9 < ref["normalisation_ratio_box_over_band"] < 1.15
    # the finite box captures a documented fraction of the full dispersion,
    # and the deficit is dominated by sub-grid (above-Nyquist) small scales,
    # not the genuine (percent-level) super-sample piece
    assert 0.8 < ref["band_captured_fraction_sigma"] < 1.0
    assert (ref["variance_deficit_sub_grid_above_knyquist"]
            > 5.0 * ref["variance_deficit_super_sample_below_kfund"])
    # the velocity field is isotropic across components
    assert ref["component_isotropy_max_over_min"] < 1.1


@needs_data
def test_subsample_binds_pr145() -> None:
    # subsample_with_meta reproduces the PR-145 subsample index draw exactly
    from obsstat.cf4_velocity_estimators import subsample as pr145_subsample
    full, meta = load_sample_and_meta(GROUPS)
    sub, sub_meta = subsample_with_meta(full, meta, 800, 20260719)
    ref = pr145_subsample(full, 800, 20260719)
    assert np.array_equal(sub.n, ref.n)
    assert len(sub_meta.dist) == 800


@needs_data
def test_idealised_covers_and_noise_under_covers() -> None:
    full, meta = load_sample_and_meta(GROUPS)
    sub, sub_meta = subsample_with_meta(full, meta, 800, 20260719)
    cov = forward_mock_coverage(sub, sub_meta, [120.0, -80.0, 60.0], 40.0,
                                RealismConfig(), n_mock=200, seed=20260719)
    require_idealised_covers(cov, 0.09, 0.06)
    assert max(cov["coverage_68_noise_only"]) < 0.60


@needs_data
def test_nongaussian_distance_error_biases_monopole() -> None:
    # the honest realism finding: a lognormal distance error under-covers the
    # radial monopole (a Malmquist bias the Gaussian covariance misses)
    full, meta = load_sample_and_meta(GROUPS)
    sub, sub_meta = subsample_with_meta(full, meta, 800, 20260719)
    cov = forward_mock_coverage(
        sub, sub_meta, [120.0, -80.0, 60.0], 40.0,
        realism_from_variant("nongaussian_distance_error"),
        n_mock=200, seed=20260719)
    monopole_68 = cov["coverage_68"][cov["labels"].index("M")]
    assert monopole_68 < 0.5   # the monopole is not covered — reported openly


@needs_data
def test_effective_n_is_far_below_n() -> None:
    full, meta = load_sample_and_meta(GROUPS)
    sub, _ = subsample_with_meta(full, meta, 800, 20260719)
    en = effective_n_modes(sub)
    # far fewer independent modes than groups -> same-box regions not independent
    assert en["field_participation_ratio"] < 0.5 * en["n_galaxies"]
    assert 1.0 <= en["bulk_flow_participation_ratio"] <= 3.0


@needs_data
def test_per_depth_discloses_least_favourable_shell() -> None:
    full, meta = load_sample_and_meta(GROUPS)
    sub, sub_meta = subsample_with_meta(full, meta, 800, 20260719)
    depth = per_depth_coverage(sub, sub_meta, [120.0, -80.0, 60.0], 40.0,
                               n_shells=3, n_mock=120, seed=20260721)
    assert depth["n_shells"] == 3
    assert 0 <= depth["least_favourable_shell"] < 3
    assert "Bonferroni" in depth["family_wise_note"]


@needs_data
def test_runner_check_mode_is_current() -> None:
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT / "scripts/codex_harness/run_pr146_forward_mocks.py"),
         "--check"], cwd=REPO_ROOT, capture_output=True, text=True,
        check=False)
    assert result.returncode == 0, result.stdout + result.stderr


@needs_data
def test_artifacts_and_mutations() -> None:
    gen = json.loads((REPO_ROOT / "docs/generated/pr146_generator_verification.json")
                     .read_text(encoding="utf-8"))
    assert all(abs(r - 1.0) < 0.5 for r in gen["bulk_flow_cov_diag_ratio"])
    ref = json.loads((REPO_ROOT / "docs/generated/pr146_independent_reference.json")
                     .read_text(encoding="utf-8"))
    assert ref["off_diagonal_ratio_box_over_analytic_approx"] > 0.0   # documented
    card = json.loads((REPO_ROOT / "docs/generated/pr146_simulator_card.json")
                      .read_text(encoding="utf-8"))
    assert card["independent_reference"]["used_for_covariance"] is False
    assert card["independent_reference"][
        "validates_diagonal_normalisation_only"] is True
    assert "monopole" in " ".join(card["caveats"]).lower()
    p0 = json.loads(
        (REPO_ROOT / "docs/generated/pr146_p0_remediation_candidates.json")
        .read_text(encoding="utf-8"))
    assert all(c["status"] == "OPEN" for c in p0["candidates"])
    assert all(c["disposition"] == "remediation_candidate"
               for c in p0["candidates"])
    c3 = next(c for c in p0["candidates"]
              if c["finding_id"] == "C3-K5-VCORR-ML-F1")
    assert "does NOT implement" in c3["scope_note"]
    report = json.loads(
        (REPO_ROOT / "docs/generated/pr146_mutation_report.json")
        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 6
    manifest = json.loads(
        (REPO_ROOT / "docs/generated/pr146_artifact_manifest.json")
        .read_text(encoding="utf-8"))
    assert manifest["raw_data_pins"]["groups_sha256"]
