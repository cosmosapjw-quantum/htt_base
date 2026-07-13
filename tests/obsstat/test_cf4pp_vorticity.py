"""K6 CF4++ WF velocity-field vorticity card (REV-R198).

Quantifies the WF mean-field curl suppression on the real 3-D CF4++ field and a
correlated-residual CR vorticity distribution. Guards: the card is committed, the
mean field is potential-flow (curl << div), the CR distribution is flagged
correlation-length-dependent (a definitive ensemble stays blocked), and no
detection/family/geometry/posterior claim.

Heavy card (CR ensemble on the 128^3 field) -> the gate READS the committed card.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts/cf4pp_vorticity_posterior.py"
OUT = REPO / "docs/generated/cf4pp_vorticity_card.json"
FIELD = REPO / "workdir/raw/cf4/CF4pp_mean_std_grids.npz"

_FORBIDDEN = ("posterior", "detection", "native solver", "family assignment")


def _card():
    assert OUT.is_file(), "cf4pp_vorticity_card.json not committed"
    return json.loads(OUT.read_text())


def test_meanfield_potential_flow():
    d = _card()
    if d["status"] == "BLOCKED_MISSING_CF4PP_FIELD":
        return
    assert d["status"] == "MEASURED_WF_CURL_SUPPRESSION_CR_PARTIAL"
    # the WF mean field is strongly curl-suppressed (potential flow)
    assert d["wf_mean_field"]["curl_over_div_ratio"] < 0.1
    assert d["headline"]["meanfield_potential_flow"] is True


def test_cr_distribution_correlation_length_dependent():
    d = _card()
    if d["status"] != "MEASURED_WF_CURL_SUPPRESSION_CR_PARTIAL":
        return
    # the CR curl is residual-dominated and depends on the correlation length ->
    # a definitive ensemble stays blocked (PARTIAL)
    assert d["headline"]["cr_distribution_correlation_length_dependent"] is True
    rows = d["cr_vorticity_distribution_vs_correlation_length"]
    amps = [r["cr_rms_curl_mean"] for r in rows.values()]
    assert max(amps) / min(amps) > 1.5


def test_claim_firewall():
    d = _card()
    blob = json.dumps(d).lower()
    for tok in _FORBIDDEN:
        assert tok not in blob, f"forbidden claim token: {tok!r}"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "cf4pp_vorticity_posterior", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["cf4pp_vorticity_posterior"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_blocked_status_when_field_absent():
    if FIELD.is_file():
        return
    mod = _load_module()
    assert mod.measure()["status"] == "BLOCKED_MISSING_CF4PP_FIELD"
