from __future__ import annotations
import json, sys
from pathlib import Path
import pytest
REPO = Path(__file__).resolve().parents[2]
for e in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if e not in sys.path: sys.path.insert(0, e)
from common.revival_bulk_bridge import fisher_rank, recover, single_window_cannot_identify  # noqa: E402
from scripts.codex_harness import run_pr222_bridge as runner  # noqa: E402
CARD = REPO/"docs/generated/pr222_result_card.json"

def test_multi_rank_3_single_rank_1():
    fr = fisher_rank()
    assert fr["multi_window_rank"] == 3 and fr["single_window_rank"] == 1

def test_gls_recovery_low_bias():
    assert recover()["recovers"]

def test_single_window_cannot_identify():
    assert single_window_cannot_identify()

def test_stored_cas_results_are_diagnostic_only():
    cas = runner._cas()
    assert cas["aggregate"] == "CAS_BLOCKED"
    assert runner.build_payload()["terminal"] == "BLOCKED_BRIDGE_GATE_FAILURE"

def test_historical_card_preserves_pre_ma04_five_axis_label():
    if not CARD.exists(): pytest.skip("card")
    c = json.loads(CARD.read_text())
    assert c["result"]["cas_status"]["aggregate"] == "CAS_5AXIS_PASS"
    assert c["terminal"] == "BULK_TO_TILT_BRIDGE_RANK3_CERTIFIED_CAS_5AXIS_PASS"
