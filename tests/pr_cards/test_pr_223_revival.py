"""PR-223 gates: multi-fluid moment cone + CAS status."""
from __future__ import annotations
import json, sys
from pathlib import Path
import pytest
REPO = Path(__file__).resolve().parents[2]
for entry in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if entry not in sys.path: sys.path.insert(0, entry)
from common.revival_multifluid import (  # noqa: E402
    antipodal_pair, isotropic_same_trace_has_no_stress, moment_cone_samples)
from scripts.codex_harness import run_pr223_multifluid as runner  # noqa: E402
CARD = REPO/"docs/generated/pr223_result_card.json"

def test_antipodal_zero_flux_nonzero_energy_and_stress():
    p = antipodal_pair()
    assert p["zero_flux"] and p["nonzero_tilt_energy"] and p["nonzero_anisotropic_stress"]
    assert p["aniso_3Pi_diag"] == [4.0, -2.0, -2.0]

def test_isotropic_same_trace_has_no_stress():
    p = antipodal_pair()
    assert isotropic_same_trace_has_no_stress(p["trace"])

def test_moment_cone_trace_nonnegative_stress_at_zero_flux():
    c = moment_cone_samples()
    assert c["trace_always_nonnegative"]
    assert c["fraction_stress_at_zero_flux"] > 0.99

def test_stored_cas_results_are_diagnostic_only():
    cas = runner._cas_status()
    assert cas["aggregate"] == "CAS_BLOCKED"
    assert runner.build_payload()["terminal"] == "BLOCKED_MULTIFLUID_GATE_FAILURE"

def test_historical_card_preserves_pre_ma04_five_axis_label():
    if not CARD.exists(): pytest.skip("card")
    c = json.loads(CARD.read_text())
    cas = c["result"]["cas_status"]
    assert cas["aggregate"] == "CAS_5AXIS_PASS"
    assert cas["contract_hash_matches_adjudication"] is True
    assert c["terminal"] == "MULTIFLUID_MOMENT_CONE_CERTIFIED_CAS_5AXIS_PASS"
