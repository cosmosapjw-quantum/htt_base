"""PR-138 contract tests: SBC + replicated-data PPC."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest

from common.sbc_ppc import (
    GaussianModel,
    InadequateModelError,
    SbcPpcError,
    freeze_discrepancies,
    generate_caption,
    lineage_hash,
    lint_caption,
    ppc_verdict,
    require_frozen_discrepancies,
    require_not_ppc,
    require_ppc_receipt,
    require_sbc_calibrated,
    require_valid_posterior,
    run_ppc,
    run_sbc,
    sbc_lineage_hash,
    sbc_verdict,
    standardized_residual_check,
    verify_lineage,
    _chi2_sf,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
GOOD = GaussianModel(Fraction(4), Fraction(1), 8, Fraction(1))
_CFG = {"n": "8"}


def _run_sbc(model, **kw):
    lh = sbc_lineage_hash(model, _CFG)
    return run_sbc(model, lineage_hash=lh, config=_CFG, **kw)


def _lineage(model, y):
    dh = "d" + str(hash(tuple(np.asarray(y).tolist())) % 10 ** 8)
    lh = lineage_hash(model, dh, _CFG, {"r": "1.0"})
    return {"claimed_hash": lh, "data_hash": dh, "config": _CFG,
            "diagnostics": {"r": "1.0"}}


def _load_runner():
    path = REPO_ROOT / "scripts/codex_harness/run_pr138_sbc_ppc.py"
    spec = importlib.util.spec_from_file_location("run_pr138", path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def test_check_normalizes_only_generation_time_source_hash() -> None:
    runner = _load_runner()
    source = runner.SOURCE_PATH
    stored = {
        "uniformity_pvalue": 0.1,
        "negative_scan": {
            "targets": {
                source: {"sha256": "1" * 64, "hits": []},
            },
        },
    }
    current = {
        "uniformity_pvalue": 0.1,
        "negative_scan": {
            "targets": {
                source: {"sha256": "2" * 64, "hits": []},
            },
        },
    }
    rel = runner.OUTPUTS["sbc"]
    assert runner._semantic_artifact(
        rel, stored
    ) == runner._semantic_artifact(rel, current)
    current["uniformity_pvalue"] = 0.2
    assert runner._semantic_artifact(
        rel, stored
    ) != runner._semantic_artifact(rel, current)
    current["uniformity_pvalue"] = 0.1
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


def test_chi2_sf_matches_scipy() -> None:
    from scipy import stats
    for x, k in ((23.4, 20), (5.0, 3), (100.0, 20), (0.5, 2)):
        assert abs(_chi2_sf(x, k) - float(1 - stats.chi2.cdf(x, k))) < 1e-9


def test_sbc_known_good_passes_known_bad_fails() -> None:
    good = _run_sbc(GOOD, n_simulations=3000, n_draws=20, seed=20260720,
                    n_bins=7)
    assert sbc_verdict(good, 0.01) == "calibrated"
    assert good["uniformity_pvalue"] > 0.01
    assert good["n_bins"] == 7 and good["dof"] == 6
    for vs in (Fraction(1, 2), Fraction(2)):
        bad = _run_sbc(GaussianModel(Fraction(4), Fraction(1), 8, vs),
                       n_simulations=3000, n_draws=20, seed=20260720,
                       n_bins=7)
        assert sbc_verdict(bad, 0.01) == "inadequate_sbc_failed"
        with pytest.raises(InadequateModelError, match="INADEQUATE"):
            require_sbc_calibrated(bad, 0.01, "sbc_pass")


def test_sbc_lineage_mandatory_and_nbins_load_bearing() -> None:
    # a mismatched SBC lineage is refused
    with pytest.raises(SbcPpcError, match="lineage mismatch"):
        run_sbc(GOOD, n_simulations=100, n_draws=20, seed=1, n_bins=7,
                lineage_hash="wrong", config=_CFG)
    # n_bins must divide n_draws+1
    with pytest.raises(SbcPpcError, match="must divide"):
        _run_sbc(GOOD, n_simulations=100, n_draws=20, seed=1, n_bins=4)


def test_sbc_verdict_cannot_be_bypassed_by_claim_or_floor() -> None:
    bad = _run_sbc(
        GaussianModel(Fraction(4), Fraction(1), 8, Fraction(1, 2)),
        n_simulations=3000,
        n_draws=20,
        seed=20260720,
        n_bins=7,
    )
    with pytest.raises(InadequateModelError, match="INADEQUATE"):
        require_sbc_calibrated(bad, 0.01, "calibrated")
    for floor in (-1.0, 1.0, float("nan"), float("inf"), True):
        with pytest.raises(SbcPpcError, match="floor must be finite"):
            sbc_verdict(bad, floor)
        with pytest.raises(SbcPpcError, match="floor must be finite"):
            require_sbc_calibrated(bad, floor, "sbc_pass")
    for pvalue in (float("nan"), float("inf"), -0.1, 1.1, True):
        malformed = {**bad, "uniformity_pvalue": pvalue}
        with pytest.raises(SbcPpcError, match="uniformity p-value"):
            sbc_verdict(malformed, 0.01)


def test_ppc_frozen_discrepancies_and_mandatory_lineage() -> None:
    frozen = freeze_discrepancies(["sample_variance", "sample_max",
                                   "sample_range"])
    rng = np.random.Generator(np.random.PCG64(3))
    y = rng.normal(0.5, 1.0, 8)
    ppc = run_ppc(GOOD, y, frozen, n_predictive=5000, seed=20260721,
                  lineage=_lineage(GOOD, y))
    assert len(ppc["discrepancy_results"]) == 3
    assert ppc_verdict(ppc, 0.005) == "adequate_conditional"
    assert ppc["lineage_verified"]
    # a mismatched PPC lineage is refused (mandatory)
    bad_lineage = dict(_lineage(GOOD, y), claimed_hash="wrong")
    with pytest.raises(SbcPpcError, match="lineage mismatch"):
        run_ppc(GOOD, y, frozen, n_predictive=100, seed=1,
                lineage=bad_lineage)
    # swapping the frozen discrepancy set is refused
    with pytest.raises(SbcPpcError, match="swapping a discrepancy"):
        require_frozen_discrepancies(frozen, ["sample_variance",
                                              "sample_mean"])


def test_known_bad_ppc_is_extreme() -> None:
    # a mis-specified under-dispersed fit produces extreme p-values
    frozen = freeze_discrepancies(["sample_variance"])
    rng = np.random.Generator(np.random.PCG64(20260720))
    y = rng.normal(0.5, 1.0, 8)
    from common.sbc_ppc import GaussianModel as GM
    fit = GM(GOOD.tau2, Fraction(1, 9), 8, Fraction(1))
    dh = "z"
    lh = lineage_hash(fit, dh, _CFG, {"r": "1.0"})
    bad = run_ppc(GOOD, y, frozen, n_predictive=5000, seed=20260721,
                  fit_sig2=1 / 9,
                  lineage={"claimed_hash": lh, "data_hash": dh,
                           "config": _CFG, "diagnostics": {"r": "1.0"}})
    assert ppc_verdict(bad, 0.005) == "inadequate_ppc_extreme"


@pytest.mark.parametrize("n_predictive", [-1, 0, True, 2.5])
def test_ppc_rejects_invalid_predictive_count(n_predictive) -> None:
    y = np.arange(8, dtype=float)
    frozen = freeze_discrepancies(["sample_variance"])
    with pytest.raises(SbcPpcError, match="positive integer"):
        run_ppc(
            GOOD,
            y,
            frozen,
            n_predictive=n_predictive,
            seed=1,
            lineage=_lineage(GOOD, y),
        )


@pytest.mark.parametrize("y", [
    np.arange(2, dtype=float),
    np.arange(8, dtype=float).reshape(2, 4),
    np.array([0.0, 1.0, np.nan, 3.0, 4.0, 5.0, 6.0, 7.0]),
])
def test_ppc_rejects_wrong_shape_or_nonfinite_observations(y) -> None:
    frozen = freeze_discrepancies(["sample_variance"])
    with pytest.raises(SbcPpcError, match="exactly 8 finite"):
        run_ppc(
            GOOD,
            y,
            frozen,
            n_predictive=100,
            seed=1,
            lineage=_lineage(GOOD, np.arange(8, dtype=float)),
        )


def test_ppc_verdict_rejects_malformed_thresholds_and_results() -> None:
    extreme = {
        "discrepancy_results": [
            {"discrepancy": "sample_variance", "bayesian_p": 0.0},
            {"discrepancy": "sample_max", "bayesian_p": 1.0},
        ],
    }
    for threshold in (-1.0, 0.5, 0.6, float("nan"), float("inf"), True):
        with pytest.raises(SbcPpcError, match="threshold must be finite"):
            ppc_verdict(extreme, threshold)
    for rows in (
        [],
        [{"discrepancy": "sample_variance", "bayesian_p": float("nan")}],
        [{"discrepancy": "sample_variance", "bayesian_p": -0.1}],
        [{"discrepancy": "sample_variance", "bayesian_p": 1.1}],
        [{"discrepancy": "sample_variance", "bayesian_p": True}],
    ):
        with pytest.raises(SbcPpcError, match="discrepancy|p-value"):
            ppc_verdict({"discrepancy_results": rows}, 0.005)


def test_lineage_and_invalid_posterior() -> None:
    dh = "abc123"
    lh = lineage_hash(GOOD, dh, {"n": "8"}, {"rhat": "1.0"})
    verify_lineage(lh, GOOD, dh, {"n": "8"}, {"rhat": "1.0"})
    with pytest.raises(SbcPpcError, match="lineage mismatch"):
        verify_lineage(lh, GOOD, dh, {"n": "9"}, {"rhat": "1.0"})
    with pytest.raises(SbcPpcError, match="invalid posterior|finite"):
        require_valid_posterior(float("nan"))
    with pytest.raises(SbcPpcError, match="finite"):
        require_valid_posterior(-1.0)


def test_ppc_receipt_type_guard() -> None:
    with pytest.raises(SbcPpcError, match="not a PPC receipt"):
        require_ppc_receipt({"kind": "caller_prediction",
                            "point_prediction": 0.5})
    with pytest.raises(SbcPpcError, match="not a PPC receipt"):
        require_ppc_receipt({"bayesian_p": 0.5})
    frozen = freeze_discrepancies(["sample_variance"])
    rng = np.random.Generator(np.random.PCG64(9))
    y = rng.normal(0.5, 1.0, 8)
    ppc = run_ppc(GOOD, y, frozen, n_predictive=1000, seed=1,
                  lineage=_lineage(GOOD, y))
    require_ppc_receipt(ppc)   # a real PPC record passes
    # a receipt missing the verified lineage is refused
    with pytest.raises(SbcPpcError, match="verified posterior lineage"):
        require_ppc_receipt({k: v for k, v in ppc.items()
                             if k != "lineage_verified"})


def test_residual_check_separate_from_ppc() -> None:
    rng = np.random.Generator(np.random.PCG64(1))
    y = rng.normal(0.5, 1.0, 8)
    rc = standardized_residual_check(GOOD, y, 0.5)
    assert rc["type"] == "residual_check"
    assert rc["is_ppc"] is False
    require_not_ppc(rc)
    with pytest.raises(SbcPpcError, match="may not be labeled is_ppc"):
        require_not_ppc(dict(rc, is_ppc=True))


def test_caption_gate() -> None:
    text = generate_caption(0.1, ["inadequate", "inadequate"], "adequate")
    lint_caption(text)
    for suffix in (" The PPC pass proves" + " the model.",
                   " Caller p-value accepted" + " as PPC.",
                   " We swapped the discrepancy" + " after failure.",
                   " SBC validates" + " the observed fit.",
                   " The residual is" + " the PPC."):
        with pytest.raises(SbcPpcError, match="forbidden"):
            lint_caption(text + suffix)


def test_runner_check_mode_is_current() -> None:
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT / "scripts/codex_harness/run_pr138_sbc_ppc.py"),
         "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_artifacts_sbc_ppc_mutations() -> None:
    sbc = json.loads(
        (REPO_ROOT / "docs/generated/pr138_sbc_report.json")
        .read_text(encoding="utf-8"))
    assert sbc["known_good"]["verdict"] == "calibrated"
    assert all(v["verdict"] == "inadequate_sbc_failed"
               for v in sbc["known_bad"].values())
    ppc = json.loads(
        (REPO_ROOT / "docs/generated/pr138_ppc_report.json")
        .read_text(encoding="utf-8"))
    assert ppc["known_good"]["verdict"] == "adequate_conditional"
    assert len(ppc["known_good"]["discrepancy_results"]) == 3
    # the known-bad mis-specified PPC is demonstrated to fail
    assert ppc["known_bad_misspecified"]["verdict"] == \
        "inadequate_ppc_extreme"
    assert ppc["known_good"]["lineage_verified"]
    residual = json.loads(
        (REPO_ROOT / "docs/generated/pr138_residual_check.json")
        .read_text(encoding="utf-8"))
    assert residual["is_ppc"] is False
    report = json.loads(
        (REPO_ROOT / "docs/generated/pr138_mutation_report.json")
        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 6
    manifest = json.loads(
        (REPO_ROOT / "docs/generated/pr138_artifact_manifest.json")
        .read_text(encoding="utf-8"))
    assert all(sha for sha in manifest["artifacts"].values())
