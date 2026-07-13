"""K5 CF4 mock-calibrated bulk-flow significance card (REV-R197).

An in-house PHYSICAL forward-mock ensemble (linear GRF velocity field + super-
sample mode + real per-object noise, at the fixed CF4 geometry) calibrates the
MV estimator's LambdaCDM sampling distribution, replacing the request-only CF4TF
release mocks (BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP). Guards: the card is
committed, the mock reproduces the analytic linear covariance (ratio ~1 ->
estimator not inflating significance), the significance is reported with the
honest nonlinear-COLA residual, and no detection/family/geometry claim.

Heavy card (250 grid realisations) -> the gate READS the committed card (the ACT
pattern) and does not rerun measure(); a data-present determinism check calls
main(["--check"]) only as a fast no-op when the CF4 catalogue is absent.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts/cf4_mock_calibrated_significance.py"
OUT = REPO / "docs/generated/cf4_mock_significance_card.json"
CF4 = REPO / "workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz"

_FORBIDDEN = ("posterior", "detection", "native solver", "family assignment")


def _card():
    assert OUT.is_file(), "cf4_mock_significance_card.json not committed"
    return json.loads(OUT.read_text())


def test_measured_and_validated():
    d = _card()
    if d["status"] == "BLOCKED_MISSING_CF4_CATALOGUE":
        return
    assert d["status"] == "MEASURED_MOCK_CALIBRATED_SIGNIFICANCE"
    v = d["validation"]
    assert v["passed"] is True
    assert v["b_obs_matches_mv_card"] is True
    # the mock reproduces the analytic linear bulk-flow covariance to the grid
    # resolution -> the estimator/geometry/noise do NOT inflate the significance
    for rho in v["cov_ratio_mock_over_analytic_linear"]:
        assert 0.85 <= rho <= 1.15


def test_significance_fields_and_floor():
    d = _card()
    if d["status"] != "MEASURED_MOCK_CALIBRATED_SIGNIFICANCE":
        return
    for R in ("50", "100", "150", "200"):
        s = d["bulk_flow_significance_vs_R"][R]
        assert s["significance_parametric_mock_sigma"] >= 0.0
        # the empirical p-value is bounded by the mock count -> a valid floor
        assert 0.0 <= s["significance_empirical_floor_sigma"] \
            <= s["significance_parametric_mock_sigma"] + 1.0
        assert 0.0 < s["p_value_parametric"] <= 1.0
        assert set(s["sigma_nl_sensitivity_sigma"]) == {"150", "250", "350"}
    # |B|(200) is the CF4 anomaly scale; the parametric tension is significant
    assert d["bulk_flow_significance_vs_R"]["200"]["amplitude_obs_kms"] > 300.0


def test_cola_residual_is_registered():
    d = _card()
    if d["status"] != "MEASURED_MOCK_CALIBRATED_SIGNIFICANCE":
        return
    # the honest ceiling: this linear mock does NOT claim the literature 2-3
    # sigma; the nonlinear COLA residual is registered
    assert "residual_gate" in d
    blob = json.dumps(d).lower()
    assert "cola" in blob or "l-picola" in blob
    assert "positions-conditional" in blob


def test_claim_firewall():
    d = _card()
    blob = json.dumps(d).lower()
    for tok in _FORBIDDEN:
        assert tok not in blob, f"forbidden claim token: {tok!r}"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "cf4_mock_calibrated_significance", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["cf4_mock_calibrated_significance"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_blocked_status_when_catalogue_absent():
    # fast no-op determinism guard: with no CF4 catalogue the card is BLOCKED
    # (the full measure() is heavy and is run standalone, not in the gate)
    if CF4.is_file():
        return
    mod = _load_module()
    assert mod.measure()["status"] == "BLOCKED_MISSING_CF4_CATALOGUE"
