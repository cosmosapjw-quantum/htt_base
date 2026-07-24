"""PR-141 contract tests: contamination-aware mixture + mandatory abstention."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from common.mixture_competition import (
    MODELS,
    CompetitionError,
    DiscriminationConfig,
    GenerativeBranch,
    Outcome,
    all_evidences,
    build_templates,
    deterministic_profile_loglik,
    discriminate,
    generate_data,
    generate_caption,
    held_out_gain,
    lint_caption,
    log_evidence,
    ppc_pvalue,
    refuse_deterministic_as_evidence,
    refuse_mio_as_likelihood,
    refuse_residual_absorption,
    require_not_detection,
    require_registered_model_list,
    template_collinearity,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

CFG = DiscriminationConfig(
    sig2=1.0, tau2=4.0, gain_margin_log_bf=3.0, identifiability_gap=2.0,
    collinearity_threshold=0.9, ppc_reject=0.01, prior_swing_ceiling=6.0,
    tau2_grid=(1.0, 4.0, 16.0), held_out_gain_floor=0.0,
    combination_margin=5.0, seed=5)


def _load_runner():
    runner_path = REPO_ROOT / "scripts/codex_harness/run_pr141_mixture.py"
    spec = importlib.util.spec_from_file_location("run_pr141", runner_path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def test_source_hash_is_generation_time_provenance() -> None:
    runner = _load_runner()
    source = runner.SOURCE_PATH

    confusion_rel = runner.OUTPUTS["confusion"]
    stored = {
        "n_cells": 12,
        "negative_scan": {
            "targets": {source: {"sha256": "1" * 64, "hits": []}},
        },
    }
    current = {
        "n_cells": 12,
        "negative_scan": {
            "targets": {source: {"sha256": "2" * 64, "hits": []}},
        },
    }
    assert runner._semantic_artifact(
        confusion_rel, stored
    ) == runner._semantic_artifact(confusion_rel, current)
    current["negative_scan"]["targets"][source]["hits"] = [{"line": 1}]
    assert runner._semantic_artifact(
        confusion_rel, stored
    ) != runner._semantic_artifact(confusion_rel, current)
    current["negative_scan"]["targets"][source] = {
        "sha256": "not-a-sha",
        "hits": [],
    }
    assert runner._semantic_artifact(
        confusion_rel, stored
    ) != runner._semantic_artifact(confusion_rel, current)

    manifest_rel = runner.OUTPUTS["manifest"]
    stored = {"input_hashes": [f"{source}:{'1' * 64}"]}
    current = {"input_hashes": [f"{source}:{'2' * 64}"]}
    assert runner._semantic_artifact(
        manifest_rel, stored
    ) == runner._semantic_artifact(manifest_rel, current)


def test_log_evidence_matches_scipy() -> None:
    from scipy import stats
    T = build_templates(40, 7)
    rng = np.random.Generator(np.random.PCG64(3))
    y = rng.normal(0.0, 1.0, 40)
    X = np.column_stack([T[c] for c in MODELS["global"]])
    cov = 1.0 * np.eye(40) + 4.0 * (X @ X.T)
    want = stats.multivariate_normal(np.zeros(40), cov).logpdf(y)
    assert abs(log_evidence(y, T, MODELS["global"], 1.0, 4.0) - want) < 1e-8


def test_clean_recovers_true_branch() -> None:
    T = build_templates(60, 7, collinear=False)
    for true in ("local", "sys", "global"):
        y = generate_data(true, T, 2.0, 1.0, 100)
        d = discriminate(y, T, CFG)
        assert d["outcome"] == Outcome.DISCRIMINATION_CANDIDATE.value
        assert d["candidate"] == true


def test_confused_abstains_non_identified() -> None:
    T = build_templates(60, 7, collinear=True)
    assert template_collinearity(T, "dipole", "systematic") > 0.9
    for true in ("local", "sys"):
        y = generate_data(true, T, 2.0, 1.0, 100)
        d = discriminate(y, T, CFG)
        assert d["outcome"] == Outcome.ABSTAIN_NON_IDENTIFIED.value
        assert d["candidate"] is None
    # global is NOT confused with the dipole/systematic pair
    y = generate_data("global", T, 2.0, 1.0, 100)
    assert discriminate(y, T, CFG)["candidate"] == "global"


def test_superposition_abstains_non_identified() -> None:
    # a genuine two-component (local + global) superposition — outside the
    # single-component list — abstains non_identified via the combined-model
    # gate, even though the local and global templates are ORTHOGONAL
    T = build_templates(60, 7, collinear=False)
    assert template_collinearity(T, "dipole", "quad") < 0.2
    for seed in (100, 101, 102, 200):
        y = 2.0 * T["dipole"] + 3.0 * T["quad"] \
            + np.random.Generator(np.random.PCG64(seed)).normal(0, 1, 60)
        d = discriminate(y, T, CFG)
        assert d["outcome"] == Outcome.ABSTAIN_NON_IDENTIFIED.value
        assert d["multi_component"] is True
        assert d["candidate"] is None


def test_identifiability_gate_is_evidence_gap_not_collinearity() -> None:
    # the gate must fire on a small evidence gap between orthogonal-template
    # models (collinearity is NOT a necessary condition) — the regression the
    # review caught: `(ev_gap < gap) AND collinear` could never fire here
    T = build_templates(60, 7, collinear=False)
    # tiny equal-strength dipole+quad: near-tie, no single model decisive
    found_near_tie = False
    for seed in range(300, 360):
        y = 0.5 * T["dipole"] + 0.9 * T["quad"] \
            + np.random.Generator(np.random.PCG64(seed)).normal(0, 1, 60)
        d = discriminate(y, T, CFG)
        if d["outcome"] == Outcome.DISCRIMINATION_CANDIDATE.value:
            # any candidate must be decisively separated from the runner-up
            assert d["identifiability_gap"] >= CFG.identifiability_gap
        else:
            found_near_tie = True
    assert found_near_tie   # at least some near-ties abstain


def test_weak_abstains_no_gain() -> None:
    T = build_templates(60, 7, collinear=False)
    for true in ("iso", "local", "sys", "global"):
        y = generate_data(true, T, 0.2, 1.0, 100)
        d = discriminate(y, T, CFG)
        assert d["outcome"] == Outcome.ABSTAIN_NO_GAIN.value


def test_held_out_gain_positive_for_signal_zero_for_noise() -> None:
    T = build_templates(60, 7)
    y_sig = generate_data("global", T, 2.0, 1.0, 100)
    y_noise = generate_data("iso", T, 0.0, 1.0, 100)
    assert held_out_gain(y_sig, T, "global", 1.0, 4.0, seed=5) > 0.1
    assert held_out_gain(y_noise, T, "global", 1.0, 4.0, seed=5) < 0.05


def test_ppc_extreme_for_outliers() -> None:
    T = build_templates(60, 7)
    rng = np.random.Generator(np.random.PCG64(100))
    y = 2.0 * T["quad"] + rng.normal(0, 1, 60)
    y[:6] += 8.0 * rng.standard_normal(6)
    assert ppc_pvalue(y, T, "global", 1.0, 4.0, seed=1) < 0.01


def test_deterministic_branch_separate_from_evidence() -> None:
    T = build_templates(60, 7)
    y = 0.2 * T["quad"] + np.random.Generator(
        np.random.PCG64(100)).normal(0, 1, 60)
    profile = {m: deterministic_profile_loglik(y, T, cols, 1.0)
               for m, cols in MODELS.items()}
    evidence = all_evidences(y, T, 1.0, 4.0)
    # the profile always favors the biggest (most-parameter) model
    assert profile["local"] >= profile["iso"]
    assert profile["global"] >= profile["iso"]
    # under a weak signal the marginal evidence favors the null
    assert max(evidence, key=evidence.get) == "iso"
    with pytest.raises(CompetitionError, match="deterministic"):
        refuse_deterministic_as_evidence(GenerativeBranch.DETERMINISTIC)
    refuse_deterministic_as_evidence(GenerativeBranch.COVARIANCE)   # ok


def test_guards() -> None:
    with pytest.raises(CompetitionError, match="absorbed"):
        refuse_residual_absorption("absorb_into_global")
    refuse_residual_absorption("explicit_competitor")   # ok
    with pytest.raises(CompetitionError, match="likelihood factor"):
        refuse_mio_as_likelihood("mio_score")
    # post-hoc model-list change without multiplicity refused
    with pytest.raises(CompetitionError, match="new registered family|updated"):
        require_registered_model_list(tuple(MODELS) + ("x",), True, None, None)
    # a fixed list before the outcome is fine
    require_registered_model_list(tuple(MODELS), False, None, None)
    # departing before the outcome is refused
    with pytest.raises(CompetitionError, match="fixed and pre-registered"):
        require_registered_model_list(("iso",), False, None, None)


def test_require_not_detection_on_abstention() -> None:
    with pytest.raises(CompetitionError, match="mandatory result"):
        require_not_detection({"outcome": Outcome.ABSTAIN_NO_GAIN.value})
    # a candidate is allowed (no raise)
    require_not_detection(
        {"outcome": Outcome.DISCRIMINATION_CANDIDATE.value})


def test_caption_gate() -> None:
    text = generate_caption(4, 8, 12)
    lint_caption(text)
    for bad in (" global anisotropy " + "detected.",
                " residuals absorbed " + "into global.",
                " mio score " + "as likelihood."):
        with pytest.raises(CompetitionError, match="forbidden"):
            lint_caption(text + bad)


def test_runner_check_mode_is_current() -> None:
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT / "scripts/codex_harness/run_pr141_mixture.py"),
         "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_artifacts_and_mutations() -> None:
    cm = json.loads((REPO_ROOT / "docs/generated/pr141_confusion_matrix.json")
                    .read_text(encoding="utf-8"))
    assert cm["n_cells"] == 12
    assert cm["n_recovered"] == 4
    assert cm["n_abstained"] == 8
    demos = json.loads(
        (REPO_ROOT / "docs/generated/pr141_abstention_demos.json")
        .read_text(encoding="utf-8"))
    assert demos["inadequate"]["outcome"] == "abstain_inadequate"
    assert demos["inadequate"]["detection_refused"] is True
    assert demos["prior_sensitive"]["outcome"] == "abstain_prior_sensitive"
    assert demos["superposed"]["outcome"] == "abstain_non_identified"
    assert demos["superposed"]["multi_component"] is True
    branch = json.loads(
        (REPO_ROOT / "docs/generated/pr141_branch_comparison.json")
        .read_text(encoding="utf-8"))
    assert branch["evidence_favors"] == "iso"
    assert branch["deterministic_branch_refused_for_comparison"] is True
    report = json.loads(
        (REPO_ROOT / "docs/generated/pr141_mutation_report.json")
        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 6
    manifest = json.loads(
        (REPO_ROOT / "docs/generated/pr141_artifact_manifest.json")
        .read_text(encoding="utf-8"))
    assert all(sha for sha in manifest["artifacts"].values())
