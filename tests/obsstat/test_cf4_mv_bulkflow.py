"""K5 CF4 minimum-variance ideal-window bulk-flow card (REV-R196).

The MV estimator (Watkins-Feldman-Hudson) ties the weights to a specified
Gaussian window of scale R, so its cosmic-variance covariance is faithful and the
LambdaCDM significance is reportable (resolving the rev-r195 withheld
significance). Guards: the card is committed and validation-gated (injected flow
recovered exactly, sigma_v diagonal, grid convergence, published-CF4 cross-check);
the significance is a treatment-dependent RANGE (not a single headline); no
detection/family/geometry claim.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts/cf4_mv_bulkflow.py"
OUT = REPO / "docs/generated/cf4_mv_bulkflow_card.json"
CAT = REPO / "workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz"

_FORBIDDEN = ("posterior", "detection", "native solver", "family assignment")


def _card():
    assert OUT.is_file(), "cf4_mv_bulkflow_card.json not committed"
    return json.loads(OUT.read_text())


def test_measured_and_validated():
    d = _card()
    assert d["status"] == "MEASURED_MV_BULKFLOW"
    v = d["validation"]
    assert v["passed"] is True
    assert v["injection_recovery_error_kms"] < 1e-6      # unbiasedness exact
    assert abs(v["cell_diagonal_sigma_v_kms"]
               - v["closed_form_sigma_v_kms"]) / v["closed_form_sigma_v_kms"] < 0.03
    assert v["khat_grid_convergence_rel"] < 0.02


def test_bulkflow_and_literature():
    d = d0 = _card()
    b200 = d["bulk_flow_vs_R"]["200"]
    assert 200.0 < b200["amplitude_kms"] < 500.0        # CF4-scale bulk flow
    lc = d["literature_crosscheck"]
    assert lc["within_band"] is True
    assert lc["apex_separation_from_published_deg"] < 60.0
    # |B| rises with the CF4 window scale (the observed anomaly)
    amps = [d0["bulk_flow_vs_R"][str(R)]["amplitude_kms"] for R in (50, 100, 150, 200)]
    assert amps == sorted(amps)


def test_significance_is_a_treatment_range():
    d = _card()
    for R in ("50", "100", "150", "200"):
        s = d["bulk_flow_vs_R"][R]["significance"]
        # the honest range: P(k)-corrected <= fiducial (lower cosmic var -> higher sigma)
        assert s["sigma_pk_corrected"] <= s["sigma_full_fiducial_pk"] + 1e-9
    assert "residual_gate" in d       # mock-calibration residual registered


def test_claim_firewall():
    d = _card()
    blob = json.dumps(d).lower()
    for tok in _FORBIDDEN:
        assert tok not in blob, f"forbidden claim token: {tok!r}"


def test_deterministic_when_data_present():
    if not CAT.is_file():
        return
    spec = importlib.util.spec_from_file_location("cf4_mv_bulkflow", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["cf4_mv_bulkflow"] = mod
    spec.loader.exec_module(mod)
    assert mod.main(["--check"]) == 0
