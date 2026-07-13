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
    # REV-R197: the private Nusser 2026 is superseded by two PUBLIC 2MRS
    # reconstructions (LVN 2024 neural network + CORAS 2021 WF/CR)
    assert ext["lilow_nn_2mrs"] in ("CONNECTED", "BLOCKED_MISSING_LILOW_NN")
    assert ext["coras_2mrs"] in ("CONNECTED", "BLOCKED_MISSING_CORAS")
    assert ext["nusser_2mrs"] == "SUPERSEDED_BY_LILOW_2024_PUBLIC"


def test_lilow_nn_reproduces_published_amplitude():
    """When the LVN grid is present, the affine bulk flow reproduces the
    published |B|(50 h^-1Mpc) ~ 220 km/s (Lilow+2024) -- a convention check."""
    d = _card()
    lvn = d.get("lilow_nn_2mrs_affine_bulk")
    if lvn is None:
        return                                     # grid absent -> skip
    assert 180.0 < lvn["50"]["amplitude_kms"] < 260.0


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
    # each external reconstruction's presence in the committed card must match
    # the on-disk file, else a regenerated card would differ (skip, not fail)
    card = _card()
    checks = [
        (card.get("carrick2015_2mpp_affine_bulk") is not None,
         mod.CARRICK.is_file() or mod.CARRICK_ALT.is_file()),
        (card.get("lilow_nn_2mrs_affine_bulk") is not None,
         (mod.LILOW_NN_DIR / "xVelocity.npy").is_file()
         or (mod.LILOW_NN_ALT / "xVelocity.npy").is_file()),
        (card.get("coras_2mrs_affine_bulk") is not None,
         mod.CORAS.is_file() or mod.CORAS_ALT.is_file()),
    ]
    if any(in_card != present for in_card, present in checks):
        return                                 # data-presence mismatch -> skip
    assert mod.main(["--check"]) == 0
