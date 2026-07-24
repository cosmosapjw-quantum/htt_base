"""PR-143 contract tests: integrated synthetic calibration + adjudication."""
from __future__ import annotations

import dataclasses
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from common.mixture_competition import DiscriminationConfig
from common.synthetic_adjudication import (
    DGP_BATTERY,
    AdjudicationError,
    Criteria,
    Verdict,
    adjudicate_ensemble,
    computational_failure_probe,
    generate_caption,
    lint_caption,
    method_ready_matrix,
    refuse_cherry_pick,
    refuse_hidden_failure,
    refuse_retune_same_id,
    refuse_synthetic_as_observed,
    require_generator_analyst_separation,
    require_non_author_referee,
    run_analyst,
    seal_challenge,
    separation_receipt,
    tally,
    verify_truth_seal,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

CFG = DiscriminationConfig(
    sig2=1.0, tau2=4.0, gain_margin_log_bf=3.0, identifiability_gap=2.0,
    collinearity_threshold=0.9, ppc_reject=0.01, prior_swing_ceiling=6.0,
    tau2_grid=(1.0, 4.0, 16.0), held_out_gain_floor=0.0,
    combination_margin=5.0, seed=5)


def _load_runner():
    runner_path = REPO_ROOT / "scripts/codex_harness/run_pr143_adjudication.py"
    spec = importlib.util.spec_from_file_location("run_pr143", runner_path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def test_source_hashes_are_generation_time_provenance() -> None:
    runner = _load_runner()
    source = runner.SOURCE_PATHS[0]
    referee_rel = runner.OUTPUTS["referee"]
    stored = {
        "measured_size": 0.05,
        "negative_scan": {
            "targets": {source: {"sha256": "1" * 64, "hits": []}},
        },
    }
    current = {
        "measured_size": 0.05,
        "negative_scan": {
            "targets": {source: {"sha256": "2" * 64, "hits": []}},
        },
    }
    assert runner._semantic_artifact(
        referee_rel, stored
    ) == runner._semantic_artifact(referee_rel, current)
    current["negative_scan"]["targets"][source]["hits"] = [{"line": 1}]
    assert runner._semantic_artifact(
        referee_rel, stored
    ) != runner._semantic_artifact(referee_rel, current)
    current["negative_scan"]["targets"][source] = {
        "sha256": "not-a-sha",
        "hits": [],
    }
    assert runner._semantic_artifact(
        referee_rel, stored
    ) != runner._semantic_artifact(referee_rel, current)

    manifest_rel = runner.OUTPUTS["manifest"]
    stored = {
        "input_hashes": [
            f"{path}:{'1' * 64}" for path in runner.SOURCE_PATHS
        ],
    }
    current = {
        "input_hashes": [
            f"{path}:{'2' * 64}" for path in runner.SOURCE_PATHS
        ],
    }
    assert runner._semantic_artifact(
        manifest_rel, stored
    ) == runner._semantic_artifact(manifest_rel, current)
    current["config_hash"] = "changed"
    assert runner._semantic_artifact(
        manifest_rel, stored
    ) != runner._semantic_artifact(manifest_rel, current)


def _challenge(seed=101, n_reps=4):
    return seal_challenge("CH-test", "generator.dgp", n_reps=n_reps,
                          n_obs=60, seed=seed, template_seed=20260718)


def test_seal_challenge_hides_truth_and_is_verifiable() -> None:
    ch = _challenge(n_reps=3)
    assert len(ch.items) == len(DGP_BATTERY) * 3
    for item in ch.blind_items():
        assert set(item) == {"index", "values", "collinear"}
    verify_truth_seal(ch)   # the sealed hash matches the realized labels/data
    # the truth hash is DATA-dependent, not a seed-independent constant
    other = _challenge(seed=999, n_reps=3)
    assert ch.truth_hash != other.truth_hash


def test_tampering_the_seal_is_detected() -> None:
    ch = _challenge(n_reps=3)
    # forge the labels after sealing -> the re-verified hash mismatches
    swapped = tuple((("global" if f == "known_null" else f), r, y, c)
                    for f, r, y, c in ch.items)
    forged = dataclasses.replace(ch, items=swapped)
    with pytest.raises(AdjudicationError, match="tampered"):
        verify_truth_seal(forged)
    an = run_analyst(ch.blind_items(), "analyst.pr141", CFG, n_obs=60,
                     template_seed=20260718)
    with pytest.raises(AdjudicationError, match="tampered"):
        tally(forged, an)


def test_tally_binds_predictions_to_unique_sealed_indices() -> None:
    ch = _challenge(n_reps=2)
    an = run_analyst(ch.blind_items(), "analyst.pr141", CFG, n_obs=60,
                     template_seed=20260718)
    baseline = tally(ch, an)
    reordered = {**an, "predictions": list(reversed(an["predictions"]))}
    assert tally(ch, reordered) == baseline
    duplicated = {
        **an,
        "predictions": [dict(pred, index=0) for pred in an["predictions"]],
    }
    with pytest.raises(AdjudicationError, match="unique in-range"):
        tally(ch, duplicated)
    out_of_range = {
        **an,
        "predictions": [
            *an["predictions"][:-1],
            dict(an["predictions"][-1], index=len(ch.items)),
        ],
    }
    with pytest.raises(AdjudicationError, match="unique in-range"):
        tally(ch, out_of_range)


def test_analyst_is_blind_and_never_false_zero_claimed() -> None:
    # the analyst is handed ONLY blind items (no SealedChallenge / truth)
    ch = _challenge(n_reps=4)
    an = run_analyst(ch.blind_items(), "analyst.pr141", CFG, n_obs=60,
                     template_seed=20260718)
    assert an["n_items"] == len(ch.items)
    counts = tally(ch, an)
    # counts are real per-family tallies (never asserts a zero false rate)
    assert sum(c["n"] for c in counts.values()) == len(ch.items)


def test_ensemble_measured_size_within_alpha_and_covariance_blocks() -> None:
    crit = Criteria(0.1, 0.75, 0.7)
    rep = adjudicate_ensemble(
        "CH-test", "generator.dgp", "analyst.pr141", "referee.nonauthor",
        seeds=[101, 102, 103], n_reps=6, n_obs=60, template_seed=20260718,
        config=CFG, criteria=crit)
    by = {r["family"]: r for r in rep["rows"]}
    # the null size is a MEASURED value within alpha (not asserted zero)
    assert by["known_null"]["criterion"] == "size"
    assert rep["measured_size"] <= 0.1
    assert by["known_null"]["passed"]
    assert by["local"]["passed"] and by["global"]["passed"]
    # covariance misspecification blocks (a genuine diagnostic limitation)
    assert not by["covariance_misspecified"]["passed"]
    assert rep["method_verdict"] == Verdict.BLOCK.value


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("size_alpha", float("nan")),
        ("size_alpha", float("inf")),
        ("size_alpha", -0.1),
        ("power_min", 1.1),
        ("abstain_min", True),
    ],
)
def test_criteria_reject_invalid_probability_thresholds(
        field: str, value) -> None:
    kwargs = {"size_alpha": 0.1, "power_min": 0.75, "abstain_min": 0.7}
    kwargs[field] = value
    with pytest.raises(AdjudicationError, match=r"threshold in \[0, 1\]"):
        Criteria(**kwargs)


