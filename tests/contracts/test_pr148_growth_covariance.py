"""PR-148 contract tests: depth-resolved fsigma8 + same-data joint covariance."""
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

from obsstat.cf4_growth_covariance import (
    GrowthCovarianceError,
    amplitude_mle,
    classify_constrained,
    depth_shell_preps,
    fiducial_fsigma8,
    fsigma8_by_depth,
    generate_caption,
    growth_difference_bound,
    held_out_depth_prediction,
    joint_covariance,
    lint_caption,
    refuse_anomaly_claim,
    refuse_cf4_p0_closure,
    refuse_correlation_endpoint_selection,
    refuse_shell_bias_single_point,
    refuse_target_tension_sigma,
    require_positive_definite,
    shell_edge_stability,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
GROUPS = REPO_ROOT / "workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz"
needs_data = pytest.mark.skipif(not GROUPS.is_file(),
                                reason="CF4 groups npz absent")


def _load_runner():
    runner_path = (
        REPO_ROOT / "scripts/codex_harness/run_pr148_growth_covariance.py"
    )
    spec = importlib.util.spec_from_file_location("run_pr148", runner_path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def test_relocated_sources_are_generation_time_provenance() -> None:
    runner = _load_runner()
    aliases = runner.SOURCE_ALIASES
    historical_source = "htt/src/common/cf4_growth_covariance.py"
    current_source = aliases[historical_source]
    stored_result = {
        "negative_scan": {
            "targets": {
                historical_source: {"sha256": "1" * 64, "hits": []},
            },
        },
    }
    current_result = {
        "negative_scan": {
            "targets": {
                current_source: {"sha256": "2" * 64, "hits": []},
            },
        },
    }
    result_rel = runner.OUTPUTS["fsigma8"]
    assert runner._semantic_artifact(
        result_rel, stored_result
    ) == runner._semantic_artifact(result_rel, current_result)
    current_result["negative_scan"]["targets"][current_source]["hits"] = [
        {"line": 1},
    ]
    assert runner._semantic_artifact(
        result_rel, stored_result
    ) != runner._semantic_artifact(result_rel, current_result)

    stored_manifest = {
        "input_hashes": [
            f"{historical}:{'1' * 64}" for historical in aliases
        ],
        "raw_data_pins": {"groups_sha256": "groups"},
    }
    current_manifest = {
        "input_hashes": [
            f"{current}:{'2' * 64}" for current in aliases.values()
        ],
        "raw_data_pins": {"groups_sha256": "groups"},
    }
    manifest_rel = runner.OUTPUTS["manifest"]
    assert runner._semantic_artifact(
        manifest_rel, stored_manifest
    ) == runner._semantic_artifact(manifest_rel, current_manifest)
    current_manifest["raw_data_pins"]["groups_sha256"] = "changed"
    assert runner._semantic_artifact(
        manifest_rel, stored_manifest
    ) != runner._semantic_artifact(manifest_rel, current_manifest)
    current_manifest["raw_data_pins"]["groups_sha256"] = "groups"
    current_manifest["input_hashes"][0] = f"{current_source}:not-a-sha"
    assert runner._semantic_artifact(
        manifest_rel, stored_manifest
    ) != runner._semantic_artifact(manifest_rel, current_manifest)


def test_guards() -> None:
    with pytest.raises(GrowthCovarianceError, match="tension"):
        refuse_target_tension_sigma("target_tension_sigma")
    refuse_target_tension_sigma("report_measured_bound")   # fine
    with pytest.raises(GrowthCovarianceError, match="correlation endpoint"):
        refuse_correlation_endpoint_selection("correlation_zero")
    with pytest.raises(GrowthCovarianceError, match="one weighted point"):
        refuse_shell_bias_single_point("single_weighted_point")
    with pytest.raises(GrowthCovarianceError, match="anomaly"):
        refuse_anomaly_claim("growth_anomaly")
    with pytest.raises(GrowthCovarianceError, match="PR-157"):
        refuse_cf4_p0_closure("cf4_p0_closed")


def test_require_positive_definite() -> None:
    require_positive_definite({
        "positive_definite": True,
        "joint_covariance": np.eye(2).tolist(),
    })
    with pytest.raises(GrowthCovarianceError, match="not identified"):
        require_positive_definite({"positive_definite": False})


@pytest.mark.parametrize("report, message", [
    ({"positive_definite": True}, "must include a finite real square"),
    (
        {
            "positive_definite": True,
            "joint_covariance": [[1.0, 2.0], [2.0, 1.0]],
        },
        "not positive-definite",
    ),
    (
        {
            "positive_definite": True,
            "joint_covariance": [[1.0, np.nan], [np.nan, 1.0]],
        },
        "finite real square",
    ),
    (
        {
            "positive_definite": True,
            "joint_covariance": [[2.0, 3.0], [0.0, 2.0]],
        },
        "not symmetric",
    ),
])
def test_positive_definite_guard_recomputes_matrix_evidence(
    report: dict, message: str
) -> None:
    with pytest.raises(GrowthCovarianceError, match=message):
        require_positive_definite(report)


@pytest.mark.parametrize("sigma, threshold, message", [
    ([-0.1], 0.5, "finite non-negative"),
    ([0.1, 0.2], 0.5, "one finite non-negative"),
    ([0.1], float("nan"), "finite and positive"),
])
def test_constrained_classification_rejects_invalid_inputs(
    sigma, threshold: float, message: str
) -> None:
    fs8 = {"fiducial_fsigma8": 0.43, "shells": [{"shell": 0}]}
    with pytest.raises(GrowthCovarianceError, match=message):
        classify_constrained(
            fs8,
            {"sigma": sigma},
            constrained_rel_err=threshold,
        )


@pytest.mark.parametrize("n_mock", [0, 1, 3, True, 3.5])
def test_joint_covariance_requires_enough_mock_realisations(
    n_mock,
) -> None:
    with pytest.raises(GrowthCovarianceError, match="greater than"):
        joint_covariance(
            None,
            [None, None, None],
            n_mock=n_mock,
            seed=1,
        )


def test_growth_difference_nonidentified_when_endpoint_unconstrained() -> None:
    fs8 = {"fiducial_fsigma8": 0.43,
           "shells": [{"shell": 0, "fsigma8": 0.4, "constrained": True,
                       "mock_sigma": 0.09},
                      {"shell": 1, "fsigma8": 0.6, "constrained": False},
                      {"shell": 2, "fsigma8": 1.2, "constrained": False}]}
    cov = {"joint_covariance": np.diag([0.01, 0.1, 0.3]).tolist(),
           "mock_diff_deepest_minus_nearest": np.linspace(-1, 1, 50).tolist()}
    g = growth_difference_bound(fs8, cov, comparator=0.43, comparator_sigma=0.02)
    assert g["growth_difference_identified"] is False
    assert g["n_constrained_shells"] == 1
    assert g["depth_dependence_verdict"] == "non_identified"
    assert g["empirical_p_interpretable"] is False
    # a same-data comparator would require the cross covariance
    assert g["shared_data_comparator_would_require_cross_covariance"][
        "cross_covariance_is_mandatory_for_shared_data"]


def test_caption_gate() -> None:
    fs8 = {"shells": [{"constrained": True}, {"constrained": False}]}
    cov = {"max_off_diagonal_correlation": 0.02}
    growth = {"depth_dependence_verdict": "non_identified",
              "empirical_p_interpretable": False,
              "empirical_mock_tail_p_value": 0.5}
    text = generate_caption(fs8, cov, growth)
    lint_caption(text)
    for bad in (" targets the " + "tension sigma.",
                " growth anomaly " + "detected.",
                " cf4 p0 " + "closed."):
        with pytest.raises(GrowthCovarianceError, match="forbidden"):
            lint_caption(text + bad)


@needs_data
def test_amplitude_mle_converges_on_deep_shell() -> None:
    # the safeguarded bracketing solve returns the SAME amplitude regardless of
    # the internal cap (no chaotic non-convergence like the old Newton loop)
    sub, _, _, preps = depth_shell_preps(GROUPS, subsample=1200, seed=20260723,
                                         n_shells=3)
    a1, _ = amplitude_mle(preps[-1].sample.v, preps[-1])
    a2, _ = amplitude_mle(preps[-1].sample.v, preps[-1], a_cap=1.0e6)
    assert abs(a1 - a2) < 1e-3            # converged, not a truncated iterate


@needs_data
def test_only_nearest_shell_constrains_fsigma8() -> None:
    sub, _, _, preps = depth_shell_preps(GROUPS, subsample=1200, seed=20260723,
                                         n_shells=3)
    fr = fsigma8_by_depth(preps)
    cov = joint_covariance(sub, preps, n_mock=200, seed=999)
    classify_constrained(fr, cov, constrained_rel_err=0.5)
    # the nearest shell constrains fsigma8 consistent with the LambdaCDM value
    assert fr["shells"][0]["constrained"]
    assert 0.2 < fr["shells"][0]["fsigma8"] < 0.7
    # the deep shells are noise-dominated and unconstrained (mock-sigma based)
    assert sum(r["constrained"] for r in fr["shells"]) < 3


@needs_data
def test_joint_covariance_is_measured_and_psd() -> None:
    sub, _, _, preps = depth_shell_preps(GROUPS, subsample=1200, seed=20260723,
                                         n_shells=3)
    cov = joint_covariance(sub, preps, n_mock=200, seed=999)
    require_positive_definite(cov)
    assert cov["positive_definite"]
    # measured, reported as found (here near-diagonal) not assumed
    assert cov["max_off_diagonal_correlation"] < 0.5


@needs_data
def test_growth_difference_is_a_bound_not_a_detection() -> None:
    sub, _, _, preps = depth_shell_preps(GROUPS, subsample=1200, seed=20260723,
                                         n_shells=3)
    fr = fsigma8_by_depth(preps)
    cov = joint_covariance(sub, preps, n_mock=200, seed=999)
    classify_constrained(fr, cov, constrained_rel_err=0.5)
    g = growth_difference_bound(fr, cov, comparator=0.43, comparator_sigma=0.02)
    # only one shell constrains fsigma8 -> the growth difference is not identified
    assert g["growth_difference_identified"] is False
    assert g["depth_dependence_verdict"] == "non_identified"
    assert g["empirical_p_interpretable"] is False


@needs_data
def test_held_out_and_stability() -> None:
    sub, _, _, preps = depth_shell_preps(GROUPS, subsample=1200, seed=20260723,
                                         n_shells=3)
    fr = fsigma8_by_depth(preps)
    cov = joint_covariance(sub, preps, n_mock=200, seed=999)
    ho = held_out_depth_prediction(fr, cov)
    assert len(ho["shells"]) == 3
    stab = shell_edge_stability(GROUPS, subsample=1200, seed=20260723,
                                n_shells=3, jitter_fractions=[0.9, 1.0, 1.1],
                                constrained_rel_err=0.5)
    # the nearest constrained shell is stable under the pre-registered jitter
    assert stab["nearest_shell_spread"] < 0.1


@needs_data
def test_runner_check_mode_is_current() -> None:
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT / "scripts/codex_harness/run_pr148_growth_covariance.py"),
         "--check"], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr


@needs_data
def test_artifacts_and_mutations() -> None:
    growth = json.loads(
        (REPO_ROOT / "docs/generated/pr148_growth_difference_bound.json")
        .read_text(encoding="utf-8"))
    assert growth["growth_difference_identified"] is False
    cov = json.loads((REPO_ROOT / "docs/generated/pr148_joint_covariance.json")
                     .read_text(encoding="utf-8"))
    assert cov["positive_definite"]
    p0 = json.loads(
        (REPO_ROOT / "docs/generated/pr148_p0_remediation_candidates.json")
        .read_text(encoding="utf-8"))
    assert all(c["status"] == "OPEN" for c in p0["candidates"])
    report = json.loads((REPO_ROOT / "docs/generated/pr148_mutation_report.json")
                        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 6
    manifest = json.loads(
        (REPO_ROOT / "docs/generated/pr148_artifact_manifest.json")
        .read_text(encoding="utf-8"))
    assert manifest["raw_data_pins"]["groups_sha256"]
