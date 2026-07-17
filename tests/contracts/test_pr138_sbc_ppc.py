"""PR-138 contract tests: SBC + replicated-data PPC."""
from __future__ import annotations

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
