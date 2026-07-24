"""PR-139 contract tests: dependency-aware holdout + train-only refit."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from common.dependency_holdout import (
    DependencyGraph,
    GroupModel,
    HoldoutError,
    HoldoutStatus,
    _gpinv,
    _mvn_logpdf,
    compare_exact_psis,
    conditional_joint_lpd,
    dependency_optimism,
    exact_group_elpd,
    generate_caption,
    influential_folds,
    lint_caption,
    marginal_covariance,
    psis_group_elpd,
    refuse_as_loo,
    require_exchangeable_unit,
    require_reliable_or_exact,
    require_train_only,
    require_units_respect_dependency,
    select_features,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_runner():
    runner_path = REPO_ROOT / "scripts/codex_harness/run_pr139_holdout.py"
    spec = importlib.util.spec_from_file_location("run_pr139", runner_path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def test_source_hash_is_generation_time_provenance() -> None:
    runner = _load_runner()
    source = runner.SOURCE_PATH

    elpd_rel = runner.OUTPUTS["elpd"]
    stored = {
        "elpd": -1.23456789,
        "negative_scan": {
            "targets": {source: {"sha256": "1" * 64, "hits": []}},
        }
    }
    current = {
        "elpd": -1.234567891,
        "negative_scan": {
            "targets": {source: {"sha256": "2" * 64, "hits": []}},
        }
    }
    assert runner._semantic_artifact(
        elpd_rel, stored
    ) == runner._semantic_artifact(elpd_rel, current)
    current["negative_scan"]["targets"][source]["hits"] = [{"line": 1}]
    assert runner._semantic_artifact(
        elpd_rel, stored
    ) != runner._semantic_artifact(elpd_rel, current)
    current["negative_scan"]["targets"][source] = {
        "sha256": "not-a-sha",
        "hits": [],
    }
    assert runner._semantic_artifact(
        elpd_rel, stored
    ) != runner._semantic_artifact(elpd_rel, current)

    manifest_rel = runner.OUTPUTS["manifest"]
    stored = {"input_hashes": [f"{source}:{'1' * 64}"]}
    current = {"input_hashes": [f"{source}:{'2' * 64}"]}
    assert runner._semantic_artifact(
        manifest_rel, stored
    ) == runner._semantic_artifact(manifest_rel, current)


def _toy(G=12, ng=4, pt=3, tau_b2=1.0, seed=101):
    rng = np.random.Generator(np.random.PCG64(seed))
    N = G * ng
    groups = tuple(int(i // ng) for i in range(N))
    X = rng.standard_normal((N, pt))
    b_g = rng.normal(0.0, tau_b2 ** 0.5, G)
    eps = rng.normal(0.0, 1.0, N)
    y = 0.3 + X @ np.array([1.5, -1.0, 0.8]) \
        + np.array([b_g[groups[i]] for i in range(N)]) + eps
    model = GroupModel(X=X, y=y, group=groups, sig2=1.0, tau_b2=tau_b2,
                       prior_tau2=10.0)
    return model, DependencyGraph("group", tuple(groups))


def test_mvn_logpdf_matches_scipy() -> None:
    from scipy import stats
    rng = np.random.Generator(np.random.PCG64(7))
    A = rng.standard_normal((4, 4))
    cov = A @ A.T + np.eye(4)
    mean = rng.standard_normal(4)
    x = rng.standard_normal(4)
    assert abs(_mvn_logpdf(x, mean, cov)
               - stats.multivariate_normal(mean, cov).logpdf(x)) < 1e-9


def test_gpinv_matches_scipy_genpareto() -> None:
    from scipy import stats
    probs = np.array([0.1, 0.5, 0.9, 0.99])
    for k, sigma in ((0.3, 2.0), (-0.2, 1.5), (0.0, 1.0)):
        got = _gpinv(probs.copy(), k, sigma)
        want = sigma * stats.genpareto.ppf(probs, c=k)
        assert np.allclose(got, want, atol=1e-10)


def test_dependency_graph_folds_and_status() -> None:
    graph = DependencyGraph("group", (0, 0, 1, 1, 2, 2))
    assert graph.status() is HoldoutStatus.LOO_IDENTIFIED
    assert graph.folds() == ((0, 1), (2, 3), (4, 5))
    single = DependencyGraph("group", (0, 0, 0, 0))
    assert single.status() is HoldoutStatus.LOO_NOT_IDENTIFIED
    with pytest.raises(HoldoutError, match="LOO_not_identified"):
        require_exchangeable_unit(single)
    with pytest.raises(HoldoutError, match="unknown unit_kind"):
        DependencyGraph("pixel", (0, 1))


def test_group_model_rejects_nonfinite_observations() -> None:
    model, _ = _toy(G=4, ng=2)
    bad_y = model.y.copy()
    bad_y[0] = np.nan
    with pytest.raises(HoldoutError, match="only finite"):
        GroupModel(
            X=model.X,
            y=bad_y,
            group=model.group,
            sig2=model.sig2,
            tau_b2=model.tau_b2,
            prior_tau2=model.prior_tau2,
        )


def test_group_model_validates_rows_and_variance_domain() -> None:
    model, _ = _toy(G=4, ng=2)
    with pytest.raises(HoldoutError, match="same row count"):
        GroupModel(model.X, model.y[:-1], model.group, 1.0, 0.5, 2.0)
    with pytest.raises(HoldoutError, match="sig2 must be positive"):
        GroupModel(model.X, model.y, model.group, 0.0, 0.5, 2.0)


def test_holdout_refuses_graph_that_conflicts_with_model_groups() -> None:
    model, _ = _toy(G=6, ng=2)
    conflicting = DependencyGraph(
        "group",
        tuple(row % 2 for row in range(model.X.shape[0])),
    )
    with pytest.raises(HoldoutError, match="model group partition"):
        exact_group_elpd(model, conflicting)
    with pytest.raises(HoldoutError, match="model group partition"):
        psis_group_elpd(model, conflicting, n_draws=100, seed=7)
    with pytest.raises(HoldoutError, match="model group partition"):
        dependency_optimism(model, conflicting)


def test_units_respect_dependency_refuses_row_split() -> None:
    clusters = [[0, 1, 2], [3, 4, 5]]
    require_units_respect_dependency(clusters, clusters)   # group folds OK
    require_units_respect_dependency([[0, 1, 2, 3, 4, 5]], clusters)
    with pytest.raises(HoldoutError, match="splits a dependency cluster"):
        require_units_respect_dependency([[0], [1], [2]], clusters)


@pytest.mark.parametrize(
    ("folds", "message"),
    (
        ([[0, 1, 2]], "omit rows"),
        ([[0, 1, 2], [0, 1, 2], [3, 4, 5]], "repeat rows"),
        ([[], [0, 1, 2], [3, 4, 5]], "fold is empty"),
    ),
)
def test_units_respect_dependency_requires_complete_partition(
        folds, message) -> None:
    with pytest.raises(HoldoutError, match=message):
        require_units_respect_dependency(folds, [[0, 1, 2], [3, 4, 5]])


def test_exact_elpd_train_only_scope_and_hashes() -> None:
    model, graph = _toy()
    exact = exact_group_elpd(model, graph, cols=range(3))
    assert exact["n_folds"] == 12
    assert {f["standardize_scope"] for f in exact["folds"]} == {"train_only"}
    # every fold records a content-addressed train-only transform hash
    assert all(f["standardize_hash"] for f in exact["folds"])


def test_exact_elpd_matches_marginal_conditional() -> None:
    # the refit route (per-fold GLS posterior + predictive) and the
    # independent marginal-MVN conditional route must agree exactly when
    # standardization is the identity (matched parametrization)
    model, graph = _toy(G=8, ng=3, tau_b2=1.0, seed=44)
    exact = exact_group_elpd(model, graph, cols=range(3), standardize=False)
    mean, cov = marginal_covariance(model, range(3))
    for g, fold in zip(model.group_ids(), exact["folds"]):
        rows = list(model.rows_of_group(g))
        want = conditional_joint_lpd(mean, cov, model.y, rows)
        assert abs(fold["log_predictive_density"] - want) < 1e-9


def test_train_only_transform_rejects_heldout_rows() -> None:
    from common.dependency_holdout import (select_features,
                                           train_only_standardization)
    model, _ = _toy(G=6, ng=3, seed=9)
    n = model.X.shape[0]
    # passing all rows while declaring row 0 held-out is refused
    with pytest.raises(HoldoutError, match="held-out rows"):
        train_only_standardization(model.X, list(range(n)), held_rows=[0])
    with pytest.raises(HoldoutError, match="held-out rows"):
        select_features(model.X, model.y, list(range(n)), 2, "train_only",
                        held_rows=[1])
    # a genuinely disjoint train set is accepted
    train_only_standardization(model.X, list(range(3, n)), held_rows=[0, 1, 2])


def test_psis_raises_on_too_few_draws() -> None:
    from common.dependency_holdout import psis_smooth
    with pytest.raises(HoldoutError, match="too few posterior draws"):
        psis_smooth(np.zeros(10))


def test_psis_reliable_and_agrees_with_exact() -> None:
    model, graph = _toy(G=16, ng=3, tau_b2=0.5, seed=202)
    exact = exact_group_elpd(model, graph, cols=range(3))
    psis = psis_group_elpd(model, graph, n_draws=4000, seed=5, cols=range(3))
    assert psis["max_pareto_k"] <= 0.7
    diffs = [abs(f["elpd"] - e["log_predictive_density"])
             for f, e in zip(psis["folds"], exact["folds"])]
    assert max(diffs) < 0.5
    require_reliable_or_exact(psis, 0.7, used_exact_fallback=False)


def test_psis_unreliable_requires_exact_fallback() -> None:
    with pytest.raises(HoldoutError, match="exact refit is required"):
        require_reliable_or_exact({"max_pareto_k": 1.3}, 0.7,
                                  used_exact_fallback=False)
    # with the exact fallback taken, no error
    require_reliable_or_exact({"max_pareto_k": 1.3}, 0.7,
                              used_exact_fallback=True)


def test_psis_diagnostics_reject_nonfinite_values() -> None:
    bad = {
        "elpd": -1.0,
        "max_pareto_k": float("nan"),
        "folds": [{"group": 0, "elpd": -1.0, "pareto_k": float("nan")}],
    }
    exact = {
        "elpd": -1.0,
        "folds": [{"group": 0, "log_predictive_density": -1.0}],
    }
    with pytest.raises(HoldoutError, match="must be finite"):
        require_reliable_or_exact(bad, 0.7, used_exact_fallback=False)
    with pytest.raises(HoldoutError, match="must be finite"):
        compare_exact_psis(exact, bad, 0.5, 0.7)
    with pytest.raises(HoldoutError, match="must be finite"):
        influential_folds(bad)


def test_psis_smoothing_rejects_nonfinite_ratios() -> None:
    from common.dependency_holdout import psis_smooth
    with pytest.raises(HoldoutError, match="finite vector"):
        psis_smooth(np.full(100, np.nan))


def test_train_only_guard_and_selection_leakage() -> None:
    require_train_only({"scope": "train_only"})
    with pytest.raises(HoldoutError, match="train_only"):
        require_train_only({"scope": "full_data"})
    # leaky (full-data) selection inflates the held-out ELPD (null signal)
    rng = np.random.Generator(np.random.PCG64(20260722))
    G, ng, pc = 8, 4, 30
    N = G * ng
    groups = tuple(int(i // ng) for i in range(N))
    X = rng.standard_normal((N, pc))
    b_g = rng.normal(0.0, 0.3 ** 0.5, G)
    eps = rng.normal(0.0, 1.0, N)
    y = 0.3 + np.array([b_g[groups[i]] for i in range(N)]) + eps
    model = GroupModel(X=X, y=y, group=groups, sig2=1.0, tau_b2=0.3,
                       prior_tau2=10.0)
    graph = DependencyGraph("group", tuple(groups))
    train_only = exact_group_elpd(model, graph, select_k=3,
                                  leaky_selection=False)
    leaky = exact_group_elpd(model, graph, select_k=3, leaky_selection=True)
    assert leaky["elpd"] - train_only["elpd"] > 1.0


def test_selection_scope_recorded() -> None:
    model, graph = _toy(G=8, ng=4, pt=3)
    chosen, meta = select_features(model.X, model.y, range(model.X.shape[0]),
                                   2, "full_data")
    assert meta["provenance"]["scope"] == "full_data"
    with pytest.raises(HoldoutError):
        require_train_only(meta["provenance"])


def test_dependency_optimism_row_beats_group() -> None:
    model, graph = _toy(G=12, ng=5, tau_b2=2.0, seed=20260722)
    opt = dependency_optimism(model, graph, cols=range(3))
    assert opt["row_optimism"] > 0.0
    assert opt["row_loo_per_obs"] > opt["group_loo_per_obs"]
    assert opt["row_fold_split_refused"] is True
    # the conditional joint density is a real MVN conditional
    mean, cov = marginal_covariance(model, range(3))
    lp = conditional_joint_lpd(mean, cov, model.y, [0, 1, 2, 3, 4])
    assert np.isfinite(lp)


def test_refuse_as_loo() -> None:
    for kind in ("channel_ablation", "full_vs_fold_evidence_difference"):
        with pytest.raises(HoldoutError, match="not a held-out"):
            refuse_as_loo(kind)
    refuse_as_loo("group_loo")   # a real LOO kind is fine


def test_caption_gate() -> None:
    text = generate_caption(-1.59, 0.48, 8.29, "LOO_identified")
    lint_caption(text)
    for bad in (" channel ablation " + "is the loo.",
                " we standardized on " + "the full data.",
                " dependent rows " + "as independent units."):
        with pytest.raises(HoldoutError, match="forbidden"):
            lint_caption(text + bad)


def test_runner_check_mode_is_current() -> None:
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT / "scripts/codex_harness/run_pr139_holdout.py"),
         "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_artifacts_and_mutations() -> None:
    elpd = json.loads((REPO_ROOT / "docs/generated/pr139_elpd_report.json")
                      .read_text(encoding="utf-8"))
    assert elpd["n_folds"] == 20
    assert {f["standardize_scope"] for f in elpd["folds"]} == {"train_only"}
    psis = json.loads((REPO_ROOT / "docs/generated/pr139_psis_report.json")
                      .read_text(encoding="utf-8"))
    assert psis["max_pareto_k"] <= 0.7
    assert psis["comparison"]["psis_agrees_with_exact"] is True
    leak = json.loads((REPO_ROOT / "docs/generated/pr139_leakage_report.json")
                      .read_text(encoding="utf-8"))
    assert leak["selection_leakage_gap"] > 1.0
    assert leak["full_data_provenance_refused"] is True
    dep = json.loads(
        (REPO_ROOT / "docs/generated/pr139_dependency_report.json")
        .read_text(encoding="utf-8"))
    assert dep["row_optimism"] > 0.0
    assert dep["single_cluster_status"] == "LOO_not_identified"
    assert dep["single_cluster_refused"] is True
    report = json.loads(
        (REPO_ROOT / "docs/generated/pr139_mutation_report.json")
        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 6
    manifest = json.loads(
        (REPO_ROOT / "docs/generated/pr139_artifact_manifest.json")
        .read_text(encoding="utf-8"))
    assert all(sha for sha in manifest["artifacts"].values())
