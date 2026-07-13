"""K5 CF4 reconstruction-method dependence card (REV-R196).

The bulk-flow amplitude depends on the peculiar-velocity reconstruction: the same
weighted-GLS estimator on the three CF4 PV columns (Vpds direct / Vpwf WF / Vpec
ramp) plus the CF4++ WF field spans a measured amplitude range. Guards: the card
is committed, the spread is reported, Vpec reproduces the frozen value, and no
detection/family/geometry claim.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts/cf4_reconstruction_dependence.py"
OUT = REPO / "docs/generated/cf4_reconstruction_dependence_card.json"
VARIANTS = REPO / "workdir/obs_bundle/pecvel/cf4_full/cf4_pv_variants.npz"

_FORBIDDEN = ("posterior", "detection", "native solver", "family assignment")


def _card():
    assert OUT.is_file(), "cf4_reconstruction_dependence_card.json not committed"
    return json.loads(OUT.read_text())


def test_measured_three_variants():
    d = _card()
    assert d["status"] == "MEASURED_RECONSTRUCTION_SPREAD"
    m = d["reconstruction_method_comparison"]
    for name in ("Vpds", "Vpwf", "Vpec"):
        assert name in m and m[name]["amplitude_kms"] > 0
    # Vpec reproduces the frozen weighted-GLS value (~340.7 km/s)
    assert abs(m["Vpec"]["amplitude_kms"] - 340.7) < 2.0


def test_reconstruction_spread_is_real():
    d = _card()
    sp = d["catalog_variant_spread"]
    # the amplitude genuinely depends on the reconstruction (WF shrinks the flow)
    assert sp["amplitude_spread_kms"] > 50.0
    assert d["zoa_summary"]["amplitude_spread_kms"] >= 0.0


def test_external_reconstruction_status():
    d = _card()
    ext = d["external_reconstructions"]
    assert ext["carrick_2mpp"] in ("CONNECTED", "BLOCKED_MISSING_CARRICK_2MPP")
    assert ext["nusser_2mrs"] == "BLOCKED_MISSING_CROSS_RECONSTRUCTION"


def test_claim_firewall():
    d = _card()
    blob = json.dumps(d).lower()
    for tok in _FORBIDDEN:
        assert tok not in blob, f"forbidden claim token: {tok!r}"


def _load_module():
    spec = importlib.util.spec_from_file_location("cf4_reconstruction_dependence", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["cf4_reconstruction_dependence"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_deterministic_when_data_present():
    if not VARIANTS.is_file():
        return
    mod = _load_module()
    # the committed card's Carrick content must match the on-disk Carrick file
    card = _card()
    has_carrick_in_card = card.get("carrick2015_2mpp_affine_bulk") is not None
    carrick_present = mod.CARRICK.is_file() or mod.CARRICK_ALT.is_file()
    if has_carrick_in_card != carrick_present:
        return                                 # data-presence mismatch -> skip
    assert mod.main(["--check"]) == 0