def test_separation_guards_live() -> None:
    require_generator_analyst_separation("generator.dgp", "analyst.pr141")
    with pytest.raises(AdjudicationError, match="generator and the analyst"):
        require_generator_analyst_separation("same", "same")
    require_non_author_referee("gen", "analyst", "referee")
    for bad in ("gen", "analyst"):
        with pytest.raises(AdjudicationError, match="NON-AUTHOR"):
            require_non_author_referee("gen", "analyst", bad)
    # the ensemble adjudicator enforces both on its production path
    with pytest.raises(AdjudicationError, match="NON-AUTHOR"):
        adjudicate_ensemble("CH", "gen", "analyst", "analyst", seeds=[1],
                            n_reps=1, n_obs=60, template_seed=20260718,
                            config=CFG, criteria=Criteria(0.1, 0.75, 0.7))


def test_computational_failure_lane() -> None:
    cf = computational_failure_probe(CFG, n_obs=60, template_seed=20260718)
    assert cf["graceful"] is True and cf["safe"] is True


def test_anti_drift_guards() -> None:
    refuse_cherry_pick(list(DGP_BATTERY))
    with pytest.raises(AdjudicationError, match="full pre-registered"):
        refuse_cherry_pick([f for f in DGP_BATTERY if f != "known_null"])
    with pytest.raises(AdjudicationError, match="SAME challenge id"):
        refuse_retune_same_id("a", "b", "CH-1", "CH-1")
    refuse_retune_same_id("a", "b", "CH-2", "CH-1")
    with pytest.raises(AdjudicationError, match="METHOD READINESS"):
        refuse_synthetic_as_observed("observed_validity")
    refuse_synthetic_as_observed("method_readiness")


