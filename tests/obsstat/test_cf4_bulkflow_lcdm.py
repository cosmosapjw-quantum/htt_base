"""K5 CF4 bulk-flow LambdaCDM cosmic-variance card (REV-R195).

The card promotes the CF4 weighted-GLS bulk flow to a real MEASUREMENT (|B|,
apex, Omega_tilt) and computes the linear estimator-matched cosmic variance,
validated against the closed-form 1-D velocity dispersion. It explicitly
WITHHOLDS the LambdaCDM amplitude significance because the linear window cosmic
variance is a lower bound (the naive chi^2 would be a spurious ~9 sigma).

Guards: the card is committed and claim-gated; the mode-function machinery is
validated + converged; |B| matches the canonical value; NO tension/anomaly or
family/geometry claim is asserted.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts/cf4_bulkflow_lcdm_variance.py"
OUT = REPO / "docs/generated/cf4_bulkflow_lcdm_card.json"
CAT = REPO / "workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz"

# framework token set: phrases that only appear in POSITIVE claims (the card
# legitimately negates "tension"/"anomaly", so those are not in the guard)
_FORBIDDEN = ("posterior", "detection", "native solver", "family assignment")


def _card():
    assert OUT.is_file(), "cf4_bulkflow_lcdm_card.json not committed"
    return json.loads(OUT.read_text())


def test_measurement_and_validation():
    d = _card()
    assert d["status"] == "MEASURED_BULKFLOW_AMPLITUDE"
    v = d["validation"]
    assert v["diagonal_matches_closed_form"] is True
    assert v["converged"] is True
    assert 250.0 < v["closed_form_sigma_v_kms"] < 420.0     # linear sigma_v ~ 300-370
    bf = d["bulk_flow"]
    assert 330.0 < bf["amplitude_kms"] < 350.0              # canonical ~340.7
    assert bf["measurement_error_kms"] < 15.0               # inverse-Fisher error


def test_significance_is_withheld():
    d = _card()
    sig = d["lcdm_amplitude_significance"]
    assert sig["significance_claimed"] is False
    assert d["linear_cosmic_variance_lower_bound"]["is_lower_bound"] is True
    # Omega_tilt is a real kinematic measurement
    assert d["omega_tilt"]["value"] > 0.0


def test_claim_firewall():
    d = _card()
    blob = json.dumps(d).lower()
    for tok in _FORBIDDEN:
        assert tok not in blob, f"forbidden claim token: {tok!r}"


def test_deterministic_when_data_present():
    if not CAT.is_file():
        return
    spec = importlib.util.spec_from_file_location("cf4_bulkflow_lcdm_variance", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["cf4_bulkflow_lcdm_variance"] = mod
    spec.loader.exec_module(mod)
    assert mod.main(["--check"]) == 0
