"""PR-145 contract tests: CF4 velocity estimator mechanics."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from obsstat.cf4_velocity_estimators import (
    Cf4Sample,
    VelocityEstimatorError,
    _chi2_sf,
    compare_vectors,
    coverage_injection,
    eight_region_partition,
    estimate,
    full_covariance_significance,
    generate_caption,
    lint_caption,
    load_sample,
    refuse_cf4_p0_closure,
    refuse_constrained_median_as_truth,
    refuse_scalar_amplitude_overlap,
    require_coverage_in_band,
    require_eight_region_label,
    require_full_covariance_significance,
    subsample,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
GROUPS = REPO_ROOT / "workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz"
needs_data = pytest.mark.skipif(not GROUPS.is_file(),
                                reason="CF4 groups npz absent")


def test_chi2_sf_matches_scipy() -> None:
    from scipy import stats
    for x, k in ((3.0, 3), (8.0, 3), (1.0, 3), (0.3, 3), (12.0, 4)):
        assert abs(_chi2_sf(x, k) - float(stats.chi2.sf(x, k))) < 1e-6


def test_guards() -> None:
    with pytest.raises(VelocityEstimatorError, match="noise-only"):
        require_full_covariance_significance("noise_only")
    require_full_covariance_significance("full_covariance")   # fine
    with pytest.raises(VelocityEstimatorError, match="scalar amplitude"):
        refuse_scalar_amplitude_overlap("scalar_amplitude_overlap")
    with pytest.raises(VelocityEstimatorError, match="not the truth"):
        refuse_constrained_median_as_truth("constrained_median_truth")
    with pytest.raises(VelocityEstimatorError, match="PR-157"):
        refuse_cf4_p0_closure("cf4_p0_closed")
    with pytest.raises(VelocityEstimatorError, match="eight-region"):
        require_eight_region_label("octant_subset")
    require_eight_region_label("eight_region_partition")   # fine


def test_rank_deficient_refuses_point_estimate() -> None:
    n = np.tile(np.array([0.0, 0.0, 1.0]), (5, 1))
    s = Cf4Sample(n=n, v=np.ones(5), w=np.ones(5), sig_v=np.ones(5),
                  pos_hmpc=n * 10.0)
    with pytest.raises(VelocityEstimatorError, match="rank-deficient"):
        estimate(s, monopole=False, label="degenerate")


def test_caption_gate() -> None:
    text = generate_caption(300.0, 8.0, 1.0)
    lint_caption(text)
    for bad in (" the constrained median is " + "the truth.",
                " the formal significance is " + "the result.",
                " scalar amplitude overlap is " + "the comparison."):
        with pytest.raises(VelocityEstimatorError, match="forbidden"):
            lint_caption(text + bad)


@needs_data
def test_full_covariance_deflates_significance() -> None:
    full = load_sample(GROUPS)
    sub = subsample(full, 3000, 20260718)
    result = estimate(sub, monopole=False, label="bulk_flow_wls")
    sig = full_covariance_significance(result)
    # the amplitude is a physically plausible few-hundred km/s, NOT 405
    assert 150.0 < sig["amplitude_kms"] < 400.0
    # the cosmic-variance covariance strictly deflates the significance
    assert sig["full_covariance_sigma"] < sig["noise_only_sigma"]
    assert sig["full_covariance_sigma"] < 3.0   # honest, not the over-claim


@needs_data
def test_constrained_estimator_and_vector_comparison() -> None:
    full = load_sample(GROUPS)
    sub = subsample(full, 3000, 20260718)
    wls = estimate(sub, monopole=False, label="bulk_flow_wls")
    constrained = estimate(sub, monopole=True, label="flow_plus_monopole")
    assert constrained.coeffs.shape == (4,)   # flow (3) + monopole (1)
    cmp = compare_vectors(wls, constrained)
    # the flow and flow+monopole estimators are consistent as vectors
    assert cmp["consistency_sigma"] < 3.0


@needs_data
def test_coverage_full_vs_noise_only_discrimination() -> None:
    full = load_sample(GROUPS)
    sub = subsample(full, 800, 20260719)
    cov = coverage_injection(sub, [120.0, -80.0, 60.0], 40.0, n_inj=200,
                             seed=20260719)
    require_coverage_in_band(cov, 0.68, 0.09)
    require_coverage_in_band(cov, 0.95, 0.06)
    # the noise-only covariance UNDER-covers (the concrete P0 failure)
    assert max(cov["coverage_68_noise_only"]) < 0.60


@needs_data
def test_partition_requires_supergalactic_frame() -> None:
    full = load_sample(GROUPS)
    part = eight_region_partition(subsample(full, 3000, 20260718))
    assert "SGX_SGY_SGZ" in part["scheme"]
    # a sample without the supergalactic columns is refused (not equatorial)
    sub = subsample(full, 100, 1)
    stripped = Cf4Sample(n=sub.n, v=sub.v, w=sub.w, sig_v=sub.sig_v,
                         pos_hmpc=sub.pos_hmpc, sg=None)
    with pytest.raises(VelocityEstimatorError, match="supergalactic"):
        eight_region_partition(stripped)


@needs_data
def test_eight_region_partition() -> None:
    full = load_sample(GROUPS)
    part = eight_region_partition(subsample(full, 3000, 20260718))
    assert part["n_regions"] == 8
    assert part["min_count"] > 0   # all eight regions populated


@needs_data
def test_runner_check_mode_is_current() -> None:
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT / "scripts/codex_harness/run_pr145_velocity_estimators.py"),
         "--check"], cwd=REPO_ROOT, capture_output=True, text=True,
        check=False)
    assert result.returncode == 0, result.stdout + result.stderr


@needs_data
def test_artifacts_and_mutations() -> None:
    bf = json.loads((REPO_ROOT / "docs/generated/pr145_bulk_flow_report.json")
                    .read_text(encoding="utf-8"))
    assert bf["full_covariance_sigma"] < bf["noise_only_sigma"]
    assert abs(bf["amplitude_kms"] - 405.0) > 1.0
    p0 = json.loads(
        (REPO_ROOT / "docs/generated/pr145_p0_remediation_candidates.json")
        .read_text(encoding="utf-8"))
    assert all(c["status"] == "OPEN" for c in p0["candidates"])
    assert all(c["disposition"] == "remediation_candidate"
               for c in p0["candidates"])
    # the C3 candidate honestly scopes out the un-implemented ML branch
    c3 = next(c for c in p0["candidates"]
              if c["finding_id"] == "C3-K5-VCORR-ML-F1")
    assert "does NOT implement" in c3["scope_note"]
    report = json.loads(
        (REPO_ROOT / "docs/generated/pr145_mutation_report.json")
        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 6
    manifest = json.loads(
        (REPO_ROOT / "docs/generated/pr145_artifact_manifest.json")
        .read_text(encoding="utf-8"))
    assert manifest["raw_data_pins"]["groups_sha256"]
