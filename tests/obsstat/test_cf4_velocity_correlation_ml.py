"""K5 CF4 velocity-field ML f sigma_8 card (REV-R198).

The precision upgrade of the rev-r196 pair-correlation diagnostic: the field-level
maximum-likelihood noise-aware estimator (Johnson+2014) on the binned CF4 cells,
C(A)=A G+N maximised over the velocity-field amplitude. Guards: the card is
committed, the injection Monte Carlo recovers the amplitude unbiased, Vpec gives a
Planck/CF4-consistent f sigma_8, the direct Vpds is flagged noise-limited, and no
detection/family/geometry claim.

Heavy card (injection MC + octant jackknife rebuild G) -> the gate READS the
committed card; a fast no-op determinism guard covers the absent-catalogue case.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts/cf4_velocity_correlation_ml.py"
OUT = REPO / "docs/generated/cf4_velocity_correlation_ml_card.json"
CF4 = REPO / "workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz"

_FORBIDDEN = ("posterior", "detection", "native solver", "family assignment")


def _card():
    assert OUT.is_file(), "cf4_velocity_correlation_ml_card.json not committed"
    return json.loads(OUT.read_text())


def test_measured_and_injection_unbiased():
    d = _card()
    if d["status"] == "BLOCKED_MISSING_CF4_CATALOGUE":
        return
    assert d["status"] == "MEASURED_ML_FSIGMA8"
    inj = d["injection_validation"]
    # the ML amplitude is recovered unbiased (injection MC pull < 3 sigma)
    assert abs(inj["unbiasedness_pull"]) < 3.0
    assert abs(inj["recovered_amplitude_mean"] - 1.0) < 0.1


def test_vpec_fsigma8_planck_cf4_consistent():
    d = _card()
    if d["status"] != "MEASURED_ML_FSIGMA8":
        return
    v = d["per_variant"]["Vpec"]
    # a clean ML measurement in the growth-rate ballpark
    assert 0.15 < v["f_sigma8_ml"] < 0.75
    assert v["f_sigma8_fisher_error"] > 0
    # consistent with the published CF4 / Planck within the conservative error
    assert d["headline"]["consistent_with_cf4"] is True
    assert d["headline"]["consistent_with_planck"] is True


def test_vpds_direct_noise_limited():
    d = _card()
    if d["status"] != "MEASURED_ML_FSIGMA8":
        return
    # the direct Vpds is honestly flagged noise-limited (amplitude rails)
    assert d["per_variant"]["Vpds"]["noise_limited_railed"] is True


def test_claim_firewall():
    d = _card()
    blob = json.dumps(d).lower()
    for tok in _FORBIDDEN:
        assert tok not in blob, f"forbidden claim token: {tok!r}"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "cf4_velocity_correlation_ml", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["cf4_velocity_correlation_ml"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_blocked_status_when_catalogue_absent():
    if CF4.is_file():
        return
    mod = _load_module()
    assert mod.measure()["status"] == "BLOCKED_MISSING_CF4_CATALOGUE"
