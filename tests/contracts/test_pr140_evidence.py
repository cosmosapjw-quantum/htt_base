"""PR-140 contract tests: normalized-prior coherent evidence."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from common.coherent_evidence import (
    EvidenceError,
    GaussianEvidenceModel,
    NormalPrior,
    bridge_sampling,
    caller_scalar_is_not_a_receipt,
    compare_engines,
    evidence_receipt,
    generate_caption,
    lint_caption,
    require_coherent,
    require_evidence_kind,
    require_independent_engines,
    require_normalized_prior,
    require_within_ceiling,
    sensitivity_grid,
    thermodynamic_integration,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_runner():
    runner_path = REPO_ROOT / "scripts/codex_harness/run_pr140_evidence.py"
    spec = importlib.util.spec_from_file_location("run_pr140", runner_path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def test_source_hash_is_generation_time_provenance() -> None:
    runner = _load_runner()
    source = runner.SOURCE_PATH

    evidence_rel = runner.OUTPUTS["evidence"]
    stored = {
        "log_bf10": 1.23456789,
        "negative_scan": {
            "targets": {source: {"sha256": "1" * 64, "hits": []}},
        },
    }
    current = {
        "log_bf10": 1.234567891,
        "negative_scan": {
            "targets": {source: {"sha256": "2" * 64, "hits": []}},
        },
    }
    assert runner._semantic_artifact(
        evidence_rel, stored
    ) == runner._semantic_artifact(evidence_rel, current)
    current["negative_scan"]["targets"][source]["hits"] = [{"line": 1}]
    assert runner._semantic_artifact(
        evidence_rel, stored
    ) != runner._semantic_artifact(evidence_rel, current)
    current["negative_scan"]["targets"][source] = {
        "sha256": "not-a-sha",
        "hits": [],
    }
    assert runner._semantic_artifact(
        evidence_rel, stored
    ) != runner._semantic_artifact(evidence_rel, current)

    manifest_rel = runner.OUTPUTS["manifest"]
    stored = {"input_hashes": [f"{source}:{'1' * 64}"]}
    current = {"input_hashes": [f"{source}:{'2' * 64}"]}
    assert runner._semantic_artifact(
        manifest_rel, stored
    ) == runner._semantic_artifact(manifest_rel, current)


def _model(seed=1, tau2=4.0, sig2=1.0, n=6):
    rng = np.random.Generator(np.random.PCG64(seed))
    y = rng.normal(0.8, 1.0, n)
    return GaussianEvidenceModel(y=y, sig2=sig2, prior=NormalPrior(0.0, tau2))


def test_exact_evidence_matches_scipy() -> None:
    from scipy import stats
    m = _model()
    cov = m.sig2 * np.eye(m.n) + m.prior.var * np.ones((m.n, m.n))
    want = stats.multivariate_normal(np.zeros(m.n), cov).logpdf(m.y)
    assert abs(m.exact_log_evidence() - want) < 1e-9


def test_both_engines_match_exact_and_are_independent() -> None:
    m = _model()
    exact = m.exact_log_evidence()
    ti = thermodynamic_integration(m, n_beta=65, beta_power=4,
                                   n_samples=8000, seed=101)
    bs = bridge_sampling(m, n_posterior=8000, n_proposal=8000, seed=202,
                         max_iter=200)
    assert abs(ti["log_evidence"] - exact) < 0.05
    assert abs(bs["log_evidence"] - exact) < 0.05
    require_independent_engines(ti, bs)
    assert ti["sample_digest"] != bs["sample_digest"]
    # same method or same provenance => not independent
    with pytest.raises(EvidenceError, match="same method"):
        require_independent_engines(ti, dict(bs, method="thermodynamic_integration"))
    with pytest.raises(EvidenceError, match="same sample provenance"):
        require_independent_engines(
            ti, dict(bs, sample_provenance=ti["sample_provenance"]))
    # DATA-independence: identical draws (matching digest) are refused even
    # under different method labels
    with pytest.raises(EvidenceError, match="identical samples"):
        require_independent_engines(
            ti, dict(bs, sample_digest=ti["sample_digest"]))


def test_underresolved_engine_is_indeterminate() -> None:
    m = _model()
    exact = m.exact_log_evidence()
    bs = bridge_sampling(m, n_posterior=8000, n_proposal=8000, seed=202,
                         max_iter=200)
    ti_bad = thermodynamic_integration(m, n_beta=9, beta_power=1,
                                       n_samples=400, seed=101,
                                       n_bootstrap=8, boot_seed=303)
    cmp = compare_engines([ti_bad, bs], exact, agreement_tol=0.05,
                          analytic_tol=0.05, se_ceiling=0.05)
    assert cmp["status"] == "indeterminate"
    with pytest.raises(EvidenceError, match="indeterminate"):
        require_coherent(cmp)


def test_prior_normalization_guard() -> None:
    require_normalized_prior(NormalPrior(0.0, 4.0))
    assert abs(NormalPrior(0.0, 4.0).normalizer_integral() - 1.0) < 1e-4
    with pytest.raises(EvidenceError, match="unnormalized"):
        require_normalized_prior(NormalPrior(0.0, 4.0, normalized=False))


def test_evidence_kind_and_caller_scalar_guards() -> None:
    for kind in ("fitted_score", "max_likelihood_ratio", "caller_scalar",
                 "profile_likelihood"):
        with pytest.raises(EvidenceError, match="not a marginal-likelihood"):
            require_evidence_kind(kind)
    require_evidence_kind("thermodynamic_integration")   # a real engine is fine
    with pytest.raises(EvidenceError, match="not an evidence receipt"):
        caller_scalar_is_not_a_receipt({"log_evidence": 1.0})


def test_sensitivity_grid_and_ceiling() -> None:
    sens = sensitivity_grid(
        lambda t2, sc: _model(tau2=t2, sig2=sc),
        [2.0, 4.0, 8.0], [1.0, 2.0])
    assert len(sens["grid"]) == 6
    assert sens["log_bf_swing"] > 0.0
    require_within_ceiling(sens, 4.0)   # under ceiling here
    with pytest.raises(EvidenceError, match="prior-sensitive"):
        require_within_ceiling({"log_bf_swing": 9.0}, 4.0)


def test_prior_sensitive_grid_gate_is_live() -> None:
    # a wide grid whose swing exceeds the ceiling is refused by the same
    # require_within_ceiling the production verdict asserts
    sens = sensitivity_grid(
        lambda t2, sc: _model(tau2=t2, sig2=sc),
        [0.1, 4.0, 1000.0], [1.0, 4.0])
    assert sens["log_bf_swing"] > 4.0
    with pytest.raises(EvidenceError, match="prior-sensitive"):
        require_within_ceiling(sens, 4.0)


def test_receipt_hash_changes_with_inputs() -> None:
    m = _model()
    ti = thermodynamic_integration(m, n_beta=33, beta_power=4,
                                   n_samples=2000, seed=1)
    bs = bridge_sampling(m, n_posterior=2000, n_proposal=2000, seed=2,
                         max_iter=100)
    cmp = compare_engines([ti, bs], m.exact_log_evidence(),
                          agreement_tol=0.1, analytic_tol=0.1, se_ceiling=1.0)
    r1 = evidence_receipt(m, [ti, bs], cmp)
    m2 = GaussianEvidenceModel(y=m.y, sig2=m.sig2, prior=NormalPrior(0.0, 9.0))
    ti2 = thermodynamic_integration(m2, n_beta=33, beta_power=4,
                                    n_samples=2000, seed=1)
    bs2 = bridge_sampling(m2, n_posterior=2000, n_proposal=2000, seed=2,
                          max_iter=100)
    cmp2 = compare_engines([ti2, bs2], m2.exact_log_evidence(),
                           agreement_tol=0.1, analytic_tol=0.1, se_ceiling=1.0)
    r2 = evidence_receipt(m2, [ti2, bs2], cmp2)
    assert r1["receipt_hash"] != r2["receipt_hash"]   # prior var changed


def test_receipt_binds_inputs() -> None:
    m = _model()
    ti = thermodynamic_integration(m, n_beta=33, beta_power=4,
                                   n_samples=2000, seed=1)
    bs = bridge_sampling(m, n_posterior=2000, n_proposal=2000, seed=2,
                         max_iter=100)
    cmp = compare_engines([ti, bs], m.exact_log_evidence(),
                          agreement_tol=0.1, analytic_tol=0.1, se_ceiling=1.0)
    receipt = evidence_receipt(m, [ti, bs], cmp)
    assert receipt["receipt_hash"] and receipt["inputs"]["prior"]["normalized"]
    assert sorted(receipt["inputs"]["engines"]) == \
        ["bridge_sampling", "thermodynamic_integration"]


def test_caption_gate() -> None:
    text = generate_caption(1.61, 0.005, 1.81, "coherent")
    lint_caption(text)
    for bad in (" the fitted score " + "is the bayes factor.",
                " we used an unnormalized " + "prior evidence.",
                " evidence agreement " + "proves the model."):
        with pytest.raises(EvidenceError, match="forbidden"):
            lint_caption(text + bad)


def test_runner_check_mode_is_current() -> None:
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT / "scripts/codex_harness/run_pr140_evidence.py"),
         "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_artifacts_and_mutations() -> None:
    ev = json.loads((REPO_ROOT / "docs/generated/pr140_evidence_report.json")
                    .read_text(encoding="utf-8"))
    assert ev["comparison"]["status"] == "coherent"
    assert ev["final_status"] == "coherent"
    assert ev["prior_sensitive"] is False
    assert ev["comparison"]["engine_gap"] < 0.05
    assert len(ev["engines"]) == 2
    assert ev["engines"][0]["sample_digest"] != ev["engines"][1]["sample_digest"]
    sens = json.loads(
        (REPO_ROOT / "docs/generated/pr140_sensitivity_report.json")
        .read_text(encoding="utf-8"))
    assert len(sens["grid"]) == 6
    demo = json.loads(
        (REPO_ROOT / "docs/generated/pr140_prior_sensitive_demo.json")
        .read_text(encoding="utf-8"))
    assert demo["log_bf_swing"] > demo["ceiling"]
    assert demo["decisive_claim_refused"] is True
    assert demo["status"] == "indeterminate"
    ind = json.loads(
        (REPO_ROOT / "docs/generated/pr140_indeterminate_demo.json")
        .read_text(encoding="utf-8"))
    assert ind["comparison"]["status"] == "indeterminate"
    assert ind["coherent_claim_refused"] is True
    receipt = json.loads((REPO_ROOT / "docs/generated/pr140_receipt.json")
                         .read_text(encoding="utf-8"))
    assert receipt["receipt_hash"]
    report = json.loads(
        (REPO_ROOT / "docs/generated/pr140_mutation_report.json")
        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 6
    manifest = json.loads(
        (REPO_ROOT / "docs/generated/pr140_artifact_manifest.json")
        .read_text(encoding="utf-8"))
    assert all(sha for sha in manifest["artifacts"].values())
