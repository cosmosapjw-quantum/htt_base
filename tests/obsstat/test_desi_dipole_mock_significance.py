"""EXT-DESI mock-calibrated dipole significance card (REV-R198).

The in-house LambdaCDM clustering + Poisson-shot mock null for the DESI DR1 BGS
number-count dipole. Guards: the card is committed, the observed dipole is
clustering-dominated (far above the shot-noise floor), it is consistent with the
LambdaCDM clustering mock across the bias range, and no detection/family/geometry
claim.

Heavy card (loads ~2.3 GB randoms + the mock ensemble) -> the gate READS the
committed card; a fast no-op guard covers the absent-data case.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts/desi_dipole_mock_significance.py"
OUT = REPO / "docs/generated/desi_dipole_mock_card.json"
RAW = REPO / "workdir/raw/desi"

_FORBIDDEN = ("posterior", "detection", "native solver", "family assignment")


def _card():
    assert OUT.is_file(), "desi_dipole_mock_card.json not committed"
    return json.loads(OUT.read_text())


def test_clustering_dominated():
    d = _card()
    if d["status"] == "BLOCKED_MISSING_DESI_RANDOMS":
        return
    assert d["status"] == "MEASURED_MOCK_CALIBRATED"
    # the dipole is far above the shot-noise floor -> clustering-dominated
    assert d["shot_noise"]["sigma_above_shot_noise"] > 5.0
    assert d["headline"]["clustering_dominated"] is True


def test_consistent_with_lcdm_clustering():
    d = _card()
    if d["status"] != "MEASURED_MOCK_CALIBRATED":
        return
    # the observed dipole is within the LambdaCDM clustering null (not an excess)
    assert d["headline"]["consistent_with_lcdm_clustering"] is True
    # robust across the bias range: every p-value is comfortably non-anomalous
    for b, r in d["lcdm_clustering_mock_null"].items():
        assert r["p_value"] > 0.02
        assert r["mock_dipole_std"] > 0


def test_claim_firewall():
    d = _card()
    blob = json.dumps(d).lower()
    for tok in _FORBIDDEN:
        assert tok not in blob, f"forbidden claim token: {tok!r}"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "desi_dipole_mock_significance", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["desi_dipole_mock_significance"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_blocked_status_when_data_absent():
    if (RAW / "BGS_ANY_NGC_0_clustering.ran.fits").is_file():
        return
    mod = _load_module()
    assert mod.measure()["status"] == "BLOCKED_MISSING_DESI_RANDOMS"
