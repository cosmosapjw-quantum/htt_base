"""PR-135 contract tests: exchangeable finite-null ranking."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from common.finite_null_ranking import (
    CalibrationSplit,
    FiniteNullError,
    broken_flattened_scan_scores,
    calibration_fingerprint,
    exact_rank_distribution,
    gaussian_sigma_from_p,
    generate_caption,
    lint_caption,
    naive_zero_permitting_p,
    pooled_rank_p,
    require_identical_scoring,
    require_rowwise_reduction,
    resolution_floor,
    scan_pooled_rank_p,
    split_evaluated_rank_p,
    type_i_simulation,
    validate_reported_p,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_runner():
    path = (
        REPO_ROOT
        / "scripts/codex_harness/run_pr135_finite_null_ranking.py"
    )
    spec = importlib.util.spec_from_file_location("run_pr135", path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def test_check_normalizes_only_generation_time_source_hash() -> None:
    runner = _load_runner()
    source = runner.SOURCE_PATH
    rel = runner.OUTPUTS["estimator"]
    stored = {
        "min_p_is_nonzero": True,
        "negative_scan": {
            "targets": {
                source: {"sha256": "1" * 64, "hits": []},
            },
        },
    }
    current = json.loads(json.dumps(stored))
    current["negative_scan"]["targets"][source]["sha256"] = "2" * 64
    assert runner._semantic_artifact(
        rel, stored
    ) == runner._semantic_artifact(rel, current)
    current["min_p_is_nonzero"] = False
    assert runner._semantic_artifact(
        rel, stored
    ) != runner._semantic_artifact(rel, current)
    current["min_p_is_nonzero"] = True
    current["negative_scan"]["targets"][source]["hits"] = [{"line": 1}]
    assert runner._semantic_artifact(
        rel, stored
    ) != runner._semantic_artifact(rel, current)
    current["negative_scan"]["targets"][source]["hits"] = []
    current["negative_scan"]["targets"][source]["sha256"] = "not-a-sha"
    assert runner._semantic_artifact(
        rel, stored
    ) != runner._semantic_artifact(rel, current)

    manifest_rel = runner.OUTPUTS["manifest"]
    stored_manifest = {"input_hashes": [f"{source}:{'1' * 64}"]}
    current_manifest = {"input_hashes": [f"{source}:{'2' * 64}"]}
    assert runner._semantic_artifact(
        manifest_rel, stored_manifest
    ) == runner._semantic_artifact(manifest_rel, current_manifest)


def test_exact_discrete_estimator() -> None:
    # obs strictly largest -> p = 1/(N+1)
    assert pooled_rank_p(5.0, [1.0, 2.0, 3.0, 4.0]) == Fraction(1, 5)
    # obs at the median -> (1 + 2)/5
    assert pooled_rank_p(2.5, [1.0, 2.0, 3.0, 4.0]) == Fraction(3, 5)
    # obs smallest -> all nulls >= obs -> p = 1
    assert pooled_rank_p(0.0, [1.0, 2.0, 3.0, 4.0]) == Fraction(1)
    # fully tied -> p = 1 (conservative)
    assert pooled_rank_p(1.0, [1.0, 1.0, 1.0]) == Fraction(1)
    # never zero
    assert pooled_rank_p(5.0, [1.0, 2.0, 3.0, 4.0]) >= resolution_floor(4)


def test_non_conservative_tie_rejected() -> None:
    with pytest.raises(FiniteNullError, match="conservative"):
        pooled_rank_p(1.0, [1.0, 2.0], tie_policy="strict_gt")


@pytest.mark.parametrize("obs,nulls", [
    (float("nan"), [1.0, 2.0]),
    (float("inf"), [1.0, 2.0]),
    (True, [1.0, 2.0]),
    (1.0, [float("nan"), 2.0]),
    (1.0, [float("inf"), 2.0]),
    (1.0, [True, 2.0]),
])
def test_pooled_rank_rejects_invalid_scores(obs, nulls) -> None:
    with pytest.raises(FiniteNullError, match="finite non-boolean"):
        pooled_rank_p(obs, nulls)


@pytest.mark.parametrize("row", [
    [float("nan"), 1.0],
    [1.0, float("nan")],
    [float("inf"), 1.0],
    [True, 1.0],
])
def test_scan_rank_rejects_invalid_scores(row) -> None:
    with pytest.raises(FiniteNullError, match="finite non-boolean"):
        scan_pooled_rank_p(row, [[0.0, 1.0]])


def test_dependence_preserving_scan() -> None:
    obs = [0.4, 1.1, 0.9, 0.7, 0.5]
    nulls = [[0.3, 0.5, 0.4, 0.6, 0.2],
             [1.4, 1.2, 0.9, 1.1, 0.8],
             [0.1, 0.2, 0.15, 0.3, 0.25],
             [0.9, 1.0, 1.05, 0.95, 0.6]]
    result = scan_pooled_rank_p(obs, nulls)
    assert result["obs_score"] == 1.1
    # one null (max 1.4) exceeds obs 1.1 -> b = 1 -> p = 2/5
    assert result["p"] == Fraction(2, 5)
    assert result["scored_identically"] is True
    assert result["reduction"] == "row_wise_max"
    # a broken (wrong-length) null row is refused
    with pytest.raises(FiniteNullError, match="scan length"):
        scan_pooled_rank_p(obs, [[1.0]])
    # flattening all scan points into one iid pool is refused by the
    # row-wise reduction guard
    flattened = broken_flattened_scan_scores(nulls)
    assert len(flattened) == 20   # 4 rows x 5 points
    with pytest.raises(FiniteNullError, match="flattened"):
        require_rowwise_reduction(flattened, len(nulls))


def test_validate_reported_p_floor_gate() -> None:
    # the production gate every reported p passes: rejects the naive b/N
    # zero, accepts the (1+b)/(N+1) form
    bad = naive_zero_permitting_p(5.0, [1.0, 2.0, 3.0, 4.0])
    assert bad == Fraction(0)
    with pytest.raises(FiniteNullError, match="zero"):
        validate_reported_p(bad, 4)
    good = pooled_rank_p(5.0, [1.0, 2.0, 3.0, 4.0])
    validate_reported_p(good, 4)   # passes


def test_split_evaluated_rank_p_holds_out_calibration() -> None:
    obs = [0.4, 1.1, 0.9]
    nulls = [[2.0, 2.1, 2.2], [1.5, 1.4, 1.3],
             [0.3, 0.2, 0.1], [0.9, 0.8, 0.7]]
    split = CalibrationSplit(calibration_ids=(0, 1), evaluation_ids=(2, 3))
    result = split_evaluated_rank_p(obs, nulls, split)
    # p computed over evaluation rows (2,3) only -> N = 2
    assert result["evaluation_n_null"] == 2
    assert result["p_computed_over"] == "evaluation_rows_only"
    assert result["calibration_held_out"] == 2


def test_identical_scoring_guard() -> None:
    require_identical_scoring("max_scan", "max_scan")
    with pytest.raises(FiniteNullError, match="local observation-only"):
        require_identical_scoring("max_scan", "sum_over_scan")


def test_resolution_and_sigma_guard() -> None:
    assert resolution_floor(39) == Fraction(1, 40)
    # p at or below floor -> no sigma
    with pytest.raises(FiniteNullError, match="resolution floor"):
        gaussian_sigma_from_p(Fraction(1, 40), 39)
    with pytest.raises(FiniteNullError, match="resolution floor"):
        gaussian_sigma_from_p(Fraction(1, 100), 39)  # p < floor
    # p above the floor -> a sigma is reportable
    sig = gaussian_sigma_from_p(Fraction(1, 100), 999)
    assert 2.5 < sig < 2.6   # two-sided 0.01 -> ~2.576


def test_exact_enumeration_exercises_estimator() -> None:
    for n in (4, 8, 16):
        enum = exact_rank_distribution(n)
        # the enumerated p-values (from the ACTUAL estimator) equal the
        # grid exactly — a real enumeration, not an assumed distribution
        assert enum["enumerated_matches_grid"] is True
        assert enum["all_super_uniform"] is True
        assert enum["uniform_prob"] == str(Fraction(1, n + 1))
        assert enum["enumerated_p_values"] == sorted(enum["grid"])


def test_type_i_simulation_super_uniform_with_negative_control() -> None:
    result = type_i_simulation(39, 20000, 20260719,
                               [Fraction(1, 100), Fraction(1, 20),
                                Fraction(1, 10), Fraction(1, 4),
                                Fraction(1, 2)])
    assert result["super_uniform"] is True
    assert result["min_p_observed"] >= result["resolution_floor"] - 1e-12
    # the b/N negative control produces exact-zero p-values (caught)
    assert result["negative_control"]["caught_by_floor_gate"] is True
    assert result["negative_control"]["min_p"] <= 0.0
    # at the sub-resolution alpha the correct estimator cannot reject,
    # while the naive b/N estimator does -> the check has power
    sub = next(r for r in result["alpha_checks"] if r["sub_resolution"])
    assert sub["empirical_reject"] == 0.0
    assert sub["naive_bN_reject"] > 0.0


def test_calibration_split_and_fingerprint() -> None:
    CalibrationSplit(calibration_ids=(0, 1, 2), evaluation_ids=(3, 4, 5))
    with pytest.raises(FiniteNullError, match="overlap"):
        CalibrationSplit(calibration_ids=(0, 1, 2),
                        evaluation_ids=(2, 3, 4))
    fp1 = calibration_fingerprint("max_of_scan", "0..4", "full",
                                  "conservative_ge", 39)
    fp2 = calibration_fingerprint("max_of_scan", "0..8", "full",
                                  "conservative_ge", 39)
    assert fp1 != fp2   # scan-range change mints a new calibration id


def test_caption_gate() -> None:
    text = generate_caption(39)
    lint_caption(text)
    for suffix in (" A p-value" + " of zero here.",
                   " A local rank" + " on the observation.",
                   " Sigma beyond" + " the resolution.",
                   " Shear" + " detected.",
                   " Bianchi family" + " identified."):
        with pytest.raises(FiniteNullError, match="forbidden"):
            lint_caption(text + suffix)


def test_runner_check_mode_is_current() -> None:
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT /
             "scripts/codex_harness/run_pr135_finite_null_ranking.py"),
         "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_artifacts_estimator_sim_mutations() -> None:
    estimator = json.loads(
        (REPO_ROOT / "docs/generated/pr135_rank_estimator.json")
        .read_text(encoding="utf-8"))
    assert estimator["min_p_is_nonzero"] is True
    assert estimator["fully_tied_column_p"] == "1"
    sim = json.loads(
        (REPO_ROOT / "docs/generated/pr135_type_i_simulation.json")
        .read_text(encoding="utf-8"))
    assert sim["super_uniform"] is True
    enum = json.loads(
        (REPO_ROOT / "docs/generated/pr135_exact_enumeration.json")
        .read_text(encoding="utf-8"))
    assert enum["all_super_uniform"] is True
    scan = json.loads(
        (REPO_ROOT / "docs/generated/pr135_max_scan.json")
        .read_text(encoding="utf-8"))
    assert scan["scored_identically"] is True
    assert scan["reduction"] == "row_wise_max"
    assert scan["split_evaluated"]["disjoint"] is True
    assert scan["split_evaluated"]["evaluation_n_null"] == 2
    report = json.loads(
        (REPO_ROOT / "docs/generated/pr135_mutation_report.json")
        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 6
    manifest = json.loads(
        (REPO_ROOT / "docs/generated/pr135_artifact_manifest.json")
        .read_text(encoding="utf-8"))
    assert all(sha for sha in manifest["artifacts"].values())