def test_hidden_failure_and_receipt() -> None:
    rep = adjudicate_ensemble(
        "CH-test", "generator.dgp", "analyst.pr141", "referee.nonauthor",
        seeds=[101, 102], n_reps=6, n_obs=60, template_seed=20260718,
        config=CFG, criteria=Criteria(0.1, 0.75, 0.7))
    cf = computational_failure_probe(CFG, n_obs=60, template_seed=20260718)
    mm = method_ready_matrix(rep, cf)
    refuse_hidden_failure(rep, mm["matrix"])
    hidden = {k: v for k, v in mm["matrix"].items()
              if k != "covariance_misspecified"}
    with pytest.raises(AdjudicationError, match="never hidden"):
        refuse_hidden_failure(rep, hidden)
    receipt = separation_receipt("CH-test", "generator.dgp", "analyst.pr141",
                                 "referee.nonauthor", Criteria(0.1, 0.75, 0.7),
                                 rep["ensemble_hash"])
    assert receipt["referee_id"] not in (receipt["generator_id"],
                                         receipt["analyst_id"])


def test_caption_gate_forbids_never_falsely_discriminates() -> None:
    text = generate_caption("block", 7, 1, 0.0067)
    lint_caption(text)
    for bad in (" the method never falsely " + "discriminates.",
                " the synthetic pass is " + "observed validity.",
                " method readiness is " + "a detection."):
        with pytest.raises(AdjudicationError, match="forbidden"):
            lint_caption(text + bad)


def test_runner_check_mode_is_current() -> None:
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT / "scripts/codex_harness/run_pr143_adjudication.py"),
         "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_artifacts_and_mutations() -> None:
    rep = json.loads((REPO_ROOT / "docs/generated/pr143_referee_report.json")
                     .read_text(encoding="utf-8"))
    assert rep["method_verdict"] == "block"
    assert rep["blocked_families"] == ["covariance_misspecified"]
    assert 0.0 < rep["measured_size"] <= 0.1   # nonzero, within alpha
    assert len(rep["rows"]) == 7
    assert rep["n_seeds"] == 10
    mm = json.loads((REPO_ROOT / "docs/generated/pr143_method_ready_matrix.json")
                    .read_text(encoding="utf-8"))
    assert sum(1 for v in mm["matrix"].values() if v == "ready") == 7
    assert mm["method_ready"] is False
    report = json.loads(
        (REPO_ROOT / "docs/generated/pr143_mutation_report.json")
        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 6
    manifest = json.loads(
        (REPO_ROOT / "docs/generated/pr143_artifact_manifest.json")
        .read_text(encoding="utf-8"))
    assert all(sha for sha in manifest["artifacts"].values())
