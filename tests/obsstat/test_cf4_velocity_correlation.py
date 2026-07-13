"""K5 CF4 velocity correlation function -> f sigma_8 diagnostic (REV-R196).

The reconstruction-INDEPENDENT statistic: the Gorski Psi_par/Psi_perp velocity
correlation function computed directly from LOS-velocity pairs (no field
reconstruction) -- the physical, well-posed replacement for an ill-posed angular
pseudo-C_l. The f sigma_8 from this simplified pair estimator is a treatment-
dependent DIAGNOSTIC (a precision value needs the max-likelihood estimator).
Guards: committed + claim-gated; Psi measured; f sigma_8 plausible; the exit-gate
registered; no detection/family/geometry claim.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts/cf4_velocity_correlation.py"
OUT = REPO / "docs/generated/cf4_velocity_correlation_card.json"
VARIANTS = REPO / "workdir/obs_bundle/pecvel/cf4_full/cf4_pv_variants.npz"

_FORBIDDEN = ("posterior", "detection", "native solver", "family assignment")


def _card():
    assert OUT.is_file(), "cf4_velocity_correlation_card.json not committed"
    return json.loads(OUT.read_text())


def test_measured_diagnostic():
    d = _card()
    assert d["status"] == "MEASURED_CORRELATION_DIAGNOSTIC"
    for c in ("Vpds", "Vpec"):
        v = d["per_variant"][c]
        assert len(v["psi_par_data_kms2"]) == len(d["separation_bins_hmpc"])
        assert 0.1 < v["f_sigma8"] < 1.6           # plausible, treatment-dependent


def test_reconstruction_independent_and_exit_gate():
    d = _card()
    ris = d["reconstruction_independent_statistic"]
    # the physical statistic is the correlation function (not an angular pseudo-Cl)
    assert "exit_gate" in ris and "max-likelihood" in ris["exit_gate"]
    assert ris["cf4_published_anchor"] == 0.38
    # Vpec (WF-smoothed) is closer to the literature than the noisy direct Vpds
    assert d["per_variant"]["Vpec"]["f_sigma8"] < d["per_variant"]["Vpds"]["f_sigma8"]


def test_claim_firewall():
    d = _card()
    blob = json.dumps(d).lower()
    for tok in _FORBIDDEN:
        assert tok not in blob, f"forbidden claim token: {tok!r}"


def test_deterministic_when_data_present():
    if not VARIANTS.is_file():
        return
    spec = importlib.util.spec_from_file_location("cf4_velocity_correlation", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["cf4_velocity_correlation"] = mod
    spec.loader.exec_module(mod)
    assert mod.main(["--check"]) == 0
