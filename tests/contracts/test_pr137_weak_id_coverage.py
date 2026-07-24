"""PR-137 contract tests: weak-identification grid coverage."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from common.weak_id_coverage import (
    Preregistration,
    WeakIdError,
    bonferroni_conf,
    build_failure_map,
    clopper_pearson_lower,
    clopper_pearson_upper,
    coverage_at_point,
    generate_caption,
    imbens_manski_c,
    lint_caption,
    lint_uniform,
    require_failure_map_complete,
    require_full_grid,
    require_uniform_certificate,
    validate_lower_bound,
    _betainc_reg,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_runner():
    runner_path = (
        REPO_ROOT / "scripts/codex_harness/run_pr137_weak_id_coverage.py"
    )
    spec = importlib.util.spec_from_file_location("run_pr137", runner_path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def test_source_hash_is_generation_time_provenance() -> None:
    runner = _load_runner()
    source = runner.SOURCE_PATH
    grid_rel = runner.OUTPUTS["grid"]
    stored = {
        "negative_scan": {
            "targets": {
                source: {"sha256": "1" * 64, "hits": []},
            }
        }
    }
    current = {
        "negative_scan": {
            "targets": {
                source: {"sha256": "2" * 64, "hits": []},
            }
        }
    }
    assert runner._semantic_artifact(
        grid_rel, stored
    ) == runner._semantic_artifact(grid_rel, current)
    current["negative_scan"]["targets"][source]["hits"] = [{"line": 1}]
    assert runner._semantic_artifact(
        grid_rel, stored
    ) != runner._semantic_artifact(grid_rel, current)

    manifest_rel = runner.OUTPUTS["manifest"]
    stored = {"input_hashes": [f"{source}:{'1' * 64}"]}
    current = {"input_hashes": [f"{source}:{'2' * 64}"]}
    assert runner._semantic_artifact(
        manifest_rel, stored
    ) == runner._semantic_artifact(manifest_rel, current)


def test_betainc_matches_reference() -> None:
    # I_0.5(1,1) = 0.5; I_x(a,b) monotone; endpoints
    assert abs(_betainc_reg(0.5, 1, 1) - 0.5) < 1e-9
    assert _betainc_reg(0.0, 2, 3) == 0.0
    assert _betainc_reg(1.0, 2, 3) == 1.0
    # against scipy
    from scipy.stats import beta as spbeta
    for x, a, b in ((0.3, 2, 5), (0.7, 4, 2), (0.1, 10, 10)):
        assert abs(_betainc_reg(x, a, b) - float(spbeta.cdf(x, a, b))) < 1e-8


def test_clopper_pearson_lower_conservative() -> None:
    # lower bound is below the point estimate
    assert clopper_pearson_lower(950, 1000, 0.99) < 0.95
    assert clopper_pearson_lower(0, 10, 0.99) == 0.0
    # monotone in k
    assert clopper_pearson_lower(900, 1000, 0.99) < \
        clopper_pearson_lower(960, 1000, 0.99)


def test_imbens_manski_c_and_coverage() -> None:
    # w=0 -> two-sided 0.95 -> c = 1.96
    assert abs(imbens_manski_c(0.0)["c"] - 1.959963985) < 1e-4
    # coverage at w=0 is ~nominal
    r = coverage_at_point(0.0, "imbens_manski", n_replicates=2000,
                          seeds=10, base_seed=20260719, w_key="0")
    assert 0.93 <= r["coverage"] <= 0.97
    assert r["marginal_lower_99"] >= 0.90
    assert r["endpoint_error"] < 1e-9


def test_boundary_config_is_least_favorable() -> None:
    # the identified-set boundary theta0 is the least-favorable position;
    # IM coverage there is ~nominal (not over-covering like the midpoint)
    for w in (0.5, 1.0, 2.0, 4.0):
        mid = coverage_at_point(w, "imbens_manski", n_replicates=5000,
                                seeds=10, base_seed=20260719,
                                w_key=str(w), theta0_position="midpoint")
        bnd = coverage_at_point(w, "imbens_manski", n_replicates=5000,
                                seeds=10, base_seed=20260719,
                                w_key=str(w), theta0_position="boundary")
        # boundary coverage is at/near nominal; midpoint over-covers
        assert bnd["coverage"] <= mid["coverage"] + 1e-9
        assert 0.94 <= bnd["coverage"] <= 0.97


def test_bonferroni_simultaneous_bound() -> None:
    # per-point conf for a joint 0.99 over 9 points
    pc = bonferroni_conf(0.99, 9)
    assert abs(pc - (1 - 0.01 / 9)) < 1e-12
    # the Bonferroni per-point lower bound is below the marginal one
    assert clopper_pearson_lower(9500, 10000, pc) < \
        clopper_pearson_lower(9500, 10000, 0.99)


@pytest.mark.parametrize("confidence", [-0.1, 0.0, 1.0, 1.1, float("nan")])
def test_confidence_domain_rejected(confidence: float) -> None:
    with pytest.raises(WeakIdError, match="confidence.*between 0 and 1"):
        clopper_pearson_lower(95, 100, confidence)
    with pytest.raises(WeakIdError, match="confidence.*between 0 and 1"):
        clopper_pearson_upper(95, 100, confidence)
    with pytest.raises(WeakIdError, match="confidence.*between 0 and 1"):
        bonferroni_conf(confidence, 9)


def test_wrong_binomial_bound_rejected() -> None:
    # an upper CP bound routed through the lower-bound guard is rejected
    k, n = 9500, 10000
    upper = clopper_pearson_upper(k, n, 0.99)
    assert upper > k / n
    with pytest.raises(WeakIdError, match="upper bound"):
        validate_lower_bound(upper, k, n, 0.99)
    with pytest.raises(WeakIdError, match="lower bound must be finite"):
        validate_lower_bound(float("nan"), k, n, 0.99)
    # the true lower bound passes
    validate_lower_bound(clopper_pearson_lower(k, n, 0.99), k, n, 0.99)


def test_deterministic_coverage() -> None:
    kw = dict(n_replicates=2000, seeds=10, base_seed=20260719, w_key="1")
    r1 = coverage_at_point(1.0, "imbens_manski", **kw)
    r2 = coverage_at_point(1.0, "imbens_manski", **kw)
    assert r1["covered"] == r2["covered"]


@pytest.mark.parametrize(
    ("n_replicates", "seeds"),
    [(-1, 10), (10, 0), (True, 10), (10, True)],
)
def test_coverage_requires_positive_integer_counts(
    n_replicates: int,
    seeds: int,
) -> None:
    with pytest.raises(WeakIdError, match="positive integer"):
        coverage_at_point(
            0.0,
            "imbens_manski",
            n_replicates=n_replicates,
            seeds=seeds,
            base_seed=1,
            w_key="0",
        )


def test_unknown_coverage_procedure_rejected() -> None:
    with pytest.raises(WeakIdError, match="unknown coverage procedure"):
        coverage_at_point(
            0.0,
            "imbens_manski_typo",
            n_replicates=20,
            seeds=2,
            base_seed=1,
            w_key="0",
        )


def test_adversarial_naive_fails_and_is_preserved() -> None:
    r = coverage_at_point(0.0, "naive_no_expansion", n_replicates=2000,
                          seeds=10, base_seed=20260719, w_key="0")
    r["family_wise_lower"] = clopper_pearson_lower(
        r["covered"], r["delivered_replicates"], 0.99)
    assert r["family_wise_lower"] < 0.93   # undercovers badly
    fmap = build_failure_map([r], 0.93, "family_wise_lower")
    assert fmap["failing_count"] == 1
    assert fmap["failing_points"][0]["w"] == "0"


def test_failure_map_rejects_non_finite_decision_inputs() -> None:
    row = {
        "w": "0",
        "procedure": "imbens_manski",
        "coverage": 0.95,
        "family_wise_lower": 0.94,
    }
    with pytest.raises(WeakIdError, match="threshold must be finite"):
        build_failure_map([row], float("nan"))
    row["family_wise_lower"] = float("nan")
    with pytest.raises(WeakIdError, match="bound.*must be finite"):
        build_failure_map([row], 0.93)


def test_full_grid_and_failure_map_guards() -> None:
    with pytest.raises(WeakIdError, match="central cases only"):
        require_full_grid(["0", "1/4"], ["0", "1/4", "1/2", "1"])
    require_full_grid(["0", "1/4", "1/2"], ["0", "1/4", "1/2"])
    with pytest.raises(WeakIdError, match="PRESERVED in the failure"):
        require_failure_map_complete(["0", "1/2"], ["0", "1/4", "1/2"])


def test_uniform_language_gate() -> None:
    with pytest.raises(WeakIdError, match="continuity/mesh"):
        require_uniform_certificate(None)
    with pytest.raises(WeakIdError, match="continuity/mesh"):
        require_uniform_certificate("nonexistent_cert")
    # a caption containing "uniform" without a cert is refused
    with pytest.raises(WeakIdError, match="continuity/mesh"):
        lint_uniform("coverage holds uniformly across the class")
    # obfuscations (hyphen, zero-width split) are also caught
    with pytest.raises(WeakIdError, match="continuity/mesh"):
        lint_uniform("coverage is uni-form over the class")
    with pytest.raises(WeakIdError, match="continuity/mesh"):
        lint_uniform("this is class-wide coverage")
    # a grid-conditional caption is fine; "nonuniform" is not a claim
    lint_uniform("grid-conditional empirical coverage over the grid")
    lint_uniform("the coverage is nonuniform across w, as expected")


def test_preregistration_pins() -> None:
    pre = Preregistration(0.95, 0.93, 2000, 10, 20260719, 0.10)
    pre.require_replicates(2000, 10)
    with pytest.raises(WeakIdError, match="at least"):
        pre.require_replicates(500, 10)
    with pytest.raises(WeakIdError, match="at least"):
        pre.require_replicates(2000, 3)
    with pytest.raises(WeakIdError, match="positive integer"):
        pre.require_replicates(float("nan"), float("nan"))
    pre.require_pinned_threshold(0.93)
    with pytest.raises(WeakIdError, match="NEW calibration"):
        pre.require_pinned_threshold(0.90)
    with pytest.raises(WeakIdError, match="thresholds must be finite"):
        pre.require_pinned_threshold(float("nan"))


def test_caption_gate() -> None:
    text = generate_caption(0.94, 9, 0)
    lint_caption(text)
    for suffix in (" We show uniform coverage" + " over the class.",
                   " Coverage from" + " the central cases.",
                   " We dropped the" + " failing corner.",
                   " We tuned the threshold" + " to the coverage."):
        with pytest.raises(WeakIdError, match="forbidden|continuity"):
            lint_caption(text + suffix)


def test_runner_check_mode_is_current() -> None:
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT /
             "scripts/codex_harness/run_pr137_weak_id_coverage.py"),
         "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_artifacts_bounds_failure_mesh_mutations() -> None:
    bounds = json.loads(
        (REPO_ROOT / "docs/generated/pr137_family_wise_bounds.json")
        .read_text(encoding="utf-8"))
    assert bounds["all_retained"] is True
    assert bounds["min_lower_bound"] >= 0.93
    assert len(bounds["bounds"]) == 9
    # a genuine simultaneous Bonferroni bound (per-point conf > 0.99)
    assert bounds["per_point_confidence_bonferroni"] > 0.99
    assert bounds["retain_config"].startswith("boundary")
    assert bounds["extension_replicates"] == 10000
    failure = json.loads(
        (REPO_ROOT / "docs/generated/pr137_failure_map.json")
        .read_text(encoding="utf-8"))
    # the adversarial naive procedure's failures are preserved
    assert failure["failing_count"] >= 1
    mesh = json.loads(
        (REPO_ROOT / "docs/generated/pr137_mesh_refinement.json")
        .read_text(encoding="utf-8"))
    assert mesh["worst_case_coverage_change"] <= 0.01
    assert mesh["coverage_change_ok"] is True
    assert mesh["passes_mesh_kill_condition"] is True
    report = json.loads(
        (REPO_ROOT / "docs/generated/pr137_mutation_report.json")
        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 6
    manifest = json.loads(
        (REPO_ROOT / "docs/generated/pr137_artifact_manifest.json")
        .read_text(encoding="utf-8"))
    assert all(sha for sha in manifest["artifacts"].values())
